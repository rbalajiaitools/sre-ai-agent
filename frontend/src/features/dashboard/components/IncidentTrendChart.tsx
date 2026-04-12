/**
 * Incident trend chart component
 */
import { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Button } from '@/components/ui/button';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { useIncidentTrends } from '../hooks';

export function IncidentTrendChart() {
  const [days, setDays] = useState(30);
  const trendsQuery = useIncidentTrends(days);

  if (trendsQuery.isLoading) {
    return <LoadingSpinner />;
  }

  if (trendsQuery.isError) {
    return (
      <div className="flex h-full items-center justify-center p-4" role="alert">
        <p className="text-sm text-red-500">
          Failed to load trends: {trendsQuery.error?.message || 'Unknown error'}
        </p>
      </div>
    );
  }

  const data = trendsQuery.data || [];

  return (
    <div className="h-full space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Incident Trends</h3>
        <div className="flex gap-1" role="group" aria-label="Select time range">
          {[7, 30, 90].map((d) => (
            <Button
              key={d}
              variant={days === d ? 'default' : 'outline'}
              size="sm"
              onClick={() => setDays(d)}
              aria-pressed={days === d}
              aria-label={`Show ${d} days`}
            >
              {d}d
            </Button>
          ))}
        </div>
      </div>

      {data.length === 0 ? (
        <div className="flex h-[300px] items-center justify-center">
          <p className="text-sm text-muted-foreground">No data available</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="date"
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            />
            <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
              }}
              labelFormatter={(value) => new Date(value).toLocaleDateString()}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="p1"
              stackId="1"
              stroke="hsl(0 84% 60%)"
              fill="hsl(0 84% 60%)"
              name="P1"
            />
            <Area
              type="monotone"
              dataKey="p2"
              stackId="1"
              stroke="hsl(25 95% 53%)"
              fill="hsl(25 95% 53%)"
              name="P2"
            />
            <Area
              type="monotone"
              dataKey="p3"
              stackId="1"
              stroke="hsl(48 96% 53%)"
              fill="hsl(48 96% 53%)"
              name="P3"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
