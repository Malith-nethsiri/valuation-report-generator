import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { X } from 'lucide-react';
import { Label } from './Label';

interface MultiSelectWithCustomInputProps {
  label: string;
  value: string[];  // Array of selected values
  onChange: (values: string[]) => void;
  predefinedOptions: Array<{ value: string; label: string }>;
  placeholder?: string;
  maxSelections?: number;
  maxCharacters?: number;
  disabled?: boolean;
  helperText?: string;
}

export const MultiSelectWithCustomInput: React.FC<MultiSelectWithCustomInputProps> = ({
  label,
  value = [],
  onChange,
  predefinedOptions,
  placeholder = "Type and press Enter, or select from dropdown",
  maxSelections = 5,
  maxCharacters = 50,
  disabled = false,
  helperText
}) => {
  // Ensure value is always an array (handle legacy string values)
  const normalizedValue = Array.isArray(value) ? value : (value ? [value] : []);

  const [inputValue, setInputValue] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Normalize to title case
  const toTitleCase = (str: string): string => {
    return str
      .toLowerCase()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Add value (from dropdown or custom input)
  const addValue = (newValue: string) => {
    const normalized = toTitleCase(newValue.trim());

    // Clear previous error
    setError(null);

    // Validation
    if (!normalized) {
      return;
    }

    if (normalized.length > maxCharacters) {
      setError(`Maximum ${maxCharacters} characters allowed`);
      return;
    }

    if (normalizedValue.length >= maxSelections) {
      setError(`Maximum ${maxSelections} selections allowed`);
      return;
    }

    // Check for duplicates (case-insensitive)
    const isDuplicate = normalizedValue.some(v => v.toLowerCase() === normalized.toLowerCase());
    if (isDuplicate) {
      setError('This value is already selected');
      return;
    }

    // Add to array
    onChange([...normalizedValue, normalized]);
    setInputValue('');
    setShowDropdown(false);
  };

  // Remove value (tag)
  const removeValue = (indexToRemove: number) => {
    onChange(normalizedValue.filter((_, index) => index !== indexToRemove));
    setError(null);
  };

  // Handle keyboard input
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (inputValue.trim()) {
        addValue(inputValue);
      }
    }
  };

  // Filter dropdown options (exclude already selected)
  const availableOptions = predefinedOptions.filter(
    opt => !normalizedValue.some(v => v.toLowerCase() === opt.value.toLowerCase())
  );

  return (
    <div className="space-y-2">
      <Label>{label}</Label>

      {/* Selected Tags */}
      {normalizedValue.length > 0 && (
        <div className="flex flex-wrap gap-2 p-2 bg-gray-50 rounded-lg">
          {normalizedValue.map((item, index) => (
            <div
              key={index}
              className="inline-flex items-center gap-1 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-sm"
            >
              <span>{item}</span>
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeValue(index)}
                  className="hover:bg-emerald-200 rounded-full p-0.5 transition-colors"
                  aria-label={`Remove ${item}`}
                >
                  <X size={14} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Input + Dropdown Container */}
      {!disabled && normalizedValue.length < maxSelections && (
        <div className="relative" ref={dropdownRef}>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              setError(null);
            }}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowDropdown(true)}
            placeholder={placeholder}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:outline-none"
          />

          {/* Dropdown Options */}
          {showDropdown && availableOptions.length > 0 && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {availableOptions.map((option, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => {
                    addValue(option.value);
                    inputRef.current?.focus();
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-emerald-50 text-sm transition-colors"
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <p className="text-xs text-red-600">{error}</p>
      )}

      {/* Helper Text */}
      {helperText && !error && (
        <p className="text-xs text-gray-500">{helperText}</p>
      )}

      {/* Selection Counter */}
      <p className="text-xs text-gray-400">
        {normalizedValue.length} / {maxSelections} selected
      </p>
    </div>
  );
};
