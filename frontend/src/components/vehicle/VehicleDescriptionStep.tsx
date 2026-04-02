/**
 * VehicleDescriptionStep - Step 4 of Vehicle Report Form
 *
 * Vehicle identification and condition assessment:
 * - Registration details (OCR auto-filled)
 * - Make, model, year
 * - Engine and transmission details
 * - Condition assessments using rating chips
 * - Parts availability status
 */

import React from 'react';
import { useFormContext, Controller } from 'react-hook-form';
import {
  Car,
  Settings,
  Wrench,
  FileText,
  Gauge,
  Fuel,
  Calendar,
  MapPin,
  Hash,
  Globe,
  Palette,
} from 'lucide-react';
import { Input } from '../Input';
import { Label } from '../Label';
import { ConditionRatingChips } from './ConditionRatingChips';
import {
  PROVINCIAL_COUNCILS,
  VEHICLE_CLASSES,
  FUEL_TYPES,
  TRANSMISSION_TYPES,
  CONDITION_RATINGS,
  PARTS_STATUS_OPTIONS,
  CLUTCH_STATUS_OPTIONS,
  DIFFERENTIAL_STATUS_OPTIONS,
  GEAR_SELECTION_OPTIONS,
  VEHICLE_STATUS_OPTIONS,
  VEHICLE_TYPES,
} from '../../types';

// Common vehicle makes
const VEHICLE_MAKES = [
  'Toyota',
  'Honda',
  'Nissan',
  'Suzuki',
  'Mitsubishi',
  'Mazda',
  'Hyundai',
  'Kia',
  'Isuzu',
  'Tata',
  'Mahindra',
  'BMW',
  'Mercedes-Benz',
  'Audi',
  'Volkswagen',
  'Ford',
  'Chevrolet',
  'Peugeot',
  'Renault',
  'Other'
];

// Body colors
const BODY_COLORS = [
  'White',
  'Black',
  'Silver',
  'Grey',
  'Red',
  'Blue',
  'Green',
  'Brown',
  'Beige',
  'Gold',
  'Orange',
  'Yellow',
  'Other'
];

// Wheel drive options
const WHEEL_DRIVE_OPTIONS = ['2WD', '4WD', 'AWD'];

