import React from 'react';
import { Check } from 'lucide-react';

interface LetterheadTemplatePreviewProps {
  templateId: string;
  templateName: string;
  templateDescription: string;
  userData: any;
  isSelected: boolean;
  onClick: () => void;
}

export const LetterheadTemplatePreview: React.FC<LetterheadTemplatePreviewProps> = ({
  templateId,
  templateName,
  templateDescription,
  userData,
  isSelected,
  onClick,
}) => {
  // Build address parts for preview
  const buildResidentialAddress = () => {
    const parts = [
      userData.house_number,
      userData.area_development,
      userData.village,
      userData.locality
    ].filter(Boolean);
    return parts.join(', ');
  };

  const residentialAddress = buildResidentialAddress();
  const phones = [userData.phone_primary, userData.phone_secondary].filter(Boolean);

  return (
    <div
      onClick={onClick}
      className={`relative cursor-pointer rounded-lg border-2 transition-all hover:shadow-lg ${
        isSelected
          ? 'border-blue-500 bg-blue-50 shadow-md'
          : 'border-gray-300 bg-white hover:border-gray-400'
      }`}
    >
      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 z-10 flex items-center justify-center w-6 h-6 bg-blue-500 rounded-full">
          <Check className="w-4 h-4 text-white" />
        </div>
      )}

      {/* Template name badge */}
      <div className="px-4 py-2 bg-gray-100 rounded-t-lg border-b">
        <h3 className="text-sm font-semibold text-gray-800">{templateName}</h3>
        <p className="text-xs text-gray-600 mt-0.5">{templateDescription}</p>
      </div>

      {/* Template preview (scaled down) */}
      <div className="p-4">
        <div
          className="bg-white border border-gray-300 p-3"
          style={{ transform: 'scale(0.85)', transformOrigin: 'top left', width: '117%' }}
        >
          {/* Render template-specific layout */}
          {templateId === 'classic' && renderClassicPreview(userData, residentialAddress, phones)}
          {templateId === 'modern' && renderModernPreview(userData, residentialAddress, phones)}
          {templateId === 'minimal' && renderMinimalPreview(userData, residentialAddress, phones)}
          {templateId === 'executive' && renderExecutivePreview(userData, residentialAddress, phones)}
          {templateId === 'compact' && renderCompactPreview(userData, residentialAddress, phones)}
          {templateId === 'premium' && renderPremiumPreview(userData, residentialAddress, phones)}
        </div>
      </div>
    </div>
  );
};

