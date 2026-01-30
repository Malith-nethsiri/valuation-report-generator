/**
 * VehicleFeaturesValuationStep - Step 5 of Vehicle Report Form
 *
 * Final step with:
 * - Vehicle features (AC, power features, airbags)
 * - Brakes and safety
 * - Suspension and tyres
 * - Electrical and lights
 * - History (accidents, repairs)
 * - Valuation fields
 * - Office data (conditional)
 * - Past valuations table (conditional)
 */

import React, { useState } from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import {
  Wind,
  Shield,
  Circle,
  Lightbulb,
  History,
  DollarSign,
  Building2,
  Plus,
  Trash2,
  Sparkles,
  Loader2,
} from 'lucide-react';
import { Input } from '../Input';
import { Label } from '../Label';
import {
  ConditionRatingChips,
  BooleanChips,
  WorkingStatusChips,
  AvailabilityChips,
} from './ConditionRatingChips';
import { vehicleApi } from '../../services/api';
import { BATTERY_CONDITION_OPTIONS } from '../../types';
import toast from 'react-hot-toast';

const APPROVAL_POSITIONS = [
  'Senior Valuer',
  'Chief Valuer',
  'Deputy Chief Valuer',
  'Valuation Officer',
  'Assistant Valuer',
  'Other'
];

