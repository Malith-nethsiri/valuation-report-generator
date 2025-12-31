import React, { useState, useEffect } from 'react';
import { Building, Sprout, Plus, Minus, X } from 'lucide-react';
import { Button } from './Button';

interface AddPropertyDialogProps {
  isOpen: boolean;
  propertyType: 'residential' | 'bare_land';
  maxAllowed: number;
  onConfirm: (count: number) => void;
  onCancel: () => void;
}

export const AddPropertyDialog: React.FC<AddPropertyDialogProps> = ({
  isOpen,
  propertyType,
  maxAllowed,
  onConfirm,
  onCancel,
}) => {
  const [count, setCount] = useState(1);

  // Reset count when dialog opens
  useEffect(() => {
    if (isOpen) {
      setCount(Math.min(1, maxAllowed));
    }
  }, [isOpen, maxAllowed]);

  if (!isOpen) return null;

  const isResidential = propertyType === 'residential';
  const propertyTypeLabel = isResidential ? 'Residential/Commercial' : 'Bare Land';
  const gradientClass = isResidential
    ? 'from-blue-500 to-indigo-600'
    : 'from-green-500 to-emerald-600';
  const iconBgClass = isResidential ? 'bg-blue-100' : 'bg-green-100';
  const iconTextClass = isResidential ? 'text-blue-600' : 'text-green-600';
  const buttonClass = isResidential
    ? 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700'
    : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700';

  const handleIncrement = () => {
    if (count < maxAllowed) {
      setCount(count + 1);
    }
  };

  const handleDecrement = () => {
    if (count > 1) {
      setCount(count - 1);
    }
  };

  const handleConfirm = () => {
    if (count >= 1 && count <= maxAllowed) {
      onConfirm(count);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleConfirm();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className={`bg-gradient-to-r ${gradientClass} text-white px-6 py-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-xl">
                {isResidential ? (
                  <Building className="h-6 w-6" />
                ) : (
                  <Sprout className="h-6 w-6" />
                )}
              </div>
              <div>
                <h3 className="text-lg font-bold">Add {propertyTypeLabel} Properties</h3>
                <p className="text-sm text-white/80">
                  How many properties would you like to add?
                </p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="p-1 hover:bg-white/20 rounded-lg transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Number Input */}
          <div className="flex items-center justify-center gap-4">
            {/* Decrement Button */}
            <button
              onClick={handleDecrement}
              disabled={count <= 1}
              className={`p-4 rounded-full transition-all duration-200 ${iconBgClass} ${iconTextClass} hover:scale-110 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100`}
            >
              <Minus className="h-6 w-6" />
            </button>

            {/* Count Display */}
            <div className="text-center">
              <input
                type="number"
                min={1}
                max={maxAllowed}
                value={count}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 1;
                  setCount(Math.max(1, Math.min(val, maxAllowed)));
                }}
                onKeyDown={handleKeyDown}
                className={`text-6xl font-bold text-center w-32 border-2 rounded-xl px-4 py-2 focus:outline-none focus:ring-4 ${
                  isResidential
                    ? 'text-blue-600 border-blue-200 focus:ring-blue-200'
                    : 'text-green-600 border-green-200 focus:ring-green-200'
                }`}
              />
            </div>

            {/* Increment Button */}
            <button
              onClick={handleIncrement}
              disabled={count >= maxAllowed}
              className={`p-4 rounded-full transition-all duration-200 ${iconBgClass} ${iconTextClass} hover:scale-110 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100`}
            >
              <Plus className="h-6 w-6" />
            </button>
          </div>

          {/* Info Box */}
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <div className="flex items-start gap-2">
              <div className={`p-1 rounded-full ${iconBgClass} mt-0.5`}>
                <svg className={`h-4 w-4 ${iconTextClass}`} fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-700">
                  <span className="font-semibold">You can add up to {maxAllowed} more {maxAllowed === 1 ? 'property' : 'properties'}</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Maximum total limit: 20 properties per report
                </p>
              </div>
            </div>
          </div>

          {/* Example */}
          <div className="text-center text-sm text-gray-500">
            <p>
              Entering <span className="font-semibold">{count}</span> will create{' '}
              <span className="font-semibold">{count} {propertyTypeLabel.toLowerCase()}</span>{' '}
              {count === 1 ? 'property' : 'properties'} in draft status
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-gray-50 px-6 py-4 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-3 bg-white border-2 border-gray-200 text-gray-700 font-medium rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all duration-200"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={count < 1 || count > maxAllowed}
            className={`flex-1 px-4 py-3 text-white font-bold rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed ${buttonClass}`}
          >
            Add {count} {count === 1 ? 'Property' : 'Properties'}
          </button>
        </div>
      </div>
    </div>
  );
};
