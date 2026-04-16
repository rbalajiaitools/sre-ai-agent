/**
 * Investigations feature hooks using TanStack Query
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '@/stores/authStore';
import { InvestigationStatus } from '@/types';
import {
  getInvestigations,
  getInvestigation,
  approveResolution,
  exportPostMortem,
  cancelInvestigation,
  startServiceInvestigation,
  deleteInvestigation,
  bulkDeleteInvestigations,
} from './api';
import { InvestigationFilters } from './types';

/**
 * Hook to fetch investigations with optional filters
 */
export function useInvestigations(filters?: InvestigationFilters) {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['investigations', tenant?.id, filters],
    queryFn: () => getInvestigations(tenant!.id, filters),
    enabled: !!tenant,
    staleTime: 1000 * 60, // 1 minute
  });
}

/**
 * Hook to fetch a single investigation by ID
 * Polls every 2 seconds until manually stopped
 */
export function useInvestigation(id: string | null) {
  return useQuery({
    queryKey: ['investigation', id],
    queryFn: () => getInvestigation(id!),
    enabled: !!id,
    refetchInterval: 2000, // Always poll every 2 seconds - simple and reliable
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook to approve resolution
 */
export function useApproveResolution(investigationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (approvedBy: string) =>
      approveResolution(investigationId, approvedBy),
    onSuccess: () => {
      // Invalidate investigation data
      queryClient.invalidateQueries({
        queryKey: ['investigation', investigationId],
      });
      queryClient.invalidateQueries({
        queryKey: ['investigations'],
      });
      // Invalidate incidents to update status
      queryClient.invalidateQueries({
        queryKey: ['incidents'],
      });
    },
  });
}

/**
 * Hook to export post-mortem PDF
 */
export function useExportPostMortem(investigationId: string) {
  return useMutation({
    mutationFn: () => exportPostMortem(investigationId),
    onSuccess: (blob) => {
      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `investigation-${investigationId}-postmortem.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}


/**
 * Hook to cancel investigation
 */
export function useCancelInvestigation(investigationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => cancelInvestigation(investigationId),
    onSuccess: () => {
      // Invalidate investigation data
      queryClient.invalidateQueries({
        queryKey: ['investigation', investigationId],
      });
      queryClient.invalidateQueries({
        queryKey: ['investigations'],
      });
    },
  });
}

/**
 * Hook to start investigation for a service
 */
export function useStartServiceInvestigation() {
  const tenant = useTenant();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serviceName: string) =>
      startServiceInvestigation(tenant!.id, serviceName),
    onSuccess: (data) => {
      // Invalidate investigations list
      queryClient.invalidateQueries({
        queryKey: ['investigations'],
      });

      // Navigate to investigation page
      navigate(`/investigations/${data.investigation_id}`);
    },
  });
}

/**
 * Hook to delete a single investigation
 */
export function useDeleteInvestigation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (investigationId: string) => deleteInvestigation(investigationId),
    onSuccess: () => {
      // Invalidate investigations list
      queryClient.invalidateQueries({
        queryKey: ['investigations'],
      });
    },
  });
}

/**
 * Hook to delete multiple investigations
 */
export function useBulkDeleteInvestigations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (investigationIds: string[]) => bulkDeleteInvestigations(investigationIds),
    onSuccess: () => {
      // Invalidate investigations list
      queryClient.invalidateQueries({
        queryKey: ['investigations'],
      });
    },
  });
}
