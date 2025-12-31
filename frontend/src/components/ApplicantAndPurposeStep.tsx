/**
 * ApplicantAndPurposeStep - Reusable component for collecting applicant details and valuation purpose
 *
 * Extracted from MultiStepForm Step 9 to enable reuse in:
 * - Existing residential/bare land forms (Step 9)
 * - New multi-property redesigned flow (Step 1)
 *
 * This component collects shared data that applies to ALL properties in a multi-property report.
 */

import React, { useEffect } from 'react';
import { UseFormRegister, FieldErrors, UseFormWatch, UseFormSetValue } from 'react-hook-form';
import { MapPin, User } from 'lucide-react';
import { Input } from './Input';
import { Label } from './Label';
import toast from 'react-hot-toast';
import { validateSriLankanNIC, validatePassport, useFieldValidation } from '../utils/validators';

interface ApplicantAndPurposeStepProps {
    register: UseFormRegister<any>;
    errors: FieldErrors<any>;
    watch: UseFormWatch<any>;
    setValue: UseFormSetValue<any>;
}

export const ApplicantAndPurposeStep: React.FC<ApplicantAndPurposeStepProps> = ({
    register,
    errors,
    watch,
    setValue
}) => {
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
                        ID Type *
                    </Label>
                    <select
                        id="applicant_id_type"
                        className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 px-4"
                        {...register('applicant_id_type')}
                    >
                        <option value="">Select ID type</option>
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
                        ID Number *
                    </Label>
                    <Input
                        id="applicant_id_number"
                        type="text"
                        placeholder={
                            idType === 'NIC'
                                ? 'e.g., 912345678V or 199212345678'
                                : idType === 'Passport'
                                    ? 'e.g., N1234567'
                                    : 'ID number'
                        }
                        className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
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

                <div className="space-y-2 mt-4">
                    <Label htmlFor="valuation_purpose" className="text-gray-700 font-medium">
                        Purpose of Valuation *
                    </Label>
                    <select
                        id="valuation_purpose"
                        className="w-full h-14 bg-white/50 border border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 px-4"
                        {...register('valuation_purpose')}
                    >
                        <option value="">Select purpose...</option>
                        <option value="Bank Loan / Mortgage">Bank Loan / Mortgage</option>
                        <option value="Sale / Purchase">Sale / Purchase</option>
                        <option value="Legal Proceedings / Court Case">Legal Proceedings / Court Case</option>
                        <option value="Insurance">Insurance</option>
                        <option value="Partition">Partition</option>
                        <option value="Mortgage Refinancing">Mortgage Refinancing</option>
                        <option value="Taxation / Estate Duty">Taxation / Estate Duty</option>
                        <option value="Investment Analysis">Investment Analysis</option>
                        <option value="Court-Ordered Valuation">Court-Ordered Valuation</option>
                    </select>
                    {errors.valuation_purpose && (
                        <p className="text-red-500 text-sm">{errors.valuation_purpose.message}</p>
                    )}
                    <p className="text-sm text-gray-500 mt-1">
                        Or type a custom purpose: <Input
                            type="text"
                            placeholder="Type custom purpose..."
                            className="mt-2 h-12 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                            onBlur={(e) => {
                                if (e.target.value) {
                                    setValue('valuation_purpose', e.target.value, { shouldValidate: true });
                                }
                            }}
                        />
                    </p>
                </div>

                <div className="space-y-2 mt-4">
                    <Label htmlFor="property_ownership" className="text-gray-700 font-medium">
                        Property Ownership <span className="text-gray-400">(Optional, auto-generated if left blank)</span>
                    </Label>
                    <Input
                        id="property_ownership"
                        type="text"
                        placeholder="e.g., owned by him, owned by her"
                        className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                        {...register('property_ownership')}
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
                            Additional Owner Names *
                        </Label>
                        <Input
                            id="additional_owner_names"
                            type="text"
                            placeholder="Enter additional owner names"
                            className="h-14 bg-white/50 border-gray-200/50 rounded-2xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200"
                            {...register('additional_owner_names')}
                        />
                        {errors.additional_owner_names && (
                            <p className="text-red-500 text-sm">{errors.additional_owner_names.message}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
