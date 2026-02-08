import { useState, useEffect, useRef } from 'react';
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
  debounceMs?: number; // Optional debounce time in milliseconds (default: 300)
}

interface DraftManagerReturn {
  isDirty: boolean;
  isSaving: boolean;
  lastSaved: Date | null;
  saveDraft: () => Promise<any>;
  setIsDirty: (dirty: boolean) => void;
  canSave: boolean; // Indicates if save operation can be triggered (not already in progress)
}

/**
 * Hook for managing draft state and operations
 *
 * Features:
 * - Tracks when form has unsaved changes (dirty state)
 * - Saves drafts to backend (create or update)
 * - Provides loading state and last saved timestamp
 * - Handles both new reports and editing existing reports
 * - Prevents duplicate saves via ref-based flag and debouncing
 */
export const useDraftManager = (config: DraftManagerConfig): DraftManagerReturn => {
  const { debounceMs = 300 } = config;

  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  // Duplicate prevention: Track if save is in progress using ref (synchronous)
  const saveInProgressRef = useRef(false);

  // Debouncing: Track last save time to prevent rapid successive saves
  const lastSaveTimeRef = useRef<number>(0);

  // Auto-track form changes to set dirty flag
  useEffect(() => {
    const subscription = config.formMethods.watch(() => {
      setIsDirty(true);
    });

    return () => subscription.unsubscribe();
  }, [config.formMethods]);

  /**
   * Save draft to backend with duplicate prevention and debouncing
   */
  const saveDraft = async (): Promise<any> => {
    // DUPLICATE PREVENTION: Check if save already in progress
    if (saveInProgressRef.current) {
      console.log('[useDraftManager] Save already in progress, ignoring duplicate request');
      return;
    }

    // DEBOUNCING: Prevent rapid successive saves
    const now = Date.now();
    if (now - lastSaveTimeRef.current < debounceMs) {
      console.log('[useDraftManager] Save request too soon after previous save, debouncing');
      return;
    }

    // Set flags immediately (synchronous) before any async operations
    saveInProgressRef.current = true;
    lastSaveTimeRef.current = now;
    setIsSaving(true);

    try {
      const formData = config.formMethods.getValues();

      // Fields to filter out - these should only exist in the `deeds` array, not at root level
      const fieldsToRemove = [
        'deed_type', 'deed_number', 'deed_date', 'notary_name', 'notary_location',
        'certificate_number', 'certificate_date', 'certificate_notary_name', 'certificate_notary_district',
      ];

      // Filter extra deed fields before saving draft
      const filteredFormData = { ...formData };
      for (const field of fieldsToRemove) {
        delete (filteredFormData as any)[field];
      }

      const reportData = {
        ...filteredFormData,
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
      saveInProgressRef.current = false; // Clear the flag
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
    setIsDirty,
    canSave: !saveInProgressRef.current // Indicates if save can be triggered
  };
};
