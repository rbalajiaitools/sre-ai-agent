/**
 * Incident Filters - filter bar for incident list
 */
import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { IncidentPriority, IncidentState } from '@/types';
import { IncidentFilter } from '../types';
import { cn } from '@/lib/utils';

interface IncidentFiltersProps {
  filter: Partial<IncidentFilter>;
  onFilterChange: (filter: Partial<IncidentFilter>) => void;
  hasP1Incidents?: boolean;
  assignmentGroups?: string[];
}

const PRIORITY_TABS = [
  { label: 'All', value: null },
  { label: 'P1', value: IncidentPriority.P1 },
  { label: 'P2', value: IncidentPriority.P2 },
  { label: 'P3', value: IncidentPriority.P3 },
  { label: 'P4+', value: 'P4+' },
];

const STATE_OPTIONS = [
  { label: 'New', value: IncidentState.NEW },
  { label: 'In Progress', value: IncidentState.IN_PROGRESS },
  { label: 'On Hold', value: IncidentState.ON_HOLD },
];

export function IncidentFilters({
  filter,
  onFilterChange,
  hasP1Incidents = false,
  assignmentGroups = [],
}: IncidentFiltersProps) {
  const [searchInput, setSearchInput] = useState(filter.search || '');

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      onFilterChange({ ...filter, search: searchInput });
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const handlePriorityClick = (priority: string | null) => {
    if (priority === null) {
      onFilterChange({ ...filter, priorities: [] });
    } else if (priority === 'P4+') {
      onFilterChange({
        ...filter,
        priorities: [IncidentPriority.P4, IncidentPriority.P5],
      });
    } else {
      onFilterChange({ ...filter, priorities: [priority as IncidentPriority] });
    }
  };

  const handleStateToggle = (state: IncidentState) => {
    const currentStates = filter.states || [];
    const newStates = currentStates.includes(state)
      ? currentStates.filter((s) => s !== state)
      : [...currentStates, state];
    onFilterChange({ ...filter, states: newStates });
  };

  const handleAssignmentGroupChange = (group: string) => {
    onFilterChange({ ...filter, assignment_group: group });
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (filter.priorities && filter.priorities.length > 0) count++;
    if (filter.states && filter.states.length > 0) count++;
    if (filter.search) count++;
    if (filter.assignment_group) count++;
    return count;
  };

  const clearFilters = () => {
    setSearchInput('');
    onFilterChange({
      priorities: [],
      states: [],
      search: '',
      assignment_group: '',
    });
  };

  const activeFilterCount = getActiveFilterCount();
  const selectedPriority =
    filter.priorities && filter.priorities.length > 0
      ? filter.priorities.includes(IncidentPriority.P4) ||
        filter.priorities.includes(IncidentPriority.P5)
        ? 'P4+'
        : filter.priorities[0]
      : null;

  return (
    <div className="space-y-3 p-4 border-b bg-muted/30">
      {/* Priority tabs */}
      <div className="flex items-center gap-2">
        {PRIORITY_TABS.map((tab) => (
          <button
            key={tab.label}
            onClick={() => handlePriorityClick(tab.value)}
            className={cn(
              'relative px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
              selectedPriority === tab.value
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted'
            )}
            aria-pressed={selectedPriority === tab.value}
          >
            {tab.label}
            {tab.value === IncidentPriority.P1 && hasP1Incidents && (
              <span
                className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-destructive"
                aria-label="Has P1 incidents"
              />
            )}
          </button>
        ))}
      </div>

      {/* State pills and search */}
      <div className="flex items-center gap-3">
        {/* State pills */}
        <div className="flex items-center gap-2">
          {STATE_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => handleStateToggle(option.value)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                filter.states?.includes(option.value)
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted hover:bg-muted/80'
              )}
              aria-pressed={filter.states?.includes(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative flex-1">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search incidents..."
            className="pl-9"
            aria-label="Search incidents"
          />
        </div>

        {/* Assignment group dropdown */}
        {assignmentGroups.length > 0 && (
          <select
            value={filter.assignment_group || ''}
            onChange={(e) => handleAssignmentGroupChange(e.target.value)}
            className="px-3 py-1.5 rounded-md border bg-background text-sm"
            aria-label="Filter by assignment group"
          >
            <option value="">All Groups</option>
            {assignmentGroups.map((group) => (
              <option key={group} value={group}>
                {group}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Active filters indicator */}
      {activeFilterCount > 0 && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>
            {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active
          </span>
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-1 text-primary hover:underline"
          >
            <X className="h-3 w-3" aria-hidden="true" />
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}
