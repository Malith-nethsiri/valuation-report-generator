import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import type { Building, Room, BuildingPhoto } from '../types';
import { MAX_BUILDING_PHOTOS, FLOOR_NAMES } from '../constants/propertyDescriptionConstants';

interface UseBuildingManagerProps {
  watch: any;
  setValue: any;
}

export function useBuildingManager({ watch, setValue }: UseBuildingManagerProps) {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [expandedBuilding, setExpandedBuilding] = useState<string | null>(null);
  const [floorCount, setFloorCount] = useState<{[buildingId: string]: number}>({});
  const [floorsExpanded, setFloorsExpanded] = useState<{[buildingId: string]: boolean}>({});
  const [uploadingPhotos, setUploadingPhotos] = useState<{[buildingId: string]: boolean}>({});

  // Initialize buildings from form values on mount
  const formBuildings = watch('buildings');

  // Normalize building data to ensure all required properties exist
  const normalizeBuilding = (building: any): Building => {
    // Migrate old age_description (string) to building_age (number)
    let buildingAge = building.building_age;
    if (buildingAge === undefined && building.age_description) {
      // Try to extract numeric value from old text field (e.g., "about 10 years old" -> 10)
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

  useEffect(() => {
    if (formBuildings && Array.isArray(formBuildings) && formBuildings.length > 0) {
      const normalized = formBuildings.map(normalizeBuilding);
      setBuildings(normalized);
      // CRITICAL: Sync normalized data back to form state so it gets submitted correctly
      setValue('buildings', normalized);

      // Initialize floorsExpanded to true for all buildings with floors
      const initialFloorsExpanded: {[buildingId: string]: boolean} = {};
      normalized.forEach(building => {
        if (building.floors && building.floors.length > 0) {
          initialFloorsExpanded[building.id] = true;
        }
      });
      setFloorsExpanded(initialFloorsExpanded);
    }
  }, []);

  // Auto-fill occupier info from applicant name when step loads
  useEffect(() => {
    const applicantFullName = watch('applicant_full_name');
    const currentOccupierName = watch('occupier_name');

    // Only auto-fill if occupier_name is empty and applicant name exists
    if (!currentOccupierName && applicantFullName) {
      setValue('occupier_name', applicantFullName);
      setValue('occupier_relationship', 'owner');
    }

    // Also auto-fill for all existing buildings
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

      // Only update if changes were made
      const hasChanges = updatedBuildings.some((b: Building, i: number) =>
        b.occupier_name !== currentBuildings[i].occupier_name
      );
      if (hasChanges) {
        setValue('buildings', updatedBuildings);
        setBuildings(updatedBuildings);
      }
    }
  }, []); // Run once on mount (when step is reached)

  // NEW: Calculate accommodation summary from rooms array (supports both count-based and old individual room approach)
  const calculateAccommodationSummary = (rooms: Room[]) => {
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
      const count = room.count || 1; // Use count if present, otherwise default to 1 for backward compatibility

      if (type.includes('bedroom') && !type.includes('attached')) summary.bedrooms += count;
      else if (type.includes('attached bathroom')) summary.bathrooms += count; // Attached bathrooms count as regular bathrooms
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

  // Add new building
  const addBuilding = () => {
    // Auto-fill occupier info from applicant name for new buildings
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

    // Initialize floorsExpanded to true for new building
    setFloorsExpanded(prev => ({
      ...prev,
      [newBuilding.id]: true
    }));
  };

  // Remove building
  const removeBuilding = (id: string) => {
    const updated = buildings.filter(b => b.id !== id);
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // Update building
  const updateBuilding = (id: string, field: string, value: any) => {
    const updated = buildings.map(b => {
      if (b.id === id) {
        const updatedBuilding = { ...b, [field]: value };
        // Auto-calculate stories from number of floors
        updatedBuilding.stories = updatedBuilding.floors.length;
        // Auto-calculate total floor area from sum of individual floor areas
        updatedBuilding.total_floor_area = updatedBuilding.floors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
        return updatedBuilding;
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // Copy occupier information from first building to target building
  const copyOccupierFromFirstBuilding = (targetBuildingId: string) => {
    if (buildings.length === 0) return;

    const firstBuilding = buildings[0];
    updateBuilding(targetBuildingId, 'occupier_name', firstBuilding.occupier_name || '');
    updateBuilding(targetBuildingId, 'occupier_relationship', firstBuilding.occupier_relationship || '');
  };

  // NEW: Update nested construction material fields
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
        return {
          ...b,
          construction_materials: updatedMaterials
        };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // Generate multiple floors at once (FLOOR_NAMES imported from constants)
  const generateFloors = (buildingId: string, count: number) => {
    if (count < 1 || count > 10) return;

    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = Array.from({ length: count }, (_, i) => ({
          floor_name: FLOOR_NAMES[i] || `Floor ${i + 1}`,
          floor_area: 0
        }));
        // Calculate total floor area
        const total_floor_area = newFloors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
        return { ...b, floors: newFloors, total_floor_area };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // Add floor to building
  const addFloor = (buildingId: string) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const floorNum = b.floors.length + 1;
        const floorName = floorNum === 1 ? 'Ground Floor' :
                         floorNum === 2 ? 'First Floor' :
                         floorNum === 3 ? 'Second Floor' : `Floor ${floorNum}`;
        const updatedFloors = [...b.floors, { floor_name: floorName, floor_area: 0 }];
        // Calculate total floor area
        const total_floor_area = updatedFloors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
        return {
          ...b,
          floors: updatedFloors,
          total_floor_area
        };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // Update floor name
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

  // Add room to floor (NEW: Simplified count-based approach)
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
        // Auto-calculate accommodation summary
        newFloors[floorIndex].accommodation_summary = calculateAccommodationSummary(newFloors[floorIndex].rooms!);
        return { ...b, floors: newFloors };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // NEW: Update room details with auto-summary recalculation
  const updateRoom = (buildingId: string, floorIndex: number, roomIndex: number, field: string, value: any) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = [...b.floors];
        const updatedRooms = [...(newFloors[floorIndex].rooms || [])];
        updatedRooms[roomIndex] = { ...updatedRooms[roomIndex], [field]: value };
        newFloors[floorIndex].rooms = updatedRooms;
        // Auto-recalculate accommodation summary
        newFloors[floorIndex].accommodation_summary = calculateAccommodationSummary(updatedRooms);
        return { ...b, floors: newFloors };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // NEW: Remove room with auto-summary recalculation
  const removeRoom = (buildingId: string, floorIndex: number, roomIndex: number) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = [...b.floors];
        const updatedRooms = (newFloors[floorIndex].rooms || []).filter((_: Room, idx: number) => idx !== roomIndex);
        newFloors[floorIndex].rooms = updatedRooms;
        // Auto-recalculate accommodation summary
        newFloors[floorIndex].accommodation_summary = calculateAccommodationSummary(updatedRooms);
        return { ...b, floors: newFloors };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // NEW: Update floor area with total recalculation
  const updateFloorArea = (buildingId: string, floorIndex: number, area: number) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = [...b.floors];
        newFloors[floorIndex].floor_area = area;
        // Recalculate total building area
        const total_floor_area = newFloors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
        return { ...b, floors: newFloors, total_floor_area };
      }
      return b;
    });
    setBuildings(updated);
    setValue('buildings', updated);
  };

  // NEW: Add room to building (NOT floor) - Building-level room management
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

    // Auto-scroll to newly added room after render
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

  // NEW: Update room in building
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

  // NEW: Remove room from building
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

  // Handle building photo upload
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

    // Set loading state
    setUploadingPhotos(prev => ({ ...prev, [buildingId]: true }));

    // Show loading toast
    const toastId = toast.loading(`Uploading ${photoCount} photo${photoCount > 1 ? 's' : ''}...`);

    const newPhotos: BuildingPhoto[] = [];
    const startingOrder = building.building_photos.length + 1;

    try {
      // Read all files sequentially to avoid race condition
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

      // Single state update with all photos
      if (newPhotos.length > 0) {
        const updated = buildings.map(b =>
          b.id === buildingId
            ? { ...b, building_photos: [...b.building_photos, ...newPhotos] }
            : b
        );
        setBuildings(updated);
        setValue('buildings', updated);

        // Show success toast
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
      // Clear loading state
      setUploadingPhotos(prev => ({ ...prev, [buildingId]: false }));

      // Reset file input
      e.target.value = '';
    }
  };

  // Handle drag and drop for building photos
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

    // Set loading state
    setUploadingPhotos(prev => ({ ...prev, [buildingId]: true }));

    // Show loading toast
    const toastId = toast.loading(`Uploading ${photoCount} photo${photoCount > 1 ? 's' : ''}...`);

    const newPhotos: BuildingPhoto[] = [];
    const startingOrder = building.building_photos.length + 1;

    try {
      // Read all files sequentially to avoid race condition
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

      // Single state update with all photos
      if (newPhotos.length > 0) {
        const updated = buildings.map(b =>
          b.id === buildingId
            ? { ...b, building_photos: [...b.building_photos, ...newPhotos] }
            : b
        );
        setBuildings(updated);
        setValue('buildings', updated);

        // Show success toast
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
      // Clear loading state
      setUploadingPhotos(prev => ({ ...prev, [buildingId]: false }));
    }
  };

  // Remove building photo
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

  // Update building photo caption
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
    buildings,
    expandedBuilding,
    setExpandedBuilding,
    addBuilding,
    removeBuilding,
    updateBuilding,
    copyOccupierFromFirstBuilding,
    updateBuildingConstructionMaterial,
    generateFloors,
    addFloor,
    updateFloorName,
    updateFloorArea,
    addRoom,
    updateRoom,
    removeRoom,
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
  };
}
