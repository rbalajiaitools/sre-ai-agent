/**
 * Service detail drawer
 */
import { useNavigate } from 'react-router-dom';
import { X, MessageSquare, List, Cloud, Server } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useServiceDetail } from '../hooks';
import { ServiceHealthSummary } from './ServiceHealthSummary';
import { ProviderType } from '@/types';
import type { ServiceStatus } from '../types';

interface ServiceDetailDrawerProps {
  serviceName: string | null;
  onClose: () => void;
}

const providerIcons = {
  [ProviderType.AWS]: Cloud,
  [ProviderType.AZURE]: Cloud,
  [ProviderType.GCP]: Cloud,
  [ProviderType.ON_PREM]: Server,
  [ProviderType.CUSTOM]: Server,
};

const statusColors: Record<ServiceStatus, string> = {
  healthy: 'bg-green-500',
  degraded: 'bg-yellow-500',
  down: 'bg-red-500',
  unknown: 'bg-gray-500',
};

export function ServiceDetailDrawer({ serviceName, onClose }: ServiceDetailDrawerProps) {
  const navigate = useNavigate();
  const serviceQuery = useServiceDetail(serviceName);

  if (!serviceName) return null;

  const service = serviceQuery.data;
  const Icon = service ? providerIcons[service.provider] : Cloud;

  return (
    <div className="fixed right-0 top-0 z-50 h-full w-[400px] border-l bg-background shadow-lg">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Service Details</h2>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close drawer">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {serviceQuery.isLoading && (
            <div className="space-y-4">
              <div className="h-8 w-3/4 animate-pulse rounded bg-muted" />
              <div className="h-20 animate-pulse rounded bg-muted" />
              <div className="h-40 animate-pulse rounded bg-muted" />
            </div>
          )}

          {serviceQuery.isError && (
            <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4" role="alert">
              <p className="text-sm text-red-500">
                Failed to load service details: {serviceQuery.error?.message}
              </p>
            </div>
          )}

          {service && (
            <div className="space-y-6">
              {/* Service header */}
              <div>
                <div className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-primary" aria-hidden="true" />
                  <h3 className="text-xl font-bold">{service.name}</h3>
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <div
                    className={`h-2 w-2 rounded-full ${statusColors[service.status]}`}
                    aria-hidden="true"
                  />
                  <span className="text-sm capitalize text-muted-foreground">
                    {service.status}
                  </span>
                  <span className="text-sm text-muted-foreground">•</span>
                  <span className="text-sm text-muted-foreground">{service.region}</span>
                </div>
              </div>

              <ServiceHealthSummary healthSummary={service.health_summary} />

              {/* Resources */}
              <div>
                <h4 className="font-semibold">Resources</h4>
                <div className="mt-2 space-y-2">
                  {service.resources && service.resources.length > 0 ? (
                    <>
                      {service.resources.slice(0, 5).map((resource) => (
                        <div
                          key={resource.resource_id}
                          className="rounded-lg border bg-card p-3 text-sm"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-medium">{resource.name}</p>
                              <p className="text-xs text-muted-foreground">{resource.type}</p>
                            </div>
                            <div className="flex items-center gap-1">
                              <div
                                className={`h-2 w-2 rounded-full ${statusColors[resource.status]}`}
                                aria-hidden="true"
                              />
                              <span className="text-xs text-muted-foreground">{resource.region}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                      {service.resources.length > 5 && (
                        <p className="text-xs text-muted-foreground">
                          +{service.resources.length - 5} more resources
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">No resources discovered yet</p>
                  )}
                </div>
              </div>

              {/* Past incidents */}
              {service.past_incidents && service.past_incidents.length > 0 && (
                <div>
                  <h4 className="font-semibold">Past Incidents</h4>
                  <div className="mt-2 space-y-2">
                    {service.past_incidents.map((incident) => (
                      <button
                        key={incident.sys_id}
                        onClick={() => navigate(`/incidents?selected=${incident.sys_id}`)}
                        className="w-full rounded-lg border bg-card p-3 text-left text-sm transition-colors hover:border-primary"
                        aria-label={`View incident ${incident.incident_number}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="font-medium">{incident.incident_number}</p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {incident.short_description}
                            </p>
                          </div>
                          <span className="text-xs text-muted-foreground">P{incident.priority}</span>
                        </div>
                        {incident.resolved_at && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            Resolved {new Date(incident.resolved_at).toLocaleDateString()}
                          </p>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Team owner */}
              {service.team_owner && (
                <div className="rounded-lg border bg-muted/50 p-3">
                  <p className="text-xs text-muted-foreground">Team Owner</p>
                  <p className="mt-1 font-medium">{service.team_owner}</p>
                </div>
              )}

              {/* Actions */}
              <div className="space-y-2">
                <Button
                  className="w-full"
                  onClick={() => navigate(`/chat?service=${encodeURIComponent(service.name)}`)}
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Investigate this Service
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() =>
                    navigate(`/topology?tab=resources&service=${encodeURIComponent(service.name)}`)
                  }
                >
                  <List className="mr-2 h-4 w-4" />
                  View All Resources
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
