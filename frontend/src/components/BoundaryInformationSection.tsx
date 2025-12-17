import React, { useState } from 'react';
import { Label } from './Label';
import { Input } from './Input';
import { Compass, ChevronDown, ChevronUp, Check } from 'lucide-react';
import { Button } from './Button';

interface BoundaryData {
  description: string;
  length?: string;
  adjoins?: string;
  notes?: string;
}

interface BoundariesData {
  north?: BoundaryData;
  south?: BoundaryData;
  east?: BoundaryData;
  west?: BoundaryData;
}

interface PhysicalBoundariesData {
  types: string[];
  description: string;
}

interface BoundaryTypesPerDirection {
  north?: string;
  south?: string;
  east?: string;
  west?: string;
}

interface BoundaryInformationSectionProps {
  boundaries?: BoundariesData;
  physicalBoundariesTypes?: string[];
  physicalBoundariesDescription?: string;
  landTraditionalName?: string;
  boundaryTypesPerDirection?: BoundaryTypesPerDirection;
  entranceType?: string;
  boundariesSummaryText?: string;
  onChange: (data: {
    boundaries: BoundariesData;
    physical_boundaries_types: string[];
    physical_boundaries_description: string;
    land_traditional_name: string;
    boundary_types_per_direction: BoundaryTypesPerDirection;
    entrance_type: string;
    boundaries_summary_text: string;
  }) => void;
  disabled?: boolean;
}

const PHYSICAL_BOUNDARY_OPTIONS = [
  { id: 'brick_walls', label: 'Brick Masonry Walls' },
  { id: 'barbed_wire', label: 'Barbed Wire Fence' },
  { id: 'live_fence', label: 'Live Fence/Hedge' },
  { id: 'concrete_posts', label: 'Concrete Posts' },
  { id: 'iron_gate', label: 'Iron/Metal Gate' },
  { id: 'rubble_foundation', label: 'Rubble Masonry Foundation' },
];

const ENTRANCE_TYPE_OPTIONS = [
  { id: 'auto_roller_gate', label: 'Auto Roller Gate' },
  { id: 'iron_gate', label: 'Iron Gate' },
  { id: 'wooden_gate', label: 'Wooden Gate' },
  { id: 'sliding_gate', label: 'Sliding Gate' },
  { id: 'swing_gate', label: 'Swing Gate' },
  { id: 'no_gate', label: 'No Gate/Open Entry' },
];

