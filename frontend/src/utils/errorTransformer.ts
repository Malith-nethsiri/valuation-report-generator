/**
 * Error Transformer Utility
 * Transforms backend validation errors into user-friendly messages
 */

interface ValidationError {
  field: string;
  message: string;
  stepIndex?: number;
  buildingIndex?: number;
  photoIndex?: number;
}

export class ValidationErrorTransformer {
  // Map form fields to step IDs (matches FORM_STEPS id values in multiStepFormConstants.ts)
  private static readonly fieldToStepMap: Record<string, number> = {
    // Step ID 1: Property & Plan
    property_plan_no: 1,
    plan_number: 1,
    plan_date: 1,
    deed_no: 1,
    deed_number: 1,
    deed_date: 1,
    lot_number: 1,
    certificate_number: 1,
    certificate_date: 1,

    // Step ID 2: Extent & Boundaries
    land_extent_acres: 2,
    land_extent_roods: 2,
    land_extent_perches: 2,
    boundaries_north: 2,
    boundaries_south: 2,
    boundaries_east: 2,
    boundaries_west: 2,

    // Step ID 3: Property Search
    property_latitude: 3,
    property_longitude: 3,
    property_location: 3,

    // Step ID 4: Property Details
    property_village: 4,
    property_district: 4,
    grama_niladari_division: 4,
    land_registry_no: 4,

    // Step ID 5: Locality Information
    electricity: 5,
    water_supply: 5,
    drainage: 5,
    special_features: 5,

    // Step ID 6: Property Description
    buildings: 6,
    building_photos: 6,
    property_photos: 6,
    floors: 6,
    rooms: 6,

    // Step ID 7: Legal Aspects
    ownership_type: 7,
    encumbrances: 7,
    legal_issues: 7,

    // Step ID 8: Land Values
    market_value: 8,
    land_value: 8,

    // Step ID 9: Applicant & Purpose
    applicant_full_name: 9,
    applicant_nic: 9,
    owner_name: 9,
    owner_nic: 9,
    owner_contact: 9,
    valuation_purpose: 9,

    // Step ID 10: Additional Details
    report_reference: 10,
    report_date: 10,
    inspection_date: 10,
    remarks: 10,

    // Step ID 11: Valuation
    total_market_value: 11,
    forced_sale_value: 11,
    distress_value: 11,
    building_value: 11,

    // Step ID 13: Certification
    certification_text: 13,
    certificate_identity_confirmed: 13,
  };

  // Step names for user-friendly display (keyed by step ID)
  private static readonly stepNames: Record<number, string> = {
    1: 'Property & Plan',
    2: 'Extent & Boundaries',
    3: 'Property Search',
    4: 'Property Details',
    5: 'Locality Information',
    6: 'Property Description',
    7: 'Legal Aspects',
    8: 'Land Values',
    9: 'Applicant & Purpose',
    10: 'Additional Details',
    11: 'Valuation',
    12: 'Invoice',
    13: 'Certification',
  };

  /**
   * Parse backend error response and extract field errors
   */
  static parseBackendError(error: any): ValidationError[] {
    const errors: ValidationError[] = [];

    // Handle axios error response
    const errorDetail = error?.response?.data?.detail || error?.detail || error?.message;

    if (!errorDetail) {
      return errors;
    }

    // If errorDetail is a string (custom ValueError from backend)
    if (typeof errorDetail === 'string') {
      const parsedError = this.parseCustomError(errorDetail);
      if (parsedError) {
        errors.push(parsedError);
      }
    }
    // If errorDetail is an array (Pydantic validation errors)
    else if (Array.isArray(errorDetail)) {
      errorDetail.forEach((err: any) => {
        const parsedError = this.parsePydanticError(err);
        if (parsedError) {
          errors.push(parsedError);
        }
      });
    }

    return errors;
  }

