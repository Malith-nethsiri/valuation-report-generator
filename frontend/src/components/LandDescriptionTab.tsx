import React, { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { Sparkles } from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';
import { Label } from './Label';
import { PropertyPhotosSection } from './PropertyPhotosSection';
import { generateEnhancedLandDescription } from '../utils/landDescriptionGenerator';
import { authTokenStorage } from '../utils/secureStorage';
import { getCSRFToken } from '../utils/csrf';
import {
  LAND_SHAPES,
  LAND_TYPES,
  FRONTAGE_TYPES,
  LAND_LEVELS,
  SOIL_TYPES,
  FLOOD_RISK_OPTIONS,
  LAND_CONDITIONS,
  ELEVATION_CHANGES,
  DRAINAGE_PATTERNS,
  VEGETATION_TYPES,
  DEVELOPMENT_FEASIBILITY_TEMPLATES,
  OCCUPIER_RELATIONSHIPS,
} from '../constants/propertyDescriptionConstants';

interface LandDescriptionTabProps {
  register: any;
  errors: any;
  watch: any;
  setValue: any;
  isBareLand: boolean;
}

export const LandDescriptionTab: React.FC<LandDescriptionTabProps> = ({
  register,
  errors: _errors,
  watch,
  setValue,
  isBareLand,
}) => {
  const [isGeneratingDescription, setIsGeneratingDescription] = useState(false);

  // Watch form values for auto-generation
  const landShape = watch('land_shape');
  const landType = watch('land_type');
  const landFrontageType = watch('land_frontage_type');
  const landLevel = watch('land_level');
  const soilType = watch('soil_type');
  const waterTableDepth = watch('water_table_depth');
  const floodRisk = watch('flood_risk');
  const landCondition = watch('land_condition');

  // Generate professional land description using AI
  const generateLandDescription = useCallback(async () => {
    setIsGeneratingDescription(true);

    try {
      // Get authentication token
      const token = authTokenStorage.getToken();
      console.log('[LAND] Generate description - Auth token present:', !!token);

      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Prepare land data for API
      const landData = {
        land_shape: landShape,
        land_type: landType,
        land_level: landLevel,
        land_level_difference: watch('land_level_difference'),
        land_frontage_type: landFrontageType,
        land_frontage_width: watch('land_frontage_width'),
        land_frontage_description: watch('land_frontage_description'),
        soil_type: soilType,
        water_table_depth: waterTableDepth,
        flood_risk: floodRisk,
        land_condition: landCondition,
        elevation_changes: watch('elevation_changes'),
        drainage_pattern: watch('drainage_pattern'),
        vegetation_type: watch('vegetation_type'),
        natural_features: watch('natural_features'),
      };

      console.log('[LAND] Sending AI description generation request...');
      const csrfToken = getCSRFToken();
      const response = await fetch('/api/land/generate-description', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          ...(csrfToken && { 'X-CSRF-Token': csrfToken })
        },
        body: JSON.stringify(landData)
      });

      console.log('[LAND] Description response status:', response.status);

      if (response.status === 401) {
        console.error('[LAND] Token expired or invalid');
        throw new Error('Your session has expired. Please refresh the page and log in again.');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[LAND] AI generation failed:', errorData);
        throw new Error(errorData.detail || 'AI generation failed');
      }

      const result = await response.json();
      console.log('[LAND] Description generated successfully with AI');
      setValue('land_description_text', result.description);
      toast.success('Land description generated with AI!');

    } catch (err: any) {
      console.error('[LAND] Error generating with AI, falling back to template system:', err);
      toast.error('AI generation failed. Using template fallback.');

      // FALLBACK: Use template-based generation
      try {
        const fallbackDescription = generateEnhancedLandDescription({
          land_shape: landShape,
          land_type: landType,
          land_level: landLevel,
          land_level_difference: watch('land_level_difference'),
          land_frontage_type: landFrontageType,
          land_frontage_width: watch('land_frontage_width'),
          land_frontage_description: watch('land_frontage_description'),
          soil_type: soilType,
          water_table_depth: waterTableDepth,
          flood_risk: floodRisk,
          land_condition: landCondition,
          elevation_changes: watch('elevation_changes'),
          drainage_pattern: watch('drainage_pattern'),
          vegetation_type: watch('vegetation_type'),
          natural_features: watch('natural_features'),
        });
        setValue('land_description_text', fallbackDescription);
        console.log('[LAND] Template fallback successful');
      } catch (fallbackErr) {
        console.error('[LAND] Template fallback also failed:', fallbackErr);
        toast.error('Failed to generate description. Please try again.');
      }
    } finally {
      setIsGeneratingDescription(false);
    }
  }, [landShape, landType, landLevel, landFrontageType, soilType, waterTableDepth, floodRisk, landCondition, setValue, watch]);

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Land Characteristics</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Land Shape */}
        <div>
          <Label htmlFor="land_shape">Land Shape</Label>
          <select
            {...register('land_shape')}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">Select shape...</option>
            {LAND_SHAPES.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Land Type */}
        <div>
          <Label htmlFor="land_type">Land Type</Label>
          <select
            {...register('land_type')}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">Select type...</option>
            {LAND_TYPES.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Frontage Type */}
        <div>
          <Label htmlFor="land_frontage_type">Road Frontage Type</Label>
          <select
            {...register('land_frontage_type')}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">Select frontage...</option>
            {FRONTAGE_TYPES.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Frontage Width */}
        <div>
          <Label htmlFor="land_frontage_width">Frontage Width (meters)</Label>
          <Input
            type="number"
            step="0.01"
            {...register('land_frontage_width', { valueAsNumber: true })}
            placeholder="e.g., 6.0"
          />
        </div>

        {/* Land Level */}
        <div>
          <Label htmlFor="land_level">Land Level</Label>
          <select
            {...register('land_level')}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">Select level...</option>
            {LAND_LEVELS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Level Difference */}
        <div>
          <Label htmlFor="land_level_difference">Level Difference (feet)</Label>
          <Input
            type="number"
            step="0.5"
            {...register('land_level_difference', { valueAsNumber: true })}
            placeholder="e.g., 1.5"
          />
        </div>

        {/* Soil Type */}
        <div>
          <Label htmlFor="soil_type">Soil Type</Label>
          <select
            {...register('soil_type')}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">Select soil type...</option>
            {SOIL_TYPES.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Water Table Depth */}
        <div>
          <Label htmlFor="water_table_depth">Water Table Depth (feet)</Label>
          <Input
            type="number"
            step="1"
            {...register('water_table_depth', { valueAsNumber: true })}
            placeholder="e.g., 15"
          />
        </div>

        {/* Flood Risk */}
        <div>
          <Label htmlFor="flood_risk">Flood Risk</Label>
          <select
            {...register('flood_risk')}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">Select flood risk...</option>
            {FLOOD_RISK_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {/* Land Condition */}
        <div>
          <Label htmlFor="land_condition">Land Condition</Label>
          <select
            {...register('land_condition')}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">Select condition...</option>
            {LAND_CONDITIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Topographical Features Section */}
      <div className="space-y-2 pt-4 border-t border-gray-200">
        <h4 className="text-md font-semibold text-gray-800 mb-3">Topographical Features</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Elevation Changes */}
          <div>
            <Label htmlFor="elevation_changes">Elevation Changes</Label>
            <select
              {...register('elevation_changes')}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Select elevation pattern...</option>
              {ELEVATION_CHANGES.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Drainage Pattern */}
          <div>
            <Label htmlFor="drainage_pattern">Drainage Pattern</Label>
            <select
              {...register('drainage_pattern')}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Select drainage pattern...</option>
              {DRAINAGE_PATTERNS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Vegetation Type */}
          <div>
            <Label htmlFor="vegetation_type">Vegetation Type</Label>
            <select
              {...register('vegetation_type')}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Select vegetation type...</option>
              {VEGETATION_TYPES.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Natural Features */}
        <div className="pt-2">
          <Label htmlFor="natural_features">Natural Features (Optional)</Label>
          <textarea
            {...register('natural_features')}
            rows={2}
            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            placeholder="e.g., Natural stream along eastern boundary, rock outcroppings on northern section, seasonal pond in southwest corner"
          />
          <p className="text-xs text-gray-500 mt-1">Describe any notable natural features like streams, ponds, rock formations, etc.</p>
        </div>
      </div>

      {/* Additional Description */}
      <div>
        <Label htmlFor="land_frontage_description">Additional Frontage Description</Label>
        <textarea
          {...register('land_frontage_description')}
          rows={2}
          className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          placeholder="Additional details about the road frontage..."
        />
      </div>

      {/* Auto-generated Description */}
      <div className="bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl p-4 border border-emerald-200">
        <div className="flex items-center justify-between mb-3">
          <Label htmlFor="land_description_text" className="text-emerald-800 font-semibold">
            Professional Land Description
          </Label>
          <Button
            type="button"
            onClick={generateLandDescription}
            disabled={isGeneratingDescription}
            className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            {isGeneratingDescription ? 'Generating...' : 'Auto-Generate'}
          </Button>
        </div>
        <textarea
          {...register('land_description_text')}
          rows={4}
          className="w-full px-4 py-3 bg-white border border-emerald-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          placeholder="Description will be auto-generated based on the fields above, or you can write manually..."
        />
        <p className="text-xs text-emerald-600 mt-2">
          This text will appear in the final report. You can edit it after auto-generation.
        </p>
      </div>

      {/* Occupier Information - For all property types */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-3">Occupier Information</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="occupier_name">Occupier Name</Label>
            <Input
              {...register('occupier_name')}
              placeholder="Enter occupier name"
            />
          </div>
          <div>
            <Label htmlFor="occupier_relationship">Relationship</Label>
            <select
              {...register('occupier_relationship')}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select relationship...</option>
              {OCCUPIER_RELATIONSHIPS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
        <p className="text-xs text-blue-600 mt-2">
          This information will appear in the Land Description section of the report
        </p>
      </div>

      {/* Development Feasibility / Ongoing Construction (for bare land) */}
      {isBareLand && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-200">
          <Label htmlFor="ongoing_construction_notes" className="text-amber-800 font-semibold">
            Development Feasibility / Ongoing Construction
            <span className="text-gray-500 text-sm ml-2 font-normal">(Optional - for bare land or development sites)</span>
          </Label>

          {/* Template Selector */}
          <div className="mt-3 mb-2">
            <select
              className="w-full px-3 py-2 text-sm bg-white border border-amber-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
              onChange={(e) => {
                const selectedTemplate = DEVELOPMENT_FEASIBILITY_TEMPLATES.find(
                  t => t.value === e.target.value
                );
                if (selectedTemplate && selectedTemplate.text) {
                  // Directly set the template text without confirmation
                  setValue('ongoing_construction_notes', selectedTemplate.text);
                  // Reset dropdown to default
                  e.target.value = '';
                }
              }}
            >
              {DEVELOPMENT_FEASIBILITY_TEMPLATES.map(template => (
                <option key={template.value} value={template.value}>
                  {template.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-amber-700 mt-1">
              Select a template to quickly fill in common development notes (you can edit after)
            </p>
          </div>

          <textarea
            {...register('ongoing_construction_notes')}
            rows={3}
            maxLength={2000}
            className="w-full px-4 py-3 bg-white border border-amber-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
            placeholder="Describe any ongoing construction, planned development, infrastructure readiness, or suitability for future building..."
          />
          <p className="text-xs text-amber-600 mt-2">
            Note any construction in progress, development plans, infrastructure availability, or development potential. Appears in bare land reports.
          </p>
        </div>
      )}

      {/* Property Photos (for bare land only) */}
      {isBareLand && (
        <PropertyPhotosSection watch={watch} setValue={setValue} />
      )}

    </div>
  );
};

export default LandDescriptionTab;
