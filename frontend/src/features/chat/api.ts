/**
 * Chat API functions
 */
import { api } from '@/api/client';
import {
  ChatThread,
  ChatMessage,
  ChatContext,
  InvestigationProgress,
  Service,
} from './types';

/**
 * Get all chat threads for a tenant
 */
export const getThreads = async (tenantId: string): Promise<ChatThread[]> => {
  return api.get<ChatThread[]>(`/chat/threads?tenant_id=${tenantId}`);
};

/**
 * Create a new chat thread
 */
export const createThread = async (
  tenantId: string,
  context?: ChatContext
): Promise<ChatThread> => {
  return api.post<ChatThread>('/chat/threads', {
    tenant_id: tenantId,
    context,
  });
};

/**
 * Get messages for a specific thread
 */
export const getMessages = async (threadId: string): Promise<ChatMessage[]> => {
  return api.get<ChatMessage[]>(`/chat/threads/${threadId}/messages`);
};

/**
 * Send a message in a thread
 */
export const sendMessage = async (
  threadId: string,
  content: string,
  context?: ChatContext
): Promise<ChatMessage> => {
  return api.post<ChatMessage>(`/chat/threads/${threadId}/messages`, {
    content,
    context,
  });
};

/**
 * Get investigation progress
 */
export const getInvestigationProgress = async (
  investigationId: string
): Promise<InvestigationProgress> => {
  return api.get<InvestigationProgress>(
    `/investigations/${investigationId}/progress`
  );
};

/**
 * Approve resolution and close ticket
 */
export const approveResolution = async (
  investigationId: string,
  approvedBy: string
): Promise<{ success: boolean }> => {
  return api.post<{ success: boolean }>(
    `/investigations/${investigationId}/approve-resolution`,
    {
      approved_by: approvedBy,
    }
  );
};

/**
 * Get list of services from topology
 */
export const getServices = async (tenantId: string): Promise<Service[]> => {
  return api.get<Service[]>(`/topology/services?tenant_id=${tenantId}`);
};
