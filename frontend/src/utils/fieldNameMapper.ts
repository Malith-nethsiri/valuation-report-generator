/**
 * Field Name Mapper Utility
 * Converts technical field names to user-friendly labels for error messages
 */

// Comprehensive mapping of all form fields to user-friendly labels
const FIELD_LABELS: Record<string, string> = {
  // Step 1: Property & Plan
  property_identification_type: "Property Identification Type",
  property_lot_description: "Lot Description",  // DEPRECATED
  lot_number: "Lot Number",
  plan_number: "Plan Number",
  plan_date: "Plan Date",
  licensed_surveyor_name: "Licensed Surveyor Name",
  deed_type: "Deed Type",
  deed_number: "Deed Number",
  deed_date: "Deed Date",
  notary_name: "Notary Name",
  notary_location: "Notary District",
  certificate_number: "Certificate Number",
  certificate_date: "Certificate Date",
  certificate_notary_name: "Certificate Notary Name",
  certificate_notary_district: "Certificate Notary District",

  // Step 2: Extent & Boundaries
  land_extent_acres: "Acres",
  land_extent_roods: "Roods",
  land_extent_perches: "Perches",
  land_extent_hectares: "Hectares",
  land_extent_square_meters: "Square Meters",
  land_extent_formatted: "Land Extent",

  // Step 3: Property Search
  property_latitude: "Latitude",
  property_longitude: "Longitude",

  // Step 4: Property Details
  property_village: "Village/Town",
  property_district: "District",
  grama_niladari_division: "Grama Niladari Division",
  property_province: "Province",

  // Step 5: Locality Information
  locality_character: "Locality Character",
  road_access: "Road Access",
  infrastructure: "Infrastructure",
  proximity_to_city: "Proximity to City",

  // Step 6: Property Description
  buildings: "Buildings",
  building_type: "Building Type",
  building_photos: "Building Photos",
  floors: "Floors",
  floor_name: "Floor Name",
  floor_area: "Floor Area",
  rooms: "Rooms",
  room_type: "Room Type",
  has_attached_bathroom: "Has Attached Bathroom",
  count: "Room Count",
  property_photos: "Property Photos",

  // Step 7: Legal Aspects
  property_legal_status: "Legal Status",
  encumbrances: "Encumbrances",
  servitudes: "Servitudes",
  restrictions: "Restrictions",

  // Step 8: Land Values
  market_value: "Market Value",
  forced_sale_value: "Forced Sale Value",
  estimated_rental: "Estimated Rental Value",

  // Step 9: Applicant & Purpose
  applicant_title: "Title",
  applicant_full_name: "Full Name",
  applicant_id_type: "ID Type",
  applicant_id_number: "ID Number",
  applicant_address_line1: "Address Line 1",
  applicant_address_line2: "Address Line 2",
  applicant_city: "City",
  applicant_district: "District",
  applicant_province: "Province",
  applicant_country: "Country",
  applicant_postal_code: "Postal Code",
  valuation_type: "Valuation Type",
  valuation_purpose: "Purpose of Valuation",
  property_type_valued: "Property Type",
  has_additional_owner: "Additional Owner",
  additional_owner_names: "Additional Owner Names",

  // Step 10: Additional Details
  submission_organization: "Submission Organization",
  submission_address: "Submission Address",
  inspection_date: "Date of Inspection",
  has_special_note: "Special Note",
  special_note_text: "Special Note Text",
  report_reference: "Reference Number",
  report_date: "Report Date",

  // Step 11: Valuation
  valuation_notes: "Valuation Notes",
  valuation_method: "Valuation Method",

  // Step 12: Certification
  certificate_identity_confirmed: "Identity Confirmation",
  valuer_name: "Valuer Name",
  valuer_signature: "Valuer Signature",
};

/**
 * Converts a field path to a user-friendly label
 * Handles simple fields and nested array structures
 *
 * @param path - Array of strings/numbers representing the field path
 * @returns User-friendly field label
 *
 * @example
 * getFieldLabel(["plan_number"]) → "Plan Number"
 * getFieldLabel(["buildings", 0, "floors", 1, "room_type"]) → "Building 1, Floor 2: Room Type"
 */
export function getFieldLabel(path: (string | number)[]): string {
  if (path.length === 0) return "Unknown Field";

  // Handle simple field (e.g., ["plan_number"])
  if (path.length === 1) {
    const fieldName = String(path[0]);
    return FIELD_LABELS[fieldName] || humanizeFieldName(fieldName);
  }

  // Handle nested arrays (e.g., ["buildings", "0", "floors", "1", "room_name"])
  return getNestedArrayLabel(path);
}

/**
 * Handles nested array field paths and converts them to readable labels
 * Supports buildings → floors → rooms structure
 *
 * @param path - Field path array with nested indices
 * @returns Formatted label with context
 *
 * @example
 * ["buildings", 0, "building_type"] → "Building 1: Building Type"
 * ["buildings", 0, "floors", 1, "rooms", 2, "room_type"] → "Building 1, Floor 2, Room 3: Room Type"
 */
function getNestedArrayLabel(path: (string | number)[]): string {
  const parts: string[] = [];
  let i = 0;

  while (i < path.length) {
    const current = String(path[i]);
    const next = i + 1 < path.length ? path[i + 1] : null;

    // Handle array indicators with indices
    if (current === 'buildings' && typeof next === 'number') {
      parts.push(`Building ${next + 1}`);
      i += 2; // Skip both the array name and index
    } else if (current === 'floors' && typeof next === 'number') {
      parts.push(`Floor ${next + 1}`);
      i += 2;
    } else if (current === 'rooms' && typeof next === 'number') {
      parts.push(`Room ${next + 1}`);
      i += 2;
    } else if (typeof current === 'string' && current !== 'buildings' && current !== 'floors' && current !== 'rooms') {
      // Regular field name - this should be the last part
      const fieldLabel = FIELD_LABELS[current] || humanizeFieldName(current);

      // If we have context parts, join them with the field label
      if (parts.length > 0) {
        return `${parts.join(', ')}: ${fieldLabel}`;
      }

      return fieldLabel;
    } else {
      // Skip standalone indices or unexpected values
      i++;
    }
  }

  // If we only collected context without a field name
  return parts.length > 0 ? parts.join(', ') : "Unknown Field";
}

/**
 * Converts snake_case field names to Title Case
 * Used as fallback when field is not in FIELD_LABELS mapping
 *
 * @param fieldName - Snake case field name
 * @returns Title Case label
 *
 * @example
 * humanizeFieldName("plan_number") → "Plan Number"
 * humanizeFieldName("property_address") → "Property Address"
 */
function humanizeFieldName(fieldName: string): string {
  return fieldName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
