/**
 * RCA Card - definitive full-detail RCA view
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { RCAResult } from '../types';
import { cn } from '@/lib/utils';
import { confidenceColors, severityColors } from '@/lib/colors';

interface RCACardProps {
  rca: RCAResult;
}

export function RCACard({ rca }: RCACardProps) {
  const [evidenceExpanded, setEvidenceExpanded] = useState(false);

  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 0.8) return { label: 'High Confidence', color: confidenceColors.high };
    if (confidence >= 0.5) return { label: 'Medium Confidence', color: confidenceColors.medium };
    return { label: 'Low Confidence', color: confidenceColors.low };
  };

  const getConfidenceExplanation = (confidence: number) => {
    if (confidence >= 0.8) {
      return 'Strong evidence supports this root cause with high certainty.';
    }
    if (confidence >= 0.5) {
      return 'Evidence suggests this root cause, but additional verification may be needed.';
    }
    return 'Limited evidence available. This root cause requires further investigation.';
  };

  const getSeverityColor = (severity: string) => {
    const key = severity as keyof typeof severityColors;
    return severityColors[key] || severityColors.low;
  };

  const confidenceLevel = getConfidenceLevel(rca.confidence);
  const confidencePercentage = Math.round(rca.confidence * 100);

  return (
    <div className="space-y-6">
      {/* Confidence Meter */}
      <div className="p-6 rounded-lg border bg-card">
        <h3 className="text-lg font-semibold mb-4">Confidence Assessment</h3>
        
        {/* Visual bar */}
        <div className="mb-4">
          <div className="h-3 bg-muted rounded-full overflow-hidden">
            <div
              className={cn('h-full transition-all', confidenceLevel.color)}
              style={{ width: `${confidencePercentage}%` }}
              role="progressbar"
              aria-valuenow={confidencePercentage}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Confidence: ${confidencePercentage}%`}
            />
          </div>
        </div>

        {/* Label and percentage */}
        <div className="flex items-center justify-between mb-2">
          <span className={cn('text-sm font-medium px-3 py-1 rounded-full', confidenceLevel.color)}>
            {confidenceLevel.label}
          </span>
          <span className="text-2xl font-bold">{confidencePercentage}%</span>
        </div>

        {/* Explanation */}
        <p className="text-sm text-muted-foreground">
          {getConfidenceExplanation(rca.confidence)}
        </p>
      </div>

      {/* Root Cause */}
      <div className="p-6 rounded-lg border bg-card">
        <h3 className="text-lg font-semibold mb-3">Root Cause</h3>
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown
            components={{
              h1: ({node, ...props}) => <h1 className="text-xl font-bold my-3" {...props} />,
              h2: ({node, ...props}) => <h2 className="text-lg font-bold my-2" {...props} />,
              h3: ({node, ...props}) => <h3 className="text-base font-semibold my-2" {...props} />,
              h4: ({node, ...props}) => <h4 className="text-sm font-semibold my-2" {...props} />,
              p: ({node, ...props}) => <p className="my-2" {...props} />,
              strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
              em: ({node, ...props}) => <em className="italic" {...props} />,
              ul: ({node, ...props}) => <ul className="list-disc ml-6 my-2" {...props} />,
              ol: ({node, ...props}) => <ol className="list-decimal ml-6 my-2" {...props} />,
              li: ({node, ...props}) => <li className="my-1" {...props} />,
              code: ({node, inline, ...props}) => 
                inline ? (
                  <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono" {...props} />
                ) : (
                  <code className="block bg-muted p-3 rounded my-2 overflow-x-auto" {...props} />
                ),
              blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-primary pl-4 my-2 italic" {...props} />,
            }}
          >
            {rca.root_cause}
          </ReactMarkdown>
        </div>
      </div>

      {/* Incident Timeline */}
      {rca.incident_timeline && rca.incident_timeline.length > 0 && (
        <div className="p-6 rounded-lg border bg-card">
          <h3 className="text-lg font-semibold mb-4">Incident Timeline</h3>
          <div className="space-y-4">
            {rca.incident_timeline.map((event, index) => (
              <div key={index} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      'h-3 w-3 rounded-full',
                      getSeverityColor(event.severity)
                    )}
                    title={`Severity: ${event.severity}`}
                  />
                  {index < rca.incident_timeline.length - 1 && (
                    <div className="w-px flex-1 bg-border mt-2" />
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <div className="text-xs text-muted-foreground mb-1">
                    {new Date(event.timestamp).toLocaleString()}
                  </div>
                  <p className="text-sm font-medium mb-1">{event.event}</p>
                  <div className="text-xs text-muted-foreground">
                    Source: {event.source}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Affected Resources */}
      {rca.affected_resources && rca.affected_resources.length > 0 && (
        <div className="p-6 rounded-lg border bg-card">
          <h3 className="text-lg font-semibold mb-4">Affected Resources</h3>
          <div className="grid grid-cols-1 gap-3">
            {rca.affected_resources.map((resource, index) => (
              <div
                key={index}
                className="p-3 rounded-md border bg-muted"
              >
                <p className="font-medium text-sm">{resource}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contributing Factors */}
      {rca.contributing_factors && rca.contributing_factors.length > 0 && (
        <div className="p-6 rounded-lg border bg-card">
          <h3 className="text-lg font-semibold mb-4">Contributing Factors</h3>
          <ol className="list-decimal list-inside space-y-2">
            {rca.contributing_factors.map((factor, index) => (
              <li key={index} className="text-sm leading-relaxed">
                {factor}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Supporting Evidence */}
      {rca.supporting_evidence && rca.supporting_evidence.length > 0 && (
        <div className="p-6 rounded-lg border bg-card">
          <button
            onClick={() => setEvidenceExpanded(!evidenceExpanded)}
            className="flex items-center gap-2 text-lg font-semibold mb-4 hover:text-primary transition-colors"
            aria-expanded={evidenceExpanded}
          >
            {evidenceExpanded ? (
              <ChevronDown className="h-5 w-5" aria-hidden="true" />
            ) : (
              <ChevronRight className="h-5 w-5" aria-hidden="true" />
            )}
            Supporting Evidence ({rca.supporting_evidence?.length || 0})
          </button>
          {evidenceExpanded && (
            <div className="space-y-3">
              {rca.supporting_evidence.map((evidence, index) => (
                <div
                  key={index}
                  className="p-3 rounded-md bg-muted border-l-2 border-primary"
                >
                  <p className="text-sm">{evidence}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
