/**
 * Incidents API functions (legacy - use features/incidents/api.ts)
 */
import { api } from './client';
import { Incident } from '@/types';

/**
 * Get all incidents for a tenant
 */
export const getIncidents = async (tenantId: string): Promise<Incident[]> => {
  return api.get<Incident[]>(`/incidents?tenant_id=${tenantId}`);
};

/**
 * Get a single incident by ID
 */
export const getIncident = async (incidentId: string): Promise<Incident> => {
  return api.get<Incident>(`/incidents/${incidentId}`);
};
