/**
 * Investigations Page - reference layout with sidebar and main content
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { Loader2, Search, Plus, MessageSquare, Trash2 } from 'lucide-react';
import { useInvestigations, useDeleteInvestigation, useBulkDeleteInvestigations } from '../hooks';
import { InvestigationFilters } from '../types';
import { Investigation } from '../types';
import { InvestigationStatus } from '@/types';
import { cn } from '@/lib/utils';

export function InvestigationsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState<InvestigationFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('All Severities');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const { data: response, isLoading, isError } = useInvestigations(filters);
  const deleteMutation = useDeleteInvestigation();
  const bulkDeleteMutation = useBulkDeleteInvestigations();

  const investigations = response?.items || [];

  // Handle selected query parameter - redirect to detail page
  useEffect(() => {
    const selectedId = searchParams.get('selected');
    if (selectedId) {
      navigate(`/investigations/${selectedId}`, { replace: true });
    }
  }, [searchParams, navigate]);

  // Filter investigations based on search query
  const filteredInvestigations = investigations.filter((inv) => {
    const matchesSearch = 
      inv.incident_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inv.service_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      '';
    return matchesSearch;
  });

  // Handle select all checkbox
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(filteredInvestigations.map(inv => inv.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  // Handle individual checkbox
  const handleSelectOne = (id: string, checked: boolean) => {
    const newSelected = new Set(selectedIds);
    if (checked) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedIds(newSelected);
  };

  // Handle bulk delete
  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    
    if (window.confirm(`Are you sure you want to delete ${selectedIds.size} investigation(s)? This action cannot be undone.`)) {
      try {
        await bulkDeleteMutation.mutateAsync(Array.from(selectedIds));
        setSelectedIds(new Set());
      } catch (error) {
        console.error('Failed to delete investigations:', error);
      }
    }
  };

  const isAllSelected = filteredInvestigations.length > 0 && selectedIds.size === filteredInvestigations.length;
  const isSomeSelected = selectedIds.size > 0 && selectedIds.size < filteredInvestigations.length;

  const getStatusBadge = (status: InvestigationStatus) => {
    const baseClasses = 'inline-flex items-center px-2.5 py-1 rounded text-xs font-medium';
    
    switch (status) {
      case InvestigationStatus.STARTED:
        return (
          <span className={cn(baseClasses, 'bg-pink-100 text-pink-700')}>
            Open
          </span>
        );
      case InvestigationStatus.INVESTIGATING:
        return (
          <span className={cn(baseClasses, 'bg-blue-100 text-blue-700')}>
            In Progress
          </span>
        );
      case InvestigationStatus.RCA_COMPLETE:
        return (
          <span className={cn(baseClasses, 'bg-gray-100 text-gray-700')}>
            Resolved
          </span>
        );
      case InvestigationStatus.RESOLVED:
        return (
          <span className={cn(baseClasses, 'bg-gray-100 text-gray-700')}>
            Resolved
          </span>
        );
      case InvestigationStatus.FAILED:
        return (
          <span className={cn(baseClasses, 'bg-red-100 text-red-700')}>
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  const getSeverityBadge = (investigation: Investigation) => {
    // Determine severity based on status and agent results
    const hasErrors = investigation.agent_results.some(r => !r.success);
    const isOpen = investigation.status === InvestigationStatus.STARTED || 
                   investigation.status === InvestigationStatus.INVESTIGATING;
    
    if (investigation.status === InvestigationStatus.FAILED || hasErrors) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded text-xs font-medium bg-red-100 text-red-700">
          Critical
        </span>
      );
    } else if (isOpen) {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded text-xs font-medium bg-orange-100 text-orange-700">
          High
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-700">
          Medium
        </span>
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Loading investigations" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-full bg-background">
        <p className="text-sm text-muted-foreground">
          Failed to load investigations. Please try again.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Investigations</h1>
            <p className="text-sm text-gray-500 mt-1">
              Manage and track active incidents and deep-dives.
            </p>
          </div>
          <div className="flex items-center gap-3">
            {selectedIds.size > 0 && (
              <button
                onClick={handleBulkDelete}
                disabled={bulkDeleteMutation.isPending}
                className="inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white text-sm font-medium rounded-md transition-colors"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                {bulkDeleteMutation.isPending ? 'Deleting...' : `Delete (${selectedIds.size})`}
              </button>
            )}
            <button
              onClick={() => navigate('/incidents')}
              className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium rounded-md transition-colors"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Investigation
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search investigations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
          </div>
          <select
            value={filters.status || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                status: e.target.value as InvestigationStatus | undefined,
              })
            }
            className="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
          >
            <option value="">All Statuses</option>
            <option value={InvestigationStatus.STARTED}>Open</option>
            <option value={InvestigationStatus.INVESTIGATING}>In Progress</option>
            <option value={InvestigationStatus.RCA_COMPLETE}>Resolved</option>
            <option value={InvestigationStatus.FAILED}>Failed</option>
          </select>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
          >
            <option>All Severities</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto bg-background">
        {filteredInvestigations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <MessageSquare className="h-16 w-16 text-gray-400 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No investigations found</h2>
            <p className="text-sm text-gray-500 max-w-md">
              {searchQuery
                ? 'Try adjusting your search or filters'
                : 'Investigations will appear here once you start investigating incidents or services.'}
            </p>
          </div>
        ) : (
          <div className="p-6">
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="bg-muted border-b border-gray-200">
                    <th className="w-12 px-6 py-3">
                      <input
                        type="checkbox"
                        checked={isAllSelected}
                        ref={(el) => {
                          if (el) el.indeterminate = isSomeSelected;
                        }}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
                        aria-label="Select all investigations"
                      />
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Title
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Severity
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Created At
                    </th>
                    <th className="text-left px-6 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Threads
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredInvestigations.map((investigation) => (
                    <tr
                      key={investigation.id}
                      className="hover:bg-muted/50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(investigation.id)}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleSelectOne(investigation.id, e.target.checked);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="h-4 w-4 rounded border-gray-300 text-teal-600 focus:ring-teal-500"
                          aria-label={`Select investigation ${investigation.incident_number}`}
                        />
                      </td>
                      <td 
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => navigate(`/investigations/${investigation.id}`)}
                      >
                        <div>
                          <div className="font-medium text-gray-900 text-sm mb-1">
                            {investigation.service_name || investigation.incident_number}
                          </div>
                          <div className="text-xs text-gray-500 line-clamp-1">
                            {investigation.incident_number}
                          </div>
                        </div>
                      </td>
                      <td 
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => navigate(`/investigations/${investigation.id}`)}
                      >
                        {getStatusBadge(investigation.status)}
                      </td>
                      <td 
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => navigate(`/investigations/${investigation.id}`)}
                      >
                        {getSeverityBadge(investigation)}
                      </td>
                      <td 
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => navigate(`/investigations/${investigation.id}`)}
                      >
                        <span className="text-sm text-gray-600">
                          {format(new Date(investigation.started_at), 'MMM dd, hh:mm a')}
                        </span>
                      </td>
                      <td 
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => navigate(`/investigations/${investigation.id}`)}
                      >
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-700 text-xs font-medium">
                          {investigation.agent_results.length}
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
  );
}
