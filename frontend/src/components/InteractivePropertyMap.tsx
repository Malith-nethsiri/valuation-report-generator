import { useEffect, useRef, useState } from 'react';
import { MapPin, Navigation2, Route as RouteIcon, Loader2, MousePointer, Navigation } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import type { RoadSegment, RoadCondition } from '../types';
import { RoadConditionsSummary } from './RoadConditionsSummary';
import { authTokenStorage } from '../utils/secureStorage';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Props {
  onPropertySelected: (data: {
    address: string;
    latitude: number;
    longitude: number;
    formattedAddress: string;
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
    accessText: string;
    steps: any[];
    mapImageUrl?: string;
    road_conditions?: RoadCondition[];
    road_segments?: RoadSegment[];
    entry_mode?: 'simple' | 'advanced';
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
  initialEntryMode?: 'simple' | 'advanced';
  initialRoadConditions?: RoadCondition[];
  initialRoadSegments?: RoadSegment[];
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
  initialEntryMode = 'simple',
  initialRoadConditions = [],
  initialRoadSegments = [],
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
  const [routeData, setRouteData] = useState<any>(null);
  const [generating, setGenerating] = useState(false);
  const [transformingAccess, setTransformingAccess] = useState(false);
  const [mapImageUrl, setMapImageUrl] = useState<string | null>(null);
  const [clickMode, setClickMode] = useState<'start' | 'property' | null>(null);
  const geocoderRef = useRef<google.maps.Geocoder | null>(null);

  // Road segments state
  const [roadSegments, setRoadSegments] = useState<RoadSegment[]>([]);
  const [expandedSegments, setExpandedSegments] = useState<Set<string>>(new Set());
  const [generatedAccessText, setGeneratedAccessText] = useState<string>(''); // New professional access text

  // Dual-mode state (NEW)
  const [entryMode, setEntryMode] = useState<'simple' | 'advanced'>('simple');
  const [roadConditions, setRoadConditions] = useState<RoadCondition[]>([]);
  const [showModeConfirmModal, setShowModeConfirmModal] = useState(false);
  const [pendingModeSwitch, setPendingModeSwitch] = useState<'simple' | 'advanced' | null>(null);
  const [showWarningModal, setShowWarningModal] = useState(false);
  const [warningSegmentCount, setWarningSegmentCount] = useState(0);

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

  // Track if we've initialized the mode (to prevent resetting user's choice)
  const modeInitializedRef = useRef(false);

  // Restore entry mode and road conditions data (NEW) - only on first mount
  useEffect(() => {
    // Only run once on initial mount
    if (modeInitializedRef.current) return;
    modeInitializedRef.current = true;

    if (initialEntryMode) {
      console.log('[InteractivePropertyMap] Restoring entry mode:', initialEntryMode);
      setEntryMode(initialEntryMode);
    }

    // Restore appropriate data based on mode
    if (initialEntryMode === 'simple' && initialRoadConditions && initialRoadConditions.length > 0) {
      console.log('[InteractivePropertyMap] Restoring simple mode road conditions:', initialRoadConditions);
      setRoadConditions(initialRoadConditions);
    } else if (initialEntryMode === 'advanced' && initialRoadSegments && initialRoadSegments.length > 0) {
      console.log('[InteractivePropertyMap] Restoring advanced mode road segments:', initialRoadSegments);
      setRoadSegments(initialRoadSegments);
    }
  }, [initialEntryMode, initialRoadConditions, initialRoadSegments]);

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || typeof google === 'undefined') return;

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
          address: geocodedData.formattedAddress,
          latitude: lat,
          longitude: lng,
          formattedAddress: geocodedData.formattedAddress,
          district: geocodedData.district,
          province: geocodedData.province,
          village: geocodedData.village,
        });

        setPropertyAddress(geocodedData.formattedAddress);
        setClickMode(null); // Reset click mode
      }
    });

    setIsLoading(false);
  }, [clickMode, onPropertySelected, onStartingPointSelected]);

  // Setup property autocomplete
  useEffect(() => {
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
          address: place.name || place.formatted_address || '',
          latitude: lat,
          longitude: lng,
          formattedAddress: place.formatted_address || '',
          district: geocodedData.district,
          province: geocodedData.province,
          village: geocodedData.village,
        });

        setPropertyAddress(place.formatted_address || '');
      }
    });

    propertyAutocompleteRef.current = autocomplete;
  }, [onPropertySelected]);

  // Setup starting point autocomplete
  useEffect(() => {
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
  }, [onStartingPointSelected]);

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

  // Helper function to extract road names from Google Maps instructions
  const extractRoadName = (htmlInstruction: string): string => {
    const temp = document.createElement('div');
    temp.innerHTML = htmlInstruction;
    const text = temp.textContent || temp.innerText || '';
    const match = text.match(/(?:onto|along|on)\s+([^,\.]+)/i);
    return match ? match[1].trim() : '';
  };

  // Road segment handlers - Removed modal-based editing

  // Inline segment editing handlers
  const toggleSegmentExpansion = (segmentId: string) => {
    const newExpanded = new Set(expandedSegments);
    if (newExpanded.has(segmentId)) {
      newExpanded.delete(segmentId);
    } else {
      newExpanded.add(segmentId);
    }
    setExpandedSegments(newExpanded);
  };

  const updateSegmentField = (segmentId: string, field: string, value: any) => {
    const newSegments = roadSegments.map(seg => {
      if (seg.id === segmentId) {
        const updated = { ...seg, [field]: value };
        // Auto-update has_details if road_type and surface_condition are set
        if (updated.road_type && updated.surface_condition) {
          updated.has_details = true;
        }
        // Auto-update distance_text when distance_km changes
        if (field === 'distance_km') {
          const km = parseFloat(value) || 0;
          updated.distance_text = km >= 1 ? `${km.toFixed(1)} km` : `${Math.round(km * 1000)} m`;
        }
        return updated;
      }
      return seg;
    });
    setRoadSegments(newSegments);
  };

  const handleDeleteSegment = (segmentId: string) => {
    const newSegments = roadSegments
      .filter(s => s.id !== segmentId)
      .map((s, idx) => ({ ...s, order: idx }));
    setRoadSegments(newSegments);
  };

  const handleMoveUp = (segmentIndex: number) => {
    if (segmentIndex === 0) return;
    const newSegments = [...roadSegments];
    [newSegments[segmentIndex - 1], newSegments[segmentIndex]] =
      [newSegments[segmentIndex], newSegments[segmentIndex - 1]];
    newSegments.forEach((s, idx) => s.order = idx);
    setRoadSegments(newSegments);
  };

  const handleMoveDown = (segmentIndex: number) => {
    if (segmentIndex === roadSegments.length - 1) return;
    const newSegments = [...roadSegments];
    [newSegments[segmentIndex], newSegments[segmentIndex + 1]] =
      [newSegments[segmentIndex + 1], newSegments[segmentIndex]];
    newSegments.forEach((s, idx) => s.order = idx);
    setRoadSegments(newSegments);
  };

  const handleMergeWithNext = (segmentIndex: number) => {
    if (segmentIndex === roadSegments.length - 1) return;

    const current = roadSegments[segmentIndex];
    const next = roadSegments[segmentIndex + 1];

    // Combine segments
    const merged: RoadSegment = {
      id: current.id,
      order: segmentIndex,
      // Combine instructions
      instruction: current.instruction && next.instruction
        ? `${current.instruction}, then ${next.instruction}`
        : current.instruction || next.instruction,
      // Combine road names
      road_name: current.road_name && next.road_name
        ? `${current.road_name} / ${next.road_name}`
        : current.road_name || next.road_name,
      // Sum distances
      distance_km: (current.distance_km || 0) + (next.distance_km || 0),
      distance_text: `${((current.distance_km || 0) + (next.distance_km || 0)).toFixed(1)} km`,
      // Keep first non-empty road type
      road_type: current.road_type || next.road_type,
      surface_condition: current.surface_condition || next.surface_condition,
      road_width_meters: current.road_width_meters || next.road_width_meters,
      additional_notes: current.additional_notes && next.additional_notes
        ? `${current.additional_notes}; ${next.additional_notes}`
        : current.additional_notes || next.additional_notes,
      has_details: current.has_details || next.has_details,
    };

    // Remove next segment and replace current with merged
    const newSegments = roadSegments
      .filter((_, idx) => idx !== segmentIndex + 1)
      .map((seg, idx) => idx === segmentIndex ? merged : seg)
      .map((s, idx) => ({ ...s, order: idx }));

    setRoadSegments(newSegments);
  };

  const handleSplitSegment = (segmentIndex: number) => {
    const segment = roadSegments[segmentIndex];
    const halfDistance = (segment.distance_km || 0) / 2;

    // Create two segments from one
    const firstHalf: RoadSegment = {
      ...segment,
      id: segment.id,
      order: segmentIndex,
      distance_km: halfDistance,
      distance_text: halfDistance >= 1 ? `${halfDistance.toFixed(1)} km` : `${Math.round(halfDistance * 1000)} m`,
      instruction: segment.instruction ? `${segment.instruction} (first half)` : undefined,
    };

    const secondHalf: RoadSegment = {
      ...segment,
      id: `${segment.id}-split-${Date.now()}`,
      order: segmentIndex + 1,
      distance_km: halfDistance,
      distance_text: halfDistance >= 1 ? `${halfDistance.toFixed(1)} km` : `${Math.round(halfDistance * 1000)} m`,
      instruction: segment.instruction ? `${segment.instruction} (second half)` : undefined,
      // Clear details for second half so user can fill them in separately
      road_type: undefined,
      surface_condition: undefined,
      road_width_meters: undefined,
      additional_notes: undefined,
      has_details: false,
    };

    // Insert both halves
    const newSegments = [
      ...roadSegments.slice(0, segmentIndex),
      firstHalf,
      secondHalf,
      ...roadSegments.slice(segmentIndex + 1),
    ].map((s, idx) => ({ ...s, order: idx }));

    setRoadSegments(newSegments);
  };

  const handleAddSegment = () => {
    // Add a new blank segment
    const newSegment: RoadSegment = {
      id: `segment-${Date.now()}`,
      order: roadSegments.length,
      has_details: false,
    };
    setRoadSegments([...roadSegments, newSegment]);
  };

  // Helper function to generate road segments from route data
  const generateSegmentsFromRoute = (): RoadSegment[] => {
    if (!routeData || !routeData.steps || routeData.steps.length === 0) {
      return [];
    }

    return routeData.steps.map((step: any, idx: number) => {
      const instruction = cleanInstruction(step.instruction || '');
      const roadNameMatch = instruction.match(/(?:onto|along|on)\s+([A-Z][A-Za-z\s]+(?:Road|Street|Avenue|Lane|Highway|Mawatha|Way))/i);
      const roadName = roadNameMatch ? roadNameMatch[1] : '';

      // Handle distance - could be string or number
      let distanceKm = 0;
      let distanceText = '';

      if (typeof step.distance === 'string') {
        distanceText = step.distance;
        distanceKm = parseFloat(step.distance.replace(/[^\d.]/g, '')) || 0;
      } else if (typeof step.distance === 'number') {
        distanceKm = step.distance;
        distanceText = `${step.distance} km`;
      }

      return {
        id: `segment-${idx}`,
        order: idx,
        instruction: instruction,
        road_name: roadName,
        distance_km: distanceKm,
        distance_text: distanceText,
        has_details: false,
      };
    });
  };

  // Mode switching handlers (NEW)
  const handleModeSwitch = (newMode: 'simple' | 'advanced') => {
    if (newMode === entryMode) return; // Already in this mode

    // Check if user has data in current mode
    const hasSimpleData = roadConditions.length > 0;
    const hasAdvancedData = roadSegments.some(s => s.has_details);

    if ((entryMode === 'simple' && hasSimpleData) ||
        (entryMode === 'advanced' && hasAdvancedData)) {
      // Show confirmation modal - data will be lost
      setPendingModeSwitch(newMode);
      setShowModeConfirmModal(true);
    } else {
      // No data, switch freely
      performModeSwitch(newMode);
    }
  };

  const performModeSwitch = (newMode: 'simple' | 'advanced') => {
    // Clear data when switching modes
    if (newMode === 'simple') {
      setRoadConditions([]);  // Start fresh
      setRoadSegments([]);     // Clear advanced data
    } else {
      // Switching to advanced mode - auto-generate segments from route
      setRoadConditions([]);   // Clear simple data
      const segments = generateSegmentsFromRoute();
      if (segments.length > 0) {
        setRoadSegments(segments);
        toast.success(`Generated ${segments.length} road segments from route. Expand each to add details.`, {
          duration: 4000,
          icon: '⚙️'
        });
      } else {
        setRoadSegments([]);
        toast.error('No route data available. Please generate a route first.', {
          duration: 3000
        });
      }
    }

    setEntryMode(newMode);
    setShowModeConfirmModal(false);
    setPendingModeSwitch(null);
  };

  const handleGenerateAccessText = () => {
    // Validation based on mode
    if (entryMode === 'simple') {
      // SIMPLE MODE validation
      if (roadConditions.length === 0) {
        toast.error('Please select at least one road condition before generating text.', {
          duration: 4000,
          icon: '⚠️'
        });
        return;
      }
      performAccessTextGeneration();
    } else {
      // ADVANCED MODE validation
      const segmentsWithoutDetails = roadSegments.filter(s => !s.has_details);
      if (segmentsWithoutDetails.length > 0) {
        setWarningSegmentCount(segmentsWithoutDetails.length);
        setShowWarningModal(true);
      } else {
        performAccessTextGeneration();
      }
    }
  };

  const performAccessTextGeneration = async () => {
    setShowWarningModal(false);
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
      // Base payload with Google Maps data
      const payload: any = {
        starting_point_name: startingPointName.trim(),
        property_position: propertyPosition,
        total_distance_km: routeData?.distance_km || 0,
        total_duration_mins: routeData?.duration_minutes || 0,
        steps: routeData?.steps || [],  // ALWAYS include Google Maps steps
      };

      // Add mode-specific data
      if (entryMode === 'simple') {
        // Send road_conditions array (simple mode)
        payload.road_conditions = roadConditions;
      } else {
        // Send road_segments array (advanced mode)
        payload.road_segments = roadSegments.map(seg => ({
          // Google Maps data (from directions API)
          google_maps_data: {
            instruction: seg.instruction || '',
            road_name: seg.road_name || '',
            distance_km: seg.distance_km || 0,
            distance_text: seg.distance_text || '',
          },
          // User-entered details (from manual input)
          user_details: {
            road_type: seg.road_type,
            surface_condition: seg.surface_condition,
            road_width_meters: seg.road_width_meters,
            additional_notes: seg.additional_notes,
            has_details: seg.has_details,
          },
        }));
      }

      // Call backend API
      const transformResponse = await axios.post(`${API_URL}/api/maps/transform-access`, payload);

      const professionalText = transformResponse.data.professional_text;
      setGeneratedAccessText(professionalText);

      // Update parent with all data including mode
      onRouteGenerated({
        distance: routeData?.distance_text || '',
        duration: routeData?.duration_text || '',
        accessText: professionalText,
        steps: routeData?.steps || [],
        mapImageUrl: mapImageUrl || undefined,
        road_conditions: entryMode === 'simple' ? roadConditions : undefined,
        road_segments: entryMode === 'advanced' ? roadSegments : undefined,
        entry_mode: entryMode,  // NEW: Save mode choice
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

        const routeInfo = {
          distance: leg.distance?.text || '',
          duration: leg.duration?.text || '',
          distance_km: distanceKm,
          duration_minutes: durationMins,
          accessText: '', // Will be updated after AI transformation
          steps: leg.steps || [],
        };

        setRouteData(routeInfo);

        // Initialize road segments from Google Maps steps
        const initialSegments: RoadSegment[] = (leg.steps || []).map((step: any, idx: number) => {
          const roadName = extractRoadName(step.html_instructions || '');
          const distanceKm = (step.distance?.value || 0) / 1000;

          return {
            id: `segment-${Date.now()}-${idx}`,
            order: idx,
            instruction: cleanInstruction(step.html_instructions || step.instructions || ''), // Store full turn-by-turn instruction
            road_name: roadName || '',
            distance_km: distanceKm,
            distance_text: step.distance?.text || '',
            has_details: false,
          };
        });
        setRoadSegments(initialSegments);

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
          axios.post(`${API_URL}/api/locality/nearby-facilities`, {
            latitude: propertyPos.lat(),
            longitude: propertyPos.lng(),
            radius_meters: 5000, // Default 5km radius
          }, {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${authToken}`
            }
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
            onRouteGenerated(routeInfo);
            return;
          }

          console.log('[InteractivePropertyMap] Calling static-map API with:', {
            origin_lat: startPos.lat(),
            origin_lng: startPos.lng(),
            dest_lat: propertyPos.lat(),
            dest_lng: propertyPos.lng(),
            polyline_length: polyline.length,
          });

          const mapResponse = await axios.post(`${API_URL}/api/maps/static-map`, {
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
          onRouteGenerated(routeInfo);
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
  const cleanInstruction = (html: string): string => {
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    return tempDiv.textContent || tempDiv.innerText || '';
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

  return (
    <div className="space-y-6">
      {/* Search Controls - STARTING POINT FIRST */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Starting Point Search - FIRST */}
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

        {/* Property Location Search - SECOND */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="inline w-4 h-4 mr-1 text-red-600" />
            Property Location <span className="text-red-500">*</span>
          </label>
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
        </div>
      </div>

      {/* Property Position Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Property Position (relative to road) - <span className="text-green-600 font-normal">Auto-detected from directions</span>
        </label>
        <div className="flex gap-2 max-w-md">
          <button
            type="button"
            onClick={() => setPropertyPosition('left')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              propertyPosition === 'left'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
            }`}
          >
            Left Side
          </button>
          <button
            type="button"
            onClick={() => setPropertyPosition('right')}
            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
              propertyPosition === 'right'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
            }`}
          >
            Right Side
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          This will be auto-detected when you generate the route. You can override if needed.
        </p>
      </div>

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

          {/* Road Conditions Section - DUAL MODE */}
          {routeData && (
            <div className="bg-white border-2 border-gray-200 rounded-xl p-6 mt-6">
              {/* Mode Switcher Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <Navigation className="w-5 h-5 text-blue-600" />
                  Road Conditions
                </h3>

                <div className="inline-flex rounded-lg border border-gray-300 bg-gray-100 p-1">
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('simple')}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                      entryMode === 'simple'
                        ? 'bg-white text-blue-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    🚀 Quick Entry
                  </button>
                  <button
                    type="button"
                    onClick={() => handleModeSwitch('advanced')}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                      entryMode === 'advanced'
                        ? 'bg-white text-blue-700 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    ⚙️ Detailed Entry
                  </button>
                </div>
              </div>

              {/* SIMPLE MODE: RoadConditionsSummary */}
              {entryMode === 'simple' && (
                <div className="mt-4">
                  <RoadConditionsSummary
                    roadConditions={roadConditions}
                    onChange={setRoadConditions}
                  />
                </div>
              )}

              {/* ADVANCED MODE: Per-Segment Editor */}
              {entryMode === 'advanced' && (
                <div className="space-y-3 mb-4">
                  {roadSegments.length > 0 ? (
                    roadSegments.map((segment, idx) => {
                      const isExpanded = expandedSegments.has(segment.id);
                  const roadTypeOptions = [
                    { value: '', label: 'Select type...' },
                    { value: 'paved_road', label: 'Paved Road / Asphalt' },
                    { value: 'carpet_road', label: 'Carpet Road' },
                    { value: 'gravel_road', label: 'Gravel Road' },
                    { value: 'sand_road', label: 'Sand Road' },
                    { value: 'earth_road', label: 'Earth Road' },
                  ];
                  const conditionOptions = ['', 'excellent', 'good', 'fair', 'poor'];

                  return (
                    <div
                      key={segment.id}
                      className={`border-2 rounded-lg overflow-hidden transition-all ${
                        segment.has_details ? 'border-green-400 bg-green-50/50' : 'border-gray-300 bg-white'
                      }`}
                    >
                      {/* Header */}
                      <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
                        <div className="flex items-center justify-between gap-3 mb-3">
                          <div className="flex items-center gap-3 flex-1">
                            <span className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm font-bold shadow-sm">
                              {idx + 1}
                            </span>
                            {segment.instruction && (
                              <div className="flex-1 bg-blue-50 border-l-4 border-blue-500 px-3 py-2 rounded">
                                <div className="flex items-start gap-2">
                                  <Navigation className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                                  <span className="text-sm text-blue-900 font-medium">{segment.instruction}</span>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-3 flex-1">
                            <div className="flex-1 min-w-0 ml-11">
                              <input
                                type="text"
                                value={segment.road_name || ''}
                                onChange={(e) => updateSegmentField(segment.id, 'road_name', e.target.value)}
                                placeholder="Road name (e.g., Hospital Circular Road)"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                              />
                            </div>
                            {segment.has_details && (
                              <span className="bg-green-600 text-white px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap">
                                ✓ Complete
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              onClick={() => toggleSegmentExpansion(segment.id)}
                              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                            >
                              {isExpanded ? '▲ Less' : '▼ More'}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteSegment(segment.id)}
                              className="px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium"
                            >
                              Delete
                            </button>
                            <button
                              type="button"
                              onClick={() => handleMoveUp(idx)}
                              disabled={idx === 0}
                              className="px-2 py-1.5 text-sm bg-gray-300 rounded-lg hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-bold"
                            >
                              ↑
                            </button>
                            <button
                              type="button"
                              onClick={() => handleMoveDown(idx)}
                              disabled={idx === roadSegments.length - 1}
                              className="px-2 py-1.5 text-sm bg-gray-300 rounded-lg hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-bold"
                            >
                              ↓
                            </button>
                            <button
                              type="button"
                              onClick={() => handleMergeWithNext(idx)}
                              disabled={idx === roadSegments.length - 1}
                              className="px-3 py-1.5 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                              title="Merge with next segment"
                            >
                              Merge →
                            </button>
                            <button
                              type="button"
                              onClick={() => handleSplitSegment(idx)}
                              className="px-3 py-1.5 text-sm bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium"
                              title="Split segment in half"
                            >
                              Split
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="p-4 space-y-4 bg-white">
                          {/* Distance */}
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                                Distance (km) <span className="text-red-500">*</span>
                              </label>
                              <div className="flex gap-2">
                                <input
                                  type="number"
                                  step="0.1"
                                  min="0"
                                  value={segment.distance_km || ''}
                                  onChange={(e) => updateSegmentField(segment.id, 'distance_km', e.target.value)}
                                  placeholder="2.5"
                                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                                <span className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg text-sm font-medium text-gray-700">
                                  km
                                </span>
                              </div>
                              {segment.distance_text && (
                                <p className="text-xs text-gray-500 mt-1">Display: {segment.distance_text}</p>
                              )}
                            </div>

                            {/* Road Width */}
                            <div>
                              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                                Road Width (meters) <span className="text-gray-400">(optional)</span>
                              </label>
                              <input
                                type="number"
                                step="0.5"
                                min="0"
                                value={segment.road_width_meters || ''}
                                onChange={(e) => updateSegmentField(segment.id, 'road_width_meters', parseFloat(e.target.value) || undefined)}
                                placeholder="6.5"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              />
                            </div>
                          </div>

                          {/* Road Type */}
                          <div>
                            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                              Road Type <span className="text-red-500">*</span>
                            </label>
                            <select
                              value={segment.road_type || ''}
                              onChange={(e) => updateSegmentField(segment.id, 'road_type', e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                              {roadTypeOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Surface Condition */}
                          <div>
                            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                              Surface Condition <span className="text-red-500">*</span>
                            </label>
                            <select
                              value={segment.surface_condition || ''}
                              onChange={(e) => updateSegmentField(segment.id, 'surface_condition', e.target.value)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                              {conditionOptions.map((condition) => (
                                <option key={condition} value={condition}>
                                  {condition ? condition.charAt(0).toUpperCase() + condition.slice(1) : 'Select condition...'}
                                </option>
                              ))}
                            </select>
                          </div>

                          {/* Additional Notes */}
                          <div>
                            <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                              Additional Notes <span className="text-gray-400">(optional)</span>
                            </label>
                            <textarea
                              rows={2}
                              value={segment.additional_notes || ''}
                              onChange={(e) => updateSegmentField(segment.id, 'additional_notes', e.target.value)}
                              placeholder="Any additional observations..."
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </div>
                        </div>
                      )}

                      {/* Compact Summary when collapsed */}
                      {!isExpanded && (
                        <div className="px-4 py-3 bg-white text-sm text-gray-600 border-t border-gray-100">
                          Distance: {segment.distance_text || 'Not set'}
                          {segment.has_details && segment.road_type && segment.surface_condition && (
                            <span className="ml-2">• {segment.road_type.replace(/_/g, ' ')} in {segment.surface_condition} condition</span>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
                  ) : (
                    <div className="text-gray-500 text-sm py-4 text-center">
                      No road segments yet. Generate a route to create segments automatically.
                    </div>
                  )}
                </div>
              )}

              {/* Add Segment Button (Advanced Mode Only) */}
              {entryMode === 'advanced' && (
                <button
                  type="button"
                  onClick={handleAddSegment}
                  className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-700 hover:border-blue-500 hover:text-blue-600 font-medium transition-colors mb-4"
                >
                  + Add Road Segment
                </button>
              )}

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

          {/* Turn-by-Turn Directions */}
          <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              Turn-by-Turn Directions
            </h3>
            <ol className="space-y-3">
              {routeData.steps.map((step: any, idx: number) => (
                <li key={idx} className="flex gap-3">
                  <span className="flex-shrink-0 w-7 h-7 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {idx + 1}
                  </span>
                  <div className="flex-1">
                    <div className="text-gray-900">{cleanInstruction(step.instructions)}</div>
                    <div className="text-sm text-gray-500 mt-1">
                      {step.distance?.text} • {step.duration?.text}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}

      {/* Instructions */}
      {!routeData && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">How to use:</h4>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li>Search for the property location in the first box</li>
            <li>Click on the suggested location to mark it on the map</li>
            <li>Search for your starting point in the second box</li>
            <li>Click on the suggested starting point</li>
            <li>Click "Generate Route & Directions" to see the route</li>
          </ol>
        </div>
      )}

      {/* Mode Switch Confirmation Modal (NEW) */}
      {showModeConfirmModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md shadow-xl">
            <h3 className="text-lg font-semibold mb-3 text-gray-900">
              Switch Entry Mode?
            </h3>

            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-md">
              <p className="text-sm text-amber-800">
                <strong>⚠️ Warning:</strong> Switching to {pendingModeSwitch === 'simple' ? 'Quick Entry' : 'Detailed Entry'} mode will clear your current road condition data. You'll need to re-enter the information in the new format.
              </p>
            </div>

            <p className="text-gray-700 mb-4 text-sm">
              {pendingModeSwitch === 'simple' && (
                "Quick Entry uses a simplified checkbox-based interface for faster data entry."
              )}
              {pendingModeSwitch === 'advanced' && (
                "Detailed Entry allows you to specify road type, condition, width, and notes for each segment individually."
              )}
            </p>

            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => {
                  setShowModeConfirmModal(false);
                  setPendingModeSwitch(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700 font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => performModeSwitch(pendingModeSwitch!)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
              >
                Switch Mode
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Warning Modal for Missing Segment Details */}
      {showWarningModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transform transition-all">
            {/* Header */}
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="bg-white rounded-full p-2">
                  <svg className="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">Warning: Missing Details</h3>
              </div>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
              <div className="flex items-start gap-3">
                <div className="bg-amber-100 rounded-full p-2 mt-1">
                  <svg className="w-5 h-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-lg font-semibold text-gray-900 mb-2">
                    {warningSegmentCount} segment{warningSegmentCount > 1 ? 's are' : ' is'} missing surface details.
                  </p>
                  <p className="text-sm text-gray-600 mb-3">
                    The AI will describe {warningSegmentCount > 1 ? 'them' : 'it'} without road type/condition information.
                  </p>
                  <div className="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
                    <p className="text-sm text-blue-800 font-medium">
                      For best results, add surface details to all segments before generating.
                    </p>
                  </div>
                </div>
              </div>

              <p className="text-sm font-semibold text-gray-700 mt-4">
                Generate anyway?
              </p>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowWarningModal(false)}
                className="px-5 py-2.5 text-sm font-semibold text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-100 transition-all shadow-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={performAccessTextGeneration}
                className="px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-green-500 to-green-600 rounded-lg hover:from-green-600 hover:to-green-700 transition-all shadow-md"
              >
                OK, Generate
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
