/**
 * Cloud Provider Settings Component - List and manage cloud provider integrations
 */
import { useState, useEffect } from 'react';
import { useAuth } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Plus, Trash2, Check, X } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  getIntegrations,
  testCloudProvider,
  saveCloudProvider,
  deleteIntegration,
  type Integration,
} from '../api';

export function CloudProviderSettings() {
  const { user, tenant } = useAuth();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  // Form state
  const [name, setName] = useState('');
  const [provider, setProvider] = useState<'aws' | 'azure' | 'gcp'>('aws');
  const [accessKeyId, setAccessKeyId] = useState('');
  const [secretAccessKey, setSecretAccessKey] = useState('');
  const [region, setRegion] = useState('us-east-1');
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    loadIntegrations();
  }, [tenant]);

  const loadIntegrations = async () => {
    if (!tenant?.id) return;
    
    try {
      setLoading(true);
      const data = await getIntegrations(tenant.id);
      // Filter cloud providers (aws, azure, gcp)
      const cloudIntegrations = data.filter(i => ['aws', 'azure', 'gcp'].includes(i.type));
      setIntegrations(cloudIntegrations);
    } catch (error) {
      console.error('Failed to load integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (provider === 'aws') {
      if (!accessKeyId || !secretAccessKey || !region) {
        setTestResult({ success: false, message: 'Please fill in all AWS fields' });
        return;
      }
    }

    setTesting(true);
    setTestResult(null);

    try {
      const result = await testCloudProvider({
        provider,
        credentials: {
          access_key_id: accessKeyId,
          secret_access_key: secretAccessKey,
          region,
        },
      });
      setTestResult(result);
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Connection test failed',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!tenant?.id || !name) {
      setTestResult({ success: false, message: 'Please provide an integration name' });
      return;
    }

    if (provider === 'aws' && (!accessKeyId || !secretAccessKey || !region)) {
      setTestResult({ success: false, message: 'Please fill in all AWS fields' });
      return;
    }

    setSaving(true);

    try {
      await saveCloudProvider(tenant.id, name, {
        provider,
        credentials: {
          access_key_id: accessKeyId,
          secret_access_key: secretAccessKey,
          region,
        },
      });

      setTestResult({ success: true, message: 'Configuration saved successfully!' });
      
      // Reset form
      setName('');
      setAccessKeyId('');
      setSecretAccessKey('');
      setRegion('us-east-1');
      setShowForm(false);
      
      // Reload integrations
      await loadIntegrations();
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to save configuration',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this integration?')) return;

    try {
      await deleteIntegration(id);
      await loadIntegrations();
    } catch (error) {
      console.error('Failed to delete integration:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Cloud Provider Integrations</h3>
          <p className="text-sm text-gray-500">
            Connect AWS, Azure, or GCP to analyze infrastructure
          </p>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Integration
          </Button>
        )}
      </div>

      {/* Existing Integrations */}
      {integrations.length > 0 && (
        <div className="space-y-4">
          {integrations.map((integration) => (
            <Card key={integration.id} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h4 className="font-medium">{integration.name}</h4>
                    <span className="inline-flex items-center rounded-full bg-lime-100 px-2 py-1 text-xs font-medium text-lime-700 uppercase">
                      {integration.type}
                    </span>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                        integration.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {integration.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">
                    Created {new Date(integration.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(integration.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-600" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add New Integration Form */}
      {showForm && (
        <Card className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium">Add Cloud Provider Integration</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowForm(false);
                  setTestResult(null);
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Integration Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Production AWS"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="provider">Provider</Label>
                <Select value={provider} onValueChange={(v: any) => setProvider(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="aws">AWS</SelectItem>
                    <SelectItem value="azure">Azure (Coming Soon)</SelectItem>
                    <SelectItem value="gcp">GCP (Coming Soon)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {provider === 'aws' && (
                <>
                  <div>
                    <Label htmlFor="accessKey">Access Key ID</Label>
                    <Input
                      id="accessKey"
                      placeholder="AKIA..."
                      value={accessKeyId}
                      onChange={(e) => setAccessKeyId(e.target.value)}
                    />
                  </div>

                  <div>
                    <Label htmlFor="secretKey">Secret Access Key</Label>
                    <Input
                      id="secretKey"
                      type="password"
                      placeholder="••••••••"
                      value={secretAccessKey}
                      onChange={(e) => setSecretAccessKey(e.target.value)}
                    />
                  </div>

                  <div>
                    <Label htmlFor="region">Region</Label>
                    <Select value={region} onValueChange={setRegion}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="us-east-1">US East (N. Virginia)</SelectItem>
                        <SelectItem value="us-east-2">US East (Ohio)</SelectItem>
                        <SelectItem value="us-west-1">US West (N. California)</SelectItem>
                        <SelectItem value="us-west-2">US West (Oregon)</SelectItem>
                        <SelectItem value="eu-west-1">EU (Ireland)</SelectItem>
                        <SelectItem value="eu-central-1">EU (Frankfurt)</SelectItem>
                        <SelectItem value="ap-south-1">Asia Pacific (Mumbai)</SelectItem>
                        <SelectItem value="ap-southeast-1">Asia Pacific (Singapore)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              {testResult && (
                <Alert variant={testResult.success ? 'default' : 'destructive'}>
                  <AlertDescription>{testResult.message}</AlertDescription>
                </Alert>
              )}

              <div className="flex gap-3">
                <Button onClick={handleTest} disabled={testing || saving} variant="outline">
                  {testing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    'Test Connection'
                  )}
                </Button>

                <Button onClick={handleSave} disabled={testing || saving}>
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      Save
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Empty State */}
      {integrations.length === 0 && !showForm && (
        <Card className="p-12 text-center">
          <p className="text-gray-500">No cloud provider integrations configured</p>
          <Button className="mt-4" onClick={() => setShowForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Your First Integration
          </Button>
        </Card>
      )}
    </div>
  );
}
