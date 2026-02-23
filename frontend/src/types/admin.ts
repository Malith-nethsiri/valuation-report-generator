/**
 * Bank account, template, and admin types.
 */

export interface BankAccount {
  id: string;
  bank_name: string;
  account_number: string;
  branch_name: string;
}

export interface BankAccountCreate {
  bank_name: string;
  account_number: string;
  branch_name: string;
}

export interface BankAccountUpdate {
  bank_name?: string;
  account_number?: string;
  branch_name?: string;
}

// Authentication Types
export interface TemplateMetadata {
  template_id: string;
  name: string;
  description: string;
  category: string;
}

export interface TemplateListResponse {
  templates: TemplateMetadata[];
}

// ===== MULTI-PROPERTY FORM TYPES =====

// Invoice types for multi-property forms
