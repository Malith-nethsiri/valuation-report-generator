/**
 * Tests for step validation schemas.
 * Tests Zod schema validation for form steps.
 */

import { describe, it, expect } from 'vitest';
import { z } from 'zod';

// Import schemas from the centralized validation file
import {
  baseApplicantPurposeSchema,
  applicantPurposeSchema,
  validateIdFormat,
  validateAdditionalOwner,
  baseAdditionalDetailsSchema,
  buildingSchema,
  floorSchema,
  roomSchema,
} from '../../schemas/validationSchemas';

describe('Property Plan Schema', () => {
  // Define the schema inline for testing (will be imported from extracted file later)
  const propertyPlanSchema = z.object({
    property_identification_type: z.enum(['plan', 'deed', 'plan_and_deed', 'certificate_of_sale'], {
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
  }).superRefine((data, ctx) => {
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
      if (!data.plan_number) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Plan number is required for hybrid mode',
          path: ['plan_number']
        });
      }
      if (!data.deed_number) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Deed number is required for hybrid mode',
          path: ['deed_number']
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

  describe('Plan Mode Validation', () => {
    it('validates deed mode correctly', () => {
      const validDeed = {
        property_identification_type: 'deed' as const,
        deed_number: '12345',
        deed_date: '01-01-2024',
      };

      const result = propertyPlanSchema.safeParse(validDeed);
      expect(result.success).toBe(true);
    });

    it('fails deed mode without deed_number', () => {
      const invalidDeed = {
        property_identification_type: 'deed' as const,
        deed_date: '01-01-2024',
      };

      const result = propertyPlanSchema.safeParse(invalidDeed);
      expect(result.success).toBe(false);
      if (!result.success) {
        const errors = result.error.flatten().fieldErrors;
        expect(errors.deed_number).toBeDefined();
      }
    });

    it('validates plan mode correctly', () => {
      const validPlan = {
        property_identification_type: 'plan' as const,
        plan_number: '1035',
        plan_date: '01-01-2024',
      };

      const result = propertyPlanSchema.safeParse(validPlan);
      expect(result.success).toBe(true);
    });

    it('fails plan mode without plan_number', () => {
      const invalidPlan = {
        property_identification_type: 'plan' as const,
        plan_date: '01-01-2024',
      };

      const result = propertyPlanSchema.safeParse(invalidPlan);
      expect(result.success).toBe(false);
      if (!result.success) {
        const errors = result.error.flatten().fieldErrors;
        expect(errors.plan_number).toBeDefined();
      }
    });

    it('validates certificate mode correctly', () => {
      const validCertificate = {
        property_identification_type: 'certificate_of_sale' as const,
        certificate_number: 'CERT123',
        certificate_date: '01-01-2024',
      };

      const result = propertyPlanSchema.safeParse(validCertificate);
      expect(result.success).toBe(true);
    });

    it('validates hybrid mode (plan_and_deed) correctly', () => {
      const validHybrid = {
        property_identification_type: 'plan_and_deed' as const,
        plan_number: '1035',
        plan_date: '01-01-2024',
        deed_number: '12345',
        deed_date: '01-01-2024',
      };

      const result = propertyPlanSchema.safeParse(validHybrid);
      expect(result.success).toBe(true);
    });

    it('fails hybrid mode without both plan and deed', () => {
      const invalidHybrid = {
        property_identification_type: 'plan_and_deed' as const,
        plan_number: '1035',
        // Missing deed_number
      };

      const result = propertyPlanSchema.safeParse(invalidHybrid);
      expect(result.success).toBe(false);
    });
  });
});

describe('Extent Boundaries Schema', () => {
  const extentBoundariesSchema = z.object({
    land_extent_acres: z.number().min(0, 'Acres cannot be negative').optional(),
    land_extent_roods: z.number().min(0, 'Roods cannot be negative').max(3, 'Roods must be between 0 and 3').optional(),
    land_extent_perches: z.number().min(0, 'Perches cannot be negative').max(39.99, 'Perches must be less than 40').optional(),
  });

  it('validates valid extent data', () => {
    const validExtent = {
      land_extent_acres: 1,
      land_extent_roods: 2,
      land_extent_perches: 30.5,
    };

    const result = extentBoundariesSchema.safeParse(validExtent);
    expect(result.success).toBe(true);
  });

  it('rejects invalid data - negative acres', () => {
    const invalidExtent = {
      land_extent_acres: -1,
    };

    const result = extentBoundariesSchema.safeParse(invalidExtent);
    expect(result.success).toBe(false);
  });

  it('rejects invalid data - roods > 3', () => {
    const invalidExtent = {
      land_extent_roods: 4,
    };

    const result = extentBoundariesSchema.safeParse(invalidExtent);
    expect(result.success).toBe(false);
  });

  it('rejects invalid data - perches >= 40', () => {
    const invalidExtent = {
      land_extent_perches: 40,
    };

    const result = extentBoundariesSchema.safeParse(invalidExtent);
    expect(result.success).toBe(false);
  });

  it('allows empty extent data', () => {
    const emptyExtent = {};

    const result = extentBoundariesSchema.safeParse(emptyExtent);
    expect(result.success).toBe(true);
  });
});

describe('Applicant Purpose Schema', () => {
  describe('Base Schema', () => {
    it('validates complete applicant data', () => {
      const validApplicant = {
        applicant_title: 'Mr.',
        applicant_full_name: 'John Doe',
        applicant_address_line1: '123 Main Street',
        applicant_district: 'Colombo',
        applicant_province: 'Western',
        applicant_country: 'Sri Lanka',
        valuation_type: 'Market Value',
        valuation_purpose: 'Bank Loan',
        property_type_valued: 'Residential',
      };

      const result = baseApplicantPurposeSchema.safeParse(validApplicant);
      expect(result.success).toBe(true);
    });

    it('fails without required fields', () => {
      const invalidApplicant = {
        applicant_title: 'Mr.',
        // Missing applicant_full_name and other required fields
      };

      const result = baseApplicantPurposeSchema.safeParse(invalidApplicant);
      expect(result.success).toBe(false);
    });
  });

  describe('ID Format Validation', () => {
    it('validates NIC format - old format (9 digits + V)', () => {
      const dataWithNIC = {
        applicant_id_type: 'NIC',
        applicant_id_number: '901234567V',
      };

      const result = validateIdFormat(dataWithNIC);
      expect(result).toBe(true);
    });

    it('validates NIC format - new format (12 digits)', () => {
      const dataWithNIC = {
        applicant_id_type: 'NIC',
        applicant_id_number: '199012345678',
      };

      const result = validateIdFormat(dataWithNIC);
      expect(result).toBe(true);
    });

    it('rejects invalid NIC format', () => {
      const invalidNIC = {
        applicant_id_type: 'NIC',
        applicant_id_number: '1234', // Too short
      };

      const result = validateIdFormat(invalidNIC);
      expect(result).toBe(false);
    });

    it('validates passport format', () => {
      const validPassport = {
        applicant_id_type: 'Passport',
        applicant_id_number: 'AB1234567',
      };

      const result = validateIdFormat(validPassport);
      expect(result).toBe(true);
    });

    it('allows missing ID fields (optional)', () => {
      const noID = {};

      const result = validateIdFormat(noID);
      expect(result).toBe(true);
    });
  });

  describe('Additional Owner Validation', () => {
    it('requires names when has_additional_owner is yes', () => {
      const withOwner = {
        has_additional_owner: 'yes',
        additional_owner_names: 'Jane Doe',
      };

      const result = validateAdditionalOwner(withOwner);
      expect(result).toBe(true);
    });

    it('fails when has_additional_owner is yes but names empty', () => {
      const missingNames = {
        has_additional_owner: 'yes',
        additional_owner_names: '',
      };

      const result = validateAdditionalOwner(missingNames);
      expect(result).toBe(false);
    });

    it('passes when has_additional_owner is no', () => {
      const noOwner = {
        has_additional_owner: 'no',
      };

      const result = validateAdditionalOwner(noOwner);
      expect(result).toBe(true);
    });
  });
});

describe('Property Search Schema', () => {
  const propertySearchSchema = z.object({
    property_latitude: z.number().optional(),
    property_longitude: z.number().optional(),
  }).refine(
    (data) => data.property_latitude && data.property_longitude,
    {
      message: "Please select a property location on the map",
      path: ["property_latitude"],
    }
  );

  it('validates coordinates', () => {
    const validLocation = {
      property_latitude: 6.9271,
      property_longitude: 79.8612,
    };

    const result = propertySearchSchema.safeParse(validLocation);
    expect(result.success).toBe(true);
  });

  it('fails without coordinates', () => {
    const noLocation = {};

    const result = propertySearchSchema.safeParse(noLocation);
    expect(result.success).toBe(false);
  });
});

describe('Property Details Schema', () => {
  const propertyDetailsSchema = z.object({
    property_village: z.string().min(2, 'Village/Town is required'),
    property_district: z.string().min(2, 'District is required'),
    grama_niladari_division: z.string().nullish(),
  });

  it('validates property details', () => {
    const validDetails = {
      property_village: 'Colombo',
      property_district: 'Colombo',
      grama_niladari_division: 'Kollupitiya',
    };

    const result = propertyDetailsSchema.safeParse(validDetails);
    expect(result.success).toBe(true);
  });

  it('fails without village', () => {
    const missingVillage = {
      property_district: 'Colombo',
    };

    const result = propertyDetailsSchema.safeParse(missingVillage);
    expect(result.success).toBe(false);
  });
});

describe('Building Schema', () => {
  it('validates building structure', () => {
    const validBuilding = {
      id: 'building_1',
      building_photos: [
        { id: 'photo_1', order: 1 },
      ],
      floors: [
        { floor_name: 'Ground Floor', floor_area: 1000 },
      ],
      rooms: [
        { room_type: 'Bedroom', count: 2 },
      ],
    };

    const result = buildingSchema.safeParse(validBuilding);
    expect(result.success).toBe(true);
  });

  it('allows empty building', () => {
    const emptyBuilding = {
      id: 'building_1',
    };

    const result = buildingSchema.safeParse(emptyBuilding);
    expect(result.success).toBe(true);
  });
});

describe('Floor Schema', () => {
  it('validates floor data', () => {
    const validFloor = {
      floor_name: 'Ground Floor',
      floor_area: 1000,
    };

    const result = floorSchema.safeParse(validFloor);
    expect(result.success).toBe(true);
  });
});

describe('Room Schema', () => {
  it('validates room data', () => {
    const validRoom = {
      room_type: 'Bedroom',
      count: 3,
      has_attached_bathroom: true,
    };

    const result = roomSchema.safeParse(validRoom);
    expect(result.success).toBe(true);
  });

  it('allows optional fields', () => {
    const minimalRoom = {};

    const result = roomSchema.safeParse(minimalRoom);
    expect(result.success).toBe(true);
  });
});

describe('Complete Form Schema Merge', () => {
  const basePropertyPlanSchema = z.object({
    property_identification_type: z.enum(['plan', 'deed', 'plan_and_deed', 'certificate_of_sale']).optional(),
  });

  const baseCertificationSchema = z.object({});

  const completeFormSchema = basePropertyPlanSchema
    .merge(baseApplicantPurposeSchema)
    .merge(baseAdditionalDetailsSchema)
    .merge(baseCertificationSchema);

  it('merges all schemas correctly', () => {
    const completeData = {
      property_identification_type: 'plan' as const,
      applicant_title: 'Mr.',
      applicant_full_name: 'John Doe',
      applicant_address_line1: '123 Main Street',
      applicant_district: 'Colombo',
      applicant_province: 'Western',
      applicant_country: 'Sri Lanka',
      valuation_type: 'Market Value',
      valuation_purpose: 'Bank Loan',
      property_type_valued: 'Residential',
    };

    const result = completeFormSchema.safeParse(completeData);
    expect(result.success).toBe(true);
  });
});
