import { apiClient } from './api';
import type { AuthResponse, User } from '../types';

export const authService = {
  async register(
    username: string,
    email: string,
    password: string,
    passwordConfirm: string
  ): Promise<AuthResponse> {
    try {
      console.log('[AuthService] Registering...');
      const response = await apiClient.register(username, email, password, passwordConfirm);
      this.setAuthData(response);
      console.log('[AuthService] Registration complete, user:', response.user.username);
      return response;
    } catch (error: any) {
      console.error('[AuthService] Registration error:', error);
      throw error;
    }
  },

  async login(username: string, password: string): Promise<AuthResponse> {
    try {
      console.log('[AuthService] Logging in...');
      const response = await apiClient.login(username, password);
      this.setAuthData(response);
      console.log('[AuthService] Login complete, user:', response.user.username);
      return response;
    } catch (error: any) {
      console.error('[AuthService] Login error:', error);
      throw error;
    }
  },

  setAuthData(data: AuthResponse): void {
    console.log('[AuthService] Setting auth data in localStorage');
    localStorage.setItem('access_token', data.tokens.access);
    localStorage.setItem('refresh_token', data.tokens.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
  },

  logout(): void {
    console.log('[AuthService] Logging out, clearing localStorage');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  isAuthenticated(): boolean {
    const isAuth = !!localStorage.getItem('access_token');
    console.log('[AuthService] isAuthenticated:', isAuth);
    return isAuth;
  },

  getCurrentUser(): User | null {
    try {
      const userStr = localStorage.getItem('user');
      if (!userStr) {
        console.log('[AuthService] No user in localStorage');
        return null;
      }
      const user = JSON.parse(userStr);
      console.log('[AuthService] Current user:', user.username);
      return user;
    } catch (error) {
      console.error('[AuthService] Error parsing user from localStorage:', error);
      return null;
    }
  },
};

