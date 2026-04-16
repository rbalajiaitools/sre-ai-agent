/**
 * Command Center - Main operational dashboard with 2-column layout
 */
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  AlertTriangle, 
  Zap, 
  Network, 
  Database, 
  Wifi, 
  Shield, 
  Boxes,
  ArrowRight,
  Clock
} from 'lucide-react';
import { useTenant } from '@/stores/authStore';
import { 
  getDashboardStats,
  getRecentActivity,
} from '@/features/dashboard/api';
import { useInvestigations } from '@/features/investigations/hooks';
import { useIncidents } from '@/features/incidents/hooks';
import { formatDistanceToNow } from 'date-fns';
import { InvestigationStatus } from '@/types';

// Investigation area cards
const investigationAreas = [
  { id: 'incident-triage', name: 'Incident Triage', icon: AlertTriangle, color: 'bg-red-50 text-red-600' },
  { id: 'performance', name: 'Performance', icon: Zap, color: 'bg-yellow-50 text-yellow-600' },
  { id: 'infrastructure', name: 'Infrastructure', icon: Network, color: 'bg-blue-50 text-blue-600' },
  { id: 'database', name: 'Database', icon: Database, color: 'bg-purple-50 text-purple-600' },
  { id: 'networking', name: 'Networking', icon: Wifi, color: 'bg-cyan-50 text-cyan-600' },
  { id: 'deployments', name: 'Deployments', icon: Boxes, color: 'bg-green-50 text-green-600' },
  { id: 'security', name: 'Security', icon: Shield, color: 'bg-orange-50 text-orange-600' },
  { id: 'kubernetes', name: 'Kubernetes', icon: Boxes, color: 'bg-indigo-50 text-indigo-600' },
];

// Sample prompts
const suggestedPrompts = [
  'Check the memory usage and execution duration patterns for the cloudscore-demo-payment-processor Lambda',
  'What code changes or feature improvements were made to Lambda functions in the past week?',
  'Show me error logs for the cloudscore-demo-payment-processor Lambda function in the past 3 days',
  'List all running EC2 instances across all regions with their health status',
  'Show me all failed deployments in the last 24 hours and their root causes',
];

