/**
 * Incidents Page - main incidents screen
 */
import { useState, useEffect, useRef } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIncidents, useRefreshIncidents, useStartInvestigation } from '../hooks';
import { IncidentFilter, ServiceNowIncident } from '../types';
import { IncidentFilters } from './IncidentFilters';
import { IncidentList } from './IncidentList';
import { IncidentDetailPanel } from './IncidentDetailPanel';
import { IncidentPriority, IncidentState } from '@/types';
import { useAppStore } from '@/stores/appStore';
import { cn } from '@/lib/utils';

export function IncidentsPage() {
  const [filter, setFilter] = useState<Partial<IncidentFilter>>({
    priorities: [],
    states: [],
    search: '',
    assignment_group: '',
  });
  const [selectedIncident, setSelectedIncident] = useState<ServiceNowIncident | null>(null);
  const listContainerRef = useRef<HTMLDivElement>(null);
  const [listHeight, setListHeight] = useState(600);

  const { data: incidents, isLoading, isError, dataUpdatedAt } = useIncidents(filter);
  const refreshMutation = useRefreshIncidents();
  const investigateMutation = useStartInvestigation();
  const { setActiveChatId } = useAppStore();

  // Calculate list height based on container
  useEffect(() => {
    const updateHeight = () => {
      if (listContainerRef.current) {
        const rect = listContainerRef.current.getBoundingClientRect();
        setListHeight(window.innerHeight - rect.top);
      }
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);

  const handleRefresh = () => {
    refreshMutation.mutate();
  };

  const handleInvestigate = (incidentNumber: string) => {
    investigateMutation.mutate(incidentNumber);
  };

  const handleSendToChat = () => {
    if (!selectedIncident) return;
    // TODO: Implement send to active chat without starting investigation
    // For now, just navigate to chat
    setActiveChatId(null);
  };

  // Get unique assignment groups for filter
  const assignmentGroups = incidents
    ? Array.from(new Set(incidents.map((i) => i.assignment_group).filter(Boolean)))
    : [];

  // Check if there are any P1 incidents
  const hasP1Incidents = incidents?.some(
    (i) => i.priority === IncidentPriority.P1 && i.state !== IncidentState.RESOLVED
  );

  // Get open incidents count
  const openIncidentsCount = incidents?.filter(
    (i) => i.state !== IncidentState.RESOLVED && i.state !== IncidentState.CLOSED
  ).length || 0;

  const lastSyncedText = dataUpdatedAt
    ? formatDistanceToNow(new Date(dataUpdatedAt), { addSuffix: true })
    : 'Never';

  return (
    <div className="flex h-full">
      {/* Left panel - Incident list */}
      <div className={cn('flex flex-col', selectedIncident ? 'w-2/3' : 'w-full')}>
        {/* Top bar */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold">Incidents</h1>
            {openIncidentsCount > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-sm font-medium">
                {openIncidentsCount}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="text-sm text-muted-foreground">
              {refreshMutation.isPending ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Syncing with ServiceNow...
                </span>
              ) : refreshMutation.isError ? (
                <span className="text-destructive">Sync failed</span>
              ) : (
                <span>Last synced: {lastSyncedText}</span>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshMutation.isPending}
              aria-label="Refresh incidents"
            >
              <RefreshCw
                className={cn(
                  'h-4 w-4',
                  refreshMutation.isPending && 'animate-spin'
                )}
                aria-hidden="true"
              />
            </Button>
          </div>
        </div>

        {/* Filters */}
        <IncidentFilters
          filter={filter}
          onFilterChange={setFilter}
          hasP1Incidents={hasP1Incidents}
          assignmentGroups={assignmentGroups}
        />

        {/* Incident list */}
        <div ref={listContainerRef} className="flex-1">
          <IncidentList
            incidents={incidents}
            isLoading={isLoading}
            isError={isError}
            selectedIncidentId={selectedIncident?.sys_id || null}
            onIncidentSelect={setSelectedIncident}
            onInvestigate={handleInvestigate}
            height={listHeight}
          />
        </div>
      </div>

      {/* Right panel - Incident detail */}
      {selectedIncident && (
        <div className="w-1/3">
          <IncidentDetailPanel
            incident={selectedIncident}
            onClose={() => setSelectedIncident(null)}
            onInvestigate={() => handleInvestigate(selectedIncident.number)}
            onSendToChat={handleSendToChat}
            isInvestigating={investigateMutation.isPending}
            investigateError={investigateMutation.isError}
          />
        </div>
      )}
    </div>
  );
}
