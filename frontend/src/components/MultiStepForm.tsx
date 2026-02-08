import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import toast, { Toaster } from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { Save } from 'lucide-react';
import { useDraftManager } from '../hooks/useDraftManager';
import { useNavigationBlocker } from '../hooks/useNavigationBlocker';
import NavigationConfirmModal from './NavigationConfirmModal';
import { ErrorSummaryPanel } from './ErrorSummaryPanel';
import { transformZodErrors, ValidationErrorSummary } from '../utils/validationErrorTransformer';
// Helper to get CSRF token from cookies (set by backend)
const getCSRFToken = (): string | null => {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
};

import {
    ArrowRight,
    ArrowLeft,
    CheckCircle2,
    FileText,
    User,
    Home,
    MapPin,
    Calendar,
    Building,
    Route,
    Compass,
    ClipboardList,
    Gavel,
    TrendingUp,
    Scale,
    Award,
    Receipt
} from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';
import { Label } from './Label';
import { AutocompleteInput } from './AutocompleteInput';
import type { DeedInfo, Report } from '../types';
import { PropertyLocationSection } from './PropertyLocationSection';
import { AccessDirectionsSection } from './AccessDirectionsSection';
import { GooglePlacesAutocomplete } from './GooglePlacesAutocomplete';
import { InteractivePropertyMap } from './InteractivePropertyMap';
import { LandExtentInput } from './LandExtentInput';
import { BoundaryInformationSection } from './BoundaryInformationSection';
import { DocumentUploadOCR } from './DocumentUploadOCR';
import { PropertyDescriptionStep } from './PropertyDescriptionStep';
import InvoiceDataStep from './InvoiceDataStep';
import LocalityInformationSection from './LocalityInformationSection';
import LegalAspectsSection from './LegalAspectsSection';
import LandValuesSection from './LandValuesSection';
import ValuationSection from './ValuationSection';
import CertificationSection from './CertificationSection';
import { DatePicker } from './DatePicker';
import { LoadingOverlay } from './LoadingOverlay';
import { validateSriLankanNIC, validatePassport, useFieldValidation } from '../utils/validators';
import { PREDEFINED_VALUATION_PURPOSES } from '../constants/valuationPurposes';
import { COMMON_DEED_TYPES, FORM_STEPS } from '../constants/multiStepFormConstants';
import { toTitleCase } from '../utils/textFormatter';

// Import schemas from centralized file
import {
    propertyPlanSchema,
    baseApplicantPurposeSchema,
    applicantPurposeSchema,
    baseAdditionalDetailsSchema,
    additionalDetailsSchema,
    extentBoundariesSchema,
    propertySearchSchema,
    propertyDetailsSchema,
    propertyDescriptionSchema,
    basePropertyPlanSchema,
    baseCertificationSchema,
    completeFormSchema,
    propertyOnlySchema,
} from '../schemas/multiStepFormSchemas';

// Import types from centralized file
import type { FormData, StepComponentProps, MultiStepFormProps, DataQualityWarning } from '../types/multiStepForm';

// Steps configuration imported from constants
const steps = FORM_STEPS;

