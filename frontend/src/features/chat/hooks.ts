/**
 * Chat feature hooks using TanStack Query
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '@/stores/authStore';
import { useAppStore } from '@/stores/appStore';
import {
  getThreads,
  createThread,
  getMessages,
  sendMessage,
  getInvestigationProgress,
  approveResolution,
  getServices,
} from './api';
import { ChatContext, ChatMessage } from './types';

/**
 * Hook to fetch all chat threads
 */
export function useChatThreads() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['chat', 'threads', tenant?.id],
    queryFn: () => getThreads(tenant!.id),
    enabled: !!tenant,
    staleTime: 1000 * 60, // 1 minute
  });
}

/**
 * Hook to fetch messages for a specific thread
 */
export function useChatMessages(threadId: string | null) {
  return useQuery({
    queryKey: ['chat', 'messages', threadId],
    queryFn: () => getMessages(threadId!),
    enabled: !!threadId,
    staleTime: 1000 * 30, // 30 seconds
  });
}

/**
 * Hook to send a message (with optimistic update)
 */
export function useSendMessage(threadId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      content,
      context,
    }: {
      content: string;
      context?: ChatContext;
    }) => sendMessage(threadId, content, context),

    // Optimistic update
    onMutate: async ({ content }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: ['chat', 'messages', threadId],
      });

      // Snapshot previous value
      const previousMessages = queryClient.getQueryData<ChatMessage[]>([
        'chat',
        'messages',
        threadId,
      ]);

      // Optimistically add user message
      const optimisticMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        thread_id: threadId,
        role: 'user',
        content,
        message_type: 'text' as const,
        metadata: {},
        created_at: new Date().toISOString(),
      };

      queryClient.setQueryData<ChatMessage[]>(
        ['chat', 'messages', threadId],
        (old) => [...(old || []), optimisticMessage]
      );

      return { previousMessages };
    },

    // On error, rollback
    onError: (_err, _variables, context) => {
      if (context?.previousMessages) {
        queryClient.setQueryData(
          ['chat', 'messages', threadId],
          context.previousMessages
        );
      }
    },

    // Always refetch after error or success
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ['chat', 'messages', threadId],
      });
      queryClient.invalidateQueries({
        queryKey: ['chat', 'threads'],
      });
    },
  });
}

/**
 * Hook to create a new thread
 */
export function useCreateThread() {
  const queryClient = useQueryClient();
  const tenant = useTenant();
  const navigate = useNavigate();
  const { setActiveChatId } = useAppStore();

  return useMutation({
    mutationFn: (context?: ChatContext) => createThread(tenant!.id, context),
    onSuccess: (newThread) => {
      // Invalidate threads list
      queryClient.invalidateQueries({
        queryKey: ['chat', 'threads'],
      });

      // Set as active chat
      setActiveChatId(newThread.id);

      // Navigate to new chat
      navigate(`/chat/${newThread.id}`);
    },
  });
}

/**
 * Hook to poll investigation progress
 */
export function useInvestigationProgress(
  investigationId: string | null,
  enabled: boolean = true
) {
  const query = useQuery({
    queryKey: ['investigation', 'progress', investigationId],
    queryFn: () => getInvestigationProgress(investigationId!),
    enabled: !!investigationId && enabled,
    refetchInterval: (data) => {
      // Stop polling if investigation is complete or failed
      if (
        data?.status === 'rca_complete' ||
        data?.status === 'resolved' ||
        data?.status === 'failed'
      ) {
        return false;
      }
      // Poll every 2 seconds while active
      return 2000;
    },
  });

  return query;
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
        queryKey: ['investigation', 'progress', investigationId],
      });
      queryClient.invalidateQueries({
        queryKey: ['chat', 'messages'],
      });
      // Invalidate incidents to update status
      queryClient.invalidateQueries({
        queryKey: ['incidents'],
      });
      queryClient.invalidateQueries({
        queryKey: ['investigations'],
      });
    },
  });
}

/**
 * Hook to fetch services for picker
 */
export function useServices() {
  const tenant = useTenant();

  return useQuery({
    queryKey: ['topology', 'services', tenant?.id],
    queryFn: () => getServices(tenant!.id),
    enabled: !!tenant,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
