"""
Migration: Move occupier information from property-level to building-level

This migration transforms the occupier data structure from property-level to building-level:
- Copies occupier_name and occupier_relationship from property to all buildings
- Only migrates if building doesn't already have occupier data
- Preserves property-level fields for backward compatibility

Usage:
    Run via admin endpoint: POST /api/admin/migrate-occupier
    Or run directly on database records that need migration
"""

from typing import Dict, List, Optional


def migrate_building_occupier(building_data: Dict, property_occupier_name: Optional[str], property_occupier_relationship: Optional[str]) -> Dict:
    """
    Migrate a single building's occupier data from property-level to building-level.

    Args:
        building_data: Building dict
        property_occupier_name: Property-level occupier name to copy
        property_occupier_relationship: Property-level occupier relationship to copy

    Returns:
        Building dict with occupier data at building level
    """
    # If building already has occupier data, skip migration
    if building_data.get('occupier_name'):
        return building_data

    # If property has occupier data, copy to building
    if property_occupier_name:
        building_data['occupier_name'] = property_occupier_name
        building_data['occupier_relationship'] = property_occupier_relationship or ''

    return building_data


def migrate_property_occupier(property_data: Dict) -> Dict:
    """
    Migrate all buildings in a property/report to have building-level occupier data.

    Args:
        property_data: Property or Report dict with buildings and occupier fields

    Returns:
        Updated property data with building-level occupier data
    """
    # Get property-level occupier data
    property_occupier_name = property_data.get('occupier_name')
    property_occupier_relationship = property_data.get('occupier_relationship')

    # If no property-level occupier or no buildings, nothing to migrate
    if not property_occupier_name or not property_data.get('buildings'):
        return property_data

    # Migrate each building
    migrated_buildings = []
    for building in property_data['buildings']:
        migrated_building = migrate_building_occupier(
            building,
            property_occupier_name,
            property_occupier_relationship
        )
        migrated_buildings.append(migrated_building)

    property_data['buildings'] = migrated_buildings

    # NOTE: We keep property-level occupier_name and occupier_relationship
    # for backward compatibility. They are marked as DEPRECATED in the schema
    # but not removed from the database.

    return property_data


def migrate_report(report_data: Dict) -> Dict:
    """
    Migrate a report's occupier data.

    Args:
        report_data: Report dict

    Returns:
        Updated report with migrated occupier data
    """
    return migrate_property_occupier(report_data)


def migrate_property(property_data: Dict) -> Dict:
    """
    Migrate a property's occupier data.

    Args:
        property_data: Property dict

    Returns:
        Updated property with migrated occupier data
    """
    return migrate_property_occupier(property_data)


# Statistics tracking
def get_migration_stats(property_data: Dict) -> Dict:
    """
    Get statistics about what would be migrated.

    Args:
        property_data: Property or Report dict

    Returns:
        Dict with migration statistics
    """
    stats = {
        'has_property_occupier': bool(property_data.get('occupier_name')),
        'total_buildings': len(property_data.get('buildings', [])),
        'buildings_with_occupier': 0,
        'buildings_to_migrate': 0
    }

    for building in property_data.get('buildings', []):
        if building.get('occupier_name'):
            stats['buildings_with_occupier'] += 1
        elif property_data.get('occupier_name'):
            stats['buildings_to_migrate'] += 1

    return stats
