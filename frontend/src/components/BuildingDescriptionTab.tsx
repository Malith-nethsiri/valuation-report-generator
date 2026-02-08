import React from 'react';
import {
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
import { MultiSelectWithCustomInput } from './MultiSelectWithCustomInput';
import type { Building } from '../types';
import {
  BUILDING_TYPES,
  CONDITIONS,
  ROOM_TYPES,
  MAX_BUILDING_PHOTOS,
  MAX_FLOORS_PER_BUILDING,
} from '../constants/propertyDescriptionConstants';

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
  floorCount: {[buildingId: string]: number};
  setFloorCount: React.Dispatch<React.SetStateAction<{[buildingId: string]: number}>>;
  floorsExpanded: {[buildingId: string]: boolean};
  setFloorsExpanded: React.Dispatch<React.SetStateAction<{[buildingId: string]: boolean}>>;
  uploadingPhotos: {[buildingId: string]: boolean};
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
  copyOccupierFromFirstBuilding: _copyOccupierFromFirstBuilding,
  updateBuildingConstructionMaterial,
  generateFloors,
  addFloor: _addFloor,
  updateFloorName,
  updateFloorArea,
  addRoom: _addRoom,
  updateRoom: _updateRoom,
  removeRoom: _removeRoom,
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
  register: _register,
  watch: _watch,
  setValue: _setValue,
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
                      <Label>Age (Years)</Label>
                      <Input
                        type="number"
                        value={building.building_age || ''}
                        onChange={(e) => updateBuilding(building.id, 'building_age', parseInt(e.target.value) || 0)}
                        placeholder="e.g., 10"
                        min="0"
                        max="200"
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

                  {/* Rental Status - Per Building */}
                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <h5 className="text-md font-semibold text-gray-900 mb-3">Rental Status</h5>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-6">
                        <span className="text-gray-700">Is this building rented?</span>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name={`is_rented_${building.id}`}
                            checked={building.is_rented === true}
                            onChange={() => updateBuilding(building.id, 'is_rented', true)}
                            className="mr-2"
                          />
                          Yes
                        </label>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name={`is_rented_${building.id}`}
                            checked={building.is_rented === false}
                            onChange={() => updateBuilding(building.id, 'is_rented', false)}
                            className="mr-2"
                          />
                          No
                        </label>
                      </div>
                      {building.is_rented && (
                        <div>
                          <Label htmlFor={`rent_details_${building.id}`}>Rent Details (Optional)</Label>
                          <textarea
                            id={`rent_details_${building.id}`}
                            value={building.rent_details || ''}
                            onChange={(e) => updateBuilding(building.id, 'rent_details', e.target.value)}
                            className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                            rows={2}
                            maxLength={500}
                            placeholder="Enter rent amount, lease terms, or other details..."
                          />
                        </div>
                      )}
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

                  {/* Utilities & Conveniences Section */}
                  <div className="bg-green-50 border border-green-200 rounded-xl p-5 mb-6">
                    <h4 className="font-semibold text-lg text-green-900 mb-4 flex items-center">
                      <Building2 className="h-5 w-5 mr-2" />
                      Utilities & Conveniences
                    </h4>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <MultiSelectWithCustomInput
                            label="Water Supply"
                            value={building.utilities_services?.water_supply || []}
                            onChange={(values) => updateBuilding(building.id, 'utilities_services', {
                              ...building.utilities_services,
                              water_supply: values
                            })}
                            predefinedOptions={[
                              { value: 'Pipe-borne (NWSDB)', label: 'Pipe-borne (NWSDB)' },
                              { value: 'Well', label: 'Well' },
                              { value: 'Bore/Tube Well', label: 'Bore/Tube Well' },
                              { value: 'Rainwater Harvesting', label: 'Rainwater Harvesting' }
                            ]}
                            maxSelections={5}
                            maxCharacters={50}
                            helperText="Select up to 5 types or add custom values (press Enter)"
                          />
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
                                checked={(building.utilities_services?.amenities as any)?.[amenity.key] || false}
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

                      {/* Communication Services */}
                      <div>
                        <Label>Communication Services</Label>
                        <div className="grid grid-cols-2 gap-3 mt-2">
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={building.utilities_services?.telephone || false}
                              onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                ...building.utilities_services,
                                telephone: e.target.checked
                              })}
                              className="mr-2 rounded"
                            />
                            Telephone Connection
                          </label>
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={building.utilities_services?.internet || false}
                              onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                                ...building.utilities_services,
                                internet: e.target.checked
                              })}
                              className="mr-2 rounded"
                            />
                            Internet Connection
                          </label>
                        </div>
                      </div>

                      {/* Gas Connection */}
                      <div>
                        <Label>Gas Connection</Label>
                        <label className="flex items-center mt-2">
                          <input
                            type="checkbox"
                            checked={building.utilities_services?.gas_connection || false}
                            onChange={(e) => updateBuilding(building.id, 'utilities_services', {
                              ...building.utilities_services,
                              gas_connection: e.target.checked
                            })}
                            className="mr-2 rounded"
                          />
                          Gas connection available
                        </label>
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

                    {/* NEW LAYOUT: Collapsible Floors Section */}
                    {building.floors.length > 0 && (
                      <div className="border-2 border-blue-200 rounded-xl p-5 mb-4 bg-blue-50">
                        <button
                          type="button"
                          onClick={() => setFloorsExpanded({
                            ...floorsExpanded,
                            [building.id]: !floorsExpanded[building.id]
                          })}
                          className="w-full flex items-center justify-between hover:opacity-80 transition-opacity"
                        >
                          <h4 className="text-lg font-semibold text-blue-900">
                            Floor Information ({building.floors.length} floor{building.floors.length !== 1 ? 's' : ''})
                          </h4>
                          {floorsExpanded[building.id] ?
                            <ChevronUp className="h-5 w-5 text-blue-600" /> :
                            <ChevronDown className="h-5 w-5 text-blue-600" />
                          }
                        </button>

                        {floorsExpanded[building.id] && (
                          <div className="mt-4 space-y-3">
                            {building.floors.map((floor, floorIdx) => (
                              <div key={floorIdx} className="bg-white border border-blue-200 rounded-lg p-4">
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <Label className="text-sm">Floor Name</Label>
                                    <Input
                                      value={floor.floor_name}
                                      onChange={(e) => updateFloorName(building.id, floorIdx, e.target.value)}
                                      className="text-sm"
                                      placeholder="e.g., Ground Floor"
                                    />
                                  </div>
                                  <div>
                                    <Label className="text-sm">Floor Area (sq ft)</Label>
                                    <Input
                                      type="number"
                                      value={floor.floor_area || ''}
                                      onChange={(e) => updateFloorArea(building.id, floorIdx, parseFloat(e.target.value) || 0)}
                                      className="text-sm"
                                      placeholder="0"
                                    />
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* NEW: Building-Level Room Details Section */}
                    <div className="border-2 border-green-200 rounded-xl p-5 mb-4 bg-green-50">
                      <div className="mb-4">
                        <h4 className="text-lg font-semibold text-green-900">
                          Room Details (Building-wide)
                        </h4>
                      </div>

                      {/* Live Accommodation Summary Badges */}
                      {building.accommodation_summary && (building.rooms?.length ?? 0) > 0 && (
                        <div className="mb-4 flex flex-wrap gap-2">
                          {building.accommodation_summary.bedrooms > 0 && (
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.bedrooms} Bedroom{building.accommodation_summary.bedrooms > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.bathrooms > 0 && (
                            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.bathrooms} Bathroom{building.accommodation_summary.bathrooms > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.living_rooms > 0 && (
                            <span className="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.living_rooms} Living Room{building.accommodation_summary.living_rooms > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.dining_rooms > 0 && (
                            <span className="px-3 py-1 bg-pink-100 text-pink-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.dining_rooms} Dining Room{building.accommodation_summary.dining_rooms > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.kitchens > 0 && (
                            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.kitchens} Kitchen{building.accommodation_summary.kitchens > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.pantries > 0 && (
                            <span className="px-3 py-1 bg-lime-100 text-lime-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.pantries} {building.accommodation_summary.pantries === 1 ? 'Pantry' : 'Pantries'}
                            </span>
                          )}
                          {building.accommodation_summary.verandahs > 0 && (
                            <span className="px-3 py-1 bg-teal-100 text-teal-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.verandahs} Verandah{building.accommodation_summary.verandahs > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.balconies > 0 && (
                            <span className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.balconies} {building.accommodation_summary.balconies === 1 ? 'Balcony' : 'Balconies'}
                            </span>
                          )}
                          {building.accommodation_summary.garages > 0 && (
                            <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.garages} Garage{building.accommodation_summary.garages > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.store_rooms > 0 && (
                            <span className="px-3 py-1 bg-slate-100 text-slate-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.store_rooms} Store Room{building.accommodation_summary.store_rooms > 1 ? 's' : ''}
                            </span>
                          )}
                          {building.accommodation_summary.other_rooms > 0 && (
                            <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm font-medium">
                              {building.accommodation_summary.other_rooms} Other{building.accommodation_summary.other_rooms > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Rooms List */}
                      {(!building.rooms || building.rooms.length === 0) ? (
                        <div className="bg-white border border-gray-200 rounded-lg p-4 text-center text-gray-500 text-sm">
                          No rooms added yet. Click "Add Room" to start.
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {(building.rooms || []).map((room, roomIdx) => (
                            <div key={roomIdx} data-room-id={`${building.id}-${roomIdx}`} className="bg-white border border-green-200 rounded-lg p-3">
                              <div className="grid grid-cols-12 gap-3 items-end">
                                <div className="col-span-6">
                                  <Label className="text-xs">Room Type</Label>
                                  <select
                                    value={room.room_type}
                                    onChange={(e) => updateRoomInBuilding(building.id, roomIdx, 'room_type', e.target.value)}
                                    className="w-full px-3 py-2 text-sm bg-white border border-gray-300 rounded-lg focus:border-green-500 focus:ring-1 focus:ring-green-500"
                                  >
                                    {ROOM_TYPES.map(type => (
                                      <option key={type} value={type}>{type}</option>
                                    ))}
                                  </select>
                                </div>
                                <div className="col-span-5">
                                  <Label className="text-xs">Number of Rooms</Label>
                                  <Input
                                    type="number"
                                    min="1"
                                    value={room.count || 1}
                                    onChange={(e) => updateRoomInBuilding(building.id, roomIdx, 'count', parseInt(e.target.value) || 1)}
                                    placeholder="1"
                                    className="text-sm"
                                  />
                                </div>
                                <div className="col-span-1">
                                  <button
                                    type="button"
                                    onClick={() => removeRoomFromBuilding(building.id, roomIdx)}
                                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg w-full"
                                    title="Remove"
                                  >
                                    <Trash2 className="h-4 w-4 mx-auto" />
                                  </button>
                                </div>
                              </div>

                              {/* Attached Bathroom Checkbox (only for Bedrooms) */}
                              {room.room_type === 'Bedroom' && (
                                <div className="mt-2">
                                  <label className="flex items-center text-sm text-gray-700">
                                    <input
                                      type="checkbox"
                                      checked={room.has_attached_bathroom || false}
                                      onChange={(e) => updateRoomInBuilding(building.id, roomIdx, 'has_attached_bathroom', e.target.checked)}
                                      className="mr-2 rounded border-gray-300 text-green-600 focus:ring-green-500"
                                    />
                                    Has attached bathroom
                                  </label>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Add Room Button - Bottom Right */}
                      <div className="flex justify-end mt-3">
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => addRoomToBuilding(building.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add Room
                        </Button>
                      </div>
                    </div>
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
                                Tip: Select multiple files using Ctrl+Click or Shift+Click
                              </p>
                              <p className="text-xs text-gray-400">
                                PNG, JPG up to 10MB each {'\u2022'} {MAX_BUILDING_PHOTOS - building.building_photos.length} slot{MAX_BUILDING_PHOTOS - building.building_photos.length !== 1 ? 's' : ''} remaining
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
  );
};

export default BuildingDescriptionTab;