// Step 1: Property & Plan Information
const PropertyPlanStep: React.FC<StepComponentProps> = ({ register, errors, setValue, watch }) => {
    const identificationType = watch('property_identification_type');

    const handleOCRDataExtracted = (extractedData: any, confidence: number) => {
        let detectedType: string | null = null;
        // Auto-fill fields from OCR
        if (setValue) {
            // Check for BOTH plan and deed (HYBRID MODE - highest priority)
            const hasPlan = !!extractedData.plan_number;
            const hasDeed = extractedData.deeds && Array.isArray(extractedData.deeds) && extractedData.deeds.length > 0;

            if (hasPlan && hasDeed) {
                // HYBRID MODE: Both plan and deed detected
                detectedType = 'plan_and_deed';
                setValue('property_identification_type', 'plan_and_deed');

                // Fill plan fields
                if (extractedData.plan_number) setValue('plan_number', extractedData.plan_number);
                if (extractedData.plan_date) setValue('plan_date', extractedData.plan_date);
                if (extractedData.licensed_surveyor_name) setValue('licensed_surveyor_name', extractedData.licensed_surveyor_name);
                if (extractedData.lot_number) setValue('lot_number', extractedData.lot_number);

                // Fill deed fields
                const firstDeed = extractedData.deeds[0];
                if (firstDeed.deed_type) setValue('deed_type', firstDeed.deed_type);
                if (firstDeed.deed_number) setValue('deed_number', firstDeed.deed_number);
                if (firstDeed.deed_date) setValue('deed_date', firstDeed.deed_date);
                if (firstDeed.notary_name) setValue('notary_name', firstDeed.notary_name);
                if (firstDeed.notary_location) setValue('notary_location', firstDeed.notary_location);
            }
            // Priority 1: Plan only
            else if (hasPlan) {
                detectedType = 'plan';
                setValue('property_identification_type', 'plan');
                if (extractedData.plan_number) setValue('plan_number', extractedData.plan_number);
                if (extractedData.plan_date) setValue('plan_date', extractedData.plan_date);
                if (extractedData.licensed_surveyor_name) setValue('licensed_surveyor_name', extractedData.licensed_surveyor_name);
                if (extractedData.lot_number) setValue('lot_number', extractedData.lot_number);
            }
            // Priority 2: Deed/certificate only
            else if (hasDeed) {
                const firstDeed = extractedData.deeds[0];

                // Check if it's a Certificate of Sale
                if (firstDeed.deed_type?.toLowerCase().includes('certificate of sale')) {
                    detectedType = 'certificate_of_sale';
                    setValue('property_identification_type', 'certificate_of_sale');
                    if (firstDeed.deed_number) setValue('certificate_number', firstDeed.deed_number);
                    if (firstDeed.deed_date) setValue('certificate_date', firstDeed.deed_date);
                    if (firstDeed.notary_name) setValue('certificate_notary_name', firstDeed.notary_name);
                    if (firstDeed.notary_location) setValue('certificate_notary_district', firstDeed.notary_location);
                } else {
                    detectedType = 'deed';
                    setValue('property_identification_type', 'deed');
                    if (firstDeed.deed_type) setValue('deed_type', firstDeed.deed_type);
                    if (firstDeed.deed_number) setValue('deed_number', firstDeed.deed_number);
                    if (firstDeed.deed_date) setValue('deed_date', firstDeed.deed_date);
                    if (firstDeed.notary_name) setValue('notary_name', firstDeed.notary_name);
                    if (firstDeed.notary_location) setValue('notary_location', firstDeed.notary_location);
                }
            }

            // Auto-fill extent data
            if (extractedData.land_extent_acres !== undefined) {
                setValue('land_extent_acres', extractedData.land_extent_acres);
                setValue('land_extent_roods', extractedData.land_extent_roods || 0);
                setValue('land_extent_perches', extractedData.land_extent_perches || 0);
                setValue('land_extent_hectares', extractedData.land_extent_hectares);
                setValue('land_extent_square_meters', extractedData.land_extent_square_meters);
                setValue('land_extent_formatted', extractedData.land_extent_formatted);
            }

            // Auto-fill boundaries
            if (extractedData.boundaries) setValue('boundaries', extractedData.boundaries);

            // Auto-fill physical boundaries
            if (extractedData.physical_boundaries_types) {
                setValue('physical_boundaries_types', extractedData.physical_boundaries_types);
            }
            if (extractedData.physical_boundaries_description) {
                setValue('physical_boundaries_description', extractedData.physical_boundaries_description);
            }

            // Auto-fill traditional name
            if (extractedData.land_traditional_name) {
                setValue('land_traditional_name', extractedData.land_traditional_name);
            }

            // Auto-fill location/administrative fields
            if (extractedData.village) setValue('property_village', extractedData.village);
            if (extractedData.gn_division_name) setValue('grama_niladari_division', extractedData.gn_division_name);
            if (extractedData.ds_division) setValue('property_divisional_secretariat', extractedData.ds_division);
            if (extractedData.district) setValue('property_district', extractedData.district);
            if (extractedData.province) setValue('property_province', extractedData.province);
            if (extractedData.korale) setValue('korale', extractedData.korale);
            if (extractedData.pradeshiya_sabha) setValue('pradeshiya_sabha', extractedData.pradeshiya_sabha);
        }

        // Show success toast
        const confidencePercent = (confidence * 100).toFixed(0);
        if (detectedType) {
            const typeLabel = detectedType.replace('_', ' ');
            if (confidence >= 0.7) {
                toast.success(`Detected ${typeLabel} information with ${confidencePercent}% confidence. Please review and edit as needed.`, {
                    duration: 5000,
                    position: 'top-right',
                });
            } else {
                toast(`Detected ${typeLabel} information with ${confidencePercent}% confidence. Please review and verify carefully.`, {
                    icon: '⚠️',
                    duration: 6000,
                    position: 'top-right',
                });
            }
        } else {
            if (confidence >= 0.7) {
                toast.success(`Data extracted with ${confidencePercent}% confidence. Please review and edit as needed.`, {
                    duration: 5000,
                    position: 'top-right',
                });
            } else {
                toast(`Data extracted with ${confidencePercent}% confidence. Please review and verify carefully.`, {
                    icon: '⚠️',
                    duration: 6000,
                    position: 'top-right',
                });
            }
        }
    };

    return (
        <div className="space-y-6">
            {/* Document Upload & OCR */}
            <DocumentUploadOCR
                onDataExtracted={handleOCRDataExtracted}
                onError={(error) => toast.error(`OCR Error: ${error}`, {
                    duration: 6000,
                    position: 'top-right',
                })}
                documentTypeHint="survey_plan"
            />

            <div className="border-t border-gray-200 my-6"></div>

            {/* Property Identification Type - Selection Cards (NEW UI) */}
            <div className="space-y-4">
                <Label className="text-gray-900 font-semibold text-lg">
                    What information do you have for this property? *
                </Label>
                <p className="text-sm text-gray-600 mb-4">
                    Select the document type(s) you have. You can now select multiple documents if you have both plan and deed!
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Card 1: Survey Plan Only */}
                    <div
                        onClick={() => setValue('property_identification_type', 'plan', { shouldValidate: true })}
                        className={`cursor-pointer border-2 rounded-2xl p-6 transition-all duration-200 transform hover:scale-[1.02] ${identificationType === 'plan'
                                ? 'border-blue-500 bg-blue-50 shadow-lg ring-2 ring-blue-200'
                                : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-md'
                            }`}
                    >
                        <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl ${identificationType === 'plan' ? 'bg-blue-500' : 'bg-gray-100'
                                }`}>
                                <Home className={`h-6 w-6 ${identificationType === 'plan' ? 'text-white' : 'text-gray-600'
                                    }`} />
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 mb-1">Survey Plan Only</h3>
                                <p className="text-sm text-gray-600">
                                    I have a survey plan with plan number and date
                                </p>
                            </div>
                            {identificationType === 'plan' && (
                                <CheckCircle2 className="h-6 w-6 text-blue-500 flex-shrink-0" />
                            )}
                        </div>
                    </div>

                    {/* Card 2: Deed Only */}
                    <div
                        onClick={() => setValue('property_identification_type', 'deed', { shouldValidate: true })}
                        className={`cursor-pointer border-2 rounded-2xl p-6 transition-all duration-200 transform hover:scale-[1.02] ${identificationType === 'deed'
                                ? 'border-green-500 bg-green-50 shadow-lg ring-2 ring-green-200'
                                : 'border-gray-200 bg-white hover:border-green-300 hover:shadow-md'
                            }`}
                    >
                        <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl ${identificationType === 'deed' ? 'bg-green-500' : 'bg-gray-100'
                                }`}>
                                <FileText className={`h-6 w-6 ${identificationType === 'deed' ? 'text-white' : 'text-gray-600'
                                    }`} />
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 mb-1">Deed Only</h3>
                                <p className="text-sm text-gray-600">
                                    I have a deed document (transfer deed, deed of gift, etc.)
                                </p>
                            </div>
                            {identificationType === 'deed' && (
                                <CheckCircle2 className="h-6 w-6 text-green-500 flex-shrink-0" />
                            )}
                        </div>
                    </div>

                    {/* Card 3: Survey Plan + Deed (HYBRID - NEW!) */}
                    <div
                        onClick={() => setValue('property_identification_type', 'plan_and_deed', { shouldValidate: true })}
                        className={`cursor-pointer border-2 rounded-2xl p-6 transition-all duration-200 transform hover:scale-[1.02] relative ${identificationType === 'plan_and_deed'
                                ? 'border-purple-500 bg-purple-50 shadow-lg ring-2 ring-purple-200'
                                : 'border-gray-200 bg-white hover:border-purple-300 hover:shadow-md'
                            }`}
                    >

                        <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl ${identificationType === 'plan_and_deed' ? 'bg-purple-500' : 'bg-gray-100'
                                }`}>
                                <div className="flex gap-1">
                                    <Home className={`h-5 w-5 ${identificationType === 'plan_and_deed' ? 'text-white' : 'text-gray-600'
                                        }`} />
                                    <FileText className={`h-5 w-5 ${identificationType === 'plan_and_deed' ? 'text-white' : 'text-gray-600'
                                        }`} />
                                </div>
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 mb-1">Survey Plan + Deed</h3>
                                <p className="text-sm text-gray-600">
                                    I have both survey plan and deed documents
                                </p>
                            </div>
                            {identificationType === 'plan_and_deed' && (
                                <CheckCircle2 className="h-6 w-6 text-purple-500 flex-shrink-0" />
                            )}
                        </div>
                    </div>

                    {/* Card 4: Certificate of Sale */}
                    <div
                        onClick={() => setValue('property_identification_type', 'certificate_of_sale', { shouldValidate: true })}
                        className={`cursor-pointer border-2 rounded-2xl p-6 transition-all duration-200 transform hover:scale-[1.02] ${identificationType === 'certificate_of_sale'
                                ? 'border-orange-500 bg-orange-50 shadow-lg ring-2 ring-orange-200'
                                : 'border-gray-200 bg-white hover:border-orange-300 hover:shadow-md'
                            }`}
                    >
                        <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl ${identificationType === 'certificate_of_sale' ? 'bg-orange-500' : 'bg-gray-100'
                                }`}>
                                <Award className={`h-6 w-6 ${identificationType === 'certificate_of_sale' ? 'text-white' : 'text-gray-600'
                                    }`} />
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900 mb-1">Certificate of Sale</h3>
                                <p className="text-sm text-gray-600">
                                    I have a certificate of sale from a court auction
                                </p>
                            </div>
                            {identificationType === 'certificate_of_sale' && (
                                <CheckCircle2 className="h-6 w-6 text-orange-500 flex-shrink-0" />
                            )}
                        </div>
                    </div>
                </div>

                {errors.property_identification_type && (
                    <p className="text-red-500 text-sm mt-2">{errors.property_identification_type.message}</p>
                )}
            </div>

            {/* Conditional Fields Based on Selection */}
            {identificationType === 'plan' && (
                <div className="space-y-4 border-2 border-blue-200 rounded-2xl p-6 bg-blue-50/30">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Property Plan Information</h3>

                    <div className="space-y-2">
                        <Label htmlFor="lot_number" className="text-gray-700 font-medium">
                            Lot Number
                        </Label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Home className="h-5 w-5 text-gray-400" />
                            </div>
                            <Input
                                id="lot_number"
                                type="text"
                                placeholder="e.g., Lot 15, Lots 1 & 2"
                                className="pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                                {...register('lot_number')}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="plan_number" className="text-gray-700 font-medium">
                                Plan Number *
                            </Label>
                            <Input
                                id="plan_number"
                                type="text"
                                placeholder="e.g., 1035, 2005/65"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                                {...register('plan_number')}
                            />
                            {errors.plan_number && (
                                <p className="text-red-500 text-sm">{errors.plan_number.message}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="plan_date" className="text-gray-700 font-medium">
                                Plan Date (DD-MM-YYYY) *
                            </Label>
                            <DatePicker
                                id="plan_date"
                                value={watch('plan_date')}
                                onChange={(date) => setValue('plan_date', date, { shouldValidate: true, shouldDirty: true })}
                                placeholder="01-01-2024"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                            />
                            {errors.plan_date && (
                                <p className="text-red-500 text-sm">{errors.plan_date.message}</p>
                            )}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="licensed_surveyor_name" className="text-gray-700 font-medium">
                            Licensed Surveyor Name
                        </Label>
                        <Input
                            id="licensed_surveyor_name"
                            type="text"
                            placeholder="Enter licensed surveyor's full name"
                            className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                            {...register('licensed_surveyor_name')}
                        />
                    </div>
                </div>
            )}

            {identificationType === 'deed' && (
                <div className="space-y-4 border-2 border-green-200 rounded-2xl p-6 bg-green-50/30">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Deed Information</h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <AutocompleteInput
                                label="Deed Type"
                                value={watch('deed_type') || ''}
                                onChange={(value) => setValue('deed_type', value)}
                                suggestions={COMMON_DEED_TYPES}
                                placeholder="Select or type deed type (e.g., Deed of Gift, Transfer Deed)"
                                allowCustom={true}
                                className="w-full"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Select from common deed types or type your own
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="deed_number" className="text-gray-700 font-medium">
                                Deed Number *
                            </Label>
                            <Input
                                id="deed_number"
                                type="text"
                                placeholder="Deed number"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                                {...register('deed_number')}
                            />
                            {errors.deed_number && (
                                <p className="text-red-500 text-sm">{errors.deed_number.message}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="deed_date" className="text-gray-700 font-medium">
                                Deed Date (DD-MM-YYYY) *
                            </Label>
                            <DatePicker
                                id="deed_date"
                                value={watch('deed_date')}
                                onChange={(date) => setValue('deed_date', date, { shouldValidate: true, shouldDirty: true })}
                                placeholder="01-01-2024"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                            />
                            {errors.deed_date && (
                                <p className="text-red-500 text-sm">{errors.deed_date.message}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="notary_name" className="text-gray-700 font-medium">
                                Notary Name
                            </Label>
                            <Input
                                id="notary_name"
                                type="text"
                                placeholder="Notary name"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                                {...register('notary_name')}
                            />
                        </div>

                        <div className="space-y-2 md:col-span-2">
                            <Label htmlFor="notary_location" className="text-gray-700 font-medium">
                                Notary District
                            </Label>
                            <Input
                                id="notary_location"
                                type="text"
                                placeholder="e.g., Colombo district"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                                {...register('notary_location')}
                            />
                        </div>
                    </div>
                </div>
            )}

            {identificationType === 'certificate_of_sale' && (
                <div className="space-y-4 border-2 border-orange-200 rounded-2xl p-6 bg-orange-50/30">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Certificate of Sale Information</h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="certificate_number" className="text-gray-700 font-medium">
                                Certificate Number *
                            </Label>
                            <Input
                                id="certificate_number"
                                type="text"
                                placeholder="e.g., 383"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200"
                                {...register('certificate_number')}
                            />
                            {errors.certificate_number && (
                                <p className="text-red-500 text-sm">{errors.certificate_number.message}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="certificate_date" className="text-gray-700 font-medium">
                                Certificate Date (DD-MM-YYYY) *
                            </Label>
                            <DatePicker
                                id="certificate_date"
                                value={watch('certificate_date')}
                                onChange={(date) => setValue('certificate_date', date, { shouldValidate: true, shouldDirty: true })}
                                placeholder="14-02-2022"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200"
                            />
                            {errors.certificate_date && (
                                <p className="text-red-500 text-sm">{errors.certificate_date.message}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="certificate_notary_name" className="text-gray-700 font-medium">
                                Notary Name
                            </Label>
                            <Input
                                id="certificate_notary_name"
                                type="text"
                                placeholder="e.g., R.G.3.A. RANDENIYA"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200"
                                {...register('certificate_notary_name')}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="certificate_notary_district" className="text-gray-700 font-medium">
                                Notary District
                            </Label>
                            <Input
                                id="certificate_notary_district"
                                type="text"
                                placeholder="e.g., Colombo district"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200"
                                {...register('certificate_notary_district')}
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* HYBRID MODE: Both Plan and Deed fields (NEW!) */}
            {identificationType === 'plan_and_deed' && (
                <div className="space-y-6">
                    {/* Plan Section */}
                    <div className="space-y-4 border-2 border-blue-200 rounded-2xl p-6 bg-blue-50/30">
                        <div className="flex items-center gap-2 mb-4">
                            <Home className="h-5 w-5 text-blue-600" />
                            <h3 className="text-lg font-semibold text-gray-900">Survey Plan Information</h3>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="lot_number" className="text-gray-700 font-medium">
                                Lot Number
                            </Label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Home className="h-5 w-5 text-gray-400" />
                                </div>
                                <Input
                                    id="lot_number"
                                    type="text"
                                    placeholder="e.g., Lot 15, Lots 1 & 2"
                                    className="pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                                    {...register('lot_number')}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="plan_number" className="text-gray-700 font-medium">
                                    Plan Number *
                                </Label>
                                <Input
                                    id="plan_number"
                                    type="text"
                                    placeholder="e.g., 1035, 2005/65"
                                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                                    {...register('plan_number')}
                                />
                                {errors.plan_number && (
                                    <p className="text-red-500 text-sm">{errors.plan_number.message}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="plan_date" className="text-gray-700 font-medium">
                                    Plan Date (DD-MM-YYYY) *
                                </Label>
                                <DatePicker
                                    id="plan_date"
                                    value={watch('plan_date')}
                                    onChange={(date) => setValue('plan_date', date, { shouldValidate: true, shouldDirty: true })}
                                    placeholder="01-01-2024"
                                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                                />
                                {errors.plan_date && (
                                    <p className="text-red-500 text-sm">{errors.plan_date.message}</p>
                                )}
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="licensed_surveyor_name" className="text-gray-700 font-medium">
                                Licensed Surveyor Name
                            </Label>
                            <Input
                                id="licensed_surveyor_name"
                                type="text"
                                placeholder="Enter licensed surveyor's full name"
                                className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                                {...register('licensed_surveyor_name')}
                            />
                        </div>
                    </div>

                    {/* Deed Section */}
                    <div className="space-y-4 border-2 border-green-200 rounded-2xl p-6 bg-green-50/30">
                        <div className="flex items-center gap-2 mb-4">
                            <FileText className="h-5 w-5 text-green-600" />
                            <h3 className="text-lg font-semibold text-gray-900">Deed Information</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <AutocompleteInput
                                    label="Deed Type"
                                    value={watch('deed_type') || ''}
                                    onChange={(value) => setValue('deed_type', value)}
                                    suggestions={COMMON_DEED_TYPES}
                                    placeholder="Select or type deed type (e.g., Deed of Gift, Transfer Deed)"
                                    allowCustom={true}
                                    className="w-full"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    Select from common deed types or type your own
                                </p>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="deed_number" className="text-gray-700 font-medium">
                                    Deed Number *
                                </Label>
                                <Input
                                    id="deed_number"
                                    type="text"
                                    placeholder="Deed number"
                                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                                    {...register('deed_number')}
                                />
                                {errors.deed_number && (
                                    <p className="text-red-500 text-sm">{errors.deed_number.message}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="deed_date" className="text-gray-700 font-medium">
                                    Deed Date (DD-MM-YYYY) *
                                </Label>
                                <DatePicker
                                    id="deed_date"
                                    value={watch('deed_date')}
                                    onChange={(date) => setValue('deed_date', date, { shouldValidate: true, shouldDirty: true })}
                                    placeholder="01-01-2024"
                                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                                />
                                {errors.deed_date && (
                                    <p className="text-red-500 text-sm">{errors.deed_date.message}</p>
                                )}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="notary_name" className="text-gray-700 font-medium">
                                    Notary Name
                                </Label>
                                <Input
                                    id="notary_name"
                                    type="text"
                                    placeholder="Notary name"
                                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                                    {...register('notary_name')}
                                />
                            </div>

                            <div className="space-y-2 md:col-span-2">
                                <Label htmlFor="notary_location" className="text-gray-700 font-medium">
                                    Notary District
                                </Label>
                                <Input
                                    id="notary_location"
                                    type="text"
                                    placeholder="e.g., Colombo district"
                                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200"
                                    {...register('notary_location')}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Info box */}
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <p className="text-sm text-purple-800">
                            <strong>Hybrid Mode:</strong> Both plan and deed information will be included in your report. The certification text will reference both documents.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

// Step 2: Land Extent & Boundaries
const ExtentBoundariesStep: React.FC<StepComponentProps> = ({ setValue, watch }) => {
    const handleExtentChange = (extentData: any) => {
        if (setValue) {
            setValue('land_extent_acres', extentData.land_extent_acres);
            setValue('land_extent_roods', extentData.land_extent_roods);
            setValue('land_extent_perches', extentData.land_extent_perches);
            setValue('land_extent_hectares', extentData.land_extent_hectares);
            setValue('land_extent_square_meters', extentData.land_extent_square_meters);
            setValue('land_extent_formatted', extentData.land_extent_formatted);
        }
    };

    const handleBoundaryChange = (data: any) => {
        if (setValue) {
            setValue('boundaries', data.boundaries);
            setValue('physical_boundaries_types', data.physical_boundaries_types);
            setValue('physical_boundaries_description', data.physical_boundaries_description);
            setValue('land_traditional_name', data.land_traditional_name);
        }
    };

    return (
        <div className="space-y-8">
            {/* Land Extent Input */}
            <LandExtentInput
                acres={watch?.('land_extent_acres') || 0}
                roods={watch?.('land_extent_roods') || 0}
                perches={watch?.('land_extent_perches') || 0}
                onChange={handleExtentChange}
            />

            <div className="border-t border-gray-200 my-6"></div>

            {/* Boundary Information */}
            <BoundaryInformationSection
                boundaries={watch?.('boundaries')}
                physicalBoundariesTypes={watch?.('physical_boundaries_types') || []}
                physicalBoundariesDescription={watch?.('physical_boundaries_description') || ''}
                landTraditionalName={watch?.('land_traditional_name') || ''}
                onChange={handleBoundaryChange}
            />
        </div>
    );
};

// Step 3: Property Search (Google Maps)
const PropertySearchStep: React.FC<StepComponentProps & { getValues: any }> = ({ setValue, getValues }) => {
    const [formData, setFormData] = useState<Partial<Report>>({});
    const [searchingProperty, setSearchingProperty] = useState(false);

    // Sync with react-hook-form
    React.useEffect(() => {
        const currentValues = getValues();
        setFormData(currentValues);
    }, [getValues]);

    const updateFormData = (updates: Partial<Report>) => {
        setFormData(prev => ({ ...prev, ...updates }));
        // Sync back to react-hook-form
        Object.keys(updates).forEach(key => {
            setValue(key, updates[key as keyof typeof updates]);
        });
    };

    return (
        <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border-2 border-blue-300 rounded-2xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                    <MapPin className="h-6 w-6 text-blue-600" />
                    Find Property & Generate Directions
                </h3>
                <p className="text-gray-600">
                    Use the interactive map to find the property location and generate access directions - just like Google Maps!
                </p>
            </div>

            {/* Interactive Google Maps */}
            <InteractivePropertyMap
                onPropertySelected={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Property selected:', data);
                    }
                    updateFormData({
                        property_latitude: data.latitude,
                        property_longitude: data.longitude,
                        // Save geocoding data for auto-fill in next step
                        property_district: data.district,
                        property_province: data.province,
                        property_village: data.village,
                    });
                }}
                onStartingPointSelected={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Starting point selected:', data);
                    }
                    updateFormData({
                        access_starting_point_name: data.address,
                        access_starting_point_latitude: data.latitude,
                        access_starting_point_longitude: data.longitude,
                    });
                }}
                onRouteGenerated={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Route generated:', data);
                    }
                    updateFormData({
                        access_directions_text: data.accessText,
                        access_distance_km: parseFloat(data.distance.replace(/[^\d.]/g, '')) || 0,
                        access_duration_minutes: parseFloat(data.duration.replace(/[^\d.]/g, '')) || 0,
                        access_route_data: { steps: data.steps, distance: data.distance, duration: data.duration },
                        // Save map image URL
                        location_map_image_data: data.mapImageUrl,
                        // NEW: Save dual-mode data
                        access_road_conditions: data.road_conditions,
                        access_road_segments: data.road_segments,
                        access_entry_mode: data.entry_mode,
                    });
                }}
                onFacilitiesFetched={(data) => {
                    if (import.meta.env.DEV) {
                        console.log('[MultiStepForm] Facilities prefetched:', data);
                    }
                    updateFormData({
                        nearby_facilities: data.facilities,
                        major_town_name: data.majorTown?.name,
                        distance_to_major_town_km: data.majorTown?.distance_km,
                        nearest_bus_stop_name: data.transport?.bus_stop?.name,
                        nearest_bus_stop_distance_km: data.transport?.bus_stop?.distance_km,
                        nearest_railway_station: data.transport?.railway_station?.name,
                        nearest_railway_distance_km: data.transport?.railway_station?.distance_km,
                    });
                }}
                initialStartingPoint={formData.access_starting_point_name}
                // Pass saved data to restore state when navigating back
                initialRouteData={formData.access_route_data}
                initialAccessText={formData.access_directions_text}
                initialMapImageUrl={formData.location_map_image_data}
                // NEW: Pass dual-mode data to restore state
                initialEntryMode={formData.access_entry_mode}
                initialRoadConditions={formData.access_road_conditions}
                initialRoadSegments={formData.access_road_segments}
            />
        </div>
    );
};

// Step 3: Property Details (auto-filled from Step 2)
const PropertyLocationNewStep: React.FC<StepComponentProps & { getValues: any }> = ({ setValue, getValues, watch }) => {
    const [formData, setFormData] = useState<Partial<Report>>({});

    // Sync with react-hook-form
    React.useEffect(() => {
        const currentValues = getValues();
        setFormData(currentValues);
    }, [getValues]);

    const updateFormData = (updates: Partial<Report>) => {
        setFormData(prev => ({ ...prev, ...updates }));
        // Sync back to react-hook-form
        Object.keys(updates).forEach(key => {
            setValue(key, updates[key as keyof typeof updates]);
        });
    };

    return (
        <div className="space-y-6">
            <PropertyLocationSection
                formData={formData}
                updateFormData={updateFormData}
            />

            {/* Show map if available */}
            {formData.location_map_image_data && (
                <div className="mt-6 border-2 border-blue-200 rounded-2xl overflow-hidden">
                    <img
                        src={formData.location_map_image_data}
                        alt="Property Location Map"
                        className="w-full h-80 object-cover"
                    />
                </div>
            )}
        </div>
    );
};

// Step 3: Applicant Information & Purpose (moved from step 2, with reversed checkbox)
const ApplicantPurposeStep: React.FC<StepComponentProps & { getValues: any }> = ({ register, errors, watch, setValue, getValues }) => {
    const hasAdditionalOwner = watch('has_additional_owner');
    const idType = watch('applicant_id_type');
    const idNumber = watch('applicant_id_number');

    // Clear additional owner names when "No" is selected
    useEffect(() => {
        if (hasAdditionalOwner === 'no') {
            setValue('additional_owner_names', undefined);
        }
    }, [hasAdditionalOwner, setValue]);

    // Dynamic validator function based on ID type
    const getIdValidator = () => {
        if (idType === 'NIC') {
            return validateSriLankanNIC;
        } else if (idType === 'Passport') {
            return validatePassport;
        }
        // For "Other", return a simple validator
        return (value: string) => {
            if (!value || value.length < 3) {
                return { isValid: false, error: 'ID number must be at least 3 characters' };
            }
            return { isValid: true };
        };
    };

    // Real-time validation with 500ms debounce
    const idValidation = useFieldValidation(
        idNumber,
        getIdValidator(),
        500
    );

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label htmlFor="applicant_title" className="text-gray-700 font-medium">
                        Title *
                    </Label>
                    <select
                        id="applicant_title"
                        className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 px-4"
                        {...register('applicant_title')}
                    >
                        <option value="">Select title</option>
                        <option value="Mr.">Mr.</option>
                        <option value="Mrs.">Mrs.</option>
                        <option value="Miss.">Miss.</option>
                        <option value="Ms.">Ms.</option>
                        <option value="Dr.">Dr.</option>
                    </select>
                    {errors.applicant_title && (
                        <p className="text-red-500 text-sm">{errors.applicant_title.message}</p>
                    )}
                </div>

                <div className="space-y-2">
                    <Label htmlFor="applicant_full_name" className="text-gray-700 font-medium">
                        Full Name *
                    </Label>
                    <Input
                        id="applicant_full_name"
                        type="text"
                        placeholder="Applicant's full name"
                        className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        {...register('applicant_full_name')}
                    />
                    {errors.applicant_full_name && (
                        <p className="text-red-500 text-sm">{errors.applicant_full_name.message}</p>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                    <Label htmlFor="applicant_id_type" className="text-gray-700 font-medium">
                        ID Type <span className="text-gray-500 text-sm font-normal">(Optional)</span>
                    </Label>
                    <select
                        id="applicant_id_type"
                        className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 px-4"
                        {...register('applicant_id_type')}
                    >
                        <option value="">Select ID type (optional)</option>
                        <option value="Passport">Passport</option>
                        <option value="NIC">NIC</option>
                        <option value="Other">Other</option>
                    </select>
                    {errors.applicant_id_type && (
                        <p className="text-red-500 text-sm">{errors.applicant_id_type.message}</p>
                    )}
                </div>

                <div className="space-y-2">
                    <Label htmlFor="applicant_id_number" className="text-gray-700 font-medium">
                        ID Number <span className="text-gray-500 text-sm font-normal">(Optional)</span>
                    </Label>
                    <Input
                        id="applicant_id_number"
                        type="text"
                        placeholder={
                            idType === 'NIC'
                                ? 'e.g., 912345678V or 199212345678'
                                : idType === 'Passport'
                                    ? 'e.g., N1234567, AB123456, A1234567'
                                    : 'ID number (optional)'
                        }
                        className="h-14 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        {...register('applicant_id_number')}
                    />
                    {/* Form validation errors take precedence (red) */}
                    {errors.applicant_id_number && (
                        <p className="text-red-500 text-sm">{errors.applicant_id_number.message}</p>
                    )}
                    {/* Real-time validation warnings (amber) - only show if no form errors */}
                    {!errors.applicant_id_number && idValidation.error && idNumber && idType && (
                        <p className="text-amber-600 text-sm flex items-center gap-1">
                            <span className="text-xs">⚠</span>
                            {idValidation.error}
                        </p>
                    )}
                    {/* Success indicator (green) - only show if valid and no form errors */}
                    {!errors.applicant_id_number && idValidation.isValid && idNumber && idType && (
                        <p className="text-emerald-600 text-sm flex items-center gap-1">
                            <span className="text-xs">✓</span>
                            Valid {idType} format
                        </p>
                    )}
                </div>
            </div>

            <div className="space-y-2">
                <Label htmlFor="applicant_address_line1" className="text-gray-700 font-medium">
                    Address Line 1 (House/Plot, Street) *
                </Label>
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                        <MapPin className="h-5 w-5 text-gray-400" />
                    </div>
                    <Input
                        id="applicant_address_line1"
                        type="text"
                        placeholder="e.g., No. 45, Main Street"
                        className="pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        {...register('applicant_address_line1')}
                    />
                </div>
                {errors.applicant_address_line1 && (
                    <p className="text-red-500 text-sm">{errors.applicant_address_line1.message}</p>
                )}
            </div>

            <div className="space-y-2">
                <Label htmlFor="applicant_address_line2" className="text-gray-700 font-medium">
                    Address Line 2 (Village/Area) <span className="text-gray-400">(Optional)</span>
                </Label>
                <Input
                    id="applicant_address_line2"
                    type="text"
                    placeholder="e.g., Colombo 07"
                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                    {...register('applicant_address_line2')}
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                    <Label htmlFor="applicant_district" className="text-gray-700 font-medium">
                        District *
                    </Label>
                    <Input
                        id="applicant_district"
                        type="text"
                        placeholder="e.g., Colombo"
                        className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        {...register('applicant_district')}
                    />
                    {errors.applicant_district && (
                        <p className="text-red-500 text-sm">{errors.applicant_district.message}</p>
                    )}
                </div>

                <div className="space-y-2">
                    <Label htmlFor="applicant_province" className="text-gray-700 font-medium">
                        Province *
                    </Label>
                    <Input
                        id="applicant_province"
                        type="text"
                        placeholder="e.g., Western"
                        className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        {...register('applicant_province')}
                    />
                    {errors.applicant_province && (
                        <p className="text-red-500 text-sm">{errors.applicant_province.message}</p>
                    )}
                </div>

                <div className="space-y-2">
                    <Label htmlFor="applicant_country" className="text-gray-700 font-medium">
                        Country *
                    </Label>
                    <Input
                        id="applicant_country"
                        type="text"
                        placeholder="Sri Lanka"
                        defaultValue="Sri Lanka"
                        className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        {...register('applicant_country')}
                    />
                    {errors.applicant_country && (
                        <p className="text-red-500 text-sm">{errors.applicant_country.message}</p>
                    )}
                </div>
            </div>

            <div className="space-y-2">
                <Label htmlFor="applicant_contact_number" className="text-gray-700 font-medium">
                    Contact Number <span className="text-gray-400">(Optional)</span>
                </Label>
                <Input
                    id="applicant_contact_number"
                    type="text"
                    placeholder="e.g., 077-1234567"
                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                    {...register('applicant_contact_number')}
                />
                {errors.applicant_contact_number && (
                    <p className="text-red-500 text-sm">{errors.applicant_contact_number.message}</p>
                )}
            </div>

            <div className="border-t border-gray-200 pt-6 mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Valuation Purpose</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label htmlFor="valuation_type" className="text-gray-700 font-medium">
                            Valuation Type *
                        </Label>
                        <select
                            id="valuation_type"
                            className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 px-4"
                            {...register('valuation_type')}
                        >
                            <option value="">Select valuation type...</option>
                            <option value="Market value">Market value</option>
                            <option value="Present Market Value">Present Market Value</option>
                            <option value="Forced Sale Value">Forced Sale Value</option>
                            <option value="Rental Value">Rental Value</option>
                            <option value="Insurance Value">Insurance Value</option>
                        </select>
                        {errors.valuation_type && (
                            <p className="text-red-500 text-sm">{errors.valuation_type.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="property_type_valued" className="text-gray-700 font-medium">
                            Property Type *
                        </Label>
                        <select
                            id="property_type_valued"
                            className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 px-4"
                            {...register('property_type_valued')}
                        >
                            <option value="">Select property type...</option>
                            <option value="immovable property">immovable property</option>
                            <option value="Residential Property">Residential Property</option>
                            <option value="Commercial Property">Commercial Property</option>
                            <option value="Agricultural Property">Agricultural Property</option>
                            <option value="Land">Land</option>
                            <option value="Mixed Use Property">Mixed Use Property</option>
                        </select>
                        {errors.property_type_valued && (
                            <p className="text-red-500 text-sm">{errors.property_type_valued.message}</p>
                        )}
                    </div>
                </div>

                <div className="mt-4">
                    <AutocompleteInput
                        label="Purpose of Valuation"
                        value={watch('valuation_purpose') || ''}
                        onChange={(value) => {
                            // Prevent whitespace-only entries
                            if (value.trim().length === 0 && value.length > 0) {
                                return;
                            }
                            // Apply title case transformation
                            const formatted = value.trim() ? toTitleCase(value) : value;
                            setValue('valuation_purpose', formatted, { shouldValidate: true });
                        }}
                        suggestions={PREDEFINED_VALUATION_PURPOSES}
                        placeholder="Purpose of Valuation"
                        required={false}
                        error={errors.valuation_purpose?.message as string}
                        allowCustom={true}
                        className="w-full"
                    />
                </div>

                <div className="space-y-2 mt-4">
                    <Label className="text-gray-700 font-medium">
                        Additional Property Owner?
                    </Label>
                    <div className="flex gap-4">
                        <label className="flex items-center">
                            <input
                                type="radio"
                                value="yes"
                                className="mr-2"
                                {...register('has_additional_owner')}
                            />
                            <span>Yes</span>
                        </label>
                        <label className="flex items-center">
                            <input
                                type="radio"
                                value="no"
                                className="mr-2"
                                {...register('has_additional_owner')}
                            />
                            <span>No</span>
                        </label>
                    </div>
                </div>

                {hasAdditionalOwner === 'yes' && (
                    <div className="space-y-2 mt-4">
                        <Label htmlFor="additional_owner_names" className="text-gray-700 font-medium">
                            Additional Owner Names
                        </Label>
                        <Input
                            id="additional_owner_names"
                            type="text"
                            placeholder="Enter additional owner names"
                            className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                            {...register('additional_owner_names')}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

// AccessDirectionsNewStep removed - now integrated into PropertySearchStep (Step 2)

// Step 6: Additional Details (Submission, Inspection, Report)
const AdditionalDetailsStep: React.FC<StepComponentProps> = ({
    register,
    errors,
    watch,
    setValue
}) => {
    const hasSpecialNote = watch('has_special_note');
    const requestType = watch('request_type'); // Watch request_type for controlled radio buttons

    return (
        <div className="space-y-6">
            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Submission Destination</h3>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="submission_recipient_position" className="text-gray-700 font-medium">
                            Recipient Position <span className="text-gray-400">(Optional)</span>
                        </Label>
                        <Input
                            id="submission_recipient_position"
                            type="text"
                            placeholder="e.g., Manager, Credit Officer, Branch Manager"
                            className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200"
                            {...register('submission_recipient_position')}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="submission_organization" className="text-gray-700 font-medium">
                            Organization <span className="text-gray-400">(Optional)</span>
                        </Label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Building className="h-5 w-5 text-gray-400" />
                            </div>
                            <Input
                                id="submission_organization"
                                type="text"
                                placeholder="e.g., Bank of Ceylon"
                                className="pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200"
                                {...register('submission_organization')}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="submission_address" className="text-gray-700 font-medium">
                            Address <span className="text-gray-400">(Optional)</span>
                        </Label>
                        <Input
                            id="submission_address"
                            type="text"
                            placeholder="Submission address"
                            className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200"
                            {...register('submission_address')}
                        />
                    </div>
                </div>
            </div>

            {/* Request Information Section */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Request Information</h3>

                <div className="space-y-2">
                    <Label className="text-gray-700 font-medium">
                        Is this a request from a client or organization? *
                    </Label>
                    <div className="flex gap-4">
                        <label className="flex items-center">
                            <input
                                type="radio"
                                value="client_request"
                                className="mr-2"
                                checked={requestType === 'client_request'}
                                {...register('request_type')}
                            />
                            <span>Client Request</span>
                        </label>
                        <label className="flex items-center">
                            <input
                                type="radio"
                                value="organization_request"
                                className="mr-2"
                                checked={requestType === 'organization_request'}
                                {...register('request_type')}
                            />
                            <span>Organization Request</span>
                        </label>
                    </div>
                    {errors.request_type && (
                        <p className="text-red-500 text-sm">{errors.request_type.message}</p>
                    )}
                </div>
            </div>

            <div className="space-y-2">
                <Label htmlFor="inspection_date" className="text-gray-700 font-medium">
                    Date of Inspection (DD-MM-YYYY) *
                </Label>
                <DatePicker
                    id="inspection_date"
                    value={watch('inspection_date')}
                    onChange={(date) => setValue('inspection_date', date, { shouldValidate: true, shouldDirty: true })}
                    placeholder="01-01-2024"
                    className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200"
                />
                {errors.inspection_date && (
                    <p className="text-red-500 text-sm">{errors.inspection_date.message}</p>
                )}
            </div>

            <div className="space-y-2">
                <Label className="text-gray-700 font-medium">
                    Special Note?
                </Label>
                <div className="flex gap-4">
                    <label className="flex items-center">
                        <input
                            type="radio"
                            value="yes"
                            className="mr-2"
                            {...register('has_special_note')}
                        />
                        <span>Yes</span>
                    </label>
                    <label className="flex items-center">
                        <input
                            type="radio"
                            value="no"
                            className="mr-2"
                            {...register('has_special_note')}
                        />
                        <span>No</span>
                    </label>
                </div>
            </div>

            {hasSpecialNote === 'yes' && (
                <div className="space-y-2">
                    <Label htmlFor="special_note_text" className="text-gray-700 font-medium">
                        Special Note Text
                    </Label>
                    <textarea
                        id="special_note_text"
                        rows={4}
                        placeholder="Enter your special note here"
                        className="w-full p-4 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 resize-none"
                        {...register('special_note_text')}
                    />
                </div>
            )}

            <div className="border-t border-gray-200 pt-6 mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Report Metadata</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                        <Label htmlFor="report_reference" className="text-gray-700 font-medium">
                            Reference Number *
                        </Label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <FileText className="h-5 w-5 text-gray-400" />
                            </div>
                            <Input
                                id="report_reference"
                                type="text"
                                placeholder="e.g., REF-2024-001"
                                className="pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200"
                                {...register('report_reference')}
                            />
                        </div>
                        {errors.report_reference && (
                            <p className="text-red-500 text-sm">{errors.report_reference.message}</p>
                        )}
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="report_date" className="text-gray-700 font-medium">
                            Report Date (DD-MM-YYYY) *
                        </Label>
                        <DatePicker
                            id="report_date"
                            value={watch('report_date')}
                            onChange={(date) => setValue('report_date', date, { shouldValidate: true, shouldDirty: true })}
                            placeholder="01-01-2024"
                            className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200"
                        />
                        {errors.report_date && (
                            <p className="text-red-500 text-sm">{errors.report_date.message}</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

// Types imported from '../types/multiStepForm'

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

        const isValid = await validateCurrentStep();
        if (isValid && currentStep < maxStep) {
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

    // Handle click on progress bar step indicators for direct navigation
    const handleStepClick = async (targetStepIndex: number) => {
        // targetStepIndex is 1-based (like currentStep)

        // In new report mode: only allow going back to completed steps (not forward)
        if (!isEditMode && targetStepIndex > currentStep) {
            return; // No feedback, just don't navigate (as per user requirement)
        }

        // Don't navigate if clicking current step
        if (targetStepIndex === currentStep) {
            return;
        }

        // Validate current step before navigating away
        const isValid = await validateCurrentStep();
        if (!isValid) {
            return; // Stay on current step if validation fails
        }

        // Navigate to target step
        setCurrentStep(targetStepIndex);
        // Smooth scroll to top
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
                    {/* Progress Steps - Clickable navigation */}
                    <div className="mb-12">
                        <div className="flex items-center justify-between relative">
                            <div className="absolute top-5 left-0 w-full h-1 bg-gray-200 rounded-full">
                                <div
                                    className="h-1 bg-gradient-to-r from-violet-500 to-purple-600 rounded-full transition-all duration-500"
                                    style={{ width: `${((currentStep - 1) / (maxStep - 1)) * 100}%` }}
                                />
                            </div>

                            {activeSteps.map((step, index) => {
                                const stepNumber = index + 1; // 1-based step number
                                const isCompleted = currentStep > stepNumber;
                                const isCurrent = currentStep === stepNumber;
                                // In edit mode: all steps clickable. In new mode: only completed steps + current
                                const isClickable = isEditMode || stepNumber <= currentStep;

                                return (
                                    <div
                                        key={step.id}
                                        className="relative z-10"
                                        onClick={() => handleStepClick(stepNumber)}
                                    >
                                        <div className={`w-10 h-10 rounded-full border-4 flex items-center justify-center transition-all duration-300 ${
                                            isCompleted
                                                ? 'bg-green-500 border-green-500 text-white'
                                                : isCurrent
                                                    ? 'bg-white border-violet-500 text-violet-500'
                                                    : 'bg-white border-gray-300 text-gray-300'
                                            } ${isClickable ? 'cursor-pointer hover:scale-110' : ''}`}>
                                            {isCompleted ? (
                                                <CheckCircle2 className="h-5 w-5" />
                                            ) : (
                                                <step.icon className="h-5 w-5" />
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

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
                            Step {currentStep} of {maxStep} •
                            <span className="ml-1">All information is securely stored and encrypted</span>
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
