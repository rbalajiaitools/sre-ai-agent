/**
 * Incident List - virtualized list of incidents
 */
import { FixedSizeList } from 'react-window';
import { Loader2 } from 'lucide-react';
import { ServiceNowIncident } from '../types';
import { IncidentRow } from './IncidentRow';
import { IncidentPriority } from '@/types';

interface IncidentListProps {
  incidents: ServiceNowIncident[] | undefined;
  isLoading: boolean;
  isError: boolean;
  selectedIncidentId: string | null;
  onIncidentSelect: (incident: ServiceNowIncident) => void;
  height: number;
}

export function IncidentList({
  incidents,
  isLoading,
  isError,
  selectedIncidentId,
  onIncidentSelect,
  height,
}: IncidentListProps) {
  // Sort incidents: P1 first, then by updated_at desc
  const sortedIncidents = incidents
    ? [...incidents].sort((a, b) => {
        // P1 incidents first
        if (a.priority === IncidentPriority.P1 && b.priority !== IncidentPriority.P1) {
          return -1;
        }
        if (b.priority === IncidentPriority.P1 && a.priority !== IncidentPriority.P1) {
          return 1;
        }
        // Then by updated_at desc
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      })
    : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" aria-label="Loading incidents" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-muted-foreground">
          Failed to load incidents. Please try again.
        </p>
      </div>
    );
  }

  if (!sortedIncidents || sortedIncidents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <p className="text-sm font-medium mb-1">No incidents found</p>
        <p className="text-xs text-muted-foreground">
          Try adjusting your filters or refresh from ServiceNow
        </p>
      </div>
    );
  }

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const incident = sortedIncidents[index];
    return (
      <div style={style}>
        <IncidentRow
          incident={incident}
          isSelected={selectedIncidentId === incident.sys_id}
          onClick={() => onIncidentSelect(incident)}
        />
      </div>
    );
  };

  return (
    <FixedSizeList
      height={height}
      itemCount={sortedIncidents.length}
      itemSize={88}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
