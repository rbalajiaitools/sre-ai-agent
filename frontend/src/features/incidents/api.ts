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

/**
 * Delete a single incident
 */
export const deleteIncident = async (
  incidentId: string,
  tenantId: string
): Promise<{ success: boolean; message: string }> => {
  return api.delete<{ success: boolean; message: string }>(
    `/incidents/${incidentId}?tenant_id=${tenantId}`
  );
};

/**
 * Delete multiple incidents in bulk
 */
export const bulkDeleteIncidents = async (
  incidentIds: string[],
  tenantId: string
): Promise<{ success: boolean; deleted_count: number; failed_count: number; message: string }> => {
  return api.post<{ success: boolean; deleted_count: number; failed_count: number; message: string }>(
    `/incidents/bulk-delete?tenant_id=${tenantId}`,
    { incident_ids: incidentIds }
  );
};
