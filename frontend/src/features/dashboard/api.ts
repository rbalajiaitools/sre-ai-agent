/**
 * Dashboard API functions
 */
import { api } from '@/api/client';
import type {
  DashboardStats,
  IncidentTrend,
  TopService,
  AgentAccuracy,
} from './types';

export async function getDashboardStats(tenantId: string): Promise<DashboardStats> {
  return api.get<DashboardStats>(
    `/dashboard/stats?tenant_id=${tenantId}`
  );
}

export async function getIncidentTrends(
  tenantId: string,
  days: number
): Promise<IncidentTrend[]> {
  return api.get<IncidentTrend[]>(
    `/dashboard/trends?tenant_id=${tenantId}&days=${days}`
  );
}

export async function getTopServices(
  tenantId: string,
  limit: number
): Promise<TopService[]> {
  return api.get<TopService[]>(
    `/dashboard/top-services?tenant_id=${tenantId}&limit=${limit}`
  );
}

export async function getAgentStats(tenantId: string): Promise<AgentAccuracy[]> {
  return api.get<AgentAccuracy[]>(
    `/dashboard/agent-stats?tenant_id=${tenantId}`
  );
}
