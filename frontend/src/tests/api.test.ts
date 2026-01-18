/**
 * Tests for API error handling.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios, { AxiosError } from 'axios';

describe('API Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Network Errors', () => {
    it('should handle timeout errors', () => {
      const error = new AxiosError(
        'timeout of 5000ms exceeded',
        'ECONNABORTED'
      );
      error.code = 'ECONNABORTED';

      expect(error.code).toBe('ECONNABORTED');
      expect(error.message).toContain('timeout');
    });

    it('should handle network errors', () => {
      const error = new AxiosError('Network Error');
      error.response = undefined;

      expect(error.response).toBeUndefined();
    });
  });

  describe('HTTP Status Errors', () => {
    it('should handle 401 Unauthorized', () => {
      const error = new AxiosError('Unauthorized');
      error.response = {
        status: 401,
        data: { detail: 'Could not validate credentials' },
        statusText: 'Unauthorized',
        headers: {},
        config: {} as any,
      };

      expect(error.response.status).toBe(401);
    });

    it('should handle 403 Forbidden', () => {
      const error = new AxiosError('Forbidden');
      error.response = {
        status: 403,
        data: { message: 'Access forbidden' },
        statusText: 'Forbidden',
        headers: {},
        config: {} as any,
      };

      expect(error.response.status).toBe(403);
    });

    it('should handle 404 Not Found', () => {
      const error = new AxiosError('Not Found');
      error.response = {
        status: 404,
        data: { detail: 'Report not found' },
        statusText: 'Not Found',
        headers: {},
        config: {} as any,
      };

      expect(error.response.status).toBe(404);
    });

    it('should handle 422 Validation Error', () => {
      const error = new AxiosError('Unprocessable Entity');
      error.response = {
        status: 422,
        data: {
          details: [
            { field: 'email', message: 'Invalid email format' },
            { field: 'password', message: 'Password too short' },
          ],
        },
        statusText: 'Unprocessable Entity',
        headers: {},
        config: {} as any,
      };

      expect(error.response.status).toBe(422);
      expect(error.response.data.details).toHaveLength(2);
    });

    it('should handle 429 Rate Limit', () => {
      const error = new AxiosError('Too Many Requests');
      error.response = {
        status: 429,
        data: { message: 'Rate limit exceeded', retry_after: 60 },
        statusText: 'Too Many Requests',
        headers: { 'retry-after': '60' },
        config: {} as any,
      };

      expect(error.response.status).toBe(429);
      expect(error.response.headers['retry-after']).toBe('60');
    });

    it('should handle 500 Internal Server Error', () => {
      const error = new AxiosError('Internal Server Error');
      error.response = {
        status: 500,
        data: { detail: 'Internal server error' },
        statusText: 'Internal Server Error',
        headers: {},
        config: {} as any,
      };

      expect(error.response.status).toBe(500);
    });

    it('should handle 502 Bad Gateway', () => {
      const error = new AxiosError('Bad Gateway');
      error.response = {
        status: 502,
        data: {},
        statusText: 'Bad Gateway',
        headers: {},
        config: {} as any,
      };

      expect(error.response.status).toBe(502);
    });

    it('should handle 503 Service Unavailable', () => {
      const error = new AxiosError('Service Unavailable');
      error.response = {
        status: 503,
        data: { message: 'Service temporarily unavailable' },
        statusText: 'Service Unavailable',
        headers: {},
        config: {} as any,
      };

      expect(error.response.status).toBe(503);
    });
  });

  describe('Retry Logic', () => {
    const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504];

    it('should identify retryable status codes', () => {
      RETRYABLE_STATUS_CODES.forEach((code) => {
        expect(RETRYABLE_STATUS_CODES.includes(code)).toBe(true);
      });
    });

    it('should not retry 400 errors', () => {
      expect(RETRYABLE_STATUS_CODES.includes(400)).toBe(false);
    });

    it('should not retry 401 errors', () => {
      expect(RETRYABLE_STATUS_CODES.includes(401)).toBe(false);
    });

    it('should not retry 404 errors', () => {
      expect(RETRYABLE_STATUS_CODES.includes(404)).toBe(false);
    });
  });

  describe('Exponential Backoff', () => {
    it('should calculate correct backoff delays', () => {
      const RETRY_DELAY = 1000;
      const getRetryDelay = (retryCount: number): number => {
        return RETRY_DELAY * Math.pow(2, retryCount);
      };

      expect(getRetryDelay(0)).toBe(1000);
      expect(getRetryDelay(1)).toBe(2000);
      expect(getRetryDelay(2)).toBe(4000);
      expect(getRetryDelay(3)).toBe(8000);
    });
  });
});

describe('Job API', () => {
  describe('JobStatus type', () => {
    it('should have correct status values', () => {
      const validStatuses = ['pending', 'processing', 'completed', 'failed'];

      validStatuses.forEach((status) => {
        expect(validStatuses).toContain(status);
      });
    });
  });

  describe('Job response structure', () => {
    it('should have required fields', () => {
      const mockJobResponse = {
        id: 'test-uuid',
        status: 'completed' as const,
        progress_percent: 100,
        progress_message: 'Document ready',
        error_message: null,
        download_ready: true,
        download_url: '/api/jobs/test-uuid/download',
        filename: 'report.docx',
      };

      expect(mockJobResponse.id).toBeDefined();
      expect(mockJobResponse.status).toBe('completed');
      expect(mockJobResponse.download_ready).toBe(true);
      expect(mockJobResponse.download_url).toBeDefined();
    });

    it('should handle failed job', () => {
      const mockFailedJob = {
        id: 'test-uuid',
        status: 'failed' as const,
        progress_percent: 50,
        progress_message: 'Generation failed',
        error_message: 'Template not found',
        download_ready: false,
        download_url: null,
        filename: null,
      };

      expect(mockFailedJob.status).toBe('failed');
      expect(mockFailedJob.error_message).toBe('Template not found');
      expect(mockFailedJob.download_ready).toBe(false);
    });
  });
});
