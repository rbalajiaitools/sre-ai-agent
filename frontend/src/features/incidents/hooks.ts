/**
 * Incidents feature hooks using TanStack Query
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '@/stores/authStore';
import { useAppStore } from '@/stores/appStore';
import {
  getIncidents,
  getIncident,
  refreshIncidents,
  startInvestigation,
} from './api';
import { IncidentFilter } from './types';

/**
 * Hook to fetch incidents with optional filters
 */
export function useIncidents() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['incidents', tenant?.id],
    queryFn: () => {
      if (!tenant?.id) {
        throw new Error('No tenant ID available');
      }
      return getIncidents(tenant.id);
    },
    enabled: !!tenant?.id,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to fetch a single incident by number
 */
export function useIncident(incidentNumber: string | null) {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['incident', tenant?.id, incidentNumber],
    queryFn: () => getIncident(tenant!.id, incidentNumber!),
    enabled: !!tenant && !!incidentNumber,
    staleTime: 1000 * 60, // 1 minute
  });
}

/**
 * Hook to refresh incidents from ServiceNow
 */
export function useRefreshIncidents() {
  const queryClient = useQueryClient();
  const tenant = useTenant();

  return useMutation({
    mutationFn: () => refreshIncidents(tenant!.id),
    onSuccess: () => {
      // Invalidate all incidents queries
      queryClient.invalidateQueries({
        queryKey: ['incidents'],
      });
    },
  });
}

/**
 * Hook to start investigation for an incident
 */
export function useStartInvestigation() {
  const queryClient = useQueryClient();
  const tenant = useTenant();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (incidentNumber: string) =>
      startInvestigation(tenant!.id, incidentNumber),
    onMutate: () => {
      // Show loading state immediately
      // The UI component should handle this via isPending
    },
    onSuccess: (data) => {
      // Invalidate incidents to update investigation status
      queryClient.invalidateQueries({
        queryKey: ['incidents'],
      });

      // Navigate to investigations page with the investigation selected
      navigate(`/investigations/${data.investigation_id}`);
    },
  });
}
