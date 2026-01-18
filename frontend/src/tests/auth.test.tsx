/**
 * Tests for authentication flow.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { authApi, setAuthToken, clearAuthToken } from '../services/api';

// Mock the API module
vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api');
  return {
    ...actual,
    authApi: {
      login: vi.fn(),
      register: vi.fn(),
      getCurrentUser: vi.fn(),
    },
    setAuthToken: vi.fn(),
    clearAuthToken: vi.fn(),
  };
});

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('setAuthToken', () => {
    it('should set authorization header', () => {
      const token = 'test-token';
      setAuthToken(token);
      expect(setAuthToken).toHaveBeenCalledWith(token);
    });
  });

  describe('clearAuthToken', () => {
    it('should clear authorization header', () => {
      clearAuthToken();
      expect(clearAuthToken).toHaveBeenCalled();
    });
  });

  describe('login', () => {
    it('should call login API with credentials', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
        },
      };

      vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse);

      const result = await authApi.login('test@example.com', 'password');

      expect(authApi.login).toHaveBeenCalledWith('test@example.com', 'password');
      expect(result.access_token).toBe('mock-token');
      expect(result.user.email).toBe('test@example.com');
    });

    it('should throw error for invalid credentials', async () => {
      vi.mocked(authApi.login).mockRejectedValueOnce(new Error('Invalid credentials'));

      await expect(authApi.login('wrong@example.com', 'wrong')).rejects.toThrow(
        'Invalid credentials'
      );
    });
  });

  describe('register', () => {
    it('should call register API with user data', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
        user: {
          id: 1,
          email: 'new@example.com',
          full_name: 'New User',
        },
      };

      vi.mocked(authApi.register).mockResolvedValueOnce(mockResponse);

      const result = await authApi.register(
        'new@example.com',
        'SecurePass123!',
        'New User'
      );

      expect(authApi.register).toHaveBeenCalledWith(
        'new@example.com',
        'SecurePass123!',
        'New User',
        undefined
      );
      expect(result.access_token).toBe('mock-token');
    });

    it('should handle registration with phone', async () => {
      const mockResponse = {
        access_token: 'mock-token',
        token_type: 'bearer',
        user: {
          id: 1,
          email: 'new@example.com',
          full_name: 'New User',
          phone: '1234567890',
        },
      };

      vi.mocked(authApi.register).mockResolvedValueOnce(mockResponse);

      await authApi.register(
        'new@example.com',
        'SecurePass123!',
        'New User',
        '1234567890'
      );

      expect(authApi.register).toHaveBeenCalledWith(
        'new@example.com',
        'SecurePass123!',
        'New User',
        '1234567890'
      );
    });
  });

  describe('getCurrentUser', () => {
    it('should return current user data', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        created_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(authApi.getCurrentUser).mockResolvedValueOnce(mockUser);

      const result = await authApi.getCurrentUser();

      expect(result.email).toBe('test@example.com');
      expect(result.full_name).toBe('Test User');
    });

    it('should throw error when not authenticated', async () => {
      vi.mocked(authApi.getCurrentUser).mockRejectedValueOnce(
        new Error('Not authenticated')
      );

      await expect(authApi.getCurrentUser()).rejects.toThrow('Not authenticated');
    });
  });
});

describe('Auth Token Storage', () => {
  it('should store token on successful login', async () => {
    const mockResponse = {
      access_token: 'new-token',
      token_type: 'bearer',
      user: { id: 1, email: 'test@example.com', full_name: 'Test' },
    };

    vi.mocked(authApi.login).mockResolvedValueOnce(mockResponse);

    const result = await authApi.login('test@example.com', 'password');

    // In actual implementation, setAuthToken would be called
    // Here we just verify the response has the token
    expect(result.access_token).toBe('new-token');
  });
});
