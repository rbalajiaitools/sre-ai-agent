/**
 * Simulation feature types
 */

export interface Service {
  id: string;
  name: string;
  type: 'api' | 'database' | 'cache' | 'queue' | 'storage';
  status: 'healthy' | 'degraded' | 'down';
  current_load: number;
  error_rate: number;
}

export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  service_id: string;
  type: 'load' | 'error' | 'latency' | 'crash';
  severity: 'low' | 'medium' | 'high' | 'critical';
  duration_seconds: number;
  parameters: Record<string, any>;
}

export interface SimulationRun {
  id: string;
  scenario_id: string;
  service_id: string;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  incident_created?: string;
  metrics: {
    requests_sent: number;
    errors_generated: number;
    avg_latency_ms: number;
  };
}

export interface TriggerSimulationRequest {
  tenant_id: string;
  service_id: string;
  scenario_type: 'load' | 'error' | 'latency' | 'crash';
  severity: 'low' | 'medium' | 'high' | 'critical';
  duration_seconds: number;
  parameters?: Record<string, any>;
}

export interface TriggerSimulationResponse {
  simulation_id: string;
  message: string;
  incident_number?: string;
}
