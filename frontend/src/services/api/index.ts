// Re-export axios instance + token helpers
export { api, setAuthToken, clearAuthToken, initializeCSRF, registerNavigate } from './client';

// Re-export all API namespaces
export { authApi } from './authApi';
export { bankAccountApi } from './bankAccountApi';
export { letterheadApi } from './letterheadApi';
export { reportApi } from './reportApi';
export { jobApi } from './jobApi';
export { vehicleApi } from './vehicleApi';
export { ocrApi } from './ocrApi';

// Re-export Job interfaces
export type { JobStatus, Job } from './jobApi';

// Re-export legacy standalone functions from reportApi
export {
  submitUserData,
  generateAndDownloadDocx,
  submitAndGenerateDocx,
  getAllUserData,
  getUserData,
  healthCheck,
} from './reportApi';

// Convenience exports for easier imports
import { reportApi } from './reportApi';
export const createReport = reportApi.createReport;
export const generateReportDocx = reportApi.generateReportDocx;
export const getUserReports = reportApi.getReports;
