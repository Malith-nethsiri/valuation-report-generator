/**
 * Text formatting utilities for cleaning external data sources
 * Handles Google Places API, OCR, and user input
 * Mode: MODERATE - Fixes all-caps, all-lowercase, and random capitals
 */

// Acronyms to preserve in uppercase
const PRESERVED_ACRONYMS = [
  'LLC', 'PO', 'NE', 'SW', 'NW', 'SE',
  'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
  'RD', 'ST', 'AVE', 'DR', 'LTD', 'PVT', 'CO', 'INC', 'PLC'
];

// Lowercase words (articles, prepositions) - except at start
const LOWERCASE_WORDS = ['of', 'and', 'the', 'in', 'at', 'by', 'via', 'to', 'from'];

export function toTitleCase(text: string | null | undefined): string {
  if (!text) return '';

  const cleaned = text.trim();
  const words = cleaned.toLowerCase().split(/\s+/);

  return words.map((word, index) => {
    if (index === 0) return capitalizeFirstLetter(word);
    if (LOWERCASE_WORDS.includes(word)) return word;
    return capitalizeFirstLetter(word);
  }).join(' ');
}

function capitalizeFirstLetter(word: string): string {
  if (!word) return '';
  return word.charAt(0).toUpperCase() + word.slice(1);
}

/**
 * Smart Title Case for OCR text
 * Handles initials (A.D.SILVA), acronyms (LLC), prefixes (DE SILVA),
 * hyphenated names (PERERA-SILVA), and possessives (PEOPLE'S)
 */
export function smartTitleCase(text: string | null | undefined): string {
  if (!text) return '';

  let cleaned = text.trim();
  if (!cleaned) return '';

  // Check if text needs transformation (all caps, all lower, or has random caps)
  const isAllUpper = cleaned === cleaned.toUpperCase() && /[A-Z]/.test(cleaned);
  const isAllLower = cleaned === cleaned.toLowerCase() && /[a-z]/.test(cleaned);
  const hasRandomCaps = /[a-z][A-Z]/.test(cleaned);

  // If already properly cased (mixed case without random caps), return as-is
  if (!isAllUpper && !isAllLower && !hasRandomCaps) {
    return cleaned;
  }

  // Process word by word
  const words = cleaned.split(/\s+/);

  const processedWords = words.map((word, wordIndex) => {
    // Check if word is an acronym to preserve
    const upperWord = word.toUpperCase();
    if (PRESERVED_ACRONYMS.includes(upperWord)) {
      return upperWord;
    }

    // Handle initials pattern (e.g., "A.D.SILVA" or "A.D." or "A.B.C.")
    // Pattern: single letters followed by dots, possibly ending with a name
    const initialsMatch = word.match(/^((?:[A-Za-z]\.)+)(.*)$/);
    if (initialsMatch) {
      const initials = initialsMatch[1].toUpperCase(); // Keep initials uppercase
      const remainder = initialsMatch[2];
      if (remainder) {
        // Process the remainder (e.g., "SILVA" in "A.D.SILVA")
        return initials + processWordPart(remainder);
      }
      return initials;
    }

    // Handle hyphenated names (e.g., "PERERA-SILVA")
    if (word.includes('-')) {
      return word.split('-').map(part => processWordPart(part)).join('-');
    }

    // Handle possessives (e.g., "PEOPLE'S")
    if (word.includes("'")) {
      const parts = word.split("'");
      return parts.map((part, i) => {
        if (i === 0) return processWordPart(part);
        // After apostrophe: 's', 't', etc. stay lowercase
        return part.toLowerCase();
      }).join("'");
    }

    // Check for lowercase words (articles, prepositions) - but not at start
    if (wordIndex > 0 && LOWERCASE_WORDS.includes(word.toLowerCase())) {
      return word.toLowerCase();
    }

    // Standard title case
    return processWordPart(word);
  });

  return processedWords.join(' ');
}

/**
 * Process a single word part (handles basic capitalization)
 */
function processWordPart(word: string): string {
  if (!word) return '';

  // Check if it's an acronym
  const upperWord = word.toUpperCase();
  if (PRESERVED_ACRONYMS.includes(upperWord)) {
    return upperWord;
  }

  // Standard: first letter uppercase, rest lowercase
  return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
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
