/**
 * Dashboard types
 */
export interface DashboardStats {
  open_incidents: number;
  p1_open: number;
  p2_open: number;
  resolved_today: number;
  avg_mttr_hours: number;
  investigations_today: number;
  auto_resolved: number;
  // Trend data (vs previous period)
  open_incidents_trend?: number;
  avg_mttr_trend?: number;
  resolved_today_trend?: number;
  investigations_today_trend?: number;
}

export interface IncidentTrend {
  date: string;
  p1: number;
  p2: number;
  p3: number;
}

export interface TopService {
  service_name: string;
  incident_count: number;
  avg_resolution_hours: number;
  last_incident_at: string;
}

export interface AgentAccuracy {
  agent_type: string;
  investigations_run: number;
  evidence_found_rate: number;
  avg_duration_seconds: number;
}
