/**
 * Service health summary component
 */
interface HealthSummary {
  total_resources: number;
  healthy_resources: number;
  degraded_resources: number;
  down_resources: number;
}

interface ServiceHealthSummaryProps {
  healthSummary: HealthSummary;
}

export function ServiceHealthSummary({ healthSummary }: ServiceHealthSummaryProps) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <h4 className="font-semibold">Health Summary</h4>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <div>
          <p className="text-2xl font-bold">{healthSummary.total_resources}</p>
          <p className="text-xs text-muted-foreground">Total Resources</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-green-500">{healthSummary.healthy_resources}</p>
          <p className="text-xs text-muted-foreground">Healthy</p>
        </div>
        {healthSummary.degraded_resources > 0 && (
          <div>
            <p className="text-2xl font-bold text-yellow-500">{healthSummary.degraded_resources}</p>
            <p className="text-xs text-muted-foreground">Degraded</p>
          </div>
        )}
        {healthSummary.down_resources > 0 && (
          <div>
            <p className="text-2xl font-bold text-red-500">{healthSummary.down_resources}</p>
            <p className="text-xs text-muted-foreground">Down</p>
          </div>
        )}
      </div>
    </div>
  );
}
