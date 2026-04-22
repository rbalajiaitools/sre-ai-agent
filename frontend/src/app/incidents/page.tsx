'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { useAuthStore } from '@/store/auth';
import { AlertTriangle, Plus } from 'lucide-react';
import { formatRelativeTime } from '@/lib/utils';
import toast from 'react-hot-toast';

export default function IncidentsPage() {
  const user = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 3,
    category: '',
  });

  const { data: incidents, isLoading } = useQuery({
    queryKey: ['incidents', user?.tenant_id],
    queryFn: async () => {
      const res = await api.get('/incidents', {
        params: { tenant_id: user?.tenant_id, limit: 100 },
      });
      return res.data;
    },
    enabled: !!user,
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const res = await api.post('/incidents', data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      toast.success('Incident created');
      setShowCreate(false);
      setFormData({ title: '', description: '', priority: 3, category: '' });
    },
    onError: () => {
      toast.error('Failed to create incident');
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      tenant_id: user?.tenant_id,
      ...formData,
    });
  };

  const getPriorityColor = (priority: number) => {
    if (priority === 1) return 'bg-red-100 text-red-800';
    if (priority === 2) return 'bg-orange-100 text-orange-800';
    if (priority === 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'resolved': return 'bg-green-100 text-green-800';
      case 'investigating': return 'bg-blue-100 text-blue-800';
      case 'mitigated': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Incidents</h1>
            <p className="text-gray-600 mt-2">Track and manage incidents</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Incident
          </button>
        </div>

        {showCreate && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Create Incident</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>P1 - Critical</option>
                  <option value={2}>P2 - High</option>
                  <option value={3}>P3 - Medium</option>
                  <option value={4}>P4 - Low</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., infrastructure, application"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="bg-white rounded-lg shadow">
          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : incidents && incidents.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {incidents.map((incident: any) => (
                <div key={incident.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-gray-400" />
                        <span className="text-sm font-mono text-gray-500">{incident.number}</span>
                        <h3 className="text-lg font-semibold text-gray-900">{incident.title}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(incident.priority)}`}>
                          P{incident.priority}
                        </span>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStateColor(incident.state)}`}>
                          {incident.state}
                        </span>
                      </div>
                      {incident.description && (
                        <p className="text-gray-600 mt-2 ml-8">{incident.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-3 ml-8 text-sm text-gray-500">
                        <span>Opened {formatRelativeTime(incident.opened_at)}</span>
                        {incident.category && <span>Category: {incident.category}</span>}
                        {incident.affected_services?.length > 0 && (
                          <span>Services: {incident.affected_services.length}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-gray-500">
              No incidents yet. Create one to get started.
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
