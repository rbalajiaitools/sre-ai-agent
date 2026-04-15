/**
 * Resource filters component
 */
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ProviderType } from '@/types';
import type { ServiceStatus, ResourceFilters as ResourceFiltersType } from '../types';

interface ResourceFiltersProps {
  filters: ResourceFiltersType;
  search: string;
  onSearchChange: (search: string) => void;
  onProviderToggle: (provider: ProviderType) => void;
  onTypeToggle: (type: string) => void;
  onStatusToggle: (status: ServiceStatus) => void;
}

const RESOURCE_TYPES = [
  'service',
  'database',
  'cache',
  'queue',
  'storage',
];

export function ResourceFilters({
  filters,
  search,
  onSearchChange,
  onProviderToggle,
  onTypeToggle,
  onStatusToggle,
}: ResourceFiltersProps) {
  return (
    <div className="space-y-4 border-b p-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search resources..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">Provider</p>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by provider">
          {/* Only show AWS for now since that's what we support */}
          <Button
            variant={filters.providers?.includes(ProviderType.AWS) ? 'default' : 'outline'}
            size="sm"
            onClick={() => onProviderToggle(ProviderType.AWS)}
            aria-pressed={filters.providers?.includes(ProviderType.AWS)}
          >
            AWS
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">Resource Type</p>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by resource type">
          {RESOURCE_TYPES.map((type) => (
            <Button
              key={type}
              variant={filters.types?.includes(type) ? 'default' : 'outline'}
              size="sm"
              onClick={() => onTypeToggle(type)}
              aria-pressed={filters.types?.includes(type)}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">Status</p>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
          {(['healthy', 'degraded', 'down', 'unknown'] as ServiceStatus[]).map((status) => (
            <Button
              key={status}
              variant={filters.statuses?.includes(status) ? 'default' : 'outline'}
              size="sm"
              onClick={() => onStatusToggle(status)}
              aria-pressed={filters.statuses?.includes(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
