/**
 * Investigation Start Message
 */
import { PlayCircle } from 'lucide-react';
import { ChatMessage } from '../../types';

interface InvestigationStartMessageProps {
  message: ChatMessage;
}

export function InvestigationStartMessage({
  message,
}: InvestigationStartMessageProps) {
  const { incident_number, service_name } = message.metadata as {
    incident_number?: string;
    service_name?: string;
  };

  return (
    <div className="rounded-lg border bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800 p-4">
      <div className="flex items-start gap-3">
        <PlayCircle
          className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5"
          aria-hidden="true"
        />
        <div className="flex-1">
          <p className="font-medium text-blue-900 dark:text-blue-100">
            Investigation started
          </p>
          <div className="mt-2 space-y-1 text-sm text-blue-800 dark:text-blue-200">
            {incident_number && (
              <div>
                <span className="font-medium">Incident:</span> {incident_number}
              </div>
            )}
            {service_name && (
              <div>
                <span className="font-medium">Service:</span> {service_name}
              </div>
            )}
          </div>
          <p className="text-xs text-blue-700 dark:text-blue-300 mt-2">
            {new Date(message.created_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
