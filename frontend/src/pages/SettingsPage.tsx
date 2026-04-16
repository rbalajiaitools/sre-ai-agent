/**
 * Settings page - Configure integrations and system settings
 */
import { useState } from 'react';
import { IntegrationsView } from '@/features/settings/components/IntegrationsView';
import { UsersManagementView } from '@/features/settings/components/UsersManagementView';
import { ApiKeysView } from '@/features/settings/components/ApiKeysView';
import { ConfigurationView } from '@/features/settings/components/ConfigurationView';
import { cn } from '@/lib/utils';
import { Settings, Users, Key, Sliders } from 'lucide-react';

type SettingsSection = 'integrations' | 'users' | 'api-keys' | 'configuration';

const MENU_ITEMS = [
  {
    id: 'integrations' as SettingsSection,
    label: 'Integrations',
    icon: Settings,
  },
  {
    id: 'users' as SettingsSection,
    label: 'Users Management',
    icon: Users,
  },
  {
    id: 'api-keys' as SettingsSection,
    label: 'API Keys',
    icon: Key,
  },
  {
    id: 'configuration' as SettingsSection,
    label: 'Configuration',
    icon: Sliders,
  },
];

export function SettingsPage() {
  const [activeSection, setActiveSection] = useState<SettingsSection>('integrations');

  const renderContent = () => {
    switch (activeSection) {
      case 'integrations':
        return <IntegrationsView />;
      case 'users':
        return <UsersManagementView />;
      case 'api-keys':
        return <ApiKeysView />;
      case 'configuration':
        return <ConfigurationView />;
      default:
        return <IntegrationsView />;
    }
  };

  return (
    <div className="flex h-full">
      {/* Sidebar Menu */}
      <div className="w-64 border-r bg-gray-50/50 p-4">
        <div className="mb-6 px-3 pt-2">
          <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
          <p className="text-sm text-gray-500 mt-1">Manage your workspace</p>
        </div>
        <nav className="space-y-1">
          {MENU_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => setActiveSection(item.id)}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden">
        {renderContent()}
      </div>
    </div>
  );
}
