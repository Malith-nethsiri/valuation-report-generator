import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import type {
  UserData,
  UserDataResponse,
  AuthResponse,
  User,
  UserUpdate,
  BankAccount,
  BankAccountCreate,
  BankAccountUpdate,
  Report,
  ReportCreate,
  TemplateMetadata,
  TemplateListResponse
} from '../types';
import { authTokenStorage } from '../utils/secureStorage';
import { API_URL } from '../config';
import { downloadFromResponse } from '../utils/downloadHelper';

const API_BASE_URL = API_URL;

// ===== ENHANCED API CLIENT WITH TIMEOUT AND RETRY =====
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minute timeout - extended for large file uploads and complex operations
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// ===== ENHANCED RESPONSE INTERCEPTOR =====
api.interceptors.response.use(
  (response) => response,
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

export const submitUserData = async (data: UserData): Promise<UserDataResponse> => {
  const response = await api.post<UserDataResponse>('/api/submit', data);
  return response.data;
};

export const generateAndDownloadDocx = async (userDataId: number): Promise<void> => {
  const response = await api.post(
    `/api/generate-docx/${userDataId}`,
    {},
    {
      responseType: 'blob',
    }
  );

  downloadFromResponse(
    response.data,
    response.headers['content-disposition'],
    'document.docx'
  );
};

export const submitAndGenerateDocx = async (data: UserData): Promise<void> => {
  const response = await api.post('/api/submit-and-generate', data, {
    responseType: 'blob',
  });

  downloadFromResponse(
    response.data,
    response.headers['content-disposition'],
    'document.docx'
  );
};

export const getAllUserData = async (): Promise<UserDataResponse[]> => {
  const response = await api.get<UserDataResponse[]>('/api/user-data');
  return response.data;
};

export const getUserData = async (id: number): Promise<UserDataResponse> => {
  const response = await api.get<UserDataResponse>(`/api/user-data/${id}`);
  return response.data;
};

export const healthCheck = async (): Promise<{ status: string; message: string }> => {
  const response = await api.get('/api/health');
  return response.data;
};

// Authentication API
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
};

// Bank Account Management API
export const bankAccountApi = {
  getAll: async (): Promise<BankAccount[]> => {
    const response = await api.get<BankAccount[]>('/api/users/me/bank-accounts');
    return response.data;
  },

  create: async (account: BankAccountCreate): Promise<BankAccount> => {
    const response = await api.post<BankAccount>('/api/users/me/bank-accounts', account);
    return response.data;
  },

  update: async (accountId: string, account: BankAccountUpdate): Promise<BankAccount> => {
    const response = await api.patch<BankAccount>(`/api/users/me/bank-accounts/${accountId}`, account);
    return response.data;
  },

  delete: async (accountId: string): Promise<void> => {
    await api.delete(`/api/users/me/bank-accounts/${accountId}`);
  },
};

// Letterhead Template API
export const letterheadApi = {
  getTemplates: async (): Promise<TemplateMetadata[]> => {
    const response = await api.get<TemplateListResponse>('/api/letterhead-templates');
    return response.data.templates;
  },
};

// Report API
export const reportApi = {
  getReports: async (): Promise<Report[]> => {
    const response = await api.get<Report[]>('/api/reports');
    return response.data;
  },

  getReport: async (id: number): Promise<Report> => {
    const response = await api.get<Report>(`/api/reports/${id}`);
    return response.data;
  },

  createReport: async (reportData: ReportCreate): Promise<Report> => {
    const response = await api.post<Report>('/api/reports', reportData);
    return response.data;
  },

  updateReport: async (id: number, reportData: Partial<ReportCreate>): Promise<Report> => {
    const response = await api.put<Report>(`/api/reports/${id}`, reportData);
    return response.data;
  },

  deleteReport: async (id: number): Promise<void> => {
    await api.delete(`/api/reports/${id}`);
  },

  generateReportDocx: async (id: number): Promise<void> => {
    const response = await api.post(
      `/api/reports/${id}/generate`,
      {},
      {
        responseType: 'blob',
      }
    );

    downloadFromResponse(
      response.data,
      response.headers['content-disposition'],
      'report.docx'
    );
  },

  duplicateReport: async (id: number): Promise<Report> => {
    const response = await api.post<Report>(`/api/reports/${id}/duplicate`);
    return response.data;
  },

  // Async document generation
  generateReportAsync: async (id: number): Promise<{ id: string }> => {
    const response = await api.post<{ id: string }>(`/api/reports/${id}/generate-async`);
    return response.data;
  },
};

// Job API for async operations
export interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  progress_message: string | null;
  error_message: string | null;
  download_ready: boolean;
  download_url: string | null;
  filename: string | null;
}

export interface Job {
  id: string;
  user_id: number;
  report_id: number | null;
  job_type: string;
  status: string;
  result_url: string | null;
  result_filename: string | null;
  error_message: string | null;
  progress_percent: number | null;
  progress_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export const jobApi = {
  getStatus: async (jobId: string): Promise<JobStatus> => {
    const response = await api.get<JobStatus>(`/api/jobs/${jobId}`);
    return response.data;
  },

  download: async (jobId: string): Promise<void> => {
    const response = await api.get(`/api/jobs/${jobId}/download`, {
      responseType: 'blob',
    });

    downloadFromResponse(
      response.data,
      response.headers['content-disposition'],
      'document.docx'
    );
  },

  listJobs: async (limit: number = 10, statusFilter?: string): Promise<Job[]> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }
    const response = await api.get<Job[]>(`/api/jobs?${params.toString()}`);
    return response.data;
  },
};

// Export the base API instance for direct use
export { api };

// Convenience exports for easier imports
export const createReport = reportApi.createReport;
export const generateReportDocx = reportApi.generateReportDocx;
export const getUserReports = reportApi.getReports;
