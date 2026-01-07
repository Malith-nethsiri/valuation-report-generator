"""
Migration: Aggregate floor-based rooms to building level

This migration transforms the room data structure from floor-level to building-level:
- Collects all rooms from all floors in a building
- Aggregates by room_type (sums counts)
- Moves aggregated rooms to building.rooms
- Simplifies floors to only contain floor_name and floor_area
- Calculates building-level accommodation_summary

Usage:
    Run via admin endpoint: POST /api/admin/migrate-rooms
"""

from typing import Dict, List


def calculate_accommodation_summary(rooms: List[Dict]) -> Dict:
    """
    Calculate accommodation summary from rooms list.

    Args:
        rooms: List of room objects with room_type and count

    Returns:
        Dict with aggregated room counts by category
    """
    summary = {
        'bedrooms': 0,
        'bathrooms': 0,
        'living_rooms': 0,
        'dining_rooms': 0,
        'kitchens': 0,
        'pantries': 0,
        'verandahs': 0,
        'balconies': 0,
        'garages': 0,
        'store_rooms': 0,
        'other_rooms': 0
    }

    for room in rooms:
        room_type = room.get('room_type', '').lower()
        count = room.get('count', 1)

        # Map room types to summary categories
        if 'bedroom' in room_type and 'attached' not in room_type:
            summary['bedrooms'] += count
        elif 'attached bathroom' in room_type or ('bathroom' in room_type and 'attached' not in room_type):
            summary['bathrooms'] += count
        elif 'living' in room_type:
            summary['living_rooms'] += count
        elif 'dining' in room_type:
            summary['dining_rooms'] += count
        elif 'kitchen' in room_type:
            summary['kitchens'] += count
        elif 'pantry' in room_type:
            summary['pantries'] += count
        elif 'verandah' in room_type:
            summary['verandahs'] += count
        elif 'balcony' in room_type:
            summary['balconies'] += count
        elif 'garage' in room_type or 'car porch' in room_type:
            summary['garages'] += count
        elif 'store' in room_type:
            summary['store_rooms'] += count
        else:
            summary['other_rooms'] += count

    return summary


def migrate_building_rooms(building_data: Dict) -> Dict:
    """
    Migrate a single building's room data from floor-level to building-level.

    Args:
        building_data: Building dict with old structure (rooms in floors)

    Returns:
        Building dict with new structure (rooms at building level)
    """
    # If building already has rooms at building level, skip migration
    if building_data.get('rooms'):
        return building_data

    # If no floors, nothing to migrate
    if not building_data.get('floors'):
        return building_data

    # Step 1: Collect all rooms from all floors
    all_rooms = []
    for floor in building_data['floors']:
        floor_rooms = floor.get('rooms', [])
        all_rooms.extend(floor_rooms)

    # Step 2: Aggregate by room_type
    room_aggregates = {}
    for room in all_rooms:
        room_type = room.get('room_type')
        if not room_type:
            continue

        count = room.get('count', 1)
        has_attached = room.get('has_attached_bathroom', False)

        if room_type not in room_aggregates:
            room_aggregates[room_type] = {
                'room_type': room_type,
                'count': 0,
                'has_attached_bathroom': has_attached
            }

        room_aggregates[room_type]['count'] += count

        # If any room of this type has attached bathroom, keep that flag
        if has_attached:
            room_aggregates[room_type]['has_attached_bathroom'] = True

    # Step 3: Move to building.rooms
    building_data['rooms'] = list(room_aggregates.values())

    # Step 4: Simplify floors (remove rooms and accommodation_summary)
    simplified_floors = []
    for floor in building_data['floors']:
        simplified_floor = {
            'floor_name': floor['floor_name'],
        }
        # Keep floor_area if it exists
        if 'floor_area' in floor and floor['floor_area'] is not None:
            simplified_floor['floor_area'] = floor['floor_area']

        simplified_floors.append(simplified_floor)

    building_data['floors'] = simplified_floors

    # Step 5: Calculate building-level accommodation_summary
    if building_data['rooms']:
        building_data['accommodation_summary'] = calculate_accommodation_summary(
            building_data['rooms']
        )

    return building_data


def migrate_property_buildings(property_data: Dict) -> Dict:
    """
    Migrate all buildings in a property.

    Args:
        property_data: Property or Report dict with buildings

    Returns:
        Updated property data with migrated buildings
    """
    if not property_data.get('buildings'):
        return property_data

    migrated_buildings = []
    for building in property_data['buildings']:
        migrated_building = migrate_building_rooms(building)
        migrated_buildings.append(migrated_building)

    property_data['buildings'] = migrated_buildings
    return property_data
