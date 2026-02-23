/**
 * Property deed, road, administrative division, and metadata types.
 */

export interface DeedInfo {
  deed_type: string;
  deed_number: string;
  deed_date: string;
  notary_name?: string;
  notary_location?: string;
}

// Building-Related Types
export interface AdministrativeDivision {
  name: string;
  gn_count: number;
}

export interface AdministrativeDivisionsData {
  [district: string]: AdministrativeDivision[];
}

export interface AdministrativeDivisionsResponse {
  status: string;
  data: AdministrativeDivisionsData;
  total_districts: number;
  total_ds_divisions: number;
}

export interface DSDivisionsResponse {
  status: string;
  district: string;
  ds_divisions: AdministrativeDivision[];
}

// Common Types
export interface PropertyMetadata {
  source: 'library' | 'new';
  library_property?: any;
  property_index?: number;
}
