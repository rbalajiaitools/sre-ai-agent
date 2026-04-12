/**
 * Topology and resource inventory types
 */
import { ProviderType } from '@/types';

export type ServiceStatus = 'healthy' | 'degraded' | 'down' | 'unknown';

export interface ServiceNode {
  id: string;
  name: string;
  type: string;
  provider: ProviderType;
  region: string;
  status: ServiceStatus;
  incident_count: number;
  resource_count: number;
  tags: Record<string, string>;
}

export type EdgeRelationship = 'DEPENDS_ON' | 'CALLS' | 'READS_FROM';

export interface ServiceEdge {
  id: string;
  source: string;
  target: string;
  relationship: EdgeRelationship;
}

export interface TopologyGraph {
  nodes: ServiceNode[];
  edges: ServiceEdge[];
}

export interface ServiceDetail extends ServiceNode {
  resources: Resource[];
  past_incidents: ServiceIncident[];
  team_owner: string;
  health_summary: {
    total_resources: number;
    healthy_resources: number;
    degraded_resources: number;
    down_resources: number;
  };
}

export interface ServiceIncident {
  incident_number: string;
  priority: string;
  short_description: string;
  resolved_at: string | null;
  sys_id: string;
}

export interface Resource {
  resource_id: string;
  name: string;
  type: string;
  provider: ProviderType;
  region: string;
  status: ServiceStatus;
  tags: Record<string, string>;
  metadata: Record<string, unknown>;
  service_name: string;
}

export interface MappedResource {
  resource_id: string;
  resource_name: string;
  provider: ProviderType;
  confidence_score: number;
}

export interface CIMapping {
  ci_name: string;
  ci_sys_id: string;
  mapped_resources: MappedResource[];
  confidence: number;
}

export interface RediscoveryJob {
  job_id: string;
}

export interface ResourceFilters {
  providers?: ProviderType[];
  types?: string[];
  statuses?: ServiceStatus[];
  search?: string;
  service_name?: string;
}
