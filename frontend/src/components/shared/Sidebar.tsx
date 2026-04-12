/**
 * Sidebar navigation component
 */
import { NavLink } from 'react-router-dom';
import {
  MessageSquare,
  Bell,
  Search,
  Network,
  BarChart3,
  Settings,
  Menu,
  X,
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
  { name: 'Incidents', path: '/incidents', icon: Bell },
  { name: 'Investigations', path: '/investigations', icon: Search },
  { name: 'Topology', path: '/topology', icon: Network },
  { name: 'Dashboard', path: '/dashboard', icon: BarChart3 },
];

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useAppStore();

  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-card transition-all duration-300',
        sidebarCollapsed ? 'w-14' : 'w-60'
      )}
    >
      {/* Logo/Brand */}
      <div className="flex h-14 items-center border-b px-4">
        {!sidebarCollapsed && (
          <h1 className="text-lg font-semibold">
            CloudScore Astra AI
          </h1>
        )}
        {sidebarCollapsed && (
          <div className="flex h-8 w-8 items-center justify-center rounded bg-primary text-primary-foreground font-bold">
            CA
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
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  'hover:bg-accent hover:text-accent-foreground',
                  isActive
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground',
                  sidebarCollapsed && 'justify-center'
                )
              }
              title={sidebarCollapsed ? item.name : undefined}
              aria-label={item.name}
            >
              <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
              {!sidebarCollapsed && <span>{item.name}</span>}
              {!sidebarCollapsed && item.badge !== undefined && (
                <span
                  className="ml-auto flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs text-destructive-foreground"
                  aria-label={`${item.badge} notifications`}
                >
                  {item.badge}
                </span>
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
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              'hover:bg-accent hover:text-accent-foreground',
              isActive
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground',
              sidebarCollapsed && 'justify-center'
            )
          }
          title={sidebarCollapsed ? 'Settings' : undefined}
          aria-label="Settings"
        >
          <Settings className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          {!sidebarCollapsed && <span>Settings</span>}
        </NavLink>
      </div>

      {/* Collapse Toggle */}
      <div className="border-t p-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className={cn('w-full', sidebarCollapsed && 'px-0')}
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? (
            <Menu className="h-5 w-5" aria-hidden="true" />
          ) : (
            <>
              <X className="h-5 w-5 mr-2" aria-hidden="true" />
              <span>Collapse</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
