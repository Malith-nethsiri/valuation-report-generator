import { useState, useEffect } from 'react';
import type { AdministrativeDivisionsData, AdministrativeDivision } from '../types';
import { api } from '../services/api';

/**
 * Hook to fetch all administrative divisions (districts and DS divisions)
 * Returns the full hierarchical data structure
 */
export function useAdministrativeDivisions() {
  const [divisions, setDivisions] = useState<AdministrativeDivisionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDivisions() {
      try {
        setLoading(true);
        const response = await api.get('/api/administrative-divisions');
        setDivisions(response.data.data);
        setError(null);
      } catch (err: any) {
        console.error('Failed to load administrative divisions:', err);
        setError(err.message || 'Failed to load administrative divisions');
      } finally {
        setLoading(false);
      }
    }

    loadDivisions();
  }, []);

  // Get list of districts
  const districts = divisions ? Object.keys(divisions).sort() : [];

  return { divisions, districts, loading, error };
}

/**
 * Hook to fetch DS Divisions for a specific district
 * Automatically refetches when district changes
 */
export function useDSDivisions(district: string | undefined) {
  const [dsDivisions, setDSDivisions] = useState<AdministrativeDivision[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!district) {
      setDSDivisions([]);
      setError(null);
      return;
    }

    async function loadDSDivisions() {
      try {
        setLoading(true);
        const response = await api.get(`/api/administrative-divisions/${encodeURIComponent(district)}`);
        setDSDivisions(response.data.ds_divisions);
        setError(null);
      } catch (err: any) {
        console.error('Failed to load DS divisions:', err);
        setError(err.message || 'Failed to load DS divisions');
        setDSDivisions([]);
      } finally {
        setLoading(false);
      }
    }

    loadDSDivisions();
  }, [district]);

  return { dsDivisions, loading, error };
}

/**
 * Hook to get DS divisions from local data (faster, no API call)
 * Useful when you already have the full divisions data
 */
export function useDSDivisionsLocal(
  divisions: AdministrativeDivisionsData | null,
  district: string | undefined
): AdministrativeDivision[] {
  if (!divisions || !district) {
    return [];
  }

  // Case-insensitive lookup
  const key = Object.keys(divisions).find(k => k.toLowerCase() === district.toLowerCase());
  return key ? divisions[key] : [];
}
