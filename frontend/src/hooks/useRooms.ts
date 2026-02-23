import type { Building, Room } from '../types';
import { calculateAccommodationSummary } from './useBuildings';

export function useRooms(
  buildings: Building[],
  setBuildings: React.Dispatch<React.SetStateAction<Building[]>>,
  setValue: any
) {
  // Floor-level room operations (rooms nested under floors)
  const addRoom = (buildingId: string, floorIndex: number) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = [...b.floors];
        if (!newFloors[floorIndex].rooms) newFloors[floorIndex].rooms = [];
        newFloors[floorIndex].rooms!.push({
          room_type: 'Bedroom',
          count: 1,
          has_attached_bathroom: false
        });
        newFloors[floorIndex].accommodation_summary = calculateAccommodationSummary(newFloors[floorIndex].rooms!);
        return { ...b, floors: newFloors };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const updateRoom = (buildingId: string, floorIndex: number, roomIndex: number, field: string, value: any) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = [...b.floors];
        const updatedRooms = [...(newFloors[floorIndex].rooms || [])];
        updatedRooms[roomIndex] = { ...updatedRooms[roomIndex], [field]: value };
        newFloors[floorIndex].rooms = updatedRooms;
        newFloors[floorIndex].accommodation_summary = calculateAccommodationSummary(updatedRooms);
        return { ...b, floors: newFloors };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const removeRoom = (buildingId: string, floorIndex: number, roomIndex: number) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = [...b.floors];
        const updatedRooms = (newFloors[floorIndex].rooms || []).filter((_: Room, idx: number) => idx !== roomIndex);
        newFloors[floorIndex].rooms = updatedRooms;
        newFloors[floorIndex].accommodation_summary = calculateAccommodationSummary(updatedRooms);
        return { ...b, floors: newFloors };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // Building-level room operations (rooms on the building directly)
  const addRoomToBuilding = (buildingId: string) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newRooms = [...(b.rooms || []), {
          room_type: 'Bedroom',
          count: 1,
          has_attached_bathroom: false
        }];
        return {
          ...b,
          rooms: newRooms,
          accommodation_summary: calculateAccommodationSummary(newRooms)
        };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);

    setTimeout(() => {
      const building = updated.find(b => b.id === buildingId);
      if (building?.rooms?.length) {
        const roomIndex = building.rooms.length - 1;
        const roomElement = document.querySelector(
          `[data-room-id="${buildingId}-${roomIndex}"]`
        );
        roomElement?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  };

  const updateRoomInBuilding = (buildingId: string, roomIndex: number, field: string, value: any) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newRooms = [...(b.rooms || [])];
        newRooms[roomIndex] = { ...newRooms[roomIndex], [field]: value };
        return {
          ...b,
          rooms: newRooms,
          accommodation_summary: calculateAccommodationSummary(newRooms)
        };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const removeRoomFromBuilding = (buildingId: string, roomIndex: number) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newRooms = (b.rooms || []).filter((_, idx) => idx !== roomIndex);
        return {
          ...b,
          rooms: newRooms,
          accommodation_summary: calculateAccommodationSummary(newRooms)
        };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  return {
    addRoom,
    updateRoom,
    removeRoom,
    addRoomToBuilding,
    updateRoomInBuilding,
    removeRoomFromBuilding,
  };
}
