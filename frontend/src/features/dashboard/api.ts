/**
 * Dashboard API functions
 */
import { apiClient } from '@/api/client';
import type {
  DashboardStats,
  IncidentTrend,
  TopService,
  AgentAccuracy,
} from './types';

export async function getDashboardStats(tenantId: string): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>(
    `/tenants/${tenantId}/dashboard/stats`
  );
  return response.data;
}

export async function getIncidentTrends(
  tenantId: string,
  days: number
): Promise<IncidentTrend[]> {
  const response = await apiClient.get<IncidentTrend[]>(
    `/tenants/${tenantId}/dashboard/trends`,
    { params: { days } }
  );
  return response.data;
}

export async function getTopServices(
  tenantId: string,
  limit: number
): Promise<TopService[]> {
  const response = await apiClient.get<TopService[]>(
    `/tenants/${tenantId}/dashboard/top-services`,
    { params: { limit } }
  );
  return response.data;
}

export async function getAgentStats(tenantId: string): Promise<AgentAccuracy[]> {
  const response = await apiClient.get<AgentAccuracy[]>(
    `/tenants/${tenantId}/dashboard/agent-stats`
  );
  return response.data;
}
