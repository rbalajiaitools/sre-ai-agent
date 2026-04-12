/**
 * On-premises provider configuration form
 */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ProviderType } from '@/types';
import { useValidateProvider } from '../hooks';
import { ValidationResultCard } from './ValidationResultCard';
import type { OnPremConfig } from '../types';

interface OnPremProviderFormProps {
  onValidated: (config: OnPremConfig) => void;
}

export function OnPremProviderForm({ onValidated }: OnPremProviderFormProps) {
  const [prometheusUrl, setPrometheusUrl] = useState('');
  const [lokiUrl, setLokiUrl] = useState('');
  const [k8sApiUrl, setK8sApiUrl] = useState('');
  const [apiToken, setApiToken] = useState('');

  const validate = useValidateProvider();

  const handleValidate = () => {
    if (!prometheusUrl) return;

    const config: OnPremConfig = {
      prometheus_url: prometheusUrl,
    };

    if (lokiUrl) config.loki_url = lokiUrl;
    if (k8sApiUrl) config.k8s_api_url = k8sApiUrl;
    if (apiToken) config.api_token = apiToken;

    validate.mutate(
      {
        provider_type: ProviderType.ON_PREM,
        name: 'On-Premises',
        config: config as unknown as Record<string, string>,
      },
      {
        onSuccess: (result) => {
          if (result.success) {
            onValidated(config);
          }
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Connect On-Premises Infrastructure</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Connect your existing monitoring tools and Kubernetes clusters
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="prometheus-url">
            Prometheus URL <span className="text-red-500">*</span>
          </Label>
          <Input
            id="prometheus-url"
            placeholder="https://prometheus.example.com"
            value={prometheusUrl}
            onChange={(e) => setPrometheusUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Required for metrics collection
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="loki-url">Loki URL (Optional)</Label>
          <Input
            id="loki-url"
            placeholder="https://loki.example.com"
            value={lokiUrl}
            onChange={(e) => setLokiUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            For log aggregation and analysis
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="k8s-api-url">Kubernetes API URL (Optional)</Label>
          <Input
            id="k8s-api-url"
            placeholder="https://kubernetes.example.com:6443"
            value={k8sApiUrl}
            onChange={(e) => setK8sApiUrl(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            For Kubernetes resource monitoring
          </p>
        </div>

        {k8sApiUrl && (
          <div className="space-y-2">
            <Label htmlFor="api-token">Bearer Token</Label>
            <Input
              id="api-token"
              type="password"
              placeholder="Enter Kubernetes API token"
              value={apiToken}
              onChange={(e) => setApiToken(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Service account token with read-only access
            </p>
          </div>
        )}

        <Button
          onClick={handleValidate}
          disabled={!prometheusUrl || validate.isPending}
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
