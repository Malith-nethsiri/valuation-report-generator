import { api } from './client';

export const ocrApi = {
  // Extract data from documents (supports vehicle_book type)
  extractData: async (files: File[], documentType?: string): Promise<any> => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    if (documentType) {
      formData.append('document_type', documentType);
    }

    const response = await api.post('/api/ocr/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
