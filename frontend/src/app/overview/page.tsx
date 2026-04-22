'use client';

import { useQuery } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { AlertTriangle, Search, Zap, TrendingUp } from 'lucide-react';

export default function OverviewPage() {
  const user = useAuthStore((state) => state.user);

  const { data: investigations } = useQuery({
    queryKey: ['investigations', user?.tenant_id],
    queryFn: async () => {
      const res = await api.get('/investigations', {
        params: { tenant_id: user?.tenant_id, limit: 5 },
      });
      return res.data;
    },
    enabled: !!user,
  });

  const { data: alerts } = useQuery({
    queryKey: ['alerts', user?.tenant_id],
    queryFn: async () => {
      const res = await api.get('/alerts', {
        params: { tenant_id: user?.tenant_id, limit: 5 },
      });
      return res.data;
    },
    enabled: !!user,
  });

  const { data: incidents } = useQuery({
    queryKey: ['incidents', user?.tenant_id],
    queryFn: async () => {
      const res = await api.get('/incidents', {
        params: { tenant_id: user?.tenant_id, limit: 5 },
      });
      return res.data;
    },
    enabled: !!user,
  });

  const stats = [
    {
      name: 'Active Investigations',
      value: investigations?.filter((i: any) => i.status === 'running').length || 0,
      icon: Search,
      color: 'bg-blue-500',
    },
    {
      name: 'Open Incidents',
      value: incidents?.filter((i: any) => i.state !== 'resolved').length || 0,
      icon: AlertTriangle,
      color: 'bg-red-500',
    },
    {
      name: 'Open Alerts',
      value: alerts?.filter((a: any) => a.status === 'open').length || 0,
      icon: AlertTriangle,
      color: 'bg-yellow-500',
    },
    {
      name: 'Actions Pending',
      value: 0,
      icon: Zap,
      color: 'bg-green-500',
    },
  ];

  return (
    <Layout>
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Overview</h1>
          <p className="text-gray-600 mt-2">Welcome back, {user?.full_name}</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.name} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">{stat.name}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  </div>
                  <div className={`${stat.color} p-3 rounded-lg`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Recent Investigations */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Investigations</h2>
          </div>
          <div className="p-6">
            {investigations && investigations.length > 0 ? (
              <div className="space-y-4">
                {investigations.map((inv: any) => (
                  <div key={inv.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div>
                      <h3 className="font-medium text-gray-900">{inv.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Status: <span className="capitalize">{inv.status}</span>
                      </p>
                    </div>
                    <a
                      href={`/investigations/${inv.id}`}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      View →
                    </a>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No investigations yet</p>
            )}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Alerts</h2>
          </div>
          <div className="p-6">
            {alerts && alerts.length > 0 ? (
              <div className="space-y-4">
                {alerts.map((alert: any) => (
                  <div key={alert.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div>
                      <h3 className="font-medium text-gray-900">{alert.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Severity: <span className="capitalize">{alert.severity}</span> • Source: {alert.source}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      alert.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                      alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No alerts yet</p>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
