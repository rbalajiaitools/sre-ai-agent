/**
 * Incident Attached Message - shows incident context in thread
 */
import { X, AlertCircle } from 'lucide-react';
import { ChatMessage } from '../../types';
import { Incident, IncidentPriority } from '@/types';
import { cn } from '@/lib/utils';

interface IncidentAttachedMessageProps {
  message: ChatMessage;
  onRemove?: () => void;
}

export function IncidentAttachedMessage({
  message,
  onRemove,
}: IncidentAttachedMessageProps) {
  const incident = message.metadata.incident as Incident;

  const getPriorityColor = (priority: IncidentPriority) => {
    switch (priority) {
      case IncidentPriority.P1:
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case IncidentPriority.P2:
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case IncidentPriority.P3:
        return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <AlertCircle
          className="h-5 w-5 text-muted-foreground mt-0.5"
          aria-hidden="true"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-medium">
                {incident.number}
              </span>
              <span
                className={cn(
                  'px-2 py-0.5 rounded text-xs font-medium',
                  getPriorityColor(incident.priority)
                )}
              >
                P{incident.priority}
              </span>
            </div>
            {onRemove && (
              <button
                onClick={onRemove}
                className="p-1 hover:bg-muted rounded transition-colors"
                aria-label="Remove incident context"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            )}
          </div>
          <p className="text-sm font-medium mb-1">
            {incident.short_description}
          </p>
          <p className="text-xs text-muted-foreground">
            State: {incident.state} • Opened{' '}
            {new Date(incident.opened_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
}
