'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import Layout from '@/components/Layout';
import api from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

export default function InvestigationDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [updates, setUpdates] = useState<string[]>([]);

  const { data: investigation, refetch } = useQuery({
    queryKey: ['investigation', id],
    queryFn: async () => {
      const res = await api.get(`/investigations/${id}`);
      return res.data;
    },
    refetchInterval: 2000,
  });

  const { data: hypotheses } = useQuery({
    queryKey: ['hypotheses', id],
    queryFn: async () => {
      const res = await api.get(`/investigations/${id}/hypotheses`);
      return res.data;
    },
    refetchInterval: 2000,
  });

  const { data: evidence } = useQuery({
    queryKey: ['evidence', id],
    queryFn: async () => {
      const res = await api.get(`/investigations/${id}/evidence`);
      return res.data;
    },
    refetchInterval: 2000,
  });

  useEffect(() => {
    if (!investigation) return;

    const eventSource = new EventSource(`/api/v1/investigations/${id}/stream`);

    eventSource.addEventListener('status_update', (e) => {
      setUpdates((prev) => [...prev, `Status: ${e.data}`]);
      refetch();
    });

    eventSource.addEventListener('completed', () => {
      setUpdates((prev) => [...prev, 'Investigation completed']);
      refetch();
    });

    eventSource.addEventListener('failed', () => {
      setUpdates((prev) => [...prev, 'Investigation failed']);
      refetch();
    });

    return () => eventSource.close();
  }, [id, investigation, refetch]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'failed': return <XCircle className="w-6 h-6 text-red-500" />;
      case 'running': return <Clock className="w-6 h-6 text-blue-500 animate-spin" />;
      default: return <AlertCircle className="w-6 h-6 text-gray-500" />;
    }
  };

  if (!investigation) {
    return (
      <Layout>
        <div className="text-center py-12">Loading...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3">
                {getStatusIcon(investigation.status)}
                <h1 className="text-3xl font-bold text-gray-900">{investigation.title}</h1>
              </div>
              {investigation.description && (
                <p className="text-gray-600 mt-3">{investigation.description}</p>
              )}
              <div className="flex items-center gap-6 mt-4 text-sm text-gray-500">
                <span>Started: {formatDate(investigation.started_at)}</span>
                {investigation.completed_at && (
                  <span>Completed: {formatDate(investigation.completed_at)}</span>
                )}
                {investigation.confidence_level && (
                  <span className="capitalize">
                    Confidence: {investigation.confidence_level} ({investigation.confidence_score?.toFixed(2)})
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {investigation.root_cause && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Root Cause</h2>
            <p className="text-gray-700">{investigation.root_cause}</p>
          </div>
        )}

        {investigation.recommendations && investigation.recommendations.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recommendations</h2>
            <ul className="space-y-2">
              {investigation.recommendations.map((rec: string, idx: number) => (
                <li key={idx} className="flex items-start">
                  <span className="text-blue-600 mr-2">•</span>
                  <span className="text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {hypotheses && hypotheses.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Hypotheses</h2>
            <div className="space-y-4">
              {hypotheses.map((hyp: any) => (
                <div key={hyp.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{hyp.hypothesis}</p>
                      {hyp.reasoning && (
                        <p className="text-sm text-gray-600 mt-2">{hyp.reasoning}</p>
                      )}
                    </div>
                    {hyp.is_validated && (
                      <CheckCircle className="w-5 h-5 text-green-500 ml-3" />
                    )}
                  </div>
                  {hyp.confidence_score && (
                    <p className="text-sm text-gray-500 mt-2">
                      Confidence: {(hyp.confidence_score * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {evidence && evidence.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Evidence</h2>
            <div className="space-y-4">
              {evidence.map((ev: any) => (
                <div key={ev.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-gray-900">{ev.source}</span>
                    <span className="text-xs text-gray-500 capitalize">{ev.evidence_type}</span>
                  </div>
                  <p className="text-gray-700">{ev.content}</p>
                  {ev.relevance_score && (
                    <p className="text-sm text-gray-500 mt-2">
                      Relevance: {(ev.relevance_score * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {updates.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Live Updates</h2>
            <div className="space-y-2">
              {updates.map((update, idx) => (
                <p key={idx} className="text-sm text-gray-600">
                  {update}
                </p>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
