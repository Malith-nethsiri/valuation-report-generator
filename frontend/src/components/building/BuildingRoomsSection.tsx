import React from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '../Button';
import { Input } from '../Input';
import { Label } from '../Label';
import type { Building } from '../../types';
import { ROOM_TYPES } from '../../constants/propertyDescriptionConstants';

interface BuildingRoomsSectionProps {
  building: Building;
  addRoomToBuilding: (buildingId: string) => void;
  updateRoomInBuilding: (buildingId: string, roomIndex: number, field: string, value: any) => void;
  removeRoomFromBuilding: (buildingId: string, roomIndex: number) => void;
}

export const BuildingRoomsSection: React.FC<BuildingRoomsSectionProps> = ({
  building,
  addRoomToBuilding,
  updateRoomInBuilding,
  removeRoomFromBuilding,
}) => {
  return (
    <div className="border-2 border-green-200 rounded-xl p-5 mb-4 bg-green-50">
      <div className="mb-4">
        <h4 className="text-lg font-semibold text-green-900">
          Room Details (Building-wide)
        </h4>
      </div>

      {/* Accommodation Summary Badges */}
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
          No rooms added yet. Click &quot;Add Room&quot; to start.
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
  );
};
