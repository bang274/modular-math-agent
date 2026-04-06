import { create } from 'zustand';

interface UIState {
  theme: 'dark' | 'light';
  sidebarOpen: boolean;
  toggleTheme: () => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'dark',
  sidebarOpen: false,
  toggleTheme: () =>
    set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
  toggleSidebar: () =>
    set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
