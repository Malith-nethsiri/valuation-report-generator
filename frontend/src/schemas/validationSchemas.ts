/**
 * Shared validation schemas for form components.
 * Consolidates common validation patterns across MultiStepForm,
 * MultiPropertyRedesignedStepForm, and ApplicantAndPurposeStep.
 */

import { z } from 'zod';
import { validateSriLankanNIC, validatePassport } from '../utils/validators';

// ===== BASE SCHEMAS (without refinements, for merging) =====

/**
 * Base applicant and purpose schema without ID validation refinements.
 * Use this for merging with other schemas.
 */
export const baseApplicantPurposeSchema = z.object({
  applicant_title: z.string().min(1, 'Please select a title'),
  applicant_full_name: z.string().min(2, 'Please enter the applicant full name'),
  applicant_id_type: z.string().optional(),
  applicant_id_number: z.string().optional(),
  applicant_address_line1: z.string().min(5, 'Please enter address line 1'),
  applicant_address_line2: z.string().optional(),
  applicant_district: z.string().min(2, 'Please enter the district'),
  applicant_province: z.string().min(2, 'Please enter the province'),
  applicant_country: z.string().min(2, 'Please enter the country').default('Sri Lanka'),
  applicant_contact_number: z.string().nullable().optional(),
  valuation_type: z.string().min(1, 'Please enter the valuation type'),
  valuation_purpose: z.string().min(1, 'Purpose of valuation is required'),
  property_type_valued: z.string().min(1, 'Please enter the property type'),
  has_additional_owner: z.string().optional(),
  additional_owner_names: z.string().nullable().optional(),
});

/**
 * Base additional details schema for submission info.
 */
export const baseAdditionalDetailsSchema = z.object({
  request_type: z.enum(['client_request', 'organization_request']).optional(),
  submission_recipient_position: z.string().optional(),
  submission_organization: z.string().optional(),
  submission_address: z.string().optional(),
  inspection_date: z.string().optional(),
  has_special_note: z.string().optional(),
  special_note_text: z.string().optional(),
  report_reference: z.string().optional(),
  report_date: z.string().optional(),
});

// ===== REFINEMENT FUNCTIONS =====

/**
 * Validate ID number format based on ID type.
 * Returns true if valid, false otherwise.
 */
export function validateIdFormat(data: { applicant_id_type?: string; applicant_id_number?: string }): boolean {
  // Optional fields - only validate if user provides data
  if (!data.applicant_id_type || !data.applicant_id_number) {
    return true;
  }

  const { applicant_id_type: idType, applicant_id_number: idNumber } = data;

  if (idType === 'NIC') {
    return validateSriLankanNIC(idNumber).isValid;
  } else if (idType === 'Passport') {
    return validatePassport(idNumber).isValid;
  } else if (idType === 'Other') {
    return idNumber.length >= 3;
  }

  return true;
}

/**
 * Generate dynamic error message for ID validation failures.
 */
export function getIdValidationError(data: { applicant_id_type?: string; applicant_id_number?: string }): { message: string; path: string[] } {
  const { applicant_id_type: idType, applicant_id_number: idNumber } = data;

  if (idType === 'NIC') {
    const result = validateSriLankanNIC(idNumber || '');
    return {
      message: result.error || 'Invalid NIC format. Use old format (9 digits + V/X) or new format (12 digits)',
      path: ['applicant_id_number'],
    };
  } else if (idType === 'Passport') {
    const result = validatePassport(idNumber || '');
    return {
      message: result.error || 'Passport must be 6-12 alphanumeric characters',
      path: ['applicant_id_number'],
    };
  } else if (idType === 'Other') {
    return {
      message: 'ID number must be at least 3 characters long',
      path: ['applicant_id_number'],
    };
  }

  return {
    message: 'Invalid ID number',
    path: ['applicant_id_number'],
  };
}

/**
 * Validate additional owner names if has_additional_owner is "yes".
 */
export function validateAdditionalOwner(data: { has_additional_owner?: string; additional_owner_names?: string | null }): boolean {
  if (data.has_additional_owner === 'yes') {
    return !!(data.additional_owner_names && data.additional_owner_names.trim().length > 0);
  }
  return true;
}

// ===== COMPLETE SCHEMAS WITH REFINEMENTS =====

/**
 * Complete applicant and purpose schema with ID and additional owner validation.
 */
export const applicantPurposeSchema = baseApplicantPurposeSchema
  .refine(validateIdFormat, getIdValidationError)
  .refine(validateAdditionalOwner, {
    message: 'Please enter the additional owner names',
    path: ['additional_owner_names'],
  });

/**
 * Valuation purpose schema with whitespace and length validation.
 */
export const valuationPurposeSchema = z
  .string()
  .min(1, 'Purpose of valuation is required')
  .refine((val) => val.trim().length > 0, {
    message: 'Purpose cannot be only whitespace'
  })
  .refine((val) => val.length <= 200, {
    message: 'Purpose must be 200 characters or less'
  });

/**
 * Step 2 schema for multi-property flow (additional details).
 */
export const step2AdditionalDetailsSchema = baseAdditionalDetailsSchema.extend({
  inspection_date: z.string().min(1, 'Please enter the inspection date (DD-MM-YYYY)'),
});

// ===== BUILDING SCHEMAS =====

/**
 * Building photo schema.
 */
export const buildingPhotoSchema = z.object({
  id: z.string(),
  image_data: z.string().optional(),
  order: z.number().optional(),
});

/**
 * Floor schema for building details.
 */
export const floorSchema = z.object({
  floor_name: z.string().optional(),
  floor_area: z.number().optional(),
});

/**
 * Room schema for building details.
 */
export const roomSchema = z.object({
  room_type: z.string().optional(),
  count: z.number().optional(),
});

/**
 * Building schema for property description.
 */
export const buildingSchema = z.object({
  id: z.string(),
  building_photos: z.array(buildingPhotoSchema).optional(),
  floors: z.array(floorSchema).optional(),
  rooms: z.array(roomSchema).optional(),
});

/**
 * Property description schema with buildings array.
 */
export const propertyDescriptionSchema = z.object({
  buildings: z.array(buildingSchema).optional(),
});

// ===== EMPTY SCHEMA =====

/**
 * Empty schema for steps without validation requirements.
 */
export const emptySchema = z.object({});
