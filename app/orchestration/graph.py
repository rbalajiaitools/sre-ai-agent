"""LangGraph StateGraph definition for investigation workflow."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.adapters.registry import ProviderRegistry
from app.connectors.servicenow.connector import ServiceNowConnector
from app.core.logging import get_logger
from app.knowledge.graph import KnowledgeGraph
from app.knowledge.memory import IncidentMemory
from app.orchestration.nodes import (
    DispatcherNode,
    PlannerNode,
    RCANode,
    ResolverNode,
)
from app.orchestration.router import route_after_dispatcher, route_after_rca
from app.orchestration.state import InvestigationState, InvestigationStatus

logger = get_logger(__name__)


class InvestigationGraph:
    """LangGraph-based investigation workflow.

    Orchestrates the complete incident investigation process:
    1. Planning - Select appropriate agents
    2. Dispatch - Run agents in parallel
    3. RCA - Synthesize findings into root cause
    4. Resolution - Generate fix recommendations
    """

    def __init__(
        self,
        llm: BaseChatModel,
        registry: ProviderRegistry,
        knowledge_graph: KnowledgeGraph,
        incident_memory: IncidentMemory,
        servicenow_connector: ServiceNowConnector,
        checkpointer: Optional[any] = None,
    ) -> None:
        """Initialize investigation graph.

        Args:
            llm: Language model for nodes
            registry: Provider registry
            knowledge_graph: Knowledge graph
            incident_memory: Incident memory
            servicenow_connector: ServiceNow connector
            checkpointer: Checkpointer for state persistence (optional)
        """
        self.llm = llm
        self.registry = registry
        self.knowledge_graph = knowledge_graph
        self.incident_memory = incident_memory
        self.servicenow_connector = servicenow_connector
        self.checkpointer = checkpointer or MemorySaver()

        # Initialize nodes
        self.planner = PlannerNode(llm, knowledge_graph, incident_memory)
        self.dispatcher = DispatcherNode(llm, registry)
        self.rca = RCANode(llm, knowledge_graph)
        self.resolver = ResolverNode(llm, servicenow_connector, incident_memory)

        # Build graph
        self.graph = self._build_graph()

        logger.info("investigation_graph_initialized")

    def _build_graph(self) -> StateGraph:
        """Build the investigation state graph.

        Returns:
            Compiled state graph
        """
        # Create graph
        workflow = StateGraph(InvestigationState)

        # Add nodes
        workflow.add_node("planner", self._wrap_node(self.planner))
        workflow.add_node("dispatcher", self._wrap_node(self.dispatcher))
        workflow.add_node("rca", self._wrap_node(self.rca))
        workflow.add_node("resolver", self._wrap_node(self.resolver))
        workflow.add_node("error_handler", self._error_handler)
        workflow.add_node("request_more_info", self._request_more_info)

        # Set entry point
        workflow.set_entry_point("planner")

        # Add edges
        workflow.add_edge("planner", "dispatcher")

        # Conditional edge after dispatcher
        workflow.add_conditional_edges(
            "dispatcher",
            route_after_dispatcher,
            {
                "rca": "rca",
                "error_handler": "error_handler",
            },
        )

        # Conditional edge after RCA
        workflow.add_conditional_edges(
            "rca",
            route_after_rca,
            {
                "resolver": "resolver",
                "request_more_info": "request_more_info",
                "error_handler": "error_handler",
            },
        )

        # Terminal edges
        workflow.add_edge("resolver", END)
        workflow.add_edge("error_handler", END)
        workflow.add_edge("request_more_info", END)

        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)

    def _wrap_node(self, node: any) -> callable:
        """Wrap node with error handling.

        Args:
            node: Node to wrap

        Returns:
            Wrapped node function
        """

        async def wrapped(state: InvestigationState) -> InvestigationState:
            try:
                return await node(state)
            except Exception as e:
                logger.error(
                    "node_execution_failed",
                    node=node.__class__.__name__,
                    investigation_id=state.get("investigation_id"),
                    error=str(e),
                )
                state["error"] = f"{node.__class__.__name__} failed: {str(e)}"
                state["status"] = InvestigationStatus.FAILED
                return state

        return wrapped

    async def _error_handler(
        self, state: InvestigationState
    ) -> InvestigationState:
        """Handle errors in investigation.

        Args:
            state: Investigation state

        Returns:
            Updated state
        """
        logger.error(
            "investigation_error",
            investigation_id=state.get("investigation_id"),
            error=state.get("error"),
            status=state.get("status"),
        )

        state["status"] = InvestigationStatus.FAILED
        state["completed_at"] = datetime.utcnow()

        # Try to update ServiceNow with error
        try:
            incident = state.get("incident")
            if incident:
                error_note = (
                    f"Automated investigation encountered an error:\n\n"
                    f"{state.get('error', 'Unknown error')}\n\n"
                    f"Manual investigation required."
                )

                await self.servicenow_connector.add_work_note(
                    incident.sys_id,
                    error_note,
                )

        except Exception as e:
            logger.warning(
                "error_handler_servicenow_update_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )

        return state

    async def _request_more_info(
        self, state: InvestigationState
    ) -> InvestigationState:
        """Request more information from human.

        Args:
            state: Investigation state

        Returns:
            Updated state
        """
        logger.info(
            "requesting_more_info",
            investigation_id=state.get("investigation_id"),
            rca_confidence=state.get("rca", {}).get("confidence") if state.get("rca") else None,
        )

        state["status"] = InvestigationStatus.NEEDS_INPUT
        state["completed_at"] = datetime.utcnow()

        # Update ServiceNow
        try:
            incident = state.get("incident")
            rca = state.get("rca")

            if incident and rca:
                note = (
                    f"Automated investigation completed with low confidence "
                    f"({rca.confidence:.0%}).\n\n"
                    f"Preliminary Root Cause:\n{rca.root_cause}\n\n"
                    f"Additional information needed:\n"
                    f"- Verify affected resources\n"
                    f"- Check for recent changes not captured in automation\n"
                    f"- Review application logs manually\n\n"
                    f"Please provide additional context to improve analysis."
                )

                await self.servicenow_connector.add_work_note(
                    incident.sys_id,
                    note,
                )

        except Exception as e:
            logger.warning(
                "request_more_info_servicenow_update_failed",
                investigation_id=state.get("investigation_id"),
                error=str(e),
            )

        return state

    async def investigate(
        self,
        tenant_id: str,
        incident: any,
        service_name: str,
        mapped_resources: list,
    ) -> str:
        """Start an investigation.

        Args:
            tenant_id: Tenant UUID
            incident: ServiceNow incident
            service_name: Service name
            mapped_resources: Mapped resources

        Returns:
            Investigation ID
        """
        investigation_id = str(uuid4())

        # Create initial state
        initial_state: InvestigationState = {
            "investigation_id": investigation_id,
            "tenant_id": tenant_id,
            "incident": incident,
            "service_name": service_name,
            "mapped_resources": mapped_resources,
            "selected_agents": [],
            "agent_results": [],
            "rca": None,
            "resolution": None,
            "status": InvestigationStatus.STARTED,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error": None,
            "similar_incidents": [],
            "topology": None,
        }

        logger.info(
            "investigation_started",
            investigation_id=investigation_id,
            tenant_id=tenant_id,
            incident_number=incident.number,
            service_name=service_name,
        )

        # Invoke graph asynchronously
        config = {"configurable": {"thread_id": investigation_id}}

        try:
            # Run graph
            final_state = await self.graph.ainvoke(initial_state, config)

            logger.info(
                "investigation_completed",
                investigation_id=investigation_id,
                status=final_state.get("status"),
                has_rca=final_state.get("rca") is not None,
                has_resolution=final_state.get("resolution") is not None,
            )

        except Exception as e:
            logger.error(
                "investigation_execution_failed",
                investigation_id=investigation_id,
                error=str(e),
            )

        return investigation_id

    async def get_state(self, investigation_id: str) -> Optional[InvestigationState]:
        """Get investigation state.

        Args:
            investigation_id: Investigation ID

        Returns:
            Investigation state or None
        """
        try:
            config = {"configurable": {"thread_id": investigation_id}}

            # Get state from checkpointer
            state_snapshot = await self.graph.aget_state(config)

            if state_snapshot and state_snapshot.values:
                return state_snapshot.values

            return None

        except Exception as e:
            logger.error(
                "get_state_failed",
                investigation_id=investigation_id,
                error=str(e),
            )
            return None
