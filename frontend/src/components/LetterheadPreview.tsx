import React from 'react';
import { Mail, Phone, MapPin, Award, GraduationCap, Building } from 'lucide-react';

interface LetterheadPreviewProps {
  userData: {
    honorific?: string;
    full_name?: string;
    email?: string;
    academic_qualifications?: string;
    membership_level?: string;
    membership_number?: string;
    professional_designation?: string;
    panel_valuer_banks?: string[];

    // Residential Address
    house_number?: string;
    area_development?: string;
    village?: string;
    locality?: string;
    phone_primary?: string;
    phone_secondary?: string;

    // Office Information
    office_department?: string;
    office_region?: string;
    office_street_city?: string;
    office_phone?: string;
  };
  reportRef?: string;
  reportDate?: string;
  templateId?: string; // NEW: Template selection
}

export const LetterheadPreview: React.FC<LetterheadPreviewProps> = ({ userData, reportRef, reportDate, templateId = 'classic' }) => {
  const {
    honorific = '',
    full_name = '',
    email = '',
    academic_qualifications = '',
    membership_level = '',
    membership_number = '',
    professional_designation = '',
    panel_valuer_banks = [],

    house_number = '',
    area_development = '',
    village = '',
    locality = '',
    phone_primary = '',
    phone_secondary = '',

    office_department = '',
    office_region = '',
    office_street_city = '',
    office_phone = ''
  } = userData;

  // Build residential address
  const buildResidentialAddress = () => {
    const parts = [house_number, area_development, village, locality].filter(Boolean);
    return parts.join(', ');
  };

  // Build office address
  const buildOfficeAddress = () => {
    const parts = [office_department, office_region, office_street_city].filter(Boolean);
    return parts.join(', ');
  };

  // Get residential phones only
  const getResidentialPhones = () => {
    const phones = [phone_primary, phone_secondary].filter(Boolean);
    return phones;
  };

  // Format panel valuer banks
  const formatPanelBanks = () => {
    if (!panel_valuer_banks || panel_valuer_banks.length === 0) return '';
    if (panel_valuer_banks.length === 1) return panel_valuer_banks[0];
    if (panel_valuer_banks.length === 2) return panel_valuer_banks.join(' & ');
    return `${panel_valuer_banks.slice(0, -1).join(', ')} & ${panel_valuer_banks[panel_valuer_banks.length - 1]}`;
  };

  const residentialAddress = buildResidentialAddress();
  const officeAddress = buildOfficeAddress();
  const residentialPhones = getResidentialPhones();
  const panelBanksText = formatPanelBanks();

  // Determine which template to show
  const getTemplateName = () => {
    const templateNames: { [key: string]: string } = {
      'classic': 'Classic Professional',
      'modern': 'Modern Professional',
      'minimal': 'Minimal Elegant',
      'executive': 'Executive Bold',
      'compact': 'Compact Professional',
      'premium': 'Premium Signature',
    };
    return templateNames[templateId] || 'Classic Professional';
  };

  return (
    <div className="bg-white border-2 border-gray-200 rounded-lg p-6 shadow-lg">
      {/* Header */}
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">Letterhead Preview</h3>
        <p className="text-sm text-blue-600">{getTemplateName()}</p>
        <div className="w-full h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent mt-2"></div>
      </div>

      {/* Letterhead Content */}
      <div className="border-2 border-gray-800 p-3 bg-white" style={{ minHeight: '200px' }}>
        {/* Render template based on templateId - default to classic */}
        {templateId === 'classic' && (
          <>
            {/* Professional Name & Title */}
            <div className="text-center border-b border-gray-800 pb-1 mb-1">
              <h1 className="text-sm font-bold text-black mb-0.5" style={{ fontSize: '11pt' }}>
                {honorific && `${honorific} `}{full_name || <span className="text-gray-400">Your Full Name</span>}
              </h1>

              {/* Academic Qualifications */}
              {academic_qualifications && (
                <p className="text-black mb-0.5" style={{ fontSize: '8pt' }}>
                  {academic_qualifications}
                </p>
              )}

              {/* Professional Designation */}
              {professional_designation && (
                <p className="font-semibold text-black mb-0.5" style={{ fontSize: '9pt' }}>
                  {professional_designation}
                </p>
              )}

              {/* Membership Information */}
              <div className="flex items-center justify-center gap-2 text-black mb-0.5" style={{ fontSize: '7pt' }}>
                {membership_level && (
                  <div className="flex items-center gap-0.5">
                    <Award size={10} />
                    <span>{membership_level}</span>
                  </div>
                )}
                {membership_number && (
                  <div className="flex items-center gap-0.5">
                    <Building size={10} />
                    <span>{membership_number}</span>
                  </div>
                )}
              </div>

              {/* Panel Valuer Status */}
              {panelBanksText && (
                <p className="text-black" style={{ fontSize: '7pt' }}>
                  <strong>Panel Valuer:</strong> {panelBanksText}
                </p>
              )}
            </div>

            {/* Contact Information Section */}
            <div className="grid md:grid-cols-2 gap-2 text-black" style={{ fontSize: '7pt' }}>
              {/* Residence */}
              <div>
                <h3 className="font-bold text-black mb-0.5">
                  RESIDENCE
                </h3>
                {residentialAddress ? (
                  <div className="flex items-start gap-0.5 text-black">
                    <MapPin size={8} className="mt-0.5 flex-shrink-0" />
                    <span>{residentialAddress}</span>
                  </div>
                ) : (
                  <p className="text-gray-400 italic" style={{ fontSize: '7pt' }}>Residential address will appear here</p>
                )}

                {residentialPhones.length > 0 && (
                  <div className="mt-0.5 space-y-0.5">
                    {residentialPhones.map((phone, index) => (
                      <div key={index} className="flex items-center gap-0.5 text-black">
                        <Phone size={8} />
                        <span>{phone}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Office */}
              <div>
                <h3 className="font-bold text-black mb-0.5">
                  OFFICE
                </h3>
                {officeAddress ? (
                  <div className="flex items-start gap-0.5 text-black">
                    <Building size={8} className="mt-0.5 flex-shrink-0" />
                    <span>{officeAddress}</span>
                  </div>
                ) : (
                  <p className="text-gray-400 italic" style={{ fontSize: '7pt' }}>Office address will appear here</p>
                )}

                {office_phone && (
                  <div className="flex items-center gap-0.5 text-black mt-0.5">
                    <Phone size={8} />
                    <span>{office_phone}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Email */}
            {email && (
              <div className="mt-1 pt-1 border-t border-gray-800">
                <div className="flex items-center justify-center gap-0.5 text-black" style={{ fontSize: '7pt' }}>
                  <Mail size={8} />
                  <span className="underline">{email}</span>
                </div>
              </div>
            )}

            {/* Report Reference Line */}
            <div className="mt-1 pt-1 border-t border-gray-800">
              <div className="flex justify-between items-center text-black" style={{ fontSize: '8pt' }}>
                {reportRef ? (
                  <div>
                    <strong>Ref:</strong> <span className="text-black">{reportRef}</span>
                  </div>
                ) : (
                  <div>
                    <strong>Ref:</strong> <span className="text-gray-400 italic">Enter your reference number</span>
                  </div>
                )}
                <div>
                  <strong>Date:</strong> <span className="text-black">{reportDate || new Date().toLocaleDateString('en-GB')}</span>
                </div>
              </div>
            </div>

            {/* Placeholder for letter content */}
            <div className="mt-2 p-2 border border-dashed border-gray-300 rounded">
              <p className="text-center text-gray-400 italic" style={{ fontSize: '8pt' }}>
                Your professional report content will appear here
              </p>
            </div>
          </>
        )}

        {/* Note: Other templates render with simplified preview for now */}
        {templateId !== 'classic' && (
          <div className="text-center p-4">
            <p className="text-gray-600">
              Preview of <strong>{getTemplateName()}</strong> template.
            </p>
            <p className="text-sm text-gray-500 mt-2">
              The full template will be applied when you generate your report.
            </p>
          </div>
        )}
      </div>

      {/* Preview Notes */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-xs text-gray-600 text-center">
          ✨ This preview updates in real-time as you fill the form above
        </p>
      </div>
    </div>
  );
};