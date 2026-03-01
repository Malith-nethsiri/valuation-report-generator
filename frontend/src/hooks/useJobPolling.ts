/**
 * Hook for polling job status during async document generation.
 *
 * Features:
 * - Poll every 2s initially, exponential backoff to 5s
 * - Max 60 attempts (2 minutes)
 * - Auto-trigger download on completion
 * - Progress tracking
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import { downloadBlobFile, DOCX_MIME_TYPE } from '../utils/downloadHelper';
import type { JobStatus } from '../types/misc';

export type { JobStatus };

interface UseJobPollingOptions {
  onComplete?: (job: JobStatus) => void;
  onError?: (error: string) => void;
  autoDownload?: boolean;
  maxAttempts?: number;
  initialInterval?: number;
  maxInterval?: number;
}

interface UseJobPollingReturn {
  startPolling: (jobId: string) => void;
  stopPolling: () => void;
  downloadResult: () => Promise<void>;
  status: JobStatus | null;
  isPolling: boolean;
  error: string | null;
  attempts: number;
}

const DEFAULT_OPTIONS: Required<UseJobPollingOptions> = {
  onComplete: () => {},
  onError: () => {},
  autoDownload: true,
  maxAttempts: 60,
  initialInterval: 2000,
  maxInterval: 5000,
};

export function useJobPolling(options: UseJobPollingOptions = {}): UseJobPollingReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options };

  const [status, setStatus] = useState<JobStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);

  const jobIdRef = useRef<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef(opts.initialInterval);

  const stopPolling = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsPolling(false);
    jobIdRef.current = null;
    intervalRef.current = opts.initialInterval;
  }, [opts.initialInterval]);

  const downloadResult = useCallback(async () => {
    if (!status?.download_url) {
      throw new Error('No download URL available');
    }

    try {
      const response = await api.get(status.download_url, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: DOCX_MIME_TYPE });
      downloadBlobFile(blob, status.filename || 'document.docx');
    } catch (err) {
      console.error('Download failed:', err);
      throw new Error('Failed to download file');
    }
  }, [status]);

  const pollJobStatus = useCallback(async () => {
    if (!jobIdRef.current) return;

    try {
      const response = await api.get<JobStatus>(`/api/jobs/${jobIdRef.current}`);
      const jobStatus = response.data;

      setStatus(jobStatus);
      setAttempts((prev) => prev + 1);

      // Check terminal states
      if (jobStatus.status === 'completed') {
        stopPolling();
        opts.onComplete(jobStatus);

        // Auto-download if enabled
        if (opts.autoDownload && jobStatus.download_ready) {
          try {
            await downloadResult();
          } catch (err) {
            console.error('Auto-download failed:', err);
          }
        }
        return;
      }

      if (jobStatus.status === 'failed') {
        stopPolling();
        const errorMsg = jobStatus.error_message || 'Job failed';
        setError(errorMsg);
        opts.onError(errorMsg);
        return;
      }

      // Check max attempts
      if (attempts >= opts.maxAttempts) {
        stopPolling();
        const errorMsg = 'Job timed out - max polling attempts reached';
        setError(errorMsg);
        opts.onError(errorMsg);
        return;
      }

      // Calculate next interval with exponential backoff
      const nextInterval = Math.min(
        intervalRef.current * 1.2,
        opts.maxInterval
      );
      intervalRef.current = nextInterval;

      // Schedule next poll
      timeoutRef.current = setTimeout(pollJobStatus, nextInterval);
    } catch (err: any) {
      console.error('Failed to poll job status:', err);

      // Don't stop on transient errors, continue polling
      if (attempts < opts.maxAttempts) {
        timeoutRef.current = setTimeout(pollJobStatus, intervalRef.current);
      } else {
        stopPolling();
        const errorMsg = err.message || 'Failed to check job status';
        setError(errorMsg);
        opts.onError(errorMsg);
      }
    }
  }, [attempts, downloadResult, opts, stopPolling]);

  const startPolling = useCallback((jobId: string) => {
    // Reset state
    stopPolling();
    setStatus(null);
    setError(null);
    setAttempts(0);

    // Start polling
    jobIdRef.current = jobId;
    setIsPolling(true);
    intervalRef.current = opts.initialInterval;

    // Initial poll immediately
    pollJobStatus();
  }, [opts.initialInterval, pollJobStatus, stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    startPolling,
    stopPolling,
    downloadResult,
    status,
    isPolling,
    error,
    attempts,
  };
}

export default useJobPolling;
