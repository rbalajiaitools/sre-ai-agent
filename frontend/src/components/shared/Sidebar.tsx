/**
 * Sidebar navigation - Professional design with collapse/expand like resolve.ai
 */
import { NavLink } from 'react-router-dom';
import {
  MessageSquare,
  AlertCircle,
  Search,
  Network,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface NavItem {
  name: string;
  path: string;
  icon: typeof MessageSquare;
  badge?: number;
}

const navItems: NavItem[] = [
  { name: 'Chat', path: '/chat', icon: MessageSquare },
  { name: 'Incidents', path: '/incidents', icon: AlertCircle },
  { name: 'Investigations', path: '/investigations', icon: Search },
  { name: 'Topology', path: '/topology', icon: Network },
  { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
  { name: 'Simulation', path: '/simulation', icon: Zap },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={cn(
        'flex flex-col bg-card border-r transition-all duration-300 ease-in-out relative',
        sidebarCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Collapse/Expand Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleSidebar}
        className={cn(
          'absolute -right-3 top-6 z-10 h-6 w-6 rounded-full border bg-background shadow-md hover:bg-accent',
          'transition-transform duration-300'
        )}
        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </Button>

      {/* Logo/Brand */}
      <div className={cn(
        'flex h-16 items-center border-b transition-all duration-300',
        sidebarCollapsed ? 'justify-center px-2' : 'gap-3 px-6'
      )}>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-lime-400 to-lime-600 shadow-lg flex-shrink-0">
          <svg
            className="h-5 w-5 text-gray-900"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
        {!sidebarCollapsed && (
          <div className="flex flex-col overflow-hidden">
            <h1 className="text-base font-bold leading-none tracking-tight truncate">
              CloudScore
            </h1>
            <p className="text-xs text-muted-foreground font-medium truncate">
              Astra AI
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2" aria-label="Main navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                  'hover:bg-accent group relative',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground',
                  sidebarCollapsed && 'justify-center'
                )
              }
              title={sidebarCollapsed ? item.name : undefined}
              aria-label={item.name}
            >
              <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              {!sidebarCollapsed && (
                <>
                  <span className="truncate">{item.name}</span>
                  {item.badge !== undefined && (
                    <span
                      className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full bg-destructive px-1.5 text-xs font-bold text-destructive-foreground"
                      aria-label={`${item.badge} notifications`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
              
              {/* Tooltip for collapsed state */}
              {sidebarCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                  {item.name}
                </div>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Settings (pinned to bottom) */}
      <div className="border-t p-2">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
              'hover:bg-accent group relative',
              isActive
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
              sidebarCollapsed && 'justify-center'
            )
          }
          title={sidebarCollapsed ? 'Settings' : undefined}
          aria-label="Settings"
        >
          <Settings className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          {!sidebarCollapsed && <span className="truncate">Settings</span>}
          
          {/* Tooltip for collapsed state */}
          {sidebarCollapsed && (
            <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
              Settings
            </div>
          )}
        </NavLink>
      </div>
    </aside>
  );
}
