import { api } from './client';
import { downloadFromResponse } from '../../utils/downloadHelper';

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
