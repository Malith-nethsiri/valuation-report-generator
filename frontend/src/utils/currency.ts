/**
 * Currency formatting utilities for Sri Lankan Rupees (LKR)
 */

/**
 * Format a number as currency with LKR prefix
 * @param value - The numeric value to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted currency string (e.g., "LKR 1,250,000.00")
 */
export const formatCurrency = (value: number, decimals = 2): string => {
  return `LKR ${value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })}`;
};

/**
 * Format a number with thousand separators and decimal places
 * @param value - The numeric value to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted number string (e.g., "1,250,000.00")
 */
export const formatNumber = (value: number, decimals = 2): string => {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

/**
 * Parse a formatted currency string back to a number
 * Removes all non-numeric characters except decimal point and minus sign
 * @param formatted - The formatted string to parse
 * @returns Parsed number value
 */
export const parseCurrency = (formatted: string): number => {
  return parseFloat(formatted.replace(/[^0-9.-]/g, '')) || 0;
};
