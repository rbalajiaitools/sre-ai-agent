/**
 * Evidence Drawer - right panel with detailed agent findings
 */
import { useState } from 'react';
import { Search, ChevronDown, ChevronRight } from 'lucide-react';
import { AgentResult } from '../types';
import { Input } from '@/components/ui/input';

interface EvidenceDrawerProps {
  agents: AgentResult[];
}

export function EvidenceDrawer({ agents }: EvidenceDrawerProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string>('all');
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set(['infrastructure', 'logs', 'metrics']));

  const toggleAgent = (agentType: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentType)) {
      newExpanded.delete(agentType);
    } else {
      newExpanded.add(agentType);
    }
    setExpandedAgents(newExpanded);
  };

  // Filter agents
  const filteredAgents =
    selectedAgent === 'all'
      ? agents
      : agents.filter((a) => a.agent_type === selectedAgent);

  // Filter evidence by search
  const getFilteredEvidence = (agent: AgentResult) => {
    if (!searchQuery || !agent.evidence) return agent.evidence || [];
    return agent.evidence.filter((e) =>
      e.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b space-y-3">
        <h3 className="text-lg font-semibold">Evidence</h3>

        {/* Search */}
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search evidence..."
            className="pl-9"
            aria-label="Search evidence"
          />
        </div>

        {/* Agent filter */}
        <select
          value={selectedAgent}
          onChange={(e) => setSelectedAgent(e.target.value)}
          className="w-full px-3 py-2 rounded-md border bg-background text-sm"
          aria-label="Filter by agent"
        >
          <option value="all">All Agents</option>
          {agents.map((agent) => (
            <option key={agent.agent_type} value={agent.agent_type}>
              {agent.agent_type.charAt(0).toUpperCase() + agent.agent_type.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Evidence list - Grouped by agent */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredAgents.map((agent) => {
          const evidence = getFilteredEvidence(agent);
          const isExpanded = expandedAgents.has(agent.agent_type);

          return (
            <div key={agent.agent_type} className="border rounded-lg">
              {/* Agent header - collapsible */}
              <button
                onClick={() => toggleAgent(agent.agent_type)}
                className="w-full p-3 flex items-center justify-between hover:bg-muted/50 transition-colors rounded-t-lg"
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm capitalize">
                    {agent.agent_type}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ({evidence.length} findings)
                  </span>
                </div>
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </button>

              {/* Agent evidence - expanded */}
              {isExpanded && (
                <div className="p-3 pt-0 space-y-2">
                  {/* Provider info */}
                  {agent.providers_queried && agent.providers_queried.length > 0 && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                      <span className="font-medium">Providers:</span>
                      <span>{agent.providers_queried.join(', ').toUpperCase()}</span>
                    </div>
                  )}

                  {/* Duration */}
                  {agent.duration_seconds !== undefined && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                      <span className="font-medium">Duration:</span>
                      <span>{agent.duration_seconds}s</span>
                    </div>
                  )}

                  {/* Evidence items */}
                  {evidence.length > 0 ? (
                    <div className="space-y-2">
                      {evidence.map((item, index) => (
                        <div
                          key={index}
                          className="p-3 rounded bg-muted/50 text-xs border"
                        >
                          <div className="prose prose-sm max-w-none dark:prose-invert">
                            <p className="whitespace-pre-wrap break-words leading-relaxed m-0">{item}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">
                      No evidence found
                    </p>
                  )}

                  {/* Analysis details if available */}
                  {agent.analysis && Object.keys(agent.analysis).length > 0 && (
                    <details className="mt-3">
                      <summary className="text-xs font-medium cursor-pointer hover:text-primary">
                        View raw analysis data
                      </summary>
                      <pre className="mt-2 p-2 rounded bg-muted text-xs overflow-x-auto">
                        {JSON.stringify(agent.analysis, null, 2)}
                      </pre>
                    </details>
                  )}

                  {/* Error if any */}
                  {agent.error && (
                    <div className="mt-2 p-2 rounded bg-red-50 dark:bg-red-900/20 text-xs text-red-600 dark:text-red-400">
                      <span className="font-medium">Error:</span> {agent.error}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Empty state */}
        {filteredAgents.length === 0 && (
          <div className="flex items-center justify-center h-32 text-center">
            <p className="text-sm text-muted-foreground">
              No agents available
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
