/**
 * Investigation Detail Page - full-page detail layout
 */
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useInvestigation } from '../hooks';
import { AgentTimeline } from './AgentTimeline';
import { RCACard } from './RCACard';
import { ResolutionPanel } from './ResolutionPanel';
import { EvidenceDrawer } from './EvidenceDrawer';
import { InvestigationStatus } from '@/types';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

export function InvestigationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: investigation, isLoading, isError } = useInvestigation(id || null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Loading investigation" />
      </div>
    );
  }

  if (isError || !investigation) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <p className="text-lg font-medium mb-2">Investigation not found</p>
        <p className="text-sm text-muted-foreground mb-4">
          The investigation you're looking for doesn't exist or has been removed.
        </p>
        <Button onClick={() => navigate('/investigations')}>
          Back to Investigations
        </Button>
      </div>
    );
  }

  const getStatusBadge = (status: InvestigationStatus) => {
    switch (status) {
      case InvestigationStatus.STARTED:
      case InvestigationStatus.INVESTIGATING:
        return (
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', statusColors.info.bg, statusColors.info.text)}>
            {status === InvestigationStatus.STARTED ? 'Started' : 'Investigating'}
          </span>
        );
      case InvestigationStatus.RCA_COMPLETE:
        return (
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', statusColors.success.bg, statusColors.success.text)}>
            RCA Complete
          </span>
        );
      case InvestigationStatus.RESOLVED:
        return (
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', statusColors.success.bg, statusColors.success.text)}>
            Resolved
          </span>
        );
      case InvestigationStatus.FAILED:
        return (
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', statusColors.error.bg, statusColors.error.text)}>
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  const getDuration = () => {
    const start = new Date(investigation.started_at);
    const end = investigation.completed_at
      ? new Date(investigation.completed_at)
      : new Date();
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const elapsedSeconds = investigation.completed_at
    ? Math.floor(
        (new Date(investigation.completed_at).getTime() -
          new Date(investigation.started_at).getTime()) /
          1000
      )
    : Math.floor(
        (new Date().getTime() - new Date(investigation.started_at).getTime()) /
          1000
      );

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Top bar - Fixed */}
      <div className="flex-shrink-0 border-b bg-background p-4">
        <div className="flex items-center gap-4 mb-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/investigations')}
            aria-label="Back to investigations"
          >
            <ArrowLeft className="h-4 w-4 mr-2" aria-hidden="true" />
            Back
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold font-mono">
                {investigation.incident_number}
              </h1>
              {investigation.service_name && (
                <>
                  <span className="text-muted-foreground">•</span>
                  <span className="text-muted-foreground">
                    {investigation.service_name}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm">
          {getStatusBadge(investigation.status)}
          <span className="text-muted-foreground">
            Started {new Date(investigation.started_at).toLocaleString()}
          </span>
          <span className="text-muted-foreground">Duration: {getDuration()}</span>
        </div>
      </div>

      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto">
        <div className="grid grid-cols-12 gap-4 p-4">
          {/* Left: Agent Timeline (30%) */}
          <div className="col-span-3">
            <AgentTimeline
              agents={investigation.agent_results || []}
              elapsedSeconds={elapsedSeconds}
            />
          </div>

          {/* Center: RCA + Resolution (45%) */}
          <div className="col-span-6 space-y-6">
            {investigation.rca ? (
              <RCACard rca={investigation.rca} />
            ) : (
              <div className="p-6 rounded-lg border bg-card text-center">
                <p className="text-muted-foreground">
                  {investigation.status === InvestigationStatus.INVESTIGATING
                    ? 'Investigation in progress...'
                    : 'No RCA available'}
                </p>
              </div>
            )}

            {investigation.resolution && (
              <ResolutionPanel
                resolution={investigation.resolution}
                investigationId={investigation.id}
                approvedBy={investigation.approved_by}
                approvedAt={investigation.approved_at}
              />
            )}
          </div>

          {/* Right: Evidence Drawer (25%) */}
          <div className="col-span-3">
            <EvidenceDrawer agents={investigation.agent_results || []} />
          </div>
        </div>
      </div>
    </div>
  );
}
