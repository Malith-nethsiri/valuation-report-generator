import React, { useState, useCallback, useEffect } from 'react';
import toast from 'react-hot-toast';
import {
  Mountain,
  Building2,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Camera,
  Upload,
  X,
  Loader2,
  Maximize2
} from 'lucide-react';
import { Button } from './Button';
import { Input } from './Input';
import { Label } from './Label';
import { generateEnhancedLandDescription } from '../utils/landDescriptionGenerator';
import { authTokenStorage } from '../utils/secureStorage';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface PropertyDescriptionStepProps {
  register: any;
  errors: any;
  watch: any;
  setValue: any;
}

// Configuration Constants
const MAX_BUILDING_PHOTOS = 5;
const MAX_PROPERTY_PHOTOS = 20;
const MAX_FLOORS_PER_BUILDING = 10;

// Constants for dropdown options
const LAND_SHAPES = [
  { value: 'rectangular', label: 'Rectangular' },
  { value: 'square', label: 'Square' },
  { value: 'triangular', label: 'Triangular' },
  { value: 'trapezoidal', label: 'Trapezoidal' },
  { value: 'quadrilateral', label: 'Quadrilateral' },
  { value: 'irregular', label: 'Irregular' },
  { value: 'l_shaped', label: 'L-Shaped' },
  { value: 'pentagon', label: 'Pentagon' },
];

const LAND_TYPES = [
  { value: 'high_land', label: 'High Land' },
  { value: 'low_land', label: 'Low Land' },
  { value: 'flat_land', label: 'Flat Land' },
  { value: 'sloping_land', label: 'Sloping Land' },
  { value: 'paddy_land', label: 'Paddy Land' },
  { value: 'garden_land', label: 'Garden Land' },
];

const FRONTAGE_TYPES = [
  { value: 'tarred', label: 'Tarred Road' },
  { value: 'gravel', label: 'Gravel Road' },
  { value: 'concrete_brick_paved', label: 'Concrete Brick Paved' },
  { value: 'earth', label: 'Earth Road' },
  { value: 'no_frontage', label: 'No Road Frontage' },
];

const LAND_LEVELS = [
  { value: 'at_road_level', label: 'At Road Level' },
  { value: 'above_road_level', label: 'Above Road Level' },
  { value: 'below_road_level', label: 'Below Road Level' },
];

const SOIL_TYPES = [
  { value: 'sand_clay', label: 'Sand Clay' },
  { value: 'gravel_clay', label: 'Gravel Clay' },
  { value: 'red_earth', label: 'Red Earth' },
  { value: 'loamy', label: 'Loamy' },
  { value: 'rocky', label: 'Rocky' },
  { value: 'marshy', label: 'Marshy' },
];

const FLOOD_RISK_OPTIONS = [
  { value: 'not_subject', label: 'Not Subject to Flooding' },
  { value: 'occasionally_floods', label: 'Occasionally Floods' },
  { value: 'flood_prone', label: 'Flood Prone Area' },
];

const LAND_CONDITIONS = [
  { value: 'developed', label: 'Developed' },
  { value: 'bare_land', label: 'Bare Land' },
  { value: 'scrub_jungle', label: 'Scrub Jungle' },
  { value: 'cultivated', label: 'Cultivated' },
  { value: 'marshy', label: 'Marshy' },
];

const ELEVATION_CHANGES = [
  { value: 'relatively_flat', label: 'Relatively Flat' },
  { value: 'gentle_slope', label: 'Gently Sloping' },
  { value: 'moderate_slope', label: 'Moderate Slopes' },
  { value: 'steep_gradients', label: 'Steep Gradients' },
  { value: 'undulating', label: 'Undulating Topography' },
];

const DRAINAGE_PATTERNS = [
  { value: 'well_drained', label: 'Well Drained' },
  { value: 'adequate_drainage', label: 'Adequate Drainage' },
  { value: 'poor_drainage', label: 'Poor Drainage' },
  { value: 'seasonal_waterlogging', label: 'Seasonal Waterlogging' },
  { value: 'artificial_drainage', label: 'Artificial Drainage Systems' },
];

const VEGETATION_TYPES = [
  { value: 'bare_land', label: 'Bare Land' },
  { value: 'grass_coverage', label: 'Grass Coverage' },
  { value: 'shrubs_bushes', label: 'Shrubs and Bushes' },
  { value: 'mature_trees', label: 'Mature Trees' },
  { value: 'mixed_vegetation', label: 'Mixed Vegetation' },
  { value: 'dense_jungle', label: 'Dense Jungle/Forest' },
];

const BUILDING_TYPES = [
  { value: 'residential', label: 'Residential' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'mixed_use', label: 'Mixed-use' },
  { value: 'outbuilding', label: 'Outbuilding' },
];

const CONDITIONS = [
  { value: 'new', label: 'New' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'poor', label: 'Poor' },
  { value: 'dilapidated', label: 'Dilapidated' },
];

const ROOF_TYPES = [
  { value: 'asbestos_sheets', label: 'Asbestos Sheets' },
  { value: 'clay_tiles', label: 'Clay Tiles' },
  { value: 'concrete_flat', label: 'Concrete Flat (RCC)' },
  { value: 'metal_sheets', label: 'Metal Sheets' },
  { value: 'timber_frame', label: 'Timber Frame' },
  { value: 'cadjans', label: 'Cadjans' },
];

const WALL_TYPES = [
  { value: 'brick_masonry', label: 'Brick Masonry' },
  { value: 'rcc_columns', label: 'RCC Columns' },
  { value: 'rubble_masonry', label: 'Rubble Masonry' },
  { value: 'timber', label: 'Timber' },
  { value: 'cadjan', label: 'Cadjan' },
  { value: 'plastered', label: 'Plastered' },
  { value: 'color_washed', label: 'Color Washed' },
];

const FLOOR_TYPES = [
  { value: 'cement', label: 'Cement' },
  { value: 'tiled', label: 'Tiled' },
  { value: 'terrazzo', label: 'Terrazzo' },
  { value: 'timber', label: 'Timber' },
  { value: 'earth', label: 'Earth' },
];

const CONVENIENCES = [
  { value: 'electricity', label: 'Electricity' },
  { value: 'tap_water', label: 'Tap Water' },
  { value: 'well_water', label: 'Well Water' },
  { value: 'telephone', label: 'Telephone' },
  { value: 'internet', label: 'Internet' },
  { value: 'sewage', label: 'Sewage System' },
  { value: 'septic_tank', label: 'Septic Tank' },
  { value: 'gas_connection', label: 'Gas Connection' },
  { value: 'air_conditioning', label: 'Air Conditioning' },
  { value: 'generator', label: 'Generator Backup' },
  { value: 'solar_panels', label: 'Solar Panels' },
  { value: 'security_system', label: 'Security System' },
];

