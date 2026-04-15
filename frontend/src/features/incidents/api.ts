/**
 * Incidents API functions
 */
import { api } from '@/api/client';
import {
  ServiceNowIncident,
  IncidentFilter,
  RefreshIncidentsResponse,
  StartInvestigationResponse,
} from './types';

/**
 * Get all incidents for a tenant
 */
export const getIncidents = async (
  tenantId: string
): Promise<ServiceNowIncident[]> => {
  const params = new URLSearchParams({ tenant_id: tenantId });
  return api.get<ServiceNowIncident[]>(`/incidents?${params.toString()}`);
};

/**
 * Get a single incident by number
 */
export const getIncident = async (
  tenantId: string,
  incidentNumber: string
): Promise<ServiceNowIncident> => {
  return api.get<ServiceNowIncident>(
    `/incidents/${incidentNumber}?tenant_id=${tenantId}`
  );
};

/**
 * Refresh incidents from ServiceNow
 */
export const refreshIncidents = async (
  tenantId: string
): Promise<RefreshIncidentsResponse> => {
  return api.post<RefreshIncidentsResponse>('/incidents/refresh', {
    tenant_id: tenantId,
  });
};

/**
 * Start investigation for an incident
 */
export const startInvestigation = async (
  tenantId: string,
  incidentNumber: string
): Promise<StartInvestigationResponse> => {
  return api.post<StartInvestigationResponse>('/investigations/start', {
    tenant_id: tenantId,
    incident_number: incidentNumber,
  });
};
