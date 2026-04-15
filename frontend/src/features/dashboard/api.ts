/**
 * Dashboard API functions
 */
import { api } from '@/api/client';

export interface DashboardStats {
  total_incidents: number;
  open_incidents: number;
  resolved_today: number;
  p1_incidents: number;
  p2_incidents: number;
  avg_resolution_hours: number;
  investigations_count: number;
  auto_resolved_count: number;
}

export interface IncidentsByPriority {
  priority: number;
  count: number;
  percentage: number;
}

export interface IncidentsByState {
  state: string;
  count: number;
}

export interface RecentActivity {
  id: string;
  type: 'incident' | 'investigation' | 'chat';
  title: string;
  timestamp: string;
  priority?: number;
}

export interface ServiceHealth {
  service_name: string;
  health_score: number;
  status: 'healthy' | 'degraded' | 'down';
  incident_count: number;
}

export async function getDashboardStats(tenantId: string): Promise<DashboardStats> {
  return api.get<DashboardStats>(`/dashboard/stats?tenant_id=${tenantId}`);
}

export async function getIncidentsByPriority(tenantId: string): Promise<IncidentsByPriority[]> {
  return api.get<IncidentsByPriority[]>(`/dashboard/incidents-by-priority?tenant_id=${tenantId}`);
}

export async function getIncidentsByState(tenantId: string): Promise<IncidentsByState[]> {
  return api.get<IncidentsByState[]>(`/dashboard/incidents-by-state?tenant_id=${tenantId}`);
}

export async function getRecentActivity(tenantId: string, limit: number = 10): Promise<RecentActivity[]> {
  return api.get<RecentActivity[]>(`/dashboard/recent-activity?tenant_id=${tenantId}&limit=${limit}`);
}

export async function getServiceHealth(tenantId: string): Promise<ServiceHealth[]> {
  return api.get<ServiceHealth[]>(`/dashboard/service-health?tenant_id=${tenantId}`);
}