const ROOM_TYPES = [
  'Verandah', 'Living Hall', 'Dining Hall', 'Kitchen', 'Bedroom',
  'Bathroom', 'Pantry', 'Garage', 'Car Porch', 'Store Room', 'Balcony', 'Other'
];

const OCCUPIER_RELATIONSHIPS = [
  { value: 'owner', label: 'Owner' },
  { value: 'tenant', label: 'Tenant' },
  { value: 'caretaker', label: 'Caretaker' },
  { value: 'family_member', label: 'Family Member' },
];

type TabType = 'land' | 'building';

interface Building {
  id: string;
  building_name: string;
  building_type: string;
  stories: number;
  age_description: string;
  condition: string;
  roof_types: string[];
  roof_description: string;
  wall_types: string[];
  wall_description: string;
  floor_types: string[];
  floor_description: string;
  total_floor_area: number;
  floors: Floor[];
  conveniences: string[];
  building_description_text: string;
  building_photos: BuildingPhoto[];
}

interface Floor {
  floor_name: string;
  floor_area: number;
  rooms: Room[];
}

interface Room {
  room_type: string;
  count: number; // How many rooms of this type
  has_attached_bathroom?: boolean;
}

interface BuildingPhoto {
  id: string;
  image_data: string;
  caption: string;
  order: number;
}

