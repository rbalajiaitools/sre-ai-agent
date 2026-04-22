'use client';

import Layout from '@/components/Layout';
import { Zap } from 'lucide-react';

export default function ActionsPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Actions</h1>
          <p className="text-gray-600 mt-2">Remediation actions and workflows</p>
        </div>

        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Zap className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Actions Yet</h2>
          <p className="text-gray-600">
            Actions will appear here when investigations suggest remediations
          </p>
        </div>
      </div>
    </Layout>
  );
}
