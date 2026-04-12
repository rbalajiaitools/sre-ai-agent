/**
 * RCA Result Message - THE most important component
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { ChatMessage, RCAResult } from '../../types';
import { cn } from '@/lib/utils';
import { confidenceColors } from '@/lib/colors';

interface RCAResultMessageProps {
  message: ChatMessage;
}

export function RCAResultMessage({ message }: RCAResultMessageProps) {
  const rca = message.metadata as unknown as RCAResult;
  const [evidenceExpanded, setEvidenceExpanded] = useState(false);

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) {
      return confidenceColors.high;
    }
    if (confidence >= 0.5) {
      return confidenceColors.medium;
    }
    return confidenceColors.low;
  };

  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Root Cause Identified</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {new Date(message.created_at).toLocaleString()}
          </p>
        </div>
        <span
          className={cn(
            'px-3 py-1 rounded-full text-sm font-medium',
            getConfidenceBadge(rca.confidence)
          )}
        >
          {Math.round(rca.confidence * 100)}% confidence
        </span>
      </div>

      {/* Root Cause */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-muted-foreground mb-2">
          Root Cause
        </h4>
        <p className="text-base leading-relaxed">{rca.root_cause}</p>
      </div>

      {/* Timeline */}
      {rca.timeline && rca.timeline.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-muted-foreground mb-3">
            Incident Timeline
          </h4>
          <div className="space-y-3">
            {rca.timeline.map((event, index) => (
              <div key={index} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="h-2 w-2 rounded-full bg-primary" />
                  {index < rca.timeline.length - 1 && (
                    <div className="w-px flex-1 bg-border mt-1" />
                  )}
                </div>
                <div className="flex-1 pb-3">
                  <div className="text-xs text-muted-foreground">
                    {new Date(event.timestamp).toLocaleString()}
                  </div>
                  <div className="text-sm mt-1">{event.event}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Source: {event.source}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Supporting Evidence */}
      {rca.evidence && rca.evidence.length > 0 && (
        <div className="mb-6">
          <button
            onClick={() => setEvidenceExpanded(!evidenceExpanded)}
            className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors mb-3"
            aria-expanded={evidenceExpanded}
            aria-label={evidenceExpanded ? 'Collapse evidence' : 'Expand evidence'}
          >
            {evidenceExpanded ? (
              <ChevronDown className="h-4 w-4" aria-hidden="true" />
            ) : (
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            )}
            Supporting Evidence ({rca.evidence.length})
          </button>
          {evidenceExpanded && (
            <div className="space-y-3 pl-6">
              {rca.evidence.map((item, index) => (
                <div
                  key={index}
                  className="border-l-2 border-primary/30 pl-3 py-1"
                >
                  <p className="text-sm">{item.description}</p>
                  <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                    <span>Agent: {item.source_agent}</span>
                    <span>Provider: {item.provider}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Affected Resources */}
      {rca.affected_resources && rca.affected_resources.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-muted-foreground mb-2">
            Affected Resources
          </h4>
          <div className="flex flex-wrap gap-2">
            {rca.affected_resources.map((resource, index) => (
              <span
                key={index}
                className="inline-flex items-center gap-1 px-3 py-1 rounded-md bg-muted text-sm"
              >
                <span className="font-medium">{resource.name}</span>
                <span className="text-muted-foreground">
                  ({resource.provider})
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Contributing Factors */}
      {rca.contributing_factors && rca.contributing_factors.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-muted-foreground mb-2">
            Contributing Factors
          </h4>
          <ul className="list-disc list-inside space-y-1 text-sm">
            {rca.contributing_factors.map((factor, index) => (
              <li key={index}>{factor}</li>
            ))}
          </ul>
        </div>
      )}

      {/* View Full Investigation Link */}
      <Link
        to={`/investigations/${rca.investigation_id}`}
        className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
      >
        View full investigation
        <ExternalLink className="h-4 w-4" aria-hidden="true" />
      </Link>
    </div>
  );
}
