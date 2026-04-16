/**
 * API Keys View - Manage API keys for programmatic access
 */
import { PageHeader } from '@/components/shared/PageHeader';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Copy, Trash2, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';

// Dummy data
const API_KEYS = [
  {
    id: '1',
    name: 'Production API Key',
    key: 'ak_prod_1234567890abcdef',
    created: '2024-01-15',
    lastUsed: '2 hours ago',
    status: 'Active',
  },
  {
    id: '2',
    name: 'Development API Key',
    key: 'ak_dev_abcdef1234567890',
    created: '2024-02-01',
    lastUsed: '1 day ago',
    status: 'Active',
  },
  {
    id: '3',
    name: 'Testing API Key',
    key: 'ak_test_fedcba0987654321',
    created: '2024-03-10',
    lastUsed: 'Never',
    status: 'Inactive',
  },
];

export function ApiKeysView() {
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());

  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  const maskKey = (key: string) => {
    return key.substring(0, 12) + '••••••••••••••••';
  };

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="API Keys"
        description="Manage API keys for programmatic access to Astra AI."
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Header Actions */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">
                API keys allow you to authenticate requests to the Astra AI API.
              </p>
            </div>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create API Key
            </Button>
          </div>

          {/* API Keys List */}
          <div className="space-y-4">
            {API_KEYS.map((apiKey) => (
              <Card key={apiKey.id} className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h4 className="font-semibold text-gray-900">{apiKey.name}</h4>
                      <Badge
                        variant={apiKey.status === 'Active' ? 'default' : 'secondary'}
                        className={
                          apiKey.status === 'Active'
                            ? 'bg-green-100 text-green-800 hover:bg-green-100'
                            : 'bg-gray-100 text-gray-700'
                        }
                      >
                        {apiKey.status}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-2 mb-3">
                      <code className="flex-1 rounded bg-gray-100 px-3 py-2 text-sm font-mono text-gray-800">
                        {visibleKeys.has(apiKey.id) ? apiKey.key : maskKey(apiKey.key)}
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleKeyVisibility(apiKey.id)}
                      >
                        {visibleKeys.has(apiKey.id) ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </Button>
                      <Button variant="outline" size="sm">
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>Created: {apiKey.created}</span>
                      <span>•</span>
                      <span>Last used: {apiKey.lastUsed}</span>
                    </div>
                  </div>

                  <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700 hover:bg-red-50">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>

          {/* Info Card */}
          <Card className="bg-blue-50 border-blue-200 p-5">
            <h4 className="font-semibold text-blue-900 mb-2">Security Best Practices</h4>
            <ul className="space-y-1 text-sm text-blue-800">
              <li>• Never share your API keys publicly or commit them to version control</li>
              <li>• Rotate your API keys regularly to maintain security</li>
              <li>• Use different API keys for different environments (production, development, testing)</li>
              <li>• Revoke any API keys that may have been compromised immediately</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
