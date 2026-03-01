/**
 * Miscellaneous types: ApiError, HealthResponse, AdjacentDateResponse, JobStatus, Job.
 */

export interface ApiError {
  detail: string;
}

// ===== JOB TYPES =====

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

export interface HealthResponse {
  status: string;
  message: string;
}

// Letterhead Template Types
export interface AdjacentDateResponse {
  adjacent_date: string | null;
}

// ===== VEHICLE TYPES =====
