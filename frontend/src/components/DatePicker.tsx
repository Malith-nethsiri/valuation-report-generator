import React, { forwardRef } from 'react';
import ReactDatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import '../styles/datepicker.css';
import { Calendar } from 'lucide-react';
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

// Custom input component that integrates with our Input component
const CustomInput = forwardRef<HTMLInputElement, any>(
  ({ value, onClick, onChange, onBlur, placeholder, className, id, disabled }, ref) => (
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none z-10">
        <Calendar className="h-5 w-5 text-gray-400" />
      </div>
      <Input
        id={id}
        ref={ref}
        type="text"
        value={value}
        onClick={onClick}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        className={`pl-12 cursor-pointer ${className}`}
        readOnly
        disabled={disabled}
      />
    </div>
  )
);

CustomInput.displayName = 'CustomInput';

export const DatePicker: React.FC<DatePickerProps> = ({
  id,
  value,
  onChange,
  onBlur,
  placeholder = 'Select date',
  className = '',
  disabled = false,
}) => {
  // Parse DD-MM-YYYY format to Date object
  const parseDate = (dateString: string): Date | null => {
    if (!dateString) return null;
    const parts = dateString.split('-');
    if (parts.length !== 3) return null;
    const day = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1; // Month is 0-indexed
    const year = parseInt(parts[2], 10);
    const date = new Date(year, month, day);
    // Validate the date
    if (isNaN(date.getTime())) return null;
    return date;
  };

  // Format Date object to DD-MM-YYYY
  const formatDate = (date: Date): string => {
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}-${month}-${year}`;
  };

  const selectedDate = value ? parseDate(value) : null;

  const handleChange = (date: Date | null) => {
    if (date) {
      onChange(formatDate(date));
    } else {
      onChange('');
    }
  };

  return (
    <ReactDatePicker
      selected={selectedDate}
      onChange={handleChange}
      onBlur={onBlur}
      dateFormat="dd-MM-yyyy"
      customInput={
        <CustomInput
          id={id}
          placeholder={placeholder}
          className={className}
          disabled={disabled}
        />
      }
      showMonthDropdown
      showYearDropdown
      dropdownMode="select"
      disabled={disabled}
      placeholderText={placeholder}
      // Additional customization
      className="w-full"
      wrapperClassName="w-full"
      calendarClassName="shadow-xl border-2 border-gray-200"
    />
  );
};
