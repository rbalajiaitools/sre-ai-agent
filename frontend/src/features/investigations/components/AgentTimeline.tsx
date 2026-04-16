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
  isCompleted?: boolean;
}

export function AgentTimeline({ agents, elapsedSeconds, isCompleted = false }: AgentTimelineProps) {
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
      {/* Overall elapsed time - only show when completed */}
      {isCompleted && (
        <div className="p-3 rounded-lg bg-muted">
          <p className="text-sm font-medium">Total Duration</p>
          <p className="text-2xl font-semibold mt-1">
            {formatDuration(elapsedSeconds)}
          </p>
        </div>
      )}

      {/* Agent timeline */}
      <div className="space-y-3">
        {displayAgents.map((agent, index) => {
          const isExpanded = expandedAgents.has(agent.agent_type);
          const isRunning = !agent.success && !agent.error;
          const hasCompleted = agent.success || agent.error;

          return (
            <div key={agent.agent_type} className="relative">
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
                <div className="mt-2 space-y-2 px-3">
                  {/* Providers and Duration */}
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    {agent.providers_queried.length > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">Providers:</span>
                        <span>{agent.providers_queried.join(', ')}</span>
                      </div>
                    )}
                    {agent.duration_seconds !== undefined && (
                      <div className="flex items-center gap-2">
                        <span className="font-medium">Duration:</span>
                        <span>{agent.duration_seconds}s</span>
                      </div>
                    )}
                  </div>

                  {/* AI Analysis - Single box with white/light grey background */}
                  {agent.ai_analysis && (
                    <div className="p-4 rounded-lg bg-white border border-gray-200">
                      <div className="space-y-2 text-xs text-gray-700">
                        {agent.ai_analysis.split('\n').map((line, idx) => {
                          const trimmedLine = line.trim();
                          
                          // Skip empty lines
                          if (!trimmedLine) return null;
                          
                          // Remove markdown formatting (**, ••, etc.)
                          const cleanLine = trimmedLine.replace(/\*\*/g, '').replace(/••/g, '');
                          
                          // Section headers (all caps with colon)
                          if (/^[A-Z\s]+:/.test(cleanLine)) {
                            return (
                              <p key={idx} className="font-bold text-gray-900 mt-3 mb-1 first:mt-0">
                                {cleanLine}
                              </p>
                            );
                          }
                          
                          // Bullet points - highlight key terms
                          if (cleanLine.startsWith('•') || cleanLine.startsWith('-')) {
                            // Extract and bold numbers, percentages, and key technical terms
                            const parts = cleanLine.split(/(\d+\.?\d*%?|\d+MB|\d+GB|\d+s|Lambda|EC2|RDS|CloudWatch|ERROR|WARNING|CRITICAL)/g);
                            return (
                              <p key={idx} className="text-gray-700 leading-relaxed pl-3">
                                {parts.map((part, i) => {
                                  // Bold numbers, percentages, sizes, and key terms
                                  if (/\d+\.?\d*%?|\d+MB|\d+GB|\d+s|Lambda|EC2|RDS|CloudWatch|ERROR|WARNING|CRITICAL/.test(part)) {
                                    return <span key={i} className="font-semibold text-gray-900">{part}</span>;
                                  }
                                  return part;
                                })}
                              </p>
                            );
                          }
                          
                          // Regular text - highlight key terms
                          const parts = cleanLine.split(/(\d+\.?\d*%?|\d+MB|\d+GB|\d+s|Lambda|EC2|RDS|CloudWatch|ERROR|WARNING|CRITICAL|high|low|critical|failed|success)/gi);
                          return (
                            <p key={idx} className="text-gray-700 leading-relaxed">
                              {parts.map((part, i) => {
                                // Bold important terms and numbers
                                if (/\d+\.?\d*%?|\d+MB|\d+GB|\d+s|Lambda|EC2|RDS|CloudWatch|ERROR|WARNING|CRITICAL|high|low|critical|failed|success/i.test(part)) {
                                  return <span key={i} className="font-semibold text-gray-900">{part}</span>;
                                }
                                return part;
                              })}
                            </p>
                          );
                        })}
                      </div>
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
