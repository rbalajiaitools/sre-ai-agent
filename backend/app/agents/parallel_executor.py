"""
Parallel Agent Executor
Executes all specialist agents concurrently for faster investigation processing.
"""
import asyncio
from typing import Dict, List, Any
import structlog
from boto3 import Session

from app.agents.specialists.infra_agent import InfrastructureAgent
from app.agents.specialists.logs_agent import LogsAgent
from app.agents.specialists.metrics_agent import MetricsAgent
from app.agents.specialists.security_agent import SecurityAgent
from app.agents.specialists.code_agent import CodeAgent

logger = structlog.get_logger(__name__)


class ParallelAgentExecutor:
    """Executes all specialist agents in parallel with timeout protection."""
    
    def __init__(
        self,
        session: Session,
        service_name: str,
        description: str,
        investigation_id: str,
        tenant_id: str,
        timeout: int = 30
    ):
        self.session = session
        self.service_name = service_name
        self.description = description
        self.investigation_id = investigation_id
        self.tenant_id = tenant_id
        self.timeout = timeout
        
    async def _run_agent_with_timeout(
        self,
        agent_name: str,
        agent_func,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Run a single agent with timeout protection."""
        import time
        start_time = time.time()
        
        try:
            logger.info(f"starting_{agent_name}_agent", investigation_id=self.investigation_id)
            
            # Run agent in thread pool to avoid blocking
            result = await asyncio.wait_for(
                asyncio.to_thread(agent_func, *args, **kwargs),
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            logger.info(f"{agent_name}_agent_complete", 
                       investigation_id=self.investigation_id,
                       evidence_count=len(result.get('evidence', [])),
                       duration=f"{duration:.2f}s")
            
            # Enrich agent result with required fields for frontend
            agent_result = {
                'agent_type': agent_name,
                'success': True,
                'evidence': result.get('evidence', []),
                'ai_analysis': result.get('ai_analysis', ''),  # Add AI analysis field
                'analysis': {
                    'recommendations': result.get('recommendations', []),
                    'findings_count': len(result.get('evidence', [])),
                },
                'duration_seconds': round(duration, 2),
                'providers_queried': self._get_providers_for_agent(agent_name),
                'error': None
            }
            
            # Update database immediately after agent completes
            # Create a new session for each update to ensure immediate visibility
            logger.info(f"{agent_name}_agent_attempting_db_save", investigation_id=self.investigation_id)
            try:
                from app.db.base import AsyncSessionLocal
                from app.db import crud
                
                logger.info(f"{agent_name}_agent_creating_db_session", investigation_id=self.investigation_id)
                async with AsyncSessionLocal() as db:
                    logger.info(f"{agent_name}_agent_fetching_investigation", investigation_id=self.investigation_id)
                    # Get current investigation
                    investigation = await crud.get_investigation(db, self.investigation_id)
                    if investigation:
                        logger.info(f"{agent_name}_agent_investigation_found", 
                                   investigation_id=self.investigation_id,
                                   current_results_count=len(investigation.agent_results or []))
                        # Append this agent's result to existing results
                        current_results = investigation.agent_results or []
                        # Remove any existing result for this agent type
                        current_results = [r for r in current_results if r.get('agent_type') != agent_name]
                        # Add new result
                        current_results.append(agent_result)
                        logger.info(f"{agent_name}_agent_updating_investigation", 
                                   investigation_id=self.investigation_id,
                                   new_results_count=len(current_results))
                        # Update investigation
                        await crud.update_investigation(
                            db=db,
                            investigation_id=self.investigation_id,
                            agent_results=current_results
                        )
                        # Commit is handled by crud.update_investigation
                        logger.info(f"{agent_name}_agent_saved_to_db", 
                                   investigation_id=self.investigation_id,
                                   agent_results_count=len(current_results))
                    else:
                        logger.error(f"{agent_name}_agent_investigation_not_found", 
                                    investigation_id=self.investigation_id)
            except Exception as db_error:
                logger.error(f"{agent_name}_agent_db_update_failed", 
                            investigation_id=self.investigation_id,
                            error=str(db_error),
                            error_type=type(db_error).__name__)
                import traceback
                logger.error(f"{agent_name}_agent_db_traceback", 
                            investigation_id=self.investigation_id,
                            traceback=traceback.format_exc())
            
            return agent_result
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            logger.warning(f"{agent_name}_agent_timeout", 
                          investigation_id=self.investigation_id,
                          timeout=self.timeout)
            return {
                'agent_type': agent_name,
                'success': False,
                'evidence': [],
                'analysis': {},
                'duration_seconds': round(duration, 2),
                'providers_queried': self._get_providers_for_agent(agent_name),
                'error': f'Agent timed out after {self.timeout} seconds'
            }
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{agent_name}_agent_error",
                        investigation_id=self.investigation_id,
                        error=str(e))
            return {
                'agent_type': agent_name,
                'success': False,
                'evidence': [],
                'analysis': {},
                'duration_seconds': round(duration, 2),
                'providers_queried': self._get_providers_for_agent(agent_name),
                'error': str(e)
            }
    
    def _get_providers_for_agent(self, agent_name: str) -> list:
        """Get list of AWS services queried by each agent type.
        Returns comprehensive list of all possible services each agent can check."""
        providers_map = {
            'infrastructure': ['S3', 'CloudFront', 'EC2', 'Lambda', 'ECS', 'ELB', 'RDS', 'DynamoDB', 'API Gateway'],
            'logs': ['CloudWatch Logs', 'CloudTrail', 'S3 Access Logs'],
            'metrics': ['CloudWatch Metrics', 'CloudWatch Alarms'],
            'security': ['IAM', 'Security Groups', 'CloudTrail', 'S3 Bucket Policies'],
            'code': ['Lambda', 'CodeDeploy', 'CloudFormation', 'CodePipeline']
        }
        return providers_map.get(agent_name, [])
    
    async def execute_all_agents(self) -> List[Dict[str, Any]]:
        """Execute all specialist agents in parallel."""
        
        # Initialize all agents
        infra_agent = InfrastructureAgent(self.session)
        logs_agent = LogsAgent(self.session)
        metrics_agent = MetricsAgent(self.session)
        security_agent = SecurityAgent(self.session)
        code_agent = CodeAgent(self.session)
        
        # Create tasks for all agents
        tasks = [
            self._run_agent_with_timeout(
                'infrastructure',
                infra_agent.investigate,
                self.service_name,
                self.description
            ),
            self._run_agent_with_timeout(
                'logs',
                logs_agent.investigate,
                self.service_name,
                self.description
            ),
            self._run_agent_with_timeout(
                'metrics',
                metrics_agent.investigate,
                self.service_name,
                self.description
            ),
            self._run_agent_with_timeout(
                'security',
                security_agent.investigate,
                self.service_name,
                self.description
            ),
            self._run_agent_with_timeout(
                'code',
                code_agent.investigate,
                self.service_name,
                self.description
            )
        ]
        
        # Execute all agents concurrently
        logger.info("executing_all_agents_parallel", 
                   investigation_id=self.investigation_id,
                   agent_count=len(tasks))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_names = ['infrastructure', 'logs', 'metrics', 'security', 'code']
                processed_results.append({
                    'agent_type': agent_names[i],
                    'success': False,
                    'evidence': [],
                    'analysis': {},
                    'duration_seconds': 0,
                    'providers_queried': self._get_providers_for_agent(agent_names[i]),
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
