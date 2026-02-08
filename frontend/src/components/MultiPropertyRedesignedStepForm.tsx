/**
 * MultiPropertyRedesignedStepForm - Main orchestrator for the new multi-property report flow
 *
 * Flow (5 steps):
 * 1. Applicant & Purpose (common data for all properties)
 * 2. Additional Details (common data for all properties)
 * 3. Property Dashboard (add and manage properties, CRUD operations)
 * 4. Invoice (with draft validation)
 * 5. Final confirmation/generation
 *
 * State Management:
 * - commonData: Applicant, purpose, additional details (shared across all properties)
 * - properties: Array of PropertyInReport with status, order, data
 * - currentStep: 1-5
 */

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast from 'react-hot-toast';
import {
    ArrowRight,
    ArrowLeft,
    User,
    FileText,
    ListChecks,
    LayoutDashboard,
    Receipt,
    CheckCircle2,
    Save
} from 'lucide-react';
import { Button } from './Button';
import { ApplicantAndPurposeStep } from './ApplicantAndPurposeStep';
import { AdditionalDetailsStep } from './AdditionalDetailsStep';
import { PropertyMiniDashboard } from './PropertyMiniDashboard';
import { PropertyInReport } from '../types';
import MultiStepForm from './MultiStepForm';
import { VehicleStepForm } from './VehicleStepForm';
import InvoiceDataStep from './InvoiceDataStep';
import { reportApi, api } from '../services/api';
import SaveProgressModal from './SaveProgressModal';
import { useNavigate } from 'react-router-dom';
import {
    step1ApplicantPurposeSchema,
    step2AdditionalDetailsSchema
} from '../schemas/validationSchemas';

interface MultiPropertyRedesignedStepFormProps {
    onSubmit: (data: any) => Promise<void>;
    onSaveDraft?: (data: any) => Promise<void>;
    isEditMode?: boolean;
    reportId?: number;
    initialData?: any;
}

const steps = [
    {
        id: 1,
        title: 'Applicant & Purpose',
        subtitle: 'Applicant details and valuation purpose',
        icon: User,
        color: 'from-emerald-500 to-green-600',
    },
    {
        id: 2,
        title: 'Additional Details',
        subtitle: 'Submission, inspection, and report info',
        icon: FileText,
        color: 'from-purple-500 to-violet-600',
    },
    {
        id: 3,
        title: 'Property Dashboard',
        subtitle: 'Add and manage properties',
        icon: LayoutDashboard,
        color: 'from-cyan-500 to-blue-600',
    },
    {
        id: 4,
        title: 'Invoice',
        subtitle: 'Professional fees',
        icon: Receipt,
        color: 'from-amber-500 to-orange-600',
    },
    {
        id: 5,
        title: 'Complete',
        subtitle: 'Generate report',
        icon: CheckCircle2,
        color: 'from-green-500 to-emerald-600',
    },
];

// Validation schemas imported from centralized file
// step1Schema = step1ApplicantPurposeSchema (with ID validation and valuation_purpose refinements)
// step2Schema = step2AdditionalDetailsSchema (with required inspection_date)
const step1Schema = step1ApplicantPurposeSchema;
const step2Schema = step2AdditionalDetailsSchema;

// Combined schema for form (all fields optional for form initialization)
const multiPropertyCommonSchema = z.object({
    // Step 1: Applicant & Purpose
    applicant_title: z.string().optional(),
    applicant_full_name: z.string().optional(),
    applicant_id_type: z.string().optional(),
    applicant_id_number: z.string().optional(),
    applicant_address_line1: z.string().optional(),
    applicant_address_line2: z.string().optional(),
    applicant_district: z.string().optional(),
    applicant_province: z.string().optional(),
    applicant_country: z.string().optional(),
    applicant_contact_number: z.string().nullable().optional(), // Optional contact number
    valuation_type: z.string().optional(),
    valuation_purpose: z.string().optional(),
    property_type_valued: z.string().optional(),
    has_additional_owner: z.string().optional(),
    additional_owner_names: z.string().nullable().optional(),

    // Step 2: Additional Details
    request_type: z.enum(['client_request', 'organization_request']).optional(),
    submission_organization: z.string().optional(),
    submission_address: z.string().optional(),
    submission_recipient_position: z.string().optional(),
    inspection_date: z.string().optional(),
    has_special_note: z.string().optional(),
    special_note_text: z.string().optional(),
    report_reference: z.string().optional(),
    report_date: z.string().optional(),
});

