import type {
  UserData,
  UserDataResponse,
  Report,
  ReportCreate,
  PaginatedReportResponse,
  ReportFilters,
  AdjacentDateResponse,
} from '../../types';
import { api } from './client';
import { downloadFromResponse } from '../../utils/downloadHelper';

// ===== FIELD FILTERING FOR REPORT API =====
// These fields should only exist in their structured array formats (deeds array, etc.)
// not as individual root-level fields. The backend rejects extra fields.
const FIELDS_TO_FILTER_FROM_REPORT = [
  // Deed fields - should be in `deeds` array only
  'deed_type', 'deed_number', 'deed_date', 'notary_name', 'notary_location',
  // Certificate fields - transformed to deed format
  'certificate_number', 'certificate_date', 'certificate_notary_name', 'certificate_notary_district',
  // OCR staging field - frontend only, dispersed into building fields by the UI before submission
  'ocr_building_plan_data',
  // Advanced road mode field - not in backend model or Pydantic schema
  'access_road_segments',
  // Dead field with wrong name - backend field is `use_applicant_address_as_property`
  'use_property_address_as_applicant',
];

/**
 * Filter out extra fields that backend doesn't accept
 * These fields exist in form state but should only be sent in structured arrays
 */
const filterReportData = <T extends Record<string, any>>(data: T): Partial<T> => {
  const filtered = { ...data };
  for (const field of FIELDS_TO_FILTER_FROM_REPORT) {
    delete filtered[field];
  }
  return filtered;
};

export const reportApi = {
  getReports: async (
    page: number = 1,
    pageSize: number = 8,
    filters?: ReportFilters
  ): Promise<PaginatedReportResponse> => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());

    if (filters?.reference) {
      params.append('reference', filters.reference);
    }
    if (filters?.applicant_name) {
      params.append('applicant_name', filters.applicant_name);
    }
    if (filters?.village) {
      params.append('village', filters.village);
    }
    if (filters?.report_date) {
      params.append('report_date', filters.report_date);
    }

    const response = await api.get<PaginatedReportResponse>(`/api/reports?${params.toString()}`);
    return response.data;
  },

  getAdjacentReportDate: async (
    currentDate: string,
    direction: 'next' | 'previous'
  ): Promise<string | null> => {
    const response = await api.get<AdjacentDateResponse>(
      `/api/reports/adjacent-date?current_date=${currentDate}&direction=${direction}`
    );
    return response.data.adjacent_date;
  },

  getReport: async (id: number): Promise<Report> => {
    const response = await api.get<Report>(`/api/reports/${id}`);
    return response.data;
  },

  createReport: async (reportData: ReportCreate): Promise<Report> => {
    // Filter out extra fields that should only exist in structured arrays
    const filteredData = filterReportData(reportData);
    const response = await api.post<Report>('/api/reports', filteredData);
    return response.data;
  },

  updateReport: async (id: number, reportData: Partial<ReportCreate>): Promise<Report> => {
    // Strip out server-generated/read-only fields that backend doesn't accept
    const {
      id: _id,
      user_id,
      created_at,
      updated_at,
      total_valuation_amount,
      ...cleanedData
    } = reportData as any;

    // Filter out extra fields that should only exist in structured arrays
    const filteredData = filterReportData(cleanedData);

    const response = await api.put<Report>(`/api/reports/${id}`, filteredData);
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

// Legacy functions (kept for backward compatibility)
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
