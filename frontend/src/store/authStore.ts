import { create } from 'zustand';
import { authService } from '../services/auth';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, passwordConfirm: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: authService.getCurrentUser(),
  isAuthenticated: authService.isAuthenticated(),

  setUser: (user) => set({ user, isAuthenticated: !!user }),

  login: async (username, password) => {
    try {
      console.log('[AuthStore] Login attempt');
      const response = await authService.login(username, password);
      set({ user: response.user, isAuthenticated: true });
      console.log('[AuthStore] Login successful, user set');
    } catch (error) {
      console.error('[AuthStore] Login failed:', error);
      throw error;
    }
  },

  register: async (username, email, password, passwordConfirm) => {
    try {
      console.log('[AuthStore] Registration attempt');
      const response = await authService.register(username, email, password, passwordConfirm);
      set({ user: response.user, isAuthenticated: true });
      console.log('[AuthStore] Registration successful, user set');
    } catch (error) {
      console.error('[AuthStore] Registration failed:', error);
      throw error;
    }
  },

  logout: () => {
    console.log('[AuthStore] Logging out');
    authService.logout();
    set({ user: null, isAuthenticated: false });
    console.log('[AuthStore] Logout complete');
  },

  checkAuth: () => {
    console.log('[AuthStore] Checking authentication...');
    const user = authService.getCurrentUser();
    const isAuth = authService.isAuthenticated();
    console.log('[AuthStore] Auth check result:', { hasUser: !!user, isAuthenticated: isAuth });
    set({ user, isAuthenticated: isAuth });
  },
}));

