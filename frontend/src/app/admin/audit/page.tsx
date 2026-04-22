'use client';

import Layout from '@/components/Layout';
import { FileText } from 'lucide-react';

export default function AuditPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
          <p className="text-gray-600 mt-2">System activity and audit trail</p>
        </div>

        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Audit Logs</h2>
          <p className="text-gray-600">
            Audit logs will appear here as actions are performed
          </p>
        </div>
      </div>
    </Layout>
  );
}
