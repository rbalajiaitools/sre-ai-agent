/**
 * Simulation API functions
 */
import { api } from '@/api/client';
import type {
  Service,
  SimulationScenario,
  SimulationRun,
  TriggerSimulationRequest,
  TriggerSimulationResponse,
} from './types';

export async function getServices(tenantId: string): Promise<Service[]> {
  return api.get<Service[]>(`/simulation/services?tenant_id=${tenantId}`);
}

export async function getScenarios(tenantId: string): Promise<SimulationScenario[]> {
  return api.get<SimulationScenario[]>(`/simulation/scenarios?tenant_id=${tenantId}`);
}

export async function getSimulationRuns(tenantId: string): Promise<SimulationRun[]> {
  return api.get<SimulationRun[]>(`/simulation/runs?tenant_id=${tenantId}`);
}

export async function triggerSimulation(
  request: TriggerSimulationRequest
): Promise<TriggerSimulationResponse> {
  return api.post<TriggerSimulationResponse>('/simulation/trigger', request);
}

export async function stopSimulation(
  tenantId: string,
  simulationId: string
): Promise<{ message: string }> {
  return api.post<{ message: string }>('/simulation/stop', {
    tenant_id: tenantId,
    simulation_id: simulationId,
  });
}
