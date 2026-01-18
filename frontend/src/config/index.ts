/**
 * Centralized Environment Configuration
 *
 * This file validates all required environment variables at startup.
 * If any required variable is missing in production, the app will fail fast
 * with a clear error message.
 */

// Determine if we're in production
const isProduction = import.meta.env.PROD;
const isDevelopment = import.meta.env.DEV;

/**
 * Get required environment variable with validation
 */
function getRequiredEnvVar(name: string, devDefault?: string): string {
  const value = import.meta.env[name];

  if (value) {
    return value;
  }

  // In development, allow fallback
  if (isDevelopment && devDefault !== undefined) {
    console.warn(`[Config] ${name} not set, using development default: ${devDefault}`);
    return devDefault;
  }

  // In production, fail fast with clear error
  if (isProduction) {
    throw new Error(
      `Missing required environment variable: ${name}. ` +
      `Please ensure this is set in your production environment.`
    );
  }

  // Fallback for development
  if (devDefault !== undefined) {
    return devDefault;
  }

  throw new Error(`Missing required environment variable: ${name}`);
}

/**
 * Get optional environment variable
 */
function getOptionalEnvVar(name: string, defaultValue: string = ''): string {
  return import.meta.env[name] || defaultValue;
}

// =============================================================================
// Environment Configuration Exports
// =============================================================================

/**
 * Backend API URL
 * Required in production, defaults to localhost:8000 in development
 */
export const API_URL = getRequiredEnvVar('VITE_API_URL', 'http://localhost:8000');

/**
 * Google Maps API Key
 * Required for map functionality
 */
export const GOOGLE_MAPS_API_KEY = getRequiredEnvVar('VITE_GOOGLE_MAPS_API_KEY', '');

/**
 * Environment flags
 */
export const ENV = {
  isProduction,
  isDevelopment,
} as const;

/**
 * Configuration object for easy access
 */
export const config = {
  apiUrl: API_URL,
  googleMapsApiKey: GOOGLE_MAPS_API_KEY,
  env: ENV,
} as const;

export default config;
