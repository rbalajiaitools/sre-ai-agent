'use client';

import Layout from '@/components/Layout';
import { Book, ExternalLink, HelpCircle, FileText, Video } from 'lucide-react';

export default function HelpPage() {
  const sections = [
    {
      title: 'Getting Started',
      icon: Book,
      items: [
        { title: 'Quick Start Guide', description: 'Get up and running in 5 minutes' },
        { title: 'Platform Overview', description: 'Understanding ASTRA AI architecture' },
        { title: 'User Guide', description: 'Complete user documentation' },
      ],
    },
    {
      title: 'Features',
      icon: FileText,
      items: [
        { title: 'AI Investigations', description: 'How to use AI-driven investigations' },
        { title: 'Alert Management', description: 'Managing alerts and incidents' },
        { title: 'Service Topology', description: 'Understanding service dependencies' },
        { title: 'Action Workflows', description: 'Remediation and approval workflows' },
      ],
    },
    {
      title: 'Integrations',
      icon: ExternalLink,
      items: [
        { title: 'AWS Connector', description: 'Integrate with AWS services' },
        { title: 'Slack Integration', description: 'Send notifications to Slack' },
        { title: 'GitHub Integration', description: 'Create PRs and track deployments' },
        { title: 'Custom Connectors', description: 'Build your own integrations' },
      ],
    },
    {
      title: 'Tutorials',
      icon: Video,
      items: [
        { title: 'Creating Your First Investigation', description: 'Step-by-step tutorial' },
        { title: 'Setting Up Connectors', description: 'Configure cloud integrations' },
        { title: 'Policy Management', description: 'Define governance policies' },
      ],
    },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Help & Documentation</h1>
          <p className="text-gray-600 mt-2">Learn how to use ASTRA AI</p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <HelpCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Need Help?</h2>
              <p className="text-gray-700 mb-3">
                ASTRA AI is an autonomous SRE platform that helps you investigate incidents,
                analyze root causes, and automate remediation workflows.
              </p>
              <div className="flex gap-3">
                <a
                  href="https://docs.astra.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center gap-1"
                >
                  View Full Documentation
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </div>

        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <div key={section.title} className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <Icon className="w-6 h-6 text-gray-600" />
                  <h2 className="text-xl font-semibold text-gray-900">{section.title}</h2>
                </div>
              </div>
              <div className="divide-y divide-gray-200">
                {section.items.map((item, idx) => (
                  <div key={idx} className="p-6 hover:bg-gray-50 cursor-pointer">
                    <h3 className="font-medium text-gray-900 mb-1">{item.title}</h3>
                    <p className="text-sm text-gray-600">{item.description}</p>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Links</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href="/api/v1/docs"
              target="_blank"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <FileText className="w-5 h-5 text-gray-600" />
              <div>
                <p className="font-medium text-gray-900">API Documentation</p>
                <p className="text-sm text-gray-600">OpenAPI/Swagger docs</p>
              </div>
            </a>
            <a
              href="https://github.com/cloudscore/astra-ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <ExternalLink className="w-5 h-5 text-gray-600" />
              <div>
                <p className="font-medium text-gray-900">GitHub Repository</p>
                <p className="text-sm text-gray-600">Source code and examples</p>
              </div>
            </a>
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-2">System Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Version</p>
              <p className="font-medium text-gray-900">0.1.0</p>
            </div>
            <div>
              <p className="text-gray-600">API Gateway</p>
              <p className="font-medium text-gray-900">http://localhost:8000</p>
            </div>
            <div>
              <p className="text-gray-600">Services</p>
              <p className="font-medium text-gray-900">11 microservices</p>
            </div>
            <div>
              <p className="text-gray-600">Status</p>
              <p className="font-medium text-green-600">All systems operational</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
