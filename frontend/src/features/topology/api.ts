/**
 * Topology API functions
 */
import { api } from '@/api/client';
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
  return api.get<TopologyGraph>(
    `/topology/graph?tenant_id=${tenantId}`
  );
}

export async function getServices(tenantId: string): Promise<ServiceNode[]> {
  return api.get<ServiceNode[]>(
    `/topology/services?tenant_id=${tenantId}`
  );
}

export async function getServiceDetail(
  tenantId: string,
  serviceName: string
): Promise<ServiceDetail> {
  return api.get<ServiceDetail>(
    `/topology/services/${encodeURIComponent(serviceName)}?tenant_id=${tenantId}`
  );
}

export async function getResources(
  tenantId: string,
  filters?: ResourceFilters
): Promise<PaginatedResponse<Resource>> {
  const params = new URLSearchParams({ tenant_id: tenantId });
  if (filters?.provider) params.append('provider', filters.provider);
  if (filters?.resource_type) params.append('resource_type', filters.resource_type);
  if (filters?.search) params.append('search', filters.search);
  
  return api.get<PaginatedResponse<Resource>>(
    `/topology/resources?${params.toString()}`
  );
}

export async function getCIMappings(tenantId: string): Promise<CIMapping[]> {
  return api.get<CIMapping[]>(
    `/topology/ci-mappings?tenant_id=${tenantId}`
  );
}

export async function updateCIMapping(
  tenantId: string,
  ciSysId: string,
  resourceIds: string[]
): Promise<CIMapping> {
  return api.put<CIMapping>(
    `/topology/ci-mappings/${ciSysId}?tenant_id=${tenantId}`,
    { resource_ids: resourceIds }
  );
}

export async function triggerRediscovery(tenantId: string): Promise<RediscoveryJob> {
  return api.post<RediscoveryJob>(
    `/topology/rediscover?tenant_id=${tenantId}`
  );
}
