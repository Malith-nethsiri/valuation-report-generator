import React, { useState, useEffect } from 'react';
import { MapPin, RefreshCw, Sparkles, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './Button';
import { Label } from './Label';
import { Input } from './Input';
import { Textarea } from './Textarea';
import { MultiSelectWithCustomInput } from './MultiSelectWithCustomInput';
import { formatFacilityName, formatPlaceName, formatAddress } from '../utils/textFormatter';
import { authTokenStorage } from '../utils/secureStorage';

// Helper to get CSRF token from cookie
const getCSRFToken = (): string | null => {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
};

// Configuration Constants
const SEARCH_RADIUS_DEFAULT = 5000; // meters (5 km)
const SEARCH_RADIUS_OPTIONS = {
  SMALL: 2000,   // 2 km
  MEDIUM: 5000,  // 5 km
  LARGE: 10000   // 10 km
};
const GEOCODING_TIMEOUT = 30000; // 30 seconds

interface Facility {
  type: string;
  google_type?: string;
  name: string;
  address?: string;
  distance_km: number;
  latitude: number;
  longitude: number;
  place_id?: string;
  selected: boolean;
}

interface LocalityData {
  // Distance to town
  distance_to_major_town_km?: number;
  major_town_name?: string;

  // Nearby facilities
  nearby_facilities?: Facility[];

  // Infrastructure
  has_electricity?: boolean;
  water_supply_type?: string[];  // Array of water supply types
  telecommunication_types?: string[];
  internet_types?: string[];

  // Public transport
  has_public_transport?: boolean;
  public_transport_routes?: string;
  public_transport_frequency?: string;
  nearest_bus_stop_distance_km?: number;
  nearest_bus_stop_name?: string;
  nearest_railway_station?: string;
  nearest_railway_distance_km?: number;

  // Area characteristics
  area_type?: string;
  development_level?: string;
  predominant_building_type?: string[];  // Array of predominant building types

  // Tourism
  is_tourist_area?: boolean;
  tourist_attractions_nearby?: string;

  // Generated narrative
  locality_description_text?: string;
}

interface Props {
  data: LocalityData;
  onChange: (data: Partial<LocalityData>) => void;
  propertyLatitude?: number;
  propertyLongitude?: number;
  propertyVillage?: string;
  propertyDistrict?: string;
  divisionalSecretariat?: string;
  pradeshiyaSabha?: string;
}

const FACILITY_CATEGORY_LABELS: Record<string, string> = {
  hospital: 'Hospitals',
  police: 'Police Stations',
  post_office: 'Post Offices',
  bank: 'Banks',
  school: 'Schools',
  place_of_worship: 'Religious Places',
  bus_station: 'Bus Stands',
  train_station: 'Railway Stations',
  gas_station: 'Filling Stations',
  lodging: 'Hotels/Resorts',
  shopping: 'Markets/Shopping',
};

function generatePublicTransportRoutes(transport: {
  bus_stop?: { name: string; distance_km: number };
  railway_station?: { name: string; distance_km: number };
}): string {
  const routes: string[] = [];

  if (transport.bus_stop) {
    routes.push(`Bus route via ${transport.bus_stop.name}`);
  }

  if (transport.railway_station) {
    routes.push(`Railway access via ${transport.railway_station.name}`);
  }

  return routes.join(', ');
}

const LocalityInformationSection: React.FC<Props> = ({
  data,
  onChange,
  propertyLatitude,
  propertyLongitude,
  propertyVillage,
  propertyDistrict,
  divisionalSecretariat,
  pradeshiyaSabha,
}) => {
  const [isLoadingFacilities, setIsLoadingFacilities] = useState(false);
  const [isGeneratingNarrative, setIsGeneratingNarrative] = useState(false);
  const [searchRadius, setSearchRadius] = useState(SEARCH_RADIUS_DEFAULT);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  // Auto-check "Public Transport Available" when transport data is present
  useEffect(() => {
    if ((data.nearest_bus_stop_name || data.nearest_railway_station) && !data.has_public_transport) {
      onChange({ has_public_transport: true });
    }
  }, [data.nearest_bus_stop_name, data.nearest_railway_station, data.has_public_transport, onChange]);

  // Auto-fetch nearby facilities
  const handleFetchFacilities = async () => {
    if (!propertyLatitude || !propertyLongitude) {
      setError('Property location is required to fetch nearby facilities');
      return;
    }

    setIsLoadingFacilities(true);
    setError(null);

    // Set timeout for the fetch operation
    const timeoutId = setTimeout(() => {
      setIsLoadingFacilities(false);
      setError('Request timeout. The server took too long to respond. Please try again or check your internet connection.');
    }, GEOCODING_TIMEOUT);

    try {
      const token = authTokenStorage.getToken();
      if (!token) {
        clearTimeout(timeoutId);
        throw new Error('Authentication required. Please log in again.');
      }

      const csrfToken = getCSRFToken();
      const response = await fetch('/api/locality/nearby-facilities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          ...(csrfToken && { 'X-CSRF-Token': csrfToken })
        },
        body: JSON.stringify({
          latitude: propertyLatitude,
          longitude: propertyLongitude,
          radius_meters: searchRadius,
        })
      });

      clearTimeout(timeoutId); // Clear timeout on successful response

      if (response.status === 401) {
        throw new Error('Session expired. Please log in again.');
      }
      if (response.status === 500) {
        const errorData = await response.json().catch(() => ({}));
        if (errorData.detail && errorData.detail.includes('not configured')) {
          throw new Error('Google Places API is not configured properly. Please contact support.');
        }
        throw new Error(errorData.detail || 'Server error while fetching facilities. Please try again later.');
      }
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch facilities (Error ${response.status})`);
      }

      const result = await response.json();

      // Process the facilities data with formatting
      const allFacilities: Facility[] = [];
      Object.entries(result.facilities || {}).forEach(([category, facilities]) => {
        (facilities as any[]).forEach((facility: any) => {
          allFacilities.push({
            ...facility,
            type: category,
            name: formatFacilityName(facility.name),
            address: facility.address ? formatAddress(facility.address) : undefined,
            selected: false // Initialize as unselected
          });
        });
      });

      // Generate public transport routes if transport data exists
      const hasTransportData = result.transport?.bus_stop || result.transport?.railway_station;
      const generatedRoutes = hasTransportData
        ? generatePublicTransportRoutes(result.transport)
        : undefined;

      // Update state with formatted data and auto-filled routes
      onChange({
        nearby_facilities: allFacilities,
        major_town_name: result.major_town?.name ? formatPlaceName(result.major_town.name) : undefined,
        distance_to_major_town_km: result.major_town?.distance_km,
        nearest_bus_stop_name: result.transport?.bus_stop?.name ? formatFacilityName(result.transport.bus_stop.name) : undefined,
        nearest_bus_stop_distance_km: result.transport?.bus_stop?.distance_km,
        nearest_railway_station: result.transport?.railway_station?.name ? formatFacilityName(result.transport.railway_station.name) : undefined,
        nearest_railway_distance_km: result.transport?.railway_station?.distance_km,
        public_transport_routes: generatedRoutes,
      });

    } catch (err: any) {
      clearTimeout(timeoutId); // Clear timeout on error
      console.error('[LOCALITY] Error fetching facilities:', err);
      const errorMessage = err.message || 'Failed to fetch nearby facilities. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoadingFacilities(false);
    }
  };

  // Generate AI narrative
  const handleGenerateNarrative = async () => {
    setIsGeneratingNarrative(true);
    setError(null);

    try {
      const token = authTokenStorage.getToken();

      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      const csrfToken = getCSRFToken();
      const response = await fetch('/api/locality/generate-narrative', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          ...(csrfToken && { 'X-CSRF-Token': csrfToken })
        },
        body: JSON.stringify({
          property_village: propertyVillage,
          property_district: propertyDistrict,
          divisional_secretariat: divisionalSecretariat,
          pradeshiya_sabha: pradeshiyaSabha,
          ...data
        })
      });

      if (response.status === 401) {
        console.error('[LOCALITY] Token expired or invalid');
        throw new Error('Your session has expired. Please refresh the page and log in again.');
      }
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[LOCALITY] Narrative generation failed:', errorData);
        throw new Error(errorData.detail || 'Failed to generate narrative');
      }

      const result = await response.json();
      onChange({ locality_description_text: result.narrative });

    } catch (err: any) {
      console.error('[LOCALITY] Error generating narrative:', err);
      setError(err.message || 'Failed to generate locality description. Please try again.');
    } finally {
      setIsGeneratingNarrative(false);
    }
  };

  // Group facilities by category
  const facilitiesByCategory: Record<string, Facility[]> = {};
  (data.nearby_facilities || []).forEach((facility) => {
    if (!facilitiesByCategory[facility.type]) {
      facilitiesByCategory[facility.type] = [];
    }
    facilitiesByCategory[facility.type].push(facility);
  });

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  // Toggle facility selection
  const toggleFacilitySelection = (facility: Facility) => {
    const updated = (data.nearby_facilities || []).map(f =>
      f.name === facility.name && f.type === facility.type
        ? { ...f, selected: !f.selected }
        : f
    );
    onChange({ nearby_facilities: updated });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Locality Information
        </h2>
        <p className="text-sm text-gray-600">
          Information about the property's surroundings, facilities, infrastructure, and area characteristics
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 text-sm">
          {error}
        </div>
      )}

      {/* Show success message if facilities were prefetched */}
      {data.nearby_facilities && data.nearby_facilities.length > 0 ? (
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
          <div className="flex items-center gap-2 mb-3">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-semibold text-green-900">
              Facilities data loaded automatically! Found {data.nearby_facilities.length} facilities.
            </span>
          </div>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Label className="text-sm text-gray-700">Search Radius:</Label>
              <select
                value={searchRadius}
                onChange={(e) => setSearchRadius(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                <option value={SEARCH_RADIUS_OPTIONS.SMALL}>2 km</option>
                <option value={SEARCH_RADIUS_OPTIONS.MEDIUM}>5 km</option>
                <option value={SEARCH_RADIUS_OPTIONS.LARGE}>10 km</option>
              </select>
            </div>
            <Button
              onClick={handleFetchFacilities}
              disabled={isLoadingFacilities}
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
            >
              {isLoadingFacilities ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Refreshing...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Refresh with different radius
                </>
              )}
            </Button>
          </div>
        </div>
      ) : (
        <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-xl p-6 border border-emerald-200">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-emerald-600" />
                Auto-Fetch Nearby Facilities
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Automatically find hospitals, banks, schools, and other facilities near the property using Google Places
              </p>
              <div className="flex items-center gap-4">
                <Label>Search Radius:</Label>
                <select
                  value={searchRadius}
                  onChange={(e) => setSearchRadius(Number(e.target.value))}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value={SEARCH_RADIUS_OPTIONS.SMALL}>2 km</option>
                  <option value={SEARCH_RADIUS_OPTIONS.MEDIUM}>5 km</option>
                  <option value={SEARCH_RADIUS_OPTIONS.LARGE}>10 km</option>
                </select>
              </div>
            </div>
            <Button
              onClick={handleFetchFacilities}
              disabled={isLoadingFacilities || !propertyLatitude || !propertyLongitude}
              className="ml-4"
            >
              {isLoadingFacilities ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Fetching...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Fetch Facilities
                </>
              )}
            </Button>
          </div>

          {!propertyLatitude && (
            <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-yellow-800 text-sm">
              Please complete the Property Location section first to enable auto-fetch.
            </div>
          )}
        </div>
      )}

      {/* Distance to Major Town - Always visible for manual entry */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Nearest Major Town</Label>
            <Input
              value={data.major_town_name || ''}
              onChange={(e) => onChange({ major_town_name: e.target.value })}
              placeholder="Enter nearest major town"
            />
          </div>
          <div>
            <Label>Distance (km)</Label>
            <Input
              type="number"
              step="0.1"
              value={data.distance_to_major_town_km || ''}
              onChange={(e) => onChange({ distance_to_major_town_km: Number(e.target.value) })}
              placeholder="e.g., 2.4"
            />
          </div>
        </div>
      </div>

      {/* Nearby Facilities */}
      {Object.keys(facilitiesByCategory).length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Nearby Facilities ({(data.nearby_facilities || []).filter(f => f.selected).length} selected)
          </h3>
          <div className="space-y-2">
            {Object.entries(facilitiesByCategory).map(([category, facilities]) => (
              <div key={category} className="border border-gray-200 rounded-lg">
                <button
                  type="button"
                  onClick={() => toggleCategory(category)}
                  className="w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors"
                >
                  <span className="font-medium text-gray-900">
                    {FACILITY_CATEGORY_LABELS[category] || category} ({facilities.length})
                  </span>
                  {expandedCategories.has(category) ? (
                    <ChevronUp className="h-4 w-4 text-gray-500" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-gray-500" />
                  )}
                </button>

                {expandedCategories.has(category) && (
                  <div className="p-3 border-t border-gray-200 space-y-2">
                    {facilities.map((facility, idx) => (
                      <div
                        key={`${facility.name}-${idx}`}
                        className="flex items-start gap-3 p-2 hover:bg-gray-50 rounded"
                      >
                        <input
                          type="checkbox"
                          checked={facility.selected}
                          onChange={() => toggleFacilitySelection(facility)}
                          className="mt-1 h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{facility.name}</div>
                          <div className="text-sm text-gray-600">
                            {facility.distance_km} km away
                            {facility.address && ` • ${facility.address}`}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Infrastructure & Utilities */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Infrastructure & Utilities</h3>
        <div className="space-y-4">
          {/* Electricity */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="has-electricity"
              checked={data.has_electricity ?? true}
              onChange={(e) => onChange({ has_electricity: e.target.checked })}
              className="h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
            />
            <label htmlFor="has-electricity" className="text-sm font-medium text-gray-900">
              Electricity Available
            </label>
          </div>

          {/* Water Supply */}
          <div>
            <MultiSelectWithCustomInput
              label="Water Supply Type"
              value={data.water_supply_type || []}
              onChange={(values) => onChange({ water_supply_type: values })}
              predefinedOptions={[
                { value: 'Pipe-borne (NWSDB)', label: 'Pipe-borne (NWSDB)' },
                { value: 'Well', label: 'Well' },
                { value: 'Bore/Tube Well', label: 'Bore/Tube Well' },
                { value: 'Rainwater Harvesting', label: 'Rainwater Harvesting' }
              ]}
              maxSelections={5}
              maxCharacters={50}
              helperText="Select up to 5 types or add custom values (press Enter)"
            />
          </div>

          {/* Telecommunication */}
          <div>
            <Label>Telecommunication</Label>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="tel-landline"
                  checked={(data.telecommunication_types || []).includes('landline')}
                  onChange={(e) => {
                    const types = data.telecommunication_types || [];
                    onChange({
                      telecommunication_types: e.target.checked
                        ? [...types, 'landline']
                        : types.filter(t => t !== 'landline')
                    });
                  }}
                  className="h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
                />
                <label htmlFor="tel-landline" className="text-sm text-gray-900">Landline Available</label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="tel-mobile"
                  checked={(data.telecommunication_types || []).includes('mobile_coverage')}
                  onChange={(e) => {
                    const types = data.telecommunication_types || [];
                    onChange({
                      telecommunication_types: e.target.checked
                        ? [...types, 'mobile_coverage']
                        : types.filter(t => t !== 'mobile_coverage')
                    });
                  }}
                  className="h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
                />
                <label htmlFor="tel-mobile" className="text-sm text-gray-900">Mobile Coverage</label>
              </div>
            </div>
          </div>

          {/* Internet */}
          <div>
            <Label>Internet</Label>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="internet-fiber"
                  checked={(data.internet_types || []).includes('fiber')}
                  onChange={(e) => {
                    const types = data.internet_types || [];
                    onChange({
                      internet_types: e.target.checked
                        ? [...types, 'fiber']
                        : types.filter(t => t !== 'fiber')
                    });
                  }}
                  className="h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
                />
                <label htmlFor="internet-fiber" className="text-sm text-gray-900">Fiber Connection</label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="internet-mobile"
                  checked={(data.internet_types || []).includes('mobile_data')}
                  onChange={(e) => {
                    const types = data.internet_types || [];
                    onChange({
                      internet_types: e.target.checked
                        ? [...types, 'mobile_data']
                        : types.filter(t => t !== 'mobile_data')
                    });
                  }}
                  className="h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
                />
                <label htmlFor="internet-mobile" className="text-sm text-gray-900">Mobile Data</label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Public Transport */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Public Transport</h3>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="has-public-transport"
              checked={data.has_public_transport ?? false}
              onChange={(e) => onChange({ has_public_transport: e.target.checked })}
              className="h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
            />
            <label htmlFor="has-public-transport" className="text-sm font-medium text-gray-900">
              Public Transport Available
            </label>
          </div>

          {data.has_public_transport && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Nearest Bus Stop</Label>
                  <Input
                    value={data.nearest_bus_stop_name || ''}
                    onChange={(e) => onChange({ nearest_bus_stop_name: e.target.value })}
                    placeholder="Enter nearest bus stop"
                  />
                </div>
                <div>
                  <Label>Distance (km)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={data.nearest_bus_stop_distance_km || ''}
                    onChange={(e) => onChange({ nearest_bus_stop_distance_km: Number(e.target.value) })}
                    placeholder="e.g., 1.2"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Nearest Railway Station</Label>
                  <Input
                    value={data.nearest_railway_station || ''}
                    onChange={(e) => onChange({ nearest_railway_station: e.target.value })}
                    placeholder="Enter nearest railway station"
                  />
                </div>
                <div>
                  <Label>Distance (km)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={data.nearest_railway_distance_km || ''}
                    onChange={(e) => onChange({ nearest_railway_distance_km: Number(e.target.value) })}
                    placeholder="e.g., 3.5"
                  />
                </div>
              </div>
              <div>
                <Label>Public Transport Routes</Label>
                <Input
                  value={data.public_transport_routes || ''}
                  onChange={(e) => onChange({ public_transport_routes: e.target.value })}
                  placeholder="Enter public transport routes"
                />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Area Characteristics */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Area Characteristics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <Label>Area Type</Label>
            <select
              value={data.area_type || ''}
              onChange={(e) => onChange({ area_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Select area type</option>
              <option value="residential">Residential</option>
              <option value="commercial">Commercial</option>
              <option value="industrial">Industrial</option>
              <option value="mixed">Mixed</option>
              <option value="agricultural">Agricultural</option>
              <option value="tourist">Tourist</option>
            </select>
          </div>
          <div>
            <Label>Development Level</Label>
            <select
              value={data.development_level || ''}
              onChange={(e) => onChange({ development_level: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Select development level</option>
              <option value="well_developed">Well Developed</option>
              <option value="developing">Developing</option>
              <option value="moderate">Moderate</option>
              <option value="undeveloped">Undeveloped</option>
            </select>
          </div>
          <div>
            <MultiSelectWithCustomInput
              label="Predominant Buildings"
              value={data.predominant_building_type || []}
              onChange={(values) => onChange({ predominant_building_type: values })}
              predefinedOptions={[
                { value: 'Single Story Residential', label: 'Single Story Residential' },
                { value: 'Multi Story Residential', label: 'Multi Story Residential' },
                { value: 'Apartments', label: 'Apartments' },
                { value: 'Commercial Buildings', label: 'Commercial Buildings' },
                { value: 'Mixed', label: 'Mixed' }
              ]}
              maxSelections={5}
              maxCharacters={50}
              helperText="Select up to 5 types or add custom values (press Enter)"
            />
          </div>
        </div>
      </div>

      {/* Tourism (Optional) */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <input
            type="checkbox"
            id="is-tourist-area"
            checked={data.is_tourist_area ?? false}
            onChange={(e) => onChange({ is_tourist_area: e.target.checked })}
            className="h-4 w-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500"
          />
          <label htmlFor="is-tourist-area" className="text-sm font-semibold text-gray-900">
            This is a tourist area
          </label>
        </div>

        {data.is_tourist_area && (
          <div>
            <Label>Nearby Tourist Attractions</Label>
            <Input
              value={data.tourist_attractions_nearby || ''}
              onChange={(e) => onChange({ tourist_attractions_nearby: e.target.value })}
              placeholder="e.g., Sigiriya Rock, Dambulla Cave Temple"
            />
          </div>
        )}
      </div>

      {/* AI-Generated Locality Description */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-6 border border-purple-200">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-600" />
              Locality Description
            </h3>
            <p className="text-sm text-gray-600">
              Generate a professional locality description using AI based on all the data above
            </p>
          </div>
          <Button
            onClick={handleGenerateNarrative}
            disabled={isGeneratingNarrative}
            className="ml-4"
          >
            {isGeneratingNarrative ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Description
              </>
            )}
          </Button>
        </div>

        <div>
          <Label>Locality Description (Editable)</Label>
          <Textarea
            value={data.locality_description_text || ''}
            onChange={(e) => onChange({ locality_description_text: e.target.value })}
            placeholder="Click 'Generate Description' to create a professional locality description, or type your own..."
            rows={8}
            className="font-serif"
          />
          <p className="text-xs text-gray-500 mt-2">
            This will appear in the LOCALITY section of your valuation report
          </p>
        </div>
      </div>
    </div>
  );
};

export default LocalityInformationSection;
