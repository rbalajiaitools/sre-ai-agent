'use client';

import Layout from '@/components/Layout';
import { Plug } from 'lucide-react';

export default function ConnectorsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Connectors</h1>
          <p className="text-gray-600 mt-2">Manage integrations</p>
        </div>

        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Plug className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Connectors Configured</h2>
          <p className="text-gray-600">
            Configure connectors to integrate with AWS, Azure, Slack, and more
          </p>
        </div>
      </div>
    </Layout>
  );
}
