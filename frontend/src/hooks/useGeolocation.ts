import { useState, useCallback, useRef, useEffect } from 'react';

type GeoStatus = 'idle' | 'requesting' | 'success' | 'error';

export interface GeolocationResult {
  latitude: number;
  longitude: number;
  accuracy: number; // metres
}

interface UseGeolocationReturn {
  status: GeoStatus;
  error: string | null;
  accuracy: number | null;
  requestLocation: () => void;
}

const GEO_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 10000,    // 10 s — enough for a cold GPS fix on most devices
  maximumAge: 30000, // accept a cached fix ≤ 30 s old for snappy re-requests
};

/**
 * Wraps the browser Geolocation API for field GPS capture.
 *
 * Design notes:
 * - Uses getCurrentPosition (not watchPosition) — no memory leaks, no
 *   duplicate listeners, single intentional request per button press.
 * - Keeps the onSuccess callback in a ref so the returned requestLocation
 *   function is always stable regardless of parent re-renders.
 * - Checks isSecureContext before calling the API (fails silently on HTTP
 *   in production, but gives the user a clear message instead of a crash).
 */
export function useGeolocation(
  onSuccess: (result: GeolocationResult) => void,
): UseGeolocationReturn {
  const [status, setStatus] = useState<GeoStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [accuracy, setAccuracy] = useState<number | null>(null);

  // Keep latest callback without re-creating requestLocation on every render
  const callbackRef = useRef(onSuccess);
  useEffect(() => {
    callbackRef.current = onSuccess;
  });

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setStatus('error');
      setError('GPS is not supported by this browser or device.');
      return;
    }

    // Geolocation API is only available in secure contexts (HTTPS / localhost).
    if (!window.isSecureContext) {
      setStatus('error');
      setError(
        'Location access requires a secure connection (HTTPS). ' +
        'Contact your system administrator.',
      );
      return;
    }

    setStatus('requesting');
    setError(null);
    setAccuracy(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy: acc } = position.coords;
        setStatus('success');
        setAccuracy(acc);
        callbackRef.current({ latitude, longitude, accuracy: acc });
      },
      (err) => {
        setStatus('error');
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setError(
              'Location access was denied. ' +
              'Enable GPS in your browser or device settings and try again.',
            );
            break;
          case err.POSITION_UNAVAILABLE:
            setError(
              'GPS signal unavailable. Move to an open area (away from buildings) and try again.',
            );
            break;
          case err.TIMEOUT:
            setError(
              'Location request timed out. Check your GPS signal strength and try again.',
            );
            break;
          default:
            setError('Unable to retrieve location. Please try again.');
        }
      },
      GEO_OPTIONS,
    );
  }, []); // stable — callback is read via ref

  return { status, error, accuracy, requestLocation };
}