/**
 * Related Knowledge Component - Shows relevant knowledge for investigation
 */
import { useEffect } from 'react';
import { BookOpen, ExternalLink, TrendingUp } from 'lucide-react';
import { useSearchKnowledge } from '@/features/knowledge/hooks';
import { useNavigate } from 'react-router-dom';

interface RelatedKnowledgeProps {
  serviceName?: string;
  incidentNumber?: string;
}

export function RelatedKnowledge({ serviceName, incidentNumber }: RelatedKnowledgeProps) {
  const searchMutation = useSearchKnowledge();
  const navigate = useNavigate();

  useEffect(() => {
    // Search for relevant knowledge when component mounts
    if (serviceName || incidentNumber) {
      searchMutation.mutate({
        service_name: serviceName,
        incident_number: incidentNumber,
        limit: 3,
      });
    }
  }, [serviceName, incidentNumber]);

  const knowledge = searchMutation.data || [];

  if (knowledge.length === 0 && !searchMutation.isPending) {
    return null; // Don't show section if no knowledge found
  }

  return (
    <div className="bg-white rounded-lg border p-4">
      <div className="flex items-center gap-2 mb-3">
        <BookOpen className="h-5 w-5 text-teal-600" />
        <h3 className="font-semibold">Related Knowledge</h3>
      </div>

      {searchMutation.isPending ? (
        <div className="text-sm text-gray-500">Searching knowledge base...</div>
      ) : knowledge.length === 0 ? (
        <div className="text-sm text-gray-500">No related knowledge found</div>
      ) : (
        <div className="space-y-3">
          {knowledge.map((item) => (
            <button
              key={item.id}
              onClick={() => navigate('/knowledge')}
              className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm text-gray-900 line-clamp-1 mb-1">
                    {item.title}
                  </h4>
                  {item.description && (
                    <p className="text-xs text-gray-600 line-clamp-2">
                      {item.description}
                    </p>
                  )}
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex items-center gap-1 mt-2 flex-wrap">
                      {item.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {item.usage_count > 0 && (
                  <div className="flex items-center gap-1 text-xs text-teal-600 flex-shrink-0">
                    <TrendingUp className="h-3 w-3" />
                    <span>{item.usage_count}</span>
                  </div>
                )}
              </div>
              {item.external_url && (
                <div className="flex items-center gap-1 text-xs text-teal-600 mt-2">
                  <ExternalLink className="h-3 w-3" />
                  <span>External Link</span>
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      <button
        onClick={() => navigate('/knowledge')}
        className="w-full mt-3 text-sm text-teal-600 hover:text-teal-700 font-medium text-center"
      >
        View All Knowledge →
      </button>
    </div>
  );
}
