"""Agent input/output Pydantic models."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.connectors.servicenow.models import ServiceNowIncident
from app.models.base import BaseSchema


class AgentType(str, Enum):
    """Types of specialist agents."""

    METRICS = "metrics"
    LOGS = "logs"
    INFRA = "infra"
    CODE = "code"
    SECURITY = "security"


class MetricAnomaly(BaseSchema):
    """Detected metric anomaly."""

    metric_name: str = Field(..., description="Name of the metric")
    anomaly_type: str = Field(..., description="Type of anomaly (spike, drop, etc.)")
    severity: str = Field(..., description="Severity (high, medium, low)")
    description: str = Field(..., description="Description of the anomaly")
    timestamp: datetime = Field(..., description="When anomaly occurred")
    baseline_value: float = Field(..., description="Normal baseline value")
    anomaly_value: float = Field(..., description="Anomalous value")


class MetricsAnalysis(BaseSchema):
    """Metrics agent analysis output."""

    anomalies_found: List[MetricAnomaly] = Field(
        default_factory=list, description="Detected anomalies"
    )
    baseline_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Baseline metric values"
    )
    incident_correlation: str = Field(
        ..., description="How metrics correlate with incident"
    )
    confidence: float = Field(
        ..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0
    )


class ErrorPattern(BaseSchema):
    """Detected error pattern in logs."""

    pattern: str = Field(..., description="Error pattern or message")
    count: int = Field(..., description="Number of occurrences")
    first_seen: datetime = Field(..., description="First occurrence")
    last_seen: datetime = Field(..., description="Last occurrence")
    severity: str = Field(..., description="Severity level")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")


class LogsAnalysis(BaseSchema):
    """Logs agent analysis output."""

    error_patterns: List[ErrorPattern] = Field(
        default_factory=list, description="Detected error patterns"
    )
    first_error_time: Optional[datetime] = Field(
        default=None, description="Time of first error"
    )
    root_cause_signals: List[str] = Field(
        default_factory=list, description="Root cause signals found in logs"
    )


class ResourceIssue(BaseSchema):
    """Infrastructure resource issue."""

    resource_name: str = Field(..., description="Resource name")
    resource_type: str = Field(..., description="Resource type")
    issue_type: str = Field(..., description="Type of issue")
    description: str = Field(..., description="Issue description")
    severity: str = Field(..., description="Severity level")


class InfraAnalysis(BaseSchema):
    """Infrastructure agent analysis output."""

    resource_issues: List[ResourceIssue] = Field(
        default_factory=list, description="Detected resource issues"
    )
    capacity_concerns: List[str] = Field(
        default_factory=list, description="Capacity concerns"
    )
    dependency_issues: List[str] = Field(
        default_factory=list, description="Dependency issues"
    )
    recent_changes_impact: str = Field(
        ..., description="Impact of recent infrastructure changes"
    )


class ChangeCorrelation(BaseSchema):
    """Change event correlation with incident."""

    change_description: str = Field(..., description="Description of change")
    change_time: datetime = Field(..., description="When change occurred")
    incident_time: datetime = Field(..., description="When incident occurred")
    time_delta_minutes: int = Field(..., description="Minutes between change and incident")
    correlation_strength: str = Field(
        ..., description="Correlation strength (strong, moderate, weak)"
    )


class CodeAnalysis(BaseSchema):
    """Code/deployment agent analysis output."""

    recent_deployments: List[str] = Field(
        default_factory=list, description="Recent deployments"
    )
    change_correlations: List[ChangeCorrelation] = Field(
        default_factory=list, description="Changes correlated with incident"
    )
    likely_culprit: Optional[str] = Field(
        default=None, description="Most likely change that caused incident"
    )


class SecurityFinding(BaseSchema):
    """Security-related finding."""

    finding_type: str = Field(..., description="Type of finding")
    description: str = Field(..., description="Finding description")
    severity: str = Field(..., description="Severity level")
    affected_resources: List[str] = Field(
        default_factory=list, description="Affected resources"
    )


class SecurityAnalysis(BaseSchema):
    """Security agent analysis output."""

    security_findings: List[SecurityFinding] = Field(
        default_factory=list, description="Security findings"
    )
    iam_changes: List[str] = Field(
        default_factory=list, description="Recent IAM changes"
    )
    unusual_activity: List[str] = Field(
        default_factory=list, description="Unusual activity detected"
    )
    is_security_incident: bool = Field(
        ..., description="Whether this appears to be a security incident"
    )


class AgentInvestigationRequest(BaseSchema):
    """Request for agent investigation."""

    tenant_id: str = Field(..., description="Tenant UUID")
    incident: ServiceNowIncident = Field(..., description="Incident to investigate")
    service_name: str = Field(..., description="Service name to investigate")
    agents_to_run: List[AgentType] = Field(
        ..., description="Which agents to run"
    )
    investigation_context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class AgentResult(BaseSchema):
    """Result from a single agent."""

    agent_type: AgentType = Field(..., description="Type of agent")
    success: bool = Field(..., description="Whether agent completed successfully")
    analysis: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific analysis output"
    )
    evidence: List[str] = Field(
        default_factory=list, description="Key findings as plain strings"
    )
    duration_seconds: float = Field(..., description="Execution duration")
    providers_queried: List[str] = Field(
        default_factory=list, description="Providers queried"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")


class InvestigationResult(BaseSchema):
    """Complete investigation result."""

    incident_number: str = Field(..., description="Incident number")
    service_name: str = Field(..., description="Service investigated")
    agent_results: List[AgentResult] = Field(
        default_factory=list, description="Results from each agent"
    )
    root_cause_summary: str = Field(..., description="Root cause summary")
    evidence: List[str] = Field(
        default_factory=list, description="All evidence collected"
    )
    recommended_actions: List[str] = Field(
        default_factory=list, description="Recommended actions"
    )
    confidence: float = Field(
        ..., description="Overall confidence (0.0-1.0)", ge=0.0, le=1.0
    )
    total_duration_seconds: float = Field(..., description="Total investigation time")
