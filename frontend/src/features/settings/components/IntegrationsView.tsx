/**
 * Integrations View - Main integrations page with card-based layout
 */
import { useState, useEffect } from 'react';
import { useAuth } from '@/stores/authStore';
import { PageHeader } from '@/components/shared/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Loader2, Search, Grid3x3, List } from 'lucide-react';
import { getIntegrations, type Integration } from '../api';
import { IntegrationCard } from './IntegrationCard';
import { IntegrationDialog } from './IntegrationDialog';

// Define available integrations
const AVAILABLE_INTEGRATIONS = [
  {
    id: 'aws',
    name: 'AWS',
    description: 'Amazon Web Services cloud platform integration for EC2, Lambda,...',
    category: 'Infrastructure',
    icon: 'A',
    iconColor: 'bg-orange-500',
    available: true,
  },
  {
    id: 'servicenow',
    name: 'ServiceNow',
    description: 'Cloud-based platform for IT service management and IT operations...',
    category: 'Observability',
    icon: 'S',
    iconColor: 'bg-gray-700',
    available: true,
  },
  {
    id: 'grafana',
    name: 'Grafana',
    description: 'Open source observability platform for metrics, logs, and traces visualization',
    category: 'Observability',
    icon: 'G',
    iconColor: 'bg-orange-600',
    available: false,
  },
  {
    id: 'datadog',
    name: 'Datadog',
    description: 'Cloud monitoring and security platform for infrastructure and application...',
    category: 'Observability',
    icon: 'D',
    iconColor: 'bg-purple-600',
    available: false,
  },
  {
    id: 'pagerduty',
    name: 'PagerDuty',
    description: 'Digital operations management platform for incident response and...',
    category: 'Observability',
    icon: 'P',
    iconColor: 'bg-green-600',
    available: false,
  },
  {
    id: 'prometheus',
    name: 'Prometheus',
    description: 'Open-source monitoring system with a dimensional data model and powerful...',
    category: 'Observability',
    icon: 'P',
    iconColor: 'bg-gray-600',
    available: false,
  },
  {
    id: 'kubernetes',
    name: 'Kubernetes',
    description: 'Container orchestration platform for automating deployment and scaling',
    category: 'Infrastructure',
    icon: 'K',
    iconColor: 'bg-blue-600',
    available: false,
  },
  {
    id: 'elasticsearch',
    name: 'Elasticsearch',
    description: 'Distributed search and analytics engine for log management and search',
    category: 'Code',
    icon: 'E',
    iconColor: 'bg-teal-700',
    available: false,
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Business communication platform for team messaging and collaboration',
    category: 'Chat',
    icon: 'S',
    iconColor: 'bg-purple-700',
    available: false,
  },
  {
    id: 'splunk',
    name: 'Splunk',
    description: 'Data platform for monitoring, searching, and analyzing machine-...',
    category: 'Observability',
    icon: 'S',
    iconColor: 'bg-gray-700',
    available: false,
  },
  {
    id: 'newrelic',
    name: 'New Relic',
    description: 'Full-stack observability platform for application and infrastructure...',
    category: 'Observability',
    icon: 'N',
    iconColor: 'bg-gray-600',
    available: false,
  },
  {
    id: 'dynatrace',
    name: 'Dynatrace',
    description: 'AI-powered observability and application performance management...',
    category: 'Observability',
    icon: 'D',
    iconColor: 'bg-gray-600',
    available: false,
  },
  {
    id: 'loki',
    name: 'Loki',
    description: 'Log aggregation system designed to work with Grafana for log storage and...',
    category: 'Observability',
    icon: 'L',
    iconColor: 'bg-gray-600',
    available: false,
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'All-in-one workspace for notes, projects, wikis, and databases',
    category: 'Chat',
    icon: 'N',
    iconColor: 'bg-gray-700',
    available: false,
  },
  {
    id: 'linear',
    name: 'Linear',
    description: 'Issue tracking and project management tool for software teams',
    category: 'Code',
    icon: 'L',
    iconColor: 'bg-gray-600',
    available: false,
  },
  {
    id: 'opensearch',
    name: 'OpenSearch',
    description: 'Open-source search and analytics suite for log analytics and monitoring',
    category: 'Observability',
    icon: 'O',
    iconColor: 'bg-gray-600',
    available: false,
  },
];

const CATEGORIES = ['All', 'Observability', 'Infrastructure', 'Code', 'Chat'];

export function IntegrationsView() {
  const { tenant } = useAuth();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null);

  useEffect(() => {
    loadIntegrations();
  }, [tenant]);

  const loadIntegrations = async () => {
    if (!tenant?.id) return;
    
    try {
      setLoading(true);
      const data = await getIntegrations(tenant.id);
      setIntegrations(data);
    } catch (error) {
      console.error('Failed to load integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get connected integrations
  const connectedIntegrations = AVAILABLE_INTEGRATIONS.filter(ai =>
    integrations.some(i => i.type === ai.id && i.is_active)
  ).map(ai => {
    const integration = integrations.find(i => i.type === ai.id && i.is_active);
    return {
      ...ai,
      status: integration?.is_active ? 'connected' : 'warning',
      statusLabel: integration?.is_active ? 'Connected' : 'Warning',
      integrationId: integration?.id,
    };
  });

  // Get available integrations (not connected)
  const availableIntegrations = AVAILABLE_INTEGRATIONS.filter(ai =>
    !integrations.some(i => i.type === ai.id && i.is_active)
  );

  // Filter integrations based on category and search
  const filterIntegrations = (items: any[]) => {
    return items.filter(item => {
      const matchesCategory = selectedCategory === 'All' || item.category === selectedCategory;
      const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           item.description.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  };

  const filteredConnected = filterIntegrations(connectedIntegrations);
  const filteredAvailable = filterIntegrations(availableIntegrations);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Integrations"
        description="Connect integrations to give Astra AI access to your data and enhance investigations."
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-7xl space-y-6">
          {/* Filters */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {CATEGORIES.map(category => (
                <Button
                  key={category}
                  variant={selectedCategory === category ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedCategory(category)}
                >
                  {category}
                </Button>
              ))}
            </div>

            <div className="flex items-center gap-3">
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Search integrations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <div className="flex items-center gap-1 rounded-md border p-1">
                <Button
                  variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                  className="h-7 w-7 p-0"
                >
                  <Grid3x3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="h-7 w-7 p-0"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Connected Integrations */}
          {filteredConnected.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                CONNECTED
              </h2>
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' : 'space-y-3'}>
                {filteredConnected.map(integration => (
                  <IntegrationCard
                    key={integration.id}
                    integration={integration}
                    viewMode={viewMode}
                    onClick={() => setSelectedIntegration(integration.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Available Integrations */}
          {filteredAvailable.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                AVAILABLE
              </h2>
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' : 'space-y-3'}>
                {filteredAvailable.map(integration => (
                  <IntegrationCard
                    key={integration.id}
                    integration={integration}
                    viewMode={viewMode}
                    onClick={() => integration.available && setSelectedIntegration(integration.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {filteredConnected.length === 0 && filteredAvailable.length === 0 && (
            <Card className="p-12 text-center">
              <p className="text-gray-500">No integrations found matching your criteria</p>
            </Card>
          )}
        </div>
      </div>

      {/* Integration Dialog */}
      {selectedIntegration && (
        <IntegrationDialog
          integrationId={selectedIntegration}
          open={!!selectedIntegration}
          onClose={() => setSelectedIntegration(null)}
          onSuccess={() => {
            loadIntegrations();
            setSelectedIntegration(null);
          }}
        />
      )}
    </div>
  );
}
