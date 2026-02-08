/**
 * Zod validation schemas for MultiStepForm component.
 * Extracted from MultiStepForm.tsx to reduce file size and improve testability.
 */

import { z } from 'zod';
import {
  baseApplicantPurposeSchema as centralizedBaseApplicantPurposeSchema,
  applicantPurposeSchema as centralizedApplicantPurposeSchema,
} from './validationSchemas';

// ===== Property & Plan Schema =====

/**
 * Property identification type enum values.
 */
export const PROPERTY_IDENTIFICATION_TYPES = ['plan', 'deed', 'plan_and_deed', 'certificate_of_sale'] as const;
export type PropertyIdentificationType = typeof PROPERTY_IDENTIFICATION_TYPES[number];

/**
 * Property plan schema with dynamic validation based on identification type.
 */
export const propertyPlanSchema = z.object({
  property_identification_type: z.enum(PROPERTY_IDENTIFICATION_TYPES, {
    required_error: 'Please select what information you have'
  }),
  // All fields as optional initially
  lot_number: z.string().optional(),
  plan_number: z.string().optional(),
  plan_date: z.string().optional(),
  licensed_surveyor_name: z.string().optional(),
  deed_type: z.string().optional(),
  deed_number: z.string().optional(),
  deed_date: z.string().optional(),
  notary_name: z.string().optional(),
  notary_location: z.string().optional(),
  certificate_number: z.string().optional(),
  certificate_date: z.string().optional(),
  certificate_notary_name: z.string().optional(),
  certificate_notary_district: z.string().optional(),
}).superRefine((data, ctx) => {
  // Dynamic validation based on selection
  if (data.property_identification_type === 'plan') {
    if (!data.plan_number) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Plan number is required',
        path: ['plan_number']
      });
    }
    if (!data.plan_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Plan date is required',
        path: ['plan_date']
      });
    }
  } else if (data.property_identification_type === 'deed') {
    if (!data.deed_number) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Deed number is required',
        path: ['deed_number']
      });
    }
    if (!data.deed_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Deed date is required',
        path: ['deed_date']
      });
    }
  } else if (data.property_identification_type === 'plan_and_deed') {
    // HYBRID MODE: Require BOTH plan and deed fields
    if (!data.plan_number) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Plan number is required for hybrid mode',
        path: ['plan_number']
      });
    }
    if (!data.plan_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Plan date is required for hybrid mode',
        path: ['plan_date']
      });
    }
    if (!data.deed_number) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Deed number is required for hybrid mode',
        path: ['deed_number']
      });
    }
    if (!data.deed_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Deed date is required for hybrid mode',
        path: ['deed_date']
      });
    }
  } else if (data.property_identification_type === 'certificate_of_sale') {
    if (!data.certificate_number) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Certificate number is required',
        path: ['certificate_number']
      });
    }
    if (!data.certificate_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Certificate date is required',
        path: ['certificate_date']
      });
    }
  }
});

// ===== Applicant & Purpose Schemas (re-exported from centralized file) =====

export const baseApplicantPurposeSchema = centralizedBaseApplicantPurposeSchema;
export const applicantPurposeSchema = centralizedApplicantPurposeSchema;

// ===== Additional Details Schema =====

/**
 * Base schema for additional details without refinement (for merging).
 */
export const baseAdditionalDetailsSchema = z.object({
  submission_recipient_position: z.string().optional(),
  submission_organization: z.string().optional(),
  submission_address: z.string().optional(),
  request_type: z.enum(['client_request', 'organization_request'], {
    required_error: 'Please select whether this is a client or organization request'
  }),
  inspection_date: z.string().min(1, 'Please enter the inspection date (DD-MM-YYYY)'),
  has_special_note: z.string().optional(),
  special_note_text: z.string().nullish(),
  report_reference: z.string().min(1, 'Please enter a reference number'),
  report_date: z.string().min(1, 'Please enter the report date'),
});

/**
 * Additional details schema with refinement (for step validation).
 */
export const additionalDetailsSchema = baseAdditionalDetailsSchema.superRefine((data, ctx) => {
  // Validate special note text is required when has_special_note is "yes"
  if (data.has_special_note === 'yes' && !data.special_note_text) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Special note text is required when you select "Yes"',
      path: ['special_note_text']
    });
  }
});

// ===== Extent & Boundaries Schema =====

/**
 * Step 2 - Extent & Boundaries validation.
 */
