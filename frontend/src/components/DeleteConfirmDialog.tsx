import React from 'react';
import { AlertCircle, X } from 'lucide-react';

interface DeleteConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  reportReference?: string;
  title?: string;
  description?: string;
  confirmButtonText?: string;
}

export const DeleteConfirmDialog: React.FC<DeleteConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  reportReference,
  title = 'Delete Report',
  description = 'Are you sure you want to delete this report? This action cannot be undone.',
  confirmButtonText = 'Delete',
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md animate-in fade-in zoom-in-95 duration-200">
        <div className="bg-white rounded-2xl shadow-2xl border border-gray-200/50">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-100">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-red-50 rounded-xl">
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-xl transition-colors duration-200"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            <p className="text-gray-600 leading-relaxed">{description}</p>
            {reportReference && (
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                <p className="text-sm text-gray-500 mb-1">Report Reference</p>
                <p className="text-base font-semibold text-gray-900">{reportReference}</p>
              </div>
            )}
            <div className="p-4 bg-red-50 rounded-xl border border-red-100">
              <p className="text-sm text-red-800 font-medium">
                ⚠️ This action cannot be undone
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-100 bg-gray-50/50 rounded-b-2xl">
            <button
              onClick={onClose}
              className="px-5 py-2.5 text-gray-700 font-medium bg-white hover:bg-gray-50 rounded-xl border border-gray-200 transition-all duration-200 shadow-sm hover:shadow"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="px-5 py-2.5 text-white font-medium bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {confirmButtonText}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};
