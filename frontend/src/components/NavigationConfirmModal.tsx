import React from 'react';
import { AlertCircle, Save, Trash2 } from 'lucide-react';

interface NavigationConfirmModalProps {
  isOpen: boolean;
  onSaveAndExit: () => Promise<void>;
  onDiscardAndExit: () => void;
  onCancel: () => void;
  isSaving: boolean;
}

/**
 * Modal component for confirming navigation when form has unsaved changes
 *
 * Provides 3 options:
 * 1. Save as Draft & Exit - Saves current form data as draft and navigates away
 * 2. Discard & Exit - Discards unsaved changes and navigates away
 * 3. Continue Editing - Cancels navigation and returns to form
 *
 * Matches the existing design system with rounded corners, gradients, and backdrop blur
 */
export const NavigationConfirmModal: React.FC<NavigationConfirmModalProps> = ({
  isOpen,
  onSaveAndExit,
  onDiscardAndExit,
  onCancel,
  isSaving
}) => {
  if (!isOpen) return null;

  const handleSaveAndExit = async () => {
    try {
      await onSaveAndExit();
    } catch (error) {
      console.error('[NavigationConfirmModal] Failed to save:', error);
      // Error handling is done in the parent component
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside modal
      >
        {/* Icon and Header */}
        <div className="mb-6">
          <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="h-6 w-6 text-orange-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            Unsaved Changes
          </h2>
          <p className="text-gray-600 text-center">
            You have unsaved changes. What would you like to do?
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-3">
          {/* Save as Draft & Exit */}
          <button
            onClick={handleSaveAndExit}
            disabled={isSaving}
            className="w-full flex items-center justify-center px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-semibold rounded-2xl shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-5 w-5 mr-2" />
                Save as Draft & Exit
              </>
            )}
          </button>

          {/* Discard & Exit */}
          <button
            onClick={onDiscardAndExit}
            disabled={isSaving}
            className="w-full flex items-center justify-center px-6 py-3 border-2 border-red-300 text-red-600 hover:bg-red-50 font-semibold rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <Trash2 className="h-5 w-5 mr-2" />
            Discard & Exit
          </button>

          {/* Continue Editing */}
          <button
            onClick={onCancel}
            disabled={isSaving}
            className="w-full px-6 py-3 text-gray-600 hover:bg-gray-50 font-medium rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Continue Editing
          </button>
        </div>
      </div>
    </div>
  );
};

export default NavigationConfirmModal;
