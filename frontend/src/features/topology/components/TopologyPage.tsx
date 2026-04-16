/**
 * Main topology page with tabs
 */
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RefreshCw, Filter, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ServiceMapView } from './ServiceMapView';
import { ServiceDetailDrawer } from './ServiceDetailDrawer';
import { ResourceInventory } from './ResourceInventory';
import { useTriggerRediscovery } from '../hooks';
import { ProviderType } from '@/types';
import type { ServiceStatus } from '../types';

export function TopologyPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'map');
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [providerFilter, setProviderFilter] = useState<ProviderType[]>([]);
  const [statusFilter, setStatusFilter] = useState<ServiceStatus[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [showSuccessNotification, setShowSuccessNotification] = useState(false);

  const rediscovery = useTriggerRediscovery();

  // Sync tab with URL
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && tab !== activeTab) {
      setActiveTab(tab);
    }
  }, [searchParams, activeTab]);

  // Auto-dismiss success notification after 3 seconds
  useEffect(() => {
    if (rediscovery.isSuccess && !rediscovery.isPending) {
      setShowSuccessNotification(true);
      const timer = setTimeout(() => {
        setShowSuccessNotification(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [rediscovery.isSuccess, rediscovery.isPending]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    setSearchParams({ tab: value });
  };

  const handleRediscover = () => {
    rediscovery.mutate();
  };

  const toggleProviderFilter = (provider: ProviderType) => {
    setProviderFilter((prev) =>
      prev.includes(provider) ? prev.filter((p) => p !== provider) : [...prev, provider]
    );
  };

  const toggleStatusFilter = (status: ServiceStatus) => {
    setStatusFilter((prev) =>
      prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]
    );
  };

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <div className="border-b bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Topology</h1>
            <p className="text-sm text-muted-foreground">
              Visualize your infrastructure and service dependencies
            </p>
          </div>
          <div className="flex items-center gap-2">
            {activeTab === 'map' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
                aria-label={showFilters ? 'Hide filters' : 'Show filters'}
                aria-expanded={showFilters}
              >
                <Filter className="mr-2 h-4 w-4" />
                Filters
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleRediscover}
              disabled={rediscovery.isPending}
              aria-label="Rediscover infrastructure"
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${rediscovery.isPending ? 'animate-spin' : ''}`}
              />
              Re-discover
            </Button>
          </div>
        </div>

        {/* Filters panel */}
        {showFilters && activeTab === 'map' && (
          <div className="mt-4 space-y-3 rounded-lg border bg-muted/50 p-4">
            <div className="space-y-2">
              <p className="text-sm font-medium">Provider</p>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by provider">
                {/* Only show AWS for now */}
                <Button
                  variant={providerFilter.includes(ProviderType.AWS) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => toggleProviderFilter(ProviderType.AWS)}
                  aria-pressed={providerFilter.includes(ProviderType.AWS)}
                >
                  AWS
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-medium">Status</p>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
                {(['healthy', 'degraded', 'down', 'unknown'] as ServiceStatus[]).map((status) => (
                  <Button
                    key={status}
                    variant={statusFilter.includes(status) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => toggleStatusFilter(status)}
                    aria-pressed={statusFilter.includes(status)}
                  >
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </Button>
                ))}
              </div>
            </div>

            {(providerFilter.length > 0 || statusFilter.length > 0) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setProviderFilter([]);
                  setStatusFilter([]);
                }}
              >
                Clear Filters
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange} className="flex flex-1 flex-col">
        <TabsList className="mx-4 mt-4 w-fit">
          <TabsTrigger value="map">Service Map</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="map" className="flex-1 p-4">
          <div className="h-full rounded-lg border bg-card">
            <ServiceMapView
              onServiceClick={setSelectedService}
              providerFilter={providerFilter}
              statusFilter={statusFilter}
            />
          </div>
        </TabsContent>

        <TabsContent value="resources" className="flex-1 p-4">
          <div className="h-full rounded-lg border bg-card">
            <ResourceInventory
              initialFilters={
                searchParams.get('service')
                  ? { service_name: searchParams.get('service')! }
                  : undefined
              }
              onResourceClick={(resourceName) => setSelectedService(resourceName)}
            />
          </div>
        </TabsContent>
      </Tabs>

      {/* Service detail drawer */}
      {selectedService && (
        <ServiceDetailDrawer
          serviceName={selectedService}
          onClose={() => setSelectedService(null)}
        />
      )}

      {/* Rediscovery progress overlay */}
      {rediscovery.isPending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="w-full max-w-md space-y-6 rounded-lg border bg-card p-8 shadow-lg">
            <div className="text-center">
              <RefreshCw className="mx-auto h-12 w-12 animate-spin text-primary" />
              <h3 className="mt-4 text-lg font-semibold">Discovering Infrastructure</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Connecting to your AWS account and mapping services...
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary" />
                <p className="text-sm">Fetching AWS resources</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary animation-delay-200" />
                <p className="text-sm">Analyzing service dependencies</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 animate-pulse rounded-full bg-primary animation-delay-400" />
                <p className="text-sm">Building topology graph</p>
              </div>
            </div>

            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full animate-progress bg-primary" />
            </div>
          </div>
        </div>
      )}

      {/* Rediscovery success notification */}
      {showSuccessNotification && (
        <div className="fixed bottom-4 right-4 rounded-lg border bg-green-500/10 border-green-500/50 p-4 shadow-lg animate-in fade-in slide-in-from-bottom-5" role="status">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-green-600">Rediscovery Complete</p>
              <p className="text-xs text-green-600">
                Infrastructure topology has been updated
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setShowSuccessNotification(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Rediscovery error */}
      {rediscovery.isError && (
        <div className="fixed bottom-4 right-4 rounded-lg border border-red-500/50 bg-red-500/10 p-4 shadow-lg" role="alert">
          <p className="text-sm font-medium text-red-500">Rediscovery failed</p>
          <p className="text-xs text-red-500">
            {rediscovery.error?.message || 'Failed to trigger infrastructure rediscovery'}
          </p>
        </div>
      )}
    </div>
  );
}