export const PropertyDescriptionStep: React.FC<PropertyDescriptionStepProps> = ({
  register,
  errors,
  watch,
  setValue
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('land');
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [expandedBuilding, setExpandedBuilding] = useState<string | null>(null);
  const [isGeneratingDescription, setIsGeneratingDescription] = useState(false);
  const [floorCount, setFloorCount] = useState<{[buildingId: string]: number}>({});
  const [uploadingPhotos, setUploadingPhotos] = useState<{[buildingId: string]: boolean}>({});

  // Initialize buildings from form values on mount
  const formBuildings = watch('buildings');

  useEffect(() => {
    if (formBuildings && Array.isArray(formBuildings) && formBuildings.length > 0) {
      setBuildings(formBuildings);
    }
  }, []);

  // Watch form values for auto-generation
  const landShape = watch('land_shape');
  const landType = watch('land_type');
  const landFrontageType = watch('land_frontage_type');
  const landLevel = watch('land_level');
  const soilType = watch('soil_type');
  const waterTableDepth = watch('water_table_depth');
  const floodRisk = watch('flood_risk');
  const landCondition = watch('land_condition');

  // Generate professional land description using AI
  const generateLandDescription = useCallback(async () => {
    setIsGeneratingDescription(true);

    try {
      // Get authentication token
      const token = authTokenStorage.getToken();
      console.log('[LAND] Generate description - Auth token present:', !!token);

      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Prepare land data for API
      const landData = {
        land_shape: landShape,
        land_type: landType,
        land_level: landLevel,
        land_level_difference: watch('land_level_difference'),
        land_frontage_type: landFrontageType,
        land_frontage_width: watch('land_frontage_width'),
        land_frontage_description: watch('land_frontage_description'),
        soil_type: soilType,
        water_table_depth: waterTableDepth,
        flood_risk: floodRisk,
        land_condition: landCondition,
        elevation_changes: watch('elevation_changes'),
        drainage_pattern: watch('drainage_pattern'),
        vegetation_type: watch('vegetation_type'),
        natural_features: watch('natural_features'),
      };

      console.log('[LAND] Sending AI description generation request...');
      const response = await fetch(`${API_BASE_URL}/api/land/generate-description`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(landData)
      });

      console.log('[LAND] Description response status:', response.status);

      if (response.status === 401) {
        console.error('[LAND] Token expired or invalid');
        throw new Error('Your session has expired. Please refresh the page and log in again.');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[LAND] AI generation failed:', errorData);
        throw new Error(errorData.detail || 'AI generation failed');
      }

      const result = await response.json();
      console.log('[LAND] Description generated successfully with AI');
      setValue('land_description_text', result.description);
      toast.success('Land description generated with AI!');

    } catch (err: any) {
      console.error('[LAND] Error generating with AI, falling back to template system:', err);
      toast.error('AI generation failed. Using template fallback.');

      // FALLBACK: Use template-based generation
      try {
        const fallbackDescription = generateEnhancedLandDescription({
          land_shape: landShape,
          land_type: landType,
          land_level: landLevel,
          land_level_difference: watch('land_level_difference'),
          land_frontage_type: landFrontageType,
          land_frontage_width: watch('land_frontage_width'),
          land_frontage_description: watch('land_frontage_description'),
          soil_type: soilType,
          water_table_depth: waterTableDepth,
          flood_risk: floodRisk,
          land_condition: landCondition,
          elevation_changes: watch('elevation_changes'),
          drainage_pattern: watch('drainage_pattern'),
          vegetation_type: watch('vegetation_type'),
          natural_features: watch('natural_features'),
        });
        setValue('land_description_text', fallbackDescription);
        console.log('[LAND] Template fallback successful');
      } catch (fallbackErr) {
        console.error('[LAND] Template fallback also failed:', fallbackErr);
        toast.error('Failed to generate description. Please try again.');
      }
    } finally {
      setIsGeneratingDescription(false);
    }
  }, [landShape, landType, landLevel, landFrontageType, soilType, waterTableDepth, floodRisk, landCondition, setValue, watch]);

  // Add new building
  const addBuilding = () => {
    const newBuilding: Building = {
      id: `building_${Date.now()}`,
      building_name: '',
      building_type: 'residential',
      stories: 1,
      age_description: '',
      condition: 'fair',
      roof_types: [],
      roof_description: '',
      wall_types: [],
      wall_description: '',
      floor_types: [],
      floor_description: '',
      total_floor_area: 0,
      floors: [{ floor_name: 'Ground Floor', floor_area: 0, rooms: [] }],
      conveniences: [],
      building_description_text: '',
      building_photos: []
    };
    const updated = [...buildings, newBuilding];
    setBuildings(updated);
    setValue('buildings', updated);
    setExpandedBuilding(newBuilding.id);
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

  // NEW: Update nested construction material fields
  const updateBuildingConstructionMaterial = (buildingId: string, section: string, field: string, value: any) => {
    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const updatedMaterials = {
          ...b.construction_materials,
          [section]: {
            ...(b.construction_materials?.[section as keyof typeof b.construction_materials] || {}),
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

  // Auto-generate floor names
  const FLOOR_NAMES = [
    'Ground Floor', 'First Floor', 'Second Floor',
    'Third Floor', 'Fourth Floor', 'Fifth Floor',
    'Sixth Floor', 'Seventh Floor', 'Eighth Floor', 'Ninth Floor'
  ];

  // Generate multiple floors at once
  const generateFloors = (buildingId: string, count: number) => {
    if (count < 1 || count > 10) return;

    const updated = buildings.map(b => {
      if (b.id === buildingId) {
        const newFloors = Array.from({ length: count }, (_, i) => ({
          floor_name: FLOOR_NAMES[i] || `Floor ${i + 1}`,
          floor_area: 0,
          rooms: []
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
        const updatedFloors = [...b.floors, { floor_name: floorName, floor_area: 0, rooms: [] }];
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
        newFloors[floorIndex].rooms.push({
          room_type: 'Bedroom',
          count: 1
        });
        // Auto-calculate accommodation summary
        newFloors[floorIndex].accommodation_summary = calculateAccommodationSummary(newFloors[floorIndex].rooms);
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
        const updatedRooms = [...newFloors[floorIndex].rooms];
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
        const updatedRooms = newFloors[floorIndex].rooms.filter((_, idx) => idx !== roomIndex);
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
        toast.success(`✓ ${newPhotos.length} photo${newPhotos.length > 1 ? 's' : ''} uploaded successfully`, {
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
        toast.success(`✓ ${newPhotos.length} photo${newPhotos.length > 1 ? 's' : ''} uploaded successfully`, {
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

  const tabs = [
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
        {/* Land Description Tab */}
        {activeTab === 'land' && (
          <div className="space-y-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Land Characteristics</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Land Shape */}
              <div>
                <Label htmlFor="land_shape">Land Shape</Label>
                <select
                  {...register('land_shape')}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Select shape...</option>
                  {LAND_SHAPES.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Land Type */}
              <div>
                <Label htmlFor="land_type">Land Type</Label>
                <select
                  {...register('land_type')}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Select type...</option>
                  {LAND_TYPES.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Frontage Type */}
              <div>
                <Label htmlFor="land_frontage_type">Road Frontage Type</Label>
                <select
                  {...register('land_frontage_type')}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Select frontage...</option>
                  {FRONTAGE_TYPES.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Frontage Width */}
              <div>
                <Label htmlFor="land_frontage_width">Frontage Width (meters)</Label>
                <Input
                  type="number"
                  step="0.01"
                  {...register('land_frontage_width')}
                  placeholder="e.g., 6.0"
                />
              </div>

              {/* Land Level */}
              <div>
                <Label htmlFor="land_level">Land Level</Label>
                <select
                  {...register('land_level')}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Select level...</option>
                  {LAND_LEVELS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Level Difference */}
              <div>
                <Label htmlFor="land_level_difference">Level Difference (feet)</Label>
                <Input
                  type="number"
                  step="0.5"
                  {...register('land_level_difference')}
                  placeholder="e.g., 1.5"
                />
              </div>

              {/* Soil Type */}
              <div>
                <Label htmlFor="soil_type">Soil Type</Label>
                <select
                  {...register('soil_type')}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Select soil type...</option>
                  {SOIL_TYPES.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Water Table Depth */}
              <div>
                <Label htmlFor="water_table_depth">Water Table Depth (feet)</Label>
                <Input
                  type="number"
                  step="1"
                  {...register('water_table_depth')}
                  placeholder="e.g., 15"
                />
              </div>

              {/* Flood Risk */}
              <div>
                <Label htmlFor="flood_risk">Flood Risk</Label>
                <select
                  {...register('flood_risk')}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Select flood risk...</option>
                  {FLOOD_RISK_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>

              {/* Land Condition */}
              <div>
                <Label htmlFor="land_condition">Land Condition</Label>
                <select
                  {...register('land_condition')}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">Select condition...</option>
                  {LAND_CONDITIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Topographical Features Section */}
            <div className="space-y-2 pt-4 border-t border-gray-200">
              <h4 className="text-md font-semibold text-gray-800 mb-3">Topographical Features</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Elevation Changes */}
                <div>
                  <Label htmlFor="elevation_changes">Elevation Changes</Label>
                  <select
                    {...register('elevation_changes')}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="">Select elevation pattern...</option>
                    {ELEVATION_CHANGES.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                {/* Drainage Pattern */}
                <div>
                  <Label htmlFor="drainage_pattern">Drainage Pattern</Label>
                  <select
                    {...register('drainage_pattern')}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="">Select drainage pattern...</option>
                    {DRAINAGE_PATTERNS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                {/* Vegetation Type */}
                <div>
                  <Label htmlFor="vegetation_type">Vegetation Type</Label>
                  <select
                    {...register('vegetation_type')}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="">Select vegetation type...</option>
                    {VEGETATION_TYPES.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Natural Features */}
              <div className="pt-2">
                <Label htmlFor="natural_features">Natural Features (Optional)</Label>
                <textarea
                  {...register('natural_features')}
                  rows={2}
                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="e.g., Natural stream along eastern boundary, rock outcroppings on northern section, seasonal pond in southwest corner"
                />
                <p className="text-xs text-gray-500 mt-1">Describe any notable natural features like streams, ponds, rock formations, etc.</p>
              </div>
            </div>

            {/* Additional Description */}
            <div>
              <Label htmlFor="land_frontage_description">Additional Frontage Description</Label>
              <textarea
                {...register('land_frontage_description')}
                rows={2}
                className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="Additional details about the road frontage..."
              />
            </div>

            {/* Auto-generated Description */}
            <div className="bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl p-4 border border-emerald-200">
              <div className="flex items-center justify-between mb-3">
                <Label htmlFor="land_description_text" className="text-emerald-800 font-semibold">
                  Professional Land Description
                </Label>
                <Button
                  type="button"
                  onClick={generateLandDescription}
                  disabled={isGeneratingDescription}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm"
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  {isGeneratingDescription ? 'Generating...' : 'Auto-Generate'}
                </Button>
              </div>
              <textarea
                {...register('land_description_text')}
                rows={4}
                className="w-full px-4 py-3 bg-white border border-emerald-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="Description will be auto-generated based on the fields above, or you can write manually..."
              />
              <p className="text-xs text-emerald-600 mt-2">
                This text will appear in the final report. You can edit it after auto-generation.
              </p>
            </div>

            {/* Occupier Information */}
            <div className="border-t border-gray-200 pt-6 mt-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Occupier Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="occupier_name">Occupier Name</Label>
                  <Input
                    {...register('occupier_name')}
                    placeholder="e.g., Mrs. Prema Nandage Sunitha Kumari Jayasinghe"
                  />
                </div>
                <div>
                  <Label htmlFor="occupier_relationship">Relationship</Label>
                  <select
                    {...register('occupier_relationship')}
                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    <option value="">Select relationship...</option>
                    {OCCUPIER_RELATIONSHIPS.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Building Details Tab */}
        {activeTab === 'building' && (
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
                    {/* Building Header */}
                    <div
                      className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer"
                      onClick={() => setExpandedBuilding(
                        expandedBuilding === building.id ? null : building.id
                      )}
                    >
                      <div className="flex items-center space-x-3">
                        <Building2 className="h-5 w-5 text-emerald-600" />
                        <span className="font-semibold text-gray-900">
                          {building.building_name || `Building ${index + 1}`}
                        </span>
                        <span className="text-sm text-gray-500">
                          ({BUILDING_TYPES.find(t => t.value === building.building_type)?.label || 'Residential'})
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeBuilding(building.id);
                          }}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                        {expandedBuilding === building.id ? (
                          <ChevronUp className="h-5 w-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                    </div>

                    {/* Building Content */}
                    {expandedBuilding === building.id && (
                      <div className="p-4 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <Label>Building Name</Label>
                            <Input
                              value={building.building_name}
                              onChange={(e) => updateBuilding(building.id, 'building_name', e.target.value.toUpperCase())}
                              placeholder="e.g., Main Residence"
                            />
                          </div>
                          <div>
                            <Label>Building Type</Label>
                            <select
                              value={building.building_type}
                              onChange={(e) => updateBuilding(building.id, 'building_type', e.target.value)}
                              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                            >
                              {BUILDING_TYPES.map(opt => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                              ))}
                            </select>
                          </div>
                          <div>
                            <Label>Age</Label>
                            <Input
                              value={building.age_description}
                              onChange={(e) => updateBuilding(building.id, 'age_description', e.target.value)}
                              placeholder="e.g., about 10 years old"
                            />
                          </div>
                          <div>
                            <Label>Condition</Label>
                            <select
                              value={building.condition}
                              onChange={(e) => updateBuilding(building.id, 'condition', e.target.value)}
                              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                            >
                              {CONDITIONS.map(opt => (
                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                        {/* Number of Floors and Total Floor Area moved to Floor Generation section */}
                        {/* OLD: Roof Types / Wall Types / Floor Types checkboxes REMOVED - now collected in detailed Construction Materials section below */}

                        {/* ===== BUILDING CONSTRUCTION DETAILS - REDESIGNED ===== */}
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-6 mt-6">
                          <h4 className="font-semibold text-lg text-amber-900 mb-4 flex items-center">
                            <Building2 className="h-5 w-5 mr-2" />
                            Building Construction Details
                          </h4>

                          {/* ROOF CONSTRUCTION */}
                          <div className="bg-white rounded-lg p-4 mb-4 space-y-3">
                            <h5 className="font-semibold text-md text-gray-800">Roof Construction</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <Label>Roof Structure Type</Label>
                                <select
                                  value={building.construction_materials?.roof_details?.structure_type || ''}
                                  onChange={(e) => updateBuildingConstructionMaterial(building.id, 'roof_details', 'structure_type', e.target.value)}
                                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                                >
                                  <option value="">Select structure...</option>
                                  <option value="timber_frame">Timber Frame</option>
                                  <option value="steel_trusses">Steel Trusses</option>
                                  <option value="concrete_slab">Concrete Slab (RCC)</option>
                                  <option value="rcc_flat">RCC Flat Roof</option>
                                  <option value="prefab_trusses">Prefabricated Trusses</option>
                                  <option value="mixed">Mixed Construction</option>
                                </select>
                              </div>
                              <div>
                                <Label>Roof Covering Material (Select all that apply)</Label>
                                <div className="grid grid-cols-2 gap-2 mt-2">
                                  {[
                                    { value: 'asbestos_sheets', label: 'Asbestos Sheets' },
                                    { value: 'clay_tiles', label: 'Clay Tiles' },
                                    { value: 'concrete_tiles', label: 'Concrete Tiles' },
                                    { value: 'metal_sheets', label: 'Metal Sheets (GI/Zinc)' },
                                    { value: 'concrete_flat', label: 'Concrete Flat' },
                                    { value: 'cadjans', label: 'Cadjans/Thatch' },
                                    { value: 'shingles', label: 'Shingles' }
                                  ].map(option => (
                                    <label key={option.value} className="flex items-center space-x-2 text-sm">
                                      <input
                                        type="checkbox"
                                        checked={building.construction_materials?.roof_details?.covering_material?.includes(option.value) || false}
                                        onChange={(e) => {
                                          const current = building.construction_materials?.roof_details?.covering_material || [];
                                          const updated = e.target.checked
                                            ? [...current, option.value]
                                            : current.filter(v => v !== option.value);
                                          updateBuildingConstructionMaterial(building.id, 'roof_details', 'covering_material', updated);
                                        }}
                                        className="rounded border-gray-300"
                                      />
                                      <span>{option.label}</span>
                                    </label>
                                  ))}
                                </div>
                              </div>
                            </div>
                            <div>
                              <Label>Additional Roof Details (Optional)</Label>
                              <Input
                                value={building.construction_materials?.roof_details?.additional_details || ''}
                                onChange={(e) => updateBuildingConstructionMaterial(building.id, 'roof_details', 'additional_details', e.target.value)}
                                placeholder="e.g., Insulated, waterproofing treatment, solar panels on roof, etc."
                              />
                            </div>
                          </div>

                          {/* WALL CONSTRUCTION */}
                          <div className="bg-white rounded-lg p-4 mb-4 space-y-3">
                            <h5 className="font-semibold text-md text-gray-800">Wall Construction</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <Label>Wall Material</Label>
                                <select
                                  value={building.construction_materials?.wall_details?.material || ''}
                                  onChange={(e) => updateBuildingConstructionMaterial(building.id, 'wall_details', 'material', e.target.value)}
                                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                                >
                                  <option value="">Select material...</option>
                                  <option value="brick_masonry">Brick Masonry</option>
                                  <option value="cement_block">Cement Block (Concrete Block)</option>
                                  <option value="stone_masonry">Stone Masonry</option>
                                  <option value="rcc_frame">RCC Frame with Infill</option>
                                  <option value="rubble_masonry">Rubble Masonry</option>
                                  <option value="mud_walls">Mud Walls (Wattle & Daub)</option>
                                  <option value="timber_frame">Timber Frame</option>
                                  <option value="cadjan">Cadjan/Woven Palm</option>
                                  <option value="prefab_panels">Prefabricated Panels</option>
                                  <option value="mixed">Mixed Materials</option>
                                </select>
                              </div>
                              <div>
                                <Label>Wall Finish (Select all that apply)</Label>
                                <div className="space-y-2 mt-2">
                                  {[
                                    { value: 'cement_plaster_painted', label: 'Cement Plaster & Painted' },
                                    { value: 'lime_plaster', label: 'Lime Plaster' },
                                    { value: 'tiles', label: 'Wall Tiles' },
                                    { value: 'exposed_brick', label: 'Exposed Brick' },
                                    { value: 'color_washed', label: 'Color Washed' },
                                    { value: 'textured', label: 'Textured Finish' },
                                    { value: 'unfinished', label: 'Unfinished' }
                                  ].map(option => (
                                    <label key={option.value} className="flex items-center space-x-2 text-sm">
                                      <input
                                        type="checkbox"
                                        checked={building.construction_materials?.wall_details?.finish?.includes(option.value) || false}
                                        onChange={(e) => {
                                          const current = building.construction_materials?.wall_details?.finish || [];
                                          const updated = e.target.checked
                                            ? [...current, option.value]
                                            : current.filter(v => v !== option.value);
                                          updateBuildingConstructionMaterial(building.id, 'wall_details', 'finish', updated);
                                        }}
                                        className="rounded border-gray-300"
                                      />
                                      <span>{option.label}</span>
                                    </label>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* FLOOR CONSTRUCTION */}
                          <div className="bg-white rounded-lg p-4 mb-4 space-y-3">
                            <h5 className="font-semibold text-md text-gray-800">Floor Construction</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <Label>Floor Material (Select all that apply)</Label>
                                <div className="grid grid-cols-2 gap-2 mt-2">
                                  {[
                                    { value: 'cement', label: 'Cement' },
                                    { value: 'tiled', label: 'Ceramic/Porcelain Tiles' },
                                    { value: 'terrazzo', label: 'Terrazzo' },
                                    { value: 'timber', label: 'Timber/Wooden' },
                                    { value: 'granite', label: 'Granite' },
                                    { value: 'marble', label: 'Marble' },
                                    { value: 'vinyl', label: 'Vinyl/Laminate' },
                                    { value: 'polished_concrete', label: 'Polished Concrete' },
                                    { value: 'earth', label: 'Earth/Compacted Soil' }
                                  ].map(option => (
                                    <label key={option.value} className="flex items-center space-x-2 text-sm">
                                      <input
                                        type="checkbox"
                                        checked={building.construction_materials?.floor_details?.material?.includes(option.value) || false}
                                        onChange={(e) => {
                                          const current = building.construction_materials?.floor_details?.material || [];
                                          const updated = e.target.checked
                                            ? [...current, option.value]
                                            : current.filter(v => v !== option.value);
                                          updateBuildingConstructionMaterial(building.id, 'floor_details', 'material', updated);
                                        }}
                                        className="rounded border-gray-300"
                                      />
                                      <span>{option.label}</span>
                                    </label>
                                  ))}
                                </div>
                              </div>
                              <div>
                                <Label>Finish Quality</Label>
                                <select
                                  value={building.construction_materials?.floor_details?.finish_quality || ''}
                                  onChange={(e) => updateBuildingConstructionMaterial(building.id, 'floor_details', 'finish_quality', e.target.value)}
                                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                                >
                                  <option value="">Select quality...</option>
                                  <option value="basic">Basic/Standard</option>
                                  <option value="standard">Good Quality</option>
                                  <option value="premium">Premium/High-End</option>
                                </select>
                              </div>
                            </div>
                          </div>

                          {/* CEILING TYPE */}
                          <div className="bg-white rounded-lg p-4">
                            <Label>Ceiling Type</Label>
                            <select
                              value={building.construction_materials?.ceiling_type || ''}
                              onChange={(e) => updateBuilding(building.id, 'construction_materials', {
                                ...building.construction_materials,
                                ceiling_type: e.target.value
                              })}
                              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl mt-2"
                            >
                              <option value="">Select ceiling...</option>
                              <option value="gypsum_board">Gypsum Board</option>
                              <option value="plywood">Plywood</option>
                              <option value="asbestos">Asbestos Ceiling</option>
                              <option value="pvc">PVC Panels</option>
                              <option value="timber">Timber Planks</option>
                              <option value="none">No Ceiling (Exposed Roof)</option>
                            </select>
                          </div>

                          {/* DOORS & WINDOWS */}
                          <div className="bg-white rounded-lg p-4 mt-4 space-y-3">
                            <h5 className="font-semibold text-md text-gray-800">Doors & Windows</h5>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {/* Windows */}
                              <div className="space-y-3">
                                <div>
                                  <Label>Window Frame Material (Select all that apply)</Label>
                                  <div className="grid grid-cols-2 gap-2 mt-2">
                                    {[
                                      { value: 'timber', label: 'Timber' },
                                      { value: 'aluminum', label: 'Aluminum' },
                                      { value: 'upvc', label: 'UPVC' },
                                      { value: 'steel', label: 'Steel' }
                                    ].map(option => (
                                      <label key={option.value} className="flex items-center space-x-2 text-sm">
                                        <input
                                          type="checkbox"
                                          checked={building.construction_materials?.doors_windows_details?.window_frame_material?.includes(option.value) || false}
                                          onChange={(e) => {
                                            const current = building.construction_materials?.doors_windows_details?.window_frame_material || [];
                                            const updated = e.target.checked
                                              ? [...current, option.value]
                                              : current.filter(v => v !== option.value);
                                            updateBuildingConstructionMaterial(building.id, 'doors_windows_details', 'window_frame_material', updated);
                                          }}
                                          className="rounded border-gray-300"
                                        />
                                        <span>{option.label}</span>
                                      </label>
                                    ))}
                                  </div>
                                </div>
                                <div>
                                  <Label>Window Glass Type (Select all that apply)</Label>
                                  <div className="grid grid-cols-2 gap-2 mt-2">
                                    {[
                                      { value: 'clear', label: 'Clear Glass' },
                                      { value: 'tinted', label: 'Tinted Glass' },
                                      { value: 'frosted', label: 'Frosted Glass' },
                                      { value: 'double_glazing', label: 'Double Glazing' }
                                    ].map(option => (
                                      <label key={option.value} className="flex items-center space-x-2 text-sm">
                                        <input
                                          type="checkbox"
                                          checked={building.construction_materials?.doors_windows_details?.window_glass_type?.includes(option.value) || false}
                                          onChange={(e) => {
                                            const current = building.construction_materials?.doors_windows_details?.window_glass_type || [];
                                            const updated = e.target.checked
                                              ? [...current, option.value]
                                              : current.filter(v => v !== option.value);
                                            updateBuildingConstructionMaterial(building.id, 'doors_windows_details', 'window_glass_type', updated);
                                          }}
                                          className="rounded border-gray-300"
                                        />
                                        <span>{option.label}</span>
                                      </label>
                                    ))}
                                  </div>
                                </div>
                                <div>
                                  <Label>Window Security (Select all that apply)</Label>
                                  <div className="space-y-2 mt-2">
                                    {[
                                      { value: 'burglar_bars', label: 'Burglar Bars' },
                                      { value: 'grills', label: 'Security Grills' },
                                      { value: 'security_mesh', label: 'Security Mesh' }
                                    ].map(option => (
                                      <label key={option.value} className="flex items-center space-x-2 text-sm">
                                        <input
                                          type="checkbox"
                                          checked={building.construction_materials?.doors_windows_details?.window_security?.includes(option.value) || false}
                                          onChange={(e) => {
                                            const current = building.construction_materials?.doors_windows_details?.window_security || [];
                                            const updated = e.target.checked
                                              ? [...current, option.value]
                                              : current.filter(v => v !== option.value);
                                            updateBuildingConstructionMaterial(building.id, 'doors_windows_details', 'window_security', updated);
                                          }}
                                          className="rounded border-gray-300"
                                        />
                                        <span>{option.label}</span>
                                      </label>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              {/* Doors */}
                              <div className="space-y-3">
                                <div>
                                  <Label>Main Door Material</Label>
                                  <select
                                    value={building.construction_materials?.doors_windows_details?.main_door_material || ''}
                                    onChange={(e) => updateBuildingConstructionMaterial(building.id, 'doors_windows_details', 'main_door_material', e.target.value)}
                                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl mt-2"
                                  >
                                    <option value="">Select material...</option>
                                    <option value="solid_timber">Solid Timber</option>
                                    <option value="panel_door">Panel Door (Timber)</option>
                                    <option value="metal">Metal/Steel</option>
                                    <option value="upvc">UPVC</option>
                                    <option value="glass">Glass Door</option>
                                  </select>
                                </div>
                                <div>
                                  <Label>Internal Door Material</Label>
                                  <select
                                    value={building.construction_materials?.doors_windows_details?.internal_door_material || ''}
                                    onChange={(e) => updateBuildingConstructionMaterial(building.id, 'doors_windows_details', 'internal_door_material', e.target.value)}
                                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl mt-2"
                                  >
                                    <option value="">Select material...</option>
                                    <option value="timber">Solid Timber</option>
                                    <option value="flush_doors">Flush Doors</option>
                                    <option value="panel_doors">Panel Doors</option>
                                    <option value="hollow_core">Hollow Core Doors</option>
                                  </select>
                                </div>
                                <div>
                                  <Label>Door Security Features (Select all that apply)</Label>
                                  <div className="space-y-2 mt-2">
                                    {[
                                      { value: 'deadbolt', label: 'Deadbolt Locks' },
                                      { value: 'security_locks', label: 'Security Locks' },
                                      { value: 'door_chain', label: 'Door Chain' },
                                      { value: 'multi_point', label: 'Multi-Point Locking' }
                                    ].map(option => (
                                      <label key={option.value} className="flex items-center space-x-2 text-sm">
                                        <input
                                          type="checkbox"
                                          checked={building.construction_materials?.doors_windows_details?.door_security?.includes(option.value) || false}
                                          onChange={(e) => {
                                            const current = building.construction_materials?.doors_windows_details?.door_security || [];
                                            const updated = e.target.checked
                                              ? [...current, option.value]
                                              : current.filter(v => v !== option.value);
                                            updateBuildingConstructionMaterial(building.id, 'doors_windows_details', 'door_security', updated);
                                          }}
                                          className="rounded border-gray-300"
                                        />
                                        <span>{option.label}</span>
                                      </label>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Utilities & Services Section */}
                        <div className="bg-green-50 border border-green-200 rounded-xl p-5 mb-6">
                          <h4 className="font-semibold text-lg text-green-900 mb-4 flex items-center">
                            <Building2 className="h-5 w-5 mr-2" />
                            Utilities & Services
                          </h4>
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label>Water Supply</Label>
                                <select
                                  value={building.utilities_services?.water_supply || ''}
                                  onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                    ...building.utilities_services,
                                    water_supply: e.target.value
                                  })}
                                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                                >
                                  <option value="">Select water supply...</option>
                                  <option value="pipe_borne">Pipe-borne Water (NWSDB)</option>
                                  <option value="well">Well</option>
                                  <option value="tube_well">Tube Well / Bore Well</option>
                                  <option value="rainwater">Rainwater Harvesting</option>
                                </select>
                              </div>
                              <div>
                                <Label>Sewage System</Label>
                                <select
                                  value={building.utilities_services?.sewage || ''}
                                  onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                    ...building.utilities_services,
                                    sewage: e.target.value
                                  })}
                                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                                >
                                  <option value="">Select sewage...</option>
                                  <option value="municipal">Municipal/Main Sewage</option>
                                  <option value="septic_tank">Septic Tank</option>
                                  <option value="pit_latrine">Pit Latrine</option>
                                </select>
                              </div>
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                              <div>
                                <Label>Electricity Source</Label>
                                <select
                                  value={building.utilities_services?.electricity?.source || ''}
                                  onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                    ...building.utilities_services,
                                    electricity: {
                                      ...building.utilities_services?.electricity,
                                      source: e.target.value
                                    }
                                  })}
                                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                                >
                                  <option value="">Select source...</option>
                                  <option value="ceb">CEB (Ceylon Electricity Board)</option>
                                  <option value="solar">Solar Power</option>
                                  <option value="generator">Generator</option>
                                </select>
                              </div>
                              <div>
                                <Label>Connection Type</Label>
                                <select
                                  value={building.utilities_services?.electricity?.three_phase ? 'three_phase' : 'single_phase'}
                                  onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                    ...building.utilities_services,
                                    electricity: {
                                      ...building.utilities_services?.electricity,
                                      three_phase: e.target.value === 'three_phase'
                                    }
                                  })}
                                  className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                                >
                                  <option value="single_phase">Single Phase</option>
                                  <option value="three_phase">Three Phase</option>
                                </select>
                              </div>
                              <div className="flex items-center pt-6">
                                <label className="flex items-center">
                                  <input
                                    type="checkbox"
                                    checked={building.utilities_services?.electricity?.solar_panels || false}
                                    onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                      ...building.utilities_services,
                                      electricity: {
                                        ...building.utilities_services?.electricity,
                                        solar_panels: e.target.checked
                                      }
                                    })}
                                    className="mr-2 rounded"
                                  />
                                  Solar Panels Installed
                                </label>
                              </div>
                            </div>

                            <div>
                              <Label>Parking Facilities</Label>
                              <div className="grid grid-cols-3 gap-4 mt-2">
                                <div>
                                  <Label className="text-sm text-gray-600">Covered Parking</Label>
                                  <Input
                                    type="number"
                                    min="0"
                                    value={building.utilities_services?.parking?.covered_spaces || ''}
                                    onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                      ...building.utilities_services,
                                      parking: {
                                        ...building.utilities_services?.parking,
                                        covered_spaces: parseInt(e.target.value) || 0
                                      }
                                    })}
                                    placeholder="Vehicles"
                                  />
                                </div>
                                <div>
                                  <Label className="text-sm text-gray-600">Uncovered Parking</Label>
                                  <Input
                                    type="number"
                                    min="0"
                                    value={building.utilities_services?.parking?.uncovered_spaces || ''}
                                    onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                      ...building.utilities_services,
                                      parking: {
                                        ...building.utilities_services?.parking,
                                        uncovered_spaces: parseInt(e.target.value) || 0
                                      }
                                    })}
                                    placeholder="Vehicles"
                                  />
                                </div>
                                <div>
                                  <Label className="text-sm font-semibold">Total Capacity</Label>
                                  <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-xl text-center">
                                    <span className="text-2xl font-bold text-blue-700">
                                      {(building.utilities_services?.parking?.covered_spaces || 0) + (building.utilities_services?.parking?.uncovered_spaces || 0)}
                                    </span>
                                    <span className="text-sm text-blue-600 ml-2">vehicles</span>
                                  </div>
                                  <p className="text-xs text-gray-500 mt-1 italic">Auto-calculated</p>
                                </div>
                              </div>
                            </div>

                            <div>
                              <Label>Security Features (Select all that apply)</Label>
                              <div className="flex flex-wrap gap-4 mt-2">
                                {['boundary_wall', 'main_gate', 'cctv', 'security_lights'].map(feature => (
                                  <label key={feature} className="flex items-center">
                                    <input
                                      type="checkbox"
                                      checked={(building.utilities_services?.security_features || []).includes(feature)}
                                      onChange={(e) => {
                                        const current = building.utilities_services?.security_features || [];
                                        const updated = e.target.checked
                                          ? [...current, feature]
                                          : current.filter(f => f !== feature);
                                        updateBuilding(building.id, 'utilities_services', {
                                          ...building.utilities_services,
                                          security_features: updated
                                        });
                                      }}
                                      className="mr-2 rounded"
                                    />
                                    {feature.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                  </label>
                                ))}
                              </div>
                            </div>

                            <div>
                              <Label>Modern Amenities</Label>
                              <div className="grid grid-cols-2 gap-3 mt-2">
                                {[
                                  { key: 'air_conditioning', label: 'Air Conditioning' },
                                  { key: 'built_in_wardrobes', label: 'Built-in Wardrobes' },
                                  { key: 'modern_kitchen', label: 'Modern Kitchen Fittings' },
                                  { key: 'pantry_cupboards', label: 'Pantry Cupboards' }
                                ].map(amenity => (
                                  <label key={amenity.key} className="flex items-center">
                                    <input
                                      type="checkbox"
                                      checked={building.utilities_services?.amenities?.[amenity.key] || false}
                                      onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                        ...building.utilities_services,
                                        amenities: {
                                          ...building.utilities_services?.amenities,
                                          [amenity.key]: e.target.checked
                                        }
                                      })}
                                      className="mr-2 rounded"
                                    />
                                    {amenity.label}
                                  </label>
                                ))}
                              </div>
                            </div>

                            <div>
                              <Label>Hot Water System</Label>
                              <select
                                value={building.utilities_services?.hot_water_system || ''}
                                onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                  ...building.utilities_services,
                                  hot_water_system: e.target.value
                                })}
                                className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl"
                              >
                                <option value="">Select system...</option>
                                <option value="none">None</option>
                                <option value="electric_geyser">Electric Geyser/Instant Heater</option>
                                <option value="solar_heater">Solar Water Heater</option>
                                <option value="gas_heater">Gas Water Heater</option>
                              </select>
                            </div>
                          </div>
                        </div>

                        {/* Conveniences */}
                        <div>
                          <Label>Conveniences</Label>
                          <div className="flex flex-wrap gap-3 mt-2">
                            {CONVENIENCES.map(conv => (
                              <label key={conv.value} className="flex items-center space-x-2 text-sm bg-gray-50 px-3 py-2 rounded-lg">
                                <input
                                  type="checkbox"
                                  checked={building.conveniences.includes(conv.value)}
                                  onChange={(e) => {
                                    const updated = e.target.checked
                                      ? [...building.conveniences, conv.value]
                                      : building.conveniences.filter(c => c !== conv.value);
                                    updateBuilding(building.id, 'conveniences', updated);
                                  }}
                                  className="rounded border-gray-300"
                                />
                                <span>{conv.label}</span>
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* Floor Plan Section */}
                        <div className="border-t border-gray-200 pt-6 mt-6">
                          <h4 className="text-lg font-semibold text-gray-900 mb-4">Floor Plan & Accommodation</h4>

                          {/* Floor Generator */}
                          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 mb-6">
                            <Label className="text-base font-semibold text-gray-900 mb-3 flex items-center">
                              <Building2 className="h-5 w-5 mr-2 text-blue-600" />
                              How many floors does this building have?
                            </Label>
                            <div className="flex items-center space-x-4 mt-3">
                              <Input
                                type="number"
                                min="1"
                                max={MAX_FLOORS_PER_BUILDING}
                                value={floorCount[building.id] || building.floors.length}
                                onChange={(e) => setFloorCount({
                                  ...floorCount,
                                  [building.id]: parseInt(e.target.value) || 1
                                })}
                                className="w-32 text-lg font-semibold"
                                placeholder="e.g., 2"
                              />
                              <Button
                                type="button"
                                onClick={() => generateFloors(building.id, floorCount[building.id] || building.floors.length)}
                                className="bg-blue-600 hover:bg-blue-700"
                              >
                                <Sparkles className="h-4 w-4 mr-2" />
                                Generate Floor Forms
                              </Button>
                            </div>
                            <p className="text-xs text-blue-700 mt-3 italic">
                              Automatically generates: Ground Floor, First Floor, Second Floor, etc. (all names are editable)
                            </p>
                          </div>

                          {/* Auto-Calculated Building Metrics - Displayed after Floor Generation */}
                          {building.floors.length > 0 && (
                            <div className="grid grid-cols-2 gap-4 mb-6">
                              {/* Number of Floors */}
                              <div className="bg-emerald-50 border-2 border-emerald-200 rounded-xl p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-sm font-medium text-emerald-700 mb-1">Number of Floors</p>
                                    <p className="text-3xl font-bold text-emerald-900">
                                      {building.floors.length}
                                    </p>
                                  </div>
                                  <Building2 className="h-10 w-10 text-emerald-400" />
                                </div>
                                <p className="text-xs text-emerald-600 mt-2 italic">Auto-calculated from generated floors</p>
                              </div>

                              {/* Total Floor Area */}
                              <div className="bg-purple-50 border-2 border-purple-200 rounded-xl p-4">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-sm font-medium text-purple-700 mb-1">Total Building Area</p>
                                    <p className="text-3xl font-bold text-purple-900">
                                      {building.total_floor_area?.toLocaleString() || 0}
                                    </p>
                                    <p className="text-sm text-purple-600">sq.ft</p>
                                  </div>
                                  <Maximize2 className="h-10 w-10 text-purple-400" />
                                </div>
                                <p className="text-xs text-purple-600 mt-2 italic">Auto-calculated from all floor areas</p>
                              </div>
                            </div>
                          )}

                          {/* Floor Cards */}
                          {building.floors.map((floor, floorIdx) => (
                            <div key={floorIdx} className="bg-white border-2 border-gray-200 rounded-xl p-5 mb-4 shadow-sm">
                              <div className="mb-4">
                                <Label className="text-sm font-medium text-gray-700">Floor Name (Editable)</Label>
                                <Input
                                  value={floor.floor_name}
                                  onChange={(e) => updateFloorName(building.id, floorIdx, e.target.value)}
                                  className="font-semibold text-lg border-blue-300 focus:border-blue-500 mt-1"
                                  placeholder="e.g., Ground Floor, Mezzanine"
                                />
                              </div>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <Label>Floor Area (sq ft)</Label>
                                  <Input
                                    type="number"
                                    value={floor.floor_area || ''}
                                    onChange={(e) => {
                                      const updated = buildings.map(b => {
                                        if (b.id === building.id) {
                                          const updatedFloors = b.floors.map((f, idx) =>
                                            idx === floorIdx ? { ...f, floor_area: parseFloat(e.target.value) || 0 } : f
                                          );
                                          // Calculate total floor area from all floors
                                          const total_floor_area = updatedFloors.reduce((sum, floor) => sum + (floor.floor_area || 0), 0);
                                          return { ...b, floors: updatedFloors, total_floor_area };
                                        }
                                        return b;
                                      });
                                      setBuildings(updated);
                                      setValue('buildings', updated);
                                    }}
                                    placeholder="e.g., 1200"
                                  />
                                </div>
                              </div>

                              {/* Room Entry Section */}
                              <div className="border-t border-gray-300 pt-4 mt-4">
                                <div className="flex items-center justify-between mb-3">
                                  <Label className="text-base font-semibold">Room Details</Label>
                                  <Button
                                    type="button"
                                    size="sm"
                                    onClick={() => addRoom(building.id, floorIdx)}
                                    className="bg-green-600 hover:bg-green-700"
                                  >
                                    <Plus className="h-4 w-4 mr-1" />
                                    Add Room
                                  </Button>
                                </div>

                                {/* Rooms List */}
                                {floor.rooms.length === 0 ? (
                                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center text-gray-500 text-sm">
                                    No rooms added yet. Click "Add Room" to start.
                                  </div>
                                ) : (
                                  <div className="space-y-3">
                                    {floor.rooms.map((room, roomIdx) => (
                                      <div key={roomIdx} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                                        <div className="grid grid-cols-12 gap-3 items-end">
                                          <div className="col-span-6">
                                            <Label className="text-xs">Room Type</Label>
                                            <select
                                              value={room.room_type}
                                              onChange={(e) => updateRoom(building.id, floorIdx, roomIdx, 'room_type', e.target.value)}
                                              className="w-full px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg"
                                            >
                                              <option value="Bedroom">Bedroom</option>
                                              <option value="Bathroom">Bathroom</option>
                                              <option value="Attached Bathroom">Attached Bathroom</option>
                                              <option value="Living Room">Living Room</option>
                                              <option value="Dining Room">Dining Room</option>
                                              <option value="Kitchen">Kitchen</option>
                                              <option value="Pantry">Pantry</option>
                                              <option value="Verandah">Verandah</option>
                                              <option value="Balcony">Balcony</option>
                                              <option value="Garage">Garage / Car Porch</option>
                                              <option value="Store Room">Store Room</option>
                                              <option value="Other">Other</option>
                                            </select>
                                          </div>
                                          <div className="col-span-5">
                                            <Label className="text-xs">Number of Rooms</Label>
                                            <Input
                                              type="number"
                                              min="1"
                                              value={room.count || 1}
                                              onChange={(e) => updateRoom(building.id, floorIdx, roomIdx, 'count', parseInt(e.target.value) || 1)}
                                              placeholder="1"
                                              className="text-sm"
                                            />
                                          </div>
                                          <div className="col-span-1">
                                            <button
                                              type="button"
                                              onClick={() => removeRoom(building.id, floorIdx, roomIdx)}
                                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg w-full"
                                              title="Remove"
                                            >
                                              <Trash2 className="h-4 w-4 mx-auto" />
                                            </button>
                                          </div>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                )}

                                {/* Accommodation Summary Display - Auto-calculated */}
                                {floor.accommodation_summary && floor.rooms.length > 0 && (
                                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4 mt-4">
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <p className="text-xs font-semibold text-blue-900 mb-2 flex items-center">
                                          <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                                          Auto-Calculated Accommodation Summary
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                          {floor.accommodation_summary.bedrooms > 0 && (
                                            <span className="px-2.5 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.bedrooms} Bedroom{floor.accommodation_summary.bedrooms !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.bathrooms > 0 && (
                                            <span className="px-2.5 py-1 bg-cyan-100 text-cyan-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.bathrooms} Bathroom{floor.accommodation_summary.bathrooms !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.living_rooms > 0 && (
                                            <span className="px-2.5 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.living_rooms} Living Room{floor.accommodation_summary.living_rooms !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.dining_rooms > 0 && (
                                            <span className="px-2.5 py-1 bg-pink-100 text-pink-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.dining_rooms} Dining Room{floor.accommodation_summary.dining_rooms !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.kitchens > 0 && (
                                            <span className="px-2.5 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.kitchens} Kitchen{floor.accommodation_summary.kitchens !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.pantries > 0 && (
                                            <span className="px-2.5 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.pantries} {floor.accommodation_summary.pantries === 1 ? 'Pantry' : 'Pantries'}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.verandahs > 0 && (
                                            <span className="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.verandahs} Verandah{floor.accommodation_summary.verandahs !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.balconies > 0 && (
                                            <span className="px-2.5 py-1 bg-teal-100 text-teal-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.balconies} {floor.accommodation_summary.balconies === 1 ? 'Balcony' : 'Balconies'}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.garages > 0 && (
                                            <span className="px-2.5 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.garages} Garage{floor.accommodation_summary.garages !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.store_rooms > 0 && (
                                            <span className="px-2.5 py-1 bg-slate-100 text-slate-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.store_rooms} Store Room{floor.accommodation_summary.store_rooms !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                          {floor.accommodation_summary.other_rooms > 0 && (
                                            <span className="px-2.5 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">
                                              {floor.accommodation_summary.other_rooms} Other Room{floor.accommodation_summary.other_rooms !== 1 ? 's' : ''}
                                            </span>
                                          )}
                                        </div>
                                        <p className="text-xs text-blue-700 mt-2 italic">
                                          This summary will be used in the report to generate professional sentences describing the accommodation.
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>

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

                          {/* Photo Upload Area */}
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
                                      💡 Tip: Select multiple files using Ctrl+Click or Shift+Click
                                    </p>
                                    <p className="text-xs text-gray-400">
                                      PNG, JPG up to 10MB each • {MAX_BUILDING_PHOTOS - building.building_photos.length} slot{MAX_BUILDING_PHOTOS - building.building_photos.length !== 1 ? 's' : ''} remaining
                                    </p>
                                  </>
                                )}
                              </label>
                            </div>
                          )}

                          {/* Photo Grid */}
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

                        {/* Additional Structures Section */}
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
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PropertyDescriptionStep;
