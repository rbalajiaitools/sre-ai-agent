/**
 * Investigations feature types
 */
import { InvestigationStatus } from '@/types';

export interface TimelineEvent {
  timestamp: string;
  event: string;
  source: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface AgentResult {
  agent_type: string;
  success: boolean;
  analysis: Record<string, unknown>;
  evidence: string[];
  duration_seconds: number;
  providers_queried: string[];
  error: string | null;
}

export interface RCAResult {
  root_cause: string;
  confidence: number;
  supporting_evidence: string[];
  affected_resources: string[];
  contributing_factors: string[];
  incident_timeline: TimelineEvent[];
}

export interface ResolutionOutput {
  recommended_fix: string;
  fix_steps: string[];
  commands: string[];
  estimated_impact: string;
  requires_human_approval: boolean;
  snow_work_note: string;
}

export interface Investigation {
  id: string;
  tenant_id: string;
  incident_number: string;
  service_name: string;
  status: InvestigationStatus;
  selected_agents: string[];
  agent_results: AgentResult[];
  rca: RCAResult | null;
  resolution: ResolutionOutput | null;
  started_at: string;
  completed_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
}

export interface InvestigationFilters {
  status?: InvestigationStatus;
  date_from?: string;
  date_to?: string;
}
