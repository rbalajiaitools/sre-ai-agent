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
    `/tenants/${tenantId}/dashboard/stats`
  );
}

export async function getIncidentTrends(
  tenantId: string,
  days: number
): Promise<IncidentTrend[]> {
  return api.get<IncidentTrend[]>(
    `/tenants/${tenantId}/dashboard/trends`,
    { params: { days } }
  );
}

export async function getTopServices(
  tenantId: string,
  limit: number
): Promise<TopService[]> {
  return api.get<TopService[]>(
    `/tenants/${tenantId}/dashboard/top-services`,
    { params: { limit } }
  );
}

export async function getAgentStats(tenantId: string): Promise<AgentAccuracy[]> {
  return api.get<AgentAccuracy[]>(
    `/tenants/${tenantId}/dashboard/agent-stats`
  );
}
