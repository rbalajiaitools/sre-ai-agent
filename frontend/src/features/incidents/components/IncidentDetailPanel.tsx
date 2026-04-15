/**
 * Incident Detail Panel - right panel with incident details
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, ExternalLink } from 'lucide-react';
import { ServiceNowIncident } from '../types';
import { IncidentPriority } from '@/types';
import { Button } from '@/components/ui/button';
import { InvestigationStatusCard } from './InvestigationStatusCard';
import { IncidentMetadata } from './IncidentMetadata';
import { IncidentWorkNotes } from './IncidentWorkNotes';
import { useStartInvestigation } from '../hooks';
import { useCreateThread } from '@/features/chat/hooks';
import { ChatContext } from '@/features/chat/types';
import { cn } from '@/lib/utils';
import { priorityColors } from '@/lib/colors';

interface IncidentDetailPanelProps {
  incident: ServiceNowIncident;
  onClose: () => void;
}

export function IncidentDetailPanel({
  incident,
  onClose,
}: IncidentDetailPanelProps) {
  const navigate = useNavigate();
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  
  const startInvestigationMutation = useStartInvestigation();
  const createThreadMutation = useCreateThread();

  const handleInvestigate = () => {
    startInvestigationMutation.mutate(incident.number);
  };

  const handleSendToChat = () => {
    const context: ChatContext = {
      incident: {
        sys_id: incident.sys_id,
        number: incident.number,
        short_description: incident.short_description,
        priority: incident.priority,
      },
    };
    createThreadMutation.mutate(context);
  };

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

  const isDescriptionLong = incident.description.length > 300;

  return (
    <div className="h-full flex flex-col border-l bg-background animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold font-mono">{incident.number}</h2>
        <button
          onClick={onClose}
          className="p-1 hover:bg-muted rounded transition-colors"
          aria-label="Close detail panel"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Badges and timestamp */}
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={cn(
              'px-2 py-1 rounded text-xs font-medium',
              getPriorityColor(incident.priority)
            )}
          >
            Priority {incident.priority}
          </span>
          <span className="px-2 py-1 rounded bg-muted text-xs font-medium">
            {getStateLabel(incident.state)}
          </span>
          <span className="text-xs text-muted-foreground">
            Opened {new Date(incident.opened_at).toLocaleString()}
          </span>
        </div>

        {/* Short description */}
        <div>
          <h3 className="text-base font-semibold mb-2">
            {incident.short_description}
          </h3>
        </div>

        {/* Full description */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-2">
            Description
          </h4>
          <div className="text-sm leading-relaxed">
            {isDescriptionLong && !descriptionExpanded ? (
              <>
                <p>{incident.description.slice(0, 300)}...</p>
                <button
                  onClick={() => setDescriptionExpanded(true)}
                  className="text-primary hover:underline text-xs mt-1"
                  aria-label="Show full description"
                >
                  Show more
                </button>
              </>
            ) : (
              <p>{incident.description}</p>
            )}
          </div>
        </div>

        {/* Metadata grid */}
        <IncidentMetadata incident={incident} />

        {/* Work notes */}
        <IncidentWorkNotes workNotes={incident.work_notes} />

        {/* Investigation status card */}
        {incident.investigation_status && incident.investigation_id && (
          <InvestigationStatusCard
            investigationId={incident.investigation_id}
            status={incident.investigation_status}
            chatThreadId={incident.investigation_id}
          />
        )}
      </div>

      {/* Action buttons */}
      <div className="p-4 border-t space-y-2">
        {startInvestigationMutation.isError && (
          <p className="text-sm text-destructive mb-2">
            Failed to start investigation. Please try again.
          </p>
        )}
        <Button
          onClick={handleInvestigate}
          disabled={startInvestigationMutation.isPending || !!incident.investigation_status}
          className="w-full"
        >
          {startInvestigationMutation.isPending ? 'Starting Investigation...' : 'Investigate'}
        </Button>
        <div className="flex gap-2">
          <Button 
            onClick={handleSendToChat} 
            variant="outline" 
            className="flex-1"
            disabled={createThreadMutation.isPending}
          >
            Send to Chat
          </Button>
          <Button
            variant="ghost"
            className="flex-1"
            onClick={() => {
              // Open ServiceNow in new tab
              window.open(
                `https://servicenow.com/incident/${incident.number}`,
                '_blank'
              );
            }}
          >
            <ExternalLink className="h-4 w-4 mr-2" aria-hidden="true" />
            ServiceNow
          </Button>
        </div>
      </div>

      {/* Loading overlay when starting investigation */}
      {startInvestigationMutation.isPending && (
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="text-center space-y-4">
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
            <div className="space-y-2">
              <p className="text-lg font-semibold">Starting Investigation</p>
              <p className="text-sm text-muted-foreground">
                Initializing 5 specialist agents...
              </p>
              <p className="text-xs text-muted-foreground">
                This may take 15-20 seconds
              </p>
            </div>
          </div>
        </div>
      )}