export const VehicleDescriptionStep: React.FC = () => {
  const { register, control, formState: { errors }, watch } = useFormContext();

  return (
    <div className="space-y-8">
      {/* Section 1: Vehicle Identification */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
            <Car className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Vehicle Identification</h3>
            <p className="text-sm text-gray-500">Registration and basic details</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Vehicle Type */}
          <div className="space-y-2">
            <Label htmlFor="vehicle_type" className="text-gray-700 font-medium">
              Vehicle Type
            </Label>
            <select
              id="vehicle_type"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('vehicle_type')}
            >
              <option value="">Select type</option>
              {VEHICLE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Registration Number */}
          <div className="space-y-2">
            <Label htmlFor="registration_number" className="text-gray-700 font-medium flex items-center gap-2">
              <Hash className="w-4 h-4" />
              Registration Number *
            </Label>
            <Input
              id="registration_number"
              type="text"
              placeholder="e.g., WP CAB-1234"
              className="h-12"
              {...register('registration_number', { required: 'Registration number is required' })}
            />
            {errors.registration_number && (
              <p className="text-red-500 text-sm">{errors.registration_number.message as string}</p>
            )}
          </div>

          {/* Provincial Council */}
          <div className="space-y-2">
            <Label htmlFor="provincial_council" className="text-gray-700 font-medium flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              Provincial Council
            </Label>
            <select
              id="provincial_council"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('provincial_council')}
            >
              <option value="">Select province</option>
              {PROVINCIAL_COUNCILS.map((province) => (
                <option key={province} value={province}>{province}</option>
              ))}
            </select>
          </div>

          {/* Class of Vehicle */}
          <div className="space-y-2">
            <Label htmlFor="class_of_vehicle" className="text-gray-700 font-medium">
              Class of Vehicle
            </Label>
            <select
              id="class_of_vehicle"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('class_of_vehicle')}
            >
              <option value="">Select class</option>
              {VEHICLE_CLASSES.map((cls) => (
                <option key={cls} value={cls}>{cls}</option>
              ))}
            </select>
          </div>

          {/* Make */}
          <div className="space-y-2">
            <Label htmlFor="make" className="text-gray-700 font-medium">
              Make *
            </Label>
            <select
              id="make"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('make', { required: 'Make is required' })}
            >
              <option value="">Select make</option>
              {VEHICLE_MAKES.map((make) => (
                <option key={make} value={make}>{make}</option>
              ))}
            </select>
            {errors.make && (
              <p className="text-red-500 text-sm">{errors.make.message as string}</p>
            )}
          </div>

          {/* Model */}
          <div className="space-y-2">
            <Label htmlFor="model" className="text-gray-700 font-medium">
              Model
            </Label>
            <Input
              id="model"
              type="text"
              placeholder="e.g., Corolla, Civic"
              className="h-12"
              {...register('model')}
            />
          </div>

          {/* Variant / Grade */}
          <div className="space-y-2">
            <Label htmlFor="variant">
              Variant / Grade <span className="text-gray-400 font-normal text-xs">(optional)</span>
            </Label>
            <Input
              id="variant"
              type="text"
              placeholder="e.g. G grade, X grade, S, Sport"
              className="h-12"
              {...register('variant')}
            />
            <p className="text-xs text-gray-500">
              Specifying the trim level helps identify exact specifications.
            </p>
          </div>

          {/* Year of Manufacture */}
          <div className="space-y-2">
            <Label htmlFor="year_of_manufacture" className="text-gray-700 font-medium flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Year of Manufacture
            </Label>
            <Input
              id="year_of_manufacture"
              type="number"
              min="1900"
              max={new Date().getFullYear() + 1}
              placeholder="e.g., 2020"
              className="h-12"
              {...register('year_of_manufacture', { valueAsNumber: true })}
            />
          </div>

          {/* Date of First Registration */}
          <div className="space-y-2">
            <Label htmlFor="date_of_first_registration" className="text-gray-700 font-medium">
              Date of First Registration
            </Label>
            <Input
              id="date_of_first_registration"
              type="text"
              placeholder="DD/MM/YYYY"
              className="h-12"
              {...register('date_of_first_registration')}
            />
          </div>

          {/* Body Colour */}
          <div className="space-y-2">
            <Label htmlFor="body_colour" className="text-gray-700 font-medium flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Body Colour
            </Label>
            <select
              id="body_colour"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('body_colour')}
            >
              <option value="">Select colour</option>
              {BODY_COLORS.map((color) => (
                <option key={color} value={color}>{color}</option>
              ))}
            </select>
          </div>

          {/* Chassis Number */}
          <div className="space-y-2">
            <Label htmlFor="chassis_number" className="text-gray-700 font-medium">
              Chassis Number
            </Label>
            <Input
              id="chassis_number"
              type="text"
              placeholder="Enter chassis number"
              className="h-12 font-mono"
              {...register('chassis_number')}
            />
          </div>

          {/* Engine Number */}
          <div className="space-y-2">
            <Label htmlFor="engine_number" className="text-gray-700 font-medium">
              Engine Number
            </Label>
            <Input
              id="engine_number"
              type="text"
              placeholder="Enter engine number"
              className="h-12 font-mono"
              {...register('engine_number')}
            />
          </div>

          {/* Vehicle Status */}
          <div className="space-y-2">
            <Label htmlFor="vehicle_status" className="text-gray-700 font-medium flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Vehicle Status
            </Label>
            <select
              id="vehicle_status"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('vehicle_status')}
            >
              <option value="">Select status</option>
              {VEHICLE_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Country of Origin */}
          <div className="space-y-2">
            <Label htmlFor="country_of_origin" className="text-gray-700 font-medium flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Country of Origin
            </Label>
            <Input
              id="country_of_origin"
              type="text"
              placeholder="e.g., Japan, India"
              className="h-12"
              {...register('country_of_origin')}
            />
          </div>

          {/* Cylinder Capacity */}
          <div className="space-y-2">
            <Label htmlFor="cylinder_capacity" className="text-gray-700 font-medium">
              Cylinder Capacity (cc)
            </Label>
            <Input
              id="cylinder_capacity"
              type="number"
              placeholder="e.g., 1500"
              className="h-12"
              {...register('cylinder_capacity', { valueAsNumber: true })}
            />
          </div>

          {/* Fuel Type */}
          <div className="space-y-2">
            <Label htmlFor="fuel_type" className="text-gray-700 font-medium flex items-center gap-2">
              <Fuel className="w-4 h-4" />
              Fuel Type
            </Label>
            <select
              id="fuel_type"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('fuel_type')}
            >
              <option value="">Select fuel type</option>
              {FUEL_TYPES.map((fuel) => (
                <option key={fuel} value={fuel}>{fuel}</option>
              ))}
            </select>
          </div>

          {/* Mileage */}
          <div className="space-y-2">
            <Label htmlFor="mileage" className="text-gray-700 font-medium flex items-center gap-2">
              <Gauge className="w-4 h-4" />
              Mileage
            </Label>
            <div className="flex gap-2">
              <Input
                id="mileage"
                type="number"
                placeholder="e.g., 50000"
                className="h-12 flex-1"
                {...register('mileage', { valueAsNumber: true })}
              />
              <select
                className="w-24 h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-3"
                {...register('mileage_unit')}
              >
                <option value="km">km</option>
                <option value="miles">miles</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Section 2: Engine & Transmission */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
            <Settings className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Engine & Transmission</h3>
            <p className="text-sm text-gray-500">Mechanical specifications</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Engine Type */}
          <div className="space-y-2">
            <Label htmlFor="engine_type" className="text-gray-700 font-medium">
              Engine Type
            </Label>
            <Input
              id="engine_type"
              type="text"
              placeholder="e.g., Inline-4, V6"
              className="h-12"
              {...register('engine_type')}
            />
          </div>

          {/* Transmission */}
          <div className="space-y-2">
            <Label htmlFor="transmission" className="text-gray-700 font-medium">
              Transmission
            </Label>
            <select
              id="transmission"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('transmission')}
            >
              <option value="">Select transmission</option>
              {TRANSMISSION_TYPES.map((trans) => (
                <option key={trans} value={trans}>{trans}</option>
              ))}
            </select>
          </div>

          {/* Wheel Drive */}
          <div className="space-y-2">
            <Label htmlFor="wheel_drive" className="text-gray-700 font-medium">
              Wheel Drive
            </Label>
            <select
              id="wheel_drive"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('wheel_drive')}
            >
              <option value="">Select drive type</option>
              {WHEEL_DRIVE_OPTIONS.map((wd) => (
                <option key={wd} value={wd}>{wd}</option>
              ))}
            </select>
          </div>

          {/* Clutch Status */}
          <div className="space-y-2">
            <Label htmlFor="clutch_status" className="text-gray-700 font-medium">
              Clutch Status
            </Label>
            <select
              id="clutch_status"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('clutch_status')}
            >
              <option value="">Select status</option>
              {CLUTCH_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Differential Status */}
          <div className="space-y-2">
            <Label htmlFor="differential_status" className="text-gray-700 font-medium">
              Differential Status
            </Label>
            <select
              id="differential_status"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('differential_status')}
            >
              <option value="">Select status</option>
              {DIFFERENTIAL_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Gear Selection */}
          <div className="space-y-2">
            <Label htmlFor="gear_selection" className="text-gray-700 font-medium">
              Gear Selection
            </Label>
            <select
              id="gear_selection"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('gear_selection')}
            >
              <option value="">Select condition</option>
              {GEAR_SELECTION_OPTIONS.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Section 3: Condition Assessment */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
            <Wrench className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Condition Assessment</h3>
            <p className="text-sm text-gray-500">Rate the condition of various components</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Running Condition */}
          <Controller
            name="running_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="running_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Running Condition"
              />
            )}
          />

          {/* Engine Condition */}
          <Controller
            name="engine_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="engine_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Engine Condition"
              />
            )}
          />

          {/* Gear Box Condition */}
          <Controller
            name="gear_box_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="gear_box_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Gear Box Condition"
              />
            )}
          />

          {/* Body Condition */}
          <Controller
            name="body_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="body_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Body Condition"
              />
            )}
          />

          {/* Chassis Condition */}
          <Controller
            name="chassis_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="chassis_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Chassis Condition"
              />
            )}
          />

          {/* Upholstery Condition */}
          <Controller
            name="upholstery_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="upholstery_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Upholstery Condition"
              />
            )}
          />

          {/* Underside Condition */}
          <Controller
            name="underside_condition"
            control={control}
            render={({ field }) => (
              <ConditionRatingChips
                name="underside_condition"
                value={field.value || ''}
                onChange={field.onChange}
                label="Underside Condition"
              />
            )}
          />
        </div>
      </div>

      {/* Section 4: Parts Availability */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
            <Settings className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Parts Availability</h3>
            <p className="text-sm text-gray-500">Availability of replacement parts</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Body Parts Status */}
          <div className="space-y-2">
            <Label htmlFor="body_parts_status" className="text-gray-700 font-medium">
              Body Parts
            </Label>
            <select
              id="body_parts_status"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('body_parts_status')}
            >
              <option value="">Select availability</option>
              {PARTS_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Engine Parts Status */}
          <div className="space-y-2">
            <Label htmlFor="engine_parts_status" className="text-gray-700 font-medium">
              Engine Parts
            </Label>
            <select
              id="engine_parts_status"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('engine_parts_status')}
            >
              <option value="">Select availability</option>
              {PARTS_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Accessories Status */}
          <div className="space-y-2">
            <Label htmlFor="accessories_status" className="text-gray-700 font-medium">
              Accessories
            </Label>
            <select
              id="accessories_status"
              className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
              {...register('accessories_status')}
            >
              <option value="">Select availability</option>
              {PARTS_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Fuel Consumption */}
      <div className="space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-gray-200">
          <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center">
            <Fuel className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-800">Fuel Performance</h3>
            <p className="text-sm text-gray-500">Average fuel consumption</p>
          </div>
        </div>

        <div className="flex gap-2 max-w-md">
          <Input
            id="fuel_consumption"
            type="number"
            step="0.1"
            placeholder="e.g., 12.5"
            className="h-12 flex-1"
            {...register('fuel_consumption', { valueAsNumber: true })}
          />
          <select
            className="w-32 h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-3"
            {...register('fuel_consumption_unit')}
          >
            <option value="km/L">km/L</option>
            <option value="L/100km">L/100km</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default VehicleDescriptionStep;
