/**
 * Client-side input validators for real-time validation
 * Provides comprehensive validation for various field types
 */

import { useState, useEffect } from 'react';

// ===== EMAIL VALIDATION =====

export const validateEmail = (email: string): { isValid: boolean; error?: string } => {
  if (!email) {
    return { isValid: false, error: 'Email is required' };
  }

  // RFC 5322 simplified email regex
  const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Invalid email format' };
  }

  if (email.length > 254) {
    return { isValid: false, error: 'Email is too long (max 254 characters)' };
  }

  return { isValid: true };
};

// ===== SRI LANKAN NIC VALIDATION =====

export const validateSriLankanNIC = (nic: string): { isValid: boolean; error?: string } => {
  if (!nic) {
    return { isValid: true }; // Optional field
  }

  nic = nic.trim().toUpperCase();

  // Old format: 9 digits + V or X (e.g., 912345678V, 801234567X)
  const oldNICRegex = /^[0-9]{9}[VvXx]$/;

  // New format: 12 digits (e.g., 199212345678)
  const newNICRegex = /^[0-9]{12}$/;

  if (!oldNICRegex.test(nic) && !newNICRegex.test(nic)) {
    return {
      isValid: false,
      error: 'Invalid NIC format. Use old format (9 digits + V/X) or new format (12 digits)',
    };
  }

  // Validate old format year digits (first 2 digits should be <= 99)
  if (oldNICRegex.test(nic)) {
    const year = parseInt(nic.substring(0, 2));
    if (year < 0 || year > 99) {
      return { isValid: false, error: 'Invalid year in NIC' };
    }

    // Validate day of year (next 3 digits)
    let dayOfYear = parseInt(nic.substring(2, 5));
    // For females, 500 is added to the day
    if (dayOfYear > 500) {
      dayOfYear -= 500;
    }
    if (dayOfYear < 1 || dayOfYear > 366) {
      return { isValid: false, error: 'Invalid day of year in NIC' };
    }
  }

  // Validate new format year digits (first 4 digits should be 1900-2099)
  if (newNICRegex.test(nic)) {
    const year = parseInt(nic.substring(0, 4));
    if (year < 1900 || year > 2099) {
      return { isValid: false, error: 'Invalid year in NIC' };
    }

    // Validate day of year (next 3 digits)
    let dayOfYear = parseInt(nic.substring(4, 7));
    // For females, 500 is added to the day
    if (dayOfYear > 500) {
      dayOfYear -= 500;
    }
    if (dayOfYear < 1 || dayOfYear > 366) {
      return { isValid: false, error: 'Invalid day of year in NIC' };
    }
  }

  return { isValid: true };
};

// ===== PASSPORT VALIDATION =====

export const validatePassport = (passport: string): { isValid: boolean; error?: string } => {
  if (!passport) {
    return { isValid: true }; // Optional field
  }

  passport = passport.trim();

  // Length check: International passports are typically 6-12 characters
  if (passport.length < 6 || passport.length > 12) {
    return {
      isValid: false,
      error: 'Passport number must be 6-12 characters',
    };
  }

  // FLEXIBLE: Accept alphanumeric characters only (no strict format)
  // International passports vary widely:
  // - US: 9 alphanumeric (e.g., 123456789)
  // - UK: 9 alphanumeric (e.g., 123456789)
  // - India: 1 letter + 7 digits (e.g., A1234567)
  // - Sri Lanka: N + 7 digits (e.g., N1234567)
  // - Canada: 2 letters + 6 digits (e.g., AB123456)
  const passportRegex = /^[A-Z0-9]{6,12}$/;

  if (!passportRegex.test(passport.toUpperCase())) {
    return {
      isValid: false,
      error: 'Passport must contain only letters and numbers',
    };
  }

  return { isValid: true };
};

// ===== PHONE NUMBER VALIDATION (Sri Lankan) =====

