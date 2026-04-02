/**
 * VehiclePhotosStep - Step 2 of Vehicle Report Form
 *
 * Upload up to 5 vehicle photos with:
 * - Drag-drop and click upload
 * - Preview with delete option
 * - Caption editing
 * - Reorder support
 */

import React, { useState, useCallback } from 'react';
import { useFormContext } from 'react-hook-form';
import { Camera, Upload, X, GripVertical, Loader2, Image as ImageIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import type { VehiclePhoto } from '../../types';

const MAX_VEHICLE_PHOTOS = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const VehiclePhotosStep: React.FC = () => {
  const { watch, setValue } = useFormContext();
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const vehiclePhotos: VehiclePhoto[] = watch('vehicle_photos') || [];

  // Generate unique ID
  const generateId = () => `photo-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Process file to base64, resized to max 827px (7cm at 300 DPI) before storing
  const MAX_PHOTO_DIM = 827;

  const processFile = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          let { width, height } = img;
          if (width > MAX_PHOTO_DIM || height > MAX_PHOTO_DIM) {
            if (width >= height) {
              height = Math.round(height * MAX_PHOTO_DIM / width);
              width = MAX_PHOTO_DIM;
            } else {
              width = Math.round(width * MAX_PHOTO_DIM / height);
              height = MAX_PHOTO_DIM;
            }
          }
          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          canvas.getContext('2d')!.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL('image/jpeg', 0.85));
        };
        img.onerror = reject;
        img.src = e.target?.result as string;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  // Handle file selection
  const handleFileSelect = useCallback(async (files: FileList | File[]) => {
    if (vehiclePhotos.length >= MAX_VEHICLE_PHOTOS) {
      toast.error(`Maximum ${MAX_VEHICLE_PHOTOS} photos allowed`);
      return;
    }

    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(file => {
      if (!file.type.startsWith('image/')) {
        toast.error(`${file.name} is not an image file`);
        return false;
      }
      if (file.size > MAX_FILE_SIZE) {
        toast.error(`${file.name} exceeds 10MB limit`);
        return false;
      }
      return true;
    });

    const slotsAvailable = MAX_VEHICLE_PHOTOS - vehiclePhotos.length;
    const filesToProcess = validFiles.slice(0, slotsAvailable);

    if (filesToProcess.length === 0) return;

    setIsUploading(true);
    const toastId = toast.loading(`Uploading ${filesToProcess.length} photo(s)...`);

    try {
      const newPhotos: VehiclePhoto[] = await Promise.all(
        filesToProcess.map(async (file, index) => {
          const imageData = await processFile(file);
          return {
            id: generateId(),
            image_data: imageData,
            caption: '',
            order: vehiclePhotos.length + index + 1,
          };
        })
      );

      setValue('vehicle_photos', [...vehiclePhotos, ...newPhotos]);
      toast.success(`${newPhotos.length} photo(s) uploaded successfully`, { id: toastId });
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload photos', { id: toastId });
    } finally {
      setIsUploading(false);
    }
  }, [vehiclePhotos, setValue]);

  // Handle drag and drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files).filter(file =>
      file.type.startsWith('image/')
    );

    if (files.length === 0) {
      toast.error('Please drop only image files');
      return;
    }

    handleFileSelect(files);
  }, [handleFileSelect]);

  // Handle file input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files);
    }
    e.target.value = ''; // Reset input
  };

  // Delete photo
  const handleDeletePhoto = (photoId: string) => {
    const updated = vehiclePhotos.filter(p => p.id !== photoId);
    setValue('vehicle_photos', updated);
    toast.success('Photo removed');
  };

  // Update caption
  const handleUpdateCaption = (photoId: string, caption: string) => {
    const updated = vehiclePhotos.map(p =>
      p.id === photoId ? { ...p, caption } : p
    );
    setValue('vehicle_photos', updated);
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-300
          ${isDragOver
            ? 'border-emerald-500 bg-emerald-50'
            : 'border-gray-300 hover:border-emerald-400 bg-gray-50/50'
          }
          ${isUploading ? 'pointer-events-none' : 'cursor-pointer'}
        `}
      >
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={handleInputChange}
          disabled={isUploading || vehiclePhotos.length >= MAX_VEHICLE_PHOTOS}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          id="vehicle-photo-upload"
        />

        <div className="space-y-4">
          <div className={`
            mx-auto w-16 h-16 rounded-2xl flex items-center justify-center transition-all
            ${isDragOver ? 'bg-emerald-500 text-white scale-110' : 'bg-gray-200 text-gray-500'}
          `}>
            {isUploading ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <Camera className="w-8 h-8" />
            )}
          </div>

          <div>
            {isUploading ? (
              <p className="text-gray-600 font-medium">Uploading photos...</p>
            ) : vehiclePhotos.length >= MAX_VEHICLE_PHOTOS ? (
              <p className="text-gray-600 font-medium">Maximum photos reached</p>
            ) : (
              <>
                <p className="text-gray-700 font-medium">
                  Click to upload or drag & drop photos
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  PNG, JPG up to 10MB each • {MAX_VEHICLE_PHOTOS - vehiclePhotos.length} slot{MAX_VEHICLE_PHOTOS - vehiclePhotos.length !== 1 ? 's' : ''} remaining
                </p>
              </>
            )}
          </div>

          {!isUploading && vehiclePhotos.length < MAX_VEHICLE_PHOTOS && (
            <label
              htmlFor="vehicle-photo-upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-xl hover:bg-emerald-600 transition-colors cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              Select Photos
            </label>
          )}
        </div>
      </div>

      {/* Photo Counter */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">
          <Camera className="w-4 h-4 inline-block mr-1" />
          {vehiclePhotos.length} of {MAX_VEHICLE_PHOTOS} photos uploaded
        </span>
        {vehiclePhotos.length > 0 && (
          <span className="text-gray-500">
            Tip: Add captions to describe each photo
          </span>
        )}
      </div>

      {/* Photo Grid */}
      {vehiclePhotos.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {vehiclePhotos.map((photo, index) => (
            <div
              key={photo.id}
              className="relative group bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Photo Preview */}
              <div className="aspect-[4/3] relative">
                <img
                  src={photo.image_data}
                  alt={photo.caption || `Vehicle photo ${index + 1}`}
                  className="w-full h-full object-cover"
                />

                {/* Order Badge */}
                <div className="absolute top-2 left-2 w-8 h-8 bg-black/70 text-white rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>

                {/* Delete Button */}
                <button
                  type="button"
                  onClick={() => handleDeletePhoto(photo.id)}
                  className="absolute top-2 right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                >
                  <X className="w-4 h-4" />
                </button>

                {/* Drag Handle (for future reorder) */}
                <div className="absolute bottom-2 right-2 w-8 h-8 bg-black/50 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-grab">
                  <GripVertical className="w-4 h-4" />
                </div>
              </div>

              {/* Caption Input */}
              <div className="p-3">
                <input
                  type="text"
                  value={photo.caption || ''}
                  onChange={(e) => handleUpdateCaption(photo.id, e.target.value)}
                  placeholder="Add a caption..."
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {vehiclePhotos.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <ImageIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>No photos uploaded yet</p>
          <p className="text-sm mt-1">
            Upload photos of the vehicle exterior, interior, engine, and any damage
          </p>
        </div>
      )}

      {/* Tips */}
      <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-100">
        <p className="text-sm text-emerald-800 font-medium mb-2">
          Photo Tips for Vehicle Valuation
        </p>
        <ul className="text-sm text-emerald-700 space-y-1">
          <li>• Front and rear exterior views</li>
          <li>• Interior dashboard and seats</li>
          <li>• Engine compartment</li>
          <li>• Any visible damage or wear</li>
          <li>• Odometer reading</li>
        </ul>
      </div>
    </div>
  );
};

export default VehiclePhotosStep;
