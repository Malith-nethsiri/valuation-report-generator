import React from 'react';
import { Building2, ChevronDown, ChevronUp, Sparkles, Maximize2 } from 'lucide-react';
import { Button } from '../Button';
import { Input } from '../Input';
import { Label } from '../Label';
import type { Building } from '../../types';
import { MAX_FLOORS_PER_BUILDING } from '../../constants/propertyDescriptionConstants';

interface BuildingFloorsSectionProps {
  building: Building;
  floorCount: { [buildingId: string]: number };
  setFloorCount: React.Dispatch<React.SetStateAction<{ [buildingId: string]: number }>>;
  floorsExpanded: { [buildingId: string]: boolean };
  setFloorsExpanded: React.Dispatch<React.SetStateAction<{ [buildingId: string]: boolean }>>;
  generateFloors: (buildingId: string, count: number) => void;
  updateFloorName: (buildingId: string, floorIndex: number, name: string) => void;
  updateFloorArea: (buildingId: string, floorIndex: number, area: number) => void;
}

export const BuildingFloorsSection: React.FC<BuildingFloorsSectionProps> = ({
  building,
  floorCount,
  setFloorCount,
  floorsExpanded,
  setFloorsExpanded,
  generateFloors,
  updateFloorName,
  updateFloorArea,
}) => {
  return (
    <div className="border-t border-gray-200 pt-6 mt-6">
      <h4 className="text-lg font-semibold text-gray-900 mb-4">Floor Plan &amp; Accommodation</h4>

      {/* Floor Generator */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 mb-6">
        <Label className="text-base font-semibold text-gray-900 mb-3 flex items-center">
          <Building2 className="h-5 w-5 mr-2 text-blue-600" />
          How many floors does this building have?
        </Label>
        <div className="flex items-center space-x-4 mt-3">
          <Input
            type="number"
            min="1"
            max={MAX_FLOORS_PER_BUILDING}
            value={floorCount[building.id] || building.floors.length}
            onChange={(e) => setFloorCount({
              ...floorCount,
              [building.id]: parseInt(e.target.value) || 1
            })}
            className="w-32 text-lg font-semibold"
            placeholder="e.g., 2"
          />
          <Button
            type="button"
            onClick={() => generateFloors(building.id, floorCount[building.id] || building.floors.length)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Generate Floor Forms
          </Button>
        </div>
        <p className="text-xs text-blue-700 mt-3 italic">
          Automatically generates: Ground Floor, First Floor, Second Floor, etc. (all names are editable)
        </p>
      </div>

      {/* Auto-Calculated Metrics */}
      {building.floors.length > 0 && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-emerald-50 border-2 border-emerald-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-emerald-700 mb-1">Number of Floors</p>
                <p className="text-3xl font-bold text-emerald-900">{building.floors.length}</p>
              </div>
              <Building2 className="h-10 w-10 text-emerald-400" />
            </div>
            <p className="text-xs text-emerald-600 mt-2 italic">Auto-calculated from generated floors</p>
          </div>
          <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-700 mb-1">Total Building Area</p>
                <p className="text-3xl font-bold text-purple-900">
                  {building.total_floor_area?.toLocaleString() || 0}
                </p>
                <p className="text-sm text-purple-600">sq.ft</p>
              </div>
              <Maximize2 className="h-10 w-10 text-purple-400" />
            </div>
            <p className="text-xs text-purple-600 mt-2 italic">Auto-calculated from all floor areas</p>
          </div>
        </div>
      )}

      {/* Collapsible Floors List */}
      {building.floors.length > 0 && (
        <div className="border-2 border-blue-200 rounded-xl p-5 mb-4 bg-blue-50">
          <button
            type="button"
            onClick={() => setFloorsExpanded({
              ...floorsExpanded,
              [building.id]: !floorsExpanded[building.id]
            })}
            className="w-full flex items-center justify-between hover:opacity-80 transition-opacity"
          >
            <h4 className="text-lg font-semibold text-blue-900">
              Floor Information ({building.floors.length} floor{building.floors.length !== 1 ? 's' : ''})
            </h4>
            {floorsExpanded[building.id] ?
              <ChevronUp className="h-5 w-5 text-blue-600" /> :
              <ChevronDown className="h-5 w-5 text-blue-600" />
            }
          </button>

          {floorsExpanded[building.id] && (
            <div className="mt-4 space-y-3">
              {building.floors.map((floor, floorIdx) => (
                <div key={floorIdx} className="bg-white border border-blue-200 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm">Floor Name</Label>
                      <Input
                        value={floor.floor_name}
                        onChange={(e) => updateFloorName(building.id, floorIdx, e.target.value)}
                        className="text-sm"
                        placeholder="e.g., Ground Floor"
                      />
                    </div>
                    <div>
                      <Label className="text-sm">Floor Area (sq ft)</Label>
                      <Input
                        type="number"
                        value={floor.floor_area || ''}
                        onChange={(e) => updateFloorArea(building.id, floorIdx, parseFloat(e.target.value) || 0)}
                        className="text-sm"
                        placeholder="0"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
