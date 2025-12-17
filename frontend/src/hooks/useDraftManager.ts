import { useState, useEffect } from 'react';
import { UseFormReturn } from 'react-hook-form';
import { reportApi } from '../services/api';
import toast from 'react-hot-toast';

interface DraftManagerConfig {
  reportId?: number;
  isEditMode: boolean;
  formMethods: {
    watch: UseFormReturn<any>['watch'];
    getValues: UseFormReturn<any>['getValues'];
    setValue: UseFormReturn<any>['setValue'];
  };
}

interface DraftManagerReturn {
  isDirty: boolean;
  isSaving: boolean;
  lastSaved: Date | null;
  saveDraft: () => Promise<any>;
  setIsDirty: (dirty: boolean) => void;
}

/**
 * Hook for managing draft state and operations
 *
 * Features:
 * - Tracks when form has unsaved changes (dirty state)
 * - Saves drafts to backend (create or update)
 * - Provides loading state and last saved timestamp
 * - Handles both new reports and editing existing reports
 */
export const useDraftManager = (config: DraftManagerConfig): DraftManagerReturn => {
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Auto-track form changes to set dirty flag
  useEffect(() => {
    const subscription = config.formMethods.watch(() => {
      setIsDirty(true);
    });

    return () => subscription.unsubscribe();
  }, [config.formMethods]);

  /**
   * Save draft to backend with retry logic
   */
  const saveDraft = async (): Promise<any> => {
    setIsSaving(true);

    try {
      const formData = config.formMethods.getValues();
      const reportData = {
        ...formData,
        status: 'draft',
        report_type: 'residential_property'
      };

      console.log('[useDraftManager] Saving draft...', {
        isEditMode: config.isEditMode,
        reportId: config.reportId
      });

      let savedReport;

      if (config.isEditMode && config.reportId) {
        // Update existing report
        savedReport = await reportApi.updateReport(config.reportId, reportData);
        console.log('[useDraftManager] Updated existing report:', savedReport.id);
      } else {
        // Create new report
        savedReport = await reportApi.createReport(reportData);
        console.log('[useDraftManager] Created new draft report:', savedReport.id);
      }

      // Update state after successful save
      setIsDirty(false);
      setLastSaved(new Date());

      return savedReport;
    } catch (error: any) {
      console.error('[useDraftManager] Failed to save draft:', error);
      throw error;
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Save draft with retry logic for network failures
   */
  const saveDraftWithRetry = async (maxRetries = 3): Promise<any> => {
    let lastError: any;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const result = await saveDraft();

        if (attempt > 1) {
          toast.success('Draft saved after retry', { duration: 3000 });
        }

        return result;
      } catch (error: any) {
        lastError = error;

        console.warn(`[useDraftManager] Save attempt ${attempt} failed:`, error);

        if (attempt < maxRetries) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff: 2s, 4s, 8s
          await new Promise(resolve => setTimeout(resolve, delay));

          toast(`Retrying save (attempt ${attempt + 1})...`, {
            icon: '⏳',
            duration: 2000
          });
        }
      }
    }

    // All retries failed
    throw lastError;
  };

  return {
    isDirty,
    isSaving,
    lastSaved,
    saveDraft: saveDraftWithRetry,
    setIsDirty
  };
};
