/**
 * AdditionalDetailsStep - Reusable component for collecting submission destination, inspection date, and report metadata
 *
 * Extracted from MultiStepForm Step 10 to enable reuse in:
 * - Existing residential/bare land forms (Step 10)
 * - New multi-property redesigned flow (Step 2)
 *
 * This component collects shared data that applies to ALL properties in a multi-property report.
 */

import React from 'react';
import { UseFormRegister, FieldErrors, UseFormWatch, UseFormSetValue } from 'react-hook-form';
import { Building, FileText } from 'lucide-react';
import { Input } from './Input';
import { Label } from './Label';
import { DatePicker } from './DatePicker';

interface AdditionalDetailsStepProps {
    register: UseFormRegister<any>;
    errors: FieldErrors<any>;
    watch: UseFormWatch<any>;
    setValue: UseFormSetValue<any>;
}

export const AdditionalDetailsStep: React.FC<AdditionalDetailsStepProps> = ({
    register,
    errors,
    watch,
    setValue
}) => {
    const hasSpecialNote = watch('has_special_note');

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
