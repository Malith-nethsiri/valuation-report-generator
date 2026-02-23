import React from 'react';
import toast from 'react-hot-toast';
import { CheckCircle2, FileText, Home, Award } from 'lucide-react';
import { Input } from '../Input';
import { Label } from '../Label';
import { AutocompleteInput } from '../AutocompleteInput';
import { DocumentUploadOCR } from '../DocumentUploadOCR';
import { DatePicker } from '../DatePicker';
import { COMMON_DEED_TYPES } from '../../constants/multiStepFormConstants';
import type { StepComponentProps } from '../../types/multiStepForm';

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
                                suggestions={[...COMMON_DEED_TYPES]}
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
                                    suggestions={[...COMMON_DEED_TYPES]}
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

export default PropertyPlanStep;
export { PropertyPlanStep };
