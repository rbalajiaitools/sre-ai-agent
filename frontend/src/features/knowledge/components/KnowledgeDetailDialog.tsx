/**
 * Knowledge Detail Dialog
 */
import { X, ExternalLink, Edit, Trash2, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Knowledge } from '../api';
import { useDeleteKnowledge } from '../hooks';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';

interface KnowledgeDetailDialogProps {
  knowledge: Knowledge;
  open: boolean;
  onClose: () => void;
}

export function KnowledgeDetailDialog({
  knowledge,
  open,
  onClose,
}: KnowledgeDetailDialogProps) {
  const deleteMutation = useDeleteKnowledge();

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this knowledge?')) {
      await deleteMutation.mutateAsync(knowledge.id);
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b">
          <div className="flex-1">
            <h2 className="text-2xl font-semibold mb-2">{knowledge.title}</h2>
            {knowledge.description && (
              <p className="text-sm text-gray-600">{knowledge.description}</p>
            )}
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
              <span>Type: {knowledge.type}</span>
              {knowledge.service_name && <span>Service: {knowledge.service_name}</span>}
              <span>Created: {format(new Date(knowledge.created_at), 'MMM dd, yyyy')}</span>
              {knowledge.created_by && <span>By: {knowledge.created_by}</span>}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Tags */}
          {knowledge.tags && knowledge.tags.length > 0 && (
            <div className="flex items-center gap-2 mb-6 flex-wrap">
              {knowledge.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Usage Stats */}
          {knowledge.usage_count > 0 && (
            <div className="bg-teal-50 border border-teal-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2 text-teal-800">
                <TrendingUp className="h-5 w-5" />
                <span className="font-medium">
                  Used {knowledge.usage_count} time{knowledge.usage_count !== 1 ? 's' : ''} in investigations
                </span>
              </div>
              {knowledge.last_used_at && (
                <p className="text-sm text-teal-700 mt-1">
                  Last used: {format(new Date(knowledge.last_used_at), 'MMM dd, yyyy')}
                </p>
              )}
            </div>
          )}

          {/* External Link */}
          {knowledge.external_url && (
            <div className="mb-6">
              <a
                href={knowledge.external_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-teal-600 hover:text-teal-700 font-medium"
              >
                <ExternalLink className="h-4 w-4" />
                Open External Link
              </a>
            </div>
          )}

          {/* Markdown Content */}
          {knowledge.content && (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{knowledge.content}</ReactMarkdown>
            </div>
          )}

          {!knowledge.content && !knowledge.external_url && (
            <p className="text-sm text-gray-500 italic">No content available</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <Button
            variant="outline"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="gap-2 text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <Trash2 className="h-4 w-4" />
            Delete
          </Button>
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
