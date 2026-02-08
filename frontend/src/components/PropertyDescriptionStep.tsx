import React, { useState } from 'react';
import { Mountain, Building2 } from 'lucide-react';
import { LandDescriptionTab } from './LandDescriptionTab';
import { BuildingDescriptionTab } from './BuildingDescriptionTab';
import { useBuildingManager } from '../hooks/useBuildingManager';
import type { TabType, PropertyDescriptionStepProps } from '../types/propertyDescription';

export const PropertyDescriptionStep: React.FC<PropertyDescriptionStepProps> = ({
  register,
  errors,
  watch,
  setValue,
  isBareLand = false
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('land');

  const buildingManager = useBuildingManager({ watch, setValue });

  const tabs = isBareLand
    ? [{ id: 'land' as TabType, label: 'Land Description', icon: Mountain }]
    : [
        { id: 'land' as TabType, label: 'Land Description', icon: Mountain },
        { id: 'building' as TabType, label: 'Building Details', icon: Building2 },
      ];

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex space-x-2 bg-gray-100 p-1 rounded-xl">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-white text-emerald-600 shadow-md'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200/50 p-6">
        {activeTab === 'land' && (
          <LandDescriptionTab
            register={register}
            errors={errors}
            watch={watch}
            setValue={setValue}
            isBareLand={isBareLand}
          />
        )}

        {activeTab === 'building' && !isBareLand && (
          <BuildingDescriptionTab
            buildings={buildingManager.buildings}
            expandedBuilding={buildingManager.expandedBuilding}
            setExpandedBuilding={buildingManager.setExpandedBuilding}
            addBuilding={buildingManager.addBuilding}
            removeBuilding={buildingManager.removeBuilding}
            updateBuilding={buildingManager.updateBuilding}
            copyOccupierFromFirstBuilding={buildingManager.copyOccupierFromFirstBuilding}
            updateBuildingConstructionMaterial={buildingManager.updateBuildingConstructionMaterial}
            generateFloors={buildingManager.generateFloors}
            addFloor={buildingManager.addFloor}
            updateFloorName={buildingManager.updateFloorName}
            updateFloorArea={buildingManager.updateFloorArea}
            addRoom={buildingManager.addRoom}
            updateRoom={buildingManager.updateRoom}
            removeRoom={buildingManager.removeRoom}
            addRoomToBuilding={buildingManager.addRoomToBuilding}
            updateRoomInBuilding={buildingManager.updateRoomInBuilding}
            removeRoomFromBuilding={buildingManager.removeRoomFromBuilding}
            handleBuildingPhotoUpload={buildingManager.handleBuildingPhotoUpload}
            handlePhotoDrop={buildingManager.handlePhotoDrop}
            removeBuildingPhoto={buildingManager.removeBuildingPhoto}
            updateBuildingPhotoCaption={buildingManager.updateBuildingPhotoCaption}
            floorCount={buildingManager.floorCount}
            setFloorCount={buildingManager.setFloorCount}
            floorsExpanded={buildingManager.floorsExpanded}
            setFloorsExpanded={buildingManager.setFloorsExpanded}
            uploadingPhotos={buildingManager.uploadingPhotos}
            register={register}
            watch={watch}
            setValue={setValue}
          />
        )}
      </div>
    </div>
  );
};

export default PropertyDescriptionStep;
