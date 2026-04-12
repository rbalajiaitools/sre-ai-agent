/**
 * Chat Input - textarea with attach buttons
 */
import { useState, useRef, KeyboardEvent } from 'react';
import { Send, Paperclip, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ChatContext } from '../types';
import { Incident } from '@/types';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ChatInputProps {
  onSend: (content: string, context?: ChatContext) => void;
  disabled?: boolean;
  context?: ChatContext;
  onContextChange?: (context: ChatContext | undefined) => void;
}

export function ChatInput({
  onSend,
  disabled,
  context,
  onContextChange,
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!message.trim() || disabled) return;

    onSend(message.trim(), context);
    setMessage('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);

    // Auto-grow textarea up to 4 lines
    const textarea = e.target;
    textarea.style.height = 'auto';
    const lineHeight = 24; // approximate line height
    const maxHeight = lineHeight * 4;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
  };

  const removeIncident = () => {
    if (onContextChange) {
      onContextChange(
        context?.service_name ? { service_name: context.service_name } : undefined
      );
    }
  };

  const removeService = () => {
    if (onContextChange) {
      onContextChange(
        context?.incident ? { incident: context.incident } : undefined
      );
    }
  };

  return (
    <div className="border-t bg-background p-4">
      {/* Context chips */}
      {(context?.incident || context?.service_name) && (
        <div className="flex flex-wrap gap-2 mb-3">
          {context.incident && (
            <ContextChip
              label={`Incident: ${context.incident.number}`}
              onRemove={removeIncident}
            />
          )}
          {context.service_name && (
            <ContextChip
              label={`Service: ${context.service_name}`}
              onRemove={removeService}
            />
          )}
        </div>
      )}

      {/* Input area */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or type 'investigate INC001'..."
            disabled={disabled}
            className="w-full resize-none rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            rows={1}
            aria-label="Message input"
          />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              disabled={disabled}
              aria-label="Attach context"
            >
              <Paperclip className="h-4 w-4" aria-hidden="true" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onSelect={() => {
                // This will be handled by parent component opening modal
                const event = new CustomEvent('attach-incident');
                window.dispatchEvent(event);
              }}
            >
              Attach incident
            </DropdownMenuItem>
            <DropdownMenuItem
              onSelect={() => {
                // This will be handled by parent component opening modal
                const event = new CustomEvent('attach-service');
                window.dispatchEvent(event);
              }}
            >
              Attach service
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          onClick={handleSend}
          disabled={!message.trim() || disabled}
          size="icon"
          aria-label="Send message"
        >
          <Send className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}

function ContextChip({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-muted text-sm">
      {label}
      <button
        onClick={onRemove}
        className="hover:bg-background rounded p-0.5 transition-colors"
        aria-label={`Remove ${label}`}
      >
        <X className="h-3 w-3" aria-hidden="true" />
      </button>
    </span>
  );
}
