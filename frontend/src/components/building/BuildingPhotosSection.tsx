import React from 'react';
import { Camera, Upload, X, Loader2, Building2 } from 'lucide-react';
import { Input } from '../Input';
import { Label } from '../Label';
import type { Building } from '../../types';
import { MAX_BUILDING_PHOTOS } from '../../constants/propertyDescriptionConstants';

interface BuildingPhotosSectionProps {
  building: Building;
  uploadingPhotos: { [buildingId: string]: boolean };
  handleBuildingPhotoUpload: (buildingId: string, e: React.ChangeEvent<HTMLInputElement>) => void;
  handlePhotoDrop: (buildingId: string, e: React.DragEvent<HTMLDivElement>) => void;
  removeBuildingPhoto: (buildingId: string, photoId: string) => void;
  updateBuildingPhotoCaption: (buildingId: string, photoId: string, caption: string) => void;
  updateBuilding: (id: string, field: string, value: any) => void;
}

export const BuildingPhotosSection: React.FC<BuildingPhotosSectionProps> = ({
  building,
  uploadingPhotos,
  handleBuildingPhotoUpload,
  handlePhotoDrop,
  removeBuildingPhoto,
  updateBuildingPhotoCaption,
  updateBuilding,
}) => {
  return (
    <>
      {/* Building Photos */}
      <div className="border-t border-gray-200 pt-4 mt-4">
        <div className="flex items-center justify-between mb-4">
          <Label className="flex items-center space-x-2">
            <Camera className="h-5 w-5 text-emerald-600" />
            <span>Building Photos (Max {MAX_BUILDING_PHOTOS})</span>
          </Label>
          <span className="text-sm text-gray-500">
            {building.building_photos.length} / {MAX_BUILDING_PHOTOS}
          </span>
        </div>

        {building.building_photos.length < MAX_BUILDING_PHOTOS && (
          <div
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors mb-4 ${
              uploadingPhotos[building.id]
                ? 'border-emerald-500 bg-emerald-50/50'
                : 'border-gray-300 hover:border-emerald-500'
            }`}
            onDrop={(e) => handlePhotoDrop(building.id, e)}
            onDragOver={(e) => e.preventDefault()}
            onDragEnter={(e) => e.preventDefault()}
          >
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => handleBuildingPhotoUpload(building.id, e)}
              className="hidden"
              id={`photo-upload-${building.id}`}
              disabled={uploadingPhotos[building.id]}
            />
            <label htmlFor={`photo-upload-${building.id}`} className={uploadingPhotos[building.id] ? 'cursor-not-allowed' : 'cursor-pointer'}>
              {uploadingPhotos[building.id] ? (
                <>
                  <Loader2 className="h-10 w-10 mx-auto text-emerald-600 mb-2 animate-spin" />
                  <p className="text-emerald-700 text-sm font-medium mb-1">Uploading photos...</p>
                  <p className="text-xs text-emerald-600">Please wait while we process your images</p>
                </>
              ) : (
                <>
                  <Upload className="h-10 w-10 mx-auto text-gray-400 mb-2" />
                  <p className="text-gray-600 text-sm font-medium mb-1">Click to upload or drag &amp; drop photos</p>
                  <p className="text-xs text-gray-500 mb-2">Tip: Select multiple files using Ctrl+Click or Shift+Click</p>
                  <p className="text-xs text-gray-400">
                    PNG, JPG up to 10MB each {'\u2022'} {MAX_BUILDING_PHOTOS - building.building_photos.length} slot{MAX_BUILDING_PHOTOS - building.building_photos.length !== 1 ? 's' : ''} remaining
                  </p>
                </>
              )}
            </label>
          </div>
        )}

        {building.building_photos.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {building.building_photos.map((photo, photoIndex) => (
              <div key={photo.id} className="border border-gray-200 rounded-xl overflow-hidden">
                <div className="relative aspect-video bg-gray-100">
                  <img
                    src={photo.image_data}
                    alt={photo.caption || `Photo ${photoIndex + 1}`}
                    className="w-full h-full object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => removeBuildingPhoto(building.id, photo.id)}
                    className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <span className="absolute top-2 left-2 px-2 py-1 bg-black/50 text-white text-xs rounded">
                    Fig. {String(photoIndex + 1).padStart(2, '0')}
                  </span>
                </div>
                <div className="p-3">
                  <Input
                    value={photo.caption}
                    onChange={(e) => updateBuildingPhotoCaption(building.id, photo.id, e.target.value)}
                    placeholder={`Caption for Fig. ${String(photoIndex + 1).padStart(2, '0')}`}
                    className="text-sm"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Additional Structures */}
      <div className="border-t border-gray-200 pt-4 mt-4">
        <Label className="text-base font-semibold mb-2 flex items-center">
          <Building2 className="h-5 w-5 mr-2 text-amber-600" />
          Additional Structures (Optional)
        </Label>
        <p className="text-sm text-gray-600 mb-3">
          Describe any separate or unattached structures on the property (e.g., store rooms, garages, outbuildings, sheds, water tanks, etc.)
        </p>
        <textarea
          value={building.additional_structures_description || ''}
          onChange={(e) => updateBuilding(building.id, 'additional_structures_description', e.target.value)}
          rows={4}
          maxLength={2000}
          placeholder="e.g., A separate 15x10 ft store room with cadjan roof and brick walls located at the rear of the property. A concrete water tank with 5,000L capacity."
          className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
        />
        <div className="flex justify-between mt-1">
          <p className="text-xs text-gray-500 italic">
            This description will appear as a separate section in the valuation report
          </p>
          <p className="text-xs text-gray-400">
            {building.additional_structures_description?.length || 0} / 2000 characters
          </p>
        </div>
      </div>
    </>
  );
};
