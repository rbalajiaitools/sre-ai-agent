/**
 * Dashboard stat card component
 */
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: number; // Percentage change
  icon?: React.ReactNode;
}

export function StatCard({ title, value, subtitle, trend, icon }: StatCardProps) {
  const getTrendIcon = () => {
    if (trend === undefined || trend === 0) return <Minus className="h-4 w-4" />;
    return trend > 0 ? (
      <TrendingUp className="h-4 w-4" />
    ) : (
      <TrendingDown className="h-4 w-4" />
    );
  };

  const getTrendColor = () => {
    if (trend === undefined || trend === 0) return 'text-muted-foreground';
    return trend > 0 ? 'text-green-500' : 'text-red-500';
  };

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        {icon && <div className="text-muted-foreground" aria-hidden="true">{icon}</div>}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-3xl font-bold">{value}</p>
        {trend !== undefined && (
          <div
            className={`flex items-center gap-1 text-sm ${getTrendColor()}`}
            aria-label={`${trend > 0 ? 'Increased' : trend < 0 ? 'Decreased' : 'No change'} by ${Math.abs(trend)} percent`}
          >
            <span aria-hidden="true">{getTrendIcon()}</span>
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
