'use client';

import Layout from '@/components/Layout';
import { Settings, Plug, Shield, FileText, Key } from 'lucide-react';
import Link from 'next/link';

export default function AdminPage() {
  const sections = [
    {
      name: 'Connectors',
      description: 'Manage integrations with cloud providers and tools',
      icon: Plug,
      href: '/admin/connectors',
      color: 'bg-blue-500',
    },
    {
      name: 'Policies',
      description: 'Configure governance and approval policies',
      icon: Shield,
      href: '/admin/policies',
      color: 'bg-green-500',
    },
    {
      name: 'Audit Logs',
      description: 'View system audit trail and activity logs',
      icon: FileText,
      href: '/admin/audit',
      color: 'bg-purple-500',
    },
    {
      name: 'Settings',
      description: 'Tenant configuration and preferences',
      icon: Settings,
      href: '/admin/settings',
      color: 'bg-orange-500',
    },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Administration</h1>
          <p className="text-gray-600 mt-2">Platform configuration and management</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <Link
                key={section.name}
                href={section.href}
                className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start gap-4">
                  <div className={`${section.color} p-3 rounded-lg`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">
                      {section.name}
                    </h2>
                    <p className="text-gray-600">{section.description}</p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </Layout>
  );
}
