import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import { authTokenStorage } from '../../utils/secureStorage';
import { API_URL } from '../../config';
import { getCSRFToken } from '../../utils/csrf';

const API_BASE_URL = API_URL;

// ===== ENHANCED API CLIENT WITH TIMEOUT AND RETRY =====
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minute timeout - extended for large file uploads and complex operations
  withCredentials: true, // Send cookies with requests (required for CSRF)
  headers: {
    'Content-Type': 'application/json',
  },
});

// ===== CSRF REQUEST INTERCEPTOR =====
api.interceptors.request.use(
  (config) => {
    // Add CSRF token to state-changing requests
    const unsafeMethods = ['POST', 'PUT', 'DELETE', 'PATCH'];
    if (config.method && unsafeMethods.includes(config.method.toUpperCase())) {
      const csrfToken = getCSRFToken();
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ===== RETRY CONFIGURATION =====
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second base delay

// Retry-able status codes
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];

/**
 * Check if error should trigger a retry
 */
const shouldRetry = (error: AxiosError, retryCount: number): boolean => {
  if (retryCount >= MAX_RETRIES) return false;

  // Retry on network errors (no response)
  if (!error.response) return true;

  // Retry on specific status codes
  if (error.response && RETRYABLE_STATUS_CODES.includes(error.response.status)) {
    return true;
  }

  return false;
};

/**
 * Calculate exponential backoff delay
 */
const getRetryDelay = (retryCount: number): number => {
  return RETRY_DELAY * Math.pow(2, retryCount);
};

/**
 * Sleep for specified milliseconds
 */
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Token management
export const setAuthToken = (token: string) => {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

export const clearAuthToken = () => {
  delete api.defaults.headers.common['Authorization'];
};

// Initialize CSRF token by making a GET request to set the cookie
export const initializeCSRF = async (): Promise<void> => {
  try {
    await api.get('/api/csrf-token');
  } catch (error) {
    console.warn('Failed to initialize CSRF token:', error);
  }
};

// ===== ENHANCED RESPONSE INTERCEPTOR =====
api.interceptors.response.use(
  (response) => {
    // Log CSRF token rotation for debugging (removed in production builds)
    if (response.headers['x-csrf-token-rotated'] === 'true') {
      console.debug('CSRF token rotated by server');
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _retryCount?: number };

    // Initialize retry tracking
    if (!originalRequest._retryCount) {
      originalRequest._retryCount = 0;
    }

    // Handle network errors (timeout, connection refused, etc.)
    if (!error.response) {
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        console.error('Request timeout:', error.message);

        // Retry on timeout
        if (shouldRetry(error, originalRequest._retryCount)) {
          originalRequest._retryCount++;
          const delay = getRetryDelay(originalRequest._retryCount - 1);
          await sleep(delay);
          return api.request(originalRequest);
        }

        throw new Error('Request timeout. Please check your internet connection and try again.');
      }

      console.error('[API] Network error details:', error);
      throw new Error('Network error. Please check your internet connection or try again later.');
    }

    const status = error.response.status;
    const responseData = error.response.data as any;

    // Handle specific HTTP error codes
    switch (status) {
      case 401: // Unauthorized
        // Skip redirect for auth endpoints - let them handle their own errors
        const requestUrl = originalRequest.url || '';
        const isAuthEndpoint = requestUrl.includes('/api/auth/login') || requestUrl.includes('/api/auth/register');

        if (isAuthEndpoint) {
          // Let the login/register components handle 401 errors
          throw new Error(responseData?.detail || 'Authentication failed');
        }

        if (!originalRequest._retry) {
          originalRequest._retry = true;

          // Check if we have a token
          const token = authTokenStorage.getToken();
          if (!token) {
            window.location.href = '/login';
            return Promise.reject(error);
          }

          // Token exists but is expired, redirect to login
          clearAuthToken();
          authTokenStorage.clearAll();
          window.location.href = '/login';
        }
        break;

      case 403: // Forbidden
        // Check if this is a CSRF error - retry once after token refresh
        const errorDetail = responseData?.detail || '';
        if (errorDetail.includes('CSRF') && !originalRequest._retry) {
          originalRequest._retry = true;
          // Wait briefly for cookie to update, then retry with fresh token
          await sleep(100);
          return api.request(originalRequest);
        }
        throw new Error(
          responseData?.message ||
          'Access forbidden. You do not have permission to perform this action.'
        );

      case 404: // Not Found
        throw new Error(
          responseData?.message ||
          'The requested resource was not found.'
        );

      case 413: // Payload Too Large
        throw new Error(
          responseData?.message ||
          'File upload is too large. Maximum file size is 10MB.'
        );

      case 422: // Validation Error
        if (responseData?.details && Array.isArray(responseData.details)) {
          // Format field-specific errors
          const fieldErrors = responseData.details
            .map((detail: any) => `${detail.field}: ${detail.message}`)
            .join('; ');
          throw new Error(`Validation failed: ${fieldErrors}`);
        }
        throw new Error(
          responseData?.message ||
          'Validation failed. Please check your input and try again.'
        );

      case 429: // Too Many Requests
        // Retry with exponential backoff
        if (shouldRetry(error, originalRequest._retryCount)) {
          originalRequest._retryCount++;
          const delay = getRetryDelay(originalRequest._retryCount - 1);
          console.warn(`Rate limited. Retrying in ${delay}ms...`);
          await sleep(delay);
          return api.request(originalRequest);
        }
        throw new Error(
          responseData?.message ||
          'Too many requests. Please wait a moment and try again.'
        );

      case 500: // Internal Server Error
      case 502: // Bad Gateway
      case 503: // Service Unavailable
      case 504: // Gateway Timeout
        // Retry server errors
        if (shouldRetry(error, originalRequest._retryCount)) {
          originalRequest._retryCount++;
          const delay = getRetryDelay(originalRequest._retryCount - 1);
          console.warn(`Server error ${status}. Retrying in ${delay}ms... (attempt ${originalRequest._retryCount}/${MAX_RETRIES})`);
          await sleep(delay);
          return api.request(originalRequest);
        }
        console.error('[API] Server error details:', {
          status,
          data: responseData,
          message: responseData?.message,
          detail: responseData?.detail,
          error: error.message
        });
        throw new Error(
          responseData?.detail ||
          responseData?.message ||
          'Server error. Please try again later or contact support if the problem persists.'
        );

      default:
        // Generic error handling
        throw new Error(
          responseData?.message ||
          error.message ||
          'An unexpected error occurred. Please try again.'
        );
    }

    return Promise.reject(error);
  }
);

export { api };
