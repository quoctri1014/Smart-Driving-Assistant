import { create } from 'zustand';
import { authService, User, DEFAULT_PERSONAL_USER } from '../services/authService';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
  checkAuth: () => void;
  refreshUser: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: DEFAULT_PERSONAL_USER,
  isAuthenticated: true,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => {
    authService.logout();
    set({ user: DEFAULT_PERSONAL_USER, isAuthenticated: true });
  },
  checkAuth: () => {
    const user = authService.getCurrentUser();
    set({ user: user || DEFAULT_PERSONAL_USER, isAuthenticated: true });
  },
  refreshUser: async () => {
    const user = await authService.fetchCurrentUser();
    set({ user: user || DEFAULT_PERSONAL_USER, isAuthenticated: true });
  },
  hasPermission: () => true,
  hasAnyPermission: () => true,
}));

