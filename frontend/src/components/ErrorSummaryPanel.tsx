/**
 * Error Summary Panel Component
 * Displays validation errors in a user-friendly, accessible panel
 * Shows field names with error messages and allows clicking to navigate to fields
 */

import React, { useEffect, useRef } from 'react';
import { AlertCircle, X } from 'lucide-react';
import { ValidationErrorSummary } from '../utils/validationErrorTransformer';

interface ErrorSummaryPanelProps {
  errors: ValidationErrorSummary[];
  onDismiss: () => void;
  onErrorClick: (fieldName: string) => void;
  isVisible: boolean;
}

/**
 * ErrorSummaryPanel Component
 *
 * Features:
 * - Displays all validation errors in a collapsible panel
 * - Clickable errors that scroll to the corresponding field
 * - Dismissible with X button or Escape key
 * - Keyboard navigation support (Tab, Enter, Escape)
 * - Auto-focus on first error for accessibility
 * - Screen reader compatible with ARIA labels
 * - Smooth animations and hover effects
 *
 * @param errors - Array of validation errors to display
 * @param onDismiss - Callback when panel is dismissed
 * @param onErrorClick - Callback when an error is clicked (receives field name)
 * @param isVisible - Whether the panel should be visible
 */
export const ErrorSummaryPanel: React.FC<ErrorSummaryPanelProps> = ({
  errors,
  onDismiss,
  onErrorClick,
  isVisible,
}) => {
  const panelRef = useRef<HTMLDivElement>(null);
  const firstErrorRef = useRef<HTMLButtonElement>(null);

  // Auto-focus first error when panel becomes visible
  useEffect(() => {
    if (isVisible && firstErrorRef.current) {
      // Small delay to ensure panel is fully rendered
      setTimeout(() => {
        firstErrorRef.current?.focus();
      }, 100);
    }
  }, [isVisible]);

  // Handle keyboard events
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onDismiss();
    }
  };

  // Don't render if not visible or no errors
  if (!isVisible || errors.length === 0) return null;

  const errorCount = errors.length;
  const errorLabel = errorCount === 1 ? 'error' : 'errors';

  return (
    <div
      ref={panelRef}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      aria-label={`${errorCount} validation ${errorLabel}`}
      onKeyDown={handleKeyDown}
      className="mb-6 border-2 border-red-300 rounded-2xl bg-red-50/80 backdrop-blur-sm shadow-lg animate-slideDown overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-red-100 to-red-50 border-b border-red-200">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0" aria-hidden="true" />
          <h3 className="font-semibold text-red-900">
            Please fix the following {errorCount} {errorLabel}:
          </h3>
        </div>
        <button
          onClick={onDismiss}
          aria-label="Dismiss error panel"
          className="p-1 rounded-lg hover:bg-red-200/50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          <X className="h-5 w-5 text-red-600" aria-hidden="true" />
        </button>
      </div>

      {/* Error List */}
      <div className="p-4 max-h-[300px] overflow-y-auto">
        <ul className="space-y-2" role="list">
          {errors.map((error, index) => (
            <li key={`${error.path.join('-')}-${index}`}>
              <button
                ref={index === 0 ? firstErrorRef : null}
                onClick={() => onErrorClick(error.fieldName)}
                className="w-full text-left px-4 py-3 rounded-xl bg-white border border-red-200 hover:bg-red-50 hover:border-red-300 transition-all duration-200 transform hover:translate-x-1 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 group cursor-pointer"
                aria-label={`Navigate to ${error.fieldLabel}: ${error.errorMessage}`}
                type="button"
              >
                <div className="flex items-start gap-3">
                  <AlertCircle
                    className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0 group-hover:scale-110 transition-transform"
                    aria-hidden="true"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium text-red-900">
                      {error.fieldLabel}:
                    </span>
                    <span className="ml-2 text-red-700">
                      {error.errorMessage}
                    </span>
                  </div>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
