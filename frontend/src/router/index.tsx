/**
 * React Router v6 configuration with protected routes
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { useAuth } from '@/stores/authStore';
import { AppLayout } from '@/components/shared/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { OnboardingPage } from '@/features/onboarding/components/OnboardingPage';
import { ChatPage } from '@/features/chat/components/ChatPage';
import { IncidentsPage } from '@/features/incidents/components/IncidentsPage';
import { InvestigationsPage } from '@/features/investigations/components/InvestigationsPage';
import { InvestigationDetailPage } from '@/features/investigations/components/InvestigationDetailPage';
import { TopologyPage } from '@/features/topology/components/TopologyPage';
import { DashboardPage } from '@/features/dashboard/components/DashboardPage';
import { CommandCenterPage } from '@/features/command-center';
import { KnowledgeGraphPage } from '@/features/knowledge';
import { SimulationPage } from '@/features/simulation/components/SimulationPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { DebugPage } from '@/pages/DebugPage';

/**
 * Protected Route wrapper - redirects to login if not authenticated
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

/**
 * Layout wrapper for authenticated pages
 */
function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

/**
 * Router configuration
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/command-center" replace />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/onboarding',
    element: (
      <ProtectedRoute>
        <OnboardingPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/command-center',
    element: (
      <ProtectedLayout>
        <CommandCenterPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/chat',
    element: (
      <ProtectedLayout>
        <ChatPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/chat/:threadId',
    element: (
      <ProtectedLayout>
        <ChatPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/incidents',
    element: (
      <ProtectedLayout>
        <IncidentsPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/investigations',
    element: (
      <ProtectedLayout>
        <InvestigationsPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/investigations/:id',
    element: (
      <ProtectedLayout>
        <InvestigationDetailPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/topology',
    element: (
      <ProtectedLayout>
        <TopologyPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/knowledge',
    element: (
      <ProtectedLayout>
        <KnowledgeGraphPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedLayout>
        <DashboardPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/simulation',
    element: (
      <ProtectedLayout>
        <SimulationPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/settings/*',
    element: (
      <ProtectedLayout>
        <SettingsPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '/debug',
    element: (
      <ProtectedLayout>
        <DebugPage />
      </ProtectedLayout>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/chat" replace />,
  },
]);
