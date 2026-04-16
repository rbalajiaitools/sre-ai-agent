/**
 * Knowledge Graph API client
 */
import { api } from '@/api/client';

export interface Knowledge {
  id: string;
  tenant_id: string;
  title: string;
  type: 'runbook' | 'architecture' | 'code_snippet' | 'investigation' | 'external_link';
  description: string | null;
  content: string | null;
  external_url: string | null;
  tags: string[] | null;
  service_name: string | null;
  incident_number: string | null;
  investigation_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  usage_count: number;
  last_used_at: string | null;
}

export interface CreateKnowledgeRequest {
  title: string;
  type: string;
  description?: string;
  content?: string;
  external_url?: string;
  tags?: string[];
  service_name?: string;
  incident_number?: string;
  investigation_id?: string;
  created_by?: string;
}

export interface UpdateKnowledgeRequest {
  title?: string;
  description?: string;
  content?: string;
  external_url?: string;
  tags?: string[];
  service_name?: string;
}

export interface ConvertInvestigationRequest {
  investigation_id: string;
  title: string;
  description?: string;
  tags?: string[];
}

export interface SearchKnowledgeRequest {
  service_name?: string;
  incident_number?: string;
  search_text?: string;
  limit?: number;
}

export async function getKnowledgeList(
  tenantId: string,
  type?: string,
  serviceName?: string
): Promise<Knowledge[]> {
  const params = new URLSearchParams({ tenant_id: tenantId });
  if (type) params.append('type', type);
  if (serviceName) params.append('service_name', serviceName);
  
  return api.get<Knowledge[]>(`/knowledge/?${params.toString()}`);
}

export async function getKnowledge(knowledgeId: string): Promise<Knowledge> {
  return api.get<Knowledge>(`/knowledge/${knowledgeId}`);
}

export async function createKnowledge(
  tenantId: string,
  data: CreateKnowledgeRequest
): Promise<Knowledge> {
  return api.post<Knowledge>(`/knowledge/?tenant_id=${tenantId}`, data);
}

export async function updateKnowledge(
  knowledgeId: string,
  data: UpdateKnowledgeRequest
): Promise<Knowledge> {
  return api.put<Knowledge>(`/knowledge/${knowledgeId}`, data);
}

export async function deleteKnowledge(knowledgeId: string): Promise<void> {
  return api.delete(`/knowledge/${knowledgeId}`);
}

export async function convertInvestigationToKnowledge(
  tenantId: string,
  data: ConvertInvestigationRequest
): Promise<Knowledge> {
  return api.post<Knowledge>(
    `/knowledge/convert-investigation?tenant_id=${tenantId}`,
    data
  );
}

export async function searchKnowledge(
  tenantId: string,
  data: SearchKnowledgeRequest
): Promise<Knowledge[]> {
  return api.post<Knowledge[]>(
    `/knowledge/search?tenant_id=${tenantId}`,
    data
  );
}
