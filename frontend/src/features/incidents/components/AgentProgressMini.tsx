/**
 * Agent Progress Mini - compact horizontal agent status
 */
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { statusColors } from '@/lib/colors';

interface AgentProgressMiniProps {
  agentsRunning: string[];
  agentsCompleted: string[];
  elapsedSeconds: number;
}

export function AgentProgressMini({
  agentsRunning,
  agentsCompleted,
  elapsedSeconds,
}: AgentProgressMiniProps) {
  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="flex items-center gap-3">
      {/* Agent dots */}
      <div className="flex items-center gap-1">
        {agentsRunning.map((agent, index) => (
          <div
            key={`running-${index}`}
            className={cn(
              'h-2 w-2 rounded-full animate-pulse',
              statusColors.info.icon
            )}
            title={agent}
            aria-label={`${agent} running`}
          />
        ))}
        {agentsCompleted.map((agent, index) => (
          <div
            key={`completed-${index}`}
            className={cn('h-2 w-2 rounded-full', statusColors.success.icon)}
            title={agent}
            aria-label={`${agent} completed`}
          />
        ))}
      </div>

      {/* Status text */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
        <span>Investigating... {formatDuration(elapsedSeconds)}</span>
      </div>
    </div>
  );
}
