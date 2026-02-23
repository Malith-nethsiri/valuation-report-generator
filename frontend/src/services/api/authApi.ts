import type { AuthResponse, User, UserUpdate } from '../../types';
import { api } from './client';

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/api/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  register: async (
    email: string,
    password: string,
    fullName: string,
    phone?: string
  ): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/api/auth/register', {
      email,
      password,
      full_name: fullName,
      phone,
    });
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/api/auth/me');
    return response.data;
  },

  updateProfile: async (userData: UserUpdate): Promise<User> => {
    const response = await api.put<User>('/api/profile', userData);
    return response.data;
  },

  logout: async (): Promise<void> => {
    // Call backend to revoke the token
    // This ensures the token can't be reused even if it hasn't expired
    await api.post('/api/auth/logout');
  },

  // Google OAuth
  getGoogleAuthUrl: async (): Promise<{ authorization_url: string; state: string }> => {
    const response = await api.get<{ authorization_url: string; state: string }>(
      '/api/auth/google/authorize'
    );
    return response.data;
  },

  googleCallback: async (code: string, state: string): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/api/auth/google/callback', {
      code,
      state,
    });
    return response.data;
  },

  // Email Verification
  sendVerificationEmail: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<{ success: boolean; message: string; email_verified: boolean }>(
      '/api/auth/send-verification'
    );
    return response.data;
  },

  verifyEmail: async (email: string, token: string): Promise<{ success: boolean; message: string; email_verified: boolean }> => {
    const response = await api.post<{ success: boolean; message: string; email_verified: boolean }>(
      '/api/auth/verify-email',
      { email, token }
    );
    return response.data;
  },
};
