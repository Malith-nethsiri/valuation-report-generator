import { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation2, Route as RouteIcon, Loader2, MousePointer, Navigation, Info, AlertTriangle, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import * as Sentry from '@sentry/react';
import type { RoadSegment, RoadCondition } from '../types';
import { RoadConditionsSummary } from './RoadConditionsSummary';
import { authTokenStorage } from '../utils/secureStorage';
import { loadGoogleMapsScript } from '../utils/loadGoogleMaps';
import { GOOGLE_MAPS_API_KEY } from '../config';
import { ManualAddressInput, type ManualAddressData } from './ManualAddressInput';
import { api } from '../services/api';

interface Props {
  onPropertySelected: (data: {
    latitude: number;
    longitude: number;
    district?: string;
    province?: string;
    village?: string;
  }) => void;
  onStartingPointSelected: (data: {
    address: string;
    latitude: number;
    longitude: number;
  }) => void;
  onRouteGenerated: (data: {
    distance: string;
    duration: string;
    distance_km?: number;  // Add numeric distance
    duration_minutes?: number;  // Add numeric duration
    accessText: string;
    steps: any[];
    mapImageUrl?: string;
    road_conditions?: RoadCondition[];
    entry_mode?: 'simple';  // Always 'simple' now - advanced mode removed
  }) => void;
  onFacilitiesFetched?: (data: {
    facilities: any[];
    majorTown?: { name: string; distance_km: number };
    transport?: any;
  }) => void;
  initialPropertyAddress?: string;
  initialStartingPoint?: string;
  // Props to restore state when navigating back
  initialRouteData?: any;
  initialAccessText?: string;
  initialMapImageUrl?: string;
  initialRoadConditions?: RoadCondition[];
}

interface GeocodingData {
  district?: string;
  province?: string;
  village?: string;
  administrativeArea?: string;
}

export function InteractivePropertyMap({
  onPropertySelected,
  onStartingPointSelected,
  onRouteGenerated,
  onFacilitiesFetched,
  initialPropertyAddress = '',
  initialStartingPoint = '',
  initialRouteData,
  initialAccessText = '',
  initialMapImageUrl,
  initialRoadConditions = [],
}: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<google.maps.Map | null>(null);
  const propertyMarkerRef = useRef<google.maps.Marker | null>(null);
  const startMarkerRef = useRef<google.maps.Marker | null>(null);
  const directionsRendererRef = useRef<google.maps.DirectionsRenderer | null>(null);
  const propertyAutocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const startAutocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);

  const [propertyAddress, setPropertyAddress] = useState(initialPropertyAddress);
  const [startingAddress, setStartingAddress] = useState(initialStartingPoint);
  const [startingPointName, setStartingPointName] = useState(''); // Human-friendly name for reports
  const [propertyPosition, setPropertyPosition] = useState<'left' | 'right'>('right');
  const [isLoading, setIsLoading] = useState(true);
  const [googleMapsLoaded, setGoogleMapsLoaded] = useState(false);
  const [routeData, setRouteData] = useState<any>(null);
  const [generating, setGenerating] = useState(false);
  const [transformingAccess, setTransformingAccess] = useState(false);
  const [mapImageUrl, setMapImageUrl] = useState<string | null>(null);
  const [clickMode, setClickMode] = useState<'start' | 'property' | null>(null);
  const geocoderRef = useRef<google.maps.Geocoder | null>(null);

  // Manual coordinate inputs
  const [manualLatitude, setManualLatitude] = useState<string>('');
  const [manualLongitude, setManualLongitude] = useState<string>('');
  const [coordinateInputMode, setCoordinateInputMode] = useState<'map' | 'manual'>('map');

  // Road conditions state (simple/summary mode only)
  const [roadConditions, setRoadConditions] = useState<RoadCondition[]>([]);
  const [generatedAccessText, setGeneratedAccessText] = useState<string>(''); // New professional access text

  // Google Maps error state for fallback
  const [mapsError, setMapsError] = useState<string | null>(null);
  const [useFallbackMode, setUseFallbackMode] = useState(false);

  // Restore state when props change (navigation back to this step)
  useEffect(() => {
    setPropertyAddress(initialPropertyAddress);
  }, [initialPropertyAddress]);

  useEffect(() => {
    setStartingAddress(initialStartingPoint);
  }, [initialStartingPoint]);

  useEffect(() => {
    if (initialRouteData) {
      console.log('[InteractivePropertyMap] Restoring route data:', initialRouteData);
      setRouteData(initialRouteData);
    }
  }, [initialRouteData]);

  useEffect(() => {
    if (initialAccessText) {
      console.log('[InteractivePropertyMap] Restoring access text:', initialAccessText);
      setGeneratedAccessText(initialAccessText);
    }
  }, [initialAccessText]);

  useEffect(() => {
    if (initialMapImageUrl) {
      console.log('[InteractivePropertyMap] Restoring map image URL:', initialMapImageUrl);
      setMapImageUrl(initialMapImageUrl);
    }
  }, [initialMapImageUrl]);

  // Restore road conditions data on mount
  useEffect(() => {
    if (initialRoadConditions && initialRoadConditions.length > 0) {
      console.log('[InteractivePropertyMap] Restoring road conditions:', initialRoadConditions);
      setRoadConditions(initialRoadConditions);
    }
  }, [initialRoadConditions]);

  // Load Google Maps script on mount
  useEffect(() => {
    if (!GOOGLE_MAPS_API_KEY) {
      console.error('[InteractivePropertyMap] Google Maps API key not configured');
      const errorMsg = 'Google Maps API key not configured';
      setMapsError(errorMsg);
      setIsLoading(false);

      // Report to Sentry
      Sentry.captureMessage(errorMsg, {
        level: 'warning',
        tags: { component: 'InteractivePropertyMap' },
      });

      return;
    }

    // Timeout for loading
    const loadTimeout = setTimeout(() => {
      if (!googleMapsLoaded) {
        const errorMsg = 'Google Maps loading timeout (15s)';
        console.error('[InteractivePropertyMap]', errorMsg);
        setMapsError(errorMsg);
        setIsLoading(false);

        Sentry.captureMessage(errorMsg, {
          level: 'error',
          tags: { component: 'InteractivePropertyMap' },
        });
      }
    }, 15000);

    loadGoogleMapsScript(GOOGLE_MAPS_API_KEY)
      .then(() => {
        clearTimeout(loadTimeout);
        console.log('[InteractivePropertyMap] Google Maps script loaded successfully');
        setGoogleMapsLoaded(true);
        setMapsError(null);
      })
      .catch((error) => {
        clearTimeout(loadTimeout);
        console.error('[InteractivePropertyMap] Failed to load Google Maps script:', error);
        const errorMsg = error instanceof Error ? error.message : 'Failed to load Google Maps';
        setMapsError(errorMsg);
        setIsLoading(false);

        // Report to Sentry
        Sentry.captureException(error, {
          tags: { component: 'InteractivePropertyMap' },
          extra: { apiKeyConfigured: true },
        });
      });

    return () => clearTimeout(loadTimeout);
  }, []); // Run once on mount

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || !googleMapsLoaded || typeof google === 'undefined') return;

    // Create map centered on Sri Lanka
    const map = new google.maps.Map(mapRef.current, {
      center: { lat: 7.8731, lng: 80.7718 }, // Sri Lanka center
      zoom: 8,
      mapTypeControl: true,
      streetViewControl: false,
      fullscreenControl: true,
    });

    mapInstanceRef.current = map;

    // Initialize geocoder
    geocoderRef.current = new google.maps.Geocoder();

    // Initialize directions renderer
    const directionsRenderer = new google.maps.DirectionsRenderer({
      map: map,
      suppressMarkers: true, // We'll add custom markers
      polylineOptions: {
        strokeColor: '#4285F4',
        strokeWeight: 5,
      },
    });
    directionsRendererRef.current = directionsRenderer;

    // Add click listener for pinning locations
    map.addListener('click', async (e: google.maps.MapMouseEvent) => {
      if (!e.latLng || !clickMode) return;

      const lat = e.latLng.lat();
      const lng = e.latLng.lng();

      // Reverse geocode to get address and administrative data
      const geocodedData = await reverseGeocode(lat, lng);

      if (clickMode === 'start') {
        // Place starting point marker (blue/B)
        if (startMarkerRef.current) {
          startMarkerRef.current.setMap(null);
        }

        const marker = new google.maps.Marker({
          position: { lat, lng },
          map: map,
          title: 'Starting Point',
          label: 'B',
          icon: {
            url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
          },
          animation: google.maps.Animation.DROP,
        });

        startMarkerRef.current = marker;

        // Center map on starting point
        map.setCenter({ lat, lng });
        map.setZoom(15);

        // Notify parent
        onStartingPointSelected({
          address: geocodedData.formattedAddress,
          latitude: lat,
          longitude: lng,
        });

        setStartingAddress(geocodedData.formattedAddress);
        // Pre-fill the starting point name for report (user can edit)
        setStartingPointName(geocodedData.formattedAddress);
        setClickMode(null); // Reset click mode
      } else if (clickMode === 'property') {
        // Place property marker (red/A)
        if (propertyMarkerRef.current) {
          propertyMarkerRef.current.setMap(null);
        }

        const marker = new google.maps.Marker({
          position: { lat, lng },
          map: map,
          title: 'Property Location',
          label: 'A',
          animation: google.maps.Animation.DROP,
        });

        propertyMarkerRef.current = marker;

        // Center map on property
        map.setCenter({ lat, lng });
        map.setZoom(15);

        // Notify parent with geocoding data
        onPropertySelected({
          latitude: lat,
          longitude: lng,
          district: geocodedData.district,
          province: geocodedData.province,
          village: geocodedData.village,
        });

        setPropertyAddress(geocodedData.formattedAddress);
        setClickMode(null); // Reset click mode
      }
    });

    setIsLoading(false);
  }, [googleMapsLoaded, clickMode, onPropertySelected, onStartingPointSelected]);

  // Setup property autocomplete
  useEffect(() => {
    if (!googleMapsLoaded) return;

    const input = document.getElementById('property-search-input') as HTMLInputElement;
    if (!input || typeof google === 'undefined') return;

    const autocomplete = new google.maps.places.Autocomplete(input, {
      componentRestrictions: { country: 'lk' },
      fields: ['formatted_address', 'geometry', 'name', 'address_components'],
    });

    autocomplete.addListener('place_changed', async () => {
      const place = autocomplete.getPlace();
      if (place.geometry && place.geometry.location) {
        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();

        // Add property marker
        if (propertyMarkerRef.current) {
          propertyMarkerRef.current.setMap(null);
        }

        const marker = new google.maps.Marker({
          position: { lat, lng },
          map: mapInstanceRef.current,
          title: 'Property Location',
          label: 'A',
          animation: google.maps.Animation.DROP,
        });

        propertyMarkerRef.current = marker;

        // Center map on property
        mapInstanceRef.current?.setCenter({ lat, lng });
        mapInstanceRef.current?.setZoom(15);

        // Extract geocoding data
        const geocodedData = await reverseGeocode(lat, lng);

        // Notify parent with geocoding data
        onPropertySelected({
          latitude: lat,
          longitude: lng,
          district: geocodedData.district,
          province: geocodedData.province,
          village: geocodedData.village,
        });

        setPropertyAddress(place.formatted_address || '');
      }
    });

    propertyAutocompleteRef.current = autocomplete;
  }, [googleMapsLoaded, onPropertySelected]);

  // Setup starting point autocomplete
  useEffect(() => {
    if (!googleMapsLoaded) return;

    const input = document.getElementById('starting-point-search-input') as HTMLInputElement;
    if (!input || typeof google === 'undefined') return;

    const autocomplete = new google.maps.places.Autocomplete(input, {
      componentRestrictions: { country: 'lk' },
      fields: ['formatted_address', 'geometry', 'name'],
    });

    autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace();
      if (place.geometry && place.geometry.location) {
        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();

        // Add starting point marker
        if (startMarkerRef.current) {
          startMarkerRef.current.setMap(null);
        }

        const marker = new google.maps.Marker({
          position: { lat, lng },
          map: mapInstanceRef.current,
          title: 'Starting Point',
          label: 'B',
          icon: {
            url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
          },
          animation: google.maps.Animation.DROP,
        });

        startMarkerRef.current = marker;

        // Notify parent
        onStartingPointSelected({
          address: place.name || place.formatted_address || '',
          latitude: lat,
          longitude: lng,
        });

        setStartingAddress(place.formatted_address || '');

        // Pre-fill the starting point name for report (user can edit)
        const placeName = place.name || place.formatted_address || '';
        setStartingPointName(placeName);
      }
    });

    startAutocompleteRef.current = autocomplete;
  }, [googleMapsLoaded, onStartingPointSelected]);

  // Sync manual coordinates when property marker is placed
  useEffect(() => {
    if (propertyMarkerRef.current) {
      const position = propertyMarkerRef.current.getPosition();
      if (position) {
        setManualLatitude(position.lat().toFixed(6));
        setManualLongitude(position.lng().toFixed(6));
      }
    }
  }, [propertyMarkerRef.current?.getPosition()]);

  // Handle manual coordinate input and update marker
  const handleManualCoordinateChange = async (lat: string, lng: string) => {
    const latNum = parseFloat(lat);
    const lngNum = parseFloat(lng);

    // Validate coordinates
    if (isNaN(latNum) || isNaN(lngNum)) {
      return;
    }

    if (latNum < -90 || latNum > 90 || lngNum < -180 || lngNum > 180) {
      toast.error('Invalid coordinates. Latitude: -90 to 90, Longitude: -180 to 180', {
        duration: 4000,
        icon: '⚠️'
      });
      return;
    }

    // Update marker on map
    if (mapInstanceRef.current) {
      if (propertyMarkerRef.current) {
        propertyMarkerRef.current.setMap(null);
      }

      const marker = new google.maps.Marker({
        position: { lat: latNum, lng: lngNum },
        map: mapInstanceRef.current,
        title: 'Property Location',
        label: 'A',
        animation: google.maps.Animation.DROP,
      });

      propertyMarkerRef.current = marker;
      mapInstanceRef.current.setCenter({ lat: latNum, lng: lngNum });
      mapInstanceRef.current.setZoom(15);

      // Reverse geocode to get address components
      const geocodedData = await reverseGeocode(latNum, lngNum);
      onPropertySelected({
        latitude: latNum,
        longitude: lngNum,
        district: geocodedData.district,
        province: geocodedData.province,
        village: geocodedData.village,
      });

      // Update property address to enable the route generation button
      setPropertyAddress(geocodedData.formattedAddress);
    }
  };

  // Reverse geocode to extract address and administrative divisions
  const reverseGeocode = async (lat: number, lng: number): Promise<GeocodingData & { formattedAddress: string }> => {
    if (!geocoderRef.current) {
      return { formattedAddress: `${lat.toFixed(6)}, ${lng.toFixed(6)}` };
    }

    try {
      const result = await geocoderRef.current.geocode({ location: { lat, lng } });

      if (!result.results || result.results.length === 0) {
        return { formattedAddress: `${lat.toFixed(6)}, ${lng.toFixed(6)}` };
      }

      const place = result.results[0];
      const formattedAddress = place.formatted_address || '';

      // Extract administrative divisions from address_components
      let district = '';
      let province = '';
      let village = '';
      let administrativeArea = '';

      for (const component of place.address_components) {
        const types = component.types;

        // District (administrative_area_level_2 in Sri Lanka)
        if (types.includes('administrative_area_level_2')) {
          district = component.long_name;
        }

        // Province (administrative_area_level_1 in Sri Lanka)
        if (types.includes('administrative_area_level_1')) {
          province = component.long_name;
        }

        // Village/Locality (locality or sublocality)
        if (types.includes('locality')) {
          village = component.long_name;
        } else if (types.includes('sublocality') && !village) {
          village = component.long_name;
        }

        // Administrative area level 3 (sometimes used for DS divisions)
        if (types.includes('administrative_area_level_3')) {
          administrativeArea = component.long_name;
        }
      }

      return {
        formattedAddress,
        district,
        province,
        village,
        administrativeArea,
      };
    } catch (error) {
      console.error('Reverse geocoding failed:', error);
      return { formattedAddress: `${lat.toFixed(6)}, ${lng.toFixed(6)}` };
    }
  };

  // Helper function - kept for potential future use
  // Security: Uses textContent instead of innerHTML to prevent XSS
  const extractRoadName = (htmlInstruction: string): string => {
    // Strip HTML tags safely using regex instead of innerHTML
    const text = htmlInstruction.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    const match = text.match(/(?:onto|along|on)\s+([^,\.]+)/i);
    return match ? match[1].trim() : '';
  };

  const handleGenerateAccessText = () => {
    // Validation for road conditions
    if (roadConditions.length === 0) {
      toast.error('Please select at least one road condition before generating text.', {
        duration: 4000,
        icon: '⚠️'
      });
      return;
    }
    performAccessTextGeneration();
  };

  const performAccessTextGeneration = async () => {
    setTransformingAccess(true);

    // Additional validation
    if (!startingPointName || !startingPointName.trim()) {
      toast.error('Please enter a starting point name first', {
        duration: 4000,
        icon: '✏️'
      });
      setTransformingAccess(false);
      return;
    }

    if (!routeData) {
      toast.error('Please generate a route first before creating access text', {
        duration: 4000,
        icon: '🗺️'
      });
      setTransformingAccess(false);
      return;
    }

    try {
      // DEBUG: Check routeData state
      console.log('[InteractivePropertyMap] routeData state:', routeData);

      // Payload with Google Maps data and road conditions
      const payload: any = {
        starting_point_name: startingPointName.trim(),
        property_position: propertyPosition,
        total_distance_km: routeData?.distance_km || 0,
        total_duration_mins: routeData?.duration_minutes || 0,
        steps: routeData?.steps || [],  // ALWAYS include Google Maps steps
        road_conditions: roadConditions,  // Send road conditions summary
      };

      // DEBUG: Log the payload being sent
      console.log('[InteractivePropertyMap] Sending to transform-access API:', {
        starting_point_name: payload.starting_point_name,
        total_distance_km: payload.total_distance_km,
        total_duration_mins: payload.total_duration_mins,
        steps_count: payload.steps.length,
        steps_sample: payload.steps.slice(0, 3),  // First 3 steps
        road_conditions: payload.road_conditions
      });

      // Call backend API
      const transformResponse = await api.post('/api/maps/transform-access', payload);

      const professionalText = transformResponse.data.professional_text;

      // DEBUG: Log the response
      console.log('[InteractivePropertyMap] Received professional text:', professionalText);

      setGeneratedAccessText(professionalText);

      // Update parent with all data
      onRouteGenerated({
        distance: routeData?.distance || '',
        duration: routeData?.duration || '',
        distance_km: routeData?.distance_km,
        duration_minutes: routeData?.duration_minutes,
        accessText: professionalText,
        steps: routeData?.steps || [],
        mapImageUrl: mapImageUrl || undefined,
        road_conditions: roadConditions,
        entry_mode: 'simple',  // Always use simple mode now
      });
    } catch (error) {
      console.error('Failed to generate access text:', error);
      toast.error('Failed to generate access text. Please try again.', {
        duration: 4000,
        icon: '❌'
      });
    } finally {
      setTransformingAccess(false);
    }
  };


  // Generate route
  const generateRoute = async () => {
    if (!propertyMarkerRef.current || !startMarkerRef.current) {
      toast.error('Please select both property location and starting point on the map', {
        duration: 4000,
        icon: '📍'
      });
      return;
    }

    if (!startingPointName.trim()) {
      toast.error('Please enter a starting point name for the report (e.g., "Clock tower junction of Kurunegala town")', {
        duration: 5000,
        icon: '✏️'
      });
      return;
    }

    setGenerating(true);

    const directionsService = new google.maps.DirectionsService();

    const request: google.maps.DirectionsRequest = {
      origin: startMarkerRef.current.getPosition()!,
      destination: propertyMarkerRef.current.getPosition()!,
      travelMode: google.maps.TravelMode.DRIVING,
    };

    directionsService.route(request, async (result, status) => {
      if (status === google.maps.DirectionsStatus.OK && result) {
        // Display route on map
        directionsRendererRef.current?.setDirections(result);

        // Hide custom markers (directions renderer will show A/B)
        propertyMarkerRef.current?.setMap(null);
        startMarkerRef.current?.setMap(null);

        const route = result.routes[0];
        const leg = route.legs[0];

        // Auto-detect property position from directions (last step)
        const detectedPosition = detectPropertyPosition(leg.steps || []);
        if (detectedPosition) {
          setPropertyPosition(detectedPosition);
          console.log('[InteractivePropertyMap] Auto-detected property position:', detectedPosition);
        }

        // Extract route data with both text and numeric values
        const distanceKm = (leg.distance?.value || 0) / 1000;  // Convert meters to km
        const durationMins = Math.round((leg.duration?.value || 0) / 60);  // Convert seconds to mins

        // Transform Google Maps steps to backend format
        const transformedSteps = (leg.steps || []).map((step: any) => ({
          instruction: step.instructions || step.html_instructions || '',
          distance: step.distance?.text || '',
          duration: step.duration?.text || '',
          maneuver: step.maneuver || ''
        }));

        const routeInfo = {
          distance: leg.distance?.text || '',
          duration: leg.duration?.text || '',
          distance_km: distanceKm,
          duration_minutes: durationMins,
          accessText: '', // Will be updated after AI transformation
          steps: transformedSteps,  // Use transformed steps instead of raw Google Maps steps
        };

        setRouteData(routeInfo);

        // Prefetch nearby facilities data in parallel (non-blocking)
        if (onFacilitiesFetched && propertyMarkerRef.current) {
          const propertyPos = propertyMarkerRef.current.getPosition()!;
          const authToken = authTokenStorage.getToken();

          console.log('[InteractivePropertyMap] Prefetching nearby facilities data...');
          console.log('[InteractivePropertyMap] Auth token present:', !!authToken);

          if (!authToken) {
            console.warn('[InteractivePropertyMap] No auth token found, skipping facilities prefetch');
            return;
          }

          // Fetch facilities in background (don't await, don't block)
          api.post('/api/locality/nearby-facilities', {
            latitude: propertyPos.lat(),
            longitude: propertyPos.lng(),
            radius_meters: 5000, // Default 5km radius
          })
          .then(facilitiesResponse => {
            console.log('[InteractivePropertyMap] Facilities prefetched successfully:', facilitiesResponse.data);

            // Process the facilities data
            const allFacilities: any[] = [];
            Object.entries(facilitiesResponse.data.facilities || {}).forEach(([category, facilities]) => {
              (facilities as any[]).forEach((facility: any) => {
                allFacilities.push({
                  ...facility,
                  type: category,
                  selected: false // Initialize as unselected
                });
              });
            });

            // Notify parent with prefetched data
            onFacilitiesFetched({
              facilities: allFacilities,
              majorTown: facilitiesResponse.data.major_town,
              transport: facilitiesResponse.data.transport,
            });
          })
          .catch(facilitiesError => {
            console.error('[InteractivePropertyMap] Failed to prefetch facilities:', facilitiesError);
            if (facilitiesError.response) {
              console.error('[InteractivePropertyMap] Error response:', facilitiesError.response.status, facilitiesError.response.data);
            }
            // Don't show error to user - this is a background prefetch
          });
        }

        // Generate static map image via backend
        try {
          const startPos = startMarkerRef.current!.getPosition()!;
          const propertyPos = propertyMarkerRef.current!.getPosition()!;

          // Get encoded polyline from route (extract the points string)
          console.log('[InteractivePropertyMap] Route overview_polyline:', route.overview_polyline);
          const polyline = (typeof route.overview_polyline === 'object' && route.overview_polyline !== null)
            ? (route.overview_polyline as any).points || ''
            : route.overview_polyline || '';

          console.log('[InteractivePropertyMap] Extracted polyline:', polyline);

          if (!polyline || typeof polyline !== 'string') {
            console.error('[InteractivePropertyMap] No valid polyline available from route. Route object:', route);
            // Preserve existing mapImageUrl if available
            onRouteGenerated({
              ...routeInfo,
              mapImageUrl: mapImageUrl || undefined,
            });
            return;
          }

          console.log('[InteractivePropertyMap] Calling static-map API with:', {
            origin_lat: startPos.lat(),
            origin_lng: startPos.lng(),
            dest_lat: propertyPos.lat(),
            dest_lng: propertyPos.lng(),
            polyline_length: polyline.length,
          });

          const mapResponse = await api.post('/api/maps/static-map', {
            origin_lat: startPos.lat(),
            origin_lng: startPos.lng(),
            dest_lat: propertyPos.lat(),
            dest_lng: propertyPos.lng(),
            polyline: polyline,
          });

          console.log('[InteractivePropertyMap] Static map response:', mapResponse.data);

          const mapUrl = mapResponse.data.map_url;
          setMapImageUrl(mapUrl);

          console.log('[InteractivePropertyMap] Map image URL set:', mapUrl);

          // Notify parent with map image URL
          onRouteGenerated({
            ...routeInfo,
            mapImageUrl: mapUrl,
          });
        } catch (error: any) {
          console.error('[InteractivePropertyMap] Failed to generate static map:', error);
          console.error('[InteractivePropertyMap] Error response:', error.response?.data);
          // Still notify parent even if map generation fails
          // IMPORTANT: Preserve existing mapImageUrl if available to avoid losing previous map data
          onRouteGenerated({
            ...routeInfo,
            mapImageUrl: mapImageUrl || undefined,
          });
        }
      } else {
        toast.error('Could not generate route: ' + status, {
          duration: 4000,
          icon: '🚫'
        });
      }

      setGenerating(false);
    });
  };

  // Clean HTML from instructions
  // Security: Uses regex instead of innerHTML to prevent XSS
  const cleanInstruction = (html: string): string => {
    // Strip HTML tags safely using regex instead of innerHTML
    return html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  };

  // Detect property position (left/right) from directions
  const detectPropertyPosition = (steps: google.maps.DirectionsStep[]): 'left' | 'right' | null => {
    if (!steps || steps.length === 0) return null;

    // Check the last step for "Destination will be on the left/right"
    const lastStep = steps[steps.length - 1];
    const instruction = cleanInstruction(lastStep.instructions || '').toLowerCase();

    // Common patterns in Google Maps directions
    if (instruction.includes('destination will be on the left') ||
        instruction.includes('destination on the left') ||
        instruction.includes('on your left') ||
        instruction.includes('left side')) {
      return 'left';
    }
    if (instruction.includes('destination will be on the right') ||
        instruction.includes('destination on the right') ||
        instruction.includes('on your right') ||
        instruction.includes('right side')) {
      return 'right';
    }

    // Check second-to-last step too (sometimes it's there)
    if (steps.length >= 2) {
      const secondLastStep = steps[steps.length - 2];
      const secondInstruction = cleanInstruction(secondLastStep.instructions || '').toLowerCase();

      if (secondInstruction.includes('destination will be on the left') ||
          secondInstruction.includes('on your left')) {
        return 'left';
      }
      if (secondInstruction.includes('destination will be on the right') ||
          secondInstruction.includes('on your right')) {
        return 'right';
      }
    }

    return null; // Could not detect
  };

  // Handle fallback address input
  const handleFallbackAddressChange = (data: ManualAddressData) => {
    if (data.coordinates) {
      onPropertySelected({
        latitude: data.coordinates.lat,
        longitude: data.coordinates.lng,
        district: data.district,
        village: data.villageTown,
      });
    }
    setPropertyAddress(data.formattedAddress);
  };

  // Retry loading Google Maps
  const handleRetryMaps = () => {
    setMapsError(null);
    setIsLoading(true);
    setGoogleMapsLoaded(false);

    // Force reload the script
    const existingScript = document.querySelector('script[src*="maps.googleapis.com"]');
    if (existingScript) {
      existingScript.remove();
    }

    loadGoogleMapsScript(GOOGLE_MAPS_API_KEY!)
      .then(() => {
        console.log('[InteractivePropertyMap] Google Maps script reloaded successfully');
        setGoogleMapsLoaded(true);
        setMapsError(null);
        setUseFallbackMode(false);
      })
      .catch((error) => {
        console.error('[InteractivePropertyMap] Failed to reload Google Maps:', error);
        const errorMsg = error instanceof Error ? error.message : 'Failed to reload Google Maps';
        setMapsError(errorMsg);
        setIsLoading(false);
      });
  };

  // Fallback UI when Google Maps is unavailable
  if (mapsError && !googleMapsLoaded) {
    return (
      <div className="space-y-6">
        {/* Error Banner */}
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-amber-900 mb-2">
                Google Maps Unavailable
              </h3>
              <p className="text-sm text-amber-800 mb-4">
                {mapsError}. You can still enter the property location manually below.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleRetryMaps}
                  className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm font-medium"
                >
                  <RefreshCw className="w-4 h-4" />
                  Retry Loading Maps
                </button>
                <button
                  onClick={() => setUseFallbackMode(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-amber-400 text-amber-800 rounded-lg hover:bg-amber-50 transition-colors text-sm font-medium"
                >
                  Continue Without Maps
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Fallback Manual Input */}
        {useFallbackMode && (
          <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-red-600" />
              Property Location (Manual Entry)
            </h3>
            <ManualAddressInput
              onChange={handleFallbackAddressChange}
              showCoordinates={true}
              required={true}
            />

            {propertyAddress && (
              <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  <span className="font-medium">Selected Address:</span> {propertyAddress}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Note about limited functionality */}
        {useFallbackMode && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">Limited Functionality Note:</h4>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Route generation and access directions are not available without Google Maps</li>
              <li>You can still manually enter property coordinates</li>
              <li>Nearby facilities lookup will use the coordinates you provide</li>
              <li>Consider refreshing the page later to try loading Maps again</li>
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search Controls - REORDERED: Property Location FIRST, Starting Point SECOND */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Property Location - FIRST */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="inline w-4 h-4 mr-1 text-red-600" />
            Property Location <span className="text-red-500">*</span>
          </label>

          {/* Toggle between map selection and manual input */}
          <div className="mb-3 flex gap-2">
            <button
              type="button"
              onClick={() => setCoordinateInputMode('map')}
              className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                coordinateInputMode === 'map'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <MapPin className="inline w-4 h-4 mr-1" />
              Select on Map
            </button>
            <button
              type="button"
              onClick={() => setCoordinateInputMode('manual')}
              className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                coordinateInputMode === 'manual'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Navigation className="inline w-4 h-4 mr-1" />
              Enter Coordinates
            </button>
          </div>

          {coordinateInputMode === 'map' ? (
            <>
              <input
                id="property-search-input"
                type="text"
                value={propertyAddress}
                onChange={(e) => setPropertyAddress(e.target.value)}
                placeholder="Search for property address..."
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-red-500 focus:border-red-500"
              />
              <button
                type="button"
                onClick={() => setClickMode('property')}
                disabled={clickMode === 'property'}
                className={`mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  clickMode === 'property'
                    ? 'bg-red-600 text-white'
                    : 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-300'
                }`}
              >
                <MousePointer className="w-4 h-4" />
                {clickMode === 'property' ? 'Click on map to pin...' : 'Click to Pin on Map'}
              </button>
            </>
          ) : (
            <div className="space-y-3 bg-gradient-to-br from-red-50 to-orange-50 p-4 rounded-xl border-2 border-red-200">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
                  Latitude
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={manualLatitude}
                  onChange={(e) => setManualLatitude(e.target.value)}
                  placeholder="e.g., 7.234567"
                  className="w-full px-3 py-2.5 border-2 border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 text-sm font-mono bg-white"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
                  Longitude
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={manualLongitude}
                  onChange={(e) => setManualLongitude(e.target.value)}
                  placeholder="e.g., 80.234567"
                  className="w-full px-3 py-2.5 border-2 border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 text-sm font-mono bg-white"
                />
              </div>

              {/* Pin Location Button */}
              <button
                type="button"
                onClick={() => handleManualCoordinateChange(manualLatitude, manualLongitude)}
                disabled={!manualLatitude || !manualLongitude}
                className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-2.5 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                <MapPin className="w-4 h-4" />
                Pin Location on Map
              </button>

              <div className="flex items-start gap-2 mt-2 text-xs text-gray-600 bg-white/60 p-2 rounded-lg">
                <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                <p>
                  Enter GPS coordinates manually (6 decimal places recommended), then click "Pin Location on Map" to mark the property.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Starting Point - SECOND */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <Navigation2 className="inline w-4 h-4 mr-1 text-blue-600" />
            Starting Point Location <span className="text-red-500">*</span>
          </label>
          <input
            id="starting-point-search-input"
            type="text"
            value={startingAddress}
            onChange={(e) => setStartingAddress(e.target.value)}
            placeholder="Search for starting point..."
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="button"
            onClick={() => setClickMode('start')}
            disabled={clickMode === 'start'}
            className={`mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
              clickMode === 'start'
                ? 'bg-blue-600 text-white'
                : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-300'
            }`}
          >
            <MousePointer className="w-4 h-4" />
            {clickMode === 'start' ? 'Click on map to pin...' : 'Click to Pin on Map'}
          </button>
        </div>
      </div>

      {/* REMOVED: Property Position UI - Auto-detection logic remains in background (detectPropertyPosition function at lines 808-846) */}

      {/* Generate Route Button */}
      <button
        onClick={generateRoute}
        disabled={generating || !propertyAddress || !startingAddress || !startingPointName.trim()}
        className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-lg font-semibold rounded-xl hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition-all shadow-lg"
      >
        {generating ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            {transformingAccess ? 'Generating Professional Access Text...' : 'Generating Route...'}
          </>
        ) : (
          <>
            <RouteIcon className="w-5 h-5" />
            Generate Route & Fetch Location Data
          </>
        )}
      </button>

      {/* Interactive Map */}
      <div className="relative">
        <div
          ref={mapRef}
          className="w-full h-[500px] rounded-xl border-4 border-gray-300 shadow-2xl"
        />
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-xl">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600" />
          </div>
        )}
      </div>

      {/* Route Summary & Directions */}
      {routeData && (
        <div className="space-y-4">
          {/* Route Summary */}
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-6">
            <h3 className="text-lg font-bold text-green-900 mb-3 flex items-center gap-2">
              <RouteIcon className="w-5 h-5" />
              Route Summary
            </h3>
            <div className="space-y-3">
              {/* Starting Point Name - Inline Editable */}
              <div className="bg-white rounded-lg p-3 border border-green-200">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Starting Point (for Report)
                </label>
                <input
                  type="text"
                  value={startingPointName}
                  onChange={(e) => setStartingPointName(e.target.value)}
                  placeholder='e.g., "Clock tower junction of Kurunegala town"'
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Professional landmark name for the report (editable)
                </p>
              </div>

              {/* Distance and Duration */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Distance:</span>
                  <span className="ml-2 font-bold text-green-900">{routeData.distance}</span>
                </div>
                <div>
                  <span className="text-gray-600">Duration:</span>
                  <span className="ml-2 font-bold text-green-900">{routeData.duration}</span>
                </div>
              </div>
            </div>
          </div>

          {/* MAP IMAGE - shown in same step */}
          {mapImageUrl && (
            <div className="bg-white border-2 border-gray-300 rounded-xl overflow-hidden shadow-lg">
              <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-blue-600" />
                  Route Map (for Report)
                </h4>
              </div>
              <img
                src={mapImageUrl}
                alt="Route Map"
                className="w-full h-80 object-cover"
              />
            </div>
          )}

          {/* Road Conditions Section - SUMMARY ONLY */}
          {routeData && (
            <div className="bg-white border-2 border-gray-200 rounded-xl p-6 mt-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <Navigation className="w-5 h-5 text-blue-600" />
                  Road Conditions
                </h3>
              </div>

              {/* Road Conditions Summary */}
              <div className="mt-4">
                <RoadConditionsSummary
                  roadConditions={roadConditions}
                  onChange={setRoadConditions}
                />
              </div>


              <button
                type="button"
                onClick={handleGenerateAccessText}
                disabled={transformingAccess}
                className="w-full mt-4 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 font-medium transition-colors flex items-center justify-center gap-2"
              >
                {transformingAccess ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Generating Professional Text...
                  </>
                ) : (
                  'Generate Professional Access Text'
                )}
              </button>
            </div>
          )}

          {/* New Professional Access Text - Only shown after generation */}
          {generatedAccessText && (
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border-2 border-blue-400 rounded-xl p-6 shadow-lg">
              <div className="flex items-center gap-2 mb-3">
                <div className="bg-blue-600 text-white px-4 py-1.5 rounded-full text-sm font-bold shadow-md">
                  ACCESS
                </div>
                <span className="text-sm text-blue-800 font-semibold">
                  Professional Access Description (Editable)
                </span>
              </div>
              <textarea
                rows={5}
                value={generatedAccessText}
                onChange={(e) => {
                  const newText = e.target.value;
                  setGeneratedAccessText(newText);
                  // Update parent with edited access text
                  if (routeData) {
                    onRouteGenerated({
                      ...routeData,
                      accessText: newText,
                      mapImageUrl: mapImageUrl || undefined,
                    });
                  }
                }}
                className="w-full px-4 py-3 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-serif text-base shadow-sm bg-white"
                placeholder="Professional access description will appear here..."
              />
              <p className="text-xs text-blue-700 mt-2 flex items-center gap-1">
                <span className="font-bold">✓</span>
                Generated from road segment details. Edit as needed for your report.
              </p>
            </div>
          )}

          {/* Turn-by-Turn Directions - HIDDEN (data still used for prompt generation) */}
        </div>
      )}

      {/* Instructions */}
      {!routeData && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">How to use:</h4>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li>Set property location first - search on map or enter coordinates manually</li>
            <li>Click on suggested location or enter precise GPS coordinates</li>
            <li>Search for your starting point in the second box</li>
            <li>Click on the suggested starting point</li>
            <li>Enter a descriptive name for the starting point</li>
            <li>Click "Generate Route & Fetch Location Data"</li>
            <li>Select road conditions and generate professional access text</li>
          </ol>
        </div>
      )}


    </div>
  );
}
