import React, { useState, useCallback, useRef, useEffect } from 'react';
import { GoogleMap, useJsApiLoader, Marker, Polyline } from '@react-google-maps/api';
import { MapPin, Navigation, Edit2, Check, X } from 'lucide-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Sri Lanka center coordinates
const SRI_LANKA_CENTER = {
  lat: 7.8731,
  lng: 80.7718
};

const mapContainerStyle = {
  width: '100%',
  height: '500px'
};

const libraries: ("places" | "drawing" | "geometry" | "visualization")[] = ["places"];

interface PlaceAutocompleteResult {
  description: string;
  place_id: string;
  structured_formatting?: {
    main_text: string;
    secondary_text: string;
  };
}

interface LocationData {
  lat: number;
  lng: number;
  formatted_address: string;
  village?: string;
  district?: string;
  province?: string;
}

interface RouteData {
  distance_km: number;
  duration_minutes: number;
  distance_text: string;
  duration_text: string;
  polyline: string;
  steps: any[];
  professional_text: string;
}

export interface PropertyLocationMapProps {
  onLocationChange: (data: {
    property_address_full?: string;
    property_village?: string;
    property_district?: string;
    property_province?: string;
    property_latitude?: number;
    property_longitude?: number;
    access_starting_point_name?: string;
    access_starting_point_latitude?: number;
    access_starting_point_longitude?: number;
    access_directions_text?: string;
    access_distance_km?: number;
    access_duration_minutes?: number;
    property_road_position?: string;
    access_route_data?: any;
  }) => void;
  initialData?: {
    property_latitude?: number;
    property_longitude?: number;
    access_starting_point_latitude?: number;
    access_starting_point_longitude?: number;
    access_directions_text?: string;
  };
  googleMapsApiKey: string;
}

