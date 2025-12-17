/**
 * Land Extent Calculation Utilities for Sri Lankan Property Measurements
 * Handles conversions between Acres-Roods-Perches (A-R-P) and metric units
 */

// Sri Lankan Land Measurement Constants
export const PERCHES_PER_ROOD = 40;
export const ROODS_PER_ACRE = 4;
export const PERCHES_PER_ACRE = PERCHES_PER_ROOD * ROODS_PER_ACRE; // 160

// Metric Conversions
export const SQUARE_METERS_PER_ACRE = 4046.86;
export const HECTARES_PER_ACRE = 0.404686;
export const SQUARE_METERS_PER_PERCH = 25.29;

export interface ExtentData {
  acres: number;
  roods: number;
  perches: number;
  hectares?: number;
  square_meters?: number;
  formatted?: string;
}

export interface NormalizedExtent {
  acres: number;
  roods: number;
  perches: number;
}

/**
 * Normalize land extent by converting excess perches to roods and excess roods to acres
 */
export function normalizeExtent(
  acres: number = 0,
  roods: number = 0,
  perches: number = 0
): NormalizedExtent {
  let a = acres || 0;
  let r = roods || 0;
  let p = perches || 0;

  // Convert excess perches to roods
  if (p >= PERCHES_PER_ROOD) {
    const extraRoods = Math.floor(p / PERCHES_PER_ROOD);
    r += extraRoods;
    p = Math.round((p - extraRoods * PERCHES_PER_ROOD) * 100) / 100;
  }

  // Convert excess roods to acres
  if (r >= ROODS_PER_ACRE) {
    const extraAcres = Math.floor(r / ROODS_PER_ACRE);
    a += extraAcres;
    r = r - extraAcres * ROODS_PER_ACRE;
  }

  return {
    acres: a,
    roods: r,
    perches: Math.round(p * 100) / 100,
  };
}

/**
 * Convert A-R-P to total perches
 */
export function calculateTotalPerches(
  acres: number = 0,
  roods: number = 0,
  perches: number = 0
): number {
  const total =
    (acres || 0) * PERCHES_PER_ACRE +
    (roods || 0) * PERCHES_PER_ROOD +
    (perches || 0);
  return Math.round(total * 100) / 100;
}

/**
 * Convert A-R-P to hectares
 */
export function arpToHectares(
  acres: number = 0,
  roods: number = 0,
  perches: number = 0
): number {
  const totalAcres =
    (acres || 0) +
    (roods || 0) / ROODS_PER_ACRE +
    (perches || 0) / PERCHES_PER_ACRE;
  const hectares = totalAcres * HECTARES_PER_ACRE;
  return Math.round(hectares * 10000) / 10000; // 4 decimal places
}

/**
 * Convert A-R-P to square meters
 */
export function arpToSquareMeters(
  acres: number = 0,
  roods: number = 0,
  perches: number = 0
): number {
  const totalPerches = calculateTotalPerches(acres, roods, perches);
  const squareMeters = totalPerches * SQUARE_METERS_PER_PERCH;
  return Math.round(squareMeters * 100) / 100; // 2 decimal places
}

/**
 * Format extent in standard Sri Lankan legal document format: "00A-0R-13.8P"
 */
export function formatExtentString(
  acres: number = 0,
  roods: number = 0,
  perches: number = 0
): string {
  const normalized = normalizeExtent(acres, roods, perches);

  const a = Math.floor(normalized.acres);
  const r = normalized.roods;
  const p = normalized.perches;

  // Format perches: show decimal only if not a whole number
  const perchesStr =
    p === Math.floor(p) ? `${Math.floor(p)}` : p.toFixed(2).replace(/\.?0+$/, '');

  return `${a.toString().padStart(2, '0')}A-${r}R-${perchesStr}P`;
}

/**
 * Calculate all extent data from A-R-P input
 */
export function calculateExtentData(
  acres: number = 0,
  roods: number = 0,
  perches: number = 0
): {
  land_extent_acres: number;
  land_extent_roods: number;
  land_extent_perches: number;
  land_extent_hectares: number;
  land_extent_square_meters: number;
  land_extent_formatted: string;
} {
  const normalized = normalizeExtent(acres, roods, perches);

  return {
    land_extent_acres: normalized.acres,
    land_extent_roods: normalized.roods,
    land_extent_perches: normalized.perches,
    land_extent_hectares: arpToHectares(
      normalized.acres,
      normalized.roods,
      normalized.perches
    ),
    land_extent_square_meters: arpToSquareMeters(
      normalized.acres,
      normalized.roods,
      normalized.perches
    ),
    land_extent_formatted: formatExtentString(
      normalized.acres,
      normalized.roods,
      normalized.perches
    ),
  };
}

/**
 * Parse a formatted extent string back to A-R-P values
 */
export function parseExtentString(extentStr: string): NormalizedExtent | null {
  try {
    const cleaned = extentStr.trim().toUpperCase();
    const parts = cleaned.split('-');

    if (parts.length !== 3) {
      return null;
    }

    const acres = parseFloat(parts[0].replace('A', ''));
    const roods = parseInt(parts[1].replace('R', ''), 10);
    const perches = parseFloat(parts[2].replace('P', ''));

    if (isNaN(acres) || isNaN(roods) || isNaN(perches)) {
      return null;
    }

    return { acres, roods, perches };
  } catch {
    return null;
  }
}

/**
 * Validate extent values
 */
export function validateExtentValues(
  acres: number = 0,
  roods: number = 0,
  perches: number = 0
): { valid: boolean; error?: string; warning?: string } {
  const a = acres || 0;
  const r = roods || 0;
  const p = perches || 0;

  if (a < 0) {
    return { valid: false, error: 'Acres cannot be negative' };
  }

  if (r < 0) {
    return { valid: false, error: 'Roods cannot be negative' };
  }

  if (p < 0) {
    return { valid: false, error: 'Perches cannot be negative' };
  }

  const total = calculateTotalPerches(a, r, p);
  if (total === 0) {
    return { valid: true, warning: 'Total extent is zero' };
  }

  const normalized = normalizeExtent(a, r, p);
  if (normalized.acres > 1000) {
    return {
      valid: true,
      warning: 'Unusually large extent (>1000 acres). Please verify.',
    };
  }

  if (total < 1) {
    return {
      valid: true,
      warning: 'Very small extent (<1 perch). Please verify.',
    };
  }

  return { valid: true };
}
