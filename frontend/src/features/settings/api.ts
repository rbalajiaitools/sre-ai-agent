/**
 * Settings API functions
 */
import { api } from '@/api/client';

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

// ServiceNow APIs
export async function getServiceNowConfig(tenantId: string): Promise<ServiceNowConfig> {
  return api.get<ServiceNowConfig>(`/settings/servicenow?tenant_id=${tenantId}`);
}

export async function testServiceNow(
  tenantId: string,
  config: ServiceNowConfig
): Promise<TestResult> {
  return api.post<TestResult>('/settings/servicenow/test', {
    tenant_id: tenantId,
    ...config,
  });
}

export async function saveServiceNow(
  tenantId: string,
  config: ServiceNowConfig
): Promise<{ success: boolean }> {
  return api.post<{ success: boolean }>('/settings/servicenow', {
    tenant_id: tenantId,
    ...config,
  });
}

// Cloud Provider APIs
export async function getCloudProviderConfig(
  tenantId: string
): Promise<CloudProviderConfig[]> {
  return api.get<CloudProviderConfig[]>(`/settings/cloud-providers?tenant_id=${tenantId}`);
}

export async function testCloudProvider(
  tenantId: string,
  config: CloudProviderConfig
): Promise<TestResult> {
  return api.post<TestResult>('/settings/cloud-providers/test', {
    tenant_id: tenantId,
    ...config,
  });
}

export async function saveCloudProvider(
  tenantId: string,
  config: CloudProviderConfig
): Promise<{ success: boolean }> {
  return api.post<{ success: boolean }>('/settings/cloud-providers', {
    tenant_id: tenantId,
    ...config,
  });
}
