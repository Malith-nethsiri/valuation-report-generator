/**
 * VehicleSpecsStep - Step 5 of Vehicle Report Form (new)
 *
 * Manufacturer specification enrichment:
 * - Optional variant/trim field for precision
 * - "Get Manufacturer Specs" button triggers Claude AI enrichment
 * - Spec data displayed with AI badge for user review
 * - User confirms specifications before proceeding
 *
 * Spec data is saved to vehicle via the standard form save flow.
 */

import React, { useState } from 'react';
import { useFormContext } from 'react-hook-form';
import {
  Cpu,
  Loader2,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Info,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { vehicleApi } from '../../services/api';
import type { VehicleSpecData } from '../../types';

export const VehicleSpecsStep: React.FC = () => {
  const { watch, setValue } = useFormContext();
  const [isEnriching, setIsEnriching] = useState(false);
  const [enrichmentStatus, setEnrichmentStatus] = useState<'idle' | 'success' | 'not_found' | 'error'>('idle');

  const vehicleId = watch('id');
  const make = watch('make');
  const model = watch('model');
  const year = watch('year_of_manufacture');
  const variant = watch('variant');
  const specData: VehicleSpecData | undefined = watch('spec_data');
  const specSource = watch('spec_source');

  const canEnrich = vehicleId && make && model && year;

  const handleEnrichSpecs = async () => {
    if (!canEnrich) {
      toast.error('Save the vehicle first, then use this feature');
      return;
    }

    setIsEnriching(true);
    setEnrichmentStatus('idle');
    const toastId = toast.loading('Fetching manufacturer specifications...');

    try {
      const result = await vehicleApi.enrichSpecs(vehicleId);
      const spec = result.spec_data;

      if (!spec || spec.confidence === 0.0) {
        setEnrichmentStatus('not_found');
        toast.error('Specifications not found — please enter manually', { id: toastId });
        return;
      }

      setValue('spec_data', spec);
      setValue('spec_source', 'ai_claude');
      setValue('spec_confidence', spec.confidence);

      // Auto-fill flat fields from spec if currently empty
      if (!watch('engine_type') && spec.engine_type) setValue('engine_type', spec.engine_type);
      if (!watch('transmission') && spec.transmission) setValue('transmission', spec.transmission);
      if (!watch('wheel_drive') && spec.wheel_drive) setValue('wheel_drive', spec.wheel_drive);
      if (!watch('fuel_type') && spec.fuel_type) setValue('fuel_type', spec.fuel_type);
      if (!watch('cylinder_capacity') && spec.displacement_cc) setValue('cylinder_capacity', spec.displacement_cc);
      if (!watch('fuel_consumption') && spec.fuel_economy_kmpl) {
        setValue('fuel_consumption', spec.fuel_economy_kmpl);
        setValue('fuel_consumption_unit', 'km/L');
      }
      if (spec.standard_features) {
        const sf = spec.standard_features;
        const currentFeatures = watch('features') || {};
        setValue('features', {
          ...currentFeatures,
          air_condition: currentFeatures.air_condition || sf.air_condition || false,
          dual_air_condition: currentFeatures.dual_air_condition || sf.dual_air_condition || false,
          power_window: currentFeatures.power_window || sf.power_window || false,
          power_steering: currentFeatures.power_steering || sf.power_steering || false,
          airbag: currentFeatures.airbag || (sf.airbag_count != null && sf.airbag_count > 0) || false,
          num_airbags: currentFeatures.num_airbags || sf.airbag_count || 0,
        });
        if (!watch('abs_available') && sf.abs_standard) setValue('abs_available', true);
        if (!watch('features.seats') && spec.seating_capacity) setValue('features.seats', spec.seating_capacity);
        if (!watch('features.doors') && spec.doors) setValue('features.doors', spec.doors);
      }

      setEnrichmentStatus('success');
      toast.success('Manufacturer specifications loaded', { id: toastId });
    } catch (error: any) {
      console.error('Spec enrichment error:', error);
      const msg = error?.response?.data?.detail || error.message || 'Failed to fetch specifications';
      if (msg.includes('make, model, and year')) {
        setEnrichmentStatus('not_found');
        toast.error('Save the vehicle first, then use this feature', { id: toastId });
      } else {
        setEnrichmentStatus('error');
        toast.error(msg, { id: toastId });
      }
    } finally {
      setIsEnriching(false);
    }
  };

  const renderSpecValue = (label: string, value: unknown, unit?: string) => {
    if (value == null) return null;
    return (
      <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
        <span className="text-sm text-gray-600">{label}</span>
        <span className="text-sm font-medium text-gray-900">
          {String(value)}{unit ? ` ${unit}` : ''}
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4 p-4 bg-purple-50 rounded-xl border border-purple-100">
        <Cpu className="w-6 h-6 text-purple-500 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-medium text-purple-900">Manufacturer Specifications</h3>
          <p className="text-sm text-purple-700 mt-1">
            Auto-fill engine, transmission, dimensions, and standard features from manufacturer data.
            Review and confirm before proceeding.
          </p>
        </div>
      </div>

      {/* Vehicle Identity Summary */}
      {(make || model || year) && (
        <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200">
          <div className="text-sm text-gray-600">Looking up specs for:</div>
          <div className="font-semibold text-gray-900">
            {[year, make, model].filter(Boolean).join(' ')}
            {variant && <span className="text-gray-500 font-normal ml-1">({variant})</span>}
          </div>
        </div>
      )}

      {/* Variant Field */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Variant / Grade <span className="text-gray-400 font-normal">(optional)</span>
        </label>
        <input
          type="text"
          value={variant || ''}
          onChange={(e) => setValue('variant', e.target.value)}
          placeholder="e.g. G grade, X grade, S, Sport"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent"
        />
        <p className="mt-1 text-xs text-gray-500">
          Specifying the trim level improves specification accuracy. Leave blank for standard/base specs.
        </p>
      </div>

      {/* Enrich Button */}
      <div className="flex flex-col items-center gap-3 p-6 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl border border-purple-100">
        <button
          type="button"
          onClick={handleEnrichSpecs}
          disabled={isEnriching || !canEnrich}
          className={`
            flex items-center gap-3 px-8 py-4 rounded-xl font-semibold text-white
            transition-all duration-300 shadow-lg
            ${isEnriching || !canEnrich
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 hover:shadow-xl transform hover:scale-[1.02]'
            }
          `}
        >
          {isEnriching ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Fetching Specifications...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              Get Manufacturer Specs
            </>
          )}
        </button>

        {!canEnrich && (
          <p className="text-sm text-amber-700 flex items-center gap-1">
            <Info className="w-4 h-4" />
            {vehicleId
              ? 'Make, model, and year are required for spec enrichment'
              : 'Save the vehicle first to enable spec enrichment'}
          </p>
        )}
        {canEnrich && !specData && (
          <p className="text-sm text-gray-500 text-center">
            AI will load engine, transmission, dimensions, and standard features
          </p>
        )}
      </div>

      {/* Enrichment Status */}
      {enrichmentStatus === 'not_found' && (
        <div className="flex items-start gap-3 p-4 bg-amber-50 rounded-xl border border-amber-200">
          <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800">Specifications not found</p>
            <p className="text-sm text-amber-700 mt-1">
              Could not find manufacturer specs for this vehicle. Please enter the specifications
              manually in the Book Data Review step.
            </p>
          </div>
        </div>
      )}

      {enrichmentStatus === 'error' && (
        <div className="flex items-start gap-3 p-4 bg-red-50 rounded-xl border border-red-200">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">Enrichment failed</p>
            <p className="text-sm text-red-700 mt-1">
              Could not load specifications. Please try again or enter values manually.
            </p>
          </div>
        </div>
      )}

      {/* Spec Data Display */}
      {specData && specSource === 'ai_claude' && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-purple-500" />
            <h3 className="font-medium text-gray-900">AI-Suggested Specifications</h3>
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
              AI · {specData.confidence != null ? `${Math.round(specData.confidence * 100)}% confidence` : 'AI'}
            </span>
          </div>

          <div className="bg-white border border-purple-200 rounded-xl p-4 space-y-1">
            <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-3">Engine & Drivetrain</p>
            {renderSpecValue('Engine Type', specData.engine_type)}
            {renderSpecValue('Displacement', specData.displacement_cc, 'cc')}
            {renderSpecValue('Transmission', specData.transmission)}
            {renderSpecValue('Wheel Drive', specData.wheel_drive)}
            {renderSpecValue('Fuel Type', specData.fuel_type)}
            {renderSpecValue('Fuel Economy (Rated)', specData.fuel_economy_kmpl, 'km/L')}
          </div>

          {(specData.length_mm || specData.seating_capacity || specData.doors) && (
            <div className="bg-white border border-purple-200 rounded-xl p-4 space-y-1">
              <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-3">Dimensions & Capacity</p>
              {renderSpecValue('Length', specData.length_mm, 'mm')}
              {renderSpecValue('Width', specData.width_mm, 'mm')}
              {renderSpecValue('Height', specData.height_mm, 'mm')}
              {renderSpecValue('Wheelbase', specData.wheelbase_mm, 'mm')}
              {renderSpecValue('Seating Capacity', specData.seating_capacity)}
              {renderSpecValue('Doors', specData.doors)}
            </div>
          )}

          {specData.standard_features && (
            <div className="bg-white border border-purple-200 rounded-xl p-4">
              <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-3">Standard Equipment</p>
              <div className="grid grid-cols-2 gap-2">
                {specData.standard_features.air_condition != null && (
                  <div className="text-sm text-gray-700">
                    A/C: <span className="font-medium">{specData.standard_features.air_condition ? 'Standard' : 'Not standard'}</span>
                  </div>
                )}
                {specData.standard_features.power_window != null && (
                  <div className="text-sm text-gray-700">
                    Power Windows: <span className="font-medium">{specData.standard_features.power_window ? 'Standard' : 'Not standard'}</span>
                  </div>
                )}
                {specData.standard_features.power_steering != null && (
                  <div className="text-sm text-gray-700">
                    Power Steering: <span className="font-medium">{specData.standard_features.power_steering ? 'Standard' : 'Not standard'}</span>
                  </div>
                )}
                {specData.standard_features.airbag_count != null && (
                  <div className="text-sm text-gray-700">
                    Airbags: <span className="font-medium">{specData.standard_features.airbag_count}</span>
                  </div>
                )}
                {specData.standard_features.abs_standard != null && (
                  <div className="text-sm text-gray-700">
                    ABS: <span className="font-medium">{specData.standard_features.abs_standard ? 'Standard' : 'Not standard'}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {specData.safety_rating && (
            <div className="bg-white border border-purple-200 rounded-xl p-4">
              {renderSpecValue('Safety Rating', specData.safety_rating)}
            </div>
          )}

          <div className="p-3 bg-amber-50 rounded-xl border border-amber-100">
            <p className="text-xs text-amber-700">
              These specifications are AI-suggested based on manufacturer data. Fields have been auto-filled
              in the form above. Review and correct any inaccuracies before completing the report.
            </p>
          </div>
        </div>
      )}

      {/* Empty state when no spec data yet */}
      {!specData && enrichmentStatus === 'idle' && (
        <div className="text-center py-6 text-gray-400">
          <Cpu className="w-10 h-10 mx-auto mb-2 text-gray-200" />
          <p className="text-sm">No specifications loaded yet</p>
          <p className="text-xs mt-1">Click the button above to auto-load manufacturer specs, or skip this step and enter values manually</p>
        </div>
      )}
    </div>
  );
};

export default VehicleSpecsStep;
