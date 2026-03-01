import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast, { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft, CheckCircle2, Save } from 'lucide-react';
import { useDraftManager } from '../hooks/useDraftManager';
import { useNavigationBlocker } from '../hooks/useNavigationBlocker';
import NavigationConfirmModal from './NavigationConfirmModal';
import { ErrorSummaryPanel } from './ErrorSummaryPanel';
import { transformZodErrors, ValidationErrorSummary } from '../utils/validationErrorTransformer';
import { Button } from './Button';
import { PropertyDescriptionStep } from './PropertyDescriptionStep';
import InvoiceDataStep from './InvoiceDataStep';
import LocalityInformationSection from './LocalityInformationSection';
import LegalAspectsSection from './LegalAspectsSection';
import LandValuesSection from './LandValuesSection';
import ValuationSection from './ValuationSection';
import CertificationSection from './CertificationSection';
import { LoadingOverlay } from './LoadingOverlay';
import { FORM_STEPS, PHASES, getFirstStepIndexInPhase } from '../constants/multiStepFormConstants';
import PhaseTabBar from './steps/PhaseTabBar';
import { PropertyPlanStep } from './steps/PropertyPlanStep';
import { ExtentBoundariesStep } from './steps/ExtentBoundariesStep';
import { PropertySearchStep } from './steps/PropertySearchStep';
import { PropertyLocationNewStep } from './steps/PropertyLocationNewStep';
import { ApplicantPurposeStep } from './steps/ApplicantPurposeStep';
import { AdditionalDetailsStep } from './steps/AdditionalDetailsStep';
import {
    propertyPlanSchema,
    applicantPurposeSchema,
    additionalDetailsSchema,
    extentBoundariesSchema,
    propertySearchSchema,
    propertyDetailsSchema,
    propertyDescriptionSchema,
    completeFormSchema,
    propertyOnlySchema,
} from '../schemas/multiStepFormSchemas';
import type { FormData, MultiStepFormProps, DataQualityWarning } from '../types/multiStepForm';
import { getCSRFToken } from '../utils/csrf';

const steps = FORM_STEPS;

/**
 * Transform individual deed form fields into backend array format
 * @param formData - Raw form data with individual deed fields
 * @returns Transformed deed array or undefined
 */
const transformDeedData = (formData: any) => {
    const identificationType = formData.property_identification_type;
    let deedData = undefined;

    if (identificationType === 'deed') {
        // Regular deed only
        const hasDeedData = formData.deed_number && formData.deed_date;
        if (hasDeedData) {
            deedData = [{
                deed_type: formData.deed_type || null,
                deed_number: formData.deed_number,
                deed_date: formData.deed_date,
                notary_name: formData.notary_name || null,
                notary_location: formData.notary_location || null,
            }];
        }
    } else if (identificationType === 'plan_and_deed') {
        // HYBRID MODE: Include deed data alongside plan data
        const hasDeedData = formData.deed_number && formData.deed_date;
        if (hasDeedData) {
            deedData = [{
                deed_type: formData.deed_type || null,
                deed_number: formData.deed_number,
                deed_date: formData.deed_date,
                notary_name: formData.notary_name || null,
                notary_location: formData.notary_location || null,
            }];
        }
    } else if (identificationType === 'certificate_of_sale') {
        // Certificate of Sale (stored as deed with fixed type)
        const hasCertData = formData.certificate_number && formData.certificate_date;
        if (hasCertData) {
            deedData = [{
                deed_type: 'Certificate of Sale',
                deed_number: formData.certificate_number,
                deed_date: formData.certificate_date,
                notary_name: formData.certificate_notary_name || null,
                notary_location: formData.certificate_notary_district || null,
            }];
        }
    }
    // If identificationType === 'plan', deedData stays undefined

    return deedData;
};

