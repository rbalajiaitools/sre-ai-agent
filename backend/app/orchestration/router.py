"""Conditional edge routing logic for investigation graph."""

from app.core.logging import get_logger
from app.orchestration.state import InvestigationState, InvestigationStatus

logger = get_logger(__name__)


def route_after_dispatcher(state: InvestigationState) -> str:
    """Route after dispatcher based on agent results.

    Args:
        state: Investigation state

    Returns:
        Next node name
    """
    agent_results = state.get("agent_results", [])

    if not agent_results:
        logger.warning(
            "no_agent_results_for_routing",
            investigation_id=state.get("investigation_id"),
        )
        return "error_handler"

    # Check if all agents failed
    successful = sum(1 for r in agent_results if r.success)

    if successful == 0:
        logger.warning(
            "all_agents_failed",
            investigation_id=state.get("investigation_id"),
            total_agents=len(agent_results),
        )
        return "error_handler"

    # At least one agent succeeded - proceed to RCA
    logger.info(
        "routing_to_rca",
        investigation_id=state.get("investigation_id"),
        successful_agents=successful,
        total_agents=len(agent_results),
    )
    return "rca"


def route_after_rca(state: InvestigationState) -> str:
    """Route after RCA based on confidence.

    Args:
        state: Investigation state

    Returns:
        Next node name
    """
    rca = state.get("rca")

    if not rca:
        logger.warning(
            "no_rca_for_routing",
            investigation_id=state.get("investigation_id"),
        )
        return "error_handler"

    # Check confidence threshold
    if rca.confidence < 0.4:
        logger.info(
            "low_confidence_rca",
            investigation_id=state.get("investigation_id"),
            confidence=rca.confidence,
        )
        return "request_more_info"

    # High confidence - proceed to resolver
    logger.info(
        "routing_to_resolver",
        investigation_id=state.get("investigation_id"),
        confidence=rca.confidence,
    )
    return "resolver"


def should_continue(state: InvestigationState) -> bool:
    """Check if investigation should continue.

    Args:
        state: Investigation state

    Returns:
        True if should continue, False otherwise
    """
    status = state.get("status")

    # Stop if failed or resolved
    if status in [InvestigationStatus.FAILED, InvestigationStatus.RESOLVED]:
        return False

    # Stop if error
    if state.get("error"):
        return False

    return True
