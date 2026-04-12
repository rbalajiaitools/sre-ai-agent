/**
 * AWS provider configuration form
 */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ProviderType } from '@/types';
import { useGenerateTerraform, useValidateProvider } from '../hooks';
import { ValidationResultCard } from './ValidationResultCard';
import { TerraformTab } from './TerraformTab';
import type { AWSConfig } from '../types';

interface AWSProviderFormProps {
  onValidated: (config: AWSConfig) => void;
}

const AWS_REGIONS = [
  'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
  'eu-west-1', 'eu-west-2', 'eu-central-1',
  'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
];

export function AWSProviderForm({ onValidated }: AWSProviderFormProps) {
  const [accountId, setAccountId] = useState('');
  const [roleArn, setRoleArn] = useState('');
  const [region, setRegion] = useState('us-east-1');

  const generateTf = useGenerateTerraform();
  const validate = useValidateProvider();

  const handleGenerateTerraform = () => {
    if (!accountId) return;
    generateTf.mutate({
      providerType: ProviderType.AWS,
      params: { account_id: accountId },
    });
  };

  const handleValidate = () => {
    if (!roleArn || !region) return;

    const externalId = generateTf.data?.hcl.match(/external_id\s*=\s*"([^"]+)"/)?.[1] || '';

    validate.mutate(
      {
        provider_type: ProviderType.AWS,
        name: `AWS ${region}`,
        config: {
          role_arn: roleArn,
          external_id: externalId,
          region,
          account_id: accountId,
        },
      },
      {
        onSuccess: (result) => {
          if (result.success) {
            onValidated({
              role_arn: roleArn,
              external_id: externalId,
              region,
              account_id: accountId,
            });
          }
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Connect AWS Account</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          We need read-only access to your AWS account for monitoring and analysis
        </p>
      </div>

      <Tabs defaultValue="terraform">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="terraform">Use Terraform (Recommended)</TabsTrigger>
          <TabsTrigger value="manual">Manual Setup</TabsTrigger>
        </TabsList>

        <TabsContent value="terraform" className="space-y-4">
          <TerraformTab
            accountId={accountId}
            onAccountIdChange={setAccountId}
            terraformCode={generateTf.data?.hcl || null}
            onGenerateTerraform={handleGenerateTerraform}
            isGenerating={generateTf.isPending}
            roleArn={roleArn}
            onRoleArnChange={setRoleArn}
            region={region}
            onRegionChange={setRegion}
            regions={AWS_REGIONS}
            onValidate={handleValidate}
            isValidating={validate.isPending}
          />

          <ValidationResultCard
            result={validate.data || null}
            isLoading={validate.isPending}
            error={validate.error?.message}
          />
        </TabsContent>

        <TabsContent value="manual" className="space-y-4">
          <div className="rounded-lg border bg-muted/50 p-4 text-sm">
            <p className="font-medium">Manual IAM Role Setup:</p>
            <ol className="mt-2 list-inside list-decimal space-y-1 text-muted-foreground">
              <li>Go to AWS IAM Console → Roles → Create Role</li>
              <li>Select "Another AWS account" as trusted entity</li>
              <li>Attach ReadOnlyAccess policy</li>
              <li>Add CloudWatch and CloudTrail read permissions</li>
              <li>Copy the Role ARN and paste below</li>
            </ol>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="manual-role-arn">Role ARN</Label>
              <Input
                id="manual-role-arn"
                placeholder="arn:aws:iam::123456789012:role/SREAgentRole"
                value={roleArn}
                onChange={(e) => setRoleArn(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="manual-region">Region</Label>
              <select
                id="manual-region"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              >
                {AWS_REGIONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            <Button onClick={handleValidate} disabled={!roleArn || validate.isPending}>
              Validate Connection
            </Button>

            <ValidationResultCard
              result={validate.data || null}
              isLoading={validate.isPending}
              error={validate.error?.message}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
