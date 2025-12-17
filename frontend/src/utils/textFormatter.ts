/**
 * Text formatting utilities for cleaning external data sources
 * Handles Google Places API, OCR, and user input
 * Mode: MODERATE - Fixes all-caps, all-lowercase, and random capitals
 */

export function toTitleCase(text: string | null | undefined): string {
  if (!text) return '';

  const cleaned = text.trim();
  const lowercaseWords = ['of', 'and', 'the', 'in', 'at', 'by', 'via', 'to', 'from'];

  const words = cleaned.toLowerCase().split(/\s+/);

  return words.map((word, index) => {
    if (index === 0) return capitalizeFirstLetter(word);
    if (lowercaseWords.includes(word)) return word;
    return capitalizeFirstLetter(word);
  }).join(' ');
}

function capitalizeFirstLetter(word: string): string {
  if (!word) return '';
  return word.charAt(0).toUpperCase() + word.slice(1);
}

export function formatPlaceName(name: string | null | undefined): string {
  if (!name) return '';

  let formatted = name.trim();

  // MODERATE MODE: Fix obvious issues
  const isAllUpper = formatted === formatted.toUpperCase();
  const isAllLower = formatted === formatted.toLowerCase();
  const hasRandomCaps = /[a-z][A-Z]/.test(formatted); // e.g., "ColOMbo"

  if (isAllUpper || isAllLower || hasRandomCaps) {
    formatted = toTitleCase(formatted);
  }

  // Preserve numbers in place names (e.g., "Colombo 7")
  formatted = formatted.replace(/\b([A-Z][a-z]+)\s+(\d+)\b/g, '$1 $2');

  return formatted;
}

export function formatAddress(address: string | null | undefined): string {
  if (!address) return '';

  let formatted = address.trim().replace(/\s+/g, ' ');

  const parts = formatted.split(',').map(part => {
    return formatPlaceName(part.trim());
  });

  return parts.join(', ');
}

export function cleanOCRText(text: string | null | undefined): string {
  if (!text) return '';

  // Remove zero-width spaces and invisible characters
  let cleaned = text.replace(/[\u200b-\u200f\ufeff]/g, '');

  // Normalize whitespace
  cleaned = cleaned.replace(/\s+/g, ' ');

  return cleaned.trim();
}

export function formatFacilityName(name: string | null | undefined): string {
  if (!name) return '';

  let formatted = formatPlaceName(name);

  // Handle possessives (e.g., "People's Bank")
  formatted = formatted.replace(/\b(\w+)'S\b/gi, (match, word) => {
    return capitalizeFirstLetter(word.toLowerCase()) + "'s";
  });

  return formatted;
}

export function formatBoundaryDescription(description: string | null | undefined): string {
  if (!description) return '';
  return cleanOCRText(description);
}

export interface Facility {
  name: string;
  address?: string;
  [key: string]: any;
}

export function formatFacilities(facilities: Facility[]): Facility[] {
  return facilities.map(facility => ({
    ...facility,
    name: formatFacilityName(facility.name),
    address: facility.address ? formatAddress(facility.address) : undefined
  }));
}
