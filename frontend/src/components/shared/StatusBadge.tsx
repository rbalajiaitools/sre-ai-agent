/**
 * Status badge component
 */
interface StatusBadgeProps {
  status: string;
  variant: 'incident' | 'investigation' | 'resource';
}

const incidentStatusStyles: Record<string, string> = {
  '1': 'bg-blue-500/10 text-blue-500 border-blue-500/20', // New
  '2': 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20', // In Progress
  '3': 'bg-orange-500/10 text-orange-500 border-orange-500/20', // On Hold
  '6': 'bg-green-500/10 text-green-500 border-green-500/20', // Resolved
  '7': 'bg-gray-500/10 text-gray-500 border-gray-500/20', // Closed
  '8': 'bg-red-500/10 text-red-500 border-red-500/20', // Canceled
};

const investigationStatusStyles: Record<string, string> = {
  started: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  investigating: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  rca_complete: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
  resolved: 'bg-green-500/10 text-green-500 border-green-500/20',
  failed: 'bg-red-500/10 text-red-500 border-red-500/20',
};

const resourceStatusStyles: Record<string, string> = {
  healthy: 'bg-green-500/10 text-green-500 border-green-500/20',
  degraded: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  down: 'bg-red-500/10 text-red-500 border-red-500/20',
  unknown: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
};

const statusLabels: Record<string, Record<string, string>> = {
  incident: {
    '1': 'New',
    '2': 'In Progress',
    '3': 'On Hold',
    '6': 'Resolved',
    '7': 'Closed',
    '8': 'Canceled',
  },
  investigation: {
    started: 'Started',
    investigating: 'Investigating',
    rca_complete: 'RCA Complete',
    resolved: 'Resolved',
    failed: 'Failed',
  },
  resource: {
    healthy: 'Healthy',
    degraded: 'Degraded',
    down: 'Down',
    unknown: 'Unknown',
  },
};

export function StatusBadge({ status, variant }: StatusBadgeProps) {
  const styles =
    variant === 'incident'
      ? incidentStatusStyles
      : variant === 'investigation'
      ? investigationStatusStyles
      : resourceStatusStyles;

  const label = statusLabels[variant][status] || status;
  const style = styles[status] || 'bg-gray-500/10 text-gray-500 border-gray-500/20';

  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium ${style}`}>
      {label}
    </span>
  );
}
