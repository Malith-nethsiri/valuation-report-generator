import React from 'react';
import { Building2, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import type { Building } from '../../types';
import { BUILDING_TYPES } from '../../constants/propertyDescriptionConstants';

interface BuildingHeaderProps {
  building: Building;
  buildingIndex: number;
  expandedBuilding: string | null;
  setExpandedBuilding: (id: string | null) => void;
  removeBuilding: (id: string) => void;
}

export const BuildingHeader: React.FC<BuildingHeaderProps> = ({
  building,
  buildingIndex,
  expandedBuilding,
  setExpandedBuilding,
  removeBuilding,
}) => {
  return (
    <div
      className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer"
      onClick={() => setExpandedBuilding(
        expandedBuilding === building.id ? null : building.id
      )}
    >
      <div className="flex items-center space-x-3">
        <Building2 className="h-5 w-5 text-emerald-600" />
        <span className="font-semibold text-gray-900">
          {building.building_name || `Building ${buildingIndex + 1}`}
        </span>
        <span className="text-sm text-gray-500">
          ({BUILDING_TYPES.find(t => t.value === building.building_type)?.label || 'Residential'})
        </span>
      </div>
      <div className="flex items-center space-x-2">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            removeBuilding(building.id);
          }}
          className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
        >
          <Trash2 className="h-4 w-4" />
        </button>
        {expandedBuilding === building.id ? (
          <ChevronUp className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        )}
      </div>
    </div>
  );
};
