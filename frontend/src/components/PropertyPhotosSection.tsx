import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import {
  Camera,
  Upload,
  X,
  Loader2
} from 'lucide-react';
import { Input } from './Input';
import { Label } from './Label';
import { MAX_PROPERTY_PHOTOS } from '../constants/propertyDescriptionConstants';
import type { PropertyPhoto } from '../types/propertyDescription';

interface PropertyPhotosSectionProps {
  watch: any;
  setValue: any;
}

export const PropertyPhotosSection: React.FC<PropertyPhotosSectionProps> = ({ watch, setValue }) => {
  const [propertyPhotos, setPropertyPhotos] = useState<PropertyPhoto[]>([]);
  const [uploadingPropertyPhotos, setUploadingPropertyPhotos] = useState(false);

  const formPropertyPhotos = watch('property_photos');

  useEffect(() => {
    if (formPropertyPhotos && Array.isArray(formPropertyPhotos) && formPropertyPhotos.length > 0) {
      setPropertyPhotos(formPropertyPhotos);
    }
  }, []);

  // Handle property photo upload
  const handlePropertyPhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    if (propertyPhotos.length >= MAX_PROPERTY_PHOTOS) {
      toast.error(`Maximum ${MAX_PROPERTY_PHOTOS} photos reached`);
      return;
    }

    const filesToProcess = Array.from(files).slice(0, MAX_PROPERTY_PHOTOS - propertyPhotos.length);
    const photoCount = filesToProcess.length;

    // Set loading state
    setUploadingPropertyPhotos(true);

    // Show loading toast
    const toastId = toast.loading(`Uploading ${photoCount} photo${photoCount > 1 ? 's' : ''}...`);

    const newPhotos: PropertyPhoto[] = [];
    const startingOrder = propertyPhotos.length + 1;

    try {
      // Read all files sequentially
      for (let i = 0; i < filesToProcess.length; i++) {
        try {
          const imageData = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(filesToProcess[i]);
          });

          newPhotos.push({
            id: `photo-${Date.now()}-${i}`,
            image_data: imageData,
            caption: '',
            order: startingOrder + i
          });
        } catch (error) {
          console.error('Error reading file:', error);
          toast.error(`Failed to read ${filesToProcess[i].name}`);
        }
      }

      // Single state update with all photos
      if (newPhotos.length > 0) {
        const updated = [...propertyPhotos, ...newPhotos];
        setPropertyPhotos(updated);
        setValue('property_photos', updated);

        // Show success toast
        toast.success(`\u2713 ${newPhotos.length} photo${newPhotos.length > 1 ? 's' : ''} uploaded successfully`, {
          id: toastId,
        });
      } else {
        toast.dismiss(toastId);
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload photos. Please try again.', { id: toastId });
    } finally {
      // Clear loading state
      setUploadingPropertyPhotos(false);
    }
  };

  // Handle drag and drop for property photos
  const handlePropertyPhotoDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (!files) return;

    if (propertyPhotos.length >= MAX_PROPERTY_PHOTOS) {
      toast.error(`Maximum ${MAX_PROPERTY_PHOTOS} photos reached`);
      return;
    }

    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
      toast.error('Please drop only image files');
      return;
    }

    const filesToProcess = imageFiles.slice(0, MAX_PROPERTY_PHOTOS - propertyPhotos.length);
    const photoCount = filesToProcess.length;

    // Set loading state
    setUploadingPropertyPhotos(true);

    // Show loading toast
    const toastId = toast.loading(`Uploading ${photoCount} photo${photoCount > 1 ? 's' : ''}...`);

    const newPhotos: PropertyPhoto[] = [];
    const startingOrder = propertyPhotos.length + 1;

    try {
      // Read all files sequentially
      for (let i = 0; i < filesToProcess.length; i++) {
        try {
          const imageData = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(filesToProcess[i]);
          });

          newPhotos.push({
            id: `photo-${Date.now()}-${i}`,
            image_data: imageData,
            caption: '',
            order: startingOrder + i
          });
        } catch (error) {
          console.error('Error reading file:', error);
          toast.error(`Failed to read ${filesToProcess[i].name}`);
        }
      }

      // Single state update with all photos
      if (newPhotos.length > 0) {
        const updated = [...propertyPhotos, ...newPhotos];
        setPropertyPhotos(updated);
        setValue('property_photos', updated);

        // Show success toast
        toast.success(`\u2713 ${newPhotos.length} photo${newPhotos.length > 1 ? 's' : ''} uploaded successfully`, {
          id: toastId,
        });
      } else {
        toast.dismiss(toastId);
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload photos. Please try again.', { id: toastId });
    } finally {
      // Clear loading state
      setUploadingPropertyPhotos(false);
    }
  };

  // Remove property photo
  const removePropertyPhoto = (photoId: string) => {
    const updated = propertyPhotos.filter(p => p.id !== photoId);
    setPropertyPhotos(updated);
    setValue('property_photos', updated);
    toast.success('Photo removed');
  };

  // Update property photo caption
  const updatePropertyPhotoCaption = (photoId: string, caption: string) => {
    const updated = propertyPhotos.map(p =>
      p.id === photoId ? { ...p, caption } : p
    );
    setPropertyPhotos(updated);
    setValue('property_photos', updated);
  };

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <Label className="flex items-center space-x-2">
          <Camera className="h-5 w-5 text-emerald-600" />
          <span>Property Photos (Max {MAX_PROPERTY_PHOTOS})</span>
        </Label>
        <span className="text-sm text-gray-500">
          {propertyPhotos.length} / {MAX_PROPERTY_PHOTOS}
        </span>
      </div>

      {/* Photo Upload Area */}
      {propertyPhotos.length < MAX_PROPERTY_PHOTOS && (
        <div
          className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors mb-4 ${
            uploadingPropertyPhotos
              ? 'border-emerald-500 bg-emerald-50/50'
              : 'border-gray-300 hover:border-emerald-500'
          }`}
          onDrop={handlePropertyPhotoDrop}
          onDragOver={(e) => e.preventDefault()}
          onDragEnter={(e) => e.preventDefault()}
        >
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handlePropertyPhotoUpload}
            className="hidden"
            id="property-photo-upload"
            disabled={uploadingPropertyPhotos}
          />
          <label htmlFor="property-photo-upload" className={uploadingPropertyPhotos ? 'cursor-not-allowed' : 'cursor-pointer'}>
            {uploadingPropertyPhotos ? (
              <>
                <Loader2 className="h-10 w-10 mx-auto text-emerald-600 mb-2 animate-spin" />
                <p className="text-emerald-700 text-sm font-medium mb-1">
                  Uploading photos...
                </p>
                <p className="text-xs text-emerald-600">
                  Please wait while we process your images
                </p>
              </>
            ) : (
              <>
                <Upload className="h-10 w-10 mx-auto text-gray-400 mb-2" />
                <p className="text-gray-600 text-sm font-medium mb-1">
                  Click to upload or drag & drop photos
                </p>
                <p className="text-xs text-gray-500 mb-2">
                  Tip: Select multiple files using Ctrl+Click or Shift+Click
                </p>
                <p className="text-xs text-gray-400">
                  PNG, JPG up to 10MB each {'\u2022'} {MAX_PROPERTY_PHOTOS - propertyPhotos.length} slot{MAX_PROPERTY_PHOTOS - propertyPhotos.length !== 1 ? 's' : ''} remaining
                </p>
              </>
            )}
          </label>
        </div>
      )}

      {/* Photo Grid */}
      {propertyPhotos.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {propertyPhotos.map((photo, photoIndex) => (
            <div key={photo.id} className="border border-gray-200 rounded-xl overflow-hidden">
              <div className="relative aspect-video bg-gray-100">
                <img
                  src={photo.image_data}
                  alt={photo.caption || `Photo ${photoIndex + 1}`}
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={() => removePropertyPhoto(photo.id)}
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
                  onChange={(e) => updatePropertyPhotoCaption(photo.id, e.target.value)}
                  placeholder={`Caption for Fig. ${String(photoIndex + 1).padStart(2, '0')}`}
                  className="text-sm"
                />
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-500 mt-4 italic">
        These photos will appear in Section 4.0 (Description of Property) in the final report
      </p>
    </div>
  );
};

export default PropertyPhotosSection;
