import { apiClient } from './apiClient';

export interface User {
  email: string;
  full_name?: string;
  role: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

class AuthService {
  async login(email: string, password: string): Promise<LoginResponse> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    // Using standard fetch here because OAuth2 form-urlencoded is needed
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Invalid email or password');
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    return data;
  }

  logout() {
    localStorage.removeItem('access_token');
    window.dispatchEvent(new Event('auth:unauthorized'));
  }

  // Parses JWT to extract basic user info (since there is no /me endpoint in auth routes audited)
  getCurrentUser(): User | null {
    const token = localStorage.getItem('access_token');
    if (!token) return null;

    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));

      const payload = JSON.parse(jsonPayload);
      return {
        email: payload.sub,
        role: payload.role || 'user',
      };
    } catch (e) {
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }
}

export const authService = new AuthService();
