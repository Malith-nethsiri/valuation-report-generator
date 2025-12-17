import React from 'react';
import { Lock, Unlock } from 'lucide-react';
import { Input } from './Input';
import { Label } from './Label';
import { formatNumber } from '../utils/currency';

interface CalculatedFieldProps {
  label: string;
  value: number;
  calculatedValue: number;
  isManual: boolean;
  onToggle: () => void;
  onChange: (value: number) => void;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  disabled?: boolean;
  className?: string;
}

/**
 * CalculatedField Component
 *
 * A hybrid input field that can switch between auto-calculated and manual entry modes.
 * - When locked (auto mode): Shows calculated value with blue background
 * - When unlocked (manual mode): Allows user input with white background
 * - Lock/unlock toggle button on the right side
 */
export function CalculatedField({
  label,
  value,
  calculatedValue,
  isManual,
  onToggle,
  onChange,
  prefix = '',
  suffix = '',
  decimals = 2,
  disabled = false,
  className = '',
}: CalculatedFieldProps) {
  const displayValue = isManual ? value : calculatedValue;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const numValue = parseFloat(e.target.value.replace(/[^0-9.-]/g, '')) || 0;
    onChange(numValue);
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <Label>{label}</Label>
      <div className="flex items-center gap-2">
        <div className="flex-1 relative">
          {prefix && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">
              {prefix}
            </span>
          )}
          <Input
            type="text"
            value={formatNumber(displayValue, decimals)}
            onChange={handleInputChange}
            disabled={disabled || !isManual}
            className={`${prefix ? 'pl-12' : ''} ${suffix ? 'pr-20' : ''} ${
              !isManual ? 'bg-blue-50 border-blue-200' : ''
            }`}
            readOnly={!isManual}
          />
          {suffix && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">
              {suffix}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={onToggle}
          disabled={disabled}
          className={`p-2 rounded-md border transition-colors ${
            isManual
              ? 'border-gray-300 bg-white hover:bg-gray-50'
              : 'border-blue-300 bg-blue-50 hover:bg-blue-100'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title={isManual ? 'Lock to use auto-calculated value' : 'Unlock to enter manual value'}
        >
          {isManual ? (
            <Unlock className="h-4 w-4 text-gray-600" />
          ) : (
            <Lock className="h-4 w-4 text-blue-600" />
          )}
        </button>
      </div>
      {!isManual && (
        <p className="text-xs text-blue-600">
          Auto-calculated value. Click unlock to enter manually.
        </p>
      )}
      {isManual && calculatedValue !== value && (
        <p className="text-xs text-orange-600">
          Manual value differs from auto-calculated ({formatNumber(calculatedValue, decimals)})
        </p>
      )}
    </div>
  );
}
