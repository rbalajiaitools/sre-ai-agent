/**
 * Investigation Start Message
 */
import { PlayCircle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ChatMessage } from '../../types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface InvestigationStartMessageProps {
  message: ChatMessage;
}

export function InvestigationStartMessage({
  message,
}: InvestigationStartMessageProps) {
  const navigate = useNavigate();
  const { investigation_id, incident_number, incident, service_name } = message.metadata as {
    investigation_id?: string;
    incident_number?: string;
    incident?: any;
    service_name?: string;
  };

  const handleViewInvestigation = () => {
    if (investigation_id) {
      navigate(`/investigations?selected=${investigation_id}`);
    }
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
            Investigation Started
          </p>
          <div className={cn('mt-2 space-y-1 text-sm', statusColors.info.textMuted)}>
            {incident_number && (
              <div>
                <span className="font-medium">Incident:</span> {incident_number}
              </div>
            )}
            {incident?.short_description && (
              <div>
                <span className="font-medium">Description:</span> {incident.short_description}
              </div>
            )}
            {service_name && (
              <div>
                <span className="font-medium">Service:</span> {service_name}
              </div>
            )}
          </div>
          <p className="mt-3 text-sm">
            {message.content}
          </p>
          {investigation_id && (
            <Button
              onClick={handleViewInvestigation}
              className="mt-4 gap-2"
              size="sm"
            >
              View Investigation Progress
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}
          <p className={cn('text-xs mt-2', statusColors.info.textMuted)}>
            {new Date(message.created_at).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
