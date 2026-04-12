/**
 * Global TypeScript types mirroring backend Pydantic models
 */

// Enums
export enum IncidentPriority {
  P1 = '1',
  P2 = '2',
  P3 = '3',
  P4 = '4',
  P5 = '5',
}

export enum IncidentState {
  NEW = '1',
  IN_PROGRESS = '2',
  ON_HOLD = '3',
  RESOLVED = '6',
  CLOSED = '7',
  CANCELED = '8',
}

export enum InvestigationStatus {
  STARTED = 'started',
  INVESTIGATING = 'investigating',
  RCA_COMPLETE = 'rca_complete',
  RESOLVED = 'resolved',
  FAILED = 'failed',
}

export enum ProviderType {
  AWS = 'aws',
  AZURE = 'azure',
  GCP = 'gcp',
  ON_PREM = 'on_prem',
  CUSTOM = 'custom',
}

export type UserRole = 'admin' | 'engineer' | 'viewer';

// Core Models
export interface Tenant {
  id: string;
  name: string;
  plan: string;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

export interface Incident {
  sys_id: string;
  number: string;
  short_description: string;
  description: string;
  priority: IncidentPriority;
  state: IncidentState;
  category: string;
  subcategory: string;
  cmdb_ci: string;
  cmdb_ci_sys_id: string;
  assignment_group: string;
  assigned_to: string | null;
  opened_at: string;
  updated_at: string;
  resolved_at: string | null;
  work_notes: string[];
  related_incidents: string[];
  tenant_id: string;
}

export interface Investigation {
  investigation_id: string;
  incident_number: string;
  tenant_id: string;
  status: InvestigationStatus;
  started_at: string;
  completed_at: string | null;
  selected_agents: string[];
  agent_results_count: number;
  has_rca: boolean;
  has_resolution: boolean;
  error: string | null;
}

export interface Provider {
  id: string;
  type: ProviderType;
  name: string;
  region: string;
  connected: boolean;
  last_sync: string | null;
}

// API Response Types
export interface ApiError {
  message: string;
  status: number;
  code: string;
  details?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Auth Types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
  tenant: Tenant;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  tenant: Tenant | null;
  isAuthenticated: boolean;
}
