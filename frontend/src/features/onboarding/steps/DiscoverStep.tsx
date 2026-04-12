/**
 * Discovery step - scans infrastructure
 */
import { useEffect } from 'react';
import { CheckCircle2, Loader2, Sparkles, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTriggerDiscovery, useDiscoveryStatus } from '../hooks';
import type { DiscoveryResult } from '../types';

interface DiscoverStepProps {
  onComplete: (result: DiscoveryResult) => void;
}

export function DiscoverStep({ onComplete }: DiscoverStepProps) {
  const triggerDiscovery = useTriggerDiscovery();
  const discoveryStatus = useDiscoveryStatus(
    triggerDiscovery.data?.job_id || null,
    !!triggerDiscovery.data
  );

  useEffect(() => {
    if (!triggerDiscovery.data && !triggerDiscovery.isPending) {
      triggerDiscovery.mutate();
    }
  }, [triggerDiscovery]);

  useEffect(() => {
    if (discoveryStatus.data?.status === 'complete' && discoveryStatus.data.result) {
      onComplete(discoveryStatus.data.result);
    }
  }, [discoveryStatus.data, onComplete]);

  // Handle trigger discovery errors
  if (triggerDiscovery.isError) {
    return (
      <div className="space-y-4 py-8 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10">
          <XCircle className="h-8 w-8 text-red-500" />
        </div>
        <h2 className="text-2xl font-bold">Failed to Start Discovery</h2>
        <p className="text-muted-foreground">
          {triggerDiscovery.error?.message || 'Unable to start infrastructure discovery'}
        </p>
        <Button onClick={() => triggerDiscovery.mutate()} variant="outline">
          Try Again
        </Button>
      </div>
    );
  }

  // Handle loading state while triggering discovery
  if (triggerDiscovery.isPending) {
    return (
      <div className="space-y-4 py-8 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
        <h2 className="text-2xl font-bold">Starting Discovery</h2>
        <p className="text-muted-foreground">Initializing infrastructure scan...</p>
      </div>
    );
  }

  const status = discoveryStatus.data?.status || 'pending';

  const steps = [
    { key: 'scanning', label: 'Scanning cloud services', active: ['scanning', 'building', 'indexing', 'complete'].includes(status) },
    { key: 'building', label: 'Building service map', active: ['building', 'indexing', 'complete'].includes(status) },
    { key: 'indexing', label: 'Indexing knowledge graph', active: ['indexing', 'complete'].includes(status) },
  ];

  if (discoveryStatus.data?.status === 'complete' && discoveryStatus.data.result) {
    return <DiscoveryResultCard result={discoveryStatus.data.result} />;
  }

  return (
    <div className="space-y-8 py-8">
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <Sparkles className="h-8 w-8 animate-pulse text-primary" />
        </div>
        <h2 className="mt-4 text-2xl font-bold">Mapping Your Infrastructure</h2>
        <p className="mt-2 text-muted-foreground">
          This will take a few moments...
        </p>
      </div>

      <div className="space-y-4">
        {steps.map((step) => (
          <div
            key={step.key}
            className="flex items-center gap-3 rounded-lg border bg-card p-4"
            role="status"
            aria-label={`${step.label} - ${step.active ? 'in progress' : 'pending'}`}
          >
            {step.active ? (
              status === 'complete' ? (
                <CheckCircle2 className="h-5 w-5 text-green-500" aria-hidden="true" />
              ) : (
                <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
              )
            ) : (
              <div className="h-5 w-5 rounded-full border-2 border-muted" aria-hidden="true" />
            )}
            <span className={step.active ? 'font-medium' : 'text-muted-foreground'}>
              {step.label}
            </span>
          </div>
        ))}
      </div>

      {discoveryStatus.isError && (
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-center" role="alert">
          <p className="text-sm text-red-500">
            {discoveryStatus.error?.message || 'Discovery failed. Please try again or contact support.'}
          </p>
        </div>
      )}
    </div>
  );
}

function DiscoveryResultCard({ result }: { result: DiscoveryResult }) {
  return (
    <div className="space-y-6 py-8">
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-500/10">
          <CheckCircle2 className="h-8 w-8 text-green-500" />
        </div>
        <h2 className="mt-4 text-2xl font-bold">Discovery Complete!</h2>
        <p className="mt-2 text-lg text-muted-foreground">
          Found {result.services_found} services and {result.resources_found} resources
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h3 className="font-semibold">Resource Breakdown</h3>
        {Object.keys(result.resource_breakdown).length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No resources discovered yet</p>
        ) : (
          <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3">
            {Object.entries(result.resource_breakdown).map(([type, count]) => (
              <div key={type} className="rounded-lg border bg-muted/50 p-3">
                <p className="text-2xl font-bold">{count}</p>
                <p className="text-sm text-muted-foreground">{type}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {result.sample_services.length > 0 && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="font-semibold">Sample Services</h3>
          <ul className="mt-3 space-y-1">
            {result.sample_services.map((service, idx) => (
              <li key={idx} className="text-sm text-muted-foreground">
                • {service}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
