/**
 * Resource inventory table
 */
import { useState } from 'react';
import { Cloud, Server, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useResources } from '../hooks';
import { ResourceFilters } from './ResourceFilters';
import { ProviderType } from '@/types';
import type { ServiceStatus, ResourceFilters as ResourceFiltersType } from '../types';

interface ResourceInventoryProps {
  initialFilters?: ResourceFiltersType;
  onResourceClick?: (resourceName: string) => void;
}

const providerIcons = {
  [ProviderType.AWS]: Cloud,
  [ProviderType.AZURE]: Cloud,
  [ProviderType.GCP]: Cloud,
  [ProviderType.ON_PREM]: Server,
  [ProviderType.CUSTOM]: Server,
};

const statusColors: Record<ServiceStatus, string> = {
  healthy: 'text-green-500',
  degraded: 'text-yellow-500',
  down: 'text-red-500',
  unknown: 'text-gray-500',
};

const statusDotColors: Record<ServiceStatus, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-yellow-500',
  down: 'bg-red-500',
  unknown: 'bg-gray-500',
};

export function ResourceInventory({ initialFilters, onResourceClick }: ResourceInventoryProps) {
  const [filters, setFilters] = useState<ResourceFiltersType>(initialFilters || {});
  const [search, setSearch] = useState('');
  const [selectedResource, setSelectedResource] = useState<string | null>(null);

  // Convert array filters to single values for API
  const apiFilters = {
    provider: filters.providers?.[0],
    resource_type: filters.types?.[0],
    search: search || undefined,
  };

  const resourcesQuery = useResources(apiFilters);

  // Client-side filtering for multiple selections
  const filteredResources = resourcesQuery.data?.items.filter((resource) => {
    // Filter by types (if multiple selected)
    if (filters.types && filters.types.length > 0) {
      if (!filters.types.includes(resource.type)) return false;
    }
    
    // Filter by providers (if multiple selected)
    if (filters.providers && filters.providers.length > 0) {
      if (!filters.providers.includes(resource.provider)) return false;
    }
    
    // Filter by statuses
    if (filters.statuses && filters.statuses.length > 0) {
      if (!filters.statuses.includes(resource.status)) return false;
    }
    
    return true;
  }) || [];

  const toggleProvider = (provider: ProviderType) => {
    const current = filters.providers || [];
    const updated = current.includes(provider)
      ? current.filter((p) => p !== provider)
      : [...current, provider];
    setFilters({ ...filters, providers: updated.length > 0 ? updated : undefined });
  };

  const toggleType = (type: string) => {
    const current = filters.types || [];
    const updated = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    setFilters({ ...filters, types: updated.length > 0 ? updated : undefined });
  };

  const toggleStatus = (status: ServiceStatus) => {
    const current = filters.statuses || [];
    const updated = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status];
    setFilters({ ...filters, statuses: updated.length > 0 ? updated : undefined });
  };

  return (
    <div className="flex h-full flex-col">
      <ResourceFilters
        filters={filters}
        search={search}
        onSearchChange={setSearch}
        onProviderToggle={toggleProvider}
        onTypeToggle={toggleType}
        onStatusToggle={toggleStatus}
      />

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {resourcesQuery.isLoading && (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        )}

        {resourcesQuery.isError && (
          <div className="flex h-full items-center justify-center p-4">
            <div className="text-center">
              <p className="text-sm text-red-500">
                Failed to load resources: {resourcesQuery.error?.message}
              </p>
            </div>
          </div>
        )}

        {resourcesQuery.data && (
          <>
            {filteredResources.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">No resources found</p>
              </div>
            ) : (
              <table className="w-full">
                <thead className="sticky top-0 border-b bg-muted/50">
                  <tr>
                    <th className="p-3 text-left text-sm font-medium">Name</th>
                    <th className="p-3 text-left text-sm font-medium">Type</th>
                    <th className="p-3 text-left text-sm font-medium">Provider</th>
                    <th className="p-3 text-left text-sm font-medium">Region</th>
                    <th className="p-3 text-left text-sm font-medium">Status</th>
                    <th className="p-3 text-left text-sm font-medium">Service</th>
                    <th className="p-3 text-left text-sm font-medium">Tags</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredResources.map((resource) => {
                    const Icon = providerIcons[resource.provider];
                    const tags = Object.entries(resource.tags);

                    return (
                      <tr
                        key={resource.resource_id}
                        onClick={() => {
                          setSelectedResource(resource.resource_id);
                          if (onResourceClick) {
                            onResourceClick(resource.name);
                          }
                        }}
                        className="cursor-pointer border-b transition-colors hover:bg-muted/50"
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedResource(resource.resource_id);
                            if (onResourceClick) {
                              onResourceClick(resource.name);
                            }
                          }
                        }}
                        aria-label={`View details for ${resource.name}`}
                      >
                        <td className="p-3 text-sm font-medium">{resource.name}</td>
                        <td className="p-3 text-sm text-muted-foreground">{resource.type}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4 text-primary" aria-hidden="true" />
                            <span className="text-sm">{resource.provider.toUpperCase()}</span>
                          </div>
                        </td>
                        <td className="p-3 text-sm text-muted-foreground">{resource.region}</td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <div
                              className={`h-2 w-2 rounded-full ${
                                statusDotColors[resource.status]
                              }`}
                              aria-hidden="true"
                            />
                            <span className={`text-sm capitalize ${statusColors[resource.status]}`}>
                              {resource.status}
                            </span>
                          </div>
                        </td>
                        <td className="p-3 text-sm">{resource.service_name}</td>
                        <td className="p-3">
                          <div className="flex flex-wrap gap-1">
                            {tags.slice(0, 2).map(([key, value]) => (
                              <Badge key={key} variant="secondary" className="text-xs">
                                {key}: {value}
                              </Badge>
                            ))}
                            {tags.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{tags.length - 2} more
                              </Badge>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </div>
  );
}

