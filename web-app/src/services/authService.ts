import { apiClient } from './apiClient';

export interface User {
  id?: number;
  email: string;
  full_name?: string;
  phone_number?: string;
  role: string;
  role_code?: string;
  data_scope?: string;
  permissions?: string[];
  organization_id?: number;
  safety_score?: number | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role?: string;
  role_code?: string;
  data_scope?: string;
  permissions?: string[];
  full_name?: string;
  email?: string;
}

export const DEFAULT_PERSONAL_USER: User = {
  id: 1,
  email: 'driver@smartassistant.local',
  full_name: 'Người Lái Xe',
  phone_number: '0901234567',
  role: 'PERSONAL_DRIVER',
  role_code: 'ENTERPRISE_ADMIN',
  data_scope: 'SELF',
  permissions: ['*'],
  organization_id: 1,
  safety_score: 98,
};

class AuthService {
  async login(email: string, password: string): Promise<LoginResponse> {
    return {
      access_token: 'personal_token',
      token_type: 'bearer',
      role: 'PERSONAL_DRIVER',
      role_code: 'ENTERPRISE_ADMIN',
      full_name: 'Người Lái Xe',
      email: 'driver@smartassistant.local',
      permissions: ['*'],
    };
  }

  async fetchCurrentUser(): Promise<User | null> {
    return this.getCurrentUser();
  }

  logout() {
    // Không cần xóa gì khi ở chế độ cá nhân
  }

  getCurrentUser(): User {
    return DEFAULT_PERSONAL_USER;
  }

  hasPermission(permission: string, user?: User | null): boolean {
    return true;
  }

  hasAnyPermission(permissions: string[], user?: User | null): boolean {
    return true;
  }

  async loginForRole(role: string): Promise<LoginResponse | null> {
    return {
      access_token: 'personal_token',
      token_type: 'bearer',
      role: 'PERSONAL_DRIVER',
      role_code: 'ENTERPRISE_ADMIN',
      full_name: 'Người Lái Xe',
      email: 'driver@smartassistant.local',
    };
  }

  isAuthenticated(): boolean {
    return true;
  }
}

export const authService = new AuthService();

