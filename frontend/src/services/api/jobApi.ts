import { api } from './client';
import { downloadFromResponse } from '../../utils/downloadHelper';
import type { JobStatus, Job } from '../../types/misc';

export type { JobStatus, Job };

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
