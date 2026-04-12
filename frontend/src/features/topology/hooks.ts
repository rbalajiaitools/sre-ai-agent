/**
 * Topology TanStack Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTenant } from '@/stores/authStore';
import * as api from './api';
import type { ResourceFilters } from './types';

export function useTopologyGraph() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['topology-graph', tenant?.id],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getTopologyGraph(tenant.id);
    },
    enabled: !!tenant,
  });
}

export function useServices() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['services', tenant?.id],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getServices(tenant.id);
    },
    enabled: !!tenant,
  });
}

export function useServiceDetail(serviceName: string | null) {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['service-detail', tenant?.id, serviceName],
    queryFn: () => {
      if (!tenant || !serviceName) throw new Error('No tenant or service name');
      return api.getServiceDetail(tenant.id, serviceName);
    },
    enabled: !!tenant && !!serviceName,
  });
}

export function useResources(filters?: ResourceFilters) {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['resources', tenant?.id, filters],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getResources(tenant.id, filters);
    },
    enabled: !!tenant,
  });
}

export function useCIMappings() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['ci-mappings', tenant?.id],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getCIMappings(tenant.id);
    },
    enabled: !!tenant,
  });
}

export function useUpdateCIMapping() {
  const tenant = useTenant();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ciSysId, resourceIds }: { ciSysId: string; resourceIds: string[] }) => {
      if (!tenant) throw new Error('No tenant');
      return api.updateCIMapping(tenant.id, ciSysId, resourceIds);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ci-mappings', tenant?.id] });
    },
  });
}

export function useTriggerRediscovery() {
  const tenant = useTenant();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.triggerRediscovery(tenant.id);
    },
    onSuccess: () => {
      // Invalidate topology and resource queries after rediscovery
      queryClient.invalidateQueries({ queryKey: ['topology-graph', tenant?.id] });
      queryClient.invalidateQueries({ queryKey: ['services', tenant?.id] });
      queryClient.invalidateQueries({ queryKey: ['resources', tenant?.id] });
    },
  });
}
