/**
 * Invoice item and invoice data types.
 */

export interface InvoiceItem {
  description: string;
  total: number;
}

export interface InvoiceData {
  items: InvoiceItem[];
  subtotal: number;
  traveling_charges?: number | null;
  discount?: number | null;
  total: number;
  bank_account_ids: string[];
  manual_bank_details?: string;
  payment_terms?: string;
}
