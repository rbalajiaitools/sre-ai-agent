/**
 * Incidents Page - Avyal.ai style
 */
import { useState, useEffect, useRef } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIncidents, useRefreshIncidents } from '../hooks';
import { IncidentFilter, ServiceNowIncident } from '../types';
import { IncidentFilters } from './IncidentFilters';
import { IncidentList } from './IncidentList';
import { IncidentDetailPanel } from './IncidentDetailPanel';
import { IncidentPriority, IncidentState } from '@/types';
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

  // Fetch all incidents without filter
  const { data: allIncidents, isLoading, isError, dataUpdatedAt } = useIncidents();
  const refreshMutation = useRefreshIncidents();

  // Apply filters client-side
  const incidents = allIncidents?.filter((incident) => {
    // Priority filter
    if (filter.priorities && filter.priorities.length > 0) {
      const incidentPriority = String(incident.priority);
      if (!filter.priorities.includes(incidentPriority as IncidentPriority)) {
        return false;
      }
    }

    // State filter
    if (filter.states && filter.states.length > 0) {
      const incidentState = String(incident.state);
      if (!filter.states.includes(incidentState)) {
        return false;
      }
    }

    // Search filter
    if (filter.search) {
      const searchLower = filter.search.toLowerCase();
      const matchesSearch =
        incident.number.toLowerCase().includes(searchLower) ||
        incident.short_description.toLowerCase().includes(searchLower) ||
        (incident.description && incident.description.toLowerCase().includes(searchLower));
      if (!matchesSearch) {
        return false;
      }
    }

    // Assignment group filter
    if (filter.assignment_group && incident.assignment_group !== filter.assignment_group) {
      return false;
    }

    return true;
  });

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

  // Get unique assignment groups for filter
  const assignmentGroups = allIncidents
    ? Array.from(new Set(allIncidents.map((i) => i.assignment_group).filter(Boolean)))
    : [];

  // Check if there are any P1 incidents
  const hasP1Incidents = allIncidents?.some(
    (i) => i.priority === IncidentPriority.P1 && i.state !== IncidentState.RESOLVED
  );

  // Get open incidents count
  const openIncidentsCount = allIncidents?.filter(
    (i) => i.state !== IncidentState.RESOLVED && i.state !== IncidentState.CLOSED
  ).length || 0;

  const lastSyncedText = dataUpdatedAt
    ? formatDistanceToNow(new Date(dataUpdatedAt), { addSuffix: true })
    : 'Never';

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <div className="bg-white border-b border-border px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-foreground">Incidents</h1>
            {openIncidentsCount > 0 && (
              <span className="px-2.5 py-1 rounded-full bg-red-100 text-red-700 text-xs font-semibold">
                {openIncidentsCount} open
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              {refreshMutation.isPending ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Syncing...
                </span>
              ) : refreshMutation.isError ? (
                <span className="text-destructive">Sync failed</span>
              ) : (
                <span>Last synced {lastSyncedText}</span>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshMutation.isPending}
              className="gap-2"
            >
              <RefreshCw
                className={cn(
                  'h-4 w-4',
                  refreshMutation.isPending && 'animate-spin'
                )}
              />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel - Incident list */}
        <div className={cn('flex flex-col bg-white', selectedIncident ? 'w-2/3' : 'w-full')}>
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
              height={listHeight}
            />
          </div>
        </div>

        {/* Right panel - Incident detail */}
        {selectedIncident && (
          <div className="w-1/3 border-l border-border bg-white">
            <IncidentDetailPanel
              incident={selectedIncident}
              onClose={() => setSelectedIncident(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
