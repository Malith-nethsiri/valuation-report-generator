import React from 'react';
import { AlertCircle } from 'lucide-react';

interface FormFieldErrorProps {
  message: string | undefined;
  fieldId?: string;
}

export const FormFieldError: React.FC<FormFieldErrorProps> = ({ message, fieldId }) => {
  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="polite"
      id={fieldId ? `${fieldId}-error` : undefined}
      className="flex items-start gap-2 mt-1.5 text-red-600 text-sm animate-fadeIn"
    >
      <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
      <span>{message}</span>
    </div>
  );
};
