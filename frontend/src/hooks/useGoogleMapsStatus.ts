/**
 * Hook to check Google Maps API availability.
 *
 * Provides:
 * - isLoaded: true when Maps API is ready
 * - isError: true when Maps API failed to load
 * - error: error message if failed
 * - retry: function to retry loading
 *
 * Used by map components to gracefully degrade when Maps unavailable.
 */

import { useState, useEffect, useCallback } from 'react';
import * as Sentry from '@sentry/react';

interface GoogleMapsStatus {
  isLoaded: boolean;
  isLoading: boolean;
  isError: boolean;
  error: string | null;
  retry: () => void;
}

// Global state for maps loading
let mapsLoadPromise: Promise<void> | null = null;
let mapsLoaded = false;
let mapsError: string | null = null;
let retryCount = 0;
const MAX_RETRIES = 3;
const LOAD_TIMEOUT = 15000; // 15 seconds

/**
 * Load Google Maps script with timeout.
 */
async function loadGoogleMaps(): Promise<void> {
  // Already loaded
  if (window.google?.maps) {
    mapsLoaded = true;
    return;
  }

  // Check if API key is configured
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  if (!apiKey) {
    throw new Error('Google Maps API key not configured');
  }

  return new Promise((resolve, reject) => {
    // Set timeout
    const timeoutId = setTimeout(() => {
      reject(new Error('Google Maps API load timeout'));
    }, LOAD_TIMEOUT);

    // Check if script already exists
    const existingScript = document.querySelector(
      'script[src*="maps.googleapis.com"]'
    );

    if (existingScript) {
      // Script exists, wait for it to load
      if (window.google?.maps) {
        clearTimeout(timeoutId);
        resolve();
        return;
      }

      // Wait for existing script
      existingScript.addEventListener('load', () => {
        clearTimeout(timeoutId);
        if (window.google?.maps) {
          resolve();
        } else {
          reject(new Error('Google Maps failed to initialize'));
        }
      });

      existingScript.addEventListener('error', () => {
        clearTimeout(timeoutId);
        reject(new Error('Failed to load Google Maps script'));
      });

      return;
    }

    // Create new script
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places,geometry&callback=__googleMapsCallback`;
    script.async = true;
    script.defer = true;

    // Setup callback
    (window as any).__googleMapsCallback = () => {
      clearTimeout(timeoutId);
      delete (window as any).__googleMapsCallback;
      resolve();
    };

    script.onerror = () => {
      clearTimeout(timeoutId);
      delete (window as any).__googleMapsCallback;
      reject(new Error('Failed to load Google Maps script'));
    };

    document.head.appendChild(script);
  });
}

/**
 * Hook to check and manage Google Maps API status.
 */
export function useGoogleMapsStatus(): GoogleMapsStatus {
  const [status, setStatus] = useState<GoogleMapsStatus>({
    isLoaded: mapsLoaded,
    isLoading: !mapsLoaded && !mapsError,
    isError: !!mapsError,
    error: mapsError,
    retry: () => {},
  });

  const attemptLoad = useCallback(async () => {
    if (mapsLoaded) {
      setStatus((s) => ({
        ...s,
        isLoaded: true,
        isLoading: false,
        isError: false,
        error: null,
      }));
      return;
    }

    setStatus((s) => ({
      ...s,
      isLoading: true,
      isError: false,
      error: null,
    }));

    try {
      if (!mapsLoadPromise) {
        mapsLoadPromise = loadGoogleMaps();
      }

      await mapsLoadPromise;
      mapsLoaded = true;
      mapsError = null;

      setStatus((s) => ({
        ...s,
        isLoaded: true,
        isLoading: false,
        isError: false,
        error: null,
      }));
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load Google Maps';
      mapsError = errorMessage;
      mapsLoadPromise = null; // Allow retry

      // Report to Sentry
      Sentry.captureException(err, {
        tags: {
          component: 'GoogleMaps',
          action: 'load',
        },
        extra: {
          retryCount,
          apiKeyConfigured: !!import.meta.env.VITE_GOOGLE_MAPS_API_KEY,
        },
      });

      setStatus((s) => ({
        ...s,
        isLoaded: false,
        isLoading: false,
        isError: true,
        error: errorMessage,
      }));
    }
  }, []);

  const retry = useCallback(() => {
    if (retryCount >= MAX_RETRIES) {
      setStatus((s) => ({
        ...s,
        error: `Maximum retry attempts (${MAX_RETRIES}) exceeded`,
      }));
      return;
    }

    retryCount++;
    mapsLoadPromise = null; // Reset promise to allow retry
    attemptLoad();
  }, [attemptLoad]);

  useEffect(() => {
    attemptLoad();
  }, [attemptLoad]);

  return {
    ...status,
    retry,
  };
}

/**
 * Check if Google Maps is currently available (synchronous check).
 */
export function isGoogleMapsAvailable(): boolean {
  return !!(window.google?.maps);
}

/**
 * Reset Maps loading state (for testing).
 */
export function resetGoogleMapsState(): void {
  mapsLoadPromise = null;
  mapsLoaded = false;
  mapsError = null;
  retryCount = 0;
}

export default useGoogleMapsStatus;