// Template-specific preview renderers
function renderClassicPreview(userData: any, residentialAddress: string, phones: string[]) {
  return (
    <div className="space-y-1">
      {/* Centered header */}
      <div className="text-center border-b border-gray-800 pb-1">
        <div className="font-bold" style={{ fontSize: '9pt' }}>
          {userData.honorific && `${userData.honorific} `}{userData.full_name || 'Your Name'}
        </div>
        {userData.academic_qualifications && (
          <div style={{ fontSize: '7pt' }}>{userData.academic_qualifications}</div>
        )}
        {userData.professional_designation && (
          <div className="font-semibold" style={{ fontSize: '8pt' }}>{userData.professional_designation}</div>
        )}
      </div>
      {/* Two-column contact */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <div className="font-bold" style={{ fontSize: '6pt' }}>RESIDENCE</div>
          {residentialAddress && <div style={{ fontSize: '6pt' }}>{residentialAddress}</div>}
        </div>
        <div>
          <div className="font-bold" style={{ fontSize: '6pt' }}>OFFICE</div>
          {userData.office_department && <div style={{ fontSize: '6pt' }}>{userData.office_department}</div>}
        </div>
      </div>
      {/* Email */}
      {userData.email && (
        <div className="text-center border-t border-gray-800 pt-1">
          <div style={{ fontSize: '6pt' }}>{userData.email}</div>
        </div>
      )}
    </div>
  );
}

function renderModernPreview(userData: any, residentialAddress: string, phones: string[]) {
  return (
    <div className="space-y-1">
      {/* Top border */}
      <div className="border-t-2 border-gray-800 mb-2"></div>
      {/* Left-aligned header */}
      <div className="text-left">
        <div className="font-bold" style={{ fontSize: '9pt' }}>
          {userData.honorific && `${userData.honorific} `}{userData.full_name || 'Your Name'}
        </div>
        {userData.professional_designation && (
          <div className="font-semibold" style={{ fontSize: '7pt' }}>{userData.professional_designation}</div>
        )}
      </div>
      {/* Horizontal contact */}
      <div className="text-left" style={{ fontSize: '6pt' }}>
        {residentialAddress && <span>{residentialAddress}</span>}
        {userData.email && <span> | {userData.email}</span>}
      </div>
      <div className="border-b border-gray-800"></div>
    </div>
  );
}

function renderMinimalPreview(userData: any, residentialAddress: string, phones: string[]) {
  return (
    <div className="space-y-2">
      {/* Centered name */}
      <div className="text-center">
        <div className="font-bold" style={{ fontSize: '10pt' }}>
          {userData.honorific && `${userData.honorific} `}{userData.full_name || 'Your Name'}
        </div>
        {userData.professional_designation && (
          <div style={{ fontSize: '8pt' }}>{userData.professional_designation}</div>
        )}
      </div>
      {/* Spacer */}
      <div className="py-2"></div>
      {/* Compact footer */}
      <div className="text-center text-gray-600" style={{ fontSize: '6pt' }}>
        {[userData.email, phones[0], userData.locality].filter(Boolean).join(' | ')}
      </div>
    </div>
  );
}

function renderExecutivePreview(userData: any, residentialAddress: string, phones: string[]) {
  return (
    <div className="space-y-1">
      {/* Double border top */}
      <div className="border-t-2 border-gray-800"></div>
      <div className="border-t border-gray-800 mb-2"></div>
      {/* Centered bold header */}
      <div className="text-center">
        <div className="font-bold" style={{ fontSize: '11pt' }}>
          {userData.honorific && `${userData.honorific} `}{userData.full_name || 'Your Name'}
        </div>
        {userData.professional_designation && (
          <div className="font-bold" style={{ fontSize: '8pt' }}>{userData.professional_designation}</div>
        )}
      </div>
      {/* Contact line */}
      <div className="text-center" style={{ fontSize: '6pt' }}>
        {[userData.locality, userData.email].filter(Boolean).join(' | ')}
      </div>
      {/* Double border bottom */}
      <div className="border-b border-gray-800 mt-2"></div>
      <div className="border-b-2 border-gray-800"></div>
    </div>
  );
}

function renderCompactPreview(userData: any, residentialAddress: string, phones: string[]) {
  return (
    <div className="space-y-0.5">
      {/* Compact centered header */}
      <div className="text-center border-b border-gray-800 pb-0.5">
        <div className="font-bold" style={{ fontSize: '7pt' }}>
          {userData.honorific && `${userData.honorific} `}{userData.full_name || 'Your Name'}
        </div>
        {userData.professional_designation && (
          <div className="font-semibold" style={{ fontSize: '6pt' }}>{userData.professional_designation}</div>
        )}
      </div>
      {/* Tiny contact section */}
      <div className="grid grid-cols-2 gap-1">
        <div style={{ fontSize: '5pt' }}>
          <div className="font-bold">RES</div>
          {userData.locality && <div>{userData.locality}</div>}
        </div>
        <div style={{ fontSize: '5pt' }}>
          <div className="font-bold">OFF</div>
          {userData.office_department && <div>{userData.office_department}</div>}
        </div>
      </div>
      {userData.email && (
        <div className="text-center border-t border-gray-800 pt-0.5" style={{ fontSize: '5pt' }}>
          {userData.email}
        </div>
      )}
    </div>
  );
}

function renderPremiumPreview(userData: any, residentialAddress: string, phones: string[]) {
  return (
    <div className="space-y-1">
      {/* Thick top border */}
      <div className="border-t-2 border-gray-800 mb-2"></div>
      {/* Left-aligned name */}
      <div className="text-left">
        <div className="font-bold" style={{ fontSize: '10pt' }}>
          {userData.honorific && `${userData.honorific} `}{userData.full_name || 'Your Name'}
        </div>
        {userData.professional_designation && (
          <div className="font-semibold" style={{ fontSize: '8pt' }}>{userData.professional_designation}</div>
        )}
      </div>
      {/* Stacked contact with bullets */}
      <div className="text-left space-y-0.5 pl-2" style={{ fontSize: '6pt' }}>
        {userData.membership_level && <div>• {userData.membership_level}</div>}
        {residentialAddress && <div>• Residence: {residentialAddress}</div>}
        {userData.email && <div>• Email: {userData.email}</div>}
      </div>
      {/* Thin bottom border */}
      <div className="border-b border-gray-800 mt-2"></div>
    </div>
  );
}
