import toast from 'react-hot-toast';
import type { Building, BuildingPhoto } from '../types';
import { MAX_BUILDING_PHOTOS } from '../constants/propertyDescriptionConstants';

export function useBuildingPhotos(
  buildings: Building[],
  setBuildings: React.Dispatch<React.SetStateAction<Building[]>>,
  setValue: any,
  setUploadingPhotos: React.Dispatch<React.SetStateAction<{ [buildingId: string]: boolean }>>
) {
  const handleBuildingPhotoUpload = async (buildingId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const building = buildings.find(b => b.id === buildingId);
    if (!building || building.building_photos.length >= MAX_BUILDING_PHOTOS) {
      if (building && building.building_photos.length >= MAX_BUILDING_PHOTOS) {
        toast.error(`Maximum ${MAX_BUILDING_PHOTOS} photos per building reached`);
      }
      return;
    }

    const filesToProcess = Array.from(files).slice(0, MAX_BUILDING_PHOTOS - building.building_photos.length);
    const photoCount = filesToProcess.length;

    setUploadingPhotos(prev => ({ ...prev, [buildingId]: true }));
    const toastId = toast.loading(`Uploading ${photoCount} photo${photoCount > 1 ? 's' : ''}...`);

    const newPhotos: BuildingPhoto[] = [];
    const startingOrder = building.building_photos.length + 1;

    try {
      for (let i = 0; i < filesToProcess.length; i++) {
        try {
          const imageData = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(filesToProcess[i]);
          });

          newPhotos.push({
            id: `photo_${Date.now()}_${i}`,
            image_data: imageData,
            caption: '',
            order: startingOrder + i
          });
        } catch (error) {
          console.error('Error reading file:', error);
          toast.error(`Failed to read ${filesToProcess[i].name}`);
        }
      }

      if (newPhotos.length > 0) {
        const updated = buildings.map(b =>
          b.id === buildingId
            ? { ...b, building_photos: [...b.building_photos, ...newPhotos] }
            : b
        );
        setBuildings(updated);
        setValue('buildings', updated);

        toast.success(`\u2713 ${newPhotos.length} photo${newPhotos.length > 1 ? 's' : ''} uploaded successfully`, {
          id: toastId,
        });
      } else {
        toast.error('Failed to upload photos', { id: toastId });
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('An error occurred during upload', { id: toastId });
    } finally {
      setUploadingPhotos(prev => ({ ...prev, [buildingId]: false }));
      e.target.value = '';
    }
  };

  const handlePhotoDrop = async (buildingId: string, e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (!files) return;

    const building = buildings.find(b => b.id === buildingId);
    if (!building || building.building_photos.length >= MAX_BUILDING_PHOTOS) {
      if (building && building.building_photos.length >= MAX_BUILDING_PHOTOS) {
        toast.error(`Maximum ${MAX_BUILDING_PHOTOS} photos per building reached`);
      }
      return;
    }

    const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
      toast.error('Please drop only image files');
      return;
    }

    const filesToProcess = imageFiles.slice(0, MAX_BUILDING_PHOTOS - building.building_photos.length);
    const photoCount = filesToProcess.length;

    setUploadingPhotos(prev => ({ ...prev, [buildingId]: true }));
    const toastId = toast.loading(`Uploading ${photoCount} photo${photoCount > 1 ? 's' : ''}...`);

    const newPhotos: BuildingPhoto[] = [];
    const startingOrder = building.building_photos.length + 1;

    try {
      for (let i = 0; i < filesToProcess.length; i++) {
        try {
          const imageData = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(filesToProcess[i]);
          });

          newPhotos.push({
            id: `photo_${Date.now()}_${i}`,
            image_data: imageData,
            caption: '',
            order: startingOrder + i
          });
        } catch (error) {
          console.error('Error reading file:', error);
          toast.error(`Failed to read ${filesToProcess[i].name}`);
        }
      }

      if (newPhotos.length > 0) {
        const updated = buildings.map(b =>
          b.id === buildingId
            ? { ...b, building_photos: [...b.building_photos, ...newPhotos] }
            : b
        );
        setBuildings(updated);
        setValue('buildings', updated);

        toast.success(`\u2713 ${newPhotos.length} photo${newPhotos.length > 1 ? 's' : ''} uploaded successfully`, {
          id: toastId,
        });
      } else {
        toast.error('Failed to upload photos', { id: toastId });
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('An error occurred during upload', { id: toastId });
    } finally {
      setUploadingPhotos(prev => ({ ...prev, [buildingId]: false }));
    }
  };

  const removeBuildingPhoto = (buildingId: string, photoId: string) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        return { ...b, building_photos: b.building_photos.filter(p => p.id !== photoId) };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  const updateBuildingPhotoCaption = (buildingId: string, photoId: string, caption: string) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        return {
          ...b,
          building_photos: b.building_photos.map(p =>
            p.id === photoId ? { ...p, caption } : p
          )
        };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  return {
    handleBuildingPhotoUpload,
    handlePhotoDrop,
    removeBuildingPhoto,
    updateBuildingPhotoCaption,
  };
}
