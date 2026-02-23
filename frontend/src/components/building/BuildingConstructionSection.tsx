import React from 'react';
import { Building2 } from 'lucide-react';
import { Input } from '../Input';
import { Label } from '../Label';
import { MultiSelectWithCustomInput } from '../MultiSelectWithCustomInput';
import type { Building } from '../../types';
import { BUILDING_TYPES, CONDITIONS } from '../../constants/propertyDescriptionConstants';

interface BuildingConstructionSectionProps {
  building: Building;
  updateBuilding: (id: string, field: string, value: any) => void;
  updateBuildingConstructionMaterial: (buildingId: string, section: string, field: string, value: any) => void;
}

export const BuildingConstructionSection: React.FC<BuildingConstructionSectionProps> = ({
  building,
  updateBuilding,
  updateBuildingConstructionMaterial,
}) => {
  return (
    <>
      {/* Basic Fields */}
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

      {/* Rental Status */}
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

      {/* Building Construction Details */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-6 mt-6">
        <h4 className="font-semibold text-lg text-amber-900 mb-4 flex items-center">
          <Building2 className="h-5 w-5 mr-2" />
          Building Construction Details
        </h4>

        {/* ROOF */}
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

        {/* WALL */}
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
                <option value="mud_walls">Mud Walls (Wattle &amp; Daub)</option>
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

        {/* FLOOR */}
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

        {/* CEILING */}
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
          <h5 className="font-semibold text-md text-gray-800">Doors &amp; Windows</h5>
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

      {/* Utilities & Conveniences */}
      <div className="bg-green-50 border border-green-200 rounded-xl p-5 mb-6">
        <h4 className="font-semibold text-lg text-green-900 mb-4 flex items-center">
          <Building2 className="h-5 w-5 mr-2" />
          Utilities &amp; Conveniences
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
    </>
  );
};
