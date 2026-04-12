/**
 * Main dashboard page
 */
import { AlertCircle, Clock, CheckCircle, Brain } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { StatCard } from './StatCard';
import { IncidentTrendChart } from './IncidentTrendChart';
import { AgentPerformanceChart } from './AgentPerformanceChart';
import { TopServicesTable } from './TopServicesTable';
import { useDashboardStats } from '../hooks';

export function DashboardPage() {
  const statsQuery = useDashboardStats();

  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Dashboard"
        description="Overview of incidents, investigations, and system performance"
      />

      <div className="flex-1 overflow-auto p-6">
        {statsQuery.isLoading && <LoadingSpinner />}

        {statsQuery.isError && (
          <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4" role="alert">
            <p className="text-sm text-red-500">
              Failed to load dashboard: {statsQuery.error?.message}
            </p>
          </div>
        )}

        {statsQuery.data && (
          <div className="space-y-6">
            {/* Stat cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Open Incidents"
                value={statsQuery.data.open_incidents}
                subtitle={`${statsQuery.data.p1_open} P1 incidents`}
                trend={statsQuery.data.open_incidents_trend}
                icon={<AlertCircle className="h-5 w-5" />}
              />
              <StatCard
                title="Avg MTTR"
                value={`${statsQuery.data.avg_mttr_hours.toFixed(1)}h`}
                trend={statsQuery.data.avg_mttr_trend}
                icon={<Clock className="h-5 w-5" />}
              />
              <StatCard
                title="Resolved Today"
                value={statsQuery.data.resolved_today}
                trend={statsQuery.data.resolved_today_trend}
                icon={<CheckCircle className="h-5 w-5" />}
              />
              <StatCard
                title="Investigations Today"
                value={statsQuery.data.investigations_today}
                subtitle={`${statsQuery.data.auto_resolved} auto-resolved`}
                trend={statsQuery.data.investigations_today_trend}
                icon={<Brain className="h-5 w-5" />}
              />
            </div>

            {/* Charts */}
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-lg border bg-card p-6">
                <IncidentTrendChart />
              </div>
              <div className="rounded-lg border bg-card p-6">
                <AgentPerformanceChart />
              </div>
            </div>

            {/* Tables */}
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-lg border bg-card p-6">
                <TopServicesTable />
              </div>
              <div className="rounded-lg border bg-card p-6">
                <h3 className="font-semibold">Recent Investigations</h3>
                <p className="mt-4 text-center text-sm text-muted-foreground">
                  View all investigations in the Investigations page
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