  /**
   * Parse custom ValueError messages from backend (e.g., building photo validation)
   */
  private static parseCustomError(errorMessage: string): ValidationError | null {
    // Pattern: "Building X has Y photos. Maximum is 5 per building."
    const buildingPhotoMatch = errorMessage.match(/Building (\d+).*has (\d+) photos/i);
    if (buildingPhotoMatch) {
      const buildingNum = parseInt(buildingPhotoMatch[1]);
      const photoCount = parseInt(buildingPhotoMatch[2]);
      const excess = photoCount - 5;

      return {
        field: 'building_photos',
        message: `Building ${buildingNum} has too many photos (${photoCount}). Please remove ${excess} photo${excess > 1 ? 's' : ''}.`,
        stepIndex: 6,
        buildingIndex: buildingNum - 1,
      };
    }

    // Pattern: "Building X, Photo Y: Missing required fields: ..."
    const missingFieldsMatch = errorMessage.match(/Building (\d+), Photo (\d+): Missing required fields: (.+)/i);
    if (missingFieldsMatch) {
      const buildingNum = parseInt(missingFieldsMatch[1]);
      const photoNum = parseInt(missingFieldsMatch[2]);
      const missingFields = missingFieldsMatch[3];

      return {
        field: 'building_photos',
        message: `Building ${buildingNum}, Photo ${photoNum}: Please upload the photo again. ${missingFields.includes('image_data') ? 'Image file is invalid.' : ''}`,
        stepIndex: 6,
        buildingIndex: buildingNum - 1,
        photoIndex: photoNum - 1,
      };
    }

    // Pattern: "Building X, Photo Y: image_data must be a string"
    const imageDataMatch = errorMessage.match(/Building (\d+), Photo (\d+): image_data/i);
    if (imageDataMatch) {
      const buildingNum = parseInt(imageDataMatch[1]);
      const photoNum = parseInt(imageDataMatch[2]);

      return {
        field: 'building_photos',
        message: `Building ${buildingNum}, Photo ${photoNum}: Please upload a valid image file (JPEG, PNG, or WebP).`,
        stepIndex: 6,
        buildingIndex: buildingNum - 1,
        photoIndex: photoNum - 1,
      };
    }

    // Pattern: "Building X, Photo Y: Invalid image data format"
    const invalidFormatMatch = errorMessage.match(/Building (\d+), Photo (\d+): Invalid image/i);
    if (invalidFormatMatch) {
      const buildingNum = parseInt(invalidFormatMatch[1]);
      const photoNum = parseInt(invalidFormatMatch[2]);

      return {
        field: 'building_photos',
        message: `Building ${buildingNum}, Photo ${photoNum}: Invalid image format. Please upload JPEG, PNG, or WebP.`,
        stepIndex: 6,
        buildingIndex: buildingNum - 1,
        photoIndex: photoNum - 1,
      };
    }

    // Generic error - try to extract field if possible
    return {
      field: 'general',
      message: this.makeUserFriendly(errorMessage),
      stepIndex: 0,
    };
  }

  /**
   * Parse Pydantic validation errors
   */
  private static parsePydanticError(error: any): ValidationError | null {
    const field = Array.isArray(error.loc) ? error.loc.join('.') : String(error.loc || 'unknown');
    const message = error.msg || error.message || 'Invalid value';
    const type = error.type || '';

    // Extract base field name for step mapping
    const baseField = field.split('.')[0];
    const stepIndex = this.fieldToStepMap[baseField] || 0;

    // Transform common Pydantic messages
    let userMessage = message;

    if (type.includes('missing')) {
      userMessage = 'This field is required';
    } else if (type.includes('string_type')) {
      userMessage = 'Please enter text';
    } else if (type.includes('int_type') || type.includes('float_type')) {
      userMessage = 'Please enter a valid number';
    } else if (message.includes('ensure this value is greater than')) {
      const fieldName = this.getFieldDisplayName(field);
      userMessage = `${fieldName} must be greater than 0`;
    } else if (message.includes('ensure this value is less than')) {
      const fieldName = this.getFieldDisplayName(field);
      const match = message.match(/less than (\d+)/);
      const maxValue = match ? match[1] : 'the maximum';
      userMessage = `${fieldName} must be less than ${maxValue}`;
    } else if (message.includes('string does not match regex')) {
      userMessage = 'Invalid format';
    } else {
      userMessage = this.makeUserFriendly(message);
    }

    return {
      field,
      message: userMessage,
      stepIndex,
    };
  }

  /**
   * Transform technical error messages into user-friendly ones
   */
  private static makeUserFriendly(message: string): string {
    // Common transformations
    const transformations: Record<string, string> = {
      'field required': 'This field is required',
      'none is not an allowed value': 'This field is required',
      'value is not a valid': 'Invalid value',
      'ensure this value': 'Value',
      'string type expected': 'Please enter text',
      'integer type expected': 'Please enter a number',
      'float type expected': 'Please enter a number',
      'value_error': 'Invalid value',
    };

    let friendly = message;

    for (const [technical, userFriendly] of Object.entries(transformations)) {
      if (friendly.toLowerCase().includes(technical)) {
        friendly = friendly.replace(new RegExp(technical, 'gi'), userFriendly);
      }
    }

    // Capitalize first letter
    friendly = friendly.charAt(0).toUpperCase() + friendly.slice(1);

    // Remove technical prefixes
    friendly = friendly.replace(/^value_error\./gi, '');
    friendly = friendly.replace(/^type_error\./gi, '');

    return friendly;
  }

  /**
   * Get user-friendly field display name
   */
  private static getFieldDisplayName(field: string): string {
    const displayNames: Record<string, string> = {
      land_extent_acres: 'Acres',
      land_extent_roods: 'Roods',
      land_extent_perches: 'Perches',
      market_value: 'Market value',
      forced_sale_value: 'Forced sale value',
      distress_value: 'Distress value',
      land_value: 'Land value',
      length: 'Room length',
      width: 'Room width',
      floor_area: 'Floor area',
    };

    // Get the last part of the field path
    const lastPart = field.split('.').pop() || field;
    return displayNames[lastPart] || lastPart.replace(/_/g, ' ');
  }

  /**
   * Get step name for display
   */
  static getStepName(stepIndex: number): string {
    return this.stepNames[stepIndex] || 'Unknown Step';
  }

  /**
   * Group errors by step
   */
  static groupErrorsByStep(errors: ValidationError[]): Record<number, ValidationError[]> {
    return errors.reduce((acc, error) => {
      const step = error.stepIndex || 0;
      if (!acc[step]) {
        acc[step] = [];
      }
      acc[step].push(error);
      return acc;
    }, {} as Record<number, ValidationError[]>);
  }
}
