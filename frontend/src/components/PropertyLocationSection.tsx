import React, { useState, useEffect } from 'react';
import { MapPin, Building2, Navigation, Info } from 'lucide-react';
import { useAdministrativeDivisions, useDSDivisionsLocal } from '../hooks/useAdministrativeDivisions';
import { AutocompleteInput } from './AutocompleteInput';
import type { Report } from '../types';

interface Props {
  formData: Partial<Report>;
  updateFormData: (updates: Partial<Report>) => void;
  applicantAddress?: {
    line1?: string;
    line2?: string;
    district?: string;
    province?: string;
  };
}

export function PropertyLocationSection({ formData, updateFormData, applicantAddress }: Props) {
  const [useSameAddress, setUseSameAddress] = useState(formData.use_applicant_address_as_property || false);
  const { divisions, districts, loading: divisionsLoading } = useAdministrativeDivisions();
  const dsDivisions = useDSDivisionsLocal(divisions, formData.property_district);

  // Handle "same as applicant" toggle
  useEffect(() => {
    if (useSameAddress && applicantAddress) {
      // Copy applicant address to property
      updateFormData({
        use_applicant_address_as_property: true,
        property_district: applicantAddress.district,
        property_province: applicantAddress.province,
      });
    } else {
      updateFormData({
        use_applicant_address_as_property: false,
      });
    }
  }, [useSameAddress]);

  // Auto-calculate direction when location changes
  useEffect(() => {
    if (formData.property_latitude && formData.property_longitude && formData.property_district) {
      // This would call an API to calculate direction from town center
      // For now, we'll leave it as a manual field or implement later
    }
  }, [formData.property_latitude, formData.property_longitude]);

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center gap-2 pb-2 border-b">
        <MapPin className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Property Location & Situation</h3>
      </div>

      {/* Same as Applicant Address Toggle */}
      {applicantAddress && (applicantAddress.line1 || applicantAddress.district) ? (
        <div className="bg-blue-50 p-4 rounded-lg">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={useSameAddress}
              onChange={(e) => setUseSameAddress(e.target.checked)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span className="font-medium">Property address is same as applicant address</span>
          </label>
          {useSameAddress && (
            <div className="mt-2 text-sm text-gray-600">
              Using: {applicantAddress.line1}, {applicantAddress.district}
            </div>
          )}
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-amber-800">
              <span className="font-medium">Tip:</span> Fill in <strong>Applicant Information</strong> (Step 7) first, then you can return here and copy the applicant address to the property address with one click.
            </p>
          </div>
        </div>
      )}

      {/* Auto-filled Google Maps Data */}
      {formData.property_village && (
        <div className="bg-green-50 p-4 rounded-lg space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <Navigation className="w-4 h-4 text-green-600" />
            <h4 className="font-medium text-green-900">From Google Maps:</h4>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-600">Village:</span>
              <span className="ml-2 font-medium">{formData.property_village}</span>
            </div>
            <div>
              <span className="text-gray-600">District:</span>
              <span className="ml-2 font-medium">{formData.property_district}</span>
            </div>
            <div>
              <span className="text-gray-600">Province:</span>
              <span className="ml-2 font-medium">{formData.property_province}</span>
            </div>
            {formData.property_latitude && (
              <div>
                <span className="text-gray-600">GPS:</span>
                <span className="ml-2 font-medium text-xs">
                  {formData.property_latitude.toFixed(6)}, {formData.property_longitude?.toFixed(6)}
                </span>
              </div>
            )}
            {formData.location_direction && (
              <div>
                <span className="text-gray-600">Direction:</span>
                <span className="ml-2 font-medium capitalize">{formData.location_direction}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Location Fields (Basic) */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Village</label>
          <input
            type="text"
            value={formData.property_village || ''}
            onChange={(e) => updateFormData({ property_village: e.target.value })}
            placeholder="e.g., Hanhamunawa"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            District <span className="text-red-500">*</span>
          </label>
          <select
            value={formData.property_district || ''}
            onChange={(e) => updateFormData({
              property_district: e.target.value,
              property_divisional_secretariat: '', // Reset DS when district changes
            })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select District</option>
            {divisionsLoading ? (
              <option>Loading districts...</option>
            ) : (
              districts.map(district => (
                <option key={district} value={district}>{district}</option>
              ))
            )}
          </select>
        </div>
      </div>

      {/* Administrative Details Section */}
      <div className="border-t pt-6 space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <Building2 className="w-5 h-5 text-blue-600" />
          <h4 className="font-medium text-gray-900">Administrative Details</h4>
        </div>

        {/* Property Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Property Number
          </label>
          <input
            type="text"
            value={formData.property_number || ''}
            onChange={(e) => updateFormData({ property_number: e.target.value })}
            placeholder="e.g., No: 1202, No:717"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">Property identification number within the village</p>
        </div>

        {/* DS Division - Autocomplete with District dependency */}
        <AutocompleteInput
          label="Divisional Secretariat Division"
          value={formData.property_divisional_secretariat || ''}
          onChange={(value) => {
            // Extract DS division name without GN count
            const dsName = value.replace(/\s*\(\d+\s+GN\s+divisions\)$/i, '').trim();
            updateFormData({ property_divisional_secretariat: dsName });
          }}
          suggestions={!formData.property_district ? [] : dsDivisions.map(ds => `${ds.name} (${ds.gn_count} GN divisions)`)}
          placeholder={formData.property_district ? "Type to search or enter custom DS Division" : "Select District first"}
          allowCustom={true}
          className={!formData.property_district ? "opacity-50 pointer-events-none" : ""}
        />
        {formData.property_district && dsDivisions.length > 0 && (
          <p className="text-xs text-gray-500 mt-1">
            {dsDivisions.length} DS divisions available in {formData.property_district}
          </p>
        )}

        {/* GN Division - with autocomplete suggestions */}
        <AutocompleteInput
          label="Grama Niladari Division"
          value={formData.grama_niladari_division || ''}
          onChange={(value) => updateFormData({ grama_niladari_division: value })}
          suggestions={[]} // TODO: Populate with actual GN divisions when data is available
          placeholder="Enter GN Division name (e.g., Bamunna, Ihala Kotte)"
          allowCustom={true}
        />

        {/* Hathpaththuwa - with autocomplete */}
        <AutocompleteInput
          label="Hathpaththuwa"
          value={formData.hathpaththuwa || ''}
          onChange={(value) => updateFormData({ hathpaththuwa: value })}
          suggestions={[]} // TODO: Populate with Hathpaththuwa names per district if data becomes available
          placeholder="Enter Hathpaththuwa name"
          allowCustom={true}
        />

        {/* Korale - with autocomplete */}
        <AutocompleteInput
          label="Korale"
          value={formData.korale || ''}
          onChange={(value) => updateFormData({ korale: value })}
          suggestions={[]} // TODO: Populate with Korale names per district
          placeholder="e.g., Walgampattu Korale of Dewamedi Hatpattu"
          allowCustom={true}
        />

        {/* Pradeshiya Sabha - with autocomplete */}
        <AutocompleteInput
          label="Pradeshiya Sabha"
          value={formData.pradeshiya_sabha || ''}
          onChange={(value) => updateFormData({ pradeshiya_sabha: value })}
          suggestions={[]} // TODO: Populate with Pradeshiya Sabha names
          placeholder="e.g., Wariyapola Pradeshiya Sabha"
          allowCustom={true}
        />

        {/* Municipal Limit Checkbox */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.is_municipal_limit || false}
              onChange={(e) => updateFormData({
                is_municipal_limit: e.target.checked,
                ward_number: e.target.checked ? formData.ward_number : undefined,
              })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span className="font-medium">Property is within Municipal Council limit</span>
          </label>

          {/* Ward Number (conditional) */}
          {formData.is_municipal_limit && (
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ward Number
              </label>
              <input
                type="text"
                value={formData.ward_number || ''}
                onChange={(e) => updateFormData({ ward_number: e.target.value })}
                placeholder="e.g., Ward No: 10"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          )}
        </div>

        {/* Assessment Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Assessment Number <span className="text-gray-400 text-xs">(optional)</span>
          </label>
          <input
            type="text"
            value={formData.assessment_number || ''}
            onChange={(e) => updateFormData({ assessment_number: e.target.value })}
            placeholder="e.g., No:158/42A"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Property Name (optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Property Name <span className="text-gray-400 text-xs">(if any)</span>
          </label>
          <input
            type="text"
            value={formData.property_name || ''}
            onChange={(e) => updateFormData({ property_name: e.target.value })}
            placeholder="e.g., Sea Rock, Green Villa"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Helper Text */}
      <div className="bg-blue-50 p-3 rounded text-sm text-blue-800">
        <strong>Tip:</strong> Select the district first to see available DS Divisions in the dropdown.
        The system will use this data to generate professional property situation descriptions.
      </div>
    </div>
  );
}
