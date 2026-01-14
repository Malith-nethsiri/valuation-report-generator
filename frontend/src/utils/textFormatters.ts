/**
 * Converts a string to title case (capitalize first letter of each word).
 *
 * @param str - The string to convert
 * @returns The string in title case with leading/trailing whitespace removed
 *
 * @example
 * toTitleCase("visa purpose") // "Visa Purpose"
 * toTitleCase("ESTATE PLANNING") // "Estate Planning"
 * toTitleCase("  bank   loan  ") // "Bank Loan"
 */
export function toTitleCase(str: string): string {
  if (!str) return str;

  // Trim leading/trailing whitespace and collapse multiple spaces
  const cleaned = str.trim().replace(/\s+/g, ' ');

  // Convert to title case
  return cleaned
    .split(' ')
    .map(word => {
      if (word.length === 0) return word;
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(' ');
}
