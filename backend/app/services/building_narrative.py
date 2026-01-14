"""
AI-powered narrative generation for building descriptions in valuation reports.
Uses Claude API (same as locality descriptions).
"""
import os
from typing import Dict, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv
from ..docx_generator import format_list_with_grammar

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def format_floors(floors: Optional[List[Dict]]) -> str:
    """Format floor data for AI prompt, using accommodation summaries if available."""
    if not floors:
        return "No floor data provided."

    lines = []
    for floor in floors:
        floor_name = floor.get('floor_name', 'Floor')
        floor_area = floor.get('floor_area', 0)

        # NEW: Use accommodation summary if available
        summary = floor.get('accommodation_summary')
        if summary:
            room_counts = []
            if summary.get('bedrooms', 0) > 0:
                count = summary['bedrooms']
                room_counts.append(f"{count} bedroom{'s' if count != 1 else ''}")
            if summary.get('bathrooms', 0) > 0:
                count = summary['bathrooms']
                room_counts.append(f"{count} bathroom{'s' if count != 1 else ''}")
            if summary.get('living_rooms', 0) > 0:
                count = summary['living_rooms']
                room_counts.append(f"{count} living room{'s' if count != 1 else ''}")
            if summary.get('dining_rooms', 0) > 0:
                count = summary['dining_rooms']
                room_counts.append(f"{count} dining room{'s' if count != 1 else ''}")
            if summary.get('kitchens', 0) > 0:
                count = summary['kitchens']
                room_counts.append(f"{count} kitchen{'s' if count != 1 else ''}")
            if summary.get('pantries', 0) > 0:
                count = summary['pantries']
                room_counts.append(f"{count} {'pantries' if count != 1 else 'pantry'}")
            if summary.get('verandahs', 0) > 0:
                count = summary['verandahs']
                room_counts.append(f"{count} verandah{'s' if count != 1 else ''}")
            if summary.get('balconies', 0) > 0:
                count = summary['balconies']
                room_counts.append(f"{count} {'balconies' if count != 1 else 'balcony'}")
            if summary.get('garages', 0) > 0:
                count = summary['garages']
                room_counts.append(f"{count} garage{'s' if count != 1 else ''}")
            if summary.get('store_rooms', 0) > 0:
                count = summary['store_rooms']
                room_counts.append(f"{count} store room{'s' if count != 1 else ''}")
            if summary.get('other_rooms', 0) > 0:
                count = summary['other_rooms']
                room_counts.append(f"{count} other room{'s' if count != 1 else ''}")

            if room_counts:
                floor_info = f"{floor_name} ({floor_area} sq ft): {', '.join(room_counts)}"
                lines.append(floor_info)
            else:
                lines.append(f"{floor_name}: {floor_area} sq ft (no rooms specified)")
        else:
            # Fallback if no summary available
            rooms = floor.get('rooms', [])
            if rooms:
                room_list = [f"{r.get('count', 1)} {r.get('room_type', 'Room')}" for r in rooms]
                lines.append(f"{floor_name}: {', '.join(room_list)}")
            else:
                lines.append(f"{floor_name}: {floor_area} sq ft")

    return "\n".join(lines)


