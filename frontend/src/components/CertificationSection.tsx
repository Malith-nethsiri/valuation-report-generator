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
  property_name?: string;
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

    // Auto-fill plan reference from Step 1
    if (data.plan_number && !data.certificate_survey_plan_ref) {
      updates.certificate_survey_plan_ref = data.plan_number;
    }

    // Auto-fill plan date from Step 1
    if (data.plan_date && !data.certificate_survey_plan_date) {
      updates.certificate_survey_plan_date = data.plan_date;
    }

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

    // Generate default certification text if not set - DYNAMIC based on property_identification_type
    if (!data.certification_text) {
      const valuerName = userProfile?.full_name || '[Valuer Name]';
      const designation = userProfile?.professional_designation || '[Designation]';

      // Build property identification text based on document type
      let identificationText = '';
      const idType = data.property_identification_type;

      if (idType === 'plan' || idType === 'plan_and_deed') {
        // Plan information available
        const planRef = data.plan_number || '[Plan Reference]';
        const planDate = data.plan_date || '[Plan Date]';
        const surveyorName = data.licensed_surveyor_name || '[Surveyor Name]';
        identificationText = `the land depicted as Plan ${planRef} dated ${planDate} made by ${surveyorName}, Licensed Surveyor`;
      }

      if (idType === 'deed') {
        // Deed only
        const firstDeed = data.deeds?.[0];
        const deedType = firstDeed?.deed_type || 'Deed';
        const deedNumber = firstDeed?.deed_number || '[Deed Number]';
        const deedDate = firstDeed?.deed_date || '[Deed Date]';
        identificationText = `the property described in ${deedType} No. ${deedNumber} dated ${deedDate}`;
      }

      if (idType === 'plan_and_deed') {
        // Both plan and deed
        const planRef = data.plan_number || '[Plan Reference]';
        const firstDeed = data.deeds?.[0];
        const deedType = firstDeed?.deed_type || 'Deed';
        const deedNumber = firstDeed?.deed_number || '[Deed Number]';
        identificationText = `the land depicted as Plan ${planRef} and described in ${deedType} No. ${deedNumber}`;
      }

      if (idType === 'certificate_of_sale') {
        // Certificate of sale
        const certNumber = data.certificate_number || '[Certificate Number]';
        const certDate = data.certificate_date || '[Certificate Date]';
        identificationText = `the property described in Certificate of Sale No. ${certNumber} dated ${certDate}`;
      }

      // Fallback if no identification type specified
      if (!identificationText) {
        identificationText = 'the property as described in the relevant legal documents';
      }

      updates.certification_text = `I, ${valuerName}, ${designation}, do hereby certify that the property inspected by me and valued above is identical to ${identificationText}.

I further certify that the property has legal, motorable access at all times.

In view of the above analysis, I am of the opinion that the values of the said property at the time of inspection subject to clear title and vacant possession are as above.`;
    }

    if (Object.keys(updates).length > 0) {
      onChange(updates);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    userProfile,
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

      {/* Certificate of Identity */}
      <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <CheckCircle2 className="h-5 w-5 text-blue-600" />
          <h3 className="font-semibold text-blue-900">Certificate of Identity</h3>
        </div>

        <div className="bg-white rounded-lg p-4 mb-4 space-y-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-sm">Survey Plan Reference</Label>
              <Input
                type="text"
                value={data.certificate_survey_plan_ref || ''}
                onChange={(e) => onChange({ certificate_survey_plan_ref: e.target.value })}
                className="mt-1 bg-gray-50"
                placeholder="e.g., Plan 1035"
              />
            </div>

            <div>
              <Label className="text-sm">Survey Plan Date</Label>
              <Input
                type="text"
                value={data.certificate_survey_plan_date || ''}
                onChange={(e) => onChange({ certificate_survey_plan_date: e.target.value })}
                className="mt-1 bg-gray-50"
                placeholder="e.g., 15-01-2024"
              />
            </div>
          </div>
        </div>

        {/* Required Checkbox */}
        <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={data.certificate_identity_confirmed || false}
              onChange={(e) => onChange({ certificate_identity_confirmed: e.target.checked })}
              className="mt-1 h-5 w-5 text-blue-600 focus:ring-2 focus:ring-blue-500 rounded border-gray-300"
            />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                I certify that the inspected property is identical to the survey plan reference above
              </p>
              <p className="text-xs text-gray-600 mt-1">
                This confirmation is required before proceeding to the next step
              </p>
            </div>
          </label>
          {!data.certificate_identity_confirmed && (
            <p className="text-xs text-red-600 mt-3 flex items-center gap-1">
              <span className="font-semibold">⚠</span>
              Please confirm the certificate of identity to proceed
            </p>
          )}
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
