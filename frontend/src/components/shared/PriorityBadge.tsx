/**
 * Priority badge component
 */
import { IncidentPriority } from '@/types';

interface PriorityBadgeProps {
  priority: IncidentPriority;
}

const priorityStyles = {
  [IncidentPriority.P1]: 'bg-red-500 text-white',
  [IncidentPriority.P2]: 'bg-orange-500 text-white',
  [IncidentPriority.P3]: 'bg-yellow-500 text-black',
  [IncidentPriority.P4]: 'bg-gray-400 text-white',
  [IncidentPriority.P5]: 'bg-gray-400 text-white',
};

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${priorityStyles[priority]}`}
    >
      P{priority}
    </span>
  );
}
