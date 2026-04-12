/**
 * Main topology page with tabs
 */
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RefreshCw, Filter } from 'lucide-react';
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

  const rediscovery = useTriggerRediscovery();

  // Sync tab with URL
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && tab !== activeTab) {
      setActiveTab(tab);
    }
  }, [searchParams, activeTab]);

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
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-card p-4">
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
              <div className="flex flex-wrap gap-2">
                {Object.values(ProviderType).map((provider) => (
                  <Button
                    key={provider}
                    variant={providerFilter.includes(provider) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => toggleProviderFilter(provider)}
                  >
                    {provider.toUpperCase()}
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
                    variant={statusFilter.includes(status) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => toggleStatusFilter(status)}
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

      {/* Rediscovery notification */}
      {rediscovery.isSuccess && (
        <div className="fixed bottom-4 right-4 rounded-lg border bg-card p-4 shadow-lg">
          <p className="text-sm font-medium">Rediscovery started</p>
          <p className="text-xs text-muted-foreground">
            Infrastructure mapping is in progress
          </p>
        </div>
      )}
    </div>
  );
}
