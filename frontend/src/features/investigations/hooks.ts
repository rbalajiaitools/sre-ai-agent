/**
 * Investigations feature hooks using TanStack Query
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useTenant } from '@/stores/authStore';
import { InvestigationStatus } from '@/types';
import {
  getInvestigations,
  getInvestigation,
  approveResolution,
  exportPostMortem,
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
 * Polls every 1 second if status is active for live updates
 */
export function useInvestigation(id: string | null) {
  return useQuery({
    queryKey: ['investigation', id],
    queryFn: () => getInvestigation(id!),
    enabled: !!id,
    refetchInterval: (data) => {
      // Poll every 1 second if investigation is active (for live agent updates)
      if (
        data?.status === InvestigationStatus.STARTED ||
        data?.status === InvestigationStatus.INVESTIGATING
      ) {
        return 1000; // 1 second for live updates
      }
      return false;
    },
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
