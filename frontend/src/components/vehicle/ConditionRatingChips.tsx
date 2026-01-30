/**
 * ConditionRatingChips - Reusable rating chips component for vehicle conditions
 *
 * Displays clickable chips for condition ratings:
 * Excellent | Good | Fair | Poor | Very Poor
 *
 * Uses brand colors (emerald primary)
 */

import React from 'react';
import { CONDITION_RATINGS } from '../../types';

interface ConditionRatingChipsProps {
  name: string;
  value: string;
  onChange: (value: string) => void;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base',
};

const getChipColor = (rating: string, isSelected: boolean) => {
  if (!isSelected) {
    return 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-gray-200';
  }

  switch (rating) {
    case 'Excellent':
      return 'bg-emerald-500 text-white border-emerald-500 shadow-md';
    case 'Good':
      return 'bg-emerald-400 text-white border-emerald-400 shadow-md';
    case 'Fair':
      return 'bg-amber-400 text-white border-amber-400 shadow-md';
    case 'Poor':
      return 'bg-orange-500 text-white border-orange-500 shadow-md';
    case 'Very Poor':
      return 'bg-red-500 text-white border-red-500 shadow-md';
    default:
      return 'bg-emerald-500 text-white border-emerald-500 shadow-md';
  }
};

export const ConditionRatingChips: React.FC<ConditionRatingChipsProps> = ({
  name,
  value,
  onChange,
  label,
  required = false,
  disabled = false,
  size = 'md',
}) => {
  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="flex flex-wrap gap-2">
        {CONDITION_RATINGS.map((rating) => {
          const isSelected = value === rating;
          return (
            <button
              key={`${name}-${rating}`}
              type="button"
              disabled={disabled}
              onClick={() => onChange(rating)}
              className={`
                ${sizeClasses[size]}
                rounded-full border font-medium transition-all duration-200
                ${getChipColor(rating, isSelected)}
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1
              `}
            >
              {rating}
            </button>
          );
        })}
      </div>
    </div>
  );
};

/**
 * SimpleConditionChips - Simpler version for Yes/No or Available/Not Available options
 */
interface SimpleChipsProps {
  name: string;
  value: boolean | null;
  onChange: (value: boolean) => void;
  options?: { label: string; value: boolean }[];
  label?: string;
  required?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const defaultBooleanOptions = [
  { label: 'Yes', value: true },
  { label: 'No', value: false },
];

export const BooleanChips: React.FC<SimpleChipsProps> = ({
  name,
  value,
  onChange,
  options = defaultBooleanOptions,
  label,
  required = false,
  disabled = false,
  size = 'md',
}) => {
  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const isSelected = value === option.value;
          return (
            <button
              key={`${name}-${option.label}`}
              type="button"
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={`
                ${sizeClasses[size]}
                rounded-full border font-medium transition-all duration-200
                ${isSelected
                  ? option.value
                    ? 'bg-emerald-500 text-white border-emerald-500 shadow-md'
                    : 'bg-red-500 text-white border-red-500 shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-gray-200'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-1
              `}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

/**
 * WorkingStatusChips - For electrical/mechanical components
 */
interface WorkingStatusChipsProps {
  name: string;
  value: boolean;
  onChange: (value: boolean) => void;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const WorkingStatusChips: React.FC<WorkingStatusChipsProps> = ({
  name,
  value,
  onChange,
  label,
  required = false,
  disabled = false,
  size = 'md',
}) => {
  return (
    <BooleanChips
      name={name}
      value={value}
      onChange={onChange}
      options={[
        { label: 'Working', value: true },
        { label: 'Not Working', value: false },
      ]}
      label={label}
      required={required}
      disabled={disabled}
      size={size}
    />
  );
};

/**
 * AvailabilityChips - For features/components availability
 */
export const AvailabilityChips: React.FC<WorkingStatusChipsProps> = ({
  name,
  value,
  onChange,
  label,
  required = false,
  disabled = false,
  size = 'md',
}) => {
  return (
    <BooleanChips
      name={name}
      value={value}
      onChange={onChange}
      options={[
        { label: 'Available', value: true },
        { label: 'Not Available', value: false },
      ]}
      label={label}
      required={required}
      disabled={disabled}
      size={size}
    />
  );
};

export default ConditionRatingChips;
