import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  User,
  FileText,
  Layers,
  Calculator,
  Receipt,
  Award,
  Home
} from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';
import { Label } from './Label';
import { DatePicker } from './DatePicker';
import { useDraftManager } from '../hooks/useDraftManager';
import { useNavigationBlocker } from '../hooks/useNavigationBlocker';
import NavigationConfirmModal from './NavigationConfirmModal';
import { LoadingOverlay } from './LoadingOverlay';
import PropertyDetailsStep from './PropertyDetailsStep';
import InvoiceDataStep from './InvoiceDataStep';
import PropertyComparisonStep from './PropertyComparisonStep';

// Type definitions for the form data
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
}

export interface PropertyMetadata {
  source: 'library' | 'new';
  library_property?: any; // PropertyResponse type
  property_index?: number;
}

export interface MultiPropertyFormData {
  // Report metadata
  report_type: 'multi_property';
  is_multi_property: true;
  status?: string;

  // Step 1: Applicant Information
  applicant_title?: string;
  applicant_full_name?: string;
  applicant_id_type?: string;
  applicant_id_number?: string;
  applicant_address_line1?: string;
  applicant_address_line2?: string;
  applicant_district?: string;
  applicant_province?: string;
  applicant_country?: string;
  has_additional_owner?: string;
  additional_owner_names?: string;

  // Step 2: Valuation Purpose
  valuation_type?: string;
  valuation_purpose?: string;
  property_type_valued?: string;
  submission_organization?: string;
  submission_address?: string;
  submission_recipient_position?: string;
  inspection_date?: string; // Shared across all properties
  report_reference?: string;
  report_date?: string;
  has_special_note?: string;
  special_note_text?: string;

  // Step 3: Property Source Selection
  property_source?: 'library' | 'new' | 'mix';

  // Step 4: Property Count
  property_count: number; // 2-20

  // Properties (mixed from library and new)
  property_ids?: number[]; // IDs of properties selected from library
  properties?: any[]; // Array of NEW PropertyCreate objects
  property_metadata?: PropertyMetadata[]; // Track which properties are from library vs new

  // Invoice data (Step N+2)
  invoice_data?: InvoiceData;

  // Certification (Step N+3)
  certification_text?: string;
  certification_valuer_name?: string;
  certification_valuer_designation?: string;
  certification_date?: string;
  certificate_identity_confirmed?: boolean;
}

// Props for the MultiPropertyStepForm component
interface MultiPropertyStepFormProps {
  onSubmit: (data: MultiPropertyFormData, submissionType: 'draft' | 'complete') => Promise<void>;
  isSubmitting: boolean;
  user: any;
  isEditMode?: boolean;
  reportId?: number;
  initialData?: any;
}

// Step configuration
const steps = [
  {
    id: 1,
    title: 'Applicant Info',
    subtitle: 'Who is requesting the valuation',
    icon: User,
    color: 'from-blue-500 to-cyan-600',
    bgColor: 'from-blue-50 to-cyan-100',
  },
  {
    id: 2,
    title: 'Valuation Purpose',
    subtitle: 'Purpose and inspection details',
    icon: FileText,
    color: 'from-emerald-500 to-green-600',
    bgColor: 'from-emerald-50 to-green-100',
  },
  {
    id: 3,
    title: 'Property Source',
    subtitle: 'Library or create new',
    icon: Layers,
    color: 'from-violet-500 to-purple-600',
    bgColor: 'from-violet-50 to-purple-100',
  },
  {
    id: 4,
    title: 'Property Count',
    subtitle: 'How many properties',
    icon: Calculator,
    color: 'from-orange-500 to-red-600',
    bgColor: 'from-orange-50 to-red-100',
  },
  // Dynamic property steps will be inserted here
  {
    id: 99, // Placeholder, will be calculated dynamically
    title: 'Review & Compare',
    subtitle: 'Compare and reorder properties',
    icon: CheckCircle2,
    color: 'from-indigo-500 to-blue-600',
    bgColor: 'from-indigo-50 to-blue-100',
  },
  {
    id: 100, // Placeholder
    title: 'Invoice',
    subtitle: 'Professional fees',
    icon: Receipt,
    color: 'from-pink-500 to-rose-600',
    bgColor: 'from-pink-50 to-rose-100',
  },
  {
    id: 101, // Placeholder
    title: 'Certification',
    subtitle: 'Final certification',
    icon: Award,
    color: 'from-amber-500 to-yellow-600',
    bgColor: 'from-amber-50 to-yellow-100',
  },
];

