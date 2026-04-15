/**
 * GCP provider configuration form
 */
import { useState } from 'react';
import { Upload, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ProviderType } from '@/types';
import { useValidateProvider } from '../hooks';
import { ValidationResultCard } from './ValidationResultCard';
import type { GCPConfig } from '../types';

interface GCPProviderFormProps {
  onValidated: (config: GCPConfig) => void;
}

export function GCPProviderForm({ onValidated }: GCPProviderFormProps) {
  const [projectId, setProjectId] = useState('');
  const [serviceAccountKey, setServiceAccountKey] = useState('');
  const [fileName, setFileName] = useState('');

  const validate = useValidateProvider();

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setServiceAccountKey(content);
    };
    reader.readAsText(file);
  };

  const handleValidate = () => {
    if (!projectId || !serviceAccountKey) return;

    validate.mutate(
      {
        provider_type: ProviderType.GCP,
        name: `GCP ${projectId}`,
        config: {
          project_id: projectId,
          service_account_key_json: serviceAccountKey,
        },
      },
      {
        onSuccess: (result) => {
          if (result.success) {
            onValidated({
              project_id: projectId,
              service_account_key_json: serviceAccountKey,
            });
          }
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Connect GCP Project</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Create a service account with read-only access to your GCP resources
        </p>
      </div>

      <div className="rounded-lg border bg-muted/50 p-4 text-sm">
        <p className="font-medium">Create Service Account:</p>
        <ol className="mt-2 list-inside list-decimal space-y-1 text-muted-foreground">
          <li>Go to GCP Console → IAM & Admin → Service Accounts</li>
          <li>Create new service account</li>
          <li>Grant Viewer role at project level</li>
          <li>Create and download JSON key</li>
        </ol>
        <a
          href="https://cloud.google.com/iam/docs/service-accounts-create"
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
          <Label htmlFor="project-id">Project ID</Label>
          <Input
            id="project-id"
            placeholder="my-gcp-project"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="service-account-key">Service Account Key (JSON)</Label>
          <div className="flex items-center gap-2">
            <Input
              id="service-account-key"
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
            <Button
              variant="outline"
              onClick={() => document.getElementById('service-account-key')?.click()}
              className="w-full"
            >
              <Upload className="mr-2 h-4 w-4" />
              {fileName || 'Upload JSON Key File'}
            </Button>
          </div>
          {fileName && (
            <p className="text-xs text-muted-foreground">
              Loaded: {fileName}
            </p>
          )}
        </div>

        <Button
          onClick={handleValidate}
          disabled={!projectId || !serviceAccountKey || validate.isPending}
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
