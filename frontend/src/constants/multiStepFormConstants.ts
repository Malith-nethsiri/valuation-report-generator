/**
 * Constants for MultiStepForm component.
 * Extracted from MultiStepForm.tsx to reduce file size and improve reusability.
 */

import {
  FileText,
  User,
  Home,
  MapPin,
  Building,
  Compass,
  ClipboardList,
  Gavel,
  TrendingUp,
  Scale,
  Award,
  Receipt,
  LucideIcon,
} from 'lucide-react';

/**
 * Common deed types used in Sri Lanka property transactions.
 */
export const COMMON_DEED_TYPES = [
  'Transfer Deed',
  'Deed of Gift',
  'Mortgage Deed',
  'Lease Deed',
  'Partition Deed',
  'Exchange Deed',
  'Deed of Sale',
  'Deed of Donation',
  'Release Deed',
  'Reconveyance Deed',
  'Deed of Assignment',
  'Usufructuary Mortgage Deed',
  'Power of Attorney Deed',
  'Certificate of Sale',
] as const;

export type DeedType = typeof COMMON_DEED_TYPES[number];

/**
 * Step configuration interface for the multi-step form.
 */
export interface FormStep {
  id: number;
  title: string;
  subtitle: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
}

/**
 * Form steps configuration for the multi-step valuation report form.
 * Each step has an id, title, subtitle, icon, and color scheme.
 * Steps are ordered to match the report generation sequence.
 */
export const FORM_STEPS: FormStep[] = [
  // Step 1: Applicant & Purpose (moved from position 9 to match report order)
  {
    id: 9,
    title: 'Applicant & Purpose',
    subtitle: 'Applicant details and valuation purpose',
    icon: User,
    color: 'from-emerald-500 to-green-600',
    bgColor: 'from-emerald-50 to-green-100',
  },
  // Step 2: Additional Details (moved from position 10 to match report order)
  {
    id: 10,
    title: 'Additional Details',
    subtitle: 'Submission, inspection, and report info',
    icon: FileText,
    color: 'from-purple-500 to-violet-600',
    bgColor: 'from-purple-50 to-violet-100',
  },
  // Step 3: Property & Plan (was step 1)
  {
    id: 1,
    title: 'Property & Plan',
    subtitle: 'Property and plan information',
    icon: Home,
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'from-blue-50 to-indigo-100',
  },
  // Step 4: Extent & Boundaries (was step 2)
  {
    id: 2,
    title: 'Extent & Boundaries',
    subtitle: 'Land extent, boundaries, and physical features',
    icon: Compass,
    color: 'from-green-500 to-emerald-600',
    bgColor: 'from-green-50 to-emerald-100',
  },
  // Step 5: Property Search (was step 3)
  {
    id: 3,
    title: 'Property Search',
    subtitle: 'Find property on Google Maps',
    icon: MapPin,
    color: 'from-orange-500 to-red-600',
    bgColor: 'from-orange-50 to-red-100',
  },
  // Step 6: Property Details (was step 4)
  {
    id: 4,
    title: 'Property Details',
    subtitle: 'Verify location and administrative info',
    icon: Building,
    color: 'from-cyan-500 to-blue-600',
    bgColor: 'from-cyan-50 to-blue-100',
  },
  // Step 7: Locality Information (was step 5)
  {
    id: 5,
    title: 'Locality Information',
    subtitle: 'Nearby facilities, infrastructure, and area',
    icon: MapPin,
    color: 'from-pink-500 to-rose-600',
    bgColor: 'from-pink-50 to-rose-100',
  },
  // Step 8: Property Description (was step 6)
  {
    id: 6,
    title: 'Property Description',
    subtitle: 'Land, building details and photos',
    icon: ClipboardList,
    color: 'from-amber-500 to-orange-600',
    bgColor: 'from-amber-50 to-orange-100',
  },
  // Step 9: Legal Aspects (was step 7)
  {
    id: 7,
    title: 'Legal Aspects',
    subtitle: 'Ownership and legal status',
    icon: Gavel,
    color: 'from-purple-500 to-violet-600',
    bgColor: 'from-purple-50 to-violet-100',
  },
  // Step 10: Land Values (was step 8)
  {
    id: 8,
    title: 'Land Values',
    subtitle: 'Comparable properties',
    icon: TrendingUp,
    color: 'from-green-500 to-teal-600',
    bgColor: 'from-green-50 to-teal-100',
  },
  // Step 11: Valuation (unchanged)
  {
    id: 11,
    title: 'Valuation',
    subtitle: 'Property valuation breakdown',
    icon: Scale,
    color: 'from-indigo-500 to-blue-600',
    bgColor: 'from-indigo-50 to-blue-100',
  },
  // Step 12: Invoice (unchanged)
  {
    id: 12,
    title: 'Invoice',
    subtitle: 'Professional fees',
    icon: Receipt,
    color: 'from-amber-500 to-orange-600',
    bgColor: 'from-amber-50 to-orange-100',
  },
  // Step 13: Certification (unchanged)
  {
    id: 13,
    title: 'Certification',
    subtitle: 'Valuer certification',
    icon: Award,
    color: 'from-amber-500 to-yellow-600',
    bgColor: 'from-amber-50 to-yellow-100',
  },
];

/**
 * Total number of steps in the form.
 */
export const TOTAL_STEPS = FORM_STEPS.length;

/**
 * Get step index by step ID.
 */
export function getStepIndexById(stepId: number): number {
  return FORM_STEPS.findIndex(step => step.id === stepId);
}

/**
 * Get step configuration by index.
 */
export function getStepByIndex(index: number): FormStep | undefined {
  return FORM_STEPS[index];
}
