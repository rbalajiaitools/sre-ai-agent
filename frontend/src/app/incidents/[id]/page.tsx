'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { AlertTriangle, Clock, CheckCircle } from 'lucide-react';

export default function IncidentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: incident } = useQuery({
    queryKey: ['incident', id],
    queryFn: async () => {
      const res = await api.get(`/incidents/${id}`);
      return res.data;
    },
  });

  const { data: alerts } = useQuery({
    queryKey: ['incident-alerts', id],
    queryFn: async () => {
      const res = await api.get(`/alerts`, {
        params: { incident_id: id },
      });
      return res.data;
    },
  });

  if (!incident) {
    return (
      <Layout>
        <div className="text-center py-12">Loading...</div>
      </Layout>
    );
  }

  const getPriorityColor = (priority: number) => {
    if (priority === 1) return 'bg-red-100 text-red-800';
    if (priority === 2) return 'bg-orange-100 text-orange-800';
    if (priority === 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'resolved':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'investigating':
        return <Clock className="w-6 h-6 text-blue-500" />;
      default:
        return <AlertTriangle className="w-6 h-6 text-orange-500" />;
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                {getStateIcon(incident.state)}
                <span className="text-sm font-mono text-gray-500">{incident.number}</span>
                <h1 className="text-3xl font-bold text-gray-900">{incident.title}</h1>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(incident.priority)}`}>
                  P{incident.priority}
                </span>
              </div>
              {incident.description && (
                <p className="text-gray-700 mt-3">{incident.description}</p>
              )}
              <div className="flex items-center gap-6 mt-4 text-sm text-gray-500">
                <span>Opened: {formatDate(incident.opened_at)}</span>
                {incident.category && <span>Category: {incident.category}</span>}
                <span className="capitalize">State: {incident.state}</span>
              </div>
            </div>
          </div>
        </div>

        {incident.affected_services && incident.affected_services.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Affected Services</h2>
            <div className="flex flex-wrap gap-2">
              {incident.affected_services.map((service: string, idx: number) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                >
                  {service}
                </span>
              ))}
            </div>
          </div>
        )}

        {alerts && alerts.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Related Alerts</h2>
            <div className="space-y-3">
              {alerts.map((alert: any) => (
                <div key={alert.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">{alert.title}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Source: {alert.source} • Fired {formatDate(alert.fired_at)}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${
                      alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      alert.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                      alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Timeline</h2>
          <div className="space-y-4">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
              <div>
                <p className="font-medium text-gray-900">Incident opened</p>
                <p className="text-sm text-gray-600">{formatDate(incident.opened_at)}</p>
              </div>
            </div>
            {incident.state === 'resolved' && incident.resolved_at && (
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-2 h-2 bg-green-600 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-900">Incident resolved</p>
                  <p className="text-sm text-gray-600">{formatDate(incident.resolved_at)}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