def format_materials(construction: Optional[Dict]) -> str:
    """Format construction materials for AI prompt using NEW enhanced structure."""
    if not construction:
        return "No construction data provided."

    parts = []

    # NEW: Roof Details
    roof = construction.get('roof_details', {})
    if roof:
        roof_parts = []
        if roof.get('structure_type'):
            structure_labels = {
                'timber_frame': 'timber frame',
                'steel_trusses': 'steel trusses',
                'concrete_slab': 'concrete slab',
                'rcc_flat': 'RCC flat roof',
                'prefab_trusses': 'prefabricated trusses',
                'mixed': 'mixed construction'
            }
            roof_parts.append(structure_labels.get(roof['structure_type'], roof['structure_type'].replace('_', ' ')))

        if roof.get('covering_material'):
            covering_labels = {
                'asbestos_sheets': 'asbestos sheets',
                'clay_tiles': 'clay tiles',
                'concrete_tiles': 'concrete tiles',
                'metal_sheets': 'metal sheets',
                'concrete_flat': 'concrete flat',
                'cadjans': 'cadjans',
                'shingles': 'shingles'
            }
            materials = [covering_labels.get(m, m.replace('_', ' ')) for m in roof['covering_material']]
            roof_parts.append(f"covered with {', '.join(materials)}")

        if roof.get('additional_details'):
            roof_parts.append(roof['additional_details'])

        if roof_parts:
            parts.append(f"Roof: {' '.join(roof_parts)}")

    # NEW: Wall Details
    wall = construction.get('wall_details', {})
    if wall:
        wall_parts = []
        if wall.get('material'):
            material_labels = {
                'brick_masonry': 'brick masonry',
                'cement_block': 'cement block',
                'stone_masonry': 'stone masonry',
                'rcc_frame': 'RCC frame',
                'rubble_masonry': 'rubble masonry',
                'mud_walls': 'mud walls',
                'timber_frame': 'timber frame',
                'cadjan': 'cadjan',
                'prefab_panels': 'prefabricated panels',
                'mixed': 'mixed materials'
            }
            wall_parts.append(material_labels.get(wall['material'], wall['material'].replace('_', ' ')))

        if wall.get('finish'):
            finish_labels = {
                'cement_plaster_painted': 'cement plaster and painted',
                'lime_plaster': 'lime plaster',
                'tiles': 'tiles',
                'exposed_brick': 'exposed brick',
                'color_washed': 'color washed',
                'textured': 'textured finish',
                'unfinished': 'unfinished'
            }
            finishes = [finish_labels.get(f, f.replace('_', ' ')) for f in wall['finish']]
            wall_parts.append(f"finished with {', '.join(finishes)}")

        if wall_parts:
            parts.append(f"Walls: {', '.join(wall_parts)}")

    # NEW: Floor Details
    floor = construction.get('floor_details', {})
    if floor and floor.get('material'):
        material_labels = {
            'cement': 'cement',
            'tiled': 'tiles',
            'terrazzo': 'terrazzo',
            'timber': 'timber',
            'granite': 'granite',
            'marble': 'marble',
            'vinyl': 'vinyl',
            'polished_concrete': 'polished concrete',
            'earth': 'earth'
        }
        materials = [material_labels.get(m, m.replace('_', ' ')) for m in floor['material']]
        floor_text = f"Floors: {', '.join(materials)}"

        if floor.get('finish_quality'):
            quality_labels = {'basic': 'basic', 'standard': 'good', 'premium': 'premium'}
            floor_text += f" ({quality_labels.get(floor['finish_quality'], floor['finish_quality'])} quality)"

        parts.append(floor_text)

    # Ceiling (keep existing)
    if construction.get('ceiling_type') and construction['ceiling_type'] != 'none':
        ceiling_labels = {
            'gypsum_board': 'gypsum board',
            'plywood': 'plywood',
            'asbestos': 'asbestos',
            'pvc': 'PVC panels',
            'timber': 'timber planks'
        }
        ceiling_type = ceiling_labels.get(construction['ceiling_type'], construction['ceiling_type'].replace('_', ' '))
        parts.append(f"Ceiling: {ceiling_type}")

    # Doors & Windows (NEW)
    doors_windows = construction.get('doors_windows_details', {})
    if doors_windows:
        dw_parts = []

        # Windows
        window_frame = doors_windows.get('window_frame_material', [])
        window_glass = doors_windows.get('window_glass_type', [])
        window_security = doors_windows.get('window_security', [])

        window_info = []
        if window_frame:
            frame_labels = {'timber': 'timber', 'aluminum': 'aluminum', 'upvc': 'UPVC', 'steel': 'steel'}
            window_info.append(', '.join([frame_labels.get(f, f) for f in window_frame]))
        if window_glass:
            glass_labels = {'clear': 'clear glass', 'tinted': 'tinted', 'frosted': 'frosted', 'double_glazing': 'double glazing'}
            window_info.append(', '.join([glass_labels.get(g, g) for g in window_glass]))
        if window_security:
            security_labels = {'burglar_bars': 'burglar bars', 'grills': 'grills', 'security_mesh': 'security mesh'}
            window_info.append(', '.join([security_labels.get(s, s) for s in window_security]))

        if window_info:
            dw_parts.append(f"Windows: {' with '.join(window_info)}")

        # Doors
        main_door = doors_windows.get('main_door_material')
        internal_door = doors_windows.get('internal_door_material')
        door_security = doors_windows.get('door_security', [])

        door_info = []
        if main_door:
            main_labels = {'solid_timber': 'solid timber', 'panel_door': 'timber panel', 'metal': 'metal', 'upvc': 'UPVC', 'glass': 'glass'}
            door_info.append(f"main door: {main_labels.get(main_door, main_door.replace('_', ' '))}")
        if internal_door:
            internal_labels = {'timber': 'timber', 'flush_doors': 'flush doors', 'panel_doors': 'panel doors', 'hollow_core': 'hollow core'}
            door_info.append(f"internal: {internal_labels.get(internal_door, internal_door.replace('_', ' '))}")
        if door_security:
            security_labels = {'deadbolt': 'deadbolt', 'security_locks': 'security locks', 'door_chain': 'door chain', 'multi_point': 'multi-point locking'}
            door_info.append(f"security: {', '.join([security_labels.get(s, s) for s in door_security])}")

        if door_info:
            dw_parts.append(f"Doors: {'; '.join(door_info)}")

        if dw_parts:
            parts.extend(dw_parts)

    # BACKWARD COMPATIBILITY: Fallback to old format if new structure not available
    if not parts:
        if construction.get('foundation_type'):
            parts.append(f"Foundation: {construction['foundation_type'].replace('_', ' ').title()}")

        wall_old = construction.get('wall_construction', {})
        if wall_old:
            wall_parts = []
            if wall_old.get('material'):
                wall_parts.append(wall_old['material'].replace('_', ' ').title())
            if wall_old.get('thickness'):
                wall_parts.append(wall_old['thickness'].replace('_', ' '))
            if wall_old.get('finish'):
                wall_parts.append(wall_old['finish'].replace('_', ' ').title())
            if wall_parts:
                parts.append(f"Walls: {', '.join(wall_parts)}")

        if construction.get('roof_structure'):
            parts.append(f"Roof: {construction['roof_structure'].replace('_', ' ').title()}")

    return "\n".join(parts) if parts else "Basic construction"


