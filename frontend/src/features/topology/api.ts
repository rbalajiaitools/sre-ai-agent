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
    `/tenants/${tenantId}/topology/graph`
  );
}

export async function getServices(tenantId: string): Promise<ServiceNode[]> {
  return api.get<ServiceNode[]>(
    `/tenants/${tenantId}/topology/services`
  );
}

export async function getServiceDetail(
  tenantId: string,
  serviceName: string
): Promise<ServiceDetail> {
  return api.get<ServiceDetail>(
    `/tenants/${tenantId}/topology/services/${encodeURIComponent(serviceName)}`
  );
}

export async function getResources(
  tenantId: string,
  filters?: ResourceFilters
): Promise<PaginatedResponse<Resource>> {
  return api.get<PaginatedResponse<Resource>>(
    `/tenants/${tenantId}/topology/resources`,
    { params: filters }
  );
}

export async function getCIMappings(tenantId: string): Promise<CIMapping[]> {
  return api.get<CIMapping[]>(
    `/tenants/${tenantId}/topology/ci-mappings`
  );
}

export async function updateCIMapping(
  tenantId: string,
  ciSysId: string,
  resourceIds: string[]
): Promise<CIMapping> {
  return api.put<CIMapping>(
    `/tenants/${tenantId}/topology/ci-mappings/${ciSysId}`,
    { resource_ids: resourceIds }
  );
}

export async function triggerRediscovery(tenantId: string): Promise<RediscoveryJob> {
  return api.post<RediscoveryJob>(
    `/tenants/${tenantId}/topology/rediscover`
  );
}
