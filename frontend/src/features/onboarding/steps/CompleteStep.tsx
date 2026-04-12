/**
 * Onboarding complete step
 */
import { useNavigate } from 'react-router-dom';
import { MessageSquare, AlertCircle, Network } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { ConfiguredProvider, DiscoveryResult } from '../types';

interface CompleteStepProps {
  providers: ConfiguredProvider[];
  discoveryResult: DiscoveryResult | null;
}

export function CompleteStep({ providers, discoveryResult }: CompleteStepProps) {
  const navigate = useNavigate();

  return (
    <div className="space-y-8 py-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold">You're All Set!</h1>
        <p className="mt-3 text-lg text-muted-foreground">
          Your SRE AI Agent is ready to help investigate incidents
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h3 className="font-semibold">What's Connected</h3>
        <ul className="mt-3 space-y-2">
          {providers.map((provider) => (
            <li key={provider.id} className="flex items-center gap-2 text-sm">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              {provider.name}
            </li>
          ))}
        </ul>
        {discoveryResult && (
          <p className="mt-4 text-sm text-muted-foreground">
            Discovered {discoveryResult.services_found} services across{' '}
            {discoveryResult.resources_found} resources
          </p>
        )}
      </div>

      <div className="space-y-3">
        <h3 className="font-semibold">Next Steps</h3>

        <button
          onClick={() => navigate('/incidents')}
          className="flex w-full items-start gap-4 rounded-lg border bg-card p-4 text-left transition-colors hover:border-primary"
        >
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-blue-500/10">
            <AlertCircle className="h-5 w-5 text-blue-500" />
          </div>
          <div className="flex-1">
            <h4 className="font-medium">View Your Incidents</h4>
            <p className="mt-1 text-sm text-muted-foreground">
              Browse and manage incidents synced from ServiceNow
            </p>
          </div>
        </button>

        <button
          onClick={() => navigate('/chat')}
          className="flex w-full items-start gap-4 rounded-lg border bg-card p-4 text-left transition-colors hover:border-primary"
        >
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-green-500/10">
            <MessageSquare className="h-5 w-5 text-green-500" />
          </div>
          <div className="flex-1">
            <h4 className="font-medium">Start a Chat</h4>
            <p className="mt-1 text-sm text-muted-foreground">
              Ask the AI agent to investigate an incident or answer questions
            </p>
          </div>
        </button>

        <button
          onClick={() => navigate('/topology')}
          className="flex w-full items-start gap-4 rounded-lg border bg-card p-4 text-left transition-colors hover:border-primary"
        >
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-purple-500/10">
            <Network className="h-5 w-5 text-purple-500" />
          </div>
          <div className="flex-1">
            <h4 className="font-medium">Explore Your Service Map</h4>
            <p className="mt-1 text-sm text-muted-foreground">
              Visualize your infrastructure and service dependencies
            </p>
          </div>
        </button>
      </div>

      <div className="pt-4 text-center">
        <Button size="lg" onClick={() => navigate('/chat')}>
          Get Started
        </Button>
      </div>
    </div>
  );
}
