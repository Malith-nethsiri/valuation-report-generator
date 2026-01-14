import React from 'react';
import { Save, CheckCircle2, ArrowRight } from 'lucide-react';

interface SaveProgressModalProps {
  isOpen: boolean;
  isSaving: boolean;
  saveError: string | null;
  onContinue: () => void;
  onExit: () => void;
}

const SaveProgressModal: React.FC<SaveProgressModalProps> = ({
  isOpen,
  isSaving,
  saveError,
  onContinue,
  onExit,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full">
        {/* Header with icon */}
        <div className="mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-cyan-100 rounded-full flex items-center justify-center mx-auto mb-4">
            {isSaving ? (
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent" />
            ) : (
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            )}
          </div>

          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            {isSaving ? 'Saving Draft' : 'Draft Saved'}
          </h2>

          <p className="text-gray-600 text-center">
            {isSaving
              ? 'Please wait while we save your progress...'
              : 'Your draft has been saved successfully. What would you like to do?'
            }
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex flex-col gap-3">
          {/* Save and Continue - Primary */}
          <button
            onClick={onContinue}
            disabled={isSaving}
            className="w-full flex items-center justify-center px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-semibold rounded-2xl shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none"
          >
            <ArrowRight className="h-5 w-5 mr-2" />
            Save and Continue
          </button>

          {/* Save & Exit - Secondary */}
          <button
            onClick={onExit}
            disabled={isSaving}
            className="w-full flex items-center justify-center px-6 py-3 border-2 border-gray-300 text-gray-700 hover:bg-gray-50 font-semibold rounded-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none"
          >
            <Save className="h-5 w-5 mr-2" />
            Save & Exit
          </button>
        </div>
      </div>
    </div>
  );
};

export default SaveProgressModal;
