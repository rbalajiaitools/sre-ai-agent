/**
 * ServiceNow configuration settings
 */
import { useState } from 'react';
import { Save, TestTube, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useServiceNowConfig, useTestServiceNow, useSaveServiceNow } from '../hooks';

export function ServiceNowSettings() {
  const configQuery = useServiceNowConfig();
  const testMutation = useTestServiceNow();
  const saveMutation = useSaveServiceNow();

  const [instanceUrl, setInstanceUrl] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Load existing config when available
  useState(() => {
    if (configQuery.data) {
      setInstanceUrl(configQuery.data.instance_url || '');
      setUsername(configQuery.data.username || '');
      // Don't load password for security
    }
  });

  const handleTest = async () => {
    await testMutation.mutateAsync({
      instance_url: instanceUrl,
      username,
      password,
    });
  };

  const handleSave = async () => {
    await saveMutation.mutateAsync({
      instance_url: instanceUrl,
      username,
      password,
    });
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold">ServiceNow Integration</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Connect to your ServiceNow instance to pull incidents automatically
        </p>
      </div>

      {configQuery.isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {!configQuery.isLoading && (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="snow-instance">Instance URL</Label>
            <Input
              id="snow-instance"
              type="url"
              placeholder="https://your-instance.service-now.com"
              value={instanceUrl}
              onChange={(e) => setInstanceUrl(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Your ServiceNow instance URL (e.g., https://dev12345.service-now.com)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="snow-username">Username</Label>
            <Input
              id="snow-username"
              type="text"
              placeholder="admin"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="snow-password">Password</Label>
            <Input
              id="snow-password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {/* Test Result */}
          {testMutation.isSuccess && (
            <div className="flex items-center gap-2 rounded-lg border border-green-500/50 bg-green-500/10 p-3 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span>Connection successful! ServiceNow is reachable.</span>
            </div>
          )}

          {testMutation.isError && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/50 bg-red-500/10 p-3 text-sm text-red-600">
              <XCircle className="h-4 w-4" />
              <span>Connection failed: {testMutation.error?.message}</span>
            </div>
          )}

          {/* Save Result */}
          {saveMutation.isSuccess && (
            <div className="flex items-center gap-2 rounded-lg border border-green-500/50 bg-green-500/10 p-3 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span>Configuration saved successfully!</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              onClick={handleTest}
              disabled={!instanceUrl || !username || !password || testMutation.isPending}
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
              onClick={handleSave}
              disabled={!instanceUrl || !username || !password || saveMutation.isPending}
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
        </div>
      )}
    </div>
  );
}
