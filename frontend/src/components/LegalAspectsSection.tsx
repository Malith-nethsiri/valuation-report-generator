import React, { useState } from 'react';
import { Gavel, ChevronDown, ChevronRight } from 'lucide-react';
import { AutocompleteInput } from './AutocompleteInput';
import { Textarea } from './Textarea';
import { Label } from './Label';

interface LegalAspectsData {
  // Basic fields
  ownership_type?: string;
  street_lines_status?: string;
  building_limits_status?: string;
  local_authority_data?: string;
  rent_act_effectiveness?: string;

  // Extended fields - Ownership & Title
  title_search_conducted?: string;
  pedigree_search_conducted?: string;
  valuation_basis_note?: string;
  property_encumbered?: string;
  encumbrance_type?: string;
  encumbrance_details?: string;

  // Extended fields - Street Lines
  street_lines_gazette_ref?: string;
  street_lines_gazette_date?: string;
  street_lines_impact_description?: string;

  // Extended fields - Building Limits
  building_distance_from_road?: string;
  building_plan_approved?: string;
  building_plan_reference?: string;
  building_approval_authority?: string;
  building_within_limits?: string;

  // Extended fields - Local Authority
  local_authority_rated?: string;
  local_authority_tax_levy?: string;
}

interface Props {
  data: LegalAspectsData;
  onChange: (data: Partial<LegalAspectsData>) => void;
}

// Dropdown options
const OWNERSHIP_TYPE_OPTIONS = [
  'Freehold',
  'Leasehold',
  'Life interest',
  'Government land',
  'State land',
  'Crown land'
];

const YES_NO_OPTIONS = ['Yes', 'No'];

const ENCUMBRANCE_TYPE_OPTIONS = [
  'None',
  'Mortgage',
  'Life Interest',
  'Lease',
  'Other'
];

const STREET_LINES_OPTIONS = [
  'Not affected',
  'Affected',
  'Partially affected',
  'Not applicable'
];

const BUILDING_LIMITS_OPTIONS = [
  'Not affected',
  'Affected',
  'Subject to approval',
  'Within limits',
  'Not applicable'
];

const BUILDING_APPROVAL_OPTIONS = [
  'Yes',
  'No',
  'Not Applicable'
];

const RENT_ACT_OPTIONS = [
  'Not affected',
  'Subject to Rent Act No. 7 of 1972',
  'Subject to Rent Act Amendment No. 26 of 2002',
  'Partially affected'
];

// Collapsible Subsection Component
interface SubsectionProps {
  title: string;
  description: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function Subsection({ title, description, isOpen, onToggle, children }: SubsectionProps) {
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex-1 text-left">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600 mt-0.5">{description}</p>
        </div>
        {isOpen ? (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="p-6 bg-white space-y-4">
          {children}
        </div>
      )}
    </div>
  );
}

