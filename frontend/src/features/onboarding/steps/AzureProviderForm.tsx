/**
 * Azure provider configuration form
 */
import { useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ProviderType } from '@/types';
import { useValidateProvider } from '../hooks';
import { ValidationResultCard } from './ValidationResultCard';
import type { AzureConfig } from '../types';

interface AzureProviderFormProps {
  onValidated: (config: AzureConfig) => void;
}

export function AzureProviderForm({ onValidated }: AzureProviderFormProps) {
  const [tenantId, setTenantId] = useState('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [subscriptionId, setSubscriptionId] = useState('');

  const validate = useValidateProvider();

  const handleValidate = () => {
    if (!tenantId || !clientId || !clientSecret || !subscriptionId) return;

    validate.mutate(
      {
        provider_type: ProviderType.AZURE,
        name: 'Azure',
        config: {
          tenant_id: tenantId,
          client_id: clientId,
          client_secret: clientSecret,
          subscription_id: subscriptionId,
        },
      },
      {
        onSuccess: (result) => {
          if (result.success) {
            onValidated({
              tenant_id: tenantId,
              client_id: clientId,
              client_secret: clientSecret,
              subscription_id: subscriptionId,
            });
          }
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Connect Azure Subscription</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Create a service principal with read-only access to your Azure resources
        </p>
      </div>

      <div className="rounded-lg border bg-muted/50 p-4 text-sm">
        <p className="font-medium">Create Service Principal:</p>
        <ol className="mt-2 list-inside list-decimal space-y-1 text-muted-foreground">
          <li>Go to Azure Portal → Azure Active Directory → App registrations</li>
          <li>Create new registration</li>
          <li>Create client secret under Certificates & secrets</li>
          <li>Assign Reader role at subscription level</li>
        </ol>
        <a
          href="https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal"
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-flex items-center gap-1 text-lime-600 hover:underline"
        >
          View detailed guide
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="tenant-id">Tenant ID</Label>
          <Input
            id="tenant-id"
            placeholder="00000000-0000-0000-0000-000000000000"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-id">Client ID (Application ID)</Label>
          <Input
            id="client-id"
            placeholder="00000000-0000-0000-0000-000000000000"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="client-secret">Client Secret</Label>
          <Input
            id="client-secret"
            type="password"
            placeholder="Enter client secret"
            value={clientSecret}
            onChange={(e) => setClientSecret(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="subscription-id">Subscription ID</Label>
          <Input
            id="subscription-id"
            placeholder="00000000-0000-0000-0000-000000000000"
            value={subscriptionId}
            onChange={(e) => setSubscriptionId(e.target.value)}
          />
        </div>

        <Button
          onClick={handleValidate}
          disabled={!tenantId || !clientId || !clientSecret || !subscriptionId || validate.isPending}
        >
          Validate Connection
        </Button>

        <ValidationResultCard
          result={validate.data || null}
          isLoading={validate.isPending}
          error={validate.error?.message}
        />
      </div>
    </div>
  );
}
