/**
 * Service Attached Message - shows service context chip
 */
import { X, Server } from 'lucide-react';
import { ChatMessage } from '../../types';

interface ServiceAttachedMessageProps {
  message: ChatMessage;
  onRemove?: () => void;
}

export function ServiceAttachedMessage({
  message,
  onRemove,
}: ServiceAttachedMessageProps) {
  const { service_name, service_type, provider } = message.metadata as {
    service_name: string;
    service_type?: string;
    provider?: string;
  };

  return (
    <div className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border bg-card shadow-sm">
      <Server className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">{service_name}</span>
        {(service_type || provider) && (
          <span className="text-xs text-muted-foreground">
            {[service_type, provider].filter(Boolean).join(' • ')}
          </span>
        )}
      </div>
      {onRemove && (
        <button
          onClick={onRemove}
          className="p-0.5 hover:bg-muted rounded transition-colors"
          aria-label="Remove service context"
        >
          <X className="h-3 w-3" aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
