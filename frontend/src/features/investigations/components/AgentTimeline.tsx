/**
 * Agent Timeline - vertical timeline of agent execution
 */
import { useState } from 'react';
import { CheckCircle2, XCircle, Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { AgentResult } from '../types';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface AgentTimelineProps {
  agents: AgentResult[];
  elapsedSeconds: number;
}

export function AgentTimeline({ agents, elapsedSeconds }: AgentTimelineProps) {
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  const toggleAgent = (agentType: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentType)) {
      newExpanded.delete(agentType);
    } else {
      newExpanded.add(agentType);
    }
    setExpandedAgents(newExpanded);
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getAgentIcon = (agent: AgentResult) => {
    if (agent.success) {
      return (
        <CheckCircle2
          className={cn('h-5 w-5', statusColors.success.icon)}
          aria-label="Success"
        />
      );
    }
    if (agent.error) {
      return (
        <XCircle
          className={cn('h-5 w-5', statusColors.error.icon)}
          aria-label="Failed"
        />
      );
    }
    // Running state with animation
    return (
      <Loader2
        className={cn('h-5 w-5 animate-spin', statusColors.info.icon)}
        aria-label="Running"
      />
    );
  };

  // Show placeholder agents if investigation is still running
  const allAgentTypes = ['infrastructure', 'logs', 'metrics', 'security', 'code'];
  const displayAgents = agents.length > 0 ? agents : allAgentTypes.map(type => ({
    agent_type: type,
    success: false,
    error: null,
    analysis: {},
    evidence: [],
    duration_seconds: 0,
    providers_queried: []
  }));

  return (
    <div className="space-y-4">
      {/* Overall elapsed time */}
      <div className="p-3 rounded-lg bg-muted">
        <p className="text-sm font-medium">Total Duration</p>
        <p className="text-2xl font-semibold mt-1">
          {formatDuration(elapsedSeconds)}
        </p>
      </div>

      {/* Agent timeline */}
      <div className="space-y-3">
        {displayAgents.map((agent, index) => {
          const isExpanded = expandedAgents.has(agent.agent_type);
          const isRunning = !agent.success && !agent.error;
          const hasCompleted = agent.success || agent.error;

          return (
            <div key={agent.agent_type} className="relative">
              {/* Timeline line */}
              {index < displayAgents.length - 1 && (
                <div className="absolute left-[18px] top-10 bottom-0 w-px bg-border" />
              )}

              {/* Agent node */}
              <button
                onClick={() => hasCompleted && toggleAgent(agent.agent_type)}
                className={cn(
                  "w-full text-left p-3 rounded-lg border transition-colors",
                  hasCompleted ? "hover:bg-muted/50" : "opacity-75",
                  isRunning && "animate-pulse"
                )}
                aria-expanded={isExpanded}
                disabled={!hasCompleted}
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {getAgentIcon(agent)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <p className="font-medium text-sm capitalize">{agent.agent_type}</p>
                      {hasCompleted && (
                        <span className="text-xs text-muted-foreground">
                          {formatDuration(agent.duration_seconds)}
                        </span>
                      )}
                      {isRunning && (
                        <span className="text-xs text-muted-foreground animate-pulse">
                          Running...
                        </span>
                      )}
                    </div>
                    {agent.error && (
                      <p className={cn('text-xs', statusColors.error.textMuted)}>
                        {agent.error}
                      </p>
                    )}
                    {isRunning && (
                      <p className="text-xs text-muted-foreground">
                        Collecting data from AWS...
                      </p>
                    )}
                  </div>
                  {hasCompleted && (
                    <>
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                      ) : (
                        <ChevronRight className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
                      )}
                    </>
                  )}
                </div>
              </button>

              {/* Expanded details */}
              {isExpanded && hasCompleted && (
                <div className="ml-11 mt-2 p-3 rounded-lg bg-muted space-y-3">
                  {/* Providers queried */}
                  {agent.providers_queried.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-2">
                        Providers Queried
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {agent.providers_queried.map((provider) => (
                          <span
                            key={provider}
                            className="px-2 py-0.5 rounded bg-background text-xs"
                          >
                            {provider}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Evidence */}
                  {agent.evidence.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-muted-foreground mb-2">
                        Evidence Found
                      </p>
                      <ul className="list-disc list-inside space-y-1 text-xs">
                        {agent.evidence.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
