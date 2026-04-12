/**
 * Agent performance chart component
 */
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { useAgentStats } from '../hooks';

export function AgentPerformanceChart() {
  const agentStatsQuery = useAgentStats();

  if (agentStatsQuery.isLoading) {
    return <LoadingSpinner />;
  }

  if (agentStatsQuery.isError) {
    return (
      <div className="flex h-full items-center justify-center p-4" role="alert">
        <p className="text-sm text-red-500">
          Failed to load agent stats: {agentStatsQuery.error?.message || 'Unknown error'}
        </p>
      </div>
    );
  }

  const data = agentStatsQuery.data || [];

  return (
    <div className="h-full space-y-4">
      <h3 className="font-semibold">Agent Performance</h3>

      {data.length === 0 ? (
        <div className="flex h-[300px] items-center justify-center">
          <p className="text-sm text-muted-foreground">No data available</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="agent_type"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              label={{ value: 'Avg Duration (s)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              formatter={(value: number, name: string, props) => {
                if (name === 'avg_duration_seconds') {
                  return [
                    <>
                      <div>Duration: {value}s</div>
                      <div>Evidence Rate: {Math.round(props.payload.evidence_found_rate * 100)}%</div>
                      <div>Investigations: {props.payload.investigations_run}</div>
                    </>,
                    'Performance'
                  ];
                }
                return [value, name];
              }}
            />
            <Bar
              dataKey="avg_duration_seconds"
              fill="hsl(var(--primary))"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
