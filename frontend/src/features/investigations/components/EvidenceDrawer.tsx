/**
 * Evidence Drawer - right panel with raw evidence
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
  const [expandedEvidence, setExpandedEvidence] = useState<Set<string>>(new Set());

  const toggleEvidence = (key: string) => {
    const newExpanded = new Set(expandedEvidence);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedEvidence(newExpanded);
  };

  // Filter agents
  const filteredAgents =
    selectedAgent === 'all'
      ? agents
      : agents.filter((a) => a.agent_type === selectedAgent);

  // Filter evidence by search
  const getFilteredEvidence = (agent: AgentResult) => {
    if (!searchQuery) return agent.evidence;
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
              {agent.agent_type}
            </option>
          ))}
        </select>
      </div>

      {/* Evidence list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {filteredAgents.map((agent) => {
          const evidence = getFilteredEvidence(agent);
          if (evidence.length === 0) return null;

          return (
            <div key={agent.agent_type} className="space-y-2">
              <h4 className="text-sm font-semibold text-muted-foreground">
                {agent.agent_type}
              </h4>
              {evidence.map((item, index) => {
                const key = `${agent.agent_type}-${index}`;
                const isExpanded = expandedEvidence.has(key);
                const isLong = item.length > 150;

                return (
                  <div
                    key={key}
                    className="p-3 rounded-lg border bg-card"
                  >
                    {/* Source info */}
                    <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
                      <span className="font-medium">{agent.agent_type}</span>
                      {agent.providers_queried.length > 0 && (
                        <>
                          <span>•</span>
                          <span>{agent.providers_queried.join(', ')}</span>
                        </>
                      )}
                    </div>

                    {/* Evidence content */}
                    <div className="text-sm">
                      {isLong && !isExpanded ? (
                        <>
                          <p>{item.slice(0, 150)}...</p>
                          <button
                            onClick={() => toggleEvidence(key)}
                            className="text-primary hover:underline text-xs mt-1"
                            aria-label="Show full evidence"
                          >
                            Show more
                          </button>
                        </>
                      ) : (
                        <>
                          <p className="whitespace-pre-wrap">{item}</p>
                          {isLong && (
                            <button
                              onClick={() => toggleEvidence(key)}
                              className="text-primary hover:underline text-xs mt-1"
                              aria-label="Show less evidence"
                            >
                              Show less
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}

        {/* Empty state */}
        {filteredAgents.every((a) => getFilteredEvidence(a).length === 0) && (
          <div className="flex items-center justify-center h-32 text-center">
            <p className="text-sm text-muted-foreground">
              {searchQuery ? 'No evidence matches your search' : 'No evidence available'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
