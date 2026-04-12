/**
 * Settings TanStack Query hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTenant } from '@/stores/authStore';
import * as api from './api';

// ServiceNow hooks
export function useServiceNowConfig() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['servicenow-config', tenant?.id],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getServiceNowConfig(tenant.id);
    },
    enabled: !!tenant,
  });
}

export function useTestServiceNow() {
  const tenant = useTenant();

  return useMutation({
    mutationFn: (config: api.ServiceNowConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.testServiceNow(tenant.id, config);
    },
  });
}

export function useSaveServiceNow() {
  const tenant = useTenant();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: api.ServiceNowConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.saveServiceNow(tenant.id, config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servicenow-config', tenant?.id] });
    },
  });
}

// Cloud Provider hooks
export function useCloudProviderConfig() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['cloud-provider-config', tenant?.id],
    queryFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.getCloudProviderConfig(tenant.id);
    },
    enabled: !!tenant,
  });
}

export function useTestCloudProvider() {
  const tenant = useTenant();

  return useMutation({
    mutationFn: (config: api.CloudProviderConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.testCloudProvider(tenant.id, config);
    },
  });
}

export function useSaveCloudProvider() {
  const tenant = useTenant();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (config: api.CloudProviderConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.saveCloudProvider(tenant.id, config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cloud-provider-config', tenant?.id] });
    },
  });
}
