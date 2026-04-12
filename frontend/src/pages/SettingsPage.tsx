/**
 * Settings page - Configure integrations
 */
import { useState } from 'react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ServiceNowSettings } from '@/features/settings/components/ServiceNowSettings';
import { CloudProviderSettings } from '@/features/settings/components/CloudProviderSettings';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('servicenow');

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Settings"
        description="Configure ServiceNow and cloud provider integrations"
      />

      <div className="flex-1 overflow-auto p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="servicenow">ServiceNow</TabsTrigger>
            <TabsTrigger value="cloud">Cloud Providers</TabsTrigger>
          </TabsList>

          <TabsContent value="servicenow" className="mt-6">
            <ServiceNowSettings />
          </TabsContent>

          <TabsContent value="cloud" className="mt-6">
            <CloudProviderSettings />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
