import React, { useEffect, useState } from 'react';
import { Label } from './Label';
import { Input } from './Input';
import { AlertCircle, Info } from 'lucide-react';
import {
  calculateExtentData,
  validateExtentValues,
  normalizeExtent,
} from '../utils/extentCalculator';

interface LandExtentInputProps {
  acres?: number;
  roods?: number;
  perches?: number;
  onChange: (extentData: {
    land_extent_acres: number;
    land_extent_roods: number;
    land_extent_perches: number;
    land_extent_hectares: number;
    land_extent_square_meters: number;
    land_extent_formatted: string;
  }) => void;
  disabled?: boolean;
  showMetric?: boolean;
  ocrFilledFields?: Set<string>;
}

export function LandExtentInput({
  acres = 0,
  roods = 0,
  perches = 0,
  onChange,
  disabled = false,
  showMetric = true,
  ocrFilledFields,
}: LandExtentInputProps) {
  const ocr = (field: string) =>
    ocrFilledFields?.has(field) ? ' bg-blue-50 border-blue-200' : '';
  const [localAcres, setLocalAcres] = useState<string>(acres?.toString() || '0');
  const [localRoods, setLocalRoods] = useState<string>(roods?.toString() || '0');
  const [localPerches, setLocalPerches] = useState<string>(
    perches?.toString() || '0'
  );
  const [validation, setValidation] = useState<{
    valid: boolean;
    error?: string;
    warning?: string;
  }>({ valid: true });

  // Calculated values for display
  const [preview, setPreview] = useState({
    formatted: '00A-0R-0P',
    hectares: '0.0000',
    squareMeters: '0.00',
  });

  // Ref to track if this is the first render
  const onChangeRef = React.useRef(onChange);
  onChangeRef.current = onChange;

  // Update preview and notify parent when values change
  useEffect(() => {
    const a = parseFloat(localAcres) || 0;
    const r = parseInt(localRoods, 10) || 0;
    const p = parseFloat(localPerches) || 0;

    // Validate
    const validationResult = validateExtentValues(a, r, p);
    setValidation(validationResult);

    if (validationResult.valid) {
      // Calculate all extent data
      const extentData = calculateExtentData(a, r, p);

      // Update preview
      setPreview({
        formatted: extentData.land_extent_formatted,
        hectares: extentData.land_extent_hectares.toFixed(4),
        squareMeters: extentData.land_extent_square_meters.toFixed(2),
      });

      // Notify parent component using ref to avoid infinite loop
      onChangeRef.current(extentData);
    }
  }, [localAcres, localRoods, localPerches]);

  const handleAcresChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Allow empty, numbers, and decimals
    if (value === '' || /^\d*\.?\d*$/.test(value)) {
      setLocalAcres(value);
    }
  };

  const handleRoodsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const numValue = parseInt(value, 10);

    // Allow empty or valid integers
    if (value === '' || (!isNaN(numValue) && numValue >= 0)) {
      setLocalRoods(value);

      // Auto-normalize if >= 4 roods
      if (numValue >= 4) {
        const normalized = normalizeExtent(
          parseFloat(localAcres) || 0,
          numValue,
          parseFloat(localPerches) || 0
        );
        setLocalAcres(normalized.acres.toString());
        setLocalRoods(normalized.roods.toString());
        setLocalPerches(normalized.perches.toString());
      }
    }
  };

  const handlePerchesChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const numValue = parseFloat(value);

    // Allow empty, numbers, and decimals
    if (value === '' || /^\d*\.?\d*$/.test(value)) {
      setLocalPerches(value);

      // Auto-normalize if >= 40 perches
      if (!isNaN(numValue) && numValue >= 40) {
        const normalized = normalizeExtent(
          parseFloat(localAcres) || 0,
          parseInt(localRoods, 10) || 0,
          numValue
        );
        setLocalAcres(normalized.acres.toString());
        setLocalRoods(normalized.roods.toString());
        setLocalPerches(normalized.perches.toString());
      }
    }
  };

  return (
    <div className="space-y-4">
      {/* Title */}
      <div>
        <Label className="text-lg font-semibold">Land Extent</Label>
        <p className="text-sm text-gray-600 mt-1">
          Enter land extent in Acres-Roods-Perches format
        </p>
      </div>

      {/* A-R-P Input Fields */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Acres */}
        <div>
          <Label htmlFor="acres">
            Acres <span className="text-gray-500 text-sm">(A)</span>
          </Label>
          <Input
            id="acres"
            type="text"
            inputMode="decimal"
            value={localAcres}
            onChange={handleAcresChange}
            disabled={disabled}
            placeholder="0"
            className={`mt-1${ocr('land_extent_acres')}`}
          />
          <p className="text-xs text-gray-500 mt-1">
            1 Acre = 4 Roods = 160 Perches
          </p>
        </div>

        {/* Roods */}
        <div>
          <Label htmlFor="roods">
            Roods <span className="text-gray-500 text-sm">(R)</span>
          </Label>
          <Input
            id="roods"
            type="text"
            inputMode="numeric"
            value={localRoods}
            onChange={handleRoodsChange}
            disabled={disabled}
            placeholder="0"
            className={`mt-1${ocr('land_extent_roods')}`}
          />
          <p className="text-xs text-gray-500 mt-1">
            0-3 (auto-converts to acres)
          </p>
        </div>

        {/* Perches */}
        <div>
          <Label htmlFor="perches">
            Perches <span className="text-gray-500 text-sm">(P)</span>
          </Label>
          <Input
            id="perches"
            type="text"
            inputMode="decimal"
            value={localPerches}
            onChange={handlePerchesChange}
            disabled={disabled}
            placeholder="0.00"
            className={`mt-1${ocr('land_extent_perches')}`}
          />
          <p className="text-xs text-gray-500 mt-1">
            0-39.99 (auto-converts to roods)
          </p>
        </div>
      </div>

      {/* Validation Messages */}
      {validation.error && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-700">{validation.error}</p>
          </div>
        </div>
      )}

      {validation.warning && !validation.error && (
        <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-800">Warning</p>
            <p className="text-sm text-yellow-700">{validation.warning}</p>
          </div>
        </div>
      )}

      {/* Preview Section */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2 mb-3">
          <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-blue-800">
              Formatted Extent
            </p>
          </div>
        </div>

        {/* Formatted String */}
        <div className="bg-white rounded-lg p-3 mb-3 border border-blue-300">
          <p className="text-xs text-gray-600 mb-1">Legal Document Format:</p>
          <p className="text-2xl font-mono font-bold text-blue-900">
            {preview.formatted}
          </p>
        </div>

        {/* Metric Conversions */}
        {showMetric && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-white rounded-lg p-3 border border-blue-200">
              <p className="text-xs text-gray-600 mb-1">Hectares:</p>
              <p className="text-lg font-semibold text-gray-900">
                {preview.hectares} ha
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-blue-200">
              <p className="text-xs text-gray-600 mb-1">Square Meters:</p>
              <p className="text-lg font-semibold text-gray-900">
                {preview.squareMeters} m²
              </p>
            </div>
          </div>
        )}

        {/* Conversion Reference */}
        <div className="mt-3 pt-3 border-t border-blue-200">
          <p className="text-xs text-blue-700">
            <strong>Conversion Reference:</strong> 1 Perch = 25.29 m² | 1 Acre
            = 0.4047 hectares
          </p>
        </div>
      </div>
    </div>
  );
}
