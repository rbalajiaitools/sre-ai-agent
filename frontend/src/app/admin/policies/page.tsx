'use client';

import Layout from '@/components/Layout';
import { Shield } from 'lucide-react';

export default function PoliciesPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Policies</h1>
          <p className="text-gray-600 mt-2">Governance and approval policies</p>
        </div>

        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Policies Configured</h2>
          <p className="text-gray-600">
            Create policies to control action execution and approvals
          </p>
        </div>
      </div>
    </Layout>
  );
}
