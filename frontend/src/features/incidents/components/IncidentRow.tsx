/**
 * Incident Row - compact row in incident list
 */
import { formatDistanceToNow } from 'date-fns';
import { Loader2, CheckCircle2 } from 'lucide-react';
import { ServiceNowIncident } from '../types';
import { IncidentPriority, InvestigationStatus } from '@/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { priorityColors, statusColors } from '@/lib/colors';

interface IncidentRowProps {
  incident: ServiceNowIncident;
  isSelected: boolean;
  onClick: () => void;
}

export function IncidentRow({
  incident,
  isSelected,
  onClick,
}: IncidentRowProps) {
  const getPriorityColor = (priority: IncidentPriority) => {
    const key = `p${priority}` as keyof typeof priorityColors;
    return priorityColors[key] || priorityColors.p4;
  };

  const getStateLabel = (state: string) => {
    const stateMap: Record<string, string> = {
      '1': 'New',
      '2': 'In Progress',
      '3': 'On Hold',
      '6': 'Resolved',
      '7': 'Closed',
      '8': 'Canceled',
    };
    return stateMap[state] || state;
  };

  const renderInvestigationStatus = () => {
    if (!incident.investigation_status) {
      return null;
    }

    const status = incident.investigation_status;

    if (
      status === InvestigationStatus.STARTED ||
      status === InvestigationStatus.INVESTIGATING
    ) {
      return (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
          <span>Investigating...</span>
        </div>
      );
    }

    if (status === InvestigationStatus.RCA_COMPLETE) {
      return (
        <Button
          size="sm"
          variant="ghost"
          onClick={onClick}
          className={cn('h-7 text-xs', statusColors.success.text)}
        >
          <CheckCircle2 className="h-3 w-3 mr-1" aria-hidden="true" />
          View RCA
        </Button>
      );
    }

    if (status === InvestigationStatus.RESOLVED) {
      return (
        <span className="text-xs text-muted-foreground px-2 py-1 rounded bg-muted">
          Resolved
        </span>
      );
    }

    return null;
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-4 border-b hover:bg-muted/50 transition-colors',
        isSelected && 'bg-muted'
      )}
      aria-current={isSelected ? 'true' : undefined}
    >
      <div className="flex items-center gap-3">
        {/* Priority badge */}
        <span
          className={cn(
            'px-2 py-0.5 rounded text-xs font-medium flex-shrink-0',
            getPriorityColor(incident.priority)
          )}
        >
          P{incident.priority}
        </span>

        {/* Incident number */}
        <span className="font-mono text-sm font-medium flex-shrink-0">
          {incident.number}
        </span>

        {/* Description and metadata */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate mb-1">
            {incident.short_description}
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {incident.cmdb_ci && (
              <span className="px-2 py-0.5 rounded bg-muted truncate max-w-[150px]">
                {incident.cmdb_ci}
              </span>
            )}
            <span className="px-2 py-0.5 rounded bg-muted">
              {getStateLabel(incident.state)}
            </span>
            <span>
              {formatDistanceToNow(new Date(incident.opened_at), {
                addSuffix: true,
              })}
            </span>
          </div>
        </div>

        {/* Investigation status */}
        <div className="flex-shrink-0">{renderInvestigationStatus()}</div>
      </div>
    </button>
  );
}
