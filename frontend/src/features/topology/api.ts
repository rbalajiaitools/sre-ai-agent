/**
 * Topology API functions
 */
import { apiClient } from '@/api/client';
import type { PaginatedResponse } from '@/types';
import type {
  TopologyGraph,
  ServiceNode,
  ServiceDetail,
  Resource,
  ResourceFilters,
  CIMapping,
  RediscoveryJob,
} from './types';

export async function getTopologyGraph(tenantId: string): Promise<TopologyGraph> {
  const response = await apiClient.get<TopologyGraph>(
    `/tenants/${tenantId}/topology/graph`
  );
  return response.data;
}

export async function getServices(tenantId: string): Promise<ServiceNode[]> {
  const response = await apiClient.get<ServiceNode[]>(
    `/tenants/${tenantId}/topology/services`
  );
  return response.data;
}

export async function getServiceDetail(
  tenantId: string,
  serviceName: string
): Promise<ServiceDetail> {
  const response = await apiClient.get<ServiceDetail>(
    `/tenants/${tenantId}/topology/services/${encodeURIComponent(serviceName)}`
  );
  return response.data;
}

export async function getResources(
  tenantId: string,
  filters?: ResourceFilters
): Promise<PaginatedResponse<Resource>> {
  const response = await apiClient.get<PaginatedResponse<Resource>>(
    `/tenants/${tenantId}/topology/resources`,
    { params: filters }
  );
  return response.data;
}

export async function getCIMappings(tenantId: string): Promise<CIMapping[]> {
  const response = await apiClient.get<CIMapping[]>(
    `/tenants/${tenantId}/topology/ci-mappings`
  );
  return response.data;
}

export async function updateCIMapping(
  tenantId: string,
  ciSysId: string,
  resourceIds: string[]
): Promise<CIMapping> {
  const response = await apiClient.put<CIMapping>(
    `/tenants/${tenantId}/topology/ci-mappings/${ciSysId}`,
    { resource_ids: resourceIds }
  );
  return response.data;
}

export async function triggerRediscovery(tenantId: string): Promise<RediscoveryJob> {
  const response = await apiClient.post<RediscoveryJob>(
    `/tenants/${tenantId}/topology/rediscover`
  );
  return response.data;
}