const PropertyLocationMap: React.FC<PropertyLocationMapProps> = ({
  onLocationChange,
  initialData,
  googleMapsApiKey
}) => {
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: googleMapsApiKey,
    libraries: libraries
  });

  // Map state
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [mapCenter, setMapCenter] = useState(SRI_LANKA_CENTER);
  const [mapZoom, setMapZoom] = useState(8);

  // Markers
  const [startingPoint, setStartingPoint] = useState<LocationData | null>(null);
  const [propertyLocation, setPropertyLocation] = useState<LocationData | null>(null);

  // Route data
  const [routeData, setRouteData] = useState<RouteData | null>(null);
  const [decodedPolyline, setDecodedPolyline] = useState<google.maps.LatLngLiteral[]>([]);

  // UI state
  const [startingPointInput, setStartingPointInput] = useState('');
  const [propertyLocationInput, setPropertyLocationInput] = useState('');
  const [startingSuggestions, setStartingSuggestions] = useState<PlaceAutocompleteResult[]>([]);
  const [propertySuggestions, setPropertySuggestions] = useState<PlaceAutocompleteResult[]>([]);
  const [directionsText, setDirectionsText] = useState('');
  const [isEditingDirections, setIsEditingDirections] = useState(false);
  const [roadPosition, setRoadPosition] = useState('left side');
  const [clickMode, setClickMode] = useState<'none' | 'starting' | 'property'>('none');

  // Debounce timers
  const startingDebounceTimer = useRef<NodeJS.Timeout | null>(null);
  const propertyDebounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Load initial data
  useEffect(() => {
    if (initialData) {
      if (initialData.property_latitude && initialData.property_longitude) {
        setPropertyLocation({
          lat: initialData.property_latitude,
          lng: initialData.property_longitude,
          formatted_address: '',
        });
        setMapCenter({
          lat: initialData.property_latitude,
          lng: initialData.property_longitude
        });
        setMapZoom(14);
      }
      if (initialData.access_starting_point_latitude && initialData.access_starting_point_longitude) {
        setStartingPoint({
          lat: initialData.access_starting_point_latitude,
          lng: initialData.access_starting_point_longitude,
          formatted_address: '',
        });
      }
      if (initialData.access_directions_text) {
        setDirectionsText(initialData.access_directions_text);
      }
    }
  }, [initialData]);

  // Fetch place autocomplete suggestions
  const fetchPlaceSuggestions = async (input: string, type: 'starting' | 'property') => {
    if (input.length < 2) {
      if (type === 'starting') setStartingSuggestions([]);
      else setPropertySuggestions([]);
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/api/maps/places/autocomplete`, {
        input,
        location: `${SRI_LANKA_CENTER.lat},${SRI_LANKA_CENTER.lng}`
      });

      if (type === 'starting') {
        setStartingSuggestions(response.data);
      } else {
        setPropertySuggestions(response.data);
      }
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  };

  // Debounced autocomplete
  const handleStartingPointInputChange = (value: string) => {
    setStartingPointInput(value);

    if (startingDebounceTimer.current) {
      clearTimeout(startingDebounceTimer.current);
    }

    startingDebounceTimer.current = setTimeout(() => {
      fetchPlaceSuggestions(value, 'starting');
    }, 500);
  };

  const handlePropertyLocationInputChange = (value: string) => {
    setPropertyLocationInput(value);

    if (propertyDebounceTimer.current) {
      clearTimeout(propertyDebounceTimer.current);
    }

    propertyDebounceTimer.current = setTimeout(() => {
      fetchPlaceSuggestions(value, 'property');
    }, 500);
  };

  // Select place from suggestions
  const selectPlace = async (placeId: string, type: 'starting' | 'property') => {
    try {
      const response = await axios.post(`${API_URL}/api/maps/places/details`, {
        place_id: placeId
      });

      const data = response.data;
      const locationData: LocationData = {
        lat: data.lat,
        lng: data.lng,
        formatted_address: data.formatted_address || data.name,
        village: data.village,
        district: data.district,
        province: data.province
      };

      if (type === 'starting') {
        setStartingPoint(locationData);
        setStartingPointInput(locationData.formatted_address);
        setStartingSuggestions([]);
      } else {
        setPropertyLocation(locationData);
        setPropertyLocationInput(locationData.formatted_address);
        setPropertySuggestions([]);

        // Center map on property
        setMapCenter({ lat: locationData.lat, lng: locationData.lng });
        setMapZoom(16);
      }

      // If both points are set, fetch route
      if (type === 'property' && startingPoint) {
        fetchRoute(startingPoint, locationData);
      } else if (type === 'starting' && propertyLocation) {
        fetchRoute(locationData, propertyLocation);
      }
    } catch (error) {
      console.error('Error fetching place details:', error);
    }
  };

  // Fetch route directions
  const fetchRoute = async (start: LocationData, end: LocationData) => {
    try {
      const response = await axios.post(`${API_URL}/api/maps/directions`, {
        origin_lat: start.lat,
        origin_lng: start.lng,
        dest_lat: end.lat,
        dest_lng: end.lng,
        starting_point_name: startingPointInput || 'the starting point'
      });

      const data: RouteData = response.data;
      setRouteData(data);
      setDirectionsText(data.professional_text);

      // Decode polyline for display
      if (data.polyline && google.maps && google.maps.geometry) {
        const decoded = google.maps.geometry.encoding.decodePath(data.polyline);
        setDecodedPolyline(decoded.map(point => ({ lat: point.lat(), lng: point.lng() })));
      }

      // Update parent with all location data
      updateParentData(end, start, data);
    } catch (error) {
      console.error('Error fetching route:', error);
    }
  };

  // Update parent component with all data
  const updateParentData = (property: LocationData, starting?: LocationData | null, route?: RouteData | null) => {
    const data: any = {
      property_address_full: property.formatted_address,
      property_village: property.village,
      property_district: property.district,
      property_province: property.province,
      property_latitude: property.lat,
      property_longitude: property.lng,
    };

    if (starting) {
      data.access_starting_point_name = startingPointInput;
      data.access_starting_point_latitude = starting.lat;
      data.access_starting_point_longitude = starting.lng;
    }

    if (route) {
      data.access_directions_text = directionsText;
      data.access_distance_km = route.distance_km;
      data.access_duration_minutes = route.duration_minutes;
      data.property_road_position = roadPosition;
      data.access_route_data = route;
    }

    onLocationChange(data);
  };

  // Handle map click
  const handleMapClick = useCallback((e: google.maps.MapMouseEvent) => {
    if (!e.latLng) return;

    const lat = e.latLng.lat();
    const lng = e.latLng.lng();

    if (clickMode === 'starting') {
      const locationData: LocationData = {
        lat,
        lng,
        formatted_address: `${lat.toFixed(6)}, ${lng.toFixed(6)}`
      };
      setStartingPoint(locationData);
      setStartingPointInput(locationData.formatted_address);
      setClickMode('none');

      if (propertyLocation) {
        fetchRoute(locationData, propertyLocation);
      }
    } else if (clickMode === 'property') {
      const locationData: LocationData = {
        lat,
        lng,
        formatted_address: `${lat.toFixed(6)}, ${lng.toFixed(6)}`
      };
      setPropertyLocation(locationData);
      setPropertyLocationInput(locationData.formatted_address);
      setMapCenter({ lat, lng });
      setMapZoom(16);
      setClickMode('none');

      if (startingPoint) {
        fetchRoute(startingPoint, locationData);
      }

      updateParentData(locationData, startingPoint, routeData);
    }
  }, [clickMode, propertyLocation, startingPoint, routeData, directionsText, roadPosition, startingPointInput]);

  // Save edited directions
  const saveDirections = () => {
    setIsEditingDirections(false);
    if (propertyLocation) {
      updateParentData(propertyLocation, startingPoint, routeData);
    }
  };

  const onLoad = useCallback((map: google.maps.Map) => {
    setMap(map);
  }, []);

  const onUnmount = useCallback(() => {
    setMap(null);
  }, []);

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Input Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Starting Point Input */}
        <div className="relative">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Starting Point (Landmark)
          </label>
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={startingPointInput}
                onChange={(e) => handleStartingPointInputChange(e.target.value)}
                placeholder="Type landmark name..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
              {startingSuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
                  {startingSuggestions.map((suggestion) => (
                    <button
                      key={suggestion.place_id}
                      onClick={() => selectPlace(suggestion.place_id, 'starting')}
                      className="w-full px-4 py-2 text-left hover:bg-emerald-50 transition-colors"
                    >
                      <div className="font-medium text-gray-900">
                        {suggestion.structured_formatting?.main_text || suggestion.description}
                      </div>
                      {suggestion.structured_formatting?.secondary_text && (
                        <div className="text-sm text-gray-500">
                          {suggestion.structured_formatting.secondary_text}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => setClickMode(clickMode === 'starting' ? 'none' : 'starting')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                clickMode === 'starting'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title="Click on map to select"
            >
              <MapPin className="h-5 w-5" />
            </button>
          </div>
          {clickMode === 'starting' && (
            <p className="mt-2 text-sm text-emerald-600 font-medium">
              Click on the map to select starting point
            </p>
          )}
        </div>

        {/* Property Location Input */}
        <div className="relative">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Property Location
          </label>
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={propertyLocationInput}
                onChange={(e) => handlePropertyLocationInputChange(e.target.value)}
                placeholder="Type property address..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
              {propertySuggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto">
                  {propertySuggestions.map((suggestion) => (
                    <button
                      key={suggestion.place_id}
                      onClick={() => selectPlace(suggestion.place_id, 'property')}
                      className="w-full px-4 py-2 text-left hover:bg-emerald-50 transition-colors"
                    >
                      <div className="font-medium text-gray-900">
                        {suggestion.structured_formatting?.main_text || suggestion.description}
                      </div>
                      {suggestion.structured_formatting?.secondary_text && (
                        <div className="text-sm text-gray-500">
                          {suggestion.structured_formatting.secondary_text}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => setClickMode(clickMode === 'property' ? 'none' : 'property')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                clickMode === 'property'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title="Click on map to select"
            >
              <MapPin className="h-5 w-5" />
            </button>
          </div>
          {clickMode === 'property' && (
            <p className="mt-2 text-sm text-emerald-600 font-medium">
              Click on the map to select property location
            </p>
          )}
        </div>
      </div>

      {/* Google Map */}
      <div className="relative rounded-xl overflow-hidden shadow-lg border-2 border-gray-200">
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          center={mapCenter}
          zoom={mapZoom}
          onLoad={onLoad}
          onUnmount={onUnmount}
          onClick={handleMapClick}
          options={{
            streetViewControl: false,
            mapTypeControl: true,
          }}
        >
          {/* Starting Point Marker */}
          {startingPoint && (
            <Marker
              position={{ lat: startingPoint.lat, lng: startingPoint.lng }}
              label="A"
              title="Starting Point"
            />
          )}

          {/* Property Location Marker */}
          {propertyLocation && (
            <Marker
              position={{ lat: propertyLocation.lat, lng: propertyLocation.lng }}
              label="B"
              title="Property Location"
              icon={{
                url: 'http://maps.google.com/mapfiles/ms/icons/green-dot.png'
              }}
            />
          )}

          {/* Route Polyline */}
          {decodedPolyline.length > 0 && (
            <Polyline
              path={decodedPolyline}
              options={{
                strokeColor: '#2563eb',
                strokeOpacity: 0.8,
                strokeWeight: 4,
              }}
            />
          )}
        </GoogleMap>
      </div>

      {/* Route Information */}
      {routeData && (
        <div className="bg-gradient-to-r from-blue-50 to-emerald-50 rounded-xl p-6 border border-blue-200">
          <div className="flex items-center gap-2 mb-4">
            <Navigation className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-bold text-gray-900">Route Information</h3>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600">Distance</p>
              <p className="text-lg font-bold text-gray-900">{routeData.distance_text}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Duration</p>
              <p className="text-lg font-bold text-gray-900">{routeData.duration_text}</p>
            </div>
            <div className="col-span-2">
              <label className="text-sm text-gray-600 block mb-2">Property Position</label>
              <select
                value={roadPosition}
                onChange={(e) => {
                  setRoadPosition(e.target.value);
                  if (propertyLocation) {
                    updateParentData(propertyLocation, startingPoint, routeData);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              >
                <option value="left side">Left side of road</option>
                <option value="right side">Right side of road</option>
                <option value="fronting the road">Fronting the road</option>
                <option value="end of the road">End of the road</option>
              </select>
            </div>
          </div>

          {/* Directions Text */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700">Access Directions</label>
              {!isEditingDirections ? (
                <button
                  onClick={() => setIsEditingDirections(true)}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  <Edit2 className="h-4 w-4" />
                  Edit
                </button>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={saveDirections}
                    className="flex items-center gap-1 text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                  >
                    <Check className="h-4 w-4" />
                    Save
                  </button>
                  <button
                    onClick={() => {
                      setDirectionsText(routeData.professional_text);
                      setIsEditingDirections(false);
                    }}
                    className="flex items-center gap-1 text-sm text-red-600 hover:text-red-700 font-medium"
                  >
                    <X className="h-4 w-4" />
                    Cancel
                  </button>
                </div>
              )}
            </div>
            {isEditingDirections ? (
              <textarea
                value={directionsText}
                onChange={(e) => setDirectionsText(e.target.value)}
                rows={6}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 font-mono text-sm"
              />
            ) : (
              <div className="bg-white px-4 py-3 rounded-lg border border-gray-200">
                <p className="text-gray-700 whitespace-pre-line">{directionsText}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PropertyLocationMap;
