/**
 * Knowledge Graph hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTenant } from '@/stores/authStore';
import * as api from './api';

export function useKnowledgeList(type?: string, serviceName?: string) {
  const tenant = useTenant();
  const tenantId = tenant?.id || '';

  return useQuery({
    queryKey: ['knowledge', tenantId, type, serviceName],
    queryFn: () => api.getKnowledgeList(tenantId, type, serviceName),
    enabled: !!tenantId,
  });
}

export function useKnowledge(knowledgeId: string) {
  return useQuery({
    queryKey: ['knowledge', knowledgeId],
    queryFn: () => api.getKnowledge(knowledgeId),
    enabled: !!knowledgeId,
  });
}

export function useCreateKnowledge() {
  const queryClient = useQueryClient();
  const tenant = useTenant();
  const tenantId = tenant?.id || '';

  return useMutation({
    mutationFn: (data: api.CreateKnowledgeRequest) =>
      api.createKnowledge(tenantId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useUpdateKnowledge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: api.UpdateKnowledgeRequest }) =>
      api.updateKnowledge(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useDeleteKnowledge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (knowledgeId: string) => api.deleteKnowledge(knowledgeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useConvertInvestigation() {
  const queryClient = useQueryClient();
  const tenant = useTenant();
  const tenantId = tenant?.id || '';

  return useMutation({
    mutationFn: (data: api.ConvertInvestigationRequest) =>
      api.convertInvestigationToKnowledge(tenantId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] });
    },
  });
}

export function useSearchKnowledge() {
  const tenant = useTenant();
  const tenantId = tenant?.id || '';

  return useMutation({
    mutationFn: (data: api.SearchKnowledgeRequest) =>
      api.searchKnowledge(tenantId, data),
  });
}
