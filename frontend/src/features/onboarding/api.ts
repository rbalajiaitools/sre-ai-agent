/**
 * Onboarding API functions
 */
import { apiClient } from '@/api/client';
import { ProviderType } from '@/types';
import type {
  ProviderConfig,
  ValidationResult,
  ProviderRegistration,
  TerraformSnippet,
  ServiceNowConfig,
  ServiceNowRegistration,
  DiscoveryJob,
  DiscoveryStatus,
} from './types';

export async function validateProvider(
  tenantId: string,
  config: ProviderConfig
): Promise<ValidationResult> {
  const response = await apiClient.post<ValidationResult>(
    `/tenants/${tenantId}/providers/validate`,
    config
  );
  return response.data;
}

export async function registerProvider(
  tenantId: string,
  config: ProviderConfig
): Promise<ProviderRegistration> {
  const response = await apiClient.post<ProviderRegistration>(
    `/tenants/${tenantId}/providers`,
    config
  );
  return response.data;
}

export async function generateTerraformSnippet(
  tenantId: string,
  providerType: ProviderType,
  params: Record<string, string>
): Promise<TerraformSnippet> {
  const response = await apiClient.post<TerraformSnippet>(
    `/tenants/${tenantId}/providers/terraform`,
    { provider_type: providerType, ...params }
  );
  return response.data;
}

export async function validateServiceNow(
  tenantId: string,
  config: ServiceNowConfig
): Promise<ValidationResult> {
  const response = await apiClient.post<ValidationResult>(
    `/tenants/${tenantId}/servicenow/validate`,
    config
  );
  return response.data;
}

export async function registerServiceNow(
  tenantId: string,
  config: ServiceNowConfig
): Promise<ServiceNowRegistration> {
  const response = await apiClient.post<ServiceNowRegistration>(
    `/tenants/${tenantId}/servicenow`,
    config
  );
  return response.data;
}

export async function triggerDiscovery(tenantId: string): Promise<DiscoveryJob> {
  const response = await apiClient.post<DiscoveryJob>(
    `/tenants/${tenantId}/discovery/trigger`
  );
  return response.data;
}

export async function getDiscoveryStatus(
  tenantId: string,
  jobId: string
): Promise<DiscoveryStatus> {
  const response = await apiClient.get<DiscoveryStatus>(
    `/tenants/${tenantId}/discovery/${jobId}`
  );
  return response.data;
}
