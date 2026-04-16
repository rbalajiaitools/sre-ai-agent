/**
 * Chat Window - Modern AI chat interface with centered content
 */
import { useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useChatMessages, useSendMessage } from '../hooks';
import { ChatContext } from '../types';
import { MessageRenderer } from './MessageRenderer';
import { ChatInput } from './ChatInput';
import { IncidentPickerModal } from './IncidentPickerModal';
import { ServicePickerModal } from './ServicePickerModal';
import { Incident } from '@/types';

interface ChatWindowProps {
  threadId: string;
}

export function ChatWindow({ threadId }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [context, setContext] = useState<ChatContext | undefined>();
  const [showIncidentPicker, setShowIncidentPicker] = useState(false);
  const [showServicePicker, setShowServicePicker] = useState(false);
  const [autoMessageSent, setAutoMessageSent] = useState(false);

  const { data: messages, isLoading, isError } = useChatMessages(threadId);
  const sendMutation = useSendMessage(threadId);

  // Auto-send initial message from URL parameter
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const initialMessage = params.get('initialMessage');
    
    if (initialMessage && messages && messages.length === 1 && !autoMessageSent && !sendMutation.isPending) {
      // Only auto-send if there's just the welcome message
      setAutoMessageSent(true);
      
      // Send the initial message
      handleSend(initialMessage);
      
      // Clean up URL parameter
      window.history.replaceState({}, '', `/chat/${threadId}`);
    }
  }, [messages, autoMessageSent, sendMutation.isPending, threadId]);

  // Auto-send message when service context is provided from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const serviceName = params.get('service');
    
    if (serviceName && messages && messages.length === 1 && !autoMessageSent && !sendMutation.isPending) {
      // Only auto-send if there's just the welcome message
      setAutoMessageSent(true);
      
      // First, show service details as a user message
      const serviceDetailsMessage = `I want to investigate the service: ${serviceName}

Please provide:
1. Current health status and metrics
2. List of all resources (Lambda functions, databases, etc.)
3. Recent incidents or issues
4. Dependencies and connections to other services
5. Any anomalies or warnings`;

      handleSend(serviceDetailsMessage, { service_name: serviceName });
    }
  }, [messages, autoMessageSent, sendMutation.isPending]);

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

  const handleSend = (content: string, ctx?: ChatContext) => {
    sendMutation.mutate({ content, context: ctx });
  };

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Loading messages" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-muted-foreground">
          Failed to load messages. Please try again.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Messages area - centered like Claude/ChatGPT */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-8">
          {messages && messages.length > 0 ? (
            <>
              {messages.map((message) => (
                <MessageRenderer key={message.id} message={message} />
              ))}
              {/* Typing indicator */}
              {sendMutation.isPending && (
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
            </>
          ) : (
            <div className="flex items-center justify-center h-full min-h-[400px]">
              <p className="text-sm text-muted-foreground">
                No messages yet. Start the conversation!
              </p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area - centered */}
      <div className="border-t bg-background">
        <div className="max-w-3xl mx-auto px-4 py-4">
          <ChatInput
            onSend={handleSend}
            disabled={sendMutation.isPending}
            context={context}
            onContextChange={setContext}
          />
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
