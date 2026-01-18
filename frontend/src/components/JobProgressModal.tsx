/**
 * Modal component for displaying job progress during async document generation.
 *
 * Features:
 * - Progress bar with percentage
 * - Status messages
 * - Error display with retry option
 * - Download button when complete
 */

import React from 'react';
import { X, FileText, Download, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import type { JobStatus } from '../hooks/useJobPolling';

interface JobProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  status: JobStatus | null;
  isPolling: boolean;
  error: string | null;
  onDownload: () => Promise<void>;
  onRetry?: () => void;
}

export function JobProgressModal({
  isOpen,
  onClose,
  status,
  isPolling,
  error,
  onDownload,
  onRetry,
}: JobProgressModalProps) {
  if (!isOpen) return null;

  const progressPercent = status?.progress_percent || 0;
  const progressMessage = status?.progress_message || 'Preparing...';
  const isCompleted = status?.status === 'completed';
  const isFailed = status?.status === 'failed' || !!error;
  const isProcessing = status?.status === 'processing' || status?.status === 'pending';

  const handleDownload = async () => {
    try {
      await onDownload();
      // Close modal after successful download
      setTimeout(onClose, 500);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={isProcessing ? undefined : onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
        {/* Close button (hidden during processing) */}
        {!isProcessing && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        )}

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className={`p-2 rounded-full ${
            isFailed ? 'bg-red-100' :
            isCompleted ? 'bg-green-100' :
            'bg-blue-100'
          }`}>
            {isFailed ? (
              <AlertCircle className="h-6 w-6 text-red-600" />
            ) : isCompleted ? (
              <CheckCircle className="h-6 w-6 text-green-600" />
            ) : (
              <FileText className="h-6 w-6 text-blue-600" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {isFailed ? 'Generation Failed' :
               isCompleted ? 'Document Ready' :
               'Generating Document'}
            </h3>
            <p className="text-sm text-gray-500">
              {isFailed ? 'An error occurred' :
               isCompleted ? 'Your document is ready for download' :
               'Please wait while we generate your document'}
            </p>
          </div>
        </div>

        {/* Progress section (for processing state) */}
        {isProcessing && (
          <div className="mb-6">
            {/* Progress bar */}
            <div className="mb-2">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">{progressMessage}</span>
                <span className="text-gray-900 font-medium">{progressPercent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            {/* Loading indicator */}
            <div className="flex items-center justify-center gap-2 text-gray-500 mt-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Processing...</span>
            </div>
          </div>
        )}

        {/* Error section */}
        {isFailed && (
          <div className="mb-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-700">
                {error || status?.error_message || 'An unknown error occurred'}
              </p>
            </div>
          </div>
        )}

        {/* Success section */}
        {isCompleted && status?.filename && (
          <div className="mb-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-700 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                {status.filename}
              </p>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          {isProcessing && (
            <button
              onClick={onClose}
              disabled
              className="flex-1 px-4 py-2 text-gray-400 bg-gray-100 rounded-lg cursor-not-allowed"
            >
              Please wait...
            </button>
          )}

          {isCompleted && (
            <>
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Close
              </button>
              <button
                onClick={handleDownload}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <Download className="h-4 w-4" />
                Download
              </button>
            </>
          )}

          {isFailed && (
            <>
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Close
              </button>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="flex-1 px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                >
                  Try Again
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default JobProgressModal;
