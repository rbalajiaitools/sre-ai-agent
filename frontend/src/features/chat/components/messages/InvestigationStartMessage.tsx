/**
 * Investigation Start Message
 */
import { PlayCircle } from 'lucide-react';
import { ChatMessage } from '../../types';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

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
    <div className={cn('rounded-lg border p-4', statusColors.info.bg, statusColors.info.border)}>
      <div className="flex items-start gap-3">
        <PlayCircle
          className={cn('h-5 w-5 mt-0.5', statusColors.info.icon)}
          aria-hidden="true"
        />
        <div className="flex-1">
          <p className={cn('font-medium', statusColors.info.text)}>
            Investigation started
          </p>
          <div className={cn('mt-2 space-y-1 text-sm', statusColors.info.textMuted)}>
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
          <p className={cn('text-xs mt-2', statusColors.info.textMuted)}>
            {new Date(message.created_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
