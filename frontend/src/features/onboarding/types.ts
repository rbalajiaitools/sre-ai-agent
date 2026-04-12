/**
 * Onboarding and provider management types
 */
import { ProviderType, IncidentPriority } from '@/types';

export enum OnboardingStep {
  WELCOME = 'welcome',
  CONNECT_PROVIDER = 'connect_provider',
  CONNECT_SERVICENOW = 'connect_servicenow',
  VALIDATE = 'validate',
  DISCOVER = 'discover',
  COMPLETE = 'complete',
}

export interface ProviderConfig {
  provider_type: ProviderType;
  name: string;
  config: Record<string, string>;
}

export interface AWSConfig {
  role_arn: string;
  external_id: string;
  region: string;
  account_id: string;
}

export interface AzureConfig {
  tenant_id: string;
  client_id: string;
  client_secret: string;
  subscription_id: string;
}

export interface GCPConfig {
  project_id: string;
  service_account_key_json: string;
}

export interface OnPremConfig {
  prometheus_url: string;
  loki_url?: string;
  k8s_api_url?: string;
  api_token?: string;
}

export interface ServiceNowConfig {
  instance_url: string;
  username: string;
  password: string;
  incident_filters: {
    priorities: IncidentPriority[];
    assignment_groups: string[];
    poll_interval_minutes: number;
  };
}

export interface ValidationCheck {
  name: string;
  passed: boolean;
  message: string;
}

export interface ValidationResult {
  success: boolean;
  provider_type: ProviderType | 'servicenow';
  checks: ValidationCheck[];
  error?: string;
}

export interface DiscoveryResult {
  services_found: number;
  resources_found: number;
  resource_breakdown: Record<string, number>;
  sample_services: string[];
}

export interface TerraformSnippet {
  hcl: string;
}

export interface ProviderRegistration {
  provider_id: string;
}

export interface ServiceNowRegistration {
  connector_id: string;
}

export interface DiscoveryJob {
  job_id: string;
}

export interface DiscoveryStatus {
  status: 'pending' | 'scanning' | 'building' | 'indexing' | 'complete' | 'failed';
  result?: DiscoveryResult;
  error?: string;
}

export interface ConfiguredProvider {
  id: string;
  provider_type: ProviderType;
  name: string;
  validated: boolean;
  validation_result?: ValidationResult;
}
