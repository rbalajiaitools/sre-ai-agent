/**
 * Integration Dialog - Modal for configuring integrations
 */
import { useState, useEffect } from 'react';
import { useAuth } from '@/stores/authStore';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, Check, Trash2, Plus, Edit2, ArrowLeft } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  testServiceNow,
  saveServiceNow,
  testCloudProvider,
  saveCloudProvider,
  deleteIntegration,
  getIntegrations,
  type Integration,
} from '../api';

interface IntegrationDialogProps {
  integrationId: string;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type ViewMode = 'list' | 'create' | 'edit';

export function IntegrationDialog({
  integrationId,
  open,
  onClose,
  onSuccess,
}: IntegrationDialogProps) {
  const { tenant } = useAuth();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [existingIntegrations, setExistingIntegrations] = useState<Integration[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('list');

  // Form state
  const [name, setName] = useState('');
  const [instanceUrl, setInstanceUrl] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [accessKeyId, setAccessKeyId] = useState('');
  const [secretAccessKey, setSecretAccessKey] = useState('');
  const [region, setRegion] = useState('us-east-1');

  useEffect(() => {
    if (open && tenant?.id) {
      loadExistingIntegrations();
    }
  }, [open, integrationId, tenant]);

  useEffect(() => {
    // Reset view mode when dialog opens
    if (open) {
      setViewMode('list');
      resetForm();
    }
  }, [open]);

  const loadExistingIntegrations = async () => {
    if (!tenant?.id) return;

    try {
      setLoading(true);
      const integrations = await getIntegrations(tenant.id);
      const filtered = integrations.filter(i => i.type === integrationId);
      setExistingIntegrations(filtered);
      
      // If no integrations exist, go directly to create mode
      if (filtered.length === 0) {
        setViewMode('create');
      }
    } catch (error) {
      console.error('Failed to load integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setName('');
    setInstanceUrl('');
    setUsername('');
    setPassword('');
    setAccessKeyId('');
    setSecretAccessKey('');
    setRegion('us-east-1');
    setTestResult(null);
  };

  const handleEdit = (integration: Integration) => {
    setName(integration.name);
    setViewMode('edit');
    setTestResult(null);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      if (integrationId === 'servicenow') {
        if (!instanceUrl || !username || !password) {
          setTestResult({ success: false, message: 'Please fill in all fields' });
          return;
        }

        const result = await testServiceNow({
          instance_url: instanceUrl,
          username,
          password,
        });
        setTestResult(result);
      } else if (integrationId === 'aws') {
        if (!accessKeyId || !secretAccessKey || !region) {
          setTestResult({ success: false, message: 'Please fill in all AWS fields' });
          return;
        }

        const result = await testCloudProvider({
          provider: 'aws',
          credentials: {
            access_key_id: accessKeyId,
            secret_access_key: secretAccessKey,
            region,
          },
        });
        setTestResult(result);
      }
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

    setSaving(true);

    try {
      if (integrationId === 'servicenow') {
        if (!instanceUrl || !username || !password) {
          setTestResult({ success: false, message: 'Please fill in all fields' });
          return;
        }

        await saveServiceNow(tenant.id, name, {
          instance_url: instanceUrl,
          username,
          password,
        });
      } else if (integrationId === 'aws') {
        if (!accessKeyId || !secretAccessKey || !region) {
          setTestResult({ success: false, message: 'Please fill in all AWS fields' });
          return;
        }

        await saveCloudProvider(tenant.id, name, {
          provider: 'aws',
          credentials: {
            access_key_id: accessKeyId,
            secret_access_key: secretAccessKey,
            region,
          },
        });
      }

      setTestResult({ success: true, message: 'Configuration saved successfully!' });
      setTimeout(() => {
        onSuccess();
      }, 1000);
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.message || 'Failed to save configuration',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (integration: Integration) => {
    if (!confirm(`Are you sure you want to delete "${integration.name}"?`)) return;

    setDeleting(true);

    try {
      await deleteIntegration(integration.id);
      await loadExistingIntegrations();
      setTestResult({ success: true, message: 'Integration deleted successfully' });
      
      // If no more integrations, switch to create mode
      if (existingIntegrations.length === 1) {
        setViewMode('create');
      }
    } catch (error) {
      console.error('Failed to delete integration:', error);
      setTestResult({
        success: false,
        message: 'Failed to delete integration',
      });
    } finally {
      setDeleting(false);
    }
  };

  const renderForm = () => {
    if (integrationId === 'servicenow') {
      return (
        <>
          <div>
            <Label htmlFor="name">Integration Name</Label>
            <Input
              id="name"
              placeholder="e.g., Production ServiceNow"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="instance">Instance URL</Label>
            <Input
              id="instance"
              placeholder="https://your-instance.service-now.com"
              value={instanceUrl}
              onChange={(e) => setInstanceUrl(e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              placeholder="admin"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </>
      );
    }

    if (integrationId === 'aws') {
      return (
        <>
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
              <SelectTrigger id="region">
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
      );
    }

    return (
      <div className="py-8 text-center text-gray-500">
        This integration is not yet available. Coming soon!
      </div>
    );
  };

  const renderListView = () => {
    return (
      <div className="space-y-4">
        {existingIntegrations.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-700">Existing Integrations</h4>
            {existingIntegrations.map((integration) => (
              <Card key={integration.id} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-gray-900">{integration.name}</h4>
                      <Badge
                        variant={integration.is_active ? 'default' : 'secondary'}
                        className={
                          integration.is_active
                            ? 'bg-green-100 text-green-800 hover:bg-green-100'
                            : 'bg-gray-100 text-gray-700'
                        }
                      >
                        {integration.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      Created {new Date(integration.created_at).toLocaleDateString()}
                      {integration.last_sync_at && (
                        <> • Last synced {new Date(integration.last_sync_at).toLocaleString()}</>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(integration)}
                      disabled={deleting}
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(integration)}
                      disabled={deleting}
                    >
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        <Button
          onClick={() => {
            resetForm();
            setViewMode('create');
          }}
          className="w-full"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add New Integration
        </Button>
      </div>
    );
  };

  const renderFormView = () => {
    const isConfigurable = integrationId === 'servicenow' || integrationId === 'aws';

    return (
      <div className="space-y-4">
        {renderForm()}

        {testResult && (
          <Alert variant={testResult.success ? 'default' : 'destructive'}>
            <AlertDescription>{testResult.message}</AlertDescription>
          </Alert>
        )}

        {isConfigurable && (
          <div className="flex gap-3">
            <Button
              onClick={handleTest}
              disabled={testing || saving}
              variant="outline"
              className="flex-1"
            >
              {testing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                'Test Connection'
              )}
            </Button>

            <Button
              onClick={handleSave}
              disabled={testing || saving}
              className="flex-1"
            >
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
        )}

        {existingIntegrations.length > 0 && (
          <Button
            onClick={() => {
              resetForm();
              setViewMode('list');
            }}
            variant="outline"
            className="w-full"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to List
          </Button>
        )}
      </div>
    );
  };

  const getTitle = () => {
    const integrationName = integrationId.toUpperCase();
    if (viewMode === 'list') {
      return `${integrationName} Integrations`;
    } else if (viewMode === 'create') {
      return `Add ${integrationName} Integration`;
    } else {
      return `Edit ${integrationName} Integration`;
    }
  };

  const getDescription = () => {
    if (viewMode === 'list') {
      return 'Manage your existing integrations or add a new one';
    } else if (viewMode === 'create') {
      return 'Connect your account to enable this integration';
    } else {
      return 'Update your integration configuration';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{getTitle()}</DialogTitle>
          <DialogDescription>{getDescription()}</DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : (
          <>
            {viewMode === 'list' && renderListView()}
            {(viewMode === 'create' || viewMode === 'edit') && renderFormView()}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
