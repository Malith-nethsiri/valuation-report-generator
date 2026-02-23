import type { TemplateMetadata, TemplateListResponse } from '../../types';
import { api } from './client';

export const letterheadApi = {
  getTemplates: async (): Promise<TemplateMetadata[]> => {
    const response = await api.get<TemplateListResponse>('/api/letterhead-templates');
    return response.data.templates;
  },
};
