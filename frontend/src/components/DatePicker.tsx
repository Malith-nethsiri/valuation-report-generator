import React from 'react';
import { Input } from './Input';

interface DatePickerProps {
  id?: string;
  value?: string;
  onChange: (date: string) => void;
  onBlur?: () => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

/**
 * Convert a DD-MM-YYYY string (the format stored in the form) to YYYY-MM-DD
 * (the format required by <input type="date"> for its `value` attribute).
 */
function toInputFormat(stored: string): string {
  if (!stored) return '';
  // DD-MM-YYYY → YYYY-MM-DD
  const parts = stored.split('-');
  if (parts.length === 3 && parts[2].length === 4) {
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return stored; // Already in another format — pass through unchanged
}

/**
 * Convert a YYYY-MM-DD string (emitted by <input type="date">) to DD-MM-YYYY
 * (the format the validation schemas and backend expect).
 */
function fromInputFormat(inputVal: string): string {
  if (!inputVal) return '';
  // YYYY-MM-DD → DD-MM-YYYY
  const parts = inputVal.split('-');
  if (parts.length === 3 && parts[0].length === 4) {
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return inputVal; // Already in another format — pass through unchanged
}

// DatePicker uses native HTML5 date input for better UX and cross-browser support.
// Internally converts between the native YYYY-MM-DD format and the DD-MM-YYYY
// format used by validation schemas and the backend.
export const DatePicker: React.FC<DatePickerProps> = ({
  id,
  value,
  onChange,
  onBlur,
  className = '',
  disabled = false,
}) => {
  return (
    <Input
      type="date"
      id={id}
      value={toInputFormat(value || '')}
      onChange={(e) => onChange(fromInputFormat(e.target.value))}
      onBlur={onBlur}
      className={className}
      disabled={disabled}
    />
  );
};
