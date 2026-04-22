'use client';

import { useState } from 'react';
import Layout from '@/components/Layout';
import { FileImage, Download } from 'lucide-react';

export default function ArchitecturePage() {
  const [generating, setGenerating] = useState(false);

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(() => {
      setGenerating(false);
    }, 2000);
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Architecture Diagram</h1>
          <p className="text-gray-600 mt-2">Generate system architecture diagrams</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Generate Diagram</h2>
          <p className="text-gray-600 mb-6">
            Create an architecture diagram based on your current service topology and dependencies.
          </p>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <FileImage className="w-5 h-5" />
            {generating ? 'Generating...' : 'Generate Diagram'}
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-12 text-center">
          <FileImage className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Architecture Diagram</h2>
          <p className="text-gray-600 mb-6">
            Your generated diagram will appear here
          </p>
          <div className="bg-gray-100 rounded-lg p-12 mb-6">
            <p className="text-gray-500">Diagram preview area</p>
          </div>
          <button className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 flex items-center gap-2 mx-auto">
            <Download className="w-5 h-5" />
            Download Diagram
          </button>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-2">About Architecture Diagrams</h3>
          <p className="text-gray-700 text-sm">
            ASTRA AI can automatically generate architecture diagrams based on your service topology,
            dependencies, and infrastructure configuration. The diagrams are created using the Eraser.io
            API and can be exported in various formats.
          </p>
        </div>
      </div>
    </Layout>
  );
}