export function BoundaryInformationSection({
  boundaries = {},
  physicalBoundariesTypes = [],
  physicalBoundariesDescription = '',
  landTraditionalName = '',
  boundaryTypesPerDirection = {},
  entranceType = '',
  boundariesSummaryText = '',
  onChange,
  disabled = false,
}: BoundaryInformationSectionProps) {
  const [localBoundaries, setLocalBoundaries] = useState<BoundariesData>(
    boundaries || {}
  );
  const [localPhysicalTypes, setLocalPhysicalTypes] = useState<string[]>(
    physicalBoundariesTypes || []
  );
  const [localPhysicalDesc, setLocalPhysicalDesc] = useState<string>(
    physicalBoundariesDescription || ''
  );
  const [localTraditionalName, setLocalTraditionalName] = useState<string>(
    landTraditionalName || ''
  );
  const [localBoundaryTypesPerDir, setLocalBoundaryTypesPerDir] = useState<BoundaryTypesPerDirection>(
    boundaryTypesPerDirection || {}
  );
  const [localEntranceType, setLocalEntranceType] = useState<string>(
    entranceType || ''
  );
  const [localSummaryText, setLocalSummaryText] = useState<string>(
    boundariesSummaryText || ''
  );

  // State for expanding/collapsing detailed inputs
  const [expandedDirections, setExpandedDirections] = useState<{
    [key: string]: boolean;
  }>({
    north: false,
    south: false,
    east: false,
    west: false,
  });

  // Generate boundary summary text based on selections
  const generateSummaryText = (
    typesPerDir: BoundaryTypesPerDirection,
    physicalTypes: string[],
    entrance: string
  ): string => {
    const boundaryTypeLabels: { [key: string]: string } = {
      'brick_walls': 'brick masonry parapet walls',
      'barbed_wire': 'barbed wire fence',
      'live_fence': 'live fence',
      'concrete_posts': 'concrete posts',
      'iron_gate': 'iron gate',
      'rubble_foundation': 'rubble masonry foundation',
    };

    const entranceLabels: { [key: string]: string } = {
      'auto_roller_gate': 'an Auto roller gate',
      'iron_gate': 'an Iron gate',
      'wooden_gate': 'a Wooden gate',
      'sliding_gate': 'a Sliding gate',
      'swing_gate': 'a Swing gate',
    };

    let parts: string[] = [];
    parts.push('The boundaries referred above are in accordance with those shown in plan and are well defined');

    // Group directions by boundary type
    const typeToDirections: { [key: string]: string[] } = {};
    const directions = ['north', 'east', 'south', 'west'] as const;

    for (const dir of directions) {
      const bType = typesPerDir[dir];
      if (bType) {
        if (!typeToDirections[bType]) {
          typeToDirections[bType] = [];
        }
        typeToDirections[bType].push(dir);
      }
    }

    // Build description
    const descriptions: string[] = [];
    for (const [bType, dirs] of Object.entries(typeToDirections)) {
      const typeLabel = boundaryTypeLabels[bType] || bType;
      let dirText: string;
      if (dirs.length === 4) {
        dirText = 'on all four sides';
      } else if (dirs.length === 1) {
        dirText = `on the ${dirs[0]}`;
      } else {
        dirText = 'on the ' + dirs.slice(0, -1).join(', ') + ` and ${dirs[dirs.length - 1]}`;
      }
      descriptions.push(`demarcated by ${typeLabel} ${dirText}`);
    }

    if (descriptions.length > 0) {
      parts.push(' and ' + descriptions.join(', '));
    } else if (physicalTypes.length > 0) {
      // Fallback to general physical boundaries
      const typeLabels = physicalTypes.slice(0, 3).map(t => boundaryTypeLabels[t] || t);
      if (physicalTypes.includes('rubble_foundation')) {
        const mainTypes = typeLabels.filter(t => !t.includes('rubble'));
        if (mainTypes.length > 0) {
          parts.push(` and demarcated by ${mainTypes[0]} constructed on rubble masonry foundation on the north, east, south and the west`);
        }
      } else if (typeLabels.length > 0) {
        parts.push(` and demarcated by ${typeLabels.join(', ')}`);
      }
    }

    parts.push('.');

    // Add entrance info
    if (entrance && entrance !== 'no_gate') {
      const entranceLabel = entranceLabels[entrance];
      if (entranceLabel) {
        parts.push(` There is ${entranceLabel} entrance to the property.`);
      }
    }

    return parts.join('');
  };

  const notifyParent = (
    updatedBoundaries: BoundariesData,
    updatedTypes: string[],
    updatedDesc: string,
    updatedName: string,
    updatedTypesPerDir: BoundaryTypesPerDirection,
    updatedEntrance: string,
    updatedSummary: string
  ) => {
    onChange({
      boundaries: updatedBoundaries,
      physical_boundaries_types: updatedTypes,
      physical_boundaries_description: updatedDesc,
      land_traditional_name: updatedName,
      boundary_types_per_direction: updatedTypesPerDir,
      entrance_type: updatedEntrance,
      boundaries_summary_text: updatedSummary,
    });
  };

  const handleBoundaryChange = (
    direction: 'north' | 'south' | 'east' | 'west',
    field: keyof BoundaryData,
    value: string
  ) => {
    const updated = {
      ...localBoundaries,
      [direction]: {
        ...localBoundaries[direction],
        [field]: value,
      },
    };
    setLocalBoundaries(updated);
    notifyParent(updated, localPhysicalTypes, localPhysicalDesc, localTraditionalName, localBoundaryTypesPerDir, localEntranceType, localSummaryText);
  };

  const togglePhysicalBoundaryType = (typeId: string) => {
    const updated = localPhysicalTypes.includes(typeId)
      ? localPhysicalTypes.filter((t) => t !== typeId)
      : [...localPhysicalTypes, typeId];
    setLocalPhysicalTypes(updated);
    // Regenerate summary if no custom text
    const newSummary = localSummaryText || generateSummaryText(localBoundaryTypesPerDir, updated, localEntranceType);
    notifyParent(localBoundaries, updated, localPhysicalDesc, localTraditionalName, localBoundaryTypesPerDir, localEntranceType, newSummary);
  };

  const handlePhysicalDescChange = (value: string) => {
    setLocalPhysicalDesc(value);
    notifyParent(localBoundaries, localPhysicalTypes, value, localTraditionalName, localBoundaryTypesPerDir, localEntranceType, localSummaryText);
  };

  const handleTraditionalNameChange = (value: string) => {
    setLocalTraditionalName(value);
    notifyParent(localBoundaries, localPhysicalTypes, localPhysicalDesc, value, localBoundaryTypesPerDir, localEntranceType, localSummaryText);
  };

  const handleBoundaryTypePerDirChange = (direction: 'north' | 'south' | 'east' | 'west', typeId: string) => {
    const updated = {
      ...localBoundaryTypesPerDir,
      [direction]: typeId || undefined,
    };
    setLocalBoundaryTypesPerDir(updated);
    // Auto-generate summary text
    const newSummary = generateSummaryText(updated, localPhysicalTypes, localEntranceType);
    setLocalSummaryText(newSummary);
    notifyParent(localBoundaries, localPhysicalTypes, localPhysicalDesc, localTraditionalName, updated, localEntranceType, newSummary);
  };

  const handleEntranceTypeChange = (typeId: string) => {
    setLocalEntranceType(typeId);
    // Auto-generate summary text
    const newSummary = generateSummaryText(localBoundaryTypesPerDir, localPhysicalTypes, typeId);
    setLocalSummaryText(newSummary);
    notifyParent(localBoundaries, localPhysicalTypes, localPhysicalDesc, localTraditionalName, localBoundaryTypesPerDir, typeId, newSummary);
  };

  const handleSummaryTextChange = (value: string) => {
    setLocalSummaryText(value);
    notifyParent(localBoundaries, localPhysicalTypes, localPhysicalDesc, localTraditionalName, localBoundaryTypesPerDir, localEntranceType, value);
  };

  const regenerateSummary = () => {
    const newSummary = generateSummaryText(localBoundaryTypesPerDir, localPhysicalTypes, localEntranceType);
    setLocalSummaryText(newSummary);
    notifyParent(localBoundaries, localPhysicalTypes, localPhysicalDesc, localTraditionalName, localBoundaryTypesPerDir, localEntranceType, newSummary);
  };

  const toggleExpanded = (direction: 'north' | 'south' | 'east' | 'west') => {
    setExpandedDirections((prev) => ({
      ...prev,
      [direction]: !prev[direction],
    }));
  };

  const renderBoundaryInput = (
    direction: 'north' | 'south' | 'east' | 'west',
    directionLabel: string,
    icon: string
  ) => {
    const boundaryData = localBoundaries[direction] || {
      description: '',
      length: '',
      adjoins: '',
      notes: '',
    };
    const isExpanded = expandedDirections[direction];

    return (
      <div key={direction} className="border border-gray-300 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{icon}</span>
            <Label className="text-lg font-semibold">{directionLabel}</Label>
          </div>
          <button
            type="button"
            onClick={() => toggleExpanded(direction)}
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
            disabled={disabled}
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-4 w-4" /> Hide Details
              </>
            ) : (
              <>
                <ChevronDown className="h-4 w-4" /> Show Details
              </>
            )}
          </button>
        </div>

        {/* Main Description (always visible) */}
        <div className="mb-3">
          <Label htmlFor={`${direction}-description`} className="text-sm">
            Boundary Description *
          </Label>
          <textarea
            id={`${direction}-description`}
            value={boundaryData.description || ''}
            onChange={(e) =>
              handleBoundaryChange(direction, 'description', e.target.value)
            }
            disabled={disabled}
            placeholder={`e.g., Lot 12 [20 ft wide road] in this Plan`}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={2}
          />
        </div>

        {/* Detailed Fields (expandable) */}
        {isExpanded && (
          <div className="space-y-3 bg-gray-50 p-3 rounded-lg">
            <div>
              <Label htmlFor={`${direction}-boundary-type`} className="text-sm">
                Physical Boundary Type (for this direction)
              </Label>
              <select
                id={`${direction}-boundary-type`}
                value={localBoundaryTypesPerDir[direction] || ''}
                onChange={(e) => handleBoundaryTypePerDirChange(direction, e.target.value)}
                disabled={disabled}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">-- Select boundary type --</option>
                {PHYSICAL_BOUNDARY_OPTIONS.map((opt) => (
                  <option key={opt.id} value={opt.id}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor={`${direction}-length`} className="text-sm">
                Length (optional)
              </Label>
              <Input
                id={`${direction}-length`}
                type="text"
                value={boundaryData.length || ''}
                onChange={(e) =>
                  handleBoundaryChange(direction, 'length', e.target.value)
                }
                disabled={disabled}
                placeholder="e.g., 120 feet, 36.5 meters"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor={`${direction}-adjoins`} className="text-sm">
                Adjoins (optional)
              </Label>
              <Input
                id={`${direction}-adjoins`}
                type="text"
                value={boundaryData.adjoins || ''}
                onChange={(e) =>
                  handleBoundaryChange(direction, 'adjoins', e.target.value)
                }
                disabled={disabled}
                placeholder="e.g., Lot 10, Main Road, Property of John Doe"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor={`${direction}-notes`} className="text-sm">
                Additional Notes (optional)
              </Label>
              <textarea
                id={`${direction}-notes`}
                value={boundaryData.notes || ''}
                onChange={(e) =>
                  handleBoundaryChange(direction, 'notes', e.target.value)
                }
                disabled={disabled}
                placeholder="Any additional boundary details"
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={2}
              />
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Traditional Land Name */}
      <div>
        <Label htmlFor="land-traditional-name" className="text-lg font-semibold">
          Traditional/Historical Land Name
        </Label>
        <p className="text-sm text-gray-600 mt-1 mb-3">
          E.g., "Welangollawatta", "Hakuruketiyawe Wela alias Hakuruketiyawe
          watta now Poranewatta"
        </p>
        <Input
          id="land-traditional-name"
          type="text"
          value={localTraditionalName}
          onChange={(e) => handleTraditionalNameChange(e.target.value)}
          disabled={disabled}
          placeholder="Enter traditional land name (optional)"
          className="mt-1"
        />
      </div>

      {/* Boundary Descriptions */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Compass className="h-6 w-6 text-blue-600" />
          <Label className="text-lg font-semibold">Boundary Descriptions</Label>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Describe boundaries for all four directions (North, South, East, West)
        </p>

        <div className="grid grid-cols-1 gap-4">
          {renderBoundaryInput('north', 'North Boundary', '⬆️')}
          {renderBoundaryInput('south', 'South Boundary', '⬇️')}
          {renderBoundaryInput('east', 'East Boundary', '➡️')}
          {renderBoundaryInput('west', 'West Boundary', '⬅️')}
        </div>
      </div>

      {/* Physical Boundaries */}
      <div>
        <Label className="text-lg font-semibold">Physical Boundaries</Label>
        <p className="text-sm text-gray-600 mt-1 mb-3">
          Select the types of physical boundaries present on the property
        </p>

        {/* Checkboxes for common types */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          {PHYSICAL_BOUNDARY_OPTIONS.map((option) => (
            <button
              key={option.id}
              type="button"
              onClick={() => togglePhysicalBoundaryType(option.id)}
              disabled={disabled}
              className={`flex items-center gap-3 p-3 border-2 rounded-lg transition-all ${
                localPhysicalTypes.includes(option.id)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 bg-white hover:border-gray-400'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div
                className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                  localPhysicalTypes.includes(option.id)
                    ? 'bg-blue-500 border-blue-500'
                    : 'border-gray-400'
                }`}
              >
                {localPhysicalTypes.includes(option.id) && (
                  <Check className="h-4 w-4 text-white" />
                )}
              </div>
              <span className="text-sm font-medium">{option.label}</span>
            </button>
          ))}
        </div>

        {/* Custom description */}
        <div>
          <Label htmlFor="physical-boundaries-description" className="text-sm">
            Additional Physical Boundary Details (optional)
          </Label>
          <textarea
            id="physical-boundaries-description"
            value={localPhysicalDesc}
            onChange={(e) => handlePhysicalDescChange(e.target.value)}
            disabled={disabled}
            placeholder="Describe any additional physical boundary features not covered above..."
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
          />
        </div>
      </div>

      {/* Entrance/Gate Type */}
      <div>
        <Label className="text-lg font-semibold">Property Entrance</Label>
        <p className="text-sm text-gray-600 mt-1 mb-3">
          Select the type of entrance/gate to the property
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {ENTRANCE_TYPE_OPTIONS.map((option) => (
            <button
              key={option.id}
              type="button"
              onClick={() => handleEntranceTypeChange(option.id)}
              disabled={disabled}
              className={`flex items-center gap-2 p-3 border-2 rounded-lg transition-all ${
                localEntranceType === option.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 bg-white hover:border-gray-400'
              } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <div
                className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                  localEntranceType === option.id
                    ? 'border-blue-500'
                    : 'border-gray-400'
                }`}
              >
                {localEntranceType === option.id && (
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                )}
              </div>
              <span className="text-sm font-medium">{option.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Boundary Summary Preview */}
      <div className="border-t pt-6">
        <div className="flex items-center justify-between mb-3">
          <Label className="text-lg font-semibold">Boundary Summary (for Report)</Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={regenerateSummary}
            disabled={disabled}
          >
            Regenerate
          </Button>
        </div>
        <p className="text-sm text-gray-600 mb-3">
          This text will appear in the final report. Edit if needed.
        </p>
        <textarea
          id="boundaries-summary-text"
          value={localSummaryText}
          onChange={(e) => handleSummaryTextChange(e.target.value)}
          disabled={disabled}
          placeholder="The boundaries referred above are in accordance with those shown in plan..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows={4}
        />
      </div>
    </div>
  );
}
