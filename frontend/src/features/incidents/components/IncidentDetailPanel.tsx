/**
 * Incident Detail Panel - right panel with incident details
 */
import { useState } from 'react';
import { X, ExternalLink, ChevronDown, ChevronRight } from 'lucide-react';
import { ServiceNowIncident } from '../types';
import { IncidentPriority } from '@/types';
import { Button } from '@/components/ui/button';
import { InvestigationStatusCard } from './InvestigationStatusCard';
import { cn } from '@/lib/utils';
import { priorityColors } from '@/lib/colors';

interface IncidentDetailPanelProps {
  incident: ServiceNowIncident;
  onClose: () => void;
  onInvestigate: () => void;
  onSendToChat: () => void;
  isInvestigating: boolean;
}

export function IncidentDetailPanel({
  incident,
  onClose,
  onInvestigate,
  onSendToChat,
  isInvestigating,
}: IncidentDetailPanelProps) {
  const [workNotesExpanded, setWorkNotesExpanded] = useState(false);
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);

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

  const visibleWorkNotes = workNotesExpanded
    ? incident.work_notes
    : incident.work_notes.slice(0, 3);

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
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-3">
            Details
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground mb-1">CI Name</p>
              <p className="font-medium">{incident.cmdb_ci || 'N/A'}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Assignment Group</p>
              <p className="font-medium">{incident.assignment_group || 'N/A'}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Category</p>
              <p className="font-medium">{incident.category || 'N/A'}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Subcategory</p>
              <p className="font-medium">{incident.subcategory || 'N/A'}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Assigned To</p>
              <p className="font-medium">{incident.assigned_to || 'Unassigned'}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-1">Updated At</p>
              <p className="font-medium">
                {new Date(incident.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Work notes */}
        {incident.work_notes.length > 0 && (
          <div>
            <button
              onClick={() => setWorkNotesExpanded(!workNotesExpanded)}
              className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors mb-3"
              aria-expanded={workNotesExpanded}
            >
              {workNotesExpanded ? (
                <ChevronDown className="h-4 w-4" aria-hidden="true" />
              ) : (
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              )}
              Work Notes ({incident.work_notes.length})
            </button>
            {(workNotesExpanded || incident.work_notes.length <= 3) && (
              <div className="space-y-2">
                {visibleWorkNotes.map((note, index) => (
                  <div
                    key={index}
                    className="p-3 rounded-md bg-muted text-sm leading-relaxed"
                  >
                    {note}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

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
        <Button
          onClick={onInvestigate}
          disabled={isInvestigating || !!incident.investigation_status}
          className="w-full"
        >
          {isInvestigating ? 'Starting Investigation...' : 'Investigate'}
        </Button>
        <div className="flex gap-2">
          <Button onClick={onSendToChat} variant="outline" className="flex-1">
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
    </div>
  );
}
