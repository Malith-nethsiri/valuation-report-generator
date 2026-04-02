/**
 * VehicleBasicInfoStep - Step 1 of Vehicle Report Form
 *
 * Collects:
 * - Purpose of Valuation
 * - Requested By (Name, Title)
 * - Report Date
 * - Inspection Date
 * - Folio Number
 * - Inspection Place
 */

import React from 'react';
import { useFormContext } from 'react-hook-form';
import { User, Calendar, FileText, MapPin } from 'lucide-react';
import { Input } from '../Input';
import { Label } from '../Label';
import { VALUATION_PURPOSE_OPTIONS } from '../../types';

export const VehicleBasicInfoStep: React.FC = () => {
  const { register, formState: { errors }, watch, setValue } = useFormContext();

  return (
    <div className="space-y-6">
      {/* Purpose of Valuation */}
      <div className="space-y-2">
        <Label htmlFor="valuation_purpose" className="text-gray-700 font-medium flex items-center gap-2">
          <FileText className="w-4 h-4" />
          Purpose of Valuation *
        </Label>
        <select
          id="valuation_purpose"
          className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
          {...register('valuation_purpose', { required: 'Purpose is required' })}
        >
          <option value="">Select purpose</option>
          {VALUATION_PURPOSE_OPTIONS.map((purpose) => (
            <option key={purpose} value={purpose}>
              {purpose}
            </option>
          ))}
          <option value="Other">Other (specify in notes)</option>
        </select>
        {errors.valuation_purpose && (
          <p className="text-red-500 text-sm">{errors.valuation_purpose.message as string}</p>
        )}
      </div>

      {/* Requested By */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="applicant_title" className="text-gray-700 font-medium flex items-center gap-2">
            <User className="w-4 h-4" />
            Title
          </Label>
          <select
            id="applicant_title"
            className="w-full h-12 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all px-4"
            {...register('applicant_title')}
          >
            <option value="">Select title</option>
            <option value="Mr.">Mr.</option>
            <option value="Mrs.">Mrs.</option>
            <option value="Miss.">Miss.</option>
            <option value="Ms.">Ms.</option>
            <option value="Dr.">Dr.</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="applicant_full_name" className="text-gray-700 font-medium">
            Requested By (Name/Organization) *
          </Label>
          <Input
            id="applicant_full_name"
            type="text"
            placeholder="Enter name or organization"
            className="h-12"
            {...register('applicant_full_name', { required: 'Requested by is required' })}
          />
          {errors.applicant_full_name && (
            <p className="text-red-500 text-sm">{errors.applicant_full_name.message as string}</p>
          )}
        </div>
      </div>

      {/* Dates */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="report_date" className="text-gray-700 font-medium flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Report Date *
          </Label>
          <Input
            id="report_date"
            type="date"
            min="1900-01-01"
            max="2100-12-31"
            className="h-12"
            {...register('report_date', {
              required: 'Report date is required',
              validate: (value) => {
                if (!value) return true;
                const year = parseInt(value.split('-')[0], 10);
                if (isNaN(year) || year < 1900 || year > 2100) return 'Year must be between 1900 and 2100';
                return true;
              },
            })}
          />
          {errors.report_date && (
            <p className="text-red-500 text-sm">{errors.report_date.message as string}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="inspection_date" className="text-gray-700 font-medium flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Inspection Date *
          </Label>
          <Input
            id="inspection_date"
            type="date"
            min="1900-01-01"
            max="2100-12-31"
            className="h-12"
            {...register('inspection_date', {
              required: 'Inspection date is required',
              validate: (value) => {
                if (!value) return true;
                const year = parseInt(value.split('-')[0], 10);
                if (isNaN(year) || year < 1900 || year > 2100) return 'Year must be between 1900 and 2100';
                return true;
              },
            })}
          />
          {errors.inspection_date && (
            <p className="text-red-500 text-sm">{errors.inspection_date.message as string}</p>
          )}
        </div>
      </div>

      {/* Folio Number and Inspection Place */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="folio_number" className="text-gray-700 font-medium">
            Folio Number
          </Label>
          <Input
            id="folio_number"
            type="text"
            placeholder="Enter folio number"
            className="h-12"
            {...register('folio_number')}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="inspection_place" className="text-gray-700 font-medium flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Inspection Place
          </Label>
          <Input
            id="inspection_place"
            type="text"
            placeholder="Where was the vehicle inspected?"
            className="h-12"
            {...register('inspection_place')}
          />
        </div>
      </div>

      {/* Office/Private Toggle */}
      <div className="p-4 bg-gray-50 rounded-xl">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            className="w-5 h-5 rounded border-gray-300 text-emerald-500 focus:ring-emerald-500"
            {...register('is_office_use')}
          />
          <div>
            <span className="font-medium text-gray-700">Office/Government Report</span>
            <p className="text-sm text-gray-500">
              Check this if this is an official government or military vehicle assessment
            </p>
          </div>
        </label>
      </div>
    </div>
  );
};

export default VehicleBasicInfoStep;
