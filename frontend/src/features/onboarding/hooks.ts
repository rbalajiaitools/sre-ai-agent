/**
 * Onboarding TanStack Query hooks
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { useAuth } from '@/stores/authStore';
import * as api from './api';
import type {
  ProviderConfig,
  ServiceNowConfig,
  ProviderType,
} from './types';

export function useValidateProvider() {
  const { tenant } = useAuth();

  return useMutation({
    mutationFn: (config: ProviderConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.validateProvider(tenant.id, config);
    },
  });
}

export function useRegisterProvider() {
  const { tenant } = useAuth();

  return useMutation({
    mutationFn: (config: ProviderConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.registerProvider(tenant.id, config);
    },
  });
}

export function useGenerateTerraform() {
  const { tenant } = useAuth();

  return useMutation({
    mutationFn: (params: { providerType: ProviderType; params: Record<string, string> }) => {
      if (!tenant) throw new Error('No tenant');
      return api.generateTerraformSnippet(tenant.id, params.providerType, params.params);
    },
  });
}

export function useValidateServiceNow() {
  const { tenant } = useAuth();

  return useMutation({
    mutationFn: (config: ServiceNowConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.validateServiceNow(tenant.id, config);
    },
  });
}

export function useRegisterServiceNow() {
  const { tenant } = useAuth();

  return useMutation({
    mutationFn: (config: ServiceNowConfig) => {
      if (!tenant) throw new Error('No tenant');
      return api.registerServiceNow(tenant.id, config);
    },
  });
}

export function useTriggerDiscovery() {
  const { tenant } = useAuth();

  return useMutation({
    mutationFn: () => {
      if (!tenant) throw new Error('No tenant');
      return api.triggerDiscovery(tenant.id);
    },
  });
}

export function useDiscoveryStatus(jobId: string | null, enabled: boolean) {
  const { tenant } = useAuth();

  return useQuery({
    queryKey: ['discovery-status', tenant?.id, jobId],
    queryFn: () => {
      if (!tenant || !jobId) throw new Error('No tenant or job ID');
      return api.getDiscoveryStatus(tenant.id, jobId);
    },
    enabled: enabled && !!tenant && !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ['pending', 'scanning', 'building', 'indexing'].includes(status)
        ? 3000
        : false;
    },
  });
}