export const MultiPropertyRedesignedStepForm: React.FC<MultiPropertyRedesignedStepFormProps> = ({
    onSubmit,
    onSaveDraft,
    isEditMode = false,
    reportId,
    initialData
}) => {
    console.log('[MultiPropertyRedesignedStepForm] Component rendered with props:', {
        isEditMode,
        reportId,
        hasInitialData: !!initialData,
        initialData: initialData
    });

    const [currentStep, setCurrentStep] = useState(1); // Always start at step 1 to review saved data
    const [properties, setProperties] = useState<PropertyInReport[]>([]);
    const [editingPropertyId, setEditingPropertyId] = useState<string | number | null>(null);
    const [showDraftWarning, setShowDraftWarning] = useState(false);
    const [draftWarningData, setDraftWarningData] = useState<{ draftCount: number; completedCount: number } | null>(null);

    // Save modal state
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);

    const navigate = useNavigate();

    // Form for common data (Steps 1 & 2)
    const formMethods = useForm({
        resolver: zodResolver(multiPropertyCommonSchema),
        defaultValues: initialData || {},
        mode: 'onChange',
    });

    const {
        register,
        handleSubmit,
        watch,
        setValue,
        getValues,
        reset,
        formState: { errors },
        trigger,
    } = formMethods;

    // Load initial data for edit mode
    useEffect(() => {
        console.log('[MultiPropertyRedesignedStepForm] useEffect triggered!', {
            hasInitialData: !!initialData,
            isEditMode,
            initialDataKeys: initialData ? Object.keys(initialData) : []
        });

        if (!initialData) {
            console.log('[MultiPropertyRedesignedStepForm] ❌ No initialData, skipping load');
            return;
        }

        if (!isEditMode) {
            console.log('[MultiPropertyRedesignedStepForm] ❌ Not in edit mode, skipping load');
            return;
        }

        console.log('[MultiPropertyRedesignedStepForm] ✅ Loading initial data for edit mode:', initialData);

        // Reset form with common data (Steps 1 & 2) - ALL FIELDS
        const formData = {
            // Step 1: Applicant & Purpose
            applicant_title: initialData.applicant_title || '',
            applicant_full_name: initialData.applicant_full_name || '',
            applicant_id_type: initialData.applicant_id_type || '',
            applicant_id_number: initialData.applicant_id_number || '',
            applicant_address_line1: initialData.applicant_address_line1 || '',
            applicant_address_line2: initialData.applicant_address_line2 || '',
            applicant_district: initialData.applicant_district || '',
            applicant_province: initialData.applicant_province || '',
            applicant_country: initialData.applicant_country || 'Sri Lanka',
            valuation_type: initialData.valuation_type || '',
            valuation_purpose: initialData.valuation_purpose || '',
            property_type_valued: initialData.property_type_valued || '',
            has_additional_owner: initialData.has_additional_owner || '',
            additional_owner_names: initialData.additional_owner_names || '',

            // Step 2: Additional Details
            submission_organization: initialData.submission_organization || '',
            submission_address: initialData.submission_address || '',
            submission_recipient_position: initialData.submission_recipient_position || '',
            inspection_date: initialData.inspection_date || '',
            has_special_note: initialData.has_special_note || '',
            special_note_text: initialData.special_note_text || '',
            report_reference: initialData.report_reference || '',
            report_date: initialData.report_date || '',

            // Invoice data (Step 4)
            invoice_data: initialData.invoice_data || null,
        };
        console.log('[MultiPropertyRedesignedStepForm] Resetting form with data:', formData);
        reset(formData);

        // Reconstruct properties array from initialData.properties
        if (initialData.properties && Array.isArray(initialData.properties)) {
            console.log('[MultiPropertyRedesignedStepForm] Found properties array:', initialData.properties);

            const reconstructedProperties = initialData.properties.map((prop: any, index: number) => ({
                id: prop.id || `property-${Date.now()}-${index}`,
                type: prop.property_type || 'residential',
                order: prop.property_order !== undefined ? prop.property_order : index,
                status: prop.status || 'draft',
                data: prop
            }));

            console.log('[MultiPropertyRedesignedStepForm] ✅ Reconstructed properties:', reconstructedProperties);
            setProperties(reconstructedProperties);
        } else {
            console.log('[MultiPropertyRedesignedStepForm] ⚠️ No properties found in initialData');
        }

        console.log('[MultiPropertyRedesignedStepForm] ✅ Finished loading initial data');
    }, [initialData, isEditMode, reset]);

    // Keyboard shortcut for save (Ctrl+S / Cmd+S)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ctrl+S (Windows/Linux) or Cmd+S (Mac)
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault(); // Prevent browser's default save dialog
                if (!isSaving && onSaveDraft) {
                    handleSaveDraft();
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isSaving, onSaveDraft]);

    // Property CRUD handlers
    const handleEditProperty = (propertyId: string | number) => {
        setEditingPropertyId(propertyId);
    };

    const handleDeleteProperty = (propertyId: string | number) => {
        if (properties.length <= 1) {
            toast.error('Cannot delete: Minimum 1 property required');
            return;
        }

        const confirmed = window.confirm('Are you sure you want to delete this property?');
        if (confirmed) {
            setProperties(prev => prev.filter(p => p.id !== propertyId));
            toast.success('Property deleted');
        }
    };

    const handleMoveUp = (propertyId: string | number) => {
        setProperties(prev => {
            const index = prev.findIndex(p => p.id === propertyId);
            if (index <= 0) return prev;

            const newProperties = [...prev];
            [newProperties[index - 1], newProperties[index]] = [newProperties[index], newProperties[index - 1]];

            // Update order fields
            return newProperties.map((p, i) => ({ ...p, order: i }));
        });
        toast.success('Property moved up');
    };

    const handleMoveDown = (propertyId: string | number) => {
        setProperties(prev => {
            const index = prev.findIndex(p => p.id === propertyId);
            if (index < 0 || index >= prev.length - 1) return prev;

            const newProperties = [...prev];
            [newProperties[index], newProperties[index + 1]] = [newProperties[index + 1], newProperties[index]];

            // Update order fields
            return newProperties.map((p, i) => ({ ...p, order: i }));
        });
        toast.success('Property moved down');
    };

    const handleDuplicateProperty = (propertyId: string | number) => {
        const property = properties.find(p => p.id === propertyId);
        if (!property) return;

        // Create duplicate data WITHOUT the database ID to prevent overwriting original
        const { id, ...dataWithoutId } = property.data || {};

        const newProperty: PropertyInReport = {
            id: `${property.type}-${Date.now()}`,
            type: property.type,
            order: properties.length,
            status: 'draft', // Duplicates start as draft
            data: { ...dataWithoutId }, // Copy data WITHOUT database ID
        };

        setProperties(prev => [...prev, newProperty]);
        console.log('[handleDuplicateProperty] Created duplicate without DB ID:', newProperty);
        toast.success('Property duplicated');
    };

    const handleAddPropertyBatch = (type: 'residential' | 'bare_land' | 'vehicle', count: number) => {
        const newProperties: PropertyInReport[] = [];

        for (let i = 0; i < count; i++) {
            newProperties.push({
                id: `${type}-${Date.now()}-${i}`,
                type: type,
                order: properties.length + i,
                status: 'draft',
                data: {},
            });
        }

        setProperties(prev => [...prev, ...newProperties]);

        // Type-specific success message
        const typeLabels: Record<string, string> = {
            residential: 'Residential/Commercial',
            bare_land: 'Bare Land',
            vehicle: 'Vehicle'
        };
        const itemName = type === 'vehicle' ? 'vehicle' : 'property';
        toast.success(`Added ${count} ${typeLabels[type]} ${count === 1 ? itemName : itemName + 's'}`);
    };

    // Property editing handlers
    const handlePropertySave = async (propertyId: string | number, data: any) => {
        setProperties(prev =>
            prev.map(p => {
                if (p.id === propertyId) {
                    // IMPORTANT: Preserve the database ID from the original property data
                    // The form data doesn't include 'id', so we need to merge it back in
                    const preservedId = p.data?.id;
                    const updatedData = preservedId ? { ...data, id: preservedId } : data;

                    console.log('[handlePropertySave] Preserving property ID:', preservedId);
                    return { ...p, data: updatedData, status: 'draft' };
                }
                return p;
            })
        );
        setEditingPropertyId(null);
        toast.success('Property saved as draft');
    };

    const handlePropertyFinish = async (propertyId: string | number, data: any) => {
        // Update local state first
        setProperties(prev =>
            prev.map(p => {
                if (p.id === propertyId) {
                    // IMPORTANT: Preserve the database ID from the original property data
                    // The form data doesn't include 'id', so we need to merge it back in
                    const preservedId = p.data?.id;
                    const updatedData = preservedId ? { ...data, id: preservedId } : data;

                    console.log('[handlePropertyFinish] Preserving property ID:', preservedId);
                    return { ...p, data: updatedData, status: 'completed' };
                }
                return p;
            })
        );

        // ✅ NEW: Save status to database immediately (only for properties with DB IDs)
        try {
            if (typeof propertyId === 'number') {
                // Property has DB ID - update status via API
                await api.patch(`/api/properties/${propertyId}/status`, { status: 'completed' });
                console.log(`[handlePropertyFinish] Status updated in database for property ${propertyId}`);
            } else {
                // New property with temp ID - local state updated, will be saved on next draft save
                console.log('[handlePropertyFinish] Property has temp ID, status updated in local state only');
                console.log('[handlePropertyFinish] Click "Save Draft" to persist this property to the database');
            }
        } catch (error) {
            console.error('[handlePropertyFinish] Failed to update status:', error);
            toast.error('Failed to save property status');
            return;
        }

        setEditingPropertyId(null);
        toast.success('Property marked as completed');
    };

    // Navigation handlers
    const handleNext = async () => {
        // Clear previous errors
        formMethods.clearErrors();

        // Validate current step
        if (currentStep === 1) {
            // Validate Step 1 fields only
            const formData = getValues();
            try {
                step1Schema.parse(formData);
            } catch (error) {
                if (error instanceof z.ZodError) {
                    // Set form errors
                    error.errors.forEach((err) => {
                        const path = err.path[0] as string;
                        formMethods.setError(path as any, {
                            type: 'manual',
                            message: err.message,
                        });
                    });
                    toast.error('Please fill in all required fields');
                    return;
                }
            }
        } else if (currentStep === 2) {
            // Validate Step 2 fields only
            const formData = getValues();
            try {
                step2Schema.parse(formData);
            } catch (error) {
                if (error instanceof z.ZodError) {
                    // Set form errors
                    error.errors.forEach((err) => {
                        const path = err.path[0] as string;
                        formMethods.setError(path as any, {
                            type: 'manual',
                            message: err.message,
                        });
                    });
                    toast.error('Please fill in all required fields');
                    return;
                }
            }
        }

        if (currentStep === 3) {
            // Validate Property Dashboard - ensure at least 1 property exists
            if (properties.length === 0) {
                toast.error('Please add at least one property');
                return;
            }

            // Draft warning logic
            const completedCount = properties.filter(p => p.status === 'completed').length;
            const draftCount = properties.filter(p => p.status === 'draft').length;

            if (completedCount === 0) {
                toast.error('You must complete at least one property before generating the report.');
                return;
            }

            if (draftCount > 0) {
                setDraftWarningData({ draftCount, completedCount });
                setShowDraftWarning(true);
                return; // Stop navigation, wait for user confirmation
            }
        }

        setCurrentStep(prev => Math.min(prev + 1, 5));
    };

    const handlePrevious = () => {
        setCurrentStep(prev => Math.max(prev - 1, 1));
    };

    const handleDraftWarningConfirm = () => {
        setShowDraftWarning(false);
        setDraftWarningData(null);
        setCurrentStep(prev => Math.min(prev + 1, 5)); // Proceed to next step
    };

    const handleDraftWarningCancel = () => {
        setShowDraftWarning(false);
        setDraftWarningData(null);
    };

    // Final submission
    const handleFinalSubmit = async () => {
        const commonData = getValues();
        const completedProperties = properties.filter(p => p.status === 'completed');

        const reportData = {
            ...commonData,
            is_multi_property: true,
            property_count: completedProperties.length,
            properties: completedProperties.map((p, index) => ({
                ...p.data,
                property_type: p.type,
                status: p.status,
                property_order: index,
            })),
        };

        try {
            await onSubmit(reportData);
            toast.success('Multi-property report created successfully!');
        } catch (error) {
            toast.error('Failed to create report');
            console.error(error);
        }
    };

    // Draft saving with modal
    const handleSaveDraft = async () => {
        if (!onSaveDraft) return;

        // Open modal immediately and start saving
        setShowSaveModal(true);
        setIsSaving(true);
        setSaveError(null);

        console.log('[handleSaveDraft] Starting draft save...');
        console.log('[handleSaveDraft] Current properties state:', properties);

        try {
            const formData = getValues();
            console.log('[handleSaveDraft] Form data:', formData);

            // Fields to filter out - these should only exist in the `deeds` array, not at root level
            const fieldsToRemove = [
                'deed_type', 'deed_number', 'deed_date', 'notary_name', 'notary_location',
                'certificate_number', 'certificate_date', 'certificate_notary_name', 'certificate_notary_district',
            ];

            // Helper to filter extra deed fields from an object
            const filterDeedFields = (obj: any) => {
                const filtered = { ...obj };
                for (const field of fieldsToRemove) {
                    delete filtered[field];
                }
                return filtered;
            };

            // Serialize properties data for API, filtering out extra deed fields from each property
            const propertiesData = properties.map(prop => filterDeedFields({
                ...prop.data,
                property_order: prop.order,
                status: prop.status,
                property_type: prop.type,
            }));
            console.log('[handleSaveDraft] Serialized properties:', propertiesData);

            // Filter extra deed fields from form data as well
            const filteredFormData = filterDeedFields(formData);

            const completeData = {
                ...filteredFormData,
                is_multi_property: true,
                property_count: properties.length,
                properties: propertiesData,
                property_metadata: properties.map(p => ({
                    id: p.id,
                    type: p.type,
                    order: p.order,
                    status: p.status
                }))
            };
            console.log('[handleSaveDraft] Complete data being sent:', completeData);

            await onSaveDraft(completeData);
            console.log('[handleSaveDraft] ✅ Draft saved successfully');

            // ✅ Reload report to sync property IDs with database
            if (reportId) {
                try {
                    const updatedReport = await reportApi.getReport(reportId);

                    // Update properties state with database IDs
                    if (updatedReport.properties && updatedReport.properties.length > 0) {
                        const updatedProperties = updatedReport.properties.map((dbProp: any, index: number) => ({
                            id: dbProp.id,  // ✅ Use integer DB ID from database
                            type: dbProp.property_type || 'residential',
                            order: dbProp.property_order !== undefined ? dbProp.property_order : index + 1,
                            status: dbProp.status || 'draft',
                            data: dbProp  // Full property data including DB ID
                        }));

                        setProperties(updatedProperties);
                        console.log('[handleSaveDraft] Properties synced with database:', updatedProperties);
                    }

                    // ✅ Update form fields with the saved data from database
                    const { properties: _, ...reportFields } = updatedReport;
                    reset(reportFields, { keepDefaultValues: false });
                    console.log('[handleSaveDraft] Form fields updated with saved data');
                } catch (error) {
                    console.error('[handleSaveDraft] Failed to reload report:', error);
                    // Don't show error to user - save was successful
                }
            }

            // Success: Show toast and enable modal buttons
            setIsSaving(false);
            toast.success('Draft saved successfully');
        } catch (error: any) {
            console.error('[handleSaveDraft] ❌ Draft save error:', error);
            // Error: Close modal and show error toast
            setShowSaveModal(false);
            setIsSaving(false);
            setSaveError(error.message || 'Unknown error');
            toast.error('Failed to save draft');
        }
    };

    // Modal handlers
    const handleSaveModalContinue = () => {
        setShowSaveModal(false);
        // Stay on current page - user continues editing
    };

    const handleSaveModalExit = () => {
        setShowSaveModal(false);
        navigate('/dashboard');
    };

    // If editing a property, show the property edit form
    if (editingPropertyId) {
        const property = properties.find(p => p.id === editingPropertyId);
        if (!property) {
            setEditingPropertyId(null);
            return null;
        }

        const commonData = getValues();

        // Handle vehicle type separately
        if (property.type === 'vehicle') {
            return (
                <VehicleStepForm
                    mode={property.data && Object.keys(property.data).length > 0 ? 'edit' : 'create'}
                    initialData={property.data}
                    isMultiPropertyContext={true}
                    onSaveProperty={(data) => handlePropertySave(property.id, data)}
                    onFinishProperty={(data) => handlePropertyFinish(property.id, data)}
                    onCancel={() => setEditingPropertyId(null)}
                />
            );
        }

        // Determine report type based on property type (for residential/bare_land)
        const reportType = property.type === 'residential' ? 'residential_property' : 'bare_land';

        return (
            <MultiStepForm
                // Standard props
                reportType={reportType}
                isEditMode={property.data && Object.keys(property.data).length > 0}
                initialData={property.data}

                // Multi-property specific props
                isEmbeddedInMultiProperty={true}
                commonData={commonData}
                onSaveProperty={(data) => handlePropertySave(property.id, data)}
                onFinishProperty={(data) => handlePropertyFinish(property.id, data)}
                onCancelProperty={() => setEditingPropertyId(null)}
                hideCertification={false}  // Keep per-property certification

                // Required but not used in embedded mode
                onSubmit={async () => { }}
                user={undefined}
            />
        );
    }

    // Render current step
    const renderStepContent = () => {
        switch (currentStep) {
            case 1:
                return <ApplicantAndPurposeStep register={register} errors={errors} watch={watch} setValue={setValue} />;
            case 2:
                return <AdditionalDetailsStep register={register} errors={errors} watch={watch} setValue={setValue} />;
            case 3:
                return (
                    <PropertyMiniDashboard
                        properties={properties}
                        onEdit={handleEditProperty}
                        onDelete={handleDeleteProperty}
                        onMoveUp={handleMoveUp}
                        onMoveDown={handleMoveDown}
                        onDuplicate={handleDuplicateProperty}
                        onAddBatch={handleAddPropertyBatch}
                    />
                );
            case 4:
                return <InvoiceDataStep formMethods={formMethods as any} properties={properties} isMultiProperty={true} />;
            case 5:
                return (
                    <div className="text-center space-y-6">
                        <CheckCircle2 className="h-24 w-24 text-green-600 mx-auto" />
                        <h2 className="text-3xl font-bold text-gray-900">Ready to Generate Report</h2>
                        <p className="text-gray-600 max-w-2xl mx-auto">
                            Your multi-property report is ready. Click "Generate Report" below to create the final DOCX document.
                        </p>
                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 max-w-2xl mx-auto">
                            <h4 className="font-semibold text-blue-900 mb-2">Report Summary</h4>
                            <ul className="text-sm text-blue-800 space-y-1 text-left">
                                <li>• Total Items: {properties.filter(p => p.status === 'completed').length}</li>
                                <li>• Residential/Commercial: {properties.filter(p => p.type === 'residential' && p.status === 'completed').length}</li>
                                <li>• Bare Land: {properties.filter(p => p.type === 'bare_land' && p.status === 'completed').length}</li>
                                <li>• Vehicles: {properties.filter(p => p.type === 'vehicle' && p.status === 'completed').length}</li>
                                <li>• Draft items will be excluded from the report</li>
                            </ul>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8 px-4">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">Multi-Property Valuation Report</h1>
                    <p className="text-gray-600 mt-1">
                        Step {currentStep} of 5: {steps[currentStep - 1].title}
                    </p>
                </div>

                {/* Progress Bar */}
                <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <div className="flex items-center justify-between">
                        {steps.map((step, index) => {
                            const StepIcon = step.icon;
                            const isActive = currentStep === step.id;
                            const isCompleted = currentStep > step.id;

                            return (
                                <div key={step.id} className="flex items-center flex-1">
                                    <div className="flex flex-col items-center flex-1">
                                        <div
                                            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                                                isCompleted
                                                    ? 'bg-green-500 text-white'
                                                    : isActive
                                                        ? `bg-gradient-to-r ${step.color} text-white`
                                                        : 'bg-gray-200 text-gray-500'
                                            }`}
                                        >
                                            <StepIcon className="h-6 w-6" />
                                        </div>
                                        <span className={`text-xs mt-2 text-center ${isActive ? 'font-bold' : ''}`}>
                                            {step.title}
                                        </span>
                                    </div>
                                    {index < steps.length - 1 && (
                                        <div
                                            className={`h-1 flex-1 mx-2 ${
                                                currentStep > step.id ? 'bg-green-500' : 'bg-gray-300'
                                            }`}
                                        />
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Content */}
                <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
                    {renderStepContent()}
                </div>

                {/* Navigation */}
                <div className="bg-white rounded-2xl shadow-lg p-6">
                    <div className="flex justify-between items-center">
                        {/* Left side: Previous button */}
                        <div>
                            {currentStep > 1 && (
                                <Button onClick={handlePrevious} variant="outline" className="flex items-center gap-2">
                                    <ArrowLeft className="h-4 w-4" />
                                    Previous
                                </Button>
                            )}
                        </div>

                        {/* Right side: Save Draft + Next/Generate */}
                        <div className="flex gap-3">
                            {/* Save Draft button - appears on ALL steps */}
                            {onSaveDraft && (
                                <Button
                                    onClick={handleSaveDraft}
                                    variant="outline"
                                    disabled={isSaving}
                                    className="flex items-center gap-2 border-blue-500 text-blue-600 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSaving ? (
                                        <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save className="h-4 w-4" />
                                            Save Draft
                                        </>
                                    )}
                                </Button>
                            )}

                            {/* Next or Generate Report button */}
                            {currentStep < 5 ? (
                                <Button onClick={handleNext} className="flex items-center gap-2">
                                    Next
                                    <ArrowRight className="h-4 w-4" />
                                </Button>
                            ) : (
                                <Button
                                    onClick={handleFinalSubmit}
                                    className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600"
                                >
                                    <CheckCircle2 className="h-4 w-4" />
                                    Generate Report
                                </Button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Modern Confirmation Dialog for Draft Properties */}
            {showDraftWarning && draftWarningData && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    {/* Backdrop */}
                    <div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={handleDraftWarningCancel}
                    />

                    {/* Dialog */}
                    <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6 border border-slate-700 animate-in fade-in zoom-in duration-200">
                        {/* Icon */}
                        <div className="flex justify-center mb-4">
                            <div className="bg-amber-500/20 p-3 rounded-full">
                                <svg className="w-8 h-8 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="text-center mb-6">
                            <h3 className="text-xl font-bold text-white mb-3">
                                Draft Properties Detected
                            </h3>
                            <div className="space-y-2">
                                <p className="text-slate-300 text-sm leading-relaxed">
                                    {draftWarningData.draftCount} {draftWarningData.draftCount === 1 ? 'property is' : 'properties are'} in draft status.
                                    Only <span className="font-semibold text-green-400">{draftWarningData.completedCount}</span> completed {draftWarningData.completedCount === 1 ? 'property' : 'properties'} will be included in the report.
                                </p>
                                <p className="text-slate-400 text-sm font-medium">
                                    Do you want to continue?
                                </p>
                            </div>
                        </div>

                        {/* Buttons */}
                        <div className="flex gap-3">
                            <button
                                onClick={handleDraftWarningCancel}
                                className="flex-1 px-4 py-2.5 rounded-lg font-medium text-slate-300 bg-slate-700 hover:bg-slate-600 transition-colors duration-200 border border-slate-600"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDraftWarningConfirm}
                                className="flex-1 px-4 py-2.5 rounded-lg font-medium text-white bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 transition-all duration-200 shadow-lg shadow-green-500/30"
                            >
                                Continue
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Save Progress Modal */}
            <SaveProgressModal
                isOpen={showSaveModal}
                isSaving={isSaving}
                saveError={saveError}
                onContinue={handleSaveModalContinue}
                onExit={handleSaveModalExit}
            />
        </div>
    );
};
