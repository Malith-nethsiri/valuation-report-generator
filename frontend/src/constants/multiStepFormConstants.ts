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
  /** Short data-category label shown in the step header (e.g. "Paper-Based · Client Documents"). */
  category: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
}

/**
 * Form steps configuration for the multi-step valuation report form.
 * Steps are ordered by workflow phase: Documents (1-5), Inspection (6-9), Valuation (10-13).
 */
export const FORM_STEPS: FormStep[] = [
  // ─── DOCUMENTS PHASE (1-5) ───────────────────────────────────────────────
  {
    id: 9,
    title: 'Applicant & Purpose',
    subtitle: 'Applicant details and valuation purpose',
    category: 'Paper-Based · Client Documents',
    icon: User,
    color: 'from-emerald-500 to-green-600',
    bgColor: 'from-emerald-50 to-green-100',
  },
  {
    id: 10,
    title: 'Additional Details',
    subtitle: 'Submission, inspection, and report info',
    category: 'Paper-Based · Client Documents + Inspection',
    icon: FileText,
    color: 'from-purple-500 to-violet-600',
    bgColor: 'from-purple-50 to-violet-100',
  },
  {
    id: 1,
    title: 'Property & Plan',
    subtitle: 'Property and plan information',
    category: 'Paper-Based · Client Documents',
    icon: Home,
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'from-blue-50 to-indigo-100',
  },
  {
    id: 2,
    title: 'Extent & Boundaries',
    subtitle: 'Land extent, boundaries, and physical features',
    category: 'Paper-Based · Client Documents + Inspection',
    icon: Compass,
    color: 'from-green-500 to-emerald-600',
    bgColor: 'from-green-50 to-emerald-100',
  },
  {
    id: 7,
    title: 'Legal Aspects',
    subtitle: 'Ownership and legal status',
    category: 'Paper-Based · Official Records',
    icon: Gavel,
    color: 'from-purple-500 to-violet-600',
    bgColor: 'from-purple-50 to-violet-100',
  },
  // ─── INSPECTION PHASE (6-9) ──────────────────────────────────────────────
  {
    id: 3,
    title: 'Property Search',
    subtitle: 'Find property on Google Maps',
    category: 'Computed · Google Maps',
    icon: MapPin,
    color: 'from-orange-500 to-red-600',
    bgColor: 'from-orange-50 to-red-100',
  },
  {
    id: 4,
    title: 'Property Details',
    subtitle: 'Verify location and administrative info',
    category: 'Paper-Based · Official Records + Inspection',
    icon: Building,
    color: 'from-cyan-500 to-blue-600',
    bgColor: 'from-cyan-50 to-blue-100',
  },
  {
    id: 5,
    title: 'Locality Information',
    subtitle: 'Nearby facilities, infrastructure, and area',
    category: 'Inspection-Based',
    icon: MapPin,
    color: 'from-pink-500 to-rose-600',
    bgColor: 'from-pink-50 to-rose-100',
  },
  {
    id: 6,
    title: 'Property Description',
    subtitle: 'Land, building details and photos',
    category: 'Inspection-Based',
    icon: ClipboardList,
    color: 'from-amber-500 to-orange-600',
    bgColor: 'from-amber-50 to-orange-100',
  },
  // ─── VALUATION PHASE (10-13) ─────────────────────────────────────────────
  {
    id: 8,
    title: 'Land Values',
    subtitle: 'Comparable properties',
    category: 'Valuation Judgment',
    icon: TrendingUp,
    color: 'from-green-500 to-teal-600',
    bgColor: 'from-green-50 to-teal-100',
  },
  {
    id: 11,
    title: 'Valuation',
    subtitle: 'Property valuation breakdown',
    category: 'Valuation Judgment',
    icon: Scale,
    color: 'from-indigo-500 to-blue-600',
    bgColor: 'from-indigo-50 to-blue-100',
  },
  {
    id: 12,
    title: 'Invoice',
    subtitle: 'Professional fees',
    category: 'Valuation Judgment',
    icon: Receipt,
    color: 'from-amber-500 to-orange-600',
    bgColor: 'from-amber-50 to-orange-100',
  },
  {
    id: 13,
    title: 'Certification',
    subtitle: 'Valuer certification',
    category: 'Computed · Auto-Generated',
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

// ─────────────────────────────────────────────────────────────────────────────
// PHASE NAVIGATION
// The 13 form steps are grouped into 3 workflow phases that match the
// valuer's real-world sessions: Documents → Inspection → Valuation.
// ─────────────────────────────────────────────────────────────────────────────

export interface Phase {
  id: number;
  name: string;
  /** Step IDs (from FormStep.id) that belong to this phase. */
  stepIds: number[];
  icon: LucideIcon;
  /** Tailwind gradient classes for the active tab accent. */
  color: string;
  /** Tailwind gradient classes for the inactive tab background. */
  bgColor: string;
}

export const PHASES: Phase[] = [
  {
    id: 1,
    name: 'Documents',
    stepIds: [9, 10, 1, 2, 7],
    icon: FileText,
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'from-blue-50 to-indigo-100',
  },
  {
    id: 2,
    name: 'Inspection',
    stepIds: [3, 4, 5, 6],
    icon: Compass,
    color: 'from-green-500 to-emerald-600',
    bgColor: 'from-green-50 to-emerald-100',
  },
  {
    id: 3,
    name: 'Valuation',
    stepIds: [8, 11, 12, 13],
    icon: Scale,
    color: 'from-amber-500 to-orange-600',
    bgColor: 'from-amber-50 to-orange-100',
  },
];

/**
 * Return the Phase that contains the given step ID, or undefined.
 */
export function getPhaseForStepId(stepId: number): Phase | undefined {
  return PHASES.find(p => p.stepIds.includes(stepId));
}

/**
 * Return the 1-indexed position of the first step (from activeSteps) that
 * belongs to the given phase. Returns 1 if none found.
 */
export function getFirstStepIndexInPhase(phase: Phase, activeSteps: FormStep[]): number {
  for (let i = 0; i < activeSteps.length; i++) {
    if (phase.stepIds.includes(activeSteps[i].id)) return i + 1;
  }
  return 1;
}
