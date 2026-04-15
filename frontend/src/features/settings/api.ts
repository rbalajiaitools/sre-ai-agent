/**
 * Settings API functions
 */
import { api } from '@/api/client';

export interface Integration {
  id: string;
  name: string;
  type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_sync_at: string | null;
}

export interface ServiceNowConfig {
  instance_url: string;
  username: string;
  password?: string;
}

export interface CloudProviderConfig {
  provider: 'aws' | 'azure' | 'gcp';
  credentials: Record<string, string>;
}

export interface TestResult {
  success: boolean;
  message: string;
}

// Integration APIs
export async function getIntegrations(
  tenantId: string,
  type?: string
): Promise<Integration[]> {
  const params = new URLSearchParams({ tenant_id: tenantId });
  if (type) params.append('type', type);
  return api.get<Integration[]>(`/settings/integrations?${params.toString()}`);
}

export async function getIntegration(integrationId: string): Promise<any> {
  return api.get<any>(`/settings/integrations/${integrationId}`);
}

export async function updateIntegration(
  integrationId: string,
  data: { name?: string; config?: any; is_active?: boolean }
): Promise<{ success: boolean }> {
  return api.put<{ success: boolean }>(`/settings/integrations/${integrationId}`, data);
}

export async function deleteIntegration(integrationId: string): Promise<{ success: boolean }> {
  return api.delete<{ success: boolean }>(`/settings/integrations/${integrationId}`);
}

// ServiceNow APIs
export async function testServiceNow(
  config: ServiceNowConfig
): Promise<TestResult> {
  return api.post<TestResult>('/settings/servicenow/test', config);
}

export async function saveServiceNow(
  tenantId: string,
  name: string,
  config: ServiceNowConfig
): Promise<{ success: boolean; integration_id: string }> {
  return api.post<{ success: boolean; integration_id: string }>('/settings/servicenow', {
    tenant_id: tenantId,
    name,
    ...config,
  });
}

// Cloud Provider APIs
export async function testCloudProvider(
  config: CloudProviderConfig
): Promise<TestResult> {
  return api.post<TestResult>('/settings/cloud-providers/test', config);
}

export async function saveCloudProvider(
  tenantId: string,
  name: string,
  config: CloudProviderConfig
): Promise<{ success: boolean; integration_id: string }> {
  return api.post<{ success: boolean; integration_id: string }>('/settings/cloud-providers', {
    tenant_id: tenantId,
    name,
    ...config,
  });
}
