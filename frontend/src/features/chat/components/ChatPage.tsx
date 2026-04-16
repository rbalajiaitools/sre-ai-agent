/**
 * Chat Page - Unified chat interface with consistent UX
 */
import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Zap, Trash2, MoreVertical, Loader2 } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { useCreateThread, useChatThreads, useDeleteThread, useChatMessages, useSendMessage } from '../hooks';
import { useInvestigations } from '@/features/investigations/hooks';
import { ChatContext } from '../types';
import { MessageRenderer } from './MessageRenderer';
import { ChatInput } from './ChatInput';
import { IncidentPickerModal } from './IncidentPickerModal';
import { ServicePickerModal } from './ServicePickerModal';
import { Incident } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Sample prompts for the empty state
const samplePrompts = [
  'List all services running in my AWS account',
  'Show me recent incidents and their status',
  'What Lambda functions are deployed and their health?',
  'Investigate incident INC0010001',
  'Show me S3 buckets and their configurations',
  'What are the recent CloudWatch alarms?',
];

export function ChatPage() {
  const { threadId } = useParams<{ threadId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { activeChatId, setActiveChatId } = useAppStore();
  const createThreadMutation = useCreateThread();
  const threadsQuery = useChatThreads();
  const investigationsQuery = useInvestigations();
  const deleteThreadMutation = useDeleteThread();
  const [activeTab, setActiveTab] = useState<'investigations' | 'chats'>('investigations');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [context, setContext] = useState<ChatContext | undefined>();
  const [showIncidentPicker, setShowIncidentPicker] = useState(false);
  const [showServicePicker, setShowServicePicker] = useState(false);
  
  // Resizable left panel
  const [leftWidth, setLeftWidth] = useState(400); // Default 400px
  const isResizing = useRef(false);
  const MIN_WIDTH = 300;
  const MAX_WIDTH = 600;

  // Get messages for active thread
  const { data: messages, isLoading: messagesLoading } = useChatMessages(threadId || null);
  
  // Only create send mutation if we have an active thread
  const sendMutationResult = useSendMessage(threadId || 'temp');
  const [pendingMessage, setPendingMessage] = useState<{ content: string; context?: ChatContext } | null>(null);

  // Handle service context from URL (Topology → Chat flow)
  useEffect(() => {
    const serviceName = searchParams.get('service');
    if (serviceName && !threadId) {
      // Create thread with service context
      createThreadMutation.mutate({
        service_name: serviceName,
      });
    }
  }, [searchParams, threadId]);

  // Sync URL param with store
  useEffect(() => {
    if (threadId && threadId !== activeChatId) {
      setActiveChatId(threadId);
    } else if (!threadId && activeChatId) {
      // Clear active chat if no threadId in URL
      setActiveChatId(null);
    }
  }, [threadId, activeChatId, setActiveChatId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Listen for attach events from ChatInput
  useEffect(() => {
    const handleAttachIncident = () => setShowIncidentPicker(true);
    const handleAttachService = () => setShowServicePicker(true);

    window.addEventListener('attach-incident', handleAttachIncident);
    window.addEventListener('attach-service', handleAttachService);

    return () => {
      window.removeEventListener('attach-incident', handleAttachIncident);
      window.removeEventListener('attach-service', handleAttachService);
    };
  }, []);

  const handlePromptClick = (prompt: string) => {
    // If no active thread, create one first
    if (!threadId) {
      setPendingMessage({ content: prompt, context });
      createThreadMutation.mutate(undefined);
    } else {
      // Already have a thread, just send the message
      sendMutationResult.mutate({ content: prompt, context });
    }
  };

  const handleSend = (content: string, ctx?: ChatContext) => {
    // If no active thread, create one first
    if (!threadId) {
      setPendingMessage({ content, context: ctx });
      createThreadMutation.mutate(undefined);
    } else {
      // Already have a thread, just send the message
      sendMutationResult.mutate({ content, context: ctx });
    }
  };

  // When thread is created and we have a pending message, send it
  useEffect(() => {
    if (threadId && pendingMessage && !createThreadMutation.isPending) {
      const { content, context: ctx } = pendingMessage;
      setPendingMessage(null);
      // Small delay to ensure thread is ready
      setTimeout(() => {
        sendMutationResult.mutate({ content, context: ctx });
      }, 100);
    }
  }, [threadId, pendingMessage, createThreadMutation.isPending]);

  const handleIncidentSelect = (incident: Incident) => {
    setContext((prev) => ({
      ...prev,
      incident,
    }));
  };

  const handleServiceSelect = (serviceName: string) => {
    setContext((prev) => ({
      ...prev,
      service_name: serviceName,
    }));
  };

  // Handle mouse move for resizing
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      
      const newWidth = e.clientX - 240; // Subtract sidebar width
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        setLeftWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing.current) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const handleMouseDown = () => {
    isResizing.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

  const handleDeleteThread = (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chat?')) {
      deleteThreadMutation.mutate(threadId);
      // If deleting active chat, clear it
      if (activeChatId === threadId) {
        setActiveChatId(null);
        navigate('/chat');
      }
    }
  };

  const handleThreadClick = (threadId: string) => {
    setActiveChatId(threadId);
    navigate(`/chat/${threadId}`);
  };

  const handleInvestigationClick = (investigationId: string) => {
    navigate(`/investigations/${investigationId}`);
  };

  // Get real data
  const chatThreads = threadsQuery.data || [];
  const investigations = investigationsQuery.data?.items || [];

  return (
    <div className="flex h-full bg-background">
      {/* Left Section - Resizable */}
      <div 
        className="flex-shrink-0 border-r bg-white overflow-hidden flex flex-col"
        style={{ width: `${leftWidth}px` }}
      >
        {/* Recent Section */}
        <div className="flex-1 flex flex-col overflow-hidden p-6">
          <h2 className="text-xl font-semibold mb-4">Recent</h2>
          
          {/* Tabs */}
          <div className="flex items-center gap-6 mb-4 border-b">
            <button
              onClick={() => setActiveTab('investigations')}
              className={`pb-2 text-sm font-medium transition-colors relative ${
                activeTab === 'investigations'
                  ? 'text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Investigations
              {activeTab === 'investigations' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('chats')}
              className={`pb-2 text-sm font-medium transition-colors relative ${
                activeTab === 'chats'
                  ? 'text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Chats
              {activeTab === 'chats' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 mb-4">
            <select className="px-3 py-1.5 border border-border rounded-md text-sm bg-white">
              <option>All teams</option>
            </select>
            <select className="px-3 py-1.5 border border-border rounded-md text-sm bg-white">
              <option>Recent</option>
            </select>
          </div>

          {/* Activity list - scrollable */}
          <div className="flex-1 overflow-y-auto space-y-2">
            {activeTab === 'investigations' ? (
              investigations.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No investigations yet
                </div>
              ) : (
                investigations.map((investigation) => (
                  <button
                    key={investigation.id}
                    onClick={() => handleInvestigationClick(investigation.id)}
                    className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors text-left"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted flex-shrink-0">
                      <span className="text-xs font-medium">I</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {investigation.incident_number}
                        {investigation.service_name && ` - ${investigation.service_name}`}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Investigations • {formatDistanceToNow(new Date(investigation.started_at), { addSuffix: true })}
                      </p>
                    </div>
                  </button>
                ))
              )
            ) : (
              chatThreads.length === 0 ? (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No chats yet
                </div>
              ) : (
                chatThreads.map((thread) => (
                  <div
                    key={thread.id}
                    className="w-full flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors group"
                  >
                    <button
                      onClick={() => handleThreadClick(thread.id)}
                      className="flex items-center gap-3 flex-1 min-w-0 text-left"
                    >
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted flex-shrink-0">
                        <span className="text-xs font-medium">C</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{thread.title}</p>
                        <p className="text-xs text-muted-foreground">
                          Chats • {formatDistanceToNow(new Date(thread.last_message_at || thread.created_at), { addSuffix: true })}
                        </p>
                      </div>
                    </button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button className="p-1 hover:bg-muted rounded opacity-0 group-hover:opacity-100 transition-opacity">
                          <MoreVertical className="h-4 w-4 text-muted-foreground" />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={(e) => handleDeleteThread(thread.id, e as any)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                ))
              )
            )}
          </div>
        </div>
      </div>

      {/* Resize handle */}
      <div
        className="w-1 bg-border hover:bg-primary/50 cursor-col-resize transition-colors flex-shrink-0"
        onMouseDown={handleMouseDown}
      />

      {/* Right Section - Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Messages area - centered like Claude/ChatGPT */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-8">
            {threadId && messages && messages.length > 0 ? (
              <>
                {messages.map((message) => (
                  <MessageRenderer key={message.id} message={message} />
                ))}
                {/* Typing indicator */}
                {sendMutationResult.isPending && (
                  <div className="flex justify-start mb-6">
                    <div className="flex gap-2 items-start">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 flex-shrink-0">
                        <span className="text-xs font-semibold text-white">AI</span>
                      </div>
                      <div className="rounded-2xl bg-muted px-4 py-3">
                        <div className="flex gap-1">
                          <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: '0ms' }} />
                          <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: '150ms' }} />
                          <span className="w-2 h-2 rounded-full bg-muted-foreground/50 animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            ) : threadId && messagesLoading ? (
              <div className="flex items-center justify-center h-full min-h-[400px]">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : (
              /* Empty state - show welcome message and prompts */
              <div className="flex flex-col items-center justify-start pt-16">
                {/* Header with icon */}
                <div className="flex items-center justify-center mb-6">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
                    <Zap className="h-6 w-6 text-white" />
                  </div>
                </div>

                {/* Main heading */}
                <h1 className="text-3xl font-semibold mb-4 text-center">
                  What can I help you with today?
                </h1>
                
                <p className="text-muted-foreground text-center mb-8 max-w-2xl">
                  Ask me anything about your AWS account, services, incidents, investigations, or infrastructure.
                  I can help you troubleshoot issues, analyze metrics, and provide insights.
                </p>

                {/* Sample prompts */}
                <div className="w-full grid grid-cols-2 gap-3 mb-8">
                  {samplePrompts.map((prompt, index) => (
                    <button
                      key={index}
                      onClick={() => handlePromptClick(prompt)}
                      disabled={createThreadMutation.isPending || sendMutationResult.isPending}
                      className="p-4 text-left border border-border rounded-lg hover:bg-muted/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <p className="text-sm">{prompt}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input area - always visible at bottom */}
        <div className="border-t bg-background">
          <div className="max-w-3xl mx-auto px-4 py-4">
            <ChatInput
              onSend={handleSend}
              disabled={sendMutationResult.isPending || createThreadMutation.isPending}
              context={context}
              onContextChange={setContext}
            />
          </div>
        </div>
      </div>

      {/* Modals */}
      <IncidentPickerModal
        open={showIncidentPicker}
        onClose={() => setShowIncidentPicker(false)}
        onSelect={handleIncidentSelect}
      />
      <ServicePickerModal
        open={showServicePicker}
        onClose={() => setShowServicePicker(false)}
        onSelect={handleServiceSelect}
      />
    </div>
  );
}
