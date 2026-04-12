/**
 * Incidents feature types
 */
import { IncidentPriority, IncidentState, InvestigationStatus } from '@/types';

export interface ServiceNowIncident {
  sys_id: string;
  number: string;
  short_description: string;
  description: string;
  priority: IncidentPriority;
  state: IncidentState;
  category: string;
  subcategory: string;
  cmdb_ci: string;
  cmdb_ci_sys_id: string;
  assignment_group: string;
  assigned_to: string | null;
  opened_at: string;
  updated_at: string;
  resolved_at: string | null;
  work_notes: string[];
  investigation_status?: InvestigationStatus;
  investigation_id?: string;
}

export interface IncidentFilter {
  priorities: IncidentPriority[];
  states: IncidentState[];
  search: string;
  assignment_group: string;
}

export interface RefreshIncidentsResponse {
  refreshed_at: string;
  count: number;
}

export interface StartInvestigationResponse {
  investigation_id: string;
  chat_thread_id: string;
}
