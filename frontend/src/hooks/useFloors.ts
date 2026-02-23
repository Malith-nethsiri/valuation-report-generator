import type { Building } from '../types';
import { FLOOR_NAMES } from '../constants/propertyDescriptionConstants';

export function useFloors(
  buildings: Building[],
  setBuildings: React.Dispatch<React.SetStateAction<Building[]>>,
  setValue: any
) {
  const generateFloors = (buildingId: string, count: number) => {
    if (count < 1 || count > 10) return;

    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = Array.from({ length: count }, (_, i) => ({
          floor_name: FLOOR_NAMES[i] || `Floor ${i + 1}`,
          floor_area: 0
        }));
        const total_floor_area = newFloors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
        return { ...b, floors: newFloors, total_floor_area };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const addFloor = (buildingId: string) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const floorNum = b.floors.length + 1;
        const floorName = floorNum === 1 ? 'Ground Floor' :
                         floorNum === 2 ? 'First Floor' :
                         floorNum === 3 ? 'Second Floor' : `Floor ${floorNum}`;
        const updatedFloors = [...b.floors, { floor_name: floorName, floor_area: 0 }];
        const total_floor_area = updatedFloors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
        return { ...b, floors: updatedFloors, total_floor_area };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const updateFloorName = (buildingId: string, floorIndex: number, newName: string) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const updatedFloors = b.floors.map((floor, idx) =>
          idx === floorIndex ? { ...floor, floor_name: newName } : floor
        );
        return { ...b, floors: updatedFloors };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const updateFloorArea = (buildingId: string, floorIndex: number, area: number) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = [...b.floors];
        newFloors[floorIndex].floor_area = area;
        const total_floor_area = newFloors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
        return { ...b, floors: newFloors, total_floor_area };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  return { generateFloors, addFloor, updateFloorName, updateFloorArea };
}
