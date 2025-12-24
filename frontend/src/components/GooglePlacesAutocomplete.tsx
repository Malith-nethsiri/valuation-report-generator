import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Loader2, Search } from 'lucide-react';
import { formatAddress, formatPlaceName } from '../utils/textFormatter';

interface PlaceResult {
  address: string;
  latitude: number;
  longitude: number;
  placeId: string;
  formattedAddress: string;
}

interface Props {
  value: string;
  onChange: (value: string) => void;
  onPlaceSelected: (place: PlaceResult) => void;
  placeholder?: string;
  label?: string;
  required?: boolean;
  className?: string;
  disabled?: boolean;
}

export function GooglePlacesAutocomplete({
  value,
  onChange,
  onPlaceSelected,
  placeholder = 'Search for a location...',
  label,
  required = false,
  className = '',
  disabled = false,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const autocompleteService = useRef<google.maps.places.AutocompleteService | null>(null);
  const placesService = useRef<google.maps.places.PlacesService | null>(null);

  useEffect(() => {
    // Check if Google Maps API is loaded
    if (typeof google === 'undefined' || !google.maps || !google.maps.places) {
      setError('Google Maps API not loaded. Please check your API key.');
      setIsLoading(false);
      return;
    }

    try {
      // Initialize services (using the new approach)
      autocompleteService.current = new google.maps.places.AutocompleteService();

      // Create a hidden div for PlacesService
      const div = document.createElement('div');
      placesService.current = new google.maps.places.PlacesService(div);

      setIsLoading(false);
      setError(null);
    } catch (err: any) {
      console.error('Error initializing Google Places:', err);
      setError('Failed to initialize autocomplete');
      setIsLoading(false);
    }
  }, []);

  // Handle input change and fetch suggestions
  const handleInputChange = async (inputValue: string) => {
    onChange(inputValue);

    if (!inputValue || inputValue.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    if (!autocompleteService.current) return;

    try {
      const request = {
        input: inputValue,
        componentRestrictions: { country: 'lk' }, // Sri Lanka only
        types: ['geocode', 'establishment'],
      };

      autocompleteService.current.getPlacePredictions(request, (predictions, status) => {
        if (status === google.maps.places.PlacesServiceStatus.OK && predictions) {
          setSuggestions(predictions);
          setShowSuggestions(true);
        } else {
          setSuggestions([]);
          setShowSuggestions(false);
        }
      });
    } catch (err) {
      console.error('Error fetching predictions:', err);
    }
  };

  // Handle place selection
  const handlePlaceSelect = (placeId: string, description: string) => {
    if (!placesService.current) return;

    const request = {
      placeId: placeId,
      fields: ['geometry', 'formatted_address', 'name', 'place_id'],
    };

    placesService.current.getDetails(request, (place, status) => {
      if (status === google.maps.places.PlacesServiceStatus.OK && place && place.geometry && place.geometry.location) {
        const placeResult: PlaceResult = {
          address: formatPlaceName(place.name || place.formatted_address || ''),
          latitude: place.geometry.location.lat(),
          longitude: place.geometry.location.lng(),
          placeId: place.place_id || '',
          formattedAddress: formatAddress(place.formatted_address || ''),
        };

        onChange(placeResult.formattedAddress);
        onPlaceSelected(placeResult);
        setShowSuggestions(false);
        setSuggestions([]);
        setError(null);
      } else {
        setError('Could not fetch place details');
      }
    });
  };

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}

      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {isLoading ? (
            <Loader2 className="h-5 w-5 text-gray-400 animate-spin" />
          ) : (
            <Search className="h-5 w-5 text-gray-400" />
          )}
        </div>

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => handleInputChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          onFocus={() => value.length >= 3 && suggestions.length > 0 && setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          className={`w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed ${
            error ? 'border-red-300' : ''
          }`}
        />

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
            {suggestions.map((suggestion, index) => (
              <button
                key={suggestion.place_id}
                type="button"
                onClick={() => handlePlaceSelect(suggestion.place_id, suggestion.description)}
                className="w-full text-left px-4 py-2 hover:bg-blue-50 focus:bg-blue-50 focus:outline-none border-b border-gray-100 last:border-b-0"
              >
                <div className="flex items-start gap-2">
                  <MapPin className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-gray-900">
                      {suggestion.structured_formatting.main_text}
                    </div>
                    <div className="text-xs text-gray-500">
                      {suggestion.structured_formatting.secondary_text}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}

      {!isLoading && !error && (
        <p className="mt-1 text-xs text-gray-500">
          Start typing to search for a location in Sri Lanka
        </p>
      )}
    </div>
  );
}
