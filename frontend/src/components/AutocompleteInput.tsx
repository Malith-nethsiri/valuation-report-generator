import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown, X, Check } from 'lucide-react';
import { Input } from './Input';

interface AutocompleteOption {
  label: string;
  value: string;
}

interface AutocompleteInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  suggestions: string[];
  placeholder?: string;
  required?: boolean;
  error?: string;
  className?: string;
  allowCustom?: boolean;
  multiSelect?: boolean;
  selectedItems?: string[];
  onSelectionChange?: (items: string[]) => void;
}

export const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  label,
  value,
  onChange,
  onBlur,
  suggestions = [],
  placeholder,
  required = false,
  error,
  className = '',
  allowCustom = true,
  multiSelect = false,
  selectedItems = [],
  onSelectionChange
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState(value);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter suggestions based on input
  useEffect(() => {
    if (!inputValue.trim()) {
      setFilteredSuggestions(suggestions);
      return;
    }

    const filtered = suggestions.filter(suggestion =>
      suggestion.toLowerCase().includes(inputValue.toLowerCase())
    );

    setFilteredSuggestions(filtered);
    setHighlightedIndex(0);
  }, [inputValue, suggestions]);

  // Update input value when prop changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    setIsOpen(true);

    if (!multiSelect) {
      onChange(newValue);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (multiSelect && onSelectionChange) {
      if (selectedItems.includes(suggestion)) {
        onSelectionChange(selectedItems.filter(item => item !== suggestion));
      } else {
        onSelectionChange([...selectedItems, suggestion]);
      }
      setInputValue('');
    } else {
      setInputValue(suggestion);
      onChange(suggestion);
      setIsOpen(false);
    }
    setHighlightedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true);
        return;
      }
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev < filteredSuggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev > 0 ? prev - 1 : filteredSuggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && filteredSuggestions[highlightedIndex]) {
          handleSuggestionClick(filteredSuggestions[highlightedIndex]);
        } else if (allowCustom && inputValue.trim()) {
          if (multiSelect && onSelectionChange) {
            if (!selectedItems.includes(inputValue.trim())) {
              onSelectionChange([...selectedItems, inputValue.trim()]);
            }
            setInputValue('');
          } else {
            onChange(inputValue.trim());
            setIsOpen(false);
          }
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        inputRef.current?.blur();
        break;
      case 'Tab':
        setIsOpen(false);
        break;
    }
  };

  const removeSelectedItem = (item: string) => {
    if (multiSelect && onSelectionChange) {
      onSelectionChange(selectedItems.filter(selected => selected !== item));
    }
  };

  const handleFocus = () => {
    setIsOpen(true);
  };

  const handleBlur = () => {
    // Small delay to allow click events to fire
    setTimeout(() => {
      setIsOpen(false);
      onBlur?.();
    }, 150);
  };

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      {/* Label */}
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {/* Multi-select tags */}
      {multiSelect && selectedItems.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {selectedItems.map((item, index) => (
            <span
              key={`${item}-${index}`}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-emerald-100 text-emerald-800 border border-emerald-200"
            >
              {item}
              <button
                type="button"
                onClick={() => removeSelectedItem(item)}
                className="ml-2 text-emerald-600 hover:text-emerald-800"
              >
                <X size={14} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="relative">
        <Input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          className={`pr-10 ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'focus:border-emerald-500 focus:ring-emerald-500'}`}
          autoComplete="off"
        />

        <button
          type="button"
          className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
          onClick={() => {
            setIsOpen(!isOpen);
            inputRef.current?.focus();
          }}
        >
          <ChevronDown
            size={20}
            className={`transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          />
        </button>
      </div>

      {/* Error message */}
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {filteredSuggestions.length > 0 ? (
            <ul className="py-1">
              {filteredSuggestions.map((suggestion, index) => (
                <li key={`${suggestion}-${index}`}>
                  <button
                    type="button"
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none flex items-center justify-between ${
                      highlightedIndex === index ? 'bg-emerald-50 text-emerald-900' : 'text-gray-900'
                    } ${multiSelect && selectedItems.includes(suggestion) ? 'bg-emerald-50' : ''}`}
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    <span>{suggestion}</span>
                    {multiSelect && selectedItems.includes(suggestion) && (
                      <Check size={16} className="text-emerald-600" />
                    )}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">
              {allowCustom ? (
                <>
                  No suggestions found.
                  <br />
                  <span className="text-xs text-emerald-600">Press Enter to add "{inputValue}"</span>
                </>
              ) : (
                'No matching options found'
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};