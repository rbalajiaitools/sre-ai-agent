/**
 * Provider connection step
 */
import { useState } from 'react';
import { Cloud, Server, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ProviderType } from '@/types';
import { AWSProviderForm } from './AWSProviderForm';
import { AzureProviderForm } from './AzureProviderForm';
import { GCPProviderForm } from './GCPProviderForm';
import { OnPremProviderForm } from './OnPremProviderForm';
import type { ConfiguredProvider } from '../types';

interface ConnectProviderStepProps {
  providers: ConfiguredProvider[];
  onProviderAdded: (provider: ConfiguredProvider) => void;
}

type SelectedProvider = ProviderType | null;

export function ConnectProviderStep({ providers, onProviderAdded }: ConnectProviderStepProps) {
  const [selectedProvider, setSelectedProvider] = useState<SelectedProvider>(null);

  const providerCards = [
    {
      type: ProviderType.AWS,
      name: 'Amazon Web Services',
      description: 'Connect your AWS account',
      icon: Cloud,
    },
    {
      type: ProviderType.AZURE,
      name: 'Microsoft Azure',
      description: 'Connect your Azure subscription',
      icon: Cloud,
    },
    {
      type: ProviderType.GCP,
      name: 'Google Cloud Platform',
      description: 'Connect your GCP project',
      icon: Cloud,
    },
    {
      type: ProviderType.ON_PREM,
      name: 'On-Premises / Custom',
      description: 'Connect existing monitoring tools',
      icon: Server,
    },
  ];

  const handleProviderValidated = (type: ProviderType, config: Record<string, unknown>) => {
    const newProvider: ConfiguredProvider = {
      id: `${type}-${Date.now()}`,
      provider_type: type,
      name: providerCards.find((p) => p.type === type)?.name || type,
      validated: true,
    };
    onProviderAdded(newProvider);
    setSelectedProvider(null);
  };

  if (selectedProvider) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => setSelectedProvider(null)}>
          ← Back to provider selection
        </Button>

        {selectedProvider === ProviderType.AWS && (
          <AWSProviderForm
            onValidated={(config) => handleProviderValidated(ProviderType.AWS, config)}
          />
        )}
        {selectedProvider === ProviderType.AZURE && (
          <AzureProviderForm
            onValidated={(config) => handleProviderValidated(ProviderType.AZURE, config)}
          />
        )}
        {selectedProvider === ProviderType.GCP && (
          <GCPProviderForm
            onValidated={(config) => handleProviderValidated(ProviderType.GCP, config)}
          />
        )}
        {selectedProvider === ProviderType.ON_PREM && (
          <OnPremProviderForm
            onValidated={(config) => handleProviderValidated(ProviderType.ON_PREM, config)}
          />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Connect Your Infrastructure</h2>
        <p className="mt-2 text-muted-foreground">
          Select and configure one or more cloud providers
        </p>
      </div>

      {providers.length > 0 && (
        <div className="rounded-lg border bg-muted/50 p-4">
          <h3 className="font-medium">Connected Providers</h3>
          <ul className="mt-2 space-y-2">
            {providers.map((provider) => (
              <li key={provider.id} className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>{provider.name}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {providerCards.map((provider) => {
          const Icon = provider.icon;
          const isConnected = providers.some((p) => p.provider_type === provider.type);

          return (
            <button
              key={provider.type}
              onClick={() => setSelectedProvider(provider.type)}
              className="relative rounded-lg border bg-card p-6 text-left transition-colors hover:border-primary"
              disabled={isConnected}
            >
              {isConnected && (
                <div className="absolute right-4 top-4">
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                </div>
              )}
              <Icon className="h-8 w-8 text-primary" />
              <h3 className="mt-4 font-semibold">{provider.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{provider.description}</p>
              <div className="mt-4">
                <span className="text-sm font-medium text-primary">
                  {isConnected ? 'Connected' : 'Configure →'}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
