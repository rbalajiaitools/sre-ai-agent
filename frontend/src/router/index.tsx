/**
 * React Router v6 configuration with protected routes
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { useAuth } from '@/stores/authStore';
import { AppLayout } from '@/components/shared/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { OnboardingPage } from '@/pages/OnboardingPage';
import { ChatPage } from '@/features/chat/components/ChatPage';
import { IncidentsPage } from '@/features/incidents/components/IncidentsPage';
import { InvestigationsPage } from '@/pages/InvestigationsPage';
import { TopologyPage } from '@/pages/TopologyPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { SettingsPage } from '@/pages/SettingsPage';

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
    element: <Navigate to="/chat" replace />,
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
        <InvestigationsPage />
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
    path: '/dashboard',
    element: (
      <ProtectedLayout>
        <DashboardPage />
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
    path: '*',
    element: <Navigate to="/chat" replace />,
  },
]);
