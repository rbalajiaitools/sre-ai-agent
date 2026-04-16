/**
 * Investigation Detail Page - full-page detail layout
 */
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2, XCircle, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useInvestigation, useCancelInvestigation } from '../hooks';
import { AgentTimeline } from './AgentTimeline';
import { RCACard } from './RCACard';
import { ResolutionPanel } from './ResolutionPanel';
import { EvidenceDrawer } from './EvidenceDrawer';
import { SaveAsKnowledgeDialog } from './SaveAsKnowledgeDialog';
import { RelatedKnowledge } from './RelatedKnowledge';
import { InvestigationStatus } from '@/types';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

export function InvestigationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: investigation, isLoading, isError } = useInvestigation(id || null);
  const cancelMutation = useCancelInvestigation(id || '');
  const [saveKnowledgeOpen, setSaveKnowledgeOpen] = useState(false);

  const handleCancel = () => {
    if (window.confirm('Are you sure you want to cancel this investigation?')) {
      cancelMutation.mutate();
    }
  };

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
    try {
      // Only show duration if investigation is completed or has been running for at least 1 second
      const start = new Date(investigation.started_at);
      const end = investigation.completed_at
        ? new Date(investigation.completed_at)
        : new Date();
      
      // Check if dates are valid
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        return '0s';
      }
      
      const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
      
      // If negative duration (clock skew), show 0s
      if (seconds < 0) return '0s';
      
      // If investigation just started (less than 1 second), show "0s"
      if (seconds < 1) return '0s';
      
      if (seconds < 60) return `${seconds}s`;
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}m ${secs}s`;
    } catch (error) {
      console.error('Error calculating duration:', error);
      return '0s';
    }
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
    <div className="h-full flex flex-col overflow-hidden bg-background">
      {/* Top bar - Fixed */}
      <div className="flex-shrink-0 border-b bg-white p-4">
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
          {(investigation.status === InvestigationStatus.INVESTIGATING || investigation.status === InvestigationStatus.STARTED) && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancel}
              disabled={cancelMutation.isPending}
            >
              <XCircle className="h-4 w-4 mr-2" aria-hidden="true" />
              {cancelMutation.isPending ? 'Canceling...' : 'Cancel Investigation'}
            </Button>
          )}
          {(investigation.status === InvestigationStatus.RESOLVED || investigation.status === InvestigationStatus.RCA_COMPLETE) && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSaveKnowledgeOpen(true)}
              className="gap-2"
            >
              <BookOpen className="h-4 w-4" aria-hidden="true" />
              Save as Knowledge
            </Button>
          )}
        </div>
        <div className="flex items-center gap-4 text-sm">
          {getStatusBadge(investigation.status)}
          <span className="text-muted-foreground">
            Started {new Date(investigation.started_at).toLocaleString()}
          </span>
          {investigation.completed_at && (
            <span className="text-muted-foreground">Duration: {getDuration()}</span>
          )}
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
              isCompleted={!!investigation.completed_at}
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

          {/* Right: Evidence Drawer + Related Knowledge (25%) */}
          <div className="col-span-3 space-y-4">
            <RelatedKnowledge
              serviceName={investigation.service_name || undefined}
              incidentNumber={investigation.incident_number}
            />
            <EvidenceDrawer agents={investigation.agent_results || []} />
          </div>
        </div>
      </div>

      {/* Save as Knowledge Dialog */}
      <SaveAsKnowledgeDialog
        investigationId={investigation.id}
        incidentNumber={investigation.incident_number}
        open={saveKnowledgeOpen}
        onClose={() => setSaveKnowledgeOpen(false)}
      />
    </div>
  );
}
