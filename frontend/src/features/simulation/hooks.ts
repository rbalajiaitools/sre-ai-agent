/**
 * Simulation feature hooks
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTenant } from '@/stores/authStore';
import {
  getServices,
  getScenarios,
  getSimulationRuns,
  triggerSimulation,
  stopSimulation,
} from './api';
import type { TriggerSimulationRequest } from './types';

export function useServices() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['simulation-services', tenant?.id],
    queryFn: () => {
      if (!tenant?.id) throw new Error('No tenant ID');
      return getServices(tenant.id);
    },
    enabled: !!tenant?.id,
  });
}

export function useScenarios() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['simulation-scenarios', tenant?.id],
    queryFn: () => {
      if (!tenant?.id) throw new Error('No tenant ID');
      return getScenarios(tenant.id);
    },
    enabled: !!tenant?.id,
  });
}

export function useSimulationRuns() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['simulation-runs', tenant?.id],
    queryFn: () => {
      if (!tenant?.id) throw new Error('No tenant ID');
      return getSimulationRuns(tenant.id);
    },
    enabled: !!tenant?.id,
    refetchInterval: 5000, // Refresh every 5 seconds
  });
}

export function useTriggerSimulation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: TriggerSimulationRequest) => triggerSimulation(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-runs'] });
      queryClient.invalidateQueries({ queryKey: ['simulation-services'] });
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
    },
  });
}

export function useStopSimulation() {
  const queryClient = useQueryClient();
  const tenant = useTenant();

  return useMutation({
    mutationFn: (simulationId: string) => {
      if (!tenant?.id) throw new Error('No tenant ID');
      return stopSimulation(tenant.id, simulationId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['simulation-runs'] });
      queryClient.invalidateQueries({ queryKey: ['simulation-services'] });
    },
  });
}
