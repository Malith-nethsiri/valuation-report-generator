/**
 * Authentication and user account types.
 */

import type { BankAccount } from './admin';

export interface User {
  id: number;
  email: string;
  honorific?: string;
  full_name: string;
  phone?: string;

  // Professional Credentials
  academic_qualifications?: string;
  membership_level?: string;
  membership_number?: string;
  professional_designation?: string;
  panel_valuer_banks?: string[];

  // Residential Address
  house_number?: string;
  area_development?: string;
  village?: string;
  locality?: string;
  phone_primary?: string;
  phone_secondary?: string;

  // Office Information
  office_department?: string;
  office_region?: string;
  office_street_city?: string;
  office_phone?: string;

  // Letterhead template preference
  preferred_letterhead_template?: string;

  // Bank Account Management
  bank_accounts?: BankAccount[];

  created_at: string;
  updated_at?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRegister {
  email: string;
  password: string;
  honorific?: string;
  full_name: string;
  phone?: string;

  // Professional Credentials
  academic_qualifications?: string;
  membership_level?: string;
  membership_number?: string;
  professional_designation?: string;
  panel_valuer_banks?: string[];

  // Residential Address
  house_number?: string;
  area_development?: string;
  village?: string;
  locality?: string;
  phone_primary?: string;
  phone_secondary?: string;

  // Office Information
  office_department?: string;
  office_region?: string;
  office_street_city?: string;
  office_phone?: string;
}

export interface UserUpdate {
  honorific?: string;
  full_name?: string;
  phone?: string;

  // Professional Credentials
  academic_qualifications?: string;
  membership_level?: string;
  membership_number?: string;
  professional_designation?: string;
  panel_valuer_banks?: string[];

  // Residential Address
  house_number?: string;
  area_development?: string;
  village?: string;
  locality?: string;
  phone_primary?: string;
  phone_secondary?: string;

  // Office Information
  office_department?: string;
  office_region?: string;
  office_street_city?: string;
  office_phone?: string;

  // Letterhead template preference
  preferred_letterhead_template?: string;

  // Bank Account Management
  bank_accounts?: BankAccount[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Deed Information
export interface UserData {
  full_name: string;
  email: string;
  phone?: string;
  address?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  country?: string;
  additional_info?: string;
}

export interface UserDataResponse extends UserData {
  id: number;
  created_at: string;
  updated_at?: string;
}

// Administrative Divisions Types (Sri Lankan specific)
