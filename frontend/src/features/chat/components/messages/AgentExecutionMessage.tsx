/**
 * Agent Execution Message - Shows real-time agent execution like Claude/resolve.ai
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight, Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { ChatMessage } from '../../types';
import { cn } from '@/lib/utils';

interface AgentExecutionMessageProps {
  message: ChatMessage;
}

interface AgentStep {
  agent: string;
  status: 'pending' | 'running' | 'success' | 'error';
  title: string;
  details?: string;
  findings?: string[];
  duration?: number;
}

export function AgentExecutionMessage({ message }: AgentExecutionMessageProps) {
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  // Parse agent steps from message metadata
  const steps: AgentStep[] = message.metadata?.agent_steps || [
    {
      agent: 'logs',
      status: 'success',
      title: 'Logs Agent',
      details: 'Analyzed CloudWatch logs for the time period',
      findings: [
        'Found 1,862 error logs in payment-service',
        'Memory leak pattern detected',
        'Error rate increased from 0.1% to 61.2%',
      ],
      duration: 3.2,
    },
    {
      agent: 'metrics',
      status: 'success',
      title: 'Metrics Agent',
      details: 'Analyzed CloudWatch metrics and dashboards',
      findings: [
        'CPU usage spiked to 95% at 10:17:59',
        'Memory usage grew from 2GB to 8GB',
        'Request latency increased 400%',
      ],
      duration: 2.8,
    },
    {
      agent: 'infrastructure',
      status: 'running',
      title: 'Infrastructure Agent',
      details: 'Checking AWS resources and configurations',
    },
    {
      agent: 'security',
      status: 'pending',
      title: 'Security Agent',
    },
    {
      agent: 'code',
      status: 'pending',
      title: 'Code Agent',
    },
  ];

  const toggleAgent = (agent: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agent)) {
      newExpanded.delete(agent);
    } else {
      newExpanded.add(agent);
    }
    setExpandedAgents(newExpanded);
  };

  const getStatusIcon = (status: AgentStep['status']) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-lime-500" />;
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: AgentStep['status']) => {
    switch (status) {
      case 'running':
        return 'border-lime-500 bg-lime-50 dark:bg-lime-950';
      case 'success':
        return 'border-green-500 bg-green-50 dark:bg-green-950';
      case 'error':
        return 'border-red-500 bg-red-50 dark:bg-red-950';
      case 'pending':
        return 'border-gray-300 bg-gray-50 dark:bg-gray-900';
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Running Investigation Agents</span>
      </div>

      <div className="space-y-2">
        {steps.map((step) => {
          const isExpanded = expandedAgents.has(step.agent);
          const hasDetails = step.details || (step.findings && step.findings.length > 0);

          return (
            <div
              key={step.agent}
              className={cn(
                'rounded-lg border-l-4 transition-all',
                getStatusColor(step.status),
                'animate-slide-in-up'
              )}
            >
              <button
                onClick={() => hasDetails && toggleAgent(step.agent)}
                className={cn(
                  'w-full px-4 py-3 text-left transition-colors',
                  hasDetails && 'hover:bg-black/5 dark:hover:bg-white/5'
                )}
                disabled={!hasDetails}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(step.status)}
                    <div>
                      <div className="font-medium text-sm">{step.title}</div>
                      {step.status === 'running' && step.details && (
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {step.details}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {step.duration && (
                      <span className="text-xs text-muted-foreground">
                        {step.duration}s
                      </span>
                    )}
                    {hasDetails && (
                      isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )
                    )}
                  </div>
                </div>
              </button>

              {isExpanded && hasDetails && (
                <div className="px-4 pb-3 space-y-2 animate-expand">
                  {step.details && step.status !== 'running' && (
                    <p className="text-sm text-muted-foreground">{step.details}</p>
                  )}
                  {step.findings && step.findings.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                        Findings
                      </div>
                      <ul className="space-y-1">
                        {step.findings.map((finding, idx) => (
                          <li
                            key={idx}
                            className="text-sm flex items-start gap-2"
                          >
                            <span className="text-primary mt-1">•</span>
                            <span>{finding}</span>
                          </li>
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