// Validation schemas
const applicantSchema = z.object({
  applicant_full_name: z.string().min(2, 'Full name is required'),
  applicant_id_type: z.string().optional(), // Optional - no checkbox needed
  applicant_id_number: z.string().optional(), // Optional - no checkbox needed
});

const purposeSchema = z.object({
  valuation_type: z.string().optional(),
  valuation_purpose: z.string().optional(),
  inspection_date: z.string().optional(),
});

const propertyCountSchema = z.object({
  property_count: z.number().min(2, 'Minimum 2 properties').max(20, 'Maximum 20 properties'),
});

const MultiPropertyStepForm: React.FC<MultiPropertyStepFormProps> = ({
  onSubmit,
  isSubmitting,
  user,
  isEditMode = false,
  reportId,
  initialData,
}) => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [showNavWarning, setShowNavWarning] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<(() => void) | null>(null);

  // Initialize form with react-hook-form
  const formMethods = useForm<MultiPropertyFormData>({
    // We'll add full resolver once we create all validation schemas
    // resolver: zodResolver(completeFormSchema),
    defaultValues: {
      report_type: 'multi_property',
      is_multi_property: true,
      property_count: 3,
      property_source: 'new',
      applicant_country: 'Sri Lanka',
      property_ids: [],
      properties: [
        // Initialize with 3 empty properties
        {},
        {},
        {},
      ],
      property_metadata: [],
      invoice_data: {
        items: [],
        subtotal: 0,
        total: 0,
        payment_terms: 'Payment due within 30 days of report date',
      },
    },
    mode: 'onChange',
  });

  const { register, handleSubmit, formState: { errors, isDirty }, setValue, watch, getValues, trigger } = formMethods;

  // Watch for property count changes
  const propertyCount = watch('property_count') || 3;
  const propertySource = watch('property_source') || 'new';
  const propertyIds = watch('property_ids') || [];
  const properties = watch('properties') || [];

  // Calculate total steps dynamically
  const getStepCount = () => {
    const baseSteps = 4; // Applicant + Purpose + Source + Count
    const newPropertyCount = properties.length;
    const finalSteps = 3; // Review + Invoice + Certification
    return baseSteps + newPropertyCount + finalSteps;
  };

  const totalSteps = getStepCount();

  // Calculate which step we're on
  const getCurrentStepType = () => {
    if (currentStep === 1) return 'applicant';
    if (currentStep === 2) return 'purpose';
    if (currentStep === 3) return 'propertySource';
    if (currentStep === 4) return 'propertyCount';

    const propertyStepsStart = 5;
    const propertyStepsEnd = 5 + properties.length - 1;

    if (currentStep >= propertyStepsStart && currentStep <= propertyStepsEnd) {
      return { type: 'property', index: currentStep - propertyStepsStart };
    }

    if (currentStep === propertyStepsEnd + 1) return 'review';
    if (currentStep === propertyStepsEnd + 2) return 'invoice';
    if (currentStep === propertyStepsEnd + 3) return 'certification';

    return 'unknown';
  };

  // Load initial data in edit mode
  useEffect(() => {
    if (isEditMode && initialData) {
      console.log('[MultiPropertyStepForm] Loading initial data for edit mode:', initialData);

      // Populate common fields
      Object.keys(initialData).forEach((key) => {
        if (initialData[key] !== undefined && initialData[key] !== null) {
          setValue(key as any, initialData[key]);
        }
      });

      // TODO: Load associated properties from API
      // This will be implemented when we add the getReportProperties endpoint
    }
  }, [isEditMode, initialData, setValue]);

  // Handle property count changes
  useEffect(() => {
    const currentCount = properties.length;
    const newCount = propertyCount;

    if (newCount > currentCount) {
      // Add empty property objects
      const propertiesToAdd = Array(newCount - currentCount).fill({});
      setValue('properties', [...properties, ...propertiesToAdd]);
    } else if (newCount < currentCount) {
      // TODO: Show confirmation modal before removing properties
      // For now, just truncate
      setValue('properties', properties.slice(0, newCount));
    }
  }, [propertyCount]);

  // Navigation handlers
  const nextStep = async () => {
    // Validate current step before proceeding
    const stepType = getCurrentStepType();
    let isValid = true;

    if (stepType === 'applicant') {
      isValid = await trigger(['applicant_full_name']);
    } else if (stepType === 'purpose') {
      isValid = await trigger(['valuation_type', 'valuation_purpose']);
    } else if (stepType === 'propertyCount') {
      isValid = await trigger(['property_count']);
    }

    if (isValid && currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (!isValid) {
      toast.error('Please fill in all required fields');
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // Form submission handler
  const handleFormSubmit = async (submissionType: 'draft' | 'complete') => {
    const formData = getValues();

    console.log('[MultiPropertyStepForm] Submitting form:', formData);

    await onSubmit(formData, submissionType);
  };

  // Render step content
  const renderStep = () => {
    const stepType = getCurrentStepType();

    if (stepType === 'applicant') {
      return renderApplicantStep();
    } else if (stepType === 'purpose') {
      return renderPurposeStep();
    } else if (stepType === 'propertySource') {
      return renderPropertySourceStep();
    } else if (stepType === 'propertyCount') {
      return renderPropertyCountStep();
    } else if (typeof stepType === 'object' && stepType.type === 'property') {
      return renderPropertyDetailsStep(stepType.index);
    } else if (stepType === 'review') {
      return renderReviewStep();
    } else if (stepType === 'invoice') {
      return renderInvoiceStep();
    } else if (stepType === 'certification') {
      return renderCertificationStep();
    }

    return <div>Unknown step</div>;
  };

  // Step 1: Applicant Information
  const renderApplicantStep = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-50 to-cyan-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Applicant Information</h3>
        <p className="text-gray-600">Who is requesting this multi-property valuation?</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Label htmlFor="applicant_title">Title</Label>
          <select
            {...register('applicant_title')}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
          >
            <option value="">Select title</option>
            <option value="Mr.">Mr.</option>
            <option value="Mrs.">Mrs.</option>
            <option value="Miss">Miss</option>
            <option value="Ms.">Ms.</option>
            <option value="Dr.">Dr.</option>
            <option value="Rev.">Rev.</option>
          </select>
        </div>

        <div>
          <Label htmlFor="applicant_full_name">Full Name *</Label>
          <Input
            {...register('applicant_full_name')}
            placeholder="Enter full name"
            className={errors.applicant_full_name ? 'border-red-500' : ''}
          />
          {errors.applicant_full_name && (
            <p className="text-red-500 text-sm mt-1">{errors.applicant_full_name.message}</p>
          )}
        </div>

        <div>
          <Label htmlFor="applicant_id_type">
            ID Type <span className="text-gray-500 text-sm font-normal">(Optional)</span>
          </Label>
          <select
            {...register('applicant_id_type')}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
          >
            <option value="">Select ID type (optional)</option>
            <option value="nic">National Identity Card (NIC)</option>
            <option value="passport">Passport</option>
            <option value="driving_license">Driving License</option>
          </select>
        </div>

        <div>
          <Label htmlFor="applicant_id_number">
            ID Number <span className="text-gray-500 text-sm font-normal">(Optional)</span>
          </Label>
          <Input
            {...register('applicant_id_number')}
            placeholder="Enter ID number (optional)"
          />
        </div>

        <div className="md:col-span-2">
          <Label htmlFor="applicant_address_line1">Address Line 1</Label>
          <Input
            {...register('applicant_address_line1')}
            placeholder="Street address"
          />
        </div>

        <div className="md:col-span-2">
          <Label htmlFor="applicant_address_line2">Address Line 2</Label>
          <Input
            {...register('applicant_address_line2')}
            placeholder="Apartment, suite, etc. (optional)"
          />
        </div>

        <div>
          <Label htmlFor="applicant_district">District</Label>
          <Input
            {...register('applicant_district')}
            placeholder="e.g., Colombo"
          />
        </div>

        <div>
          <Label htmlFor="applicant_province">Province</Label>
          <Input
            {...register('applicant_province')}
            placeholder="e.g., Western"
          />
        </div>

        <div>
          <Label htmlFor="applicant_country">Country</Label>
          <Input
            {...register('applicant_country')}
            defaultValue="Sri Lanka"
          />
        </div>
      </div>
    </div>
  );

  // Step 2: Valuation Purpose
  const renderPurposeStep = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-emerald-50 to-green-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Valuation Purpose</h3>
        <p className="text-gray-600">Why are these properties being valued?</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Label htmlFor="valuation_type">Valuation Type</Label>
          <select
            {...register('valuation_type')}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
          >
            <option value="">Select type</option>
            <option value="Market Value">Market Value</option>
            <option value="Forced Sale Value">Forced Sale Value</option>
            <option value="Insurance Value">Insurance Value</option>
          </select>
        </div>

        <div>
          <Label htmlFor="valuation_purpose">Valuation Purpose</Label>
          <select
            {...register('valuation_purpose')}
            className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent"
          >
            <option value="">Select purpose</option>
            <option value="Loan">Loan</option>
            <option value="Mortgage">Mortgage</option>
            <option value="Sale">Sale</option>
            <option value="Insurance">Insurance</option>
            <option value="Tax Assessment">Tax Assessment</option>
            <option value="Portfolio Valuation">Portfolio Valuation</option>
          </select>
        </div>

        <div className="md:col-span-2">
          <Label htmlFor="inspection_date">Inspection Date (Shared)</Label>
          <DatePicker
            id="inspection_date"
            value={watch('inspection_date') || ''}
            onChange={(date) => setValue('inspection_date', date)}
            placeholder="DD-MM-YYYY"
            className="w-full"
          />
          <p className="text-sm text-gray-500 mt-1">This date applies to all properties in this report</p>
        </div>

        <div className="md:col-span-2">
          <Label htmlFor="submission_organization">Submission Organization</Label>
          <Input
            {...register('submission_organization')}
            placeholder="e.g., ABC Bank, XYZ Insurance Company"
          />
        </div>

        <div className="md:col-span-2">
          <Label htmlFor="report_reference">Report Reference (Optional)</Label>
          <Input
            {...register('report_reference')}
            placeholder="Internal reference number"
          />
        </div>
      </div>
    </div>
  );

  // Step 3: Property Source Selection
  const renderPropertySourceStep = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-violet-50 to-purple-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Property Source</h3>
        <p className="text-gray-600">Where will the properties come from?</p>
      </div>

      <div className="space-y-4">
        <p className="text-gray-700 font-medium mb-4">Choose how you want to add properties to this report:</p>

        {/* Placeholder for PropertySourceSelector component */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 border border-gray-200">
          <div className="space-y-3">
            <label className="flex items-center p-4 border-2 border-gray-300 rounded-xl cursor-pointer hover:border-violet-500 transition-colors">
              <input
                type="radio"
                {...register('property_source')}
                value="new"
                className="mr-3"
              />
              <div>
                <div className="font-semibold text-gray-900">Create New Properties</div>
                <div className="text-sm text-gray-600">Enter all property details from scratch</div>
              </div>
            </label>

            <label className="flex items-center p-4 border-2 border-gray-300 rounded-xl cursor-pointer hover:border-violet-500 transition-colors opacity-50">
              <input
                type="radio"
                {...register('property_source')}
                value="library"
                disabled
                className="mr-3"
              />
              <div>
                <div className="font-semibold text-gray-900">Select from Property Library</div>
                <div className="text-sm text-gray-600">Choose existing property templates (Coming soon)</div>
              </div>
            </label>

            <label className="flex items-center p-4 border-2 border-gray-300 rounded-xl cursor-pointer hover:border-violet-500 transition-colors opacity-50">
              <input
                type="radio"
                {...register('property_source')}
                value="mix"
                disabled
                className="mr-3"
              />
              <div>
                <div className="font-semibold text-gray-900">Mix Both</div>
                <div className="text-sm text-gray-600">Combine library properties with new ones (Coming soon)</div>
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  // Step 4: Property Count Selection
  const renderPropertyCountStep = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-orange-50 to-red-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Property Count</h3>
        <p className="text-gray-600">How many properties will be valued?</p>
      </div>

      <div>
        <Label htmlFor="property_count">Number of Properties (2-20)</Label>
        <Input
          type="number"
          {...register('property_count', { valueAsNumber: true })}
          min={2}
          max={20}
          className="w-full"
        />
        {errors.property_count && (
          <p className="text-red-500 text-sm mt-1">{errors.property_count.message}</p>
        )}

        <div className="mt-4 p-4 bg-blue-50 rounded-xl">
          <p className="text-sm text-gray-700">
            You are valuing <span className="font-bold text-violet-600">{propertyCount} properties</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">
            You'll need to provide details for each property in the following steps
          </p>
        </div>
      </div>
    </div>
  );

  // Property Details Step (repeated for each property)
  const renderPropertyDetailsStep = (propertyIndex: number) => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-indigo-50 to-blue-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Property {propertyIndex + 1} Details
        </h3>
        <p className="text-gray-600">Enter information for property {propertyIndex + 1} of {propertyCount}</p>
      </div>

      <PropertyDetailsStep
        propertyIndex={propertyIndex}
        formMethods={formMethods}
        isEditMode={isEditMode}
      />
    </div>
  );

  // Handle editing a specific property from the review step
  const handleEditProperty = (propertyIndex: number) => {
    // Navigate to the property step (5 + propertyIndex)
    const propertyStep = 5 + propertyIndex;
    setCurrentStep(propertyStep);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Review & Compare Step
  const renderReviewStep = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-indigo-50 to-blue-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Review & Compare Properties</h3>
        <p className="text-gray-600">Review all properties and reorder if needed</p>
      </div>

      <PropertyComparisonStep
        formMethods={formMethods}
        onEditProperty={handleEditProperty}
      />
    </div>
  );

  // Invoice Step
  const renderInvoiceStep = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-pink-50 to-rose-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Professional Fees Invoice</h3>
        <p className="text-gray-600">Enter invoice details for this valuation</p>
      </div>

      <InvoiceDataStep formMethods={formMethods} />
    </div>
  );

  // Certification Step
  const renderCertificationStep = () => (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-amber-50 to-yellow-100 rounded-2xl p-6 mb-6">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Certification</h3>
        <p className="text-gray-600">Certify this multi-property valuation report</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <Label htmlFor="certification_valuer_name">Valuer Name</Label>
          <Input
            {...register('certification_valuer_name')}
            defaultValue={user?.full_name}
            placeholder="Valuer name"
          />
        </div>

        <div>
          <Label htmlFor="certification_date">Certification Date</Label>
          <DatePicker
            id="certification_date"
            value={watch('certification_date') || ''}
            onChange={(date) => setValue('certification_date', date)}
            placeholder="DD-MM-YYYY"
          />
        </div>

        <div className="md:col-span-2">
          <Label htmlFor="certification_valuer_designation">Designation</Label>
          <Input
            {...register('certification_valuer_designation')}
            placeholder="e.g., Chartered Valuation Surveyor"
          />
        </div>

        <div className="md:col-span-2">
          <div className="flex items-start">
            <input
              type="checkbox"
              {...register('certificate_identity_confirmed')}
              className="mt-1 mr-3"
            />
            <Label htmlFor="certificate_identity_confirmed" className="cursor-pointer">
              I confirm that I have personally inspected the properties and certify the accuracy of this valuation report
            </Label>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-violet-50 py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Progress Bar */}
        <div className="mb-12">
          <div className="flex items-center justify-between relative mb-4">
            <div className="absolute top-5 left-0 w-full h-1 bg-gray-200 rounded-full">
              <div
                className="h-1 bg-gradient-to-r from-violet-500 to-purple-600 transition-all duration-500 rounded-full"
                style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
              />
            </div>

            {/* Step indicators - show first 4, current property step, and last 3 */}
            <div className="relative z-10 flex justify-between w-full">
              {Array.from({ length: Math.min(7, totalSteps) }).map((_, index) => {
                let stepNum = index + 1;
                if (index >= 4 && totalSteps > 7) {
                  // Adjust for middle steps
                  stepNum = index < 4 ? index + 1 : totalSteps - (6 - index);
                }

                const isActive = currentStep === stepNum;
                const isCompleted = currentStep > stepNum;

                return (
                  <div
                    key={stepNum}
                    className={`w-10 h-10 rounded-full border-4 flex items-center justify-center font-bold transition-all duration-300 ${
                      isCompleted
                        ? 'bg-green-500 border-green-600 text-white'
                        : isActive
                        ? 'bg-violet-500 border-violet-600 text-white scale-110'
                        : 'bg-white border-gray-300 text-gray-400'
                    }`}
                  >
                    {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : stepNum}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Step {currentStep} of {totalSteps}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {propertyCount} properties • Multi-Property Valuation Report
            </p>
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8 lg:p-12">
          {renderStep()}

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center pt-8 mt-8 border-t border-gray-200/50">
            <Button
              type="button"
              onClick={prevStep}
              disabled={currentStep === 1}
              className={`flex items-center px-6 py-3 rounded-2xl font-medium transition-all duration-200 ${
                currentStep === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Previous
            </Button>

            <div className="flex gap-3">
              {currentStep === totalSteps ? (
                <>
                  <Button
                    type="button"
                    onClick={() => handleFormSubmit('draft')}
                    disabled={isSubmitting}
                    className="px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-2xl font-medium"
                  >
                    Save as Draft
                  </Button>
                  <Button
                    type="button"
                    onClick={() => handleFormSubmit('complete')}
                    disabled={isSubmitting}
                    className="px-8 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-2xl font-bold shadow-lg"
                  >
                    {isSubmitting ? 'Submitting...' : 'Generate Report'}
                  </Button>
                </>
              ) : (
                <Button
                  type="button"
                  onClick={nextStep}
                  className="flex items-center px-8 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-2xl font-bold shadow-lg"
                >
                  Next
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Help Text */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Your progress is automatically saved as you complete each step</p>
        </div>
      </div>

      {/* Loading Overlay */}
      {isSubmitting && <LoadingOverlay message="Submitting report..." />}
    </div>
  );
};

export default MultiPropertyStepForm;
export type { MultiPropertyFormData };
