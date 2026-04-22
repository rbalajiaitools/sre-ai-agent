'use client';

import Layout from '@/components/Layout';
import { Map } from 'lucide-react';

export default function ServiceMapPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Service Map</h1>
          <p className="text-gray-600 mt-2">Topology visualization</p>
        </div>

        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Map className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Service Map Coming Soon</h2>
          <p className="text-gray-600">
            Interactive topology visualization will be available here
          </p>
        </div>
      </div>
    </Layout>
  );
}
