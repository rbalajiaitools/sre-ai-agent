/**
 * Zustand store for global UI state
 */
import { create } from 'zustand';

interface AppState {
  activeChatId: string | null;
  sidebarCollapsed: boolean;
}

interface AppActions {
  setActiveChatId: (chatId: string | null) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

type AppStore = AppState & AppActions;

export const useAppStore = create<AppStore>((set) => ({
  // Initial state
  activeChatId: null,
  sidebarCollapsed: false,

  // Actions
  setActiveChatId: (chatId: string | null) => {
    set({ activeChatId: chatId });
  },

  toggleSidebar: () => {
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
  },

  setSidebarCollapsed: (collapsed: boolean) => {
    set({ sidebarCollapsed: collapsed });
  },
}));
