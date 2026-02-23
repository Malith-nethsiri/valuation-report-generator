import { useEffect } from 'react';
import type { Building } from '../types';
import { FLOOR_NAMES } from '../constants/propertyDescriptionConstants';

// Re-export FLOOR_NAMES for use in useFloors
export { FLOOR_NAMES };

/**
 * Normalize building data to ensure all required properties exist.
 * Also migrates legacy `age_description` (string) → `building_age` (number).
 */
export const normalizeBuilding = (building: any): Building => {
  let buildingAge = building.building_age;
  if (buildingAge === undefined && building.age_description) {
    const match = building.age_description.match(/\d+/);
    buildingAge = match ? parseInt(match[0], 10) : 0;
  }

  return {
    ...building,
    building_age: buildingAge || 0,
    rooms: building.rooms || [],
    floors: building.floors || [],
    building_photos: building.building_photos || [],
    conveniences: building.conveniences || [],
    roof_types: building.roof_types || [],
    wall_types: building.wall_types || [],
    floor_types: building.floor_types || []
  };
};

/**
 * Calculate accommodation summary from a rooms array.
 * Supports both count-based and legacy individual-room approaches.
 */
export const calculateAccommodationSummary = (rooms: { room_type: string; count?: number; has_attached_bathroom?: boolean }[]) => {
  const summary = {
    bedrooms: 0,
    bathrooms: 0,
    living_rooms: 0,
    dining_rooms: 0,
    kitchens: 0,
    pantries: 0,
    verandahs: 0,
    balconies: 0,
    garages: 0,
    store_rooms: 0,
    other_rooms: 0
  };

  rooms.forEach(room => {
    const type = room.room_type.toLowerCase();
    const count = room.count || 1;

    if (type.includes('bedroom') && !type.includes('attached')) summary.bedrooms += count;
    else if (type.includes('attached bathroom')) summary.bathrooms += count;
    else if (type.includes('bathroom')) summary.bathrooms += count;
    else if (type.includes('living')) summary.living_rooms += count;
    else if (type.includes('dining')) summary.dining_rooms += count;
    else if (type.includes('kitchen')) summary.kitchens += count;
    else if (type.includes('pantry')) summary.pantries += count;
    else if (type.includes('verandah')) summary.verandahs += count;
    else if (type.includes('balcony')) summary.balconies += count;
    else if (type.includes('garage') || type.includes('car porch')) summary.garages += count;
    else if (type.includes('store')) summary.store_rooms += count;
    else summary.other_rooms += count;
  });

  return summary;
};

export function useBuildings(
  buildings: Building[],
  setBuildings: React.Dispatch<React.SetStateAction<Building[]>>,
  setValue: any,
  setExpandedBuilding: React.Dispatch<React.SetStateAction<string | null>>,
  setFloorsExpanded: React.Dispatch<React.SetStateAction<{ [buildingId: string]: boolean }>>,
  watch: any
) {
  const formBuildings = watch('buildings');

  // Initialize buildings from form values on mount
  useEffect(() => {
    if (formBuildings && Array.isArray(formBuildings) && formBuildings.length > 0) {
      const normalized = formBuildings.map(normalizeBuilding);
      setBuildings(normalized);
      // CRITICAL: Sync normalized data back to form state so it gets submitted correctly
      setValue('buildings', normalized);

      // Initialize floorsExpanded to true for all buildings with floors
      const initialFloorsExpanded: { [buildingId: string]: boolean } = {};
      normalized.forEach(building => {
        if (building.floors && building.floors.length > 0) {
          initialFloorsExpanded[building.id] = true;
        }
      });
      setFloorsExpanded(initialFloorsExpanded);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-fill occupier info from applicant name when step loads
  useEffect(() => {
    const applicantFullName = watch('applicant_full_name');
    const currentOccupierName = watch('occupier_name');

    if (!currentOccupierName && applicantFullName) {
      setValue('occupier_name', applicantFullName);
      setValue('occupier_relationship', 'owner');
    }

    const currentBuildings = watch('buildings') || [];
    if (currentBuildings.length > 0 && applicantFullName) {
      const updatedBuildings = currentBuildings.map((building: Building) => {
        if (!building.occupier_name) {
          return {
            ...building,
            occupier_name: applicantFullName,
            occupier_relationship: 'owner'
          };
        }
        return building;
      });

      const hasChanges = updatedBuildings.some((b: Building, i: number) =>
        b.occupier_name !== currentBuildings[i].occupier_name
      );
      if (hasChanges) {
        setValue('buildings', updatedBuildings);
        setBuildings(updatedBuildings);
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const addBuilding = () => {
    const applicantFullName = watch('applicant_full_name') || '';

    const newBuilding: Building = {
      id: `building_${Date.now()}`,
      building_name: '',
      building_type: 'residential',
      stories: 1,
      building_age: 0,
      condition: 'fair',
      occupier_name: applicantFullName,
      occupier_relationship: applicantFullName ? 'owner' : '',
      roof_types: [],
      roof_description: '',
      wall_types: [],
      wall_description: '',
      floor_types: [],
      floor_description: '',
      total_floor_area: 0,
      floors: [{ floor_name: 'Ground Floor', floor_area: 0 }],
      rooms: [],
      accommodation_summary: undefined,
      conveniences: [],
      building_description_text: '',
      building_photos: []
    };
    const updated = [...buildings, newBuilding];
    setBuildings(updated);
    setValue('buildings', updated);
    setExpandedBuilding(newBuilding.id);

    setFloorsExpanded(prev => ({
      ...prev,
      [newBuilding.id]: true
    }));
  };

  const removeBuilding = (id: string) => {
    const updated = buildings.filter(b => b.id !== id);
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const updateBuilding = (id: string, field: string, value: any) => {
    const updated = buildings.map(b => {
      if (b.id === id) {
        const updatedBuilding = { ...b, [field]: value };
        updatedBuilding.stories = updatedBuilding.floors.length;
        updatedBuilding.total_floor_area = updatedBuilding.floors.reduce(
          (sum: number, floor: { floor_area?: number }) => sum + (floor.floor_area || 0), 0
        );
        return updatedBuilding;
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const copyOccupierFromFirstBuilding = (targetBuildingId: string) => {
    if (buildings.length === 0) return;
    const firstBuilding = buildings[0];
    updateBuilding(targetBuildingId, 'occupier_name', firstBuilding.occupier_name || '');
    updateBuilding(targetBuildingId, 'occupier_relationship', firstBuilding.occupier_relationship || '');
  };

  const updateBuildingConstructionMaterial = (buildingId: string, section: string, field: string, value: any) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const updatedMaterials = {
          ...b.construction_materials,
          [section]: {
            ...((b.construction_materials as any)?.[section] || {}),
            [field]: value
          }
        };
        return { ...b, construction_materials: updatedMaterials };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  return {
    addBuilding,
    removeBuilding,
    updateBuilding,
    copyOccupierFromFirstBuilding,
    updateBuildingConstructionMaterial,
  };
}
