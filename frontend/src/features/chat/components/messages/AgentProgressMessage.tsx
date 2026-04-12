/**
 * Agent Progress Message - streaming agent updates
 */
import { useState } from 'react';
import { Loader2, CheckCircle2, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { ChatMessage, AgentSummary } from '../../types';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface AgentProgressMessageProps {
  message: ChatMessage;
}

export function AgentProgressMessage({ message }: AgentProgressMessageProps) {
  const [expanded, setExpanded] = useState(true);
  
  const {
    agents_running = [],
    agents_completed = [],
    elapsed_seconds = 0,
    current_step = '',
  } = message.metadata as {
    agents_running?: string[];
    agents_completed?: AgentSummary[];
    elapsed_seconds?: number;
    current_step?: string;
  };

  const isComplete = agents_running.length === 0;

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getStatusIcon = (status: AgentSummary['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className={cn('h-4 w-4', statusColors.success.icon)} aria-label="Completed" />;
      case 'failed':
        return <XCircle className={cn('h-4 w-4', statusColors.error.icon)} aria-label="Failed" />;
      default:
        return <Loader2 className={cn('h-4 w-4 animate-spin', statusColors.info.icon)} aria-label="Running" />;
    }
  };

  return (
    <div className={cn(
      "rounded-lg border p-4 transition-all",
      isComplete ? "bg-muted/50" : "bg-card shadow-sm"
    )}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center justify-between w-full text-left"
        aria-expanded={expanded}
        aria-label={expanded ? 'Collapse progress' : 'Expand progress'}
      >
        <div className="flex items-center gap-2">
          {expanded ? (
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          )}
          <span className="font-medium">
            {isComplete ? 'Investigation Complete' : 'Investigation in Progress'}
          </span>
        </div>
        <span className="text-sm text-muted-foreground">
          {formatDuration(elapsed_seconds)}
        </span>
      </button>

      {expanded && (
        <div className="mt-4 space-y-3">
          {/* Current Step */}
          {!isComplete && current_step && (
            <div className="text-sm text-muted-foreground">
              {current_step}
            </div>
          )}

          {/* Running Agents */}
          {agents_running.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">
                Running
              </h4>
              <div className="space-y-2">
                {agents_running.map((agent) => (
                  <div key={agent} className="flex items-center gap-2 text-sm">
                    <Loader2 className={cn('h-4 w-4 animate-spin', statusColors.info.icon)} aria-hidden="true" />
                    <span>{agent}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Completed Agents */}
          {agents_completed.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-muted-foreground mb-2">
                Completed ({agents_completed.length})
              </h4>
              <div className="space-y-2">
                {agents_completed.map((agent) => (
                  <div key={agent.agent_name} className="flex items-start gap-2">
                    {getStatusIcon(agent.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium truncate">
                          {agent.agent_name}
                        </span>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {formatDuration(agent.duration_seconds)}
                        </span>
                      </div>
                      {agent.finding_summary && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {agent.finding_summary}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