def format_utilities(utilities: Optional[Dict]) -> str:
    """Format utilities for AI prompt."""
    if not utilities:
        return "No utilities data provided."

    parts = []

    if utilities.get('water_supply'):
        water_supply = utilities['water_supply']
        water_map = {
            'Pipe-borne (NWSDB)': 'pipe-borne water (NWSDB)',
            'Well': 'well water',
            'Bore/Tube Well': 'bore/tube well water',
            'Rainwater Harvesting': 'rainwater harvesting',
            # Old values for backward compatibility
            'pipe_borne': 'pipe-borne water (NWSDB)',
            'well': 'well water',
            'tube_well': 'tube well'
        }

        # Handle both string (legacy) and array (new) formats
        if isinstance(water_supply, str):
            # Legacy single value
            parts.append(water_map.get(water_supply, water_supply))
        elif isinstance(water_supply, list):
            # New multi-select array
            mapped_values = [
                water_map.get(ws, ws.lower())
                for ws in water_supply
            ]
            parts.append(format_list_with_grammar(mapped_values))

    elec = utilities.get('electricity', {})
    if elec.get('source'):
        source = 'CEB' if elec['source'] == 'ceb' else elec['source'].title()
        phase = " (Three-Phase)" if elec.get('three_phase') else ""
        parts.append(f"{source} electricity{phase}")

    parking = utilities.get('parking', {})
    total = (parking.get('covered_spaces', 0) + parking.get('uncovered_spaces', 0))
    if total > 0:
        parts.append(f"Parking for {total} vehicle{'s' if total != 1 else ''}")

    # Communication services
    comm_parts = []
    if utilities.get('telephone'):
        comm_parts.append('telephone')
    if utilities.get('internet'):
        comm_parts.append('internet')
    if comm_parts:
        parts.append(f"Communication: {', '.join(comm_parts)}")

    # Gas connection
    if utilities.get('gas_connection'):
        parts.append('Gas connection available')

    security = utilities.get('security_features', [])
    if security:
        sec_labels = {
            'boundary_wall': 'Boundary wall',
            'main_gate': 'Main gate',
            'cctv': 'CCTV',
            'security_lights': 'Security lighting'
        }
        sec_list = [sec_labels.get(s, s) for s in security]
        parts.append(f"Security: {', '.join(sec_list)}")

    amenities = utilities.get('amenities', {})
    amen_list = []
    if amenities.get('air_conditioning'):
        amen_list.append('air conditioning')
    if amenities.get('built_in_wardrobes'):
        amen_list.append('built-in wardrobes')
    if amenities.get('modern_kitchen'):
        amen_list.append('modern kitchen fittings')
    if amen_list:
        parts.append(f"Amenities: {', '.join(amen_list)}")

    if utilities.get('hot_water_system') and utilities['hot_water_system'] != 'none':
        hw_map = {
            'electric_geyser': 'Electric geyser',
            'solar_heater': 'Solar water heater',
            'gas_heater': 'Gas water heater'
        }
        parts.append(hw_map.get(utilities['hot_water_system'], 'Hot water system'))

    return "\n".join(parts) if parts else "Basic utilities"


