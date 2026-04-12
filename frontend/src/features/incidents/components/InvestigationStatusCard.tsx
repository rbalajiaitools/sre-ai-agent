/**
 * Investigation Status Card - compact status display in detail panel
 */
import { CheckCircle2, Loader2, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { InvestigationStatus } from '@/types';
import { AgentProgressMini } from './AgentProgressMini';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface InvestigationStatusCardProps {
  investigationId: string;
  status: InvestigationStatus;
  chatThreadId?: string;
  rootCauseSummary?: string;
  resolutionSummary?: string;
  resolvedAt?: string;
  agentsRunning?: string[];
  agentsCompleted?: string[];
  elapsedSeconds?: number;
}

export function InvestigationStatusCard({
  investigationId,
  status,
  chatThreadId,
  rootCauseSummary,
  resolutionSummary,
  resolvedAt,
  agentsRunning = [],
  agentsCompleted = [],
  elapsedSeconds = 0,
}: InvestigationStatusCardProps) {
  const isInvestigating =
    status === InvestigationStatus.STARTED ||
    status === InvestigationStatus.INVESTIGATING;
  const isComplete = status === InvestigationStatus.RCA_COMPLETE;
  const isResolved = status === InvestigationStatus.RESOLVED;

  return (
    <div className="rounded-lg border bg-card p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {isInvestigating && (
            <Loader2
              className={cn('h-4 w-4 animate-spin', statusColors.info.icon)}
              aria-hidden="true"
            />
          )}
          {isComplete && (
            <CheckCircle2
              className={cn('h-4 w-4', statusColors.success.icon)}
              aria-hidden="true"
            />
          )}
          {isResolved && (
            <CheckCircle2
              className={cn('h-4 w-4', statusColors.success.icon)}
              aria-hidden="true"
            />
          )}
          <span className="text-sm font-medium">
            {isInvestigating && 'Investigation in Progress'}
            {isComplete && 'Root Cause Identified'}
            {isResolved && 'Resolved'}
          </span>
        </div>
        {chatThreadId && (
          <Link
            to={`/chat/${chatThreadId}`}
            className="text-xs text-primary hover:underline inline-flex items-center gap-1"
          >
            View in chat
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </Link>
        )}
      </div>

      {/* Content based on status */}
      {isInvestigating && (
        <AgentProgressMini
          agentsRunning={agentsRunning}
          agentsCompleted={agentsCompleted}
          elapsedSeconds={elapsedSeconds}
        />
      )}

      {isComplete && rootCauseSummary && (
        <p className="text-sm text-muted-foreground">{rootCauseSummary}</p>
      )}

      {isResolved && (
        <div className="space-y-2">
          {resolutionSummary && (
            <p className="text-sm text-muted-foreground">{resolutionSummary}</p>
          )}
          {resolvedAt && (
            <p className="text-xs text-muted-foreground">
              Closed {new Date(resolvedAt).toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
