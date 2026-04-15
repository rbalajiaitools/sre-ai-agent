/**
 * Zustand store for authentication state
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Tenant } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  tenant: Tenant | null;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (token: string, user: User, tenant: Tenant) => void;
  logout: () => void;
  setTenant: (tenant: Tenant) => void;
  setUser: (user: User) => void;
}

type AuthStore = AuthState & AuthActions;

// Default demo user and tenant for development
const DEFAULT_USER: User = {
  id: 'user-001',
  email: 'demo@example.com',
  name: 'Demo User',
  role: 'admin',
};

const DEFAULT_TENANT: Tenant = {
  id: 'tenant-001',
  name: 'CloudScore Astra AI',
  plan: 'enterprise',
  created_at: '2024-01-01T00:00:00Z',
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state - auto-login for development
      user: DEFAULT_USER,
      token: 'demo-token-12345',
      tenant: DEFAULT_TENANT,
      isAuthenticated: true,

      // Actions
      login: (token: string, user: User, tenant: Tenant) => {
        set({
          token,
          user,
          tenant,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({
          user: null,
          token: null,
          tenant: null,
          isAuthenticated: false,
        });
      },

      setTenant: (tenant: Tenant) => {
        set({ tenant });
      },

      setUser: (user: User) => {
        set({ user });
      },
    }),
    {
      name: 'auth-storage',
      version: 2, // Increment version to force cache clear
      migrate: (persistedState: any, version: number) => {
        // Force reset to default tenant if version changed
        if (version < 2) {
          return {
            user: DEFAULT_USER,
            token: 'demo-token-12345',
            tenant: DEFAULT_TENANT,
            isAuthenticated: true,
          };
        }
        return persistedState;
      },
    }
  )
);

// Selector hooks for convenience
export const useAuth = () => useAuthStore((state) => ({
  isAuthenticated: state.isAuthenticated,
  token: state.token,
  user: state.user,
  tenant: state.tenant,
}));

export const useUser = () => useAuthStore((state) => state.user);

export const useTenant = () => useAuthStore((state) => state.tenant);
