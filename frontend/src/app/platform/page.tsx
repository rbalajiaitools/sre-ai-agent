'use client';

import Layout from '@/components/Layout';
import { Activity, Database, Zap, MessageSquare } from 'lucide-react';

export default function PlatformPage() {
  const services = [
    { name: 'API Gateway', port: 8000, status: 'running', icon: Activity },
    { name: 'Auth Service', port: 8009, status: 'running', icon: Activity },
    { name: 'Alert Service', port: 8001, status: 'running', icon: Activity },
    { name: 'Investigation Engine', port: 8002, status: 'running', icon: Activity },
    { name: 'AI Engine', port: 8003, status: 'running', icon: Activity },
    { name: 'Knowledge Graph', port: 8004, status: 'running', icon: Activity },
    { name: 'Action Engine', port: 8005, status: 'running', icon: Activity },
    { name: 'Admin Service', port: 8006, status: 'running', icon: Activity },
    { name: 'Notification Service', port: 8007, status: 'running', icon: Activity },
    { name: 'Eval Service', port: 8008, status: 'running', icon: Activity },
    { name: 'Eraser Service', port: 8010, status: 'running', icon: Activity },
  ];

  const infrastructure = [
    { name: 'PostgreSQL', port: 5432, status: 'running', icon: Database },
    { name: 'Redis', port: 6379, status: 'running', icon: Database },
    { name: 'Kafka', port: 9092, status: 'running', icon: MessageSquare },
    { name: 'Temporal', port: 7233, status: 'running', icon: Zap },
  ];

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Platform Overview</h1>
          <p className="text-gray-600 mt-2">System health and infrastructure status</p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Application Services</h2>
          <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
            {services.map((service) => {
              const Icon = service.icon;
              return (
                <div key={service.name} className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900">{service.name}</p>
                      <p className="text-sm text-gray-500">Port {service.port}</p>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    {service.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Infrastructure</h2>
          <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
            {infrastructure.map((infra) => {
              const Icon = infra.icon;
              return (
                <div key={infra.name} className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900">{infra.name}</p>
                      <p className="text-sm text-gray-500">Port {infra.port}</p>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    {infra.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Layout>
  );
}
