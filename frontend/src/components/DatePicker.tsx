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

// DatePicker uses native HTML5 date input for better UX and cross-browser support
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
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      onBlur={onBlur}
      className={className}
      disabled={disabled}
    />
  );
};
