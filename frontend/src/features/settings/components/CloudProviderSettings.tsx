/**
 * Cloud provider configuration settings
 */
import { useState } from 'react';
import { Save, TestTube, CheckCircle, XCircle, Loader2, Cloud } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useCloudProviderConfig, useTestCloudProvider, useSaveCloudProvider } from '../hooks';

export function CloudProviderSettings() {
  const [activeProvider, setActiveProvider] = useState('aws');
  const configQuery = useCloudProviderConfig();
  const testMutation = useTestCloudProvider();
  const saveMutation = useSaveCloudProvider();

  // AWS State
  const [awsAccessKey, setAwsAccessKey] = useState('');
  const [awsSecretKey, setAwsSecretKey] = useState('');
  const [awsRegion, setAwsRegion] = useState('us-east-1');

  const handleTestAWS = async () => {
    await testMutation.mutateAsync({
      provider: 'aws',
      credentials: {
        access_key_id: awsAccessKey,
        secret_access_key: awsSecretKey,
        region: awsRegion,
      },
    });
  };

  const handleSaveAWS = async () => {
    await saveMutation.mutateAsync({
      provider: 'aws',
      credentials: {
        access_key_id: awsAccessKey,
        secret_access_key: awsSecretKey,
        region: awsRegion,
      },
    });
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Cloud Provider Integration</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Connect your cloud provider to enable infrastructure monitoring and log analysis
        </p>
      </div>

      <Tabs value={activeProvider} onValueChange={setActiveProvider}>
        <TabsList>
          <TabsTrigger value="aws">
            <Cloud className="mr-2 h-4 w-4" />
            AWS
          </TabsTrigger>
          <TabsTrigger value="azure" disabled>
            <Cloud className="mr-2 h-4 w-4" />
            Azure (Coming Soon)
          </TabsTrigger>
          <TabsTrigger value="gcp" disabled>
            <Cloud className="mr-2 h-4 w-4" />
            GCP (Coming Soon)
          </TabsTrigger>
        </TabsList>

        <TabsContent value="aws" className="mt-6 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="aws-access-key">AWS Access Key ID</Label>
            <Input
              id="aws-access-key"
              type="text"
              placeholder="AKIAIOSFODNN7EXAMPLE"
              value={awsAccessKey}
              onChange={(e) => setAwsAccessKey(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Your AWS access key ID with permissions for CloudWatch, CloudTrail, and Cost Explorer
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="aws-secret-key">AWS Secret Access Key</Label>
            <Input
              id="aws-secret-key"
              type="password"
              placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
              value={awsSecretKey}
              onChange={(e) => setAwsSecretKey(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="aws-region">Default Region</Label>
            <select
              id="aws-region"
              value={awsRegion}
              onChange={(e) => setAwsRegion(e.target.value)}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            >
              <option value="us-east-1">US East (N. Virginia)</option>
              <option value="us-east-2">US East (Ohio)</option>
              <option value="us-west-1">US West (N. California)</option>
              <option value="us-west-2">US West (Oregon)</option>
              <option value="eu-west-1">EU (Ireland)</option>
              <option value="eu-central-1">EU (Frankfurt)</option>
              <option value="ap-south-1">Asia Pacific (Mumbai)</option>
              <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
            </select>
          </div>

          {/* Test Result */}
          {testMutation.isSuccess && testMutation.variables?.provider === 'aws' && (
            <div className="flex items-center gap-2 rounded-lg border border-green-500/50 bg-green-500/10 p-3 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span>AWS connection successful! Credentials are valid.</span>
            </div>
          )}

          {testMutation.isError && testMutation.variables?.provider === 'aws' && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-600">
              <XCircle className="h-4 w-4" />
              <span>AWS connection failed: {testMutation.error?.message}</span>
            </div>
          )}

          {/* Save Result */}
          {saveMutation.isSuccess && saveMutation.variables?.provider === 'aws' && (
            <div className="flex items-center gap-2 rounded-lg border border-green-500/50 bg-green-500/10 p-3 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span>AWS configuration saved successfully!</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              onClick={handleTestAWS}
              disabled={!awsAccessKey || !awsSecretKey || testMutation.isPending}
              variant="outline"
            >
              {testMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <TestTube className="mr-2 h-4 w-4" />
                  Test Connection
                </>
              )}
            </Button>

            <Button
              onClick={handleSaveAWS}
              disabled={!awsAccessKey || !awsSecretKey || saveMutation.isPending}
            >
              {saveMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Configuration
                </>
              )}
            </Button>
          </div>

          <div className="rounded-lg border bg-muted/50 p-4">
            <h4 className="text-sm font-medium mb-2">Required AWS Permissions</h4>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• CloudWatch Logs: Read access to log groups and streams</li>
              <li>• CloudWatch Metrics: Read access to metrics</li>
              <li>• CloudTrail: Read access to events</li>
              <li>• EC2: Describe instances, security groups, VPCs</li>
              <li>• RDS: Describe DB instances</li>
              <li>• Cost Explorer: Read cost and usage data</li>
            </ul>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
