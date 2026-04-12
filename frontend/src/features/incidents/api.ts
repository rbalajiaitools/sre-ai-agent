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
 * Get all incidents for a tenant with optional filters
 */
export const getIncidents = async (
  tenantId: string,
  filter?: Partial<IncidentFilter>
): Promise<ServiceNowIncident[]> => {
  const params = new URLSearchParams({ tenant_id: tenantId });

  if (filter?.priorities && filter.priorities.length > 0) {
    params.append('priorities', filter.priorities.join(','));
  }
  if (filter?.states && filter.states.length > 0) {
    params.append('states', filter.states.join(','));
  }
  if (filter?.search) {
    params.append('search', filter.search);
  }
  if (filter?.assignment_group) {
    params.append('assignment_group', filter.assignment_group);
  }

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
