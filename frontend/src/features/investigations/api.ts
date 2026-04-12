/**
 * Investigations API functions
 */
import { api } from '@/api/client';
import { PaginatedResponse } from '@/types';
import { Investigation, InvestigationFilters } from './types';

/**
 * Get all investigations for a tenant with optional filters
 */
export const getInvestigations = async (
  tenantId: string,
  filters?: InvestigationFilters
): Promise<PaginatedResponse<Investigation>> => {
  const params = new URLSearchParams({ tenant_id: tenantId });

  if (filters?.status) {
    params.append('status', filters.status);
  }
  if (filters?.date_from) {
    params.append('date_from', filters.date_from);
  }
  if (filters?.date_to) {
    params.append('date_to', filters.date_to);
  }

  return api.get<PaginatedResponse<Investigation>>(
    `/investigations?${params.toString()}`
  );
};

/**
 * Get a single investigation by ID
 */
export const getInvestigation = async (
  id: string
): Promise<Investigation> => {
  return api.get<Investigation>(`/investigations/${id}`);
};

/**
 * Approve resolution and close ticket
 */
export const approveResolution = async (
  id: string,
  approvedBy: string
): Promise<Investigation> => {
  return api.post<Investigation>(`/investigations/${id}/approve`, {
    approved_by: approvedBy,
  });
};

/**
 * Export post-mortem as PDF
 */
export const exportPostMortem = async (id: string): Promise<Blob> => {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/investigations/${id}/export`,
    {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error('Failed to export post-mortem');
  }

  return response.blob();
};
