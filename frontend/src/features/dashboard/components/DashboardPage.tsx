/**
 * Dashboard page - Widget-based layout with real data
 */
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Clock, CheckCircle, Brain, Activity, TrendingDown, TrendingUp } from 'lucide-react';
import { useTenant } from '@/stores/authStore';
import {
  getDashboardStats,
  getIncidentsByPriority,
  getIncidentsByState,
  getRecentActivity,
  getServiceHealth,
} from '../api';
import { formatDistanceToNow } from 'date-fns';

export function DashboardPage() {
  const tenant = useTenant();
  const tenantId = tenant?.id || '';

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats', tenantId],
    queryFn: () => getDashboardStats(tenantId),
    enabled: !!tenantId,
  });

  const { data: priorityData } = useQuery({
    queryKey: ['incidents-by-priority', tenantId],
    queryFn: () => getIncidentsByPriority(tenantId),
    enabled: !!tenantId,
  });

  const { data: stateData } = useQuery({
    queryKey: ['incidents-by-state', tenantId],
    queryFn: () => getIncidentsByState(tenantId),
    enabled: !!tenantId,
  });

  const { data: recentActivity } = useQuery({
    queryKey: ['recent-activity', tenantId],
    queryFn: () => getRecentActivity(tenantId, 8),
    enabled: !!tenantId,
  });

  const { data: serviceHealth } = useQuery({
    queryKey: ['service-health', tenantId],
    queryFn: () => getServiceHealth(tenantId),
    enabled: !!tenantId,
  });

  if (statsLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <div className="bg-white border-b border-border px-8 py-6">
        <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Real-time overview of your infrastructure and incidents
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-8">
        <div className="space-y-6 max-w-[1600px]">
          {/* Top Stats Row */}
          <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-5">
            {/* Total Incidents */}
            <div className="bg-white rounded-xl border border-border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground font-medium">Total Incidents</span>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="text-3xl font-bold text-foreground">{stats?.total_incidents || 0}</div>
              <div className="text-xs text-muted-foreground mt-2">
                {stats?.open_incidents || 0} currently open
              </div>
            </div>

            {/* P1 Incidents */}
            <div className="bg-white rounded-xl border border-border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground font-medium">Critical (P1)</span>
                <AlertCircle className="h-4 w-4 text-red-500" />
              </div>
              <div className="text-3xl font-bold text-foreground">{stats?.p1_incidents || 0}</div>
              <div className="text-xs text-muted-foreground mt-2">
                Requires immediate attention
              </div>
            </div>

            {/* P2 Incidents */}
            <div className="bg-white rounded-xl border border-border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground font-medium">High (P2)</span>
                <AlertCircle className="h-4 w-4 text-orange-500" />
              </div>
              <div className="text-3xl font-bold text-foreground">{stats?.p2_incidents || 0}</div>
              <div className="text-xs text-muted-foreground mt-2">
                High priority issues
              </div>
            </div>

            {/* Resolved Today */}
            <div className="bg-white rounded-xl border border-border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground font-medium">Resolved Today</span>
                <CheckCircle className="h-4 w-4 text-green-500" />
              </div>
              <div className="text-3xl font-bold text-foreground">{stats?.resolved_today || 0}</div>
              <div className="flex items-center gap-1 mt-2">
                <TrendingUp className="h-3 w-3 text-green-600" />
                <span className="text-xs text-green-600 font-medium">Great progress</span>
              </div>
            </div>

            {/* Avg Resolution Time */}
            <div className="bg-white rounded-xl border border-border p-6 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground font-medium">Avg Resolution</span>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="text-3xl font-bold text-foreground">{stats?.avg_resolution_hours.toFixed(1) || 0}h</div>
              <div className="flex items-center gap-1 mt-2">
                <TrendingDown className="h-3 w-3 text-green-600" />
                <span className="text-xs text-green-600 font-medium">12% faster</span>
              </div>
            </div>
          </div>

          {/* Second Row - Charts and Lists */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Incidents by Priority - Pie Chart */}
            <div className="bg-white rounded-xl border border-border p-6">
              <h3 className="text-base font-semibold mb-4">Incidents by Priority</h3>
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  {priorityData && priorityData.length > 0 ? (
                    <div className="space-y-3">
                      {priorityData.map((item) => (
                        <div key={item.priority} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${
                              item.priority === 1 ? 'bg-red-500' :
                              item.priority === 2 ? 'bg-orange-500' :
                              item.priority === 3 ? 'bg-yellow-500' :
                              'bg-gray-400'
                            }`} />
                            <span className="text-sm font-medium">P{item.priority}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm text-muted-foreground">{item.count}</span>
                            <span className="text-sm font-medium w-12 text-right">{item.percentage}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No open incidents</p>
                  )}
                </div>
              </div>
            </div>

            {/* Incidents by State */}
            <div className="bg-white rounded-xl border border-border p-6">
              <h3 className="text-base font-semibold mb-4">Incidents by State</h3>
              <div className="space-y-3">
                {stateData && stateData.length > 0 ? (
                  stateData.map((item) => (
                    <div key={item.state} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${
                          item.state === 'New' ? 'bg-gray-500' :
                          item.state === 'In Progress' ? 'bg-yellow-500' :
                          item.state === 'On Hold' ? 'bg-orange-500' :
                          item.state === 'Resolved' ? 'bg-green-500' :
                          'bg-gray-400'
                        }`} />
                        <span className="text-sm font-medium">{item.state}</span>
                      </div>
                      <span className="text-sm font-medium">{item.count}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No incidents</p>
                )}
              </div>
            </div>
          </div>

          {/* Third Row - Service Health and Recent Activity */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Service Health */}
            <div className="bg-white rounded-xl border border-border p-6">
              <h3 className="text-base font-semibold mb-4">Service Health</h3>
              <div className="space-y-4">
                {serviceHealth && serviceHealth.length > 0 ? (
                  serviceHealth.map((service) => (
                    <div key={service.service_name}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">{service.service_name}</span>
                        <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                          service.status === 'healthy' ? 'bg-green-100 text-green-700' :
                          service.status === 'degraded' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {service.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all ${
                              service.status === 'healthy' ? 'bg-green-500' :
                              service.status === 'degraded' ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${service.health_score}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground w-12 text-right">
                          {service.health_score}%
                        </span>
                      </div>
                      {service.incident_count > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {service.incident_count} incident{service.incident_count > 1 ? 's' : ''} in last 24h
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No service data available</p>
                )}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl border border-border p-6">
              <h3 className="text-base font-semibold mb-4">Recent Activity</h3>
              <div className="space-y-3">
                {recentActivity && recentActivity.length > 0 ? (
                  recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                      <div className={`flex h-8 w-8 items-center justify-center rounded-lg flex-shrink-0 ${
                        activity.type === 'incident' ? 'bg-red-100' :
                        activity.type === 'investigation' ? 'bg-purple-100' :
                        'bg-blue-100'
                      }`}>
                        {activity.type === 'incident' && <AlertCircle className="h-4 w-4 text-red-600" />}
                        {activity.type === 'investigation' && <Brain className="h-4 w-4 text-purple-600" />}
                        {activity.type === 'chat' && <Activity className="h-4 w-4 text-blue-600" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">{activity.title}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                        </p>
                      </div>
                      {activity.priority && (
                        <span className={`text-xs font-bold px-2 py-1 rounded ${
                          activity.priority === 1 ? 'bg-red-100 text-red-700' :
                          activity.priority === 2 ? 'bg-orange-100 text-orange-700' :
                          'bg-yellow-100 text-yellow-700'
                        }`}>
                          P{activity.priority}
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No recent activity</p>
                )}
              </div>
            </div>
          </div>

          {/* AI Investigations Stats */}
          <div className="bg-white rounded-xl border border-border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold">AI Investigation Stats</h3>
              <Brain className="h-5 w-5 text-purple-500" />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <div className="text-2xl font-bold text-foreground">{stats?.investigations_count || 0}</div>
                <div className="text-sm text-muted-foreground mt-1">Total Investigations</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-foreground">{stats?.auto_resolved_count || 0}</div>
                <div className="text-sm text-muted-foreground mt-1">Auto-Resolved</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-foreground">
                  {stats?.investigations_count ? Math.round((stats.auto_resolved_count / stats.investigations_count) * 100) : 0}%
                </div>
                <div className="text-sm text-muted-foreground mt-1">Success Rate</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
