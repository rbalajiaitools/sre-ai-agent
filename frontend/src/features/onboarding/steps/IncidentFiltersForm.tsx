/**
 * Incident filters form component
 */
import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { IncidentPriority } from '@/types';

interface IncidentFiltersFormProps {
  priorities: IncidentPriority[];
  onPrioritiesChange: (priorities: IncidentPriority[]) => void;
  assignmentGroups: string[];
  onAssignmentGroupsChange: (groups: string[]) => void;
  pollInterval: number;
  onPollIntervalChange: (interval: number) => void;
}

const POLL_INTERVALS = [
  { value: 5, label: '5 minutes' },
  { value: 10, label: '10 minutes' },
  { value: 15, label: '15 minutes' },
  { value: 30, label: '30 minutes' },
];

export function IncidentFiltersForm({
  priorities,
  onPrioritiesChange,
  assignmentGroups,
  onAssignmentGroupsChange,
  pollInterval,
  onPollIntervalChange,
}: IncidentFiltersFormProps) {
  const [groupInput, setGroupInput] = useState('');

  const togglePriority = (priority: IncidentPriority) => {
    const newPriorities = priorities.includes(priority)
      ? priorities.filter((p) => p !== priority)
      : [...priorities, priority];
    onPrioritiesChange(newPriorities);
  };

  const addAssignmentGroup = () => {
    if (groupInput.trim() && !assignmentGroups.includes(groupInput.trim())) {
      onAssignmentGroupsChange([...assignmentGroups, groupInput.trim()]);
      setGroupInput('');
    }
  };

  const removeAssignmentGroup = (group: string) => {
    onAssignmentGroupsChange(assignmentGroups.filter((g) => g !== group));
  };

  return (
    <>
      <div className="space-y-2">
        <Label>Incident Priorities to Monitor</Label>
        <div className="flex flex-wrap gap-2">
          {[
            IncidentPriority.P1,
            IncidentPriority.P2,
            IncidentPriority.P3,
            IncidentPriority.P4,
            IncidentPriority.P5,
          ].map((priority) => (
            <button
              key={priority}
              onClick={() => togglePriority(priority)}
              className={`rounded-md border px-3 py-1 text-sm transition-colors ${
                priorities.includes(priority)
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-input bg-background hover:bg-muted'
              }`}
            >
              P{priority}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="assignment-groups">Assignment Groups (Optional)</Label>
        <div className="flex gap-2">
          <Input
            id="assignment-groups"
            placeholder="Enter group name"
            value={groupInput}
            onChange={(e) => setGroupInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                addAssignmentGroup();
              }
            }}
          />
          <Button onClick={addAssignmentGroup} variant="outline">
            Add
          </Button>
        </div>
        {assignmentGroups.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {assignmentGroups.map((group) => (
              <Badge key={group} variant="secondary" className="gap-1">
                {group}
                <button
                  onClick={() => removeAssignmentGroup(group)}
                  className="ml-1 hover:text-destructive"
                  aria-label={`Remove ${group}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="poll-interval">Poll Interval</Label>
        <select
          id="poll-interval"
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={pollInterval}
          onChange={(e) => onPollIntervalChange(Number(e.target.value))}
        >
          {POLL_INTERVALS.map((interval) => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>
      </div>
    </>
  );
}
