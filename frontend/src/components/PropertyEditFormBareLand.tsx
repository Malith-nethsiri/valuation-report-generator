/**
 * PropertyEditFormBareLand - 10-step form for editing bare land properties within multi-property reports
 *
 * This component is nearly identical to PropertyEditFormResidential but with isBareLand={true} behavior
 * for the PropertyDescriptionStep, which hides building-related fields and shows property photos only.
 *
 * Key Features:
 * - Only 10 steps (excludes Applicant & Purpose, Additional Details)
 * - "Save & Exit" button on all steps (saves as draft)
 * - "Finish" button on Step 10 (validates and marks as completed)
 * - Receives commonData (applicant, purpose, additional details) as context
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import {
    ArrowRight,
    ArrowLeft,
    CheckCircle2,
    Home,
    MapPin,
    Building,
    Compass,
    ClipboardList,
    Gavel,
    TrendingUp,
    Scale,
    Award,
    Save,
    LogOut
} from 'lucide-react';
import { Button } from './Button';
import { PropertyDescriptionStep } from './PropertyDescriptionStep';
import LocalityInformationSection from './LocalityInformationSection';
import LegalAspectsSection from './LegalAspectsSection';
import LandValuesSection from './LandValuesSection';
import ValuationSection from './ValuationSection';
import CertificationSection from './CertificationSection';

interface PropertyEditFormBareLandProps {
    propertyData?: any;
    commonData: {
        applicant_title?: string;
        applicant_full_name?: string;
        applicant_id_type?: string;
        applicant_id_number?: string;
        applicant_address_line1?: string;
        applicant_address_line2?: string;
        applicant_district?: string;
        applicant_province?: string;
        applicant_country?: string;
        valuation_type?: string;
        valuation_purpose?: string;
        property_type_valued?: string;
        property_ownership?: string;
        has_additional_owner?: string;
        additional_owner_names?: string;
        submission_recipient_position?: string;
        submission_organization?: string;
        submission_address?: string;
        inspection_date?: string;
        has_special_note?: string;
        special_note_text?: string;
        report_reference?: string;
        report_date?: string;
    };
    onSave: (data: any) => Promise<void>;
    onFinish: (data: any) => Promise<void>;
    onCancel?: () => void;
}

const steps = [
    {
        id: 1,
        title: 'Property & Plan',
        subtitle: 'Property and plan information',
        icon: Home,
        color: 'from-blue-500 to-indigo-600',
    },
    {
        id: 2,
        title: 'Extent & Boundaries',
        subtitle: 'Land extent and boundaries',
        icon: Compass,
        color: 'from-green-500 to-emerald-600',
    },
    {
        id: 3,
        title: 'Property Search',
        subtitle: 'Find property on map',
        icon: MapPin,
        color: 'from-orange-500 to-red-600',
    },
    {
        id: 4,
        title: 'Property Details',
        subtitle: 'Location and administrative info',
        icon: Building,
        color: 'from-cyan-500 to-blue-600',
    },
    {
        id: 5,
        title: 'Locality Information',
        subtitle: 'Nearby facilities and infrastructure',
        icon: MapPin,
        color: 'from-pink-500 to-rose-600',
    },
    {
        id: 6,
        title: 'Property Description',
        subtitle: 'Land photos (5 max)',
        icon: ClipboardList,
        color: 'from-amber-500 to-orange-600',
    },
    {
        id: 7,
        title: 'Legal Aspects',
        subtitle: 'Ownership and legal status',
        icon: Gavel,
        color: 'from-purple-500 to-violet-600',
    },
    {
        id: 8,
        title: 'Land Values',
        subtitle: 'Comparable properties',
        icon: TrendingUp,
        color: 'from-green-500 to-teal-600',
    },
    {
        id: 9,
        title: 'Valuation',
        subtitle: 'Property valuation breakdown',
        icon: Scale,
        color: 'from-indigo-500 to-blue-600',
    },
    {
        id: 10,
        title: 'Certification',
        subtitle: 'Property certification',
        icon: Award,
        color: 'from-amber-500 to-yellow-600',
    },
];

export const PropertyEditFormBareLand: React.FC<PropertyEditFormBareLandProps> = ({
    propertyData,
    commonData,
    onSave,
    onFinish,
    onCancel
}) => {
    const [currentStep, setCurrentStep] = useState(1);
    const [isSaving, setIsSaving] = useState(false);

    const {
        register,
        handleSubmit,
        watch,
        setValue,
        getValues,
        formState: { errors },
        trigger,
        clearErrors,
    } = useForm({
        defaultValues: propertyData || {},
        mode: 'onChange',
    });

    const handleSaveAndExit = async () => {
        setIsSaving(true);
        try {
            const data = getValues();
            await onSave(data);
            toast.success('Property saved as draft');
        } catch (error) {
            toast.error('Failed to save property');
            console.error('Save error:', error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleFinish = async () => {
        const isValid = await trigger();

        if (!isValid) {
            toast.error('Please fill in all required fields before completing this property');
            return;
        }

        setIsSaving(true);
        try {
            const data = getValues();
            await onFinish(data);
            toast.success('Property marked as completed');
        } catch (error) {
            toast.error('Failed to complete property');
            console.error('Finish error:', error);
        } finally {
            setIsSaving(false);
        }
    };

    const handleNext = async () => {
        // Clear all previous errors before validating current step
        clearErrors();

        // Define fields to validate for each step
        const stepFields: Record<number, string[]> = {
            1: ['property_lot_description', 'plan_number', 'deed_number'],
            2: ['land_extent_formatted', 'boundaries'],
            3: [], // Property search - no required fields
            4: ['property_village', 'property_district', 'property_province'],
            5: [], // Locality - handled by component
            6: [], // Property description (bare land) - handled by component
            7: [], // Legal aspects - handled by component
            8: [], // Land values - handled by component
            9: [], // Valuation - handled by component
            10: [], // Certification - handled by component
        };

        // Validate only fields for the current step
        const fieldsToValidate = stepFields[currentStep] || [];

        let isValid = true;
        if (fieldsToValidate.length > 0) {
            isValid = await trigger(fieldsToValidate as any);
        }

        if (isValid && currentStep < 10) {
            setCurrentStep(currentStep + 1);
        }
    };

    const handlePrevious = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
        }
    };

    const stepProps = {
        register,
        errors,
        watch,
        setValue,
        getValues,
    };

    const renderStepContent = () => {
        switch (currentStep) {
            case 1: // Property & Plan
                return (
                    <div className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">Property Lot Description</label>
                            <input
                                type="text"
                                placeholder="e.g., Lot 1, 2, 3"
                                className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl px-4"
                                {...register('property_lot_description')}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">Plan Number</label>
                            <input
                                type="text"
                                placeholder="e.g., 2011/5/45"
                                className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl px-4"
                                {...register('plan_number')}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">Deed Number</label>
                            <input
                                type="text"
                                placeholder="Deed number"
                                className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl px-4"
                                {...register('deed_number')}
                            />
                        </div>
                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mt-4">
                            <p className="text-sm text-blue-800">
                                <strong>Bare Land Property:</strong> This form is optimized for bare land properties.
                                No building details will be collected. Maximum 5 property photos allowed.
                            </p>
                        </div>
                    </div>
                );

            case 2: // Extent & Boundaries
                return (
                    <div className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">Land Extent (Formatted)</label>
                            <input
                                type="text"
                                placeholder="e.g., 10 perches or 1 Acre, 2 Roods, 20 Perches"
                                className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl px-4"
                                {...register('land_extent_formatted')}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">Boundaries</label>
                            <textarea
                                rows={4}
                                placeholder="Describe property boundaries"
                                className="w-full p-4 bg-white/50 border border-gray-200/50 rounded-2xl resize-none"
                                {...register('boundaries')}
                            />
                        </div>
                    </div>
                );

            case 3: // Property Search
                return (
                    <div className="space-y-6">
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                            <p className="text-sm text-amber-800">
                                Property search and map integration would go here.
                                For bare land properties, this helps locate the plot on Google Maps.
                            </p>
                        </div>
                    </div>
                );

            case 4: // Property Details (Location)
                return (
                    <div className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">Village *</label>
                            <input
                                type="text"
                                placeholder="Property village"
                                className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl px-4"
                                {...register('property_village', { required: 'Village is required' })}
                            />
                            {errors.property_village && (
                                <p className="text-red-500 text-sm">{errors.property_village.message}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">District *</label>
                            <input
                                type="text"
                                placeholder="Property district"
                                className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl px-4"
                                {...register('property_district', { required: 'District is required' })}
                            />
                            {errors.property_district && (
                                <p className="text-red-500 text-sm">{errors.property_district.message}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <label className="text-gray-700 font-medium">Province</label>
                            <input
                                type="text"
                                placeholder="Property province"
                                className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl px-4"
                                {...register('property_province')}
                            />
                        </div>
                    </div>
                );

            case 5: // Locality Information
                return <LocalityInformationSection {...stepProps} />;

            case 6: // Property Description (Bare Land - no buildings, 5 photos max)
                return <PropertyDescriptionStep {...stepProps} isBareLand={true} />;

            case 7: // Legal Aspects
                return <LegalAspectsSection {...stepProps} />;

            case 8: // Land Values
                return <LandValuesSection {...stepProps} />;

            case 9: // Valuation
                return <ValuationSection {...stepProps} />;

            case 10: // Certification (per property)
                return <CertificationSection {...stepProps} />;

            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-green-50 py-8 px-4">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <h1 className="text-2xl font-bold text-gray-900">Edit Bare Land Property</h1>
                    <p className="text-gray-600 mt-1">
                        Step {currentStep} of 10: {steps[currentStep - 1].title}
                    </p>
                </div>

                {/* Progress Steps */}
                <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
                    <div className="flex items-center justify-between overflow-x-auto pb-2">
                        {steps.map((step, index) => {
                            const StepIcon = step.icon;
                            const isActive = currentStep === step.id;
                            const isCompleted = currentStep > step.id;

                            return (
                                <div key={step.id} className="flex items-center">
                                    <div
                                        className={`flex flex-col items-center cursor-pointer transition-all duration-200 ${
                                            isActive ? 'scale-110' : 'scale-100'
                                        }`}
                                        onClick={() => setCurrentStep(step.id)}
                                    >
                                        <div
                                            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-200 ${
                                                isCompleted
                                                    ? 'bg-green-500 text-white'
                                                    : isActive
                                                        ? `bg-gradient-to-r ${step.color} text-white`
                                                        : 'bg-gray-200 text-gray-500'
                                            }`}
                                        >
                                            {isCompleted ? (
                                                <CheckCircle2 className="h-6 w-6" />
                                            ) : (
                                                <StepIcon className="h-6 w-6" />
                                            )}
                                        </div>
                                        <span
                                            className={`text-xs mt-2 text-center max-w-[80px] ${
                                                isActive ? 'font-bold text-gray-900' : 'text-gray-600'
                                            }`}
                                        >
                                            {step.title}
                                        </span>
                                    </div>
                                    {index < steps.length - 1 && (
                                        <div
                                            className={`h-1 w-8 mx-2 transition-all duration-200 ${
                                                currentStep > step.id ? 'bg-green-500' : 'bg-gray-300'
                                            }`}
                                        />
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Form Content */}
                <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
                    {renderStepContent()}
                </div>

                {/* Navigation Buttons */}
                <div className="bg-white rounded-2xl shadow-lg p-6">
                    <div className="flex justify-between items-center">
                        <div className="flex gap-3">
                            {currentStep > 1 && (
                                <Button
                                    onClick={handlePrevious}
                                    variant="outline"
                                    className="flex items-center gap-2"
                                >
                                    <ArrowLeft className="h-4 w-4" />
                                    Previous
                                </Button>
                            )}

                            {onCancel && (
                                <Button
                                    onClick={onCancel}
                                    variant="outline"
                                    className="flex items-center gap-2 text-gray-600"
                                >
                                    <LogOut className="h-4 w-4" />
                                    Back to Dashboard
                                </Button>
                            )}
                        </div>

                        <div className="flex gap-3">
                            <Button
                                onClick={handleSaveAndExit}
                                variant="outline"
                                disabled={isSaving}
                                className="flex items-center gap-2 border-blue-500 text-blue-600 hover:bg-blue-50"
                            >
                                <Save className="h-4 w-4" />
                                {isSaving ? 'Saving...' : 'Save & Exit'}
                            </Button>

                            {currentStep < 10 ? (
                                <Button
                                    onClick={handleNext}
                                    className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600"
                                >
                                    Next
                                    <ArrowRight className="h-4 w-4" />
                                </Button>
                            ) : (
                                <Button
                                    onClick={handleFinish}
                                    disabled={isSaving}
                                    className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600"
                                >
                                    <CheckCircle2 className="h-4 w-4" />
                                    {isSaving ? 'Completing...' : 'Finish'}
                                </Button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
