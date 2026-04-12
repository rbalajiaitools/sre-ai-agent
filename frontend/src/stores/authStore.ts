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

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      token: null,
      tenant: null,
      isAuthenticated: false,

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
    }
  )
);

// Selector hooks for convenience
export const useAuth = () => useAuthStore((state) => ({
  isAuthenticated: state.isAuthenticated,
  token: state.token,
}));

export const useUser = () => useAuthStore((state) => state.user);

export const useTenant = () => useAuthStore((state) => state.tenant);
