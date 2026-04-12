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
  'Compute',
  'Container',
  'Database',
  'Serverless',
  'Queue',
  'Load Balancer',
  'Storage',
  'Network',
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
        <div className="flex flex-wrap gap-2">
          {Object.values(ProviderType).map((provider) => (
            <Button
              key={provider}
              variant={filters.providers?.includes(provider) ? 'default' : 'outline'}
              size="sm"
              onClick={() => onProviderToggle(provider)}
            >
              {provider.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">Resource Type</p>
        <div className="flex flex-wrap gap-2">
          {RESOURCE_TYPES.map((type) => (
            <Button
              key={type}
              variant={filters.types?.includes(type) ? 'default' : 'outline'}
              size="sm"
              onClick={() => onTypeToggle(type)}
            >
              {type}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-sm font-medium">Status</p>
        <div className="flex flex-wrap gap-2">
          {(['healthy', 'degraded', 'down', 'unknown'] as ServiceStatus[]).map((status) => (
            <Button
              key={status}
              variant={filters.statuses?.includes(status) ? 'default' : 'outline'}
              size="sm"
              onClick={() => onStatusToggle(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
