import React, { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import type { RoadCondition } from '../types';

interface Props {
  roadConditions: RoadCondition[];
  onChange: (conditions: RoadCondition[]) => void;
}

const ROAD_TYPES = [
  { value: 'paved_road', label: 'Paved Road / Asphalt' },
  { value: 'concrete_road', label: 'Concrete Road' },
  { value: 'carpet_road', label: 'Carpet Road' },
  { value: 'gravel_road', label: 'Gravel Road' },
  { value: 'sand_road', label: 'Sand Road' },
  { value: 'earth_road', label: 'Earth Road' },
] as const;

const CONDITIONS = ['excellent', 'good', 'fair', 'poor'] as const;

export function RoadConditionsSummary({ roadConditions, onChange }: Props) {
  // Track which road types are selected
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());

  // Initialize selected types from existing conditions
  useEffect(() => {
    const types = new Set(roadConditions.map(c => c.road_type));
    setSelectedTypes(types);
  }, []);

  // Handle checkbox toggle
  const toggleRoadType = (roadType: string) => {
    const newSelectedTypes = new Set(selectedTypes);

    if (newSelectedTypes.has(roadType)) {
      // Remove this road type
      newSelectedTypes.delete(roadType);
      // Remove from conditions array
      const newConditions = roadConditions.filter(c => c.road_type !== roadType);
      onChange(newConditions);
    } else {
      // Add this road type with default values
      newSelectedTypes.add(roadType);
      const newCondition: RoadCondition = {
        road_type: roadType as any,
        condition: 'good',  // Default condition
        distance_km: undefined,  // Optional distance
        notes: ''
      };
      onChange([...roadConditions, newCondition]);
    }

    setSelectedTypes(newSelectedTypes);
  };

  // Update condition for a specific road type
  const updateCondition = (roadType: string, field: 'condition' | 'notes' | 'distance_km', value: any) => {
    const newConditions = roadConditions.map(c =>
      c.road_type === roadType
        ? { ...c, [field]: value }
        : c
    );
    onChange(newConditions);
  };

  // Get condition data for a specific road type
  const getConditionData = (roadType: string): RoadCondition | undefined => {
    return roadConditions.find(c => c.road_type === roadType);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <strong>How it works:</strong> Select the road types you encounter along the route and their conditions.
          The system will automatically integrate this information with turn-by-turn directions (road names, landmarks, junctions) to create a professional access description.
          <div className="mt-2 text-xs text-blue-700">
            <strong>Note:</strong> Distance is optional - you can specify distances for each road type if known, or leave blank.
          </div>
        </div>
      </div>

      {/* Road Type Checkboxes with Dynamic Fields */}
      <div className="space-y-3">
        {ROAD_TYPES.map(({ value, label }) => {
          const isSelected = selectedTypes.has(value);
          const conditionData = getConditionData(value);

          return (
            <div key={value} className="border rounded-lg overflow-hidden">
              {/* Checkbox Row */}
              <label className={`flex items-center gap-3 p-4 cursor-pointer transition-colors ${
                isSelected ? 'bg-blue-50 border-b' : 'bg-white hover:bg-gray-50'
              }`}>
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleRoadType(value)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <span className={`font-medium ${isSelected ? 'text-blue-900' : 'text-gray-700'}`}>
                  {label}
                </span>
              </label>

              {/* Condition Fields (shown only when checked) */}
              {isSelected && conditionData && (
                <div className="p-4 bg-gray-50 space-y-3">
                  {/* Condition Buttons */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Condition <span className="text-red-500">*</span>
                    </label>
                    <div className="grid grid-cols-4 gap-2">
                      {CONDITIONS.map((condition) => (
                        <button
                          key={condition}
                          type="button"
                          onClick={() => updateCondition(value, 'condition', condition)}
                          className={`px-3 py-2 rounded-md border-2 font-medium text-sm transition-colors ${
                            conditionData.condition === condition
                              ? 'border-blue-600 bg-blue-50 text-blue-700'
                              : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                          }`}
                        >
                          {condition.charAt(0).toUpperCase() + condition.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Distance Field (Optional) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Distance <span className="text-gray-400">(optional, in km)</span>
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      value={conditionData.distance_km || ''}
                      onChange={(e) => updateCondition(value, 'distance_km', e.target.value ? parseFloat(e.target.value) : undefined)}
                      placeholder="e.g., 15.5"
                      className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>

                  {/* Notes Field */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Additional Notes <span className="text-gray-400">(optional)</span>
                    </label>
                    <textarea
                      rows={2}
                      value={conditionData.notes || ''}
                      onChange={(e) => updateCondition(value, 'notes', e.target.value)}
                      placeholder="e.g., Seasonal flooding during monsoon, Recently repaired section, Last 500m only..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary */}
      {selectedTypes.size > 0 && (
        <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
          <strong>Selected:</strong> {selectedTypes.size} road type{selectedTypes.size !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
