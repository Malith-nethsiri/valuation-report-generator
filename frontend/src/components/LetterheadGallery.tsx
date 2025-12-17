import React, { useEffect, useState } from 'react';
import { LetterheadTemplatePreview } from './LetterheadTemplatePreview';
import { letterheadApi } from '../services/api';
import type { TemplateMetadata } from '../types';

interface LetterheadGalleryProps {
  selectedTemplate: string;
  onTemplateSelect: (templateId: string) => void;
  userData: any;
}

export const LetterheadGallery: React.FC<LetterheadGalleryProps> = ({
  selectedTemplate,
  onTemplateSelect,
  userData,
}) => {
  const [templates, setTemplates] = useState<TemplateMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoading(true);
        const templateList = await letterheadApi.getTemplates();
        setTemplates(templateList);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch templates:', err);
        setError('Failed to load templates. Using default template.');
        // Fallback to classic template
        setTemplates([
          {
            template_id: 'classic',
            name: 'Classic Professional',
            description: 'Traditional centered layout with dual borders',
            category: 'traditional',
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading templates...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-yellow-800 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Gallery grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => (
          <LetterheadTemplatePreview
            key={template.template_id}
            templateId={template.template_id}
            templateName={template.name}
            templateDescription={template.description}
            userData={userData}
            isSelected={selectedTemplate === template.template_id}
            onClick={() => onTemplateSelect(template.template_id)}
          />
        ))}
      </div>

      {/* Selection info */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Selected:</strong>{' '}
          {templates.find((t) => t.template_id === selectedTemplate)?.name || 'Classic Professional'}
        </p>
        <p className="text-xs text-blue-600 mt-1">
          This template will be used for all your reports. You can change it anytime.
        </p>
      </div>
    </div>
  );
};