export const validateSriLankanPhone = (phone: string): { isValid: boolean; error?: string } => {
  if (!phone) {
    return { isValid: true }; // Optional field
  }

  // Remove spaces, hyphens, parentheses
  const cleaned = phone.replace(/[\s\-\(\)]/g, '');

  // Sri Lankan mobile: 10 digits starting with 07 (e.g., 0712345678)
  // Landline: 10 digits starting with 0 (e.g., 0112345678)
  // International: +94 followed by 9 digits (e.g., +94712345678)
  const localRegex = /^0[1-9][0-9]{8}$/;
  const internationalRegex = /^\+94[1-9][0-9]{8}$/;

  if (!localRegex.test(cleaned) && !internationalRegex.test(cleaned)) {
    return {
      isValid: false,
      error: 'Invalid phone format. Use: 0712345678 or +94712345678',
    };
  }

  return { isValid: true };
};

// ===== PLAN NUMBER VALIDATION =====

export const validatePlanNumber = (planNumber: string): { isValid: boolean; error?: string } => {
  if (!planNumber) {
    return { isValid: false, error: 'Plan number is required' };
  }

  planNumber = planNumber.trim();

  // Allow alphanumeric with common separators: / - _ .
  // Example valid formats: PS/12345, 2023-001, PLAN_123, SP.456
  const planRegex = /^[A-Za-z0-9\/\-_.]{2,50}$/;

  if (!planRegex.test(planNumber)) {
    return {
      isValid: false,
      error: 'Invalid plan number. Use only letters, numbers, and separators (/ - _ .)',
    };
  }

  return { isValid: true };
};

// ===== COORDINATES VALIDATION =====

export const validateLatitude = (lat: number | string): { isValid: boolean; error?: string } => {
  if (lat === '' || lat === null || lat === undefined) {
    return { isValid: true }; // Optional field
  }

  const latitude = typeof lat === 'string' ? parseFloat(lat) : lat;

  if (isNaN(latitude)) {
    return { isValid: false, error: 'Latitude must be a number' };
  }

  if (latitude < -90 || latitude > 90) {
    return { isValid: false, error: 'Latitude must be between -90 and 90 degrees' };
  }

  return { isValid: true };
};

export const validateLongitude = (lng: number | string): { isValid: boolean; error?: string } => {
  if (lng === '' || lng === null || lng === undefined) {
    return { isValid: true }; // Optional field
  }

  const longitude = typeof lng === 'string' ? parseFloat(lng) : lng;

  if (isNaN(longitude)) {
    return { isValid: false, error: 'Longitude must be a number' };
  }

  if (longitude < -180 || longitude > 180) {
    return { isValid: false, error: 'Longitude must be between -180 and 180 degrees' };
  }

  return { isValid: true };
};

// ===== DATE VALIDATION (DD-MM-YYYY) =====

export const validateDate = (dateStr: string): { isValid: boolean; error?: string } => {
  if (!dateStr) {
    return { isValid: true }; // Optional field
  }

  // DD-MM-YYYY format
  const dateRegex = /^(\d{2})-(\d{2})-(\d{4})$/;
  const match = dateStr.match(dateRegex);

  if (!match) {
    return { isValid: false, error: 'Invalid date format. Use DD-MM-YYYY (e.g., 25-12-2023)' };
  }

  const day = parseInt(match[1], 10);
  const month = parseInt(match[2], 10);
  const year = parseInt(match[3], 10);

  // Check valid ranges
  if (month < 1 || month > 12) {
    return { isValid: false, error: 'Invalid month (must be 1-12)' };
  }

  if (day < 1 || day > 31) {
    return { isValid: false, error: 'Invalid day (must be 1-31)' };
  }

  if (year < 1900 || year > 2100) {
    return { isValid: false, error: 'Invalid year (must be 1900-2100)' };
  }

  // Check days in month
  const daysInMonth = new Date(year, month, 0).getDate();
  if (day > daysInMonth) {
    return { isValid: false, error: `Invalid day for month ${month} (max ${daysInMonth} days)` };
  }

  return { isValid: true };
};