export const extentBoundariesSchema = z.object({
  land_extent_acres: z.number().min(0, 'Acres cannot be negative').optional(),
  land_extent_roods: z.number().min(0, 'Roods cannot be negative').max(3, 'Roods must be between 0 and 3').optional(),
  land_extent_perches: z.number().min(0, 'Perches cannot be negative').max(39.99, 'Perches must be less than 40').optional(),
});

// ===== Property Search Schema =====

/**
 * Step 3 - Property Search validation (location required).
 */
export const propertySearchSchema = z.object({
  property_latitude: z.number().optional(),
  property_longitude: z.number().optional(),
}).refine(
  (data) => {
    // Coordinates should be provided
    return data.property_latitude && data.property_longitude;
  },
  {
    message: "Please select a property location on the map",
    path: ["property_latitude"],
  }
);

// ===== Property Details Schema =====

/**
 * Step 4 - Property Details validation.
 */
export const propertyDetailsSchema = z.object({
  property_village: z.string().min(2, 'Village/Town is required'),
  property_district: z.string().min(2, 'District is required'),
  grama_niladari_division: z.string().nullish(),
});

// ===== Property Description Schema =====

/**
 * Step 6 - Property Description validation.
 */
export const propertyDescriptionSchema = z.object({
  buildings: z.array(z.object({
    building_type: z.string().min(1, 'Building type is required').max(100, 'Building type name is too long').optional(),
    building_photos: z.array(z.object({
      id: z.string(),
      image_data: z.string().refine(val => val.startsWith('data:image/'), 'Invalid image format'),
      order: z.number().min(0),
    })).max(5, 'Maximum 5 photos per building'),
    floors: z.array(z.object({
      floor_name: z.string().min(1, 'Floor name is required'),
      floor_area: z.number().min(0, 'Floor area must be positive').optional(),
    })),
    rooms: z.array(z.object({
      room_type: z.string().min(1, 'Room type is required'),
      count: z.number().min(1, 'Count must be at least 1'),
      has_attached_bathroom: z.boolean().nullish(),
    })).optional(),
  })).optional(),
  property_photos: z.array(z.any()).max(20, 'Maximum 20 property photos').optional(),
});

// ===== Base Property Plan Schema (for merging) =====

/**
 * Combined schema for the entire form (without refined schema).
 */
export const basePropertyPlanSchema = z.object({
  property_identification_type: z.enum(PROPERTY_IDENTIFICATION_TYPES, {
    required_error: 'Please select what information you have'
  }),
  lot_number: z.string().optional(),
  plan_number: z.string().optional(),
  plan_date: z.string().optional(),
  licensed_surveyor_name: z.string().optional(),
  deed_type: z.string().optional(),
  deed_number: z.string().optional(),
  deed_date: z.string().optional(),
  notary_name: z.string().optional(),
  notary_location: z.string().optional(),
  certificate_number: z.string().optional(),
  certificate_date: z.string().optional(),
  certificate_notary_name: z.string().optional(),
  certificate_notary_district: z.string().optional(),
});

// ===== Certification Schema =====

/**
 * Certification schema (for final submission validation).
 * Note: certificate_identity_confirmed validation removed - Certificate of Identity is now optional.
 */
export const baseCertificationSchema = z.object({});

// ===== Complete Form Schema =====

/**
 * Complete form schema merging all base schemas.
 */
export const completeFormSchema = basePropertyPlanSchema
  .merge(baseApplicantPurposeSchema)
  .merge(baseAdditionalDetailsSchema)
  .merge(baseCertificationSchema);

/**
 * Property-only schema for embedded multi-property mode (excludes applicant & additional details).
 */
export const propertyOnlySchema = basePropertyPlanSchema
  .merge(baseCertificationSchema);

// ===== Type Exports =====

export type PropertyPlanFormData = z.infer<typeof propertyPlanSchema>;
export type AdditionalDetailsFormData = z.infer<typeof additionalDetailsSchema>;
export type ExtentBoundariesFormData = z.infer<typeof extentBoundariesSchema>;
export type PropertySearchFormData = z.infer<typeof propertySearchSchema>;
export type PropertyDetailsFormData = z.infer<typeof propertyDetailsSchema>;
export type PropertyDescriptionFormData = z.infer<typeof propertyDescriptionSchema>;
export type CompleteFormData = z.infer<typeof completeFormSchema>;
