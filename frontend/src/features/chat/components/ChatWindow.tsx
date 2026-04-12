/**
 * Chat Window - displays messages and input
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

  const { data: messages, isLoading, isError } = useChatMessages(threadId);
  const sendMutation = useSendMessage(threadId);

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
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages && messages.length > 0 ? (
          <>
            {messages.map((message) => (
              <MessageRenderer key={message.id} message={message} />
            ))}
            {/* Typing indicator */}
            {sendMutation.isPending && (
              <div className="flex justify-start mb-4">
                <div className="max-w-[80%] mr-auto">
                  <div className="rounded-lg border bg-card p-4">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-muted-foreground">
              No messages yet. Start the conversation!
            </p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <ChatInput
        onSend={handleSend}
        disabled={sendMutation.isPending}
        context={context}
        onContextChange={setContext}
      />

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
