import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { User } from '../types';
import { authApi, setAuthToken, clearAuthToken, initializeCSRF, registerNavigate } from '../services/api';
import { authTokenStorage } from '../utils/secureStorage';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (code: string, state: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, phone?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
  updateUserProfile: (userData: any) => Promise<void>;
  sendVerificationEmail: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Register navigate callback so the API client can use React Router navigation
  useEffect(() => {
    registerNavigate(navigate);
  }, [navigate]);

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      // Initialize CSRF token in background (don't block auth flow)
      // CSRF cookie will be ready before any POST/PUT/DELETE requests
      initializeCSRF();

      const token = authTokenStorage.getToken();
      if (token) {
        setAuthToken(token);
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
          // Also store user data in secure storage
          authTokenStorage.setUserData(userData);
        } catch (error) {
          // Token is invalid, clear it
          authTokenStorage.clearAll();
          clearAuthToken();
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    try {
      const response = await authApi.login(email, password);
      const { access_token, user: userData } = response;

      // Store token and user data securely
      authTokenStorage.setToken(access_token);
      authTokenStorage.setUserData(userData);
      setAuthToken(access_token);
      setUser(userData);

      // Refresh CSRF token after login (non-blocking)
      initializeCSRF();
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  const register = async (
    email: string,
    password: string,
    fullName: string,
    phone?: string
  ): Promise<void> => {
    try {
      const response = await authApi.register(email, password, fullName, phone);
      const { access_token, user: userData } = response;

      // Store token and user data securely
      authTokenStorage.setToken(access_token);
      authTokenStorage.setUserData(userData);
      setAuthToken(access_token);
      setUser(userData);

      // Refresh CSRF token after registration (non-blocking)
      initializeCSRF();
    } catch (error: any) {
      if (error.response?.status === 400 && error.response?.data?.detail === 'Email already registered') {
        throw new Error('This email is already registered. Please try logging in instead.');
      }
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  const logout = async (): Promise<void> => {
    try {
      // Call backend to revoke the token
      await authApi.logout();
    } catch (error) {
      // Log but don't block - token will expire eventually anyway
      console.warn('Logout API call failed:', error);
    } finally {
      // Always clear local storage regardless of API success
      authTokenStorage.clearAll();
      clearAuthToken();
      setUser(null);
    }
  };

  const updateUser = (userData: Partial<User>): void => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  const updateUserProfile = async (userData: any): Promise<void> => {
    try {
      const updatedUser = await authApi.updateProfile(userData);
      // Update the local user state with the returned data
      setUser(updatedUser);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update profile');
    }
  };

  const loginWithGoogle = async (code: string, state: string): Promise<void> => {
    try {
      const response = await authApi.googleCallback(code, state);
      const { access_token, user: userData } = response;

      // Store token and user data securely
      authTokenStorage.setToken(access_token);
      authTokenStorage.setUserData(userData);
      setAuthToken(access_token);
      setUser(userData);

      // Refresh CSRF token after login (non-blocking)
      initializeCSRF();
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Google login failed');
    }
  };

  const sendVerificationEmail = async (): Promise<void> => {
    try {
      await authApi.sendVerificationEmail();
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to send verification email');
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    loginWithGoogle,
    register,
    logout,
    updateUser,
    updateUserProfile,
    sendVerificationEmail,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthProvider;