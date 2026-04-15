/**
 * Investigations Page - table layout showing all investigations
 */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { Loader2, FileSearch } from 'lucide-react';
import { useInvestigations } from '../hooks';
import { InvestigationFilters } from '../types';
import { InvestigationStatus } from '@/types';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

export function InvestigationsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState<InvestigationFilters>({});
  const { data: response, isLoading, isError } = useInvestigations(filters);

  const investigations = response?.items || [];

  // Handle selected query parameter - redirect to detail page
  useEffect(() => {
    const selectedId = searchParams.get('selected');
    if (selectedId) {
      navigate(`/investigations/${selectedId}`, { replace: true });
    }
  }, [searchParams, navigate]);

  const getStatusBadge = (status: InvestigationStatus) => {
    switch (status) {
      case InvestigationStatus.STARTED:
      case InvestigationStatus.INVESTIGATING:
        return (
          <span className={cn('px-2 py-1 rounded text-xs font-medium', statusColors.info.bg, statusColors.info.text)}>
            {status === InvestigationStatus.STARTED ? 'Started' : 'Investigating'}
          </span>
        );
      case InvestigationStatus.RCA_COMPLETE:
        return (
          <span className={cn('px-2 py-1 rounded text-xs font-medium', statusColors.success.bg, statusColors.success.text)}>
            RCA Complete
          </span>
        );
      case InvestigationStatus.RESOLVED:
        return (
          <span className={cn('px-2 py-1 rounded text-xs font-medium', statusColors.success.bg, statusColors.success.text)}>
            Resolved
          </span>
        );
      case InvestigationStatus.FAILED:
        return (
          <span className={cn('px-2 py-1 rounded text-xs font-medium', statusColors.error.bg, statusColors.error.text)}>
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  const getDuration = (startedAt: string, completedAt: string | null) => {
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    return `${mins}m`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Loading investigations" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-muted-foreground">
          Failed to load investigations. Please try again.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b p-4">
        <h1 className="text-2xl font-semibold">Investigations</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review completed and in-progress investigations
        </p>
      </div>

      {/* Filters */}
      <div className="border-b p-4">
        <div className="flex items-center gap-3">
          <select
            value={filters.status || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                status: e.target.value as InvestigationStatus | undefined,
              })
            }
            className="px-3 py-2 rounded-md border bg-background text-sm"
            aria-label="Filter by status"
          >
            <option value="">All Statuses</option>
            <option value={InvestigationStatus.INVESTIGATING}>Investigating</option>
            <option value={InvestigationStatus.RCA_COMPLETE}>RCA Complete</option>
            <option value={InvestigationStatus.RESOLVED}>Resolved</option>
            <option value={InvestigationStatus.FAILED}>Failed</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {investigations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <FileSearch className="h-16 w-16 text-muted-foreground mb-4" aria-hidden="true" />
            <h2 className="text-xl font-semibold mb-2">No investigations found</h2>
            <p className="text-sm text-muted-foreground max-w-md">
              Investigations will appear here once you start investigating incidents from the Incidents page.
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-muted/50 sticky top-0">
              <tr>
                <th className="text-left p-4 text-sm font-medium">Incident</th>
                <th className="text-left p-4 text-sm font-medium">Service</th>
                <th className="text-left p-4 text-sm font-medium">Status</th>
                <th className="text-left p-4 text-sm font-medium">Agents Run</th>
                <th className="text-left p-4 text-sm font-medium">Started</th>
                <th className="text-left p-4 text-sm font-medium">Duration</th>
              </tr>
            </thead>
            <tbody>
              {investigations.map((investigation) => (
                <tr
                  key={investigation.id}
                  onClick={() => navigate(`/investigations/${investigation.id}`)}
                  className="border-b hover:bg-muted/50 cursor-pointer transition-colors"
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(`/investigations/${investigation.id}`);
                    }
                  }}
                  aria-label={`View investigation ${investigation.incident_number}`}
                >
                  <td className="p-4">
                    <span className="font-mono text-sm font-medium">
                      {investigation.incident_number}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm">{investigation.service_name || 'N/A'}</span>
                  </td>
                  <td className="p-4">{getStatusBadge(investigation.status)}</td>
                  <td className="p-4">
                    <span className="text-sm">{investigation.agent_results.length}</span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(investigation.started_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="text-sm text-muted-foreground">
                      {getDuration(investigation.started_at, investigation.completed_at)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
