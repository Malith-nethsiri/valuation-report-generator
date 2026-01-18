import React from 'react';
import { UseFormReturn } from 'react-hook-form';
import { Home, MapPin, Ruler, FileText } from 'lucide-react';
import { Input } from './Input';
import { Label } from './Label';
import { DatePicker } from './DatePicker';
import { MultiPropertyFormData } from './MultiPropertyStepForm';

interface PropertyDetailsStepProps {
  propertyIndex: number;
  formMethods: UseFormReturn<MultiPropertyFormData>;
  isEditMode: boolean;
}

const PropertyDetailsStep: React.FC<PropertyDetailsStepProps> = ({
  propertyIndex,
  formMethods,
  isEditMode,
}) => {
  const { register, watch, setValue, formState: { errors } } = formMethods;

  // Field prefix for this property
  const fieldPrefix = `properties.${propertyIndex}`;

  return (
    <div className="space-y-8">
      {/* Property Identification Section */}
      <div className="bg-gradient-to-r from-blue-50 to-cyan-100 rounded-2xl p-6">
        <div className="flex items-center mb-4">
          <Home className="h-6 w-6 text-blue-600 mr-3" />
          <h4 className="text-lg font-bold text-gray-900">Property Identification</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <Label htmlFor={`${fieldPrefix}.lot_number`}>
              Lot Number
            </Label>
            <Input
              {...register(`${fieldPrefix}.lot_number` as any)}
              placeholder="e.g., Lot 15, Lots 1 & 2"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.plan_number`}>Plan Number</Label>
            <Input
              {...register(`${fieldPrefix}.plan_number` as any)}
              placeholder="Plan number"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.plan_date`}>Plan Date</Label>
            <DatePicker
              id={`${fieldPrefix}.plan_date`}
              value={watch(`${fieldPrefix}.plan_date` as any) || ''}
              onChange={(date) => setValue(`${fieldPrefix}.plan_date` as any, date)}
              placeholder="DD-MM-YYYY"
            />
          </div>

          <div className="md:col-span-2">
            <Label htmlFor={`${fieldPrefix}.licensed_surveyor_name`}>
              Licensed Surveyor Name
            </Label>
            <Input
              {...register(`${fieldPrefix}.licensed_surveyor_name` as any)}
              placeholder="Surveyor name"
            />
          </div>
        </div>
      </div>

      {/* Property Location Section */}
      <div className="bg-gradient-to-r from-emerald-50 to-green-100 rounded-2xl p-6">
        <div className="flex items-center mb-4">
          <MapPin className="h-6 w-6 text-emerald-600 mr-3" />
          <h4 className="text-lg font-bold text-gray-900">Property Location</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor={`${fieldPrefix}.property_village`}>Village/City *</Label>
            <Input
              {...register(`${fieldPrefix}.property_village` as any)}
              placeholder="Enter village name"
              required
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.property_district`}>District *</Label>
            <Input
              {...register(`${fieldPrefix}.property_district` as any)}
              placeholder="e.g., Colombo"
              required
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.property_province`}>Province</Label>
            <Input
              {...register(`${fieldPrefix}.property_province` as any)}
              placeholder="e.g., Western"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.grama_niladari_division`}>
              Grama Niladari Division
            </Label>
            <Input
              {...register(`${fieldPrefix}.grama_niladari_division` as any)}
              placeholder="Enter GN Division name"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.property_number`}>Property Number</Label>
            <Input
              {...register(`${fieldPrefix}.property_number` as any)}
              placeholder="Enter property number"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.korale`}>Korale</Label>
            <Input
              {...register(`${fieldPrefix}.korale` as any)}
              placeholder="Enter Korale name"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.pradeshiya_sabha`}>Pradeshiya Sabha</Label>
            <Input
              {...register(`${fieldPrefix}.pradeshiya_sabha` as any)}
              placeholder="Enter Pradeshiya Sabha name"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.property_latitude`}>Latitude</Label>
            <Input
              type="number"
              step="0.000001"
              {...register(`${fieldPrefix}.property_latitude` as any, { valueAsNumber: true })}
              placeholder="6.9271"
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.property_longitude`}>Longitude</Label>
            <Input
              type="number"
              step="0.000001"
              {...register(`${fieldPrefix}.property_longitude` as any, { valueAsNumber: true })}
              placeholder="79.8612"
            />
          </div>
        </div>
      </div>

      {/* Land Extent Section */}
      <div className="bg-gradient-to-r from-violet-50 to-purple-100 rounded-2xl p-6">
        <div className="flex items-center mb-4">
          <Ruler className="h-6 w-6 text-violet-600 mr-3" />
          <h4 className="text-lg font-bold text-gray-900">Land Extent</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label htmlFor={`${fieldPrefix}.land_extent_acres`}>Acres</Label>
            <Input
              type="number"
              step="0.01"
              {...register(`${fieldPrefix}.land_extent_acres` as any, { valueAsNumber: true })}
              placeholder="0"
              min={0}
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.land_extent_roods`}>Roods</Label>
            <Input
              type="number"
              {...register(`${fieldPrefix}.land_extent_roods` as any, { valueAsNumber: true })}
              placeholder="0"
              min={0}
              max={3}
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.land_extent_perches`}>Perches</Label>
            <Input
              type="number"
              step="0.01"
              {...register(`${fieldPrefix}.land_extent_perches` as any, { valueAsNumber: true })}
              placeholder="0"
              min={0}
              max={40}
            />
          </div>

          <div className="md:col-span-3">
            <Label htmlFor={`${fieldPrefix}.land_extent_formatted`}>
              Formatted Land Extent
            </Label>
            <Input
              {...register(`${fieldPrefix}.land_extent_formatted` as any)}
              placeholder="e.g., 1A 2R 15P"
            />
            <p className="text-xs text-gray-500 mt-1">
              This will be auto-calculated from acres, roods, and perches
            </p>
          </div>
        </div>
      </div>

      {/* Property Description Section */}
      <div className="bg-gradient-to-r from-orange-50 to-red-100 rounded-2xl p-6">
        <div className="flex items-center mb-4">
          <FileText className="h-6 w-6 text-orange-600 mr-3" />
          <h4 className="text-lg font-bold text-gray-900">Property Description</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor={`${fieldPrefix}.land_shape`}>Land Shape</Label>
            <select
              {...register(`${fieldPrefix}.land_shape` as any)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            >
              <option value="">Select shape</option>
              <option value="Regular">Regular</option>
              <option value="Irregular">Irregular</option>
              <option value="Rectangular">Rectangular</option>
              <option value="Square">Square</option>
            </select>
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.land_type`}>Land Type</Label>
            <select
              {...register(`${fieldPrefix}.land_type` as any)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            >
              <option value="">Select type</option>
              <option value="Bare Land">Bare Land</option>
              <option value="Built-up">Built-up</option>
              <option value="Agricultural">Agricultural</option>
              <option value="Commercial">Commercial</option>
            </select>
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.land_level`}>Land Level</Label>
            <select
              {...register(`${fieldPrefix}.land_level` as any)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
            >
              <option value="">Select level</option>
              <option value="Level">Level</option>
              <option value="Sloping">Sloping</option>
              <option value="Undulating">Undulating</option>
            </select>
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.soil_type`}>Soil Type</Label>
            <Input
              {...register(`${fieldPrefix}.soil_type` as any)}
              placeholder="e.g., Clay, Sandy"
            />
          </div>

          <div className="md:col-span-2">
            <Label htmlFor={`${fieldPrefix}.land_description_text`}>
              Additional Description
            </Label>
            <textarea
              {...register(`${fieldPrefix}.land_description_text` as any)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              rows={3}
              placeholder="Additional property description..."
            />
          </div>
        </div>
      </div>

      {/* Valuation Section */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-100 rounded-2xl p-6">
        <div className="flex items-center mb-4">
          <FileText className="h-6 w-6 text-indigo-600 mr-3" />
          <h4 className="text-lg font-bold text-gray-900">Valuation</h4>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor={`${fieldPrefix}.valuation_rate_per_perch`}>
              Rate per Perch (LKR)
            </Label>
            <Input
              type="number"
              step="0.01"
              {...register(`${fieldPrefix}.valuation_rate_per_perch` as any, { valueAsNumber: true })}
              placeholder="0.00"
              min={0}
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.valuation_total_land_value`}>
              Total Land Value (LKR)
            </Label>
            <Input
              type="number"
              step="0.01"
              {...register(`${fieldPrefix}.valuation_total_land_value` as any, { valueAsNumber: true })}
              placeholder="0.00"
              min={0}
            />
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.valuation_market_value`}>
              Market Value (LKR) *
            </Label>
            <Input
              type="number"
              step="0.01"
              {...register(`${fieldPrefix}.valuation_market_value` as any, { valueAsNumber: true })}
              placeholder="0.00"
              min={0}
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              This value will be used in the total valuation calculation
            </p>
          </div>

          <div>
            <Label htmlFor={`${fieldPrefix}.valuation_forced_sale_value`}>
              Forced Sale Value (LKR)
            </Label>
            <Input
              type="number"
              step="0.01"
              {...register(`${fieldPrefix}.valuation_forced_sale_value` as any, { valueAsNumber: true })}
              placeholder="0.00"
              min={0}
            />
          </div>

          <div className="md:col-span-2">
            <Label htmlFor={`${fieldPrefix}.land_market_analysis`}>
              Market Analysis Notes
            </Label>
            <textarea
              {...register(`${fieldPrefix}.land_market_analysis` as any)}
              className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              rows={3}
              placeholder="Market analysis, comparable properties, etc..."
            />
          </div>
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 rounded-xl p-4">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Note:</span> Only essential fields are shown here for quick entry.
          For detailed property information (boundaries, buildings, legal aspects), you can edit the property
          after report creation or use the Property Library for frequently valued properties.
        </p>
      </div>
    </div>
  );
};

export default PropertyDetailsStep;
