/**
 * Onboarding API functions
 */
import { api } from '@/api/client';
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
  return api.post<ValidationResult>(
    `/tenants/${tenantId}/providers/validate`,
    config
  );
}

export async function registerProvider(
  tenantId: string,
  config: ProviderConfig
): Promise<ProviderRegistration> {
  return api.post<ProviderRegistration>(
    `/tenants/${tenantId}/providers`,
    config
  );
}

export async function generateTerraformSnippet(
  tenantId: string,
  providerType: ProviderType,
  params: Record<string, string>
): Promise<TerraformSnippet> {
  return api.post<TerraformSnippet>(
    `/tenants/${tenantId}/providers/terraform`,
    { provider_type: providerType, ...params }
  );
}

export async function validateServiceNow(
  tenantId: string,
  config: ServiceNowConfig
): Promise<ValidationResult> {
  return api.post<ValidationResult>(
    `/tenants/${tenantId}/servicenow/validate`,
    config
  );
}

export async function registerServiceNow(
  tenantId: string,
  config: ServiceNowConfig
): Promise<ServiceNowRegistration> {
  return api.post<ServiceNowRegistration>(
    `/tenants/${tenantId}/servicenow`,
    config
  );
}

export async function triggerDiscovery(tenantId: string): Promise<DiscoveryJob> {
  return api.post<DiscoveryJob>(
    `/tenants/${tenantId}/discovery/trigger`
  );
}

export async function getDiscoveryStatus(
  tenantId: string,
  jobId: string
): Promise<DiscoveryStatus> {
  return api.get<DiscoveryStatus>(
    `/tenants/${tenantId}/discovery/${jobId}`
  );
}
