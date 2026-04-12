/**
 * Validation step - validates all configured providers
 */
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { ConfiguredProvider } from '../types';

interface ValidateStepProps {
  providers: ConfiguredProvider[];
  serviceNowConfigured: boolean;
  onValidateAll: () => void;
  onFixProvider: (providerId: string) => void;
  isValidating: boolean;
}

export function ValidateStep({
  providers,
  serviceNowConfigured,
  onValidateAll,
  onFixProvider,
  isValidating,
}: ValidateStepProps) {
  const allValidated = providers.every((p) => p.validated) && serviceNowConfigured;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Validate Connections</h2>
        <p className="mt-2 text-muted-foreground">
          Let's verify all your connections are working correctly
        </p>
      </div>

      <div className="space-y-3">
        {providers.map((provider) => (
          <div
            key={provider.id}
            className="flex items-center justify-between rounded-lg border bg-card p-4"
          >
            <div className="flex items-center gap-3">
              {isValidating ? (
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              ) : provider.validated ? (
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              <div>
                <p className="font-medium">{provider.name}</p>
                <p className="text-sm text-muted-foreground">
                  {provider.validated ? 'Connected' : 'Connection failed'}
                </p>
              </div>
            </div>
            {!provider.validated && !isValidating && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onFixProvider(provider.id)}
              >
                Fix
              </Button>
            )}
          </div>
        ))}

        <div
          className="flex items-center justify-between rounded-lg border bg-card p-4"
        >
          <div className="flex items-center gap-3">
            {isValidating ? (
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : serviceNowConfigured ? (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            ) : (
              <XCircle className="h-5 w-5 text-yellow-500" />
            )}
            <div>
              <p className="font-medium">ServiceNow</p>
              <p className="text-sm text-muted-foreground">
                {serviceNowConfigured ? 'Connected' : 'Not configured (optional)'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {!allValidated && !isValidating && (
        <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4">
          <p className="text-sm text-yellow-500">
            Some connections need attention. Click "Fix" to reconfigure, or continue without them.
          </p>
        </div>
      )}

      <Button
        onClick={onValidateAll}
        disabled={isValidating || providers.length === 0}
        className="w-full"
      >
        {isValidating ? 'Validating...' : 'Run Full Validation'}
      </Button>
    </div>
  );
}
