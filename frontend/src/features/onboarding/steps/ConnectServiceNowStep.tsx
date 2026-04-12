/**
 * ServiceNow connection step
 */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { IncidentPriority } from '@/types';
import { useValidateServiceNow } from '../hooks';
import { ValidationResultCard } from './ValidationResultCard';
import { IncidentFiltersForm } from './IncidentFiltersForm';
import type { ServiceNowConfig } from '../types';

interface ConnectServiceNowStepProps {
  onValidated: (config: ServiceNowConfig) => void;
  onSkip: () => void;
}

export function ConnectServiceNowStep({ onValidated, onSkip }: ConnectServiceNowStepProps) {
  const [instanceUrl, setInstanceUrl] = useState('');
  const [authType, setAuthType] = useState<'basic' | 'oauth'>('basic');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [priorities, setPriorities] = useState<IncidentPriority[]>([
    IncidentPriority.P1,
    IncidentPriority.P2,
  ]);
  const [assignmentGroups, setAssignmentGroups] = useState<string[]>([]);
  const [pollInterval, setPollInterval] = useState(10);

  const validate = useValidateServiceNow();

  const handleValidate = () => {
    if (!instanceUrl || !username || !password) return;

    const config: ServiceNowConfig = {
      instance_url: instanceUrl,
      username,
      password,
      incident_filters: {
        priorities,
        assignment_groups: assignmentGroups,
        poll_interval_minutes: pollInterval,
      },
    };

    validate.mutate(config, {
      onSuccess: (result) => {
        if (result.success) {
          onValidated(config);
        }
      },
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Connect ServiceNow</h2>
        <p className="mt-2 text-muted-foreground">
          Sync incidents from your ServiceNow instance
        </p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="instance-url">Instance URL</Label>
          <Input
            id="instance-url"
            placeholder="https://your-instance.service-now.com"
            value={instanceUrl}
            onChange={(e) => setInstanceUrl(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label>Authentication Type</Label>
          <div className="flex gap-2">
            <Button
              variant={authType === 'basic' ? 'default' : 'outline'}
              onClick={() => setAuthType('basic')}
              className="flex-1"
            >
              Basic Auth
            </Button>
            <Button
              variant={authType === 'oauth' ? 'default' : 'outline'}
              onClick={() => setAuthType('oauth')}
              className="flex-1"
            >
              OAuth 2.0
            </Button>
          </div>
        </div>

        {authType === 'basic' && (
          <>
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </>
        )}

        <IncidentFiltersForm
          priorities={priorities}
          onPrioritiesChange={setPriorities}
          assignmentGroups={assignmentGroups}
          onAssignmentGroupsChange={setAssignmentGroups}
          pollInterval={pollInterval}
          onPollIntervalChange={setPollInterval}
        />

        <div className="flex gap-2">
          <Button
            onClick={handleValidate}
            disabled={!instanceUrl || !username || !password || validate.isPending}
          >
            Test Connection
          </Button>
          <Button variant="outline" onClick={onSkip}>
            Skip for Now
          </Button>
        </div>

        <ValidationResultCard
          result={validate.data || null}
          isLoading={validate.isPending}
          error={validate.error?.message}
        />
      </div>
    </div>
  );
}
