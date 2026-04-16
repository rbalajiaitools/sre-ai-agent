/**
 * Incidents Page - Split-panel layout with table and detail panel
 */
import { useState } from 'react';
import { format } from 'date-fns';
import { RefreshCw, Loader2, Search, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useIncidents, useRefreshIncidents } from '../hooks';
import { ServiceNowIncident } from '../types';
import { IncidentPriority, IncidentState } from '@/types';
import { IncidentDetailPanel } from './IncidentDetailPanel';
import { cn } from '@/lib/utils';

export function IncidentsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [stateFilter, setStateFilter] = useState<string>('');
  const [selectedIncident, setSelectedIncident] = useState<ServiceNowIncident | null>(null);

  const { data: allIncidents, isLoading, isError } = useIncidents();
  const refreshMutation = useRefreshIncidents();

  // Apply filters
  const filteredIncidents = allIncidents?.filter((incident) => {
    const matchesSearch = 
      incident.number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.short_description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (incident.cmdb_ci && incident.cmdb_ci.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesPriority = !priorityFilter || String(incident.priority) === priorityFilter;
    const matchesState = !stateFilter || String(incident.state) === stateFilter;
    
    return matchesSearch && matchesPriority && matchesState;
  }) || [];

  const handleRefresh = () => {
    refreshMutation.mutate();
  };

  const handleIncidentClick = (incident: ServiceNowIncident) => {
    setSelectedIncident(incident);
  };

  const handleCloseDetail = () => {
    setSelectedIncident(null);
  };

  const getPriorityBadge = (priority: IncidentPriority) => {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    switch (priority) {
      case IncidentPriority.P1:
        return (
          <span className={cn(baseClasses, 'bg-red-100 text-red-800')}>
            Critical
          </span>
        );
      case IncidentPriority.P2:
        return (
          <span className={cn(baseClasses, 'bg-orange-100 text-orange-800')}>
            High
          </span>
        );
      case IncidentPriority.P3:
        return (
          <span className={cn(baseClasses, 'bg-yellow-100 text-yellow-800')}>
            Medium
          </span>
        );
      case IncidentPriority.P4:
      case IncidentPriority.P5:
        return (
          <span className={cn(baseClasses, 'bg-gray-100 text-gray-800')}>
            Low
          </span>
        );
      default:
        return null;
    }
  };

  const getStateBadge = (state: IncidentState) => {
    const baseClasses = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium';
    
    switch (state) {
      case IncidentState.NEW:
        return (
          <span className={cn(baseClasses, 'bg-blue-100 text-blue-800')}>
            New
          </span>
        );
      case IncidentState.IN_PROGRESS:
        return (
          <span className={cn(baseClasses, 'bg-purple-100 text-purple-800')}>
            In Progress
          </span>
        );
      case IncidentState.ON_HOLD:
        return (
          <span className={cn(baseClasses, 'bg-yellow-100 text-yellow-800')}>
            On Hold
          </span>
        );
      case IncidentState.RESOLVED:
        return (
          <span className={cn(baseClasses, 'bg-green-100 text-green-800')}>
            Resolved
          </span>
        );
      case IncidentState.CLOSED:
        return (
          <span className={cn(baseClasses, 'bg-gray-100 text-gray-800')}>
            Closed
          </span>
        );
      case IncidentState.CANCELED:
        return (
          <span className={cn(baseClasses, 'bg-gray-100 text-gray-800')}>
            Canceled
          </span>
        );
      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Loading incidents" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <p className="text-sm text-muted-foreground">
          Failed to load incidents. Please try again.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex bg-background">
      {/* Left Panel - Table */}
      <div className={cn(
        "flex flex-col transition-all duration-200",
        selectedIncident ? "w-2/3" : "w-full"
      )}>
        {/* Header */}
        <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Incidents</h1>
            <p className="text-sm text-gray-500 mt-1">
              Manage and track ServiceNow incidents
            </p>
          </div>
          <Button
            onClick={handleRefresh}
            disabled={refreshMutation.isPending}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw
              className={cn(
                'h-4 w-4',
                refreshMutation.isPending && 'animate-spin'
              )}
            />
            {refreshMutation.isPending ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search incidents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
          </div>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
          >
            <option value="">All Priorities</option>
            <option value="1">Critical (P1)</option>
            <option value="2">High (P2)</option>
            <option value="3">Medium (P3)</option>
            <option value="4">Low (P4)</option>
            <option value="5">Planning (P5)</option>
          </select>
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
          >
            <option value="">All States</option>
            <option value="1">New</option>
            <option value="2">In Progress</option>
            <option value="3">On Hold</option>
            <option value="6">Resolved</option>
            <option value="7">Closed</option>
            <option value="8">Canceled</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto bg-background">
        {filteredIncidents.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <AlertCircle className="h-16 w-16 text-gray-400 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No incidents found</h2>
            <p className="text-sm text-gray-500 max-w-md">
              {searchQuery || priorityFilter || stateFilter
                ? 'Try adjusting your search or filters'
                : 'No incidents available. Click Refresh to sync from ServiceNow.'}
            </p>
          </div>
        ) : (
          <div className="p-6">
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="bg-muted border-b border-gray-200">
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Number
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      State
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      CI
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Opened
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredIncidents.map((incident) => (
                    <tr
                      key={incident.sys_id}
                      onClick={() => handleIncidentClick(incident)}
                      className={cn(
                        "hover:bg-muted/50 cursor-pointer transition-colors",
                        selectedIncident?.sys_id === incident.sys_id && "bg-muted/50"
                      )}
                    >
                      <td className="px-6 py-4">
                        <span className="font-mono text-sm font-medium text-gray-900">
                          {incident.number}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="max-w-md">
                          <p className="text-sm text-gray-900 truncate">
                            {incident.short_description}
                          </p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getPriorityBadge(incident.priority)}
                      </td>
                      <td className="px-6 py-4">
                        {getStateBadge(incident.state)}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-600">
                          {incident.cmdb_ci || '-'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-600">
                          {format(new Date(incident.opened_at), 'MMM dd, hh:mm a')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
      </div>

      {/* Right Panel - Detail */}
      {selectedIncident && (
        <div className="w-1/3 border-l">
          <IncidentDetailPanel
            incident={selectedIncident}
            onClose={handleCloseDetail}
          />
        </div>
      )}
    </div>
  );
}
