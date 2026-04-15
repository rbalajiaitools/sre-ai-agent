/**
 * ServiceNow Settings Component - List and manage ServiceNow integrations
 */
import { useState, useEffect } from 'react';
import { useAuth } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Plus, Trash2, Edit2, Check, X } from 'lucide-react';
import {
  getIntegrations,
  testServiceNow,
  saveServiceNow,
  deleteIntegration,
  type Integration,
} from '../api';

export function ServiceNowSettings() {
  const { user, tenant } = useAuth();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  
  // Form state
  const [name, setName] = useState('');
  const [instanceUrl, setInstanceUrl] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
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
      const data = await getIntegrations(tenant.id, 'servicenow');
      setIntegrations(data);
    } catch (error) {
      console.error('Failed to load integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    if (!instanceUrl || !username || !password) {
      setTestResult({ success: false, message: 'Please fill in all fields' });
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const result = await testServiceNow({
        instance_url: instanceUrl,
        username,
        password,
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
    if (!tenant?.id || !name || !instanceUrl || !username || !password) {
      setTestResult({ success: false, message: 'Please fill in all fields including name' });
      return;
    }

    setSaving(true);

    try {
      await saveServiceNow(tenant.id, name, {
        instance_url: instanceUrl,
        username,
        password,
      });

      setTestResult({ success: true, message: 'Configuration saved successfully!' });
      
      // Reset form
      setName('');
      setInstanceUrl('');
      setUsername('');
      setPassword('');
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
          <h3 className="text-lg font-medium">ServiceNow Integrations</h3>
          <p className="text-sm text-gray-500">
            Connect your ServiceNow instances to pull incidents
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
                    {integration.last_sync_at && (
                      <> • Last synced {new Date(integration.last_sync_at).toLocaleString()}</>
                    )}
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
              <h4 className="font-medium">Add ServiceNow Integration</h4>
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
          <p className="text-gray-500">No ServiceNow integrations configured</p>
          <Button className="mt-4" onClick={() => setShowForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Your First Integration
          </Button>
        </Card>
      )}
    </div>
  );
}
