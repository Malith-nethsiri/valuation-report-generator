/**
 * Validation Error Transformer Utility
 * Transforms Zod validation errors into user-friendly format for display
 */

import { ZodIssue } from 'zod';
import { getFieldLabel } from './fieldNameMapper';

/**
 * Interface for validation error summary
 * Used by ErrorSummaryPanel to display errors
 */
export interface ValidationErrorSummary {
  fieldName: string;           // Technical field name (e.g., "plan_number")
  fieldLabel: string;          // User-friendly label (e.g., "Plan Number")
  errorMessage: string;        // Clean error message (e.g., "This field is required")
  path: (string | number)[];   // Full path array from Zod (e.g., ["plan_number"] or ["buildings", 0, "room_name"])
}

/**
 * Transforms Zod validation errors into user-friendly error summaries
 *
 * @param zodErrors - Array of Zod validation errors
 * @param formValues - Optional form values for context-aware error messages
 * @returns Array of ValidationErrorSummary objects
 *
 * Features:
 * - Converts technical field names to readable labels
 * - Cleans error messages
 * - Deduplicates errors (one per field)
 * - Handles nested array paths
 *
 * @example
 * const errors = [
 *   { path: ["plan_number"], message: "Required" },
 *   { path: ["plan_date"], message: "Invalid date" }
 * ];
 * transformZodErrors(errors) → [
 *   { fieldName: "plan_number", fieldLabel: "Plan Number", errorMessage: "This field is required", path: ["plan_number"] },
 *   { fieldName: "plan_date", fieldLabel: "Plan Date", errorMessage: "Invalid date", path: ["plan_date"] }
 * ]
 */
export function transformZodErrors(
  zodErrors: ZodIssue[],
  formValues?: any
): ValidationErrorSummary[] {
  // Use Map to automatically deduplicate by path key
  const errorMap = new Map<string, ValidationErrorSummary>();

  for (const error of zodErrors) {
    const path = error.path;
    const fieldName = path.length > 0 ? String(path[0]) : 'unknown';
    const pathKey = path.join('.');

    // Skip if we already have an error for this exact field path
    // This ensures we show only the first error per field
    if (errorMap.has(pathKey)) {
      continue;
    }

    // Get user-friendly field label
    const fieldLabel = getFieldLabel(path);

    // Clean and format error message
    const errorMessage = cleanErrorMessage(error.message);

    errorMap.set(pathKey, {
      fieldName,
      fieldLabel,
      errorMessage,
      path,
    });
  }

  return Array.from(errorMap.values());
}

/**
 * Cleans and standardizes error messages for better user experience
 *
 * @param message - Raw error message from Zod
 * @returns Cleaned, user-friendly error message
 *
 * Transformations:
 * - "Required" → "This field is required"
 * - "Invalid" → "Invalid value"
 * - Ensures first letter is capitalized
 * - Preserves custom error messages
 *
 * @example
 * cleanErrorMessage("Required") → "This field is required"
 * cleanErrorMessage("invalid email") → "Invalid email"
 * cleanErrorMessage("Password must be at least 8 characters") → "Password must be at least 8 characters"
 */
function cleanErrorMessage(message: string): string {
  // Handle common Zod error messages
  let cleaned = message;

  // Transform generic messages to be more user-friendly
  if (cleaned === 'Required' || cleaned === 'required') {
    cleaned = 'This field is required';
  } else if (cleaned === 'Invalid' || cleaned === 'invalid') {
    cleaned = 'Invalid value';
  } else if (cleaned.toLowerCase() === 'invalid type') {
    cleaned = 'Please enter a valid value';
  }

  // Ensure first letter is capitalized
  cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);

  return cleaned;
}

/**
 * Deduplicates validation errors by field path
 * Keeps only the first error for each unique field
 *
 * @param errors - Array of ValidationErrorSummary objects
 * @returns Deduplicated array
 *
 * @example
 * const errors = [
 *   { path: ["plan_number"], ... },
 *   { path: ["plan_number"], ... }, // duplicate
 *   { path: ["plan_date"], ... }
 * ];
 * deduplicateErrors(errors) → [
 *   { path: ["plan_number"], ... },
 *   { path: ["plan_date"], ... }
 * ]
 */
export function deduplicateErrors(
  errors: ValidationErrorSummary[]
): ValidationErrorSummary[] {
  const seen = new Set<string>();

  return errors.filter((error) => {
    const key = error.path.join('.');
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}
