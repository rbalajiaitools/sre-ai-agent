/**
 * Dashboard TanStack Query hooks
 */
import { useQuery } from '@tanstack/react-query';
import { useTenant } from '@/stores/authStore';
import * as api from './api';

export function useDashboardStats() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['dashboard-stats', tenant?.id],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getDashboardStats(tenant.id);
    },
    enabled: !!tenant,
    refetchInterval: 60000, // Refresh every minute
  });
}

export function useIncidentTrends(days: number) {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['incident-trends', tenant?.id, days],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getIncidentTrends(tenant.id, days);
    },
    enabled: !!tenant,
  });
}

export function useTopServices(limit: number = 10) {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['top-services', tenant?.id, limit],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getTopServices(tenant.id, limit);
    },
    enabled: !!tenant,
  });
}

export function useAgentStats() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['agent-stats', tenant?.id],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getAgentStats(tenant.id);
    },
    enabled: !!tenant,
  });
}
