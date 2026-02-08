import React, { useState, useEffect } from 'react';
import { Route, MapIcon, Navigation2, Loader2 } from 'lucide-react';
import type { Report, RoadCondition } from '../types';
import { GooglePlacesAutocomplete } from './GooglePlacesAutocomplete';
import { RoadConditionsSummary } from './RoadConditionsSummary';
import { api } from '../services/api';

interface Props {
  formData: Partial<Report>;
  updateFormData: (updates: Partial<Report>) => void;
}

interface RouteStep {
  instruction: string;
  distance: string;
  duration: string;
  maneuver?: string;
}

interface RouteData {
  distance_km: number;
  distance_text: string;
  duration_minutes: number;
  duration_text: string;
  polyline: string;
  steps: RouteStep[];
}

export function AccessDirectionsSection({ formData, updateFormData }: Props) {
  const [generating, setGenerating] = useState(false);
  const [generatingText, setGeneratingText] = useState(false);
  const [routeData, setRouteData] = useState<RouteData | null>(null);
  const [roadConditions, setRoadConditions] = useState<RoadCondition[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [useManualCoordinates, setUseManualCoordinates] = useState(false);

  // Auto-generate professional text when road conditions change
  useEffect(() => {
    if (routeData && roadConditions.length > 0 && formData.access_starting_point_name) {
      generateProfessionalText();
    }
  }, [roadConditions]);

  async function generateDirections() {
    // Validation
    if (!formData.access_starting_point_latitude || !formData.property_latitude) {
      setError('Please select both starting point and property location first');
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      // Call directions API
      const directionsResponse = await api.post('/api/maps/directions', {
        origin_lat: formData.access_starting_point_latitude,
        origin_lng: formData.access_starting_point_longitude,
        dest_lat: formData.property_latitude,
        dest_lng: formData.property_longitude,
      });

      const data = directionsResponse.data;
      setRouteData(data);

      // Generate static map with route
      try {
        const mapResponse = await api.post('/api/maps/static-map', {
          origin_lat: formData.access_starting_point_latitude,
          origin_lng: formData.access_starting_point_longitude,
          dest_lat: formData.property_latitude,
          dest_lng: formData.property_longitude,
          polyline: data.polyline,
        });

        // Update form with route data (no professional text yet - waiting for road conditions)
        updateFormData({
          access_distance_km: data.distance_km,
          access_duration_minutes: data.duration_minutes,
          access_route_data: data,
          location_map_image_data: mapResponse.data.map_url,
        });
      } catch (mapError) {
        console.error('Map generation failed:', mapError);
        // Still update route data even if map fails
        updateFormData({
          access_distance_km: data.distance_km,
          access_duration_minutes: data.duration_minutes,
          access_route_data: data,
        });
      }

    } catch (err: any) {
      console.error('Failed to generate directions:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to generate directions');
    } finally {
      setGenerating(false);
    }
  }

  // Generate professional text from route data + road conditions
  async function generateProfessionalText() {
    if (!formData.access_starting_point_name || !routeData) {
      return;
    }

    setGeneratingText(true);

    try {
      const response = await api.post('/api/maps/transform-access', {
        starting_point_name: formData.access_starting_point_name,
        property_position: formData.property_road_position || 'right side',
        total_distance_km: routeData.distance_km,
        total_duration_mins: routeData.duration_minutes,
        steps: routeData.steps,
        road_conditions: roadConditions,  // NEW: Send simplified road conditions
      });

      const professionalText = response.data.professional_text;

      // Update form with professional text and road conditions
      updateFormData({
        access_directions_text: professionalText,
        access_road_conditions: roadConditions,
      });

    } catch (err: any) {
      console.error('Failed to generate professional text:', err);
      // Use fallback if AI fails
      const fallbackText = generateFallbackText();
      updateFormData({
        access_directions_text: fallbackText,
        access_road_conditions: roadConditions,
      });
    } finally {
      setGeneratingText(false);
    }
  }

  // Fallback text generation
  function generateFallbackText(): string {
    if (!formData.access_starting_point_name || !routeData) {
      return '';
    }

    const startPoint = formData.access_starting_point_name;
    const distance = routeData.distance_text;
    const position = formData.property_road_position || 'right side';

    return `From ${startPoint}, proceed along the route for a distance of approximately ${distance} to reach the property on ${position} of the road fronting same.`;
  }

  // Clean HTML tags from instructions
  function cleanInstruction(html: string): string {
    return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ');
  }

  // Handle road conditions change
  function handleRoadConditionsChange(conditions: RoadCondition[]) {
    setRoadConditions(conditions);
    // Auto-generation happens via useEffect
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center gap-2 pb-2 border-b">
        <Route className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Access & Directions</h3>
      </div>

      {/* Starting Point Input with Google Places Autocomplete */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-gray-700">
            Starting Point <span className="text-red-500">*</span>
          </label>
          <button
            type="button"
            onClick={() => setUseManualCoordinates(!useManualCoordinates)}
            className="text-xs text-blue-600 hover:text-blue-700 underline"
          >
            {useManualCoordinates ? 'Use Address Search' : 'Enter Coordinates Manually'}
          </button>
        </div>

        {!useManualCoordinates ? (
          <GooglePlacesAutocomplete
            value={formData.access_starting_point_name || ''}
            onChange={(value) => updateFormData({ access_starting_point_name: value })}
            onPlaceSelected={(place) => {
              updateFormData({
                access_starting_point_name: place.formattedAddress,
                access_starting_point_latitude: place.latitude,
                access_starting_point_longitude: place.longitude,
              });
            }}
            placeholder="Search for starting point (e.g., Kurunegala town, Clock tower)"
            className="mb-2"
          />
        ) : (
          <div>
            <input
              type="text"
              value={formData.access_starting_point_name || ''}
              onChange={(e) => updateFormData({ access_starting_point_name: e.target.value })}
              placeholder="Starting point name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 mb-3"
            />

            <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={formData.access_starting_point_latitude || ''}
                  onChange={(e) => updateFormData({ access_starting_point_latitude: parseFloat(e.target.value) })}
                  placeholder="e.g., 7.4867"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={formData.access_starting_point_longitude || ''}
                  onChange={(e) => updateFormData({ access_starting_point_longitude: parseFloat(e.target.value) })}
                  placeholder="e.g., 80.3642"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {formData.access_starting_point_latitude && formData.access_starting_point_longitude && (
          <div className="mt-2 bg-green-50 border border-green-200 rounded p-2 text-sm text-green-800">
            Location set: {formData.access_starting_point_latitude.toFixed(6)}, {formData.access_starting_point_longitude.toFixed(6)}
          </div>
        )}
      </div>

      {/* Generate Button */}
      <button
        onClick={generateDirections}
        disabled={generating || !formData.property_latitude || !formData.access_starting_point_latitude}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {generating ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating Route...
          </>
        ) : (
          <>
            <Navigation2 className="w-5 h-5" />
            Generate Route & Directions
          </>
        )}
      </button>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Route Data Display */}
      {routeData && (
        <div className="space-y-6">
          {/* Route Summary */}
          <div className="bg-green-50 p-4 rounded-lg space-y-2">
            <div className="flex items-center gap-2 mb-2">
              <MapIcon className="w-4 h-4 text-green-600" />
              <h4 className="font-medium text-green-900">Route Information:</h4>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-600">Distance:</span>
                <span className="ml-2 font-medium">{routeData.distance_text}</span>
              </div>
              <div>
                <span className="text-gray-600">Duration:</span>
                <span className="ml-2 font-medium">{routeData.duration_text}</span>
              </div>
            </div>
          </div>

          {/* Road Conditions Summary - NEW COMPONENT */}
          <div className="border rounded-lg p-4">
            <h4 className="font-medium mb-4 flex items-center gap-2">
              <Navigation2 className="w-5 h-5 text-blue-600" />
              Road Conditions
            </h4>
            <RoadConditionsSummary
              roadConditions={roadConditions}
              onChange={handleRoadConditionsChange}
            />
          </div>

          {/* Road Position */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Property Position Relative to Road
            </label>
            <select
              value={formData.property_road_position || ''}
              onChange={(e) => {
                updateFormData({ property_road_position: e.target.value });
                // Regenerate text if we already have conditions
                if (roadConditions.length > 0) {
                  setTimeout(() => generateProfessionalText(), 100);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select position</option>
              <option value="right side">Right side</option>
              <option value="left side">Left side</option>
              <option value="both sides">Both sides</option>
            </select>
          </div>

          {/* Professional ACCESS Text (FINAL - shown only after road conditions are added) */}
          {formData.access_directions_text && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <div className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                  ACCESS
                </div>
                <span className="text-sm text-green-800 font-medium">
                  This will appear in your report
                </span>
                {generatingText && (
                  <Loader2 className="w-4 h-4 text-green-600 animate-spin ml-auto" />
                )}
              </div>

              <label className="block text-sm font-bold text-gray-900 mb-2">
                Professional ACCESS Description
              </label>
              <textarea
                rows={12}
                value={formData.access_directions_text || ''}
                onChange={(e) => updateFormData({ access_directions_text: e.target.value })}
                className="w-full px-4 py-3 border-2 border-green-200 rounded-lg focus:ring-green-500 focus:border-green-500 font-serif text-base shadow-sm"
                placeholder="The professional access description will be auto-generated here. You can edit it as needed..."
              />
              <p className="text-xs text-green-700 mt-2 flex items-center gap-1">
                <span className="font-medium">✓</span>
                Auto-generated from route data and road conditions. Edit to match your preferred style.
              </p>
            </div>
          )}

          {/* Turn-by-Turn Directions - HIDDEN (data still used for prompt generation) */}
        </div>
      )}

      {/* Helper Text */}
      {!routeData && !generating && (
        <div className="bg-blue-50 p-3 rounded text-sm text-blue-800">
          <strong>How it works:</strong> Search for your starting point using the autocomplete search (or enter coordinates manually),
          then click "Generate Route & Directions" to get turn-by-turn directions and a map showing the route to the property.
        </div>
      )}
    </div>
  );
}
