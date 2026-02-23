import { useState } from 'react';
import type { Building } from '../types';
import { useBuildings } from './useBuildings';
import { useFloors } from './useFloors';
import { useRooms } from './useRooms';
import { useBuildingPhotos } from './useBuildingPhotos';

interface UseBuildingManagerProps {
  watch: any;
  setValue: any;
}

export function useBuildingManager({ watch, setValue }: UseBuildingManagerProps) {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [expandedBuilding, setExpandedBuilding] = useState<string | null>(null);
  const [floorCount, setFloorCount] = useState<{ [buildingId: string]: number }>({});
  const [floorsExpanded, setFloorsExpanded] = useState<{ [buildingId: string]: boolean }>({});
  const [uploadingPhotos, setUploadingPhotos] = useState<{ [buildingId: string]: boolean }>({});

  const buildingOps = useBuildings(
    buildings, setBuildings, setValue, setExpandedBuilding, setFloorsExpanded, watch
  );

  const floorOps = useFloors(buildings, setBuildings, setValue);

  const roomOps = useRooms(buildings, setBuildings, setValue);

  const photoOps = useBuildingPhotos(
    buildings, setBuildings, setValue, setUploadingPhotos
  );

  return {
    buildings,
    expandedBuilding,
    setExpandedBuilding,
    ...buildingOps,
    ...floorOps,
    ...roomOps,
    ...photoOps,
    floorCount,
    setFloorCount,
    floorsExpanded,
    setFloorsExpanded,
    uploadingPhotos,
  };
}