async def generate_building_narrative(
    building_name: str,
    building_type: str,
    stories: int,
    floors: Optional[List[Dict]] = None,
    construction_materials: Optional[Dict] = None,
    utilities_services: Optional[Dict] = None,
    total_floor_area: Optional[float] = None,
    building_age: Optional[int] = None,
    condition: Optional[str] = None,
    roof_types: Optional[List[str]] = None,
    wall_types: Optional[List[str]] = None,
    floor_types: Optional[List[str]] = None
) -> Optional[str]:
    """
    Generate professional building description for Sri Lankan valuation reports.
    Returns condensed one-paragraph description matching industry standards.
    """
    if not ANTHROPIC_API_KEY:
        print("[BUILDING_NARRATIVE] Warning: ANTHROPIC_API_KEY not set")
        return None

    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        # Build context from all building data
        context_parts = []
        context_parts.append(f"Building Name: {building_name}")
        context_parts.append(f"Type: {building_type}")
        context_parts.append(f"Stories: {stories}")

        if total_floor_area:
            context_parts.append(f"Total Area: {total_floor_area} sq ft")

        if building_age is not None and building_age > 0:
            year_word = "year" if building_age == 1 else "years"
            context_parts.append(f"Age: {building_age} {year_word}")

        if condition:
            context_parts.append(f"Condition: {condition}")

        if roof_types:
            roof_labels = {
                'asbestos_sheets': 'asbestos sheets',
                'clay_tiles': 'clay tiles',
                'metal_sheets': 'metal sheets',
                'concrete': 'concrete',
                'cadjan': 'cadjan',
                'zinc_sheets': 'zinc sheets'
            }
            roof_text = ', '.join([roof_labels.get(r, r) for r in roof_types])
            context_parts.append(f"Roof: {roof_text}")

        if wall_types:
            wall_labels = {
                'brick': 'brick masonry',
                'cement_block': 'cement block',
                'stone': 'stone',
                'cadjan': 'cadjan',
                'rcc_columns': 'RCC columns'
            }
            wall_text = ', '.join([wall_labels.get(w, w) for w in wall_types])
            context_parts.append(f"Walls: {wall_text}")

        if floor_types:
            floor_labels = {
                'cement': 'cement',
                'tile': 'tiles',
                'terrazzo': 'terrazzo',
                'timber': 'timber',
                'granite': 'granite'
            }
            floor_text = ', '.join([floor_labels.get(f, f) for f in floor_types])
            context_parts.append(f"Floors: {floor_text}")

        if floors:
            context_parts.append(f"\nFloor Details:\n{format_floors(floors)}")

        if construction_materials:
            context_parts.append(f"\nConstruction Details:\n{format_materials(construction_materials)}")

        if utilities_services:
            context_parts.append(f"\nUtilities & Services:\n{format_utilities(utilities_services)}")

        context = "\n".join(context_parts)

        # Prompt engineering for Sri Lankan valuation style
        prompt = f"""You are a professional property valuer in Sri Lanka writing a building description for a formal valuation report.

BUILDING DATA:
{context}

TASK: Generate a professional building description in ONE paragraph (maximum 150 words).

STYLE REQUIREMENTS (Critical - match Sri Lankan valuation reports):
1. Start with construction: "This is constructed with [roof covering] on [roof structure] supported by [wall material and finish] and the floor is [floor materials] rendered."
2. Flow naturally into accommodation using ROOM COUNTS from the provided floor details: "The accommodation comprises [Floor Name] having [X bedrooms, Y bathrooms, Z living rooms, etc.]"
3. Mention key utilities and features: "The building is provided with [utilities list]."
4. Use formal, technical language
5. Third person, past tense for construction
6. Condensed but comprehensive
7. IMPORTANT: Generate professional sentences from the structured data, NOT just list items

EXAMPLE STYLE (professional Sri Lankan valuation):
"This is constructed with clay tiles on timber frame roof supported by brick masonry walls finished with cement plaster and painted, and the floor is cement and tiles rendered. The accommodation comprises the Ground Floor having three bedrooms (two with attached bathrooms), one living room, one dining room, one kitchen and one verandah, and the First Floor having two bedrooms and one family room. The building is provided with pipe-borne water, CEB electricity with three-phase connection, modern kitchen fittings, built-in wardrobes and hot water facilities. Parking is available for two vehicles with boundary wall and main gate."

NOTE: When the Floor Details section shows room counts (e.g., "Ground Floor (1,245 sq ft): 3 bedrooms, 2 bathrooms, 1 kitchen"), use these counts to generate the accommodation description. Express them as "three bedrooms, two bathrooms, one kitchen" in your narrative.

Generate now:"""

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Same model as locality
            max_tokens=300,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        narrative = message.content[0].text.strip()
        print(f"[BUILDING_NARRATIVE] Generated {len(narrative)} chars")
        return narrative

    except Exception as e:
        print(f"[BUILDING_NARRATIVE] Error: {str(e)}")
        return None
