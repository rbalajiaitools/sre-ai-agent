'use client';

import Layout from '@/components/Layout';
import { Network, Map } from 'lucide-react';
import Link from 'next/link';

export default function ServicesPage() {
  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Services</h1>
          <p className="text-gray-600 mt-2">Service catalog and topology</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link
            href="/services/map"
            className="bg-white rounded-lg shadow p-8 hover:shadow-lg transition-shadow"
          >
            <Map className="w-12 h-12 text-blue-600 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Service Map</h2>
            <p className="text-gray-600">
              Visualize service topology and dependencies
            </p>
          </Link>

          <div className="bg-white rounded-lg shadow p-8">
            <Network className="w-12 h-12 text-green-600 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Service Catalog</h2>
            <p className="text-gray-600">
              Browse and manage registered services
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Network className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Services Registered</h2>
          <p className="text-gray-600">
            Services will appear here once they are registered in the knowledge graph
          </p>
        </div>
      </div>
    </Layout>
  );
}
