'use client';

import { useQuery } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { Activity, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

export default function ServiceHealthPage() {
  const user = useAuthStore((state) => state.user);

  const { data: healthData } = useQuery({
    queryKey: ['health-dashboard', user?.tenant_id],
    queryFn: async () => {
      const res = await api.get('/graph/health-dashboard', {
        params: { tenant_id: user?.tenant_id },
      });
      return res.data;
    },
    enabled: !!user,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="w-6 h-6 text-yellow-500" />;
      case 'down':
        return <XCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Activity className="w-6 h-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      case 'down':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Service Health Dashboard</h1>
          <p className="text-gray-600 mt-2">Real-time health monitoring</p>
        </div>

        {healthData && (
          <>
            {/* Overall Health */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Overall Health</h2>
              <div className="flex items-center gap-4">
                <div className="text-6xl font-bold" style={{ color: healthData.overall_health >= 0.9 ? '#10b981' : healthData.overall_health >= 0.7 ? '#f59e0b' : '#ef4444' }}>
                  {(healthData.overall_health * 100).toFixed(0)}%
                </div>
                <div>
                  <p className="text-gray-600">System Health Score</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Based on {healthData.services?.length || 0} services
                  </p>
                </div>
              </div>
            </div>

            {/* Service List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Services</h2>
              </div>
              <div className="divide-y divide-gray-200">
                {healthData.services?.map((service: any, idx: number) => (
                  <div key={idx} className="p-6 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 flex-1">
                        {getStatusIcon(service.status)}
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">{service.name}</h3>
                          <div className="flex items-center gap-4 mt-1">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(service.status)}`}>
                              {service.status}
                            </span>
                            <span className={`text-sm font-medium ${getHealthScoreColor(service.health_score)}`}>
                              Health: {(service.health_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="h-2 rounded-full"
                            style={{
                              width: `${service.health_score * 100}%`,
                              backgroundColor: service.health_score >= 0.9 ? '#10b981' : service.health_score >= 0.7 ? '#f59e0b' : '#ef4444'
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {!healthData && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Activity className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Health Data</h2>
            <p className="text-gray-600">Fetching service health information...</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
