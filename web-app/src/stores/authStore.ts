import { create } from 'zustand';
import { authService, User } from '../services/authService';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User) => void;
  logout: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => {
    authService.logout();
    set({ user: null, isAuthenticated: false });
  },
  checkAuth: () => {
    const user = authService.getCurrentUser();
    set({ user, isAuthenticated: !!user });
  }
}));
