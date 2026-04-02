import React from 'react';
import { CheckCircle2, FileText, Home, Award } from 'lucide-react';
import { Input } from '../Input';
import { Label } from '../Label';
import { AutocompleteInput } from '../AutocompleteInput';
import { DatePicker } from '../DatePicker';
import { COMMON_DEED_TYPES } from '../../constants/multiStepFormConstants';

interface PropertyPlanFieldsProps {
    register: any;
    errors: any;
    watch: any;
    setValue: any;
    ocrFilledFields?: Set<string>;
}

export const PropertyPlanFields: React.FC<PropertyPlanFieldsProps> = ({
    register,
    errors,
    watch,
    setValue,
    ocrFilledFields,
}) => {
    const identificationType = watch('property_identification_type');

    const ocr = (field: string) =>
        ocrFilledFields?.has(field) ? ' bg-blue-50 border-blue-200' : '';

    return (
        <div className="space-y-6">
            {/* Property Identification Type - Selection Cards */}
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
                            <div className={`p-3 rounded-xl ${identificationType === 'plan' ? 'bg-blue-500' : 'bg-gray-100'}`}>
                                <Home className={`h-6 w-6 ${identificationType === 'plan' ? 'text-white' : 'text-gray-600'}`} />
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
                            <div className={`p-3 rounded-xl ${identificationType === 'deed' ? 'bg-green-500' : 'bg-gray-100'}`}>
                                <FileText className={`h-6 w-6 ${identificationType === 'deed' ? 'text-white' : 'text-gray-600'}`} />
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

                    {/* Card 3: Survey Plan + Deed (HYBRID) */}
                    <div
                        onClick={() => setValue('property_identification_type', 'plan_and_deed', { shouldValidate: true })}
                        className={`cursor-pointer border-2 rounded-2xl p-6 transition-all duration-200 transform hover:scale-[1.02] relative ${identificationType === 'plan_and_deed'
                                ? 'border-purple-500 bg-purple-50 shadow-lg ring-2 ring-purple-200'
                                : 'border-gray-200 bg-white hover:border-purple-300 hover:shadow-md'
                            }`}
                    >
                        <div className="flex items-start gap-4">
                            <div className={`p-3 rounded-xl ${identificationType === 'plan_and_deed' ? 'bg-purple-500' : 'bg-gray-100'}`}>
                                <div className="flex gap-1">
                                    <Home className={`h-5 w-5 ${identificationType === 'plan_and_deed' ? 'text-white' : 'text-gray-600'}`} />
                                    <FileText className={`h-5 w-5 ${identificationType === 'plan_and_deed' ? 'text-white' : 'text-gray-600'}`} />
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
                            <div className={`p-3 rounded-xl ${identificationType === 'certificate_of_sale' ? 'bg-orange-500' : 'bg-gray-100'}`}>
                                <Award className={`h-6 w-6 ${identificationType === 'certificate_of_sale' ? 'text-white' : 'text-gray-600'}`} />
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
                                className={`pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('lot_number')}`}
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
                                className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('plan_number')}`}
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
                                className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('plan_date')}`}
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
                            className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('licensed_surveyor_name')}`}
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
                                className={`w-full${ocr('deed_type')}`}
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
                                className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('deed_number')}`}
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
                                className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('deed_date')}`}
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
                                className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('notary_name')}`}
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
                                className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('notary_location')}`}
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

            {/* HYBRID MODE: Both Plan and Deed fields */}
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
                                    className={`pl-12 h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('lot_number')}`}
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
                                    className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('plan_number')}`}
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
                                    className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('plan_date')}`}
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
                                className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200${ocr('licensed_surveyor_name')}`}
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
                                    className={`w-full${ocr('deed_type')}`}
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
                                    className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('deed_number')}`}
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
                                    className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('deed_date')}`}
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
                                    className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('notary_name')}`}
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
                                    className={`h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-200${ocr('notary_location')}`}
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

export default PropertyPlanFields;