export default function LegalAspectsSection({ data, onChange }: Props) {
  // State to track which subsections are open (all open by default for better UX)
  const [openSections, setOpenSections] = useState({
    ownership: true,
    streetLines: true,
    buildingLimits: true,
    localAuthority: true,
    rentAct: true
  });

  const toggleSection = (section: keyof typeof openSections) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 bg-purple-100 rounded-lg">
          <Gavel className="h-6 w-6 text-purple-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Legal Aspects</h2>
          <p className="text-sm text-gray-600 mt-1">
            Ownership, title, restrictions, and legal status of the property
          </p>
        </div>
      </div>

      {/* Information Box */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <p className="text-sm text-purple-800">
          <strong>Note:</strong> All fields are optional. The report will generate professional
          paragraphs based on the data you provide. More detailed information results in more
          comprehensive legal aspects descriptions.
        </p>
      </div>

      {/* ===== SUBSECTION 1: OWNERSHIP & TITLE ===== */}
      <Subsection
        title="(a). Ownership & Title"
        description="Property ownership, deed details, and title search information"
        isOpen={openSections.ownership}
        onToggle={() => toggleSection('ownership')}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Ownership Type */}
          <AutocompleteInput
            label="Ownership Type"
            value={data.ownership_type || ''}
            onChange={(value) => onChange({ ownership_type: value })}
            suggestions={OWNERSHIP_TYPE_OPTIONS}
            placeholder="Select ownership type"
            allowCustom={true}
          />

          {/* Title Search Conducted */}
          <AutocompleteInput
            label="Title Search Conducted?"
            value={data.title_search_conducted || ''}
            onChange={(value) => onChange({ title_search_conducted: value })}
            suggestions={YES_NO_OPTIONS}
            placeholder="Select Yes or No"
            allowCustom={false}
          />

          {/* Pedigree Search Conducted */}
          <AutocompleteInput
            label="Pedigree Search Conducted?"
            value={data.pedigree_search_conducted || ''}
            onChange={(value) => onChange({ pedigree_search_conducted: value })}
            suggestions={YES_NO_OPTIONS}
            placeholder="Select Yes or No"
            allowCustom={false}
          />

          {/* Property Encumbered */}
          <AutocompleteInput
            label="Property Encumbered?"
            value={data.property_encumbered || ''}
            onChange={(value) => onChange({ property_encumbered: value })}
            suggestions={YES_NO_OPTIONS}
            placeholder="Select Yes or No"
            allowCustom={false}
          />
        </div>

        {/* Conditional: Show encumbrance fields if property is encumbered */}
        {data.property_encumbered === 'Yes' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <AutocompleteInput
              label="Encumbrance Type"
              value={data.encumbrance_type || ''}
              onChange={(value) => onChange({ encumbrance_type: value })}
              suggestions={ENCUMBRANCE_TYPE_OPTIONS}
              placeholder="Select encumbrance type"
              allowCustom={true}
            />

            <div className="md:col-span-2">
              <Label>Encumbrance Details</Label>
              <Textarea
                value={data.encumbrance_details || ''}
                onChange={(e) => onChange({ encumbrance_details: e.target.value })}
                placeholder="Enter details (e.g., bank name for mortgage, person name for life interest...)"
                rows={2}
                className="mt-2"
              />
            </div>
          </div>
        )}

        {/* Valuation Basis Note */}
        <div>
          <Label>Valuation Basis Note</Label>
          <Textarea
            value={data.valuation_basis_note || ''}
            onChange={(e) => onChange({ valuation_basis_note: e.target.value })}
            placeholder='e.g., "free from all encumbrances" or "subject to existing mortgage"'
            rows={2}
            className="mt-2"
          />
          <p className="text-xs text-gray-500 mt-1">
            Optional custom statement about valuation basis. If left empty, a default will be used.
          </p>
        </div>
      </Subsection>

      {/* ===== SUBSECTION 2: STREET LINES ===== */}
      <Subsection
        title="(b). Street Lines"
        description="Street line regulations and gazette references"
        isOpen={openSections.streetLines}
        onToggle={() => toggleSection('streetLines')}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Street Lines Status */}
          <div className="md:col-span-2">
            <AutocompleteInput
              label="Street Lines Status"
              value={data.street_lines_status || ''}
              onChange={(value) => onChange({ street_lines_status: value })}
              suggestions={STREET_LINES_OPTIONS}
              placeholder="Select street lines status"
              allowCustom={true}
            />
          </div>

          {/* Gazette Reference */}
          <AutocompleteInput
            label="Gazette Reference (if applicable)"
            value={data.street_lines_gazette_ref || ''}
            onChange={(value) => onChange({ street_lines_gazette_ref: value })}
            suggestions={[]}
            placeholder="e.g., No. 1234/5"
            allowCustom={true}
          />

          {/* Gazette Date */}
          <AutocompleteInput
            label="Gazette Date (if applicable)"
            value={data.street_lines_gazette_date || ''}
            onChange={(value) => onChange({ street_lines_gazette_date: value })}
            suggestions={[]}
            placeholder="DD-MM-YYYY"
            allowCustom={true}
          />
        </div>

        {/* Impact Description */}
        <div>
          <Label>Impact Description (Optional)</Label>
          <Textarea
            value={data.street_lines_impact_description || ''}
            onChange={(e) => onChange({ street_lines_impact_description: e.target.value })}
            placeholder="Describe how street lines affect the property..."
            rows={3}
            className="mt-2"
          />
        </div>
      </Subsection>

      {/* ===== SUBSECTION 3: BUILDING LIMITS ===== */}
      <Subsection
        title="(c). Building Limits"
        description="Building approvals, setbacks, and limit compliance"
        isOpen={openSections.buildingLimits}
        onToggle={() => toggleSection('buildingLimits')}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Building Limits Status */}
          <div className="md:col-span-2">
            <AutocompleteInput
              label="Building Limits Status"
              value={data.building_limits_status || ''}
              onChange={(value) => onChange({ building_limits_status: value })}
              suggestions={BUILDING_LIMITS_OPTIONS}
              placeholder="Select building limits status"
              allowCustom={true}
            />
          </div>

          {/* Building Plan Approved */}
          <AutocompleteInput
            label="Building Plan Approved?"
            value={data.building_plan_approved || ''}
            onChange={(value) => onChange({ building_plan_approved: value })}
            suggestions={BUILDING_APPROVAL_OPTIONS}
            placeholder="Select approval status"
            allowCustom={false}
          />

          {/* Building Within Limits */}
          <AutocompleteInput
            label="Building Within Limits?"
            value={data.building_within_limits || ''}
            onChange={(value) => onChange({ building_within_limits: value })}
            suggestions={YES_NO_OPTIONS}
            placeholder="Select Yes or No"
            allowCustom={false}
          />

          {/* Distance from Road */}
          <AutocompleteInput
            label="Distance from Access Road"
            value={data.building_distance_from_road || ''}
            onChange={(value) => onChange({ building_distance_from_road: value })}
            suggestions={[]}
            placeholder="e.g., 25 feet"
            allowCustom={true}
          />

          {/* Approval Authority */}
          <AutocompleteInput
            label="Approval Authority"
            value={data.building_approval_authority || ''}
            onChange={(value) => onChange({ building_approval_authority: value })}
            suggestions={[]}
            placeholder="e.g., Rambukkana Pradeshiya Sabha"
            allowCustom={true}
          />

          {/* Plan Reference */}
          <div className="md:col-span-2">
            <AutocompleteInput
              label="Building Plan Reference (if applicable)"
              value={data.building_plan_reference || ''}
              onChange={(value) => onChange({ building_plan_reference: value })}
              suggestions={[]}
              placeholder="Enter building plan reference number"
              allowCustom={true}
            />
          </div>
        </div>
      </Subsection>

      {/* ===== SUBSECTION 4: LOCAL AUTHORITY ===== */}
      <Subsection
        title="(d). Local Authority Data"
        description="Rating, taxation, and administrative information"
        isOpen={openSections.localAuthority}
        onToggle={() => toggleSection('localAuthority')}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Property Rated */}
          <AutocompleteInput
            label="Property Rated for Taxes?"
            value={data.local_authority_rated || ''}
            onChange={(value) => onChange({ local_authority_rated: value })}
            suggestions={YES_NO_OPTIONS}
            placeholder="Select Yes or No"
            allowCustom={false}
          />

          {/* Tax Levy (conditional) */}
          {data.local_authority_rated === 'Yes' && (
            <AutocompleteInput
              label="Tax Levy Information"
              value={data.local_authority_tax_levy || ''}
              onChange={(value) => onChange({ local_authority_tax_levy: value })}
              suggestions={[]}
              placeholder="Enter tax amount or description"
              allowCustom={true}
            />
          )}
        </div>

        {/* Free-text override (backward compatibility) */}
        <div>
          <Label>Local Authority Data (Free Text Override)</Label>
          <Textarea
            value={data.local_authority_data || ''}
            onChange={(e) => onChange({ local_authority_data: e.target.value })}
            placeholder="Enter custom local authority information (optional - system will auto-generate if left empty)..."
            rows={3}
            className="mt-2"
          />
          <p className="text-xs text-gray-500 mt-1">
            Leave empty to auto-generate from property location data (Pradeshiya Sabha, District, Province).
            Use this field only if you want to override the automatic text.
          </p>
        </div>
      </Subsection>

      {/* ===== SUBSECTION 5: RENT ACT ===== */}
      <Subsection
        title="(e). Rent Act Effectiveness"
        description="Rent control regulations and applicability"
        isOpen={openSections.rentAct}
        onToggle={() => toggleSection('rentAct')}
      >
        <AutocompleteInput
          label="Rent Act Effectiveness"
          value={data.rent_act_effectiveness || ''}
          onChange={(value) => onChange({ rent_act_effectiveness: value })}
          suggestions={RENT_ACT_OPTIONS}
          placeholder="Select rent act status"
          allowCustom={true}
        />
        <p className="text-xs text-gray-500 mt-2">
          Select the applicable rent act regulation status for this property.
        </p>
      </Subsection>
    </div>
  );
}