export const VehicleFeaturesValuationStep: React.FC = () => {
  const { register, control, watch, setValue, getValues } = useFormContext();
  const [isLoadingValuation, setIsLoadingValuation] = useState(false);

  const isOfficeUse = watch('is_office_use');
  const pastValuations = watch('past_valuations') || [];
  const vehicleId = watch('id'); // For existing vehicles

  // Add new past valuation row
  const addPastValuation = () => {
    const newRow = {
      serial: pastValuations.length + 1,
      civil_no: '',
      military_no: '',
      year: '',
      value: '',
      market_value: '',
    };
    setValue('past_valuations', [...pastValuations, newRow]);
  };

  // Remove past valuation row
  const removePastValuation = (index: number) => {
    const updated = pastValuations.filter((_: any, i: number) => i !== index);
    // Re-number serials
    updated.forEach((row: any, i: number) => {
      row.serial = i + 1;
    });
    setValue('past_valuations', updated);
  };

  // Update past valuation field
  const updatePastValuation = (index: number, field: string, value: any) => {
    const updated = [...pastValuations];
    updated[index] = { ...updated[index], [field]: value };
    setValue('past_valuations', updated);
  };

  // Get AI valuation suggestion
  const handleGetValuationSuggestion = async () => {
    if (!vehicleId) {
      toast.error('Please save the vehicle first to get AI suggestions');
      return;
    }

    setIsLoadingValuation(true);
    try {
      const suggestion = await vehicleApi.getValuationSuggestion(vehicleId);

      if (suggestion.suggested_market_value) {
        setValue('market_value', suggestion.suggested_market_value);
      }
      if (suggestion.suggested_forced_sale_value) {
        setValue('forced_sale_value', suggestion.suggested_forced_sale_value);
      }
      if (suggestion.suggested_brand_new_price) {
        setValue('brand_new_price', suggestion.suggested_brand_new_price);
      }
      if (suggestion.valuation_summary) {
        setValue('valuation_summary', suggestion.valuation_summary);
      }

      toast.success('Valuation suggestion applied');
    } catch (error: any) {
      console.error('Valuation suggestion error:', error);
      toast.error(error.message || 'Failed to get valuation suggestion');
    } finally {
      setIsLoadingValuation(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Section 1: Brakes & Safety */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center">
            <Shield className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Brakes & Safety</h3>
            <p className="text-sm text-gray-500">Brake system condition and safety features</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Foot Brake Condition */}
          <Controller
            name="foot_brake_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="foot_brake_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Foot Brake Condition"
              />
            )}
          />

          {/* Parking Brake Condition */}
          <Controller
            name="parking_brake_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="parking_brake_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Parking Brake Condition"
              />
            )}
          />

          {/* Disc Brake Available */}
          <Controller
            name="disc_brake_available"
            control={control}
            render={({ field }) => (
              <AvailabilityChips
                name="disc_brake_available"
                value={field.value}
                onChange={field.onChange}
                label="Disc Brake"
              />
            )}
          />

          {/* ABS Available */}
          <Controller
            name="abs_available"
            control={control}
            render={({ field }) => (
              <AvailabilityChips
                name="abs_available"
                value={field.value}
                onChange={field.onChange}
                label="ABS"
              />
            )}
          />
        </div>
      </div>

      {/* Section 2: Features */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
            <Wind className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Comfort & Features</h3>
            <p className="text-sm text-gray-500">Vehicle amenities and features</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {/* Feature Checkboxes */}
          {[
            { name: 'features.air_condition', label: 'Air Condition' },
            { name: 'features.dual_air_condition', label: 'Dual A/C' },
            { name: 'features.power_mirror', label: 'Power Mirror' },
            { name: 'features.power_window', label: 'Power Window' },
            { name: 'features.power_steering', label: 'Power Steering' },
            { name: 'features.airbag', label: 'Airbag' },
          ].map((feature) => (
            <label key={feature.name} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 cursor-pointer transition-colors">
              <input
                type="checkbox"
                className="w-5 h-5 rounded border-gray-300 text-emerald-500 focus:ring-emerald-500"
                {...register(feature.name)}
              />
              <span className="text-sm font-medium text-gray-700">{feature.label}</span>
            </label>
          ))}
        </div>

        {/* Numeric Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label className="text-gray-700 font-medium">Number of Airbags</Label>
            <Input
              type="number"
              min="0"
              max="12"
              placeholder="e.g., 2"
              className="h-12"
              {...register('features.num_airbags', { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-gray-700 font-medium">Seats</Label>
            <Input
              type="number"
              min="1"
              max="50"
              placeholder="e.g., 5"
              className="h-12"
              {...register('features.seats', { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-gray-700 font-medium">Doors</Label>
            <Input
              type="number"
              min="0"
              max="6"
              placeholder="e.g., 4"
              className="h-12"
              {...register('features.doors', { valueAsNumber: true })}
            />
          </div>
        </div>
      </div>

      {/* Section 3: Suspension */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
            <Circle className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Suspension</h3>
            <p className="text-sm text-gray-500">Front and rear suspension condition</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Controller
            name="suspension.front"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="suspension.front"
                value={field.value || ''}
                onChange={field.onChange}
                label="Front Suspension"
              />
            )}
          />

          <Controller
            name="suspension.rear"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="suspension.rear"
                value={field.value || ''}
                onChange={field.onChange}
                label="Rear Suspension"
              />
            )}
          />
        </div>
      </div>

      {/* Section 4: Tyres */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-gray-800 flex items-center justify-center">
            <Circle className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Tyres</h3>
            <p className="text-sm text-gray-500">Tyre specifications and condition</p>
          </div>
        </div>

        {/* Front Tyres */}
        <div className="p-4 bg-gray-50 rounded-xl space-y-4">
          <h4 className="font-medium text-gray-700">Front Tyres</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Input
              placeholder="Brand"
              className="h-10"
              {...register('tyres.front.brand')}
            />
            <Input
              placeholder="Size (e.g., 195/65R15)"
              className="h-10"
              {...register('tyres.front.size')}
            />
            <Input
              type="number"
              min="0"
              max="100"
              placeholder="Tread %"
              className="h-10"
              {...register('tyres.front.tread_percent', { valueAsNumber: true })}
            />
            <Controller
              name="tyres.front.condition"
              control={control}
              render={({ field }) => (
                <select
                  className="h-10 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 px-3"
                  value={field.value || ''}
                  onChange={field.onChange}
                >
                  <option value="">Condition</option>
                  <option value="Excellent">Excellent</option>
                  <option value="Good">Good</option>
                  <option value="Fair">Fair</option>
                  <option value="Poor">Poor</option>
                  <option value="Very Poor">Very Poor</option>
                </select>
              )}
            />
          </div>
        </div>

        {/* Rear Tyres */}
        <div className="p-4 bg-gray-50 rounded-xl space-y-4">
          <h4 className="font-medium text-gray-700">Rear Tyres</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Input
              placeholder="Brand"
              className="h-10"
              {...register('tyres.rear.brand')}
            />
            <Input
              placeholder="Size (e.g., 195/65R15)"
              className="h-10"
              {...register('tyres.rear.size')}
            />
            <Input
              type="number"
              min="0"
              max="100"
              placeholder="Tread %"
              className="h-10"
              {...register('tyres.rear.tread_percent', { valueAsNumber: true })}
            />
            <Controller
              name="tyres.rear.condition"
              control={control}
              render={({ field }) => (
                <select
                  className="h-10 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 px-3"
                  value={field.value || ''}
                  onChange={field.onChange}
                >
                  <option value="">Condition</option>
                  <option value="Excellent">Excellent</option>
                  <option value="Good">Good</option>
                  <option value="Fair">Fair</option>
                  <option value="Poor">Poor</option>
                  <option value="Very Poor">Very Poor</option>
                </select>
              )}
            />
          </div>
        </div>

        {/* Tyre Options */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Controller
            name="tyres.spare_available"
            control={control}
            render={({ field }) => (
              <AvailabilityChips
                name="tyres.spare_available"
                value={field.value}
                onChange={field.onChange}
                label="Spare Tyre"
                size="sm"
              />
            )}
          />

          <Controller
            name="tyres.need_replacement"
            control={control}
            render={({ field }) => (
              <BooleanChips
                name="tyres.need_replacement"
                value={field.value}
                onChange={field.onChange}
                label="Need Replacement"
                size="sm"
              />
            )}
          />

          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-700">Rear Type (for trucks)</Label>
            <div className="flex gap-2">
              {['single', 'dual'].map((type) => (
                <label key={type} className="flex items-center gap-2">
                  <input
                    type="radio"
                    value={type}
                    {...register('tyres.rear_type')}
                    className="w-4 h-4 text-emerald-500 focus:ring-emerald-500"
                  />
                  <span className="text-sm capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Section 5: Electrical & Lights */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-yellow-100 flex items-center justify-center">
            <Lightbulb className="w-5 h-5 text-yellow-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Electrical & Lights</h3>
            <p className="text-sm text-gray-500">Electrical system and lighting</p>
          </div>
        </div>

        {/* Electrical */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { name: 'electrical.starter', label: 'Starter' },
            { name: 'electrical.horn', label: 'Horn' },
            { name: 'electrical.wiper', label: 'Wiper' },
          ].map((item) => (
            <Controller
              key={item.name}
              name={item.name}
              control={control}
              render={({ field }) => (
                <WorkingStatusChips
                  name={item.name}
                  value={field.value}
                  onChange={field.onChange}
                  label={item.label}
                  size="sm"
                />
              )}
            />
          ))}

          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-700">Battery</Label>
            <select
              className="w-full h-10 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 px-3"
              {...register('electrical.battery_condition')}
            >
              <option value="">Select condition</option>
              {BATTERY_CONDITION_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Lights */}
        <div className="p-4 bg-gray-50 rounded-xl">
          <h4 className="font-medium text-gray-700 mb-4">Lights</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { name: 'lights.head', label: 'Head' },
              { name: 'lights.dim', label: 'Dim' },
              { name: 'lights.signal', label: 'Signal' },
              { name: 'lights.parking', label: 'Parking' },
              { name: 'lights.reverse', label: 'Reverse' },
              { name: 'lights.meter', label: 'Meter' },
            ].map((light) => (
              <Controller
                key={light.name}
                name={light.name}
                control={control}
                render={({ field }) => (
                  <WorkingStatusChips
                    name={light.name}
                    value={field.value}
                    onChange={field.onChange}
                    label={light.label}
                    size="sm"
                  />
                )}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Section 6: History */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center">
            <History className="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">History & Repairs</h3>
            <p className="text-sm text-gray-500">Vehicle history information</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Controller
            name="has_accidents"
            control={control}
            render={({ field }) => (
              <BooleanChips
                name="has_accidents"
                value={field.value}
                onChange={field.onChange}
                label="Accident History"
              />
            )}
          />

          <Controller
            name="has_repairs"
            control={control}
            render={({ field }) => (
              <BooleanChips
                name="has_repairs"
                value={field.value}
                onChange={field.onChange}
                label="Repair History"
              />
            )}
          />

          <Controller
            name="needs_repairs_within_year"
            control={control}
            render={({ field }) => (
              <BooleanChips
                name="needs_repairs_within_year"
                value={field.value}
                onChange={field.onChange}
                label="Repairs Needed Within Year"
              />
            )}
          />

          <Controller
            name="body_parts_replaced"
            control={control}
            render={({ field }) => (
              <BooleanChips
                name="body_parts_replaced"
                value={field.value}
                onChange={field.onChange}
                label="Body Parts Replaced"
              />
            )}
          />
        </div>
      </div>

      {/* Section 7: Valuation */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
            <DollarSign className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Valuation</h3>
            <p className="text-sm text-gray-500">Vehicle valuation details</p>
          </div>
        </div>

        {/* AI Suggestion Button */}
        {vehicleId && (
          <button
            type="button"
            onClick={handleGetValuationSuggestion}
            disabled={isLoadingValuation}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-xl hover:from-purple-600 hover:to-indigo-700 transition-all disabled:opacity-50"
          >
            {isLoadingValuation ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            Get AI Valuation Suggestion
          </button>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-gray-700 font-medium">Purchase Price (Rs.)</Label>
            <Input
              type="number"
              placeholder="Enter purchase price"
              className="h-12"
              {...register('purchase_price', { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-gray-700 font-medium">Brand New Price (Rs.)</Label>
            <Input
              type="number"
              placeholder="Enter brand new price"
              className="h-12"
              {...register('brand_new_price', { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-gray-700 font-medium">Market Value (Rs.) *</Label>
            <Input
              type="number"
              placeholder="Enter market value"
              className="h-12"
              {...register('market_value', { valueAsNumber: true, required: 'Market value is required' })}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-gray-700 font-medium">Forced Sale Value (Rs.)</Label>
            <Input
              type="number"
              placeholder="Enter forced sale value"
              className="h-12"
              {...register('forced_sale_value', { valueAsNumber: true })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-gray-700 font-medium">Valuation Summary</Label>
          <textarea
            rows={4}
            placeholder="By considering the above facts, the market value of the vehicle valued is Rs. ..."
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-none"
            {...register('valuation_summary')}
          />
        </div>
      </div>

      {/* Section 8: Office Use (Conditional) */}
      {isOfficeUse && (
        <div className="space-y-6">
          <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-800">For Office Use Only</h3>
              <p className="text-sm text-gray-500">Government and military vehicle details</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="text-gray-700 font-medium">Civil No</Label>
              <Input
                type="text"
                placeholder="Enter civil number"
                className="h-12"
                {...register('office_data.civil_no')}
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-700 font-medium">Military No</Label>
              <Input
                type="text"
                placeholder="Enter military number"
                className="h-12"
                {...register('office_data.military_no')}
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-700 font-medium">Approval Position</Label>
              <select
                className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 px-4"
                {...register('office_data.approval_position')}
              >
                <option value="">Select position</option>
                {APPROVAL_POSITIONS.map((pos) => (
                  <option key={pos} value={pos}>{pos}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Past Valuations Table */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-700">Previous Assessment</h4>
              <button
                type="button"
                onClick={addPastValuation}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Add Row
              </button>
            </div>

            {pastValuations.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="px-3 py-2 text-left font-medium text-gray-700">S/N</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Civil No</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Military No</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Year</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-700">Value (Rs.)</th>
                      <th className="px-3 py-2 text-left font-medium text-gray-700"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {pastValuations.map((row: any, index: number) => (
                      <tr key={index} className="border-b border-gray-100">
                        <td className="px-3 py-2">{index + 1}</td>
                        <td className="px-3 py-2">
                          <Input
                            type="text"
                            value={row.civil_no || ''}
                            onChange={(e) => updatePastValuation(index, 'civil_no', e.target.value)}
                            className="h-8 text-sm"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <Input
                            type="text"
                            value={row.military_no || ''}
                            onChange={(e) => updatePastValuation(index, 'military_no', e.target.value)}
                            className="h-8 text-sm"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <Input
                            type="number"
                            value={row.year || ''}
                            onChange={(e) => updatePastValuation(index, 'year', e.target.value)}
                            className="h-8 text-sm w-20"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <Input
                            type="number"
                            value={row.value || ''}
                            onChange={(e) => updatePastValuation(index, 'value', e.target.value)}
                            className="h-8 text-sm"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            onClick={() => removePastValuation(index)}
                            className="p-1 text-red-500 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {pastValuations.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                No previous assessments added. Click "Add Row" to add comparison vehicles.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VehicleFeaturesValuationStep;
