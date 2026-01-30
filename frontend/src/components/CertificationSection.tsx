import React, { useEffect } from 'react';
import { Award, CheckCircle2 } from 'lucide-react';
import { Label } from './Label';
import { Input } from './Input';
import { Textarea } from './Textarea';
import { User } from '../types';

interface CertificationData {
  certification_text?: string;
  certificate_survey_plan_ref?: string;
  certificate_survey_plan_date?: string;
  certificate_identity_confirmed?: boolean;
  certification_valuer_name?: string;
  certification_valuer_designation?: string;
  certification_date?: string;

  // For reference (from previous steps)
  plan_number?: string;
  plan_date?: string;
  licensed_surveyor_name?: string;
  property_identification_type?: string; // NEW: 'plan', 'deed', 'plan_and_deed', 'certificate_of_sale'
  deeds?: Array<{
    deed_type?: string;
    deed_number?: string;
    deed_date?: string;
  }>;
  certificate_number?: string;
  certificate_date?: string;
}

interface Props {
  data: CertificationData;
  onChange: (data: Partial<CertificationData>) => void;
  userProfile?: User | null;
}

export default function CertificationSection({ data, onChange, userProfile }: Props) {
  // Auto-fill from previous steps and user profile
  useEffect(() => {
    const updates: Partial<CertificationData> = {};

    // Note: certificate_survey_plan_ref/date are deprecated
    // Certificate of Identity now uses plan_number and plan_date directly
    // These fields are kept for backward compatibility only

    // Auto-fill valuer info from user profile
    if (userProfile) {
      if (!data.certification_valuer_name) {
        updates.certification_valuer_name = userProfile.full_name;
      }
      if (!data.certification_valuer_designation && userProfile.professional_designation) {
        updates.certification_valuer_designation = userProfile.professional_designation;
      }
    }

    // Auto-fill current date
    if (!data.certification_date) {
      const today = new Date();
      const formattedDate = today.toISOString().split('T')[0]; // YYYY-MM-DD
      updates.certification_date = formattedDate;
    }

    // Generate simplified certification text if not set - DYNAMIC based on property_identification_type
    if (!data.certification_text) {
      const valuerName = userProfile?.full_name || '[Valuer Name]';
      const designation = userProfile?.professional_designation || '[Designation]';

      // Build property identification text based on document type
      let identificationText = '';
      const idType = data.property_identification_type;

      if (idType === 'plan' || idType === 'plan_and_deed') {
        // Plan information available (ignore deed as per requirements)
        const planRef = data.plan_number || '[Plan Reference]';
        const planDate = data.plan_date || '[Plan Date]';
        const surveyorName = data.licensed_surveyor_name || '[Surveyor Name]';
        const lotNum = data.lot_number;

        // Include lot number if available (new format)
        if (lotNum && lotNum.trim()) {
          identificationText = `the property depicted as Lot ${lotNum} in Plan No ${planRef} dated ${planDate} made by ${surveyorName}, Licensed Surveyor`;
        } else {
          identificationText = `the property depicted as Plan No ${planRef} dated ${planDate} made by ${surveyorName}, Licensed Surveyor`;
        }
      }

      if (idType === 'deed') {
        // Deed only (fallback when no plan available)
        const firstDeed = data.deeds?.[0];
        const deedType = firstDeed?.deed_type || 'Deed';
        const deedNumber = firstDeed?.deed_number || '[Deed Number]';
        const deedDate = firstDeed?.deed_date || '[Deed Date]';
        identificationText = `the property described in ${deedType} No. ${deedNumber} dated ${deedDate}`;
      }

      if (idType === 'certificate_of_sale') {
        // Certificate of sale
        const certNumber = data.certificate_number || '[Certificate Number]';
        const certDate = data.certificate_date || '[Certificate Date]';
        identificationText = `the property described in Certificate of Sale No. ${certNumber} dated ${certDate}`;
      }

      // Fallback if no identification type specified
      if (!identificationText) {
        identificationText = 'the property described in this report';
      }

      // Simplified single-paragraph certification (removed multi-paragraph format)
      updates.certification_text = `I, ${valuerName}, ${designation}, do hereby certify that the property inspected by me and valued above is identical to ${identificationText}.`;
    }

    if (Object.keys(updates).length > 0) {
      onChange(updates);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    userProfile,
    data.lot_number, // NEW: Re-generate when lot number changes
    data.plan_number,
    data.plan_date,
    data.licensed_surveyor_name,
    data.certificate_survey_plan_ref,
    data.certificate_survey_plan_date,
    data.certification_valuer_name,
    data.certification_valuer_designation,
    data.certification_date,
    data.certification_text,
    data.property_identification_type, // NEW: Re-generate when identification type changes
    data.deeds, // NEW: Re-generate when deeds change
    data.certificate_number, // NEW: Re-generate when certificate changes
    data.certificate_date
  ]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 bg-amber-100 rounded-lg">
          <Award className="h-6 w-6 text-amber-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Certification</h2>
          <p className="text-sm text-gray-600 mt-1">
            Professional certification and valuer signature
          </p>
        </div>
      </div>

      {/* Certification Statement */}
      <div>
        <Label>Certification Statement</Label>
        <Textarea
          value={data.certification_text || ''}
          onChange={(e) => onChange({ certification_text: e.target.value })}
          rows={8}
          className="mt-2 font-serif"
          placeholder="Enter certification statement..."
        />
        <p className="text-xs text-gray-500 mt-1">
          This statement will appear in the certification section of the report. Edit as needed to match your requirements.
        </p>
      </div>

      {/* Certificate of Identity - DEPRECATED FIELDS */}
      <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle2 className="h-5 w-5 text-yellow-600" />
          <h3 className="font-semibold text-yellow-900">Certificate of Identity (Deprecated)</h3>
        </div>

        <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-4 mb-4">
          <p className="text-sm text-yellow-800 font-medium mb-2">
            Note: These fields are deprecated
          </p>
          <p className="text-xs text-yellow-700">
            Certificate of Identity now automatically uses Plan Number and Plan Date from the Property Description step.
            These fields are displayed for backward compatibility only and cannot be edited.
          </p>
        </div>

        <div className="bg-white rounded-lg p-4 mb-4 space-y-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-sm text-gray-600">Survey Plan Reference (Read-Only)</Label>
              <Input
                type="text"
                value={data.plan_number || data.certificate_survey_plan_ref || ''}
                disabled
                className="mt-1 bg-gray-100 cursor-not-allowed"
                placeholder="Uses plan_number from Property Description"
              />
              <p className="text-xs text-gray-500 mt-1">
                Value from Property Description: plan_number
              </p>
            </div>

            <div>
              <Label className="text-sm text-gray-600">Survey Plan Date (Read-Only)</Label>
              <Input
                type="text"
                value={data.plan_date || data.certificate_survey_plan_date || ''}
                disabled
                className="mt-1 bg-gray-100 cursor-not-allowed"
                placeholder="Uses plan_date from Property Description"
              />
              <p className="text-xs text-gray-500 mt-1">
                Value from Property Description: plan_date
              </p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 border border-green-300 rounded-lg p-4">
          <p className="text-sm text-green-800">
            <span className="font-semibold">Certificate of Identity is now optional.</span> It will be automatically generated in the report
            if property identification data (plan or deed information) is available.
          </p>
        </div>
      </div>

      {/* Valuer Signature Section */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Valuer Signature</h3>

        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Valuer Name</Label>
              <Input
                type="text"
                value={data.certification_valuer_name || ''}
                onChange={(e) => onChange({ certification_valuer_name: e.target.value })}
                disabled
                className="mt-1 bg-gray-100 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">
                Auto-filled from your profile
              </p>
            </div>

            <div>
              <Label>Professional Designation</Label>
              <Input
                type="text"
                value={data.certification_valuer_designation || ''}
                onChange={(e) => onChange({ certification_valuer_designation: e.target.value })}
                disabled
                className="mt-1 bg-gray-100 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">
                Auto-filled from your profile
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Certification Date</Label>
              <Input
                type="date"
                value={data.certification_date || ''}
                onChange={(e) => onChange({ certification_date: e.target.value })}
                className="mt-1"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Signature Preview Box */}
      <div className="bg-white border-2 border-gray-300 rounded-lg p-6">
        <p className="text-sm text-gray-500 mb-4">Signature Block Preview:</p>
        <div className="space-y-3">
          <div className="border-b border-gray-400 w-64"></div>
          <p className="font-semibold text-gray-900">
            {data.certification_valuer_name || '[Valuer Name]'}
          </p>
          <p className="text-gray-700">
            {data.certification_valuer_designation || '[Professional Designation]'}
          </p>
          <p className="text-gray-700">
            {data.certification_date
              ? new Date(data.certification_date).toLocaleDateString('en-GB', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric'
                })
              : '[Date]'}
          </p>
        </div>
      </div>

      {/* Information Box */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-sm text-amber-800">
          <strong>Note:</strong> Your name and professional designation are auto-filled from your user profile.
          The certification statement can be edited to match specific requirements. The certificate of identity
          checkbox must be confirmed before proceeding.
        </p>
      </div>
    </div>
  );
}
