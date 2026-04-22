'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import { CheckCircle } from 'lucide-react';

export default function SetupPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [credentials, setCredentials] = useState<any>(null);

  const handleBootstrap = async () => {
    setLoading(true);
    try {
      const response = await api.post('/bootstrap');
      setCredentials(response.data);
      setCompleted(true);
      toast.success('System bootstrapped successfully!');
    } catch (error: any) {
      if (error.response?.status === 400) {
        toast.error('System already bootstrapped');
        router.push('/login');
      } else {
        toast.error('Bootstrap failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">ASTRA AI Setup</h1>
          <p className="text-gray-600 mt-2">Initialize your platform</p>
        </div>

        {!completed ? (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                What will be created:
              </h2>
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  Default organization tenant
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  Admin user account
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-blue-600" />
                  Database schema initialization
                </li>
              </ul>
            </div>

            <button
              onClick={handleBootstrap}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? 'Initializing...' : 'Initialize Platform'}
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Setup Complete!
                </h2>
              </div>
              <p className="text-gray-700 mb-4">
                Your ASTRA AI platform has been initialized successfully.
              </p>
              <div className="bg-white rounded-lg p-4 space-y-2">
                <p className="text-sm font-medium text-gray-700">Admin Credentials:</p>
                <div className="font-mono text-sm">
                  <p>
                    <span className="text-gray-600">Email:</span>{' '}
                    <span className="font-semibold">{credentials?.admin_email}</span>
                  </p>
                  <p>
                    <span className="text-gray-600">Password:</span>{' '}
                    <span className="font-semibold">{credentials?.admin_password}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    Tenant ID: {credentials?.tenant_id}
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => router.push('/login')}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Go to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