export function CommandCenterPage() {
  const navigate = useNavigate();
  const tenant = useTenant();
  const tenantId = tenant?.id || '';

  // Fetch data
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats', tenantId],
    queryFn: () => getDashboardStats(tenantId),
    enabled: !!tenantId,
  });

  const { data: recentActivity } = useQuery({
    queryKey: ['recent-activity', tenantId],
    queryFn: () => getRecentActivity(tenantId, 8),
    enabled: !!tenantId,
  });

  const { data: investigationsResponse } = useInvestigations();
  const investigations = investigationsResponse?.items || [];

  const { data: incidents } = useIncidents();

  // Calculate metrics
  const openInvestigations = investigations.filter(
    inv => inv.status === InvestigationStatus.INVESTIGATING || inv.status === InvestigationStatus.STARTED
  ).length;

  const resolvedToday = investigations.filter(inv => {
    if (!inv.completed_at) return false;
    const completedDate = new Date(inv.completed_at);
    const today = new Date();
    return completedDate.toDateString() === today.toDateString();
  }).length;

  const activeAlerts = incidents?.filter(inc => 
    inc.state !== '6' && inc.state !== '7' // Not resolved or closed
  ).length || 0;

  const totalAlerts = incidents?.length || 0;

  // Get active incidents with priority
  const activeIncidents = incidents?.filter(inc => 
    inc.state !== '6' && inc.state !== '7'
  ).slice(0, 5) || [];

  return (
    <div className="h-full flex flex-col bg-background overflow-auto">
      <div className="max-w-[1800px] mx-auto w-full p-6 space-y-6">
        {/* Top Section - Dashboard Stats (Full Width) */}
        <div className="space-y-4">
          {/* First Row - 5 cards */}
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-white rounded-lg border p-4">
              <div className="text-xs text-gray-600 mb-1">Total Incidents</div>
              <div className="text-2xl font-bold">{stats?.total_incidents || 0}</div>
              <div className="text-xs text-gray-500 mt-1">{stats?.open_incidents || 0} currently open</div>
            </div>
            <div className="bg-white rounded-lg border p-4">
              <div className="text-xs text-gray-600 mb-1">Critical (P1)</div>
              <div className="text-2xl font-bold text-red-600">{stats?.p1_incidents || 0}</div>
              <div className="text-xs text-gray-500 mt-1">Requires immediate attention</div>
            </div>
            <div className="bg-white rounded-lg border p-4">
              <div className="text-xs text-gray-600 mb-1">High (P2)</div>
              <div className="text-2xl font-bold text-orange-600">{stats?.p2_incidents || 0}</div>
              <div className="text-xs text-gray-500 mt-1">High priority issues</div>
            </div>
            <div className="bg-white rounded-lg border p-4">
              <div className="text-xs text-gray-600 mb-1">Resolved Today</div>
              <div className="text-2xl font-bold text-green-600">{stats?.resolved_today || 0}</div>
              <div className="text-xs text-gray-500 mt-1">Great progress</div>
            </div>
            <div className="bg-white rounded-lg border p-4">
              <div className="text-xs text-gray-600 mb-1">Avg Resolution</div>
              <div className="text-2xl font-bold">{stats?.avg_resolution_hours?.toFixed(1) || '0.0'}h</div>
              <div className="text-xs text-gray-500 mt-1">12% faster</div>
            </div>
          </div>

          {/* AI Investigation Stats */}
          <div className="bg-white rounded-lg border p-4">
            <h3 className="text-sm font-semibold text-gray-600 mb-3">AI Investigation Stats</h3>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <div className="text-2xl font-bold">{stats?.investigations_count || 10}</div>
                <div className="text-xs text-gray-600 mt-1">Total Investigations</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{stats?.auto_resolved_count || 3}</div>
                <div className="text-xs text-gray-600 mt-1">Auto-Resolved</div>
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {stats?.investigations_count ? Math.round((stats.auto_resolved_count / stats.investigations_count) * 100) : 30}%
                </div>
                <div className="text-xs text-gray-600 mt-1">Success Rate</div>
              </div>
            </div>
          </div>
        </div>

        {/* Horizontal Separator */}
        <div className="border-t border-gray-300"></div>

        {/* Bottom Section - Left and Right with Vertical Separator */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left Column - Main Content (8 cols) */}
          <div className="col-span-8 space-y-6 pr-6 border-r border-gray-300">
            {/* Investigate by Area */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                INVESTIGATE BY AREA
              </h2>
              <div className="grid grid-cols-3 gap-3">
                {investigationAreas.slice(0, 6).map((area) => {
                  const Icon = area.icon;
                  return (
                    <button
                      key={area.id}
                      onClick={() => navigate('/chat')}
                      className={`${area.color} p-4 rounded-lg hover:shadow-md transition-all text-left`}
                    >
                      <Icon className="h-5 w-5 mb-2" />
                      <div className="text-sm font-medium">{area.name}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Suggested Prompts */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                  SUGGESTED FOR YOUR ENVIRONMENT
                </h2>
              </div>
              <div className="space-y-2">
                {suggestedPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => navigate('/chat')}
                    className="w-full text-left p-3 bg-white rounded-lg border hover:border-teal-500 hover:shadow-sm transition-all group"
                  >
                    <div className="flex items-center gap-3">
                      <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-teal-600 transition-colors flex-shrink-0" />
                      <span className="text-sm text-gray-700">{prompt}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Recent Activity */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                  RECENT ACTIVITY
                </h2>
                <button
                  onClick={() => navigate('/investigations')}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1"
                >
                  View all
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>
              <div className="bg-white rounded-lg border">
                {recentActivity && recentActivity.length > 0 ? (
                  <div className="divide-y">
                    {recentActivity.slice(0, 5).map((activity) => (
                      <button
                        key={activity.id}
                        onClick={() => navigate('/investigations')}
                        className="w-full p-3 hover:bg-muted/50 transition-colors text-left flex items-center justify-between"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div className={`flex h-2 w-2 rounded-full flex-shrink-0 ${
                            activity.type === 'investigation' ? 'bg-purple-500' : 'bg-blue-500'
                          }`} />
                          <span className="text-sm text-gray-700 truncate">{activity.title}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500 flex-shrink-0 ml-4">
                          <Clock className="h-3 w-3" />
                          {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center">
                    <p className="text-sm text-gray-500">No recent activity</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Widgets (4 cols) */}
          <div className="col-span-4 space-y-6 pl-6">
            {/* System Overview */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                SYSTEM OVERVIEW
              </h2>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white p-4 rounded-lg border">
                  <div className="text-3xl font-bold text-red-600">{openInvestigations}</div>
                  <div className="text-xs text-gray-600 mt-1">Open Investigations</div>
                </div>
                <div className="bg-white p-4 rounded-lg border">
                  <div className="text-3xl font-bold text-green-600">{resolvedToday}</div>
                  <div className="text-xs text-gray-600 mt-1">Resolved today</div>
                </div>
                <div className="bg-white p-4 rounded-lg border">
                  <div className="text-3xl font-bold text-blue-600">{activeAlerts}</div>
                  <div className="text-xs text-gray-600 mt-1">Active alerts</div>
                </div>
                <div className="bg-white p-4 rounded-lg border">
                  <div className="text-3xl font-bold text-gray-900">{totalAlerts}</div>
                  <div className="text-xs text-gray-600 mt-1">Total all time</div>
                </div>
              </div>
            </div>

            {/* Active Incidents */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                  ACTIVE INCIDENTS
                </h2>
                <button
                  onClick={() => navigate('/incidents')}
                  className="text-xs text-teal-600 hover:text-teal-700 font-medium"
                >
                  All
                </button>
              </div>
              <div className="bg-white rounded-lg border">
                {activeIncidents.length > 0 ? (
                  <div className="divide-y">
                    {activeIncidents.slice(0, 4).map((incident) => (
                      <button
                        key={incident.sys_id}
                        onClick={() => navigate('/incidents')}
                        className="w-full p-3 hover:bg-muted/50 transition-colors text-left"
                      >
                        <div className="space-y-2">
                          <div className="text-xs font-medium text-gray-900 line-clamp-2">
                            {incident.short_description}
                          </div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                              incident.priority === '1' ? 'bg-red-100 text-red-700' :
                              incident.priority === '2' ? 'bg-orange-100 text-orange-700' :
                              'bg-yellow-100 text-yellow-700'
                            }`}>
                              {incident.priority === '1' ? 'critical' : 
                               incident.priority === '2' ? 'high' : 'medium'}
                            </span>
                            <span className="text-xs text-gray-500 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {formatDistanceToNow(new Date(incident.opened_at), { addSuffix: true })}
                            </span>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center">
                    <p className="text-sm text-gray-500">No active incidents</p>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Access */}
            <div className="space-y-4">
              <h2 className="text-sm font-semibold text-gray-600 uppercase tracking-wider">
                QUICK ACCESS
              </h2>
              <div className="space-y-2">
                <button
                  onClick={() => navigate('/investigations')}
                  className="w-full text-left p-3 bg-white rounded-lg border hover:border-teal-500 hover:shadow-sm transition-all flex items-center justify-between group"
                >
                  <span className="text-sm font-medium text-gray-700">All Investigations</span>
                  <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-teal-600" />
                </button>
                <button
                  onClick={() => navigate('/topology')}
                  className="w-full text-left p-3 bg-white rounded-lg border hover:border-teal-500 hover:shadow-sm transition-all flex items-center justify-between group"
                >
                  <span className="text-sm font-medium text-gray-700">Connected Integrations</span>
                  <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-teal-600" />
                </button>
                <button
                  onClick={() => navigate('/knowledge')}
                  className="w-full text-left p-3 bg-white rounded-lg border hover:border-teal-500 hover:shadow-sm transition-all flex items-center justify-between group"
                >
                  <span className="text-sm font-medium text-gray-700">Knowledge Graph</span>
                  <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-teal-600" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
