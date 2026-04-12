/**
 * Chat feature types
 */
import { Incident } from '@/types';

export enum MessageType {
  TEXT = 'text',
  INVESTIGATION_START = 'investigation_start',
  AGENT_PROGRESS = 'agent_progress',
  RCA_RESULT = 'rca_result',
  RESOLUTION = 'resolution',
  INCIDENT_ATTACHED = 'incident_attached',
  SERVICE_ATTACHED = 'service_attached',
  ERROR = 'error',
}

export interface ChatThread {
  id: string;
  title: string;
  created_at: string;
  last_message_at: string;
  investigation_id?: string;
  incident_number?: string;
}

export interface ChatMessage {
  id: string;
  thread_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_type: MessageType;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ChatContext {
  incident?: Incident;
  service_name?: string;
}

export interface AgentSummary {
  agent_name: string;
  status: 'running' | 'completed' | 'failed';
  finding_summary: string;
  duration_seconds: number;
}

export interface InvestigationProgress {
  investigation_id: string;
  status: 'started' | 'investigating' | 'rca_complete' | 'resolved' | 'failed';
  current_step: string;
  agents_running: string[];
  agents_completed: AgentSummary[];
  started_at: string;
  elapsed_seconds: number;
}

export interface RCAResult {
  root_cause: string;
  confidence: number;
  timeline: TimelineEvent[];
  evidence: Evidence[];
  affected_resources: AffectedResource[];
  contributing_factors: string[];
  investigation_id: string;
}

export interface TimelineEvent {
  timestamp: string;
  event: string;
  source: string;
}

export interface Evidence {
  description: string;
  source_agent: string;
  provider: string;
  data: Record<string, unknown>;
}

export interface AffectedResource {
  name: string;
  type: string;
  provider: string;
  status: string;
}

export interface Resolution {
  recommended_fix: string;
  fix_steps: string[];
  commands: string[];
  estimated_impact: string;
  requires_human_approval: boolean;
  approved: boolean;
  approved_by?: string;
  approved_at?: string;
}

export interface Service {
  id: string;
  name: string;
  type: string;
  provider: string;
}