const MultiStepForm: React.FC<MultiStepFormProps> = ({
    onSubmit,
    isSubmitting = false,
    user,
    isEditMode = false,
    reportId,
    initialData,
    reportType = 'residential_property',
    isEmbeddedInMultiProperty = false,
    commonData,
    onSaveProperty,
    onFinishProperty,
    onCancelProperty,
    hideCertification = false
}) => {
    const isBareLand = reportType === 'bare_land';

    // Filter steps based on context (multi-property vs standalone)
    const getActiveSteps = () => {
        if (!isEmbeddedInMultiProperty) {
            return steps;  // All 13 steps for standalone reports
        }

        // Multi-property: Exclude steps 9, 10, and 12
        // - Step 9 (Applicant): Common data handled at report level
        // - Step 10 (Additional Details): Common data handled at report level
        // - Step 12 (Invoice): Handled at report level (step 4 of multi-property flow)
        let filteredSteps = steps.filter(step => step.id !== 9 && step.id !== 10 && step.id !== 12);

        if (hideCertification) {
            filteredSteps = filteredSteps.filter(step => step.id !== 13);
        }

        // Re-number for display (1-10 instead of 1,2,3,4,5,6,7,8,12,13)
        return filteredSteps.map((step, index) => ({
            ...step,
            displayId: index + 1,  // Display sequential numbers
            originalId: step.id     // Keep original for render logic
        }));
    };

    const activeSteps = getActiveSteps();
    const maxStep = activeSteps.length;

    const [currentStep, setCurrentStep] = useState(1);
    const navigate = useNavigate();
    const [showNavigationModal, setShowNavigationModal] = useState(false);
    const [pendingNavigation, setPendingNavigation] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [isSavingAndContinue, setIsSavingAndContinue] = useState(false);
    const [isSavingAndExit, setIsSavingAndExit] = useState(false);
    const [validationErrors, setValidationErrors] = useState<ValidationErrorSummary[]>([]);
    const [showErrorPanel, setShowErrorPanel] = useState(false);
    const [dataQualityWarnings, setDataQualityWarnings] = useState<DataQualityWarning[]>([]);
    const [showWarningsPanel, setShowWarningsPanel] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState<string>('');


    const formMethods = useForm<FormData>({
        resolver: zodResolver(isEmbeddedInMultiProperty ? propertyOnlySchema : completeFormSchema),
        mode: 'onTouched',        // Validate on blur
        reValidateMode: 'onChange', // Re-validate on change after first validation
        defaultValues: {
            // Initialize all optional fields with undefined so they're tracked by react-hook-form
            property_village: undefined,
            property_district: undefined,
            property_province: undefined,
            property_latitude: undefined,
            property_longitude: undefined,
            property_number: undefined,
            property_divisional_secretariat: undefined,
            grama_niladari_division: undefined,
            korale: undefined,
            pradeshiya_sabha: undefined,
            ward_number: undefined,
            is_municipal_limit: undefined,
            assessment_number: undefined,
            property_road_position: undefined,
            location_direction: undefined,
            access_starting_point_name: undefined,
            access_starting_point_latitude: undefined,
            access_starting_point_longitude: undefined,
            access_directions_text: undefined,
            access_distance_km: undefined,
            access_duration_minutes: undefined,
            access_route_data: undefined,
            access_road_type: undefined,
            location_map_image_data: undefined,
            use_property_address_as_applicant: false,
            // DEED DATA FIX: Register deed fields in defaultValues so react-hook-form tracks them
            deed_type: '',
            deed_number: '',
            deed_date: '',
            notary_name: '',
            notary_location: '',
            certificate_number: '',
            certificate_date: '',
            certificate_notary_name: '',
            certificate_notary_district: '',
            // Certification checkbox
            certificate_identity_confirmed: false,

            // Merge commonData when embedded in multi-property
            ...(isEmbeddedInMultiProperty && commonData ? {
                applicant_title: commonData.applicant_title,
                applicant_full_name: commonData.applicant_full_name,
                applicant_id_type: commonData.applicant_id_type,
                applicant_id_number: commonData.applicant_id_number,
                applicant_address_line1: commonData.applicant_address_line1,
                applicant_address_line2: commonData.applicant_address_line2,
                applicant_district: commonData.applicant_district,
                applicant_province: commonData.applicant_province,
                applicant_country: commonData.applicant_country,
                valuation_type: commonData.valuation_type,
                valuation_purpose: commonData.valuation_purpose,
                property_type_valued: commonData.property_type_valued,
                has_additional_owner: commonData.has_additional_owner,
                additional_owner_names: commonData.additional_owner_names,
                submission_recipient_position: commonData.submission_recipient_position,
                submission_organization: commonData.submission_organization,
                submission_address: commonData.submission_address,
                inspection_date: commonData.inspection_date,
                has_special_note: commonData.has_special_note,
                special_note_text: commonData.special_note_text,
                report_reference: commonData.report_reference,
                report_date: commonData.report_date,
            } : {}),
        } as Partial<FormData>,
    });

    // Destructure form methods for convenience
    const {
        register,
        handleSubmit,
        formState: { errors },
        trigger,
        watch,
        getValues,
        setValue,
        reset,
        clearErrors,
    } = formMethods;

    // Load initial data for edit mode
    useEffect(() => {
        if (isEditMode && initialData) {
            console.log('[MultiStepForm] Loading initial data for editing:', initialData);

            // Convert boolean values to strings for backward compatibility
            const convertedData = {
                ...initialData,
                has_deed_info: typeof initialData.has_deed_info === 'boolean'
                    ? (initialData.has_deed_info ? 'yes' : 'no')
                    : initialData.has_deed_info,
                has_special_note: typeof initialData.has_special_note === 'boolean'
                    ? (initialData.has_special_note ? 'yes' : 'no')
                    : initialData.has_special_note,
                has_additional_owner: typeof initialData.has_additional_owner === 'boolean'
                    ? (initialData.has_additional_owner ? 'yes' : 'no')
                    : initialData.has_additional_owner,
                // Ensure arrays are properly initialized
                buildings: initialData.buildings || [],
                property_photos: initialData.property_photos || [],
                comparable_properties: initialData.comparable_properties || [],
                deeds: initialData.deeds || [],
                valuation_addons: initialData.valuation_addons || [],
                // Ensure nested objects are preserved
                valuation_buildings_data: initialData.valuation_buildings_data || [],
            };

            console.log('[MultiStepForm] Converted data for form:', convertedData);
            console.log('[MultiStepForm] Buildings data:', convertedData.buildings);
            console.log('[MultiStepForm] Valuation data:', convertedData.valuation_buildings_data);

            reset(convertedData);

            // DEED DATA FIX: Unpack deeds array into individual form fields
            // Backend stores deeds as JSON array, but form uses individual fields
            if (convertedData.deeds && Array.isArray(convertedData.deeds) && convertedData.deeds.length > 0) {
                console.log('[MultiStepForm] Unpacking deed data from array:', convertedData.deeds);
                const firstDeed = convertedData.deeds[0];

                if (firstDeed.deed_type === 'Certificate of Sale') {
                    // Certificate of Sale mode
                    setValue('property_identification_type', 'certificate_of_sale');
                    setValue('certificate_number', firstDeed.deed_number || '');
                    setValue('certificate_date', firstDeed.deed_date || '');
                    setValue('certificate_notary_name', firstDeed.notary_name || '');
                    setValue('certificate_notary_district', firstDeed.notary_location || '');
                    console.log('[MultiStepForm] Set certificate fields');
                } else if (convertedData.plan_number) {
                    // Hybrid mode (plan + deed)
                    setValue('property_identification_type', 'plan_and_deed');
                    setValue('deed_type', firstDeed.deed_type || '');
                    setValue('deed_number', firstDeed.deed_number || '');
                    setValue('deed_date', firstDeed.deed_date || '');
                    setValue('notary_name', firstDeed.notary_name || '');
                    setValue('notary_location', firstDeed.notary_location || '');
                    console.log('[MultiStepForm] Set hybrid plan+deed fields');
                } else {
                    // Deed only mode
                    setValue('property_identification_type', 'deed');
                    setValue('deed_type', firstDeed.deed_type || '');
                    setValue('deed_number', firstDeed.deed_number || '');
                    setValue('deed_date', firstDeed.deed_date || '');
                    setValue('notary_name', firstDeed.notary_name || '');
                    setValue('notary_location', firstDeed.notary_location || '');
                    console.log('[MultiStepForm] Set deed-only fields');
                }
            }

            toast.success('Report loaded for editing', { duration: 2000 });
        }
    }, [isEditMode, initialData, reset]);

    // Clear applicant/additional details errors in embedded mode (these fields are handled by parent)
    useEffect(() => {
        if (isEmbeddedInMultiProperty) {
            // Clear validation errors for applicant and additional details fields
            const fieldsToSkip = [
                'applicant_title', 'applicant_full_name', 'applicant_id_type', 'applicant_id_number',
                'applicant_address_line1', 'applicant_address_line2', 'applicant_district',
                'applicant_province', 'applicant_country', 'valuation_type', 'valuation_purpose',
                'property_type_valued', 'has_additional_owner', 'additional_owner_names',
                'submission_organization', 'submission_address', 'submission_recipient_position',
                'inspection_date', 'has_special_note', 'special_note_text', 'report_reference', 'report_date'
            ];
            clearErrors(fieldsToSkip as any);

            // Also clear from validation errors state (for ErrorSummaryPanel)
            setValidationErrors([]);

            // Hide error panel since we're clearing applicant errors
            setShowErrorPanel(false);
        }
    }, [isEmbeddedInMultiProperty, clearErrors]);

    // Draft management hooks
    // Disable draft manager in embedded mode (multi-property handles saves explicitly)
    const { isDirty, saveDraft } = useDraftManager({
        reportId,
        isEditMode: isEditMode && !isEmbeddedInMultiProperty,  // Disable in embedded mode
        formMethods: { watch, getValues, setValue }
    });

    // Disable navigation blocker in embedded mode (users need to freely navigate back to dashboard)
    useNavigationBlocker(isDirty && !isSaving && !isEmbeddedInMultiProperty, () => {
        setShowNavigationModal(true);
    });


    const getCurrentStepSchema = () => {
        // Get the actual step ID (originalId for multi-property, id for standalone)
        // This ensures validation matches the component being rendered regardless of display order
        const currentStepConfig = activeSteps[currentStep - 1];
        const actualStepId = currentStepConfig?.originalId || currentStepConfig?.id || currentStep;

        switch (actualStepId) {
            case 1: return propertyPlanSchema; // Property & Plan validation
            case 2: return extentBoundariesSchema; // Extent & Boundaries validation
            case 3: return propertySearchSchema; // Property Search - location required
            case 4: return propertyDetailsSchema; // Property Details - village/district required
            case 5: return z.object({}); // Locality Information - no required validation
            case 6: return propertyDescriptionSchema; // Property Description validation
            case 7: return z.object({}); // Legal Aspects - no required validation
            case 8: return z.object({}); // Land Values - no required validation
            case 9: return applicantPurposeSchema; // Applicant & Purpose validation
            case 10: return additionalDetailsSchema; // Additional Details validation
            case 11: return z.object({}); // Valuation - no required validation
            case 12: return z.object({}); // Invoice - optional, no strict validation
            case 13: return z.object({}); // Certification - certificate_identity_confirmed validation removed (now optional)
            default: return z.object({});
        }
    };

    const validateCurrentStep = async () => {
        // In embedded multi-property mode, skip validation entirely
        // Properties can be incomplete - validation happens in parent form
        if (isEmbeddedInMultiProperty) {
            return true;
        }

        const stepSchema = getCurrentStepSchema();
        const stepData = getValues();

        try {
            stepSchema.parse(stepData);
            // Clear errors on successful validation
            setValidationErrors([]);
            setShowErrorPanel(false);
            return true;
        } catch (error) {
            if (error instanceof z.ZodError) {
                // Transform Zod errors to user-friendly format
                const transformedErrors = transformZodErrors(error.errors);
                setValidationErrors(transformedErrors);
                setShowErrorPanel(true);

                // Trigger validation to show inline errors
                // Ensure stepSchema.shape is an object before calling Object.keys
                if (stepSchema && stepSchema.shape) {
                    await trigger(Object.keys(stepSchema.shape) as any);
                }

                // Scroll to first error and focus
                setTimeout(() => {
                    const firstErrorField = error.errors[0]?.path[0];
                    if (firstErrorField) {
                        const element = document.getElementById(String(firstErrorField));
                        element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        element?.focus();
                    }
                }, 100);
            }
            return false;
        }
    };

    // Check data quality for non-blocking warnings
    const checkDataQuality = () => {
        const formData = getValues();
        const warnings: DataQualityWarning[] = [];

        // Check property identification completeness
        const idType = formData.property_identification_type;

        if (idType === 'plan' || idType === 'plan_and_deed') {
            if (!formData.licensed_surveyor_name) {
                warnings.push({
                    field: 'licensed_surveyor_name',
                    message: 'Licensed surveyor name is missing. This information strengthens the report.',
                    severity: 'warning'
                });
            }
            if (!formData.lot_number) {
                warnings.push({
                    field: 'lot_number',
                    message: 'Lot number is missing. Consider adding this for clarity.',
                    severity: 'info'
                });
            }
        }

        if (idType === 'deed' || idType === 'plan_and_deed') {
            if (!formData.deed_type) {
                warnings.push({
                    field: 'deed_type',
                    message: 'Deed type is missing (e.g., Transfer Deed, Deed of Gift). Consider adding this.',
                    severity: 'info'
                });
            }
            if (!formData.notary_name) {
                warnings.push({
                    field: 'notary_name',
                    message: 'Notary name is missing. This information may be required for legal purposes.',
                    severity: 'warning'
                });
            }
        }

        // Check boundary information
        const boundaries = formData.boundaries;
        if (boundaries) {
            const hasAllBoundaries = boundaries.north && boundaries.south && boundaries.east && boundaries.west;
            if (!hasAllBoundaries) {
                warnings.push({
                    field: 'boundaries',
                    message: 'Some boundary descriptions are missing (North/South/East/West). Complete boundary information improves report quality.',
                    severity: 'warning'
                });
            }
        } else {
            warnings.push({
                field: 'boundaries',
                message: 'Boundary information is missing. This is important for property identification.',
                severity: 'warning'
            });
        }

        // Check property location
        if (!formData.property_latitude) {
            warnings.push({
                field: 'property_latitude',
                message: 'Property location is not set. Use the Property Search step to add location.',
                severity: 'warning'
            });
        }

        // Check applicant information
        if (!formData.applicant_full_name) {
            warnings.push({
                field: 'applicant_full_name',
                message: 'Applicant name is missing. This is required for the final report.',
                severity: 'warning'
            });
        }

        // Check building/land description
        if (!formData.buildings || formData.buildings.length === 0) {
            warnings.push({
                field: 'buildings',
                message: 'No building information added. If the property has structures, add them in Property Description.',
                severity: 'info'
            });
        }

        setDataQualityWarnings(warnings);
        setShowWarningsPanel(warnings.length > 0);

        return warnings;
    };

    const handleErrorClick = (fieldName: string) => {
        const element = document.getElementById(fieldName);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            element.focus();

            // Add temporary highlight effect
            element.classList.add('ring-2', 'ring-red-500', 'ring-offset-2');
            setTimeout(() => {
                element.classList.remove('ring-2', 'ring-red-500', 'ring-offset-2');
            }, 2000);
        }
    };

    const nextStep = async (e?: React.MouseEvent<HTMLButtonElement>) => {
        e?.preventDefault(); // Prevent any form submission
        e?.stopPropagation(); // Prevent event bubbling

        // Always run validation so errors appear in the error panel, but never block navigation
        await validateCurrentStep();

        if (currentStep < maxStep) {
            const nextStepNum = currentStep + 1;
            setCurrentStep(nextStepNum);

            // Smooth scroll to top when navigating to next step
            window.scrollTo({ top: 0, behavior: 'smooth' });

            // Check data quality when entering the final certification step
            if (nextStepNum === maxStep) {
                setTimeout(() => {
                    checkDataQuality();
                }, 500); // Small delay to allow step to render
            }
        }
    };

    const prevStep = (e?: React.MouseEvent<HTMLButtonElement>) => {
        e?.preventDefault(); // Prevent any form submission
        e?.stopPropagation(); // Prevent event bubbling

        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
            // Smooth scroll to top when navigating to previous step
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    // Handle click on phase step dots — free navigation, no validation gate
    const handleStepClick = (targetStepIndex: number) => {
        if (targetStepIndex === currentStep) return;
        setCurrentStep(targetStepIndex);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // Handle click on a phase tab — jump to the first step of that phase
    const handlePhaseClick = (phaseId: number) => {
        const phase = PHASES.find(p => p.id === phaseId);
        if (!phase) return;
        const targetIndex = getFirstStepIndexInPhase(phase, activeSteps);
        setCurrentStep(targetIndex);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // Save and Continue handler (new)
    const handleSaveAndContinue = async (e?: React.MouseEvent<HTMLButtonElement>) => {
        e?.preventDefault();
        e?.stopPropagation();

        try {
            setIsSavingAndContinue(true);
            const formData = getValues(); // NO validation - drafts can be incomplete

            // Transform deed data to array format
            const deedData = transformDeedData(formData);

            // Prepare submission data with transformed deed data
            const submissionData = {
                ...formData,
                deeds: deedData,
                has_deed_info: deedData ? 'yes' : 'no',
            };

            // Multi-property mode: call onSaveProperty
            if (isEmbeddedInMultiProperty && onSaveProperty) {
                await onSaveProperty(submissionData);
            } else {
                // Standalone mode: call onSubmit with 'draft'
                await onSubmit(submissionData, 'draft');
            }

            toast.success('Draft saved successfully');
            // Stay on current page - user continues editing
        } catch (error) {
            toast.error('Failed to save draft');
            console.error('Save error:', error);
        } finally {
            setIsSavingAndContinue(false);
        }
    };

    // Save & Exit handler
    const handleSaveAndExit = async (e?: React.MouseEvent<HTMLButtonElement>) => {
        e?.preventDefault();
        e?.stopPropagation();

        try {
            setIsSavingAndExit(true);
            const formData = getValues(); // NO validation - drafts can be incomplete

            // Transform deed data to array format
            const deedData = transformDeedData(formData);

            // Prepare submission data with transformed deed data
            const submissionData = {
                ...formData,
                deeds: deedData,
                has_deed_info: deedData ? 'yes' : 'no',
            };

            // Multi-property mode: call onSaveProperty
            if (isEmbeddedInMultiProperty && onSaveProperty) {
                await onSaveProperty(submissionData);
            } else {
                // Standalone mode: call onSubmit with 'draft'
                await onSubmit(submissionData, 'draft');
            }

            toast.success('Draft saved successfully');
            // Navigate to dashboard after successful save
            if (!isEmbeddedInMultiProperty) {
                navigate('/dashboard');
            }
        } catch (error) {
            toast.error('Failed to save draft');
            console.error('Save error:', error);
        } finally {
            setIsSavingAndExit(false);
        }
    };

    // Keyboard shortcut for "Save and Continue" (Ctrl+S / Cmd+S)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault(); // Prevent browser's default save dialog
                if (!isSavingAndContinue && !isSavingAndExit && !isSubmitting) {
                    handleSaveAndContinue();
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isSavingAndContinue, isSavingAndExit, isSubmitting]);

    // Modal handlers
    const handleSaveAndProceed = async () => {
        await saveDraft();
        setShowNavigationModal(false);
        toast.success('Draft saved successfully');
        navigate(pendingNavigation || '/dashboard');
    };

    const handleDiscardAndProceed = () => {
        setShowNavigationModal(false);
        navigate(pendingNavigation || '/dashboard');
    };


    // Auto-save on window close
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (isDirty) {
                e.preventDefault();
                const formData = getValues();
                const reportData = { ...formData, status: 'draft', report_type: 'residential_property' };

                const token = localStorage.getItem('authToken');
                const csrfToken = getCSRFToken();

                // Use fetch with keepalive instead of sendBeacon to allow custom headers (CSRF token)
                // keepalive: true allows the request to complete even during page unload
                fetch('/api/reports', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token && { Authorization: `Bearer ${token}` }),
                        ...(csrfToken && { 'X-CSRF-Token': csrfToken }),
                    },
                    body: JSON.stringify(reportData),
                    keepalive: true,
                });
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [isDirty, getValues]);



    const handleFormSubmit = async (validatedData: FormData) => {
        // CERTIFICATION STEP ENFORCEMENT: Only allow submission from final step
        if (currentStep !== maxStep && !isEmbeddedInMultiProperty) {
            toast.error('Please complete the Certification step before submitting the report');
            setCurrentStep(maxStep);
            return;
        }

        // Check data quality for warnings (non-blocking)
        const warnings = checkDataQuality();

        if (warnings.length > 0) {
            // Show warnings but allow user to proceed
            toast((t) => (
                <div className="flex flex-col gap-2">
                    <p className="font-semibold">⚠️ Data Quality Warnings ({warnings.length})</p>
                    <p className="text-sm">Your report has some missing information. You can still proceed, but the report quality may be improved by filling these fields.</p>
                    <button
                        onClick={() => toast.dismiss(t.id)}
                        className="mt-2 text-xs bg-amber-500 text-white px-3 py-1 rounded hover:bg-amber-600"
                    >
                        Dismiss
                    </button>
                </div>
            ), {
                duration: 8000,
                icon: '⚠️',
            });
        }

        // CRITICAL FIX: The Zod resolver strips out fields not in the schema!
        // We must use getValues() to get ALL form data, including optional fields set via setValue()
        const allFormData = getValues();

        if (import.meta.env.DEV) {
            console.log('[MultiStepForm] Validated data from handleSubmit:', validatedData);
            console.log('[MultiStepForm] ALL form data from getValues():', allFormData);
            console.log('[MultiStepForm] Property location fields:', {
                property_village: allFormData.property_village,
                property_district: allFormData.property_district,
                property_latitude: allFormData.property_latitude,
                property_longitude: allFormData.property_longitude,
                grama_niladari_division: allFormData.grama_niladari_division,
                property_divisional_secretariat: allFormData.property_divisional_secretariat,
                korale: allFormData.korale,
                pradeshiya_sabha: allFormData.pradeshiya_sabha,
            });
            console.log('[MultiStepForm] Access fields:', {
                access_directions_text: allFormData.access_directions_text,
                access_starting_point_name: allFormData.access_starting_point_name,
                access_distance_km: allFormData.access_distance_km,
                location_map_image_data: allFormData.location_map_image_data,
            });
        }

        // Transform deed data using utility function
        const deedData = transformDeedData(allFormData);

        // Transform comparable properties from frontend format to backend format
        let transformedComparableProperties = undefined;
        if (allFormData.comparable_properties && Array.isArray(allFormData.comparable_properties)) {
            // Filter out items without location_description and transform the rest
            const validComparableProps = allFormData.comparable_properties
                .filter((comp: any) => comp.location_description && comp.location_description.trim() !== '')
                .map((comp: any) => ({
                    property_address: comp.location_description,  // Required field: location_description → property_address
                    property_type: comp.property_type || null,
                    land_extent_acres: comp.extent ? comp.extent / 40 : null,  // Convert perches to acres (40 perches = 1 acre)
                    price_per_perch: comp.rate_per_perch || null,  // rate_per_perch → price_per_perch
                    sale_price: comp.total_value || null,  // total_value → sale_price
                    sale_date: null,
                    sale_year: null,
                    location: comp.location_description || null,  // Keep original for reference
                    description: null,
                    source: null,
                    adjustments: null,
                    distance_km: null
                }));

            // Only set transformedComparableProperties if there are valid items
            transformedComparableProperties = validComparableProps.length > 0 ? validComparableProps : undefined;
        }

        // Fields to filter out - these should only exist in the `deeds` array, not at root level
        const fieldsToRemove = [
            'deed_type', 'deed_number', 'deed_date', 'notary_name', 'notary_location',
            'certificate_number', 'certificate_date', 'certificate_notary_name', 'certificate_notary_district',
        ];

        // Merge validated data with ALL form data to ensure nothing is lost
        const submissionData = {
            ...validatedData,  // Fields validated by Zod schema
            ...allFormData,    // ALL fields including those set via setValue()
            property_identification_type: allFormData.property_identification_type,
            deeds: deedData,   // Transform to array for backend
            has_deed_info: deedData ? 'yes' : 'no',
            comparable_properties: transformedComparableProperties,  // Use transformed data
        };

        // Remove extra deed fields that should only be in the deeds array
        for (const field of fieldsToRemove) {
            delete (submissionData as any)[field];
        }

        if (import.meta.env.DEV) {
            console.log('[MultiStepForm] Final submission data:', submissionData);
        }
        await onSubmit(submissionData, 'complete');
    };

    // Multi-property finish handler
    const handleFinishProperty = async () => {
        if (!isEmbeddedInMultiProperty || !onFinishProperty) return;

        // COMPLETELY clear all validation errors and hide error panel
        setValidationErrors([]);
        setShowErrorPanel(false);
        clearErrors();

        // In embedded mode, DON'T validate anything - just save the property
        // Applicant & additional details are validated by the parent form
        // Property fields are optional - users can save incomplete properties as drafts

        setIsSaving(true);
        try {
            const allFormData = getValues();
            await onFinishProperty(allFormData);
            toast.success('Property marked as completed');
        } catch (error) {
            toast.error('Failed to complete property');
            console.error('Finish error:', error);
        } finally {
            setIsSaving(false);
        }
    };

    const renderStep = () => {
        const stepProps = { register, errors, watch, setValue, getValues };
        // Use watch() instead of getValues() to make form data reactive
        const allValues = watch();

        // Get the actual step ID (originalId for multi-property, id for standalone)
        const currentStepConfig = activeSteps[currentStep - 1];
        const actualStepId = currentStepConfig?.originalId || currentStepConfig?.id || currentStep;

        switch (actualStepId) {
            case 1: return <PropertyPlanStep {...stepProps} />;
            case 2: return <ExtentBoundariesStep {...stepProps} />;
            case 3: return <PropertySearchStep {...stepProps} />;
            case 4: return <PropertyLocationNewStep {...stepProps} />;
            case 5: return (
                <LocalityInformationSection
                    data={{
                        distance_to_major_town_km: allValues.distance_to_major_town_km,
                        major_town_name: allValues.major_town_name,
                        nearby_facilities: allValues.nearby_facilities,
                        has_electricity: allValues.has_electricity,
                        water_supply_type: allValues.water_supply_type,
                        telecommunication_types: allValues.telecommunication_types,
                        internet_types: allValues.internet_types,
                        has_public_transport: allValues.has_public_transport,
                        public_transport_routes: allValues.public_transport_routes,
                        public_transport_frequency: allValues.public_transport_frequency,
                        nearest_bus_stop_distance_km: allValues.nearest_bus_stop_distance_km,
                        nearest_bus_stop_name: allValues.nearest_bus_stop_name,
                        nearest_railway_station: allValues.nearest_railway_station,
                        nearest_railway_distance_km: allValues.nearest_railway_distance_km,
                        area_type: allValues.area_type,
                        development_level: allValues.development_level,
                        predominant_building_type: allValues.predominant_building_type,
                        is_tourist_area: allValues.is_tourist_area,
                        tourist_attractions_nearby: allValues.tourist_attractions_nearby,
                        locality_description_text: allValues.locality_description_text,
                    }}
                    onChange={(updates) => {
                        Object.entries(updates).forEach(([key, value]) => {
                            setValue(key as any, value, { shouldDirty: true, shouldTouch: true, shouldValidate: false });
                        });
                    }}
                    propertyLatitude={allValues.property_latitude}
                    propertyLongitude={allValues.property_longitude}
                    propertyVillage={allValues.property_village}
                    propertyDistrict={allValues.property_district}
                    divisionalSecretariat={allValues.property_divisional_secretariat}
                    pradeshiyaSabha={allValues.pradeshiya_sabha}
                />
            );
            case 6: return <PropertyDescriptionStep {...stepProps} isBareLand={isBareLand} />;
            case 7: return (
                <LegalAspectsSection
                    data={allValues}
                    onChange={(updates) => {
                        Object.entries(updates).forEach(([key, value]) => {
                            setValue(key as any, value, { shouldDirty: true, shouldTouch: true, shouldValidate: false });
                        });
                    }}
                />
            );
            case 8: return (
                <LandValuesSection
                    data={allValues}
                    onChange={(updates) => {
                        Object.entries(updates).forEach(([key, value]) => {
                            setValue(key as any, value, { shouldDirty: true, shouldTouch: true, shouldValidate: false });
                        });
                    }}
                />
            );
            case 9: return <ApplicantPurposeStep {...stepProps} />;
            case 10: return <AdditionalDetailsStep {...stepProps} />;
            case 11: return (
                <ValuationSection
                    data={allValues}
                    onChange={(updates) => {
                        Object.entries(updates).forEach(([key, value]) => {
                            setValue(key as any, value, { shouldDirty: true, shouldTouch: true, shouldValidate: false });
                        });
                    }}
                    buildings={allValues.buildings || []}
                    valuation_type={allValues.valuation_type}
                />
            );
            case 12: return <InvoiceDataStep formMethods={formMethods} isMultiProperty={false} />;
            case 13: return (
                <CertificationSection
                    data={allValues}
                    onChange={(updates) => {
                        Object.entries(updates).forEach(([key, value]) => {
                            setValue(key as any, value, { shouldDirty: true, shouldTouch: true, shouldValidate: false });
                        });
                    }}
                    userProfile={user}
                />
            );
            default: return <PropertyPlanStep {...stepProps} />;
        }
    };

    const currentStepData = activeSteps[currentStep - 1];

    return (
        <>
            <Toaster />
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 py-12">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Phase Tab Navigator */}
                    <PhaseTabBar
                        phases={PHASES}
                        activeSteps={activeSteps}
                        currentStep={currentStep}
                        onPhaseClick={handlePhaseClick}
                        onStepClick={handleStepClick}
                    />

                    {/* Main Form */}
                    <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8 lg:p-12">
                        {/* Step Header */}
                        <div className="text-center mb-8">
                            <div className={`inline-flex p-4 rounded-3xl bg-gradient-to-br ${currentStepData.color} shadow-2xl mb-6 animate-float`}>
                                <currentStepData.icon className="h-12 w-12 text-white" />
                            </div>
                            <h2 className="text-3xl font-bold gradient-text-primary mb-2">
                                {currentStepData.title}
                            </h2>
                            <p className="text-gray-600 text-lg">
                                {currentStepData.subtitle}
                            </p>
                            {currentStepData.category && (
                                <span className="inline-block mt-2 px-3 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-500 tracking-wide">
                                    {currentStepData.category}
                                </span>
                            )}
                        </div>

                        {/* Step Content */}
                        <form onSubmit={handleSubmit(handleFormSubmit)}>
                            {/* Error Summary Panel */}
                            {showErrorPanel && validationErrors.length > 0 && (
                                <ErrorSummaryPanel
                                    errors={validationErrors}
                                    isVisible={showErrorPanel}
                                    onDismiss={() => setShowErrorPanel(false)}
                                    onErrorClick={handleErrorClick}
                                />
                            )}

                            {/* Data Quality Warnings Panel (non-blocking) */}
                            {showWarningsPanel && dataQualityWarnings.length > 0 && currentStep === maxStep && (
                                <div className="mb-6 bg-amber-50 border-2 border-amber-300 rounded-2xl p-6 animate-slideDown">
                                    <div className="flex items-start gap-4">
                                        <div className="flex-shrink-0">
                                            <div className="p-3 bg-amber-100 rounded-full">
                                                <svg className="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                                </svg>
                                            </div>
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center justify-between mb-3">
                                                <h3 className="text-lg font-semibold text-amber-900">
                                                    Data Quality Warnings ({dataQualityWarnings.length})
                                                </h3>
                                                <button
                                                    type="button"
                                                    onClick={() => setShowWarningsPanel(false)}
                                                    className="text-amber-600 hover:text-amber-800 transition-colors"
                                                >
                                                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                    </svg>
                                                </button>
                                            </div>
                                            <p className="text-sm text-amber-800 mb-4">
                                                Your report has some missing or incomplete information. You can still proceed with report generation, but filling these fields will improve the quality and completeness of your report.
                                            </p>
                                            <div className="space-y-2">
                                                {dataQualityWarnings.map((warning, index) => (
                                                    <div
                                                        key={`${warning.field}-${warning.message}-${index}`}
                                                        className={`flex items-start gap-3 p-3 rounded-lg ${warning.severity === 'warning' ? 'bg-amber-100' : 'bg-blue-50'
                                                            }`}
                                                    >
                                                        <div className="flex-shrink-0 mt-0.5">
                                                            {warning.severity === 'warning' ? (
                                                                <svg className="h-5 w-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
                                                                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                                                </svg>
                                                            ) : (
                                                                <svg className="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                                                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                                                </svg>
                                                            )}
                                                        </div>
                                                        <div className="flex-1">
                                                            <p className={`text-sm font-medium ${warning.severity === 'warning' ? 'text-amber-900' : 'text-blue-900'
                                                                }`}>
                                                                {warning.message}
                                                            </p>
                                                        </div>
                                                        <button
                                                            type="button"
                                                            onClick={() => {
                                                                // Navigate to the step containing this field
                                                                const element = document.getElementById(warning.field);
                                                                if (element) {
                                                                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                                                    element.focus();
                                                                }
                                                            }}
                                                            className="text-xs text-amber-700 hover:text-amber-900 font-medium underline"
                                                        >
                                                            Go to field
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="mt-4 pt-4 border-t border-amber-200">
                                                <div className="flex items-center gap-2 text-sm text-amber-800">
                                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                    <span>These are suggestions only. You can proceed with report generation.</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="mb-8">
                                {renderStep()}
                            </div>

                            {/* Navigation Buttons */}
                            <div className="flex justify-between items-center pt-6 border-t border-gray-200/50">
                                <div className="flex gap-3">
                                    {/* Previous button */}
                                    {currentStep > 1 && (
                                        <Button
                                            type="button"
                                            onClick={prevStep}
                                            variant="outline"
                                            className="flex items-center gap-2"
                                        >
                                            <ArrowLeft className="h-4 w-4" />
                                            Previous
                                        </Button>
                                    )}

                                    {/* Back to Dashboard button (multi-property only) */}
                                    {isEmbeddedInMultiProperty && onCancelProperty && (
                                        <Button
                                            type="button"
                                            onClick={onCancelProperty}
                                            variant="outline"
                                            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
                                        >
                                            <ArrowLeft className="h-4 w-4" />
                                            Back to Dashboard
                                        </Button>
                                    )}
                                </div>

                                <div className="flex gap-3">
                                    {/* Save and Continue button - Primary (filled) */}
                                    {!isEmbeddedInMultiProperty && (
                                        <Button
                                            type="button"
                                            onClick={handleSaveAndContinue}
                                            disabled={isSavingAndContinue || isSavingAndExit || isSubmitting}
                                            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-semibold rounded-2xl shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {isSavingAndContinue ? (
                                                <>
                                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                                                    Saving...
                                                </>
                                            ) : (
                                                <>
                                                    <Save className="h-5 w-5 mr-2" />
                                                    Save and Continue
                                                </>
                                            )}
                                        </Button>
                                    )}

                                    {/* Save & Exit button - Secondary (outline) */}
                                    {isEmbeddedInMultiProperty && onSaveProperty ? (
                                        <Button
                                            type="button"
                                            onClick={handleSaveAndExit}
                                            variant="outline"
                                            disabled={isSaving}
                                            className="flex items-center gap-2 border-blue-500 text-blue-600 hover:bg-blue-50"
                                        >
                                            <Save className="h-4 w-4" />
                                            {isSaving ? 'Saving...' : 'Save & Exit'}
                                        </Button>
                                    ) : !isEmbeddedInMultiProperty && (
                                        <Button
                                            type="button"
                                            onClick={handleSaveAndExit}
                                            variant="outline"
                                            disabled={isSavingAndContinue || isSavingAndExit || isSubmitting}
                                            className="flex items-center gap-2 px-6 py-3 border-2 border-blue-500 text-blue-600 hover:bg-blue-50 font-semibold rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {isSavingAndExit ? (
                                                <>
                                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2" />
                                                    Saving...
                                                </>
                                            ) : (
                                                <>
                                                    <Save className="h-5 w-5 mr-2" />
                                                    Save & Exit
                                                </>
                                            )}
                                        </Button>
                                    )}

                                    {/* Next or Complete/Finish button */}
                                    {currentStep < maxStep ? (
                                        <Button
                                            type="button"
                                            onClick={nextStep}
                                            disabled={isSubmitting}
                                            className="flex items-center gap-2 bg-gradient-to-r from-violet-500 to-purple-600"
                                        >
                                            Next
                                            <ArrowRight className="h-4 w-4" />
                                        </Button>
                                    ) : (
                                        <Button
                                            type={isEmbeddedInMultiProperty ? "button" : "submit"}
                                            onClick={isEmbeddedInMultiProperty ? handleFinishProperty : undefined}
                                            disabled={isSubmitting || isSaving}
                                            className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600"
                                        >
                                            <CheckCircle2 className="h-4 w-4" />
                                            {isEmbeddedInMultiProperty
                                                ? (isSaving ? 'Completing...' : 'Finish Property')
                                                : (isSubmitting ? 'Generating...' : 'Generate Report')
                                            }
                                        </Button>
                                    )}
                                </div>
                            </div>
                        </form>
                    </div>

                    {/* Step Info */}
                    <div className="mt-8 text-center">
                        <p className="text-gray-500">
                            {currentStepData?.category && (
                                <span className="mr-1">{currentStepData.category} · </span>
                            )}
                            All information is securely stored and encrypted
                        </p>
                    </div>
                </div>
            </div>

            <NavigationConfirmModal
                isOpen={showNavigationModal}
                onSaveAndExit={handleSaveAndProceed}
                onDiscardAndExit={handleDiscardAndProceed}
                onCancel={() => setShowNavigationModal(false)}
                isSaving={isSaving}
            />

            {/* Loading Overlay for async operations */}
            <LoadingOverlay
                isVisible={isSubmitting || isSaving || loadingMessage !== ''}
                message={loadingMessage || (isSaving ? 'Saving draft...' : 'Processing...')}
            />

        </>
    );
};

export default MultiStepForm;
export type { FormData as ResidentialPropertyFormData };
