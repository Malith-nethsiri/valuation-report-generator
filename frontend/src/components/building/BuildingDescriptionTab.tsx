import React from 'react';
import { Building2, Plus } from 'lucide-react';
import { Button } from '../Button';
import type { Building } from '../../types';
import { BuildingHeader } from './BuildingHeader';
import { BuildingConstructionSection } from './BuildingConstructionSection';
import { BuildingFloorsSection } from './BuildingFloorsSection';
import { BuildingRoomsSection } from './BuildingRoomsSection';
import { BuildingPhotosSection } from './BuildingPhotosSection';

interface BuildingDescriptionTabProps {
  buildings: Building[];
  expandedBuilding: string | null;
  setExpandedBuilding: (id: string | null) => void;
  addBuilding: () => void;
  removeBuilding: (id: string) => void;
  updateBuilding: (id: string, field: string, value: any) => void;
  copyOccupierFromFirstBuilding: (id: string) => void;
  updateBuildingConstructionMaterial: (buildingId: string, section: string, field: string, value: any) => void;
  generateFloors: (buildingId: string, count: number) => void;
  addFloor: (buildingId: string) => void;
  updateFloorName: (buildingId: string, floorIndex: number, name: string) => void;
  updateFloorArea: (buildingId: string, floorIndex: number, area: number) => void;
  addRoom: (buildingId: string, floorIndex: number) => void;
  updateRoom: (buildingId: string, floorIndex: number, roomIndex: number, field: string, value: any) => void;
  removeRoom: (buildingId: string, floorIndex: number, roomIndex: number) => void;
  addRoomToBuilding: (buildingId: string) => void;
  updateRoomInBuilding: (buildingId: string, roomIndex: number, field: string, value: any) => void;
  removeRoomFromBuilding: (buildingId: string, roomIndex: number) => void;
  handleBuildingPhotoUpload: (buildingId: string, e: React.ChangeEvent<HTMLInputElement>) => void;
  handlePhotoDrop: (buildingId: string, e: React.DragEvent<HTMLDivElement>) => void;
  removeBuildingPhoto: (buildingId: string, photoId: string) => void;
  updateBuildingPhotoCaption: (buildingId: string, photoId: string, caption: string) => void;
  floorCount: { [buildingId: string]: number };
  setFloorCount: React.Dispatch<React.SetStateAction<{ [buildingId: string]: number }>>;
  floorsExpanded: { [buildingId: string]: boolean };
  setFloorsExpanded: React.Dispatch<React.SetStateAction<{ [buildingId: string]: boolean }>>;
  uploadingPhotos: { [buildingId: string]: boolean };
  register: any;
  watch: any;
  setValue: any;
}

export const BuildingDescriptionTab: React.FC<BuildingDescriptionTabProps> = ({
  buildings,
  expandedBuilding,
  setExpandedBuilding,
  addBuilding,
  removeBuilding,
  updateBuilding,
  updateBuildingConstructionMaterial,
  generateFloors,
  updateFloorName,
  updateFloorArea,
  addRoomToBuilding,
  updateRoomInBuilding,
  removeRoomFromBuilding,
  handleBuildingPhotoUpload,
  handlePhotoDrop,
  removeBuildingPhoto,
  updateBuildingPhotoCaption,
  floorCount,
  setFloorCount,
  floorsExpanded,
  setFloorsExpanded,
  uploadingPhotos,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-gray-900">Building Details</h3>
        <Button
          type="button"
          onClick={addBuilding}
          className="bg-emerald-600 hover:bg-emerald-700 text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Building
        </Button>
      </div>

      {buildings.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
          <Building2 className="h-12 w-12 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 mb-4">No buildings added yet</p>
          <Button
            type="button"
            onClick={addBuilding}
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add First Building
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {buildings.map((building, index) => (
            <div
              key={building.id}
              className="border border-gray-200 rounded-xl overflow-hidden"
            >
              <BuildingHeader
                building={building}
                buildingIndex={index}
                expandedBuilding={expandedBuilding}
                setExpandedBuilding={setExpandedBuilding}
                removeBuilding={removeBuilding}
              />

              {expandedBuilding === building.id && (
                <div className="p-4 space-y-4">
                  <BuildingConstructionSection
                    building={building}
                    updateBuilding={updateBuilding}
                    updateBuildingConstructionMaterial={updateBuildingConstructionMaterial}
                  />

                  <BuildingFloorsSection
                    building={building}
                    floorCount={floorCount}
                    setFloorCount={setFloorCount}
                    floorsExpanded={floorsExpanded}
                    setFloorsExpanded={setFloorsExpanded}
                    generateFloors={generateFloors}
                    updateFloorName={updateFloorName}
                    updateFloorArea={updateFloorArea}
                  />

                  <BuildingRoomsSection
                    building={building}
                    addRoomToBuilding={addRoomToBuilding}
                    updateRoomInBuilding={updateRoomInBuilding}
                    removeRoomFromBuilding={removeRoomFromBuilding}
                  />

                  <BuildingPhotosSection
                    building={building}
                    uploadingPhotos={uploadingPhotos}
                    handleBuildingPhotoUpload={handleBuildingPhotoUpload}
                    handlePhotoDrop={handlePhotoDrop}
                    removeBuildingPhoto={removeBuildingPhoto}
                    updateBuildingPhotoCaption={updateBuildingPhotoCaption}
                    updateBuilding={updateBuilding}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BuildingDescriptionTab;