// ===== FILE VALIDATION =====

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
const ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];

export const validateImageFile = (file: File): { isValid: boolean; error?: string } => {
  if (!file) {
    return { isValid: false, error: 'No file provided' };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return {
      isValid: false,
      error: `File too large (${sizeMB}MB). Maximum size is 10MB`,
    };
  }

  // Check file type
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return {
      isValid: false,
      error: `Invalid file type (${file.type}). Allowed: JPEG, PNG, WebP`,
    };
  }

  return { isValid: true };
};

export const validateDocumentFile = (file: File): { isValid: boolean; error?: string } => {
  if (!file) {
    return { isValid: false, error: 'No file provided' };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return {
      isValid: false,
      error: `File too large (${sizeMB}MB). Maximum size is 10MB`,
    };
  }

  // Check file type
  if (!ALLOWED_DOCUMENT_TYPES.includes(file.type)) {
    return {
      isValid: false,
      error: `Invalid file type (${file.type}). Allowed: PDF, JPEG, PNG`,
    };
  }

  return { isValid: true };
};

// ===== INPUT SANITIZATION =====

export const sanitizeInput = (input: string): string => {
  if (!input) return input;

  // Remove potentially dangerous characters used in injection attacks
  const dangerousChars = ['<', '>', '{', '}', '(', ')', ';', '`', '$'];
  let sanitized = input;

  dangerousChars.forEach((char) => {
    sanitized = sanitized.replace(new RegExp(char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), '');
  });

  return sanitized.trim();
};

export const sanitizeAlphanumeric = (input: string, allowSpaces = true): string => {
  if (!input) return input;

  // Keep only letters, numbers, and optionally spaces
  const regex = allowSpaces ? /[^a-zA-Z0-9\s]/g : /[^a-zA-Z0-9]/g;
  return input.replace(regex, '').trim();
};

export const sanitizeNumeric = (input: string, allowDecimal = false): string => {
  if (!input) return input;

  // Keep only numbers and optionally decimal point
  const regex = allowDecimal ? /[^0-9.]/g : /[^0-9]/g;
  let sanitized = input.replace(regex, '');

  // Ensure only one decimal point
  if (allowDecimal) {
    const parts = sanitized.split('.');
    if (parts.length > 2) {
      sanitized = parts[0] + '.' + parts.slice(1).join('');
    }
  }

  return sanitized;
};

// ===== REACT HOOK FOR REAL-TIME VALIDATION =====

type ValidatorFunction = (value: any) => { isValid: boolean; error?: string };

export const useFieldValidation = (
  value: any,
  validator: ValidatorFunction,
  debounceMs = 500
): { isValid: boolean; error: string | null; isValidating: boolean } => {
  const [isValid, setIsValid] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  useEffect(() => {
    // Don't validate empty values
    if (!value || value === '') {
      setIsValid(true);
      setError(null);
      setIsValidating(false);
      return;
    }

    setIsValidating(true);

    // Debounce validation
    const timeoutId = setTimeout(() => {
      const result = validator(value);
      setIsValid(result.isValid);
      setError(result.error || null);
      setIsValidating(false);
    }, debounceMs);

    return () => clearTimeout(timeoutId);
  }, [value, validator, debounceMs]);

  return { isValid, error, isValidating };
};

// ===== VALIDATION HELPERS =====

export const isValidURL = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

export const isPositiveNumber = (value: number | string): boolean => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return !isNaN(num) && num > 0;
};

export const isNonNegativeNumber = (value: number | string): boolean => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return !isNaN(num) && num >= 0;
};

export const isInRange = (value: number | string, min: number, max: number): boolean => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return !isNaN(num) && num >= min && num <= max;
};
