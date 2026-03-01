"""
Situation, location, access, and boundary text generators.
"""
from typing import Optional
import logging

from .. import models
from ..utils import append_label_if_missing, clean_spelling_errors, format_no_field

logger = logging.getLogger(__name__)


def generate_situation_text(report: models.Report) -> Optional[str]:
    """
    Generate SITUATION section text from property location data.
    """
    print(f"[SITUATION] Report ID: {report.id}")
    print(f"[SITUATION] Village: {report.property_village}")
    print(f"[SITUATION] District: {report.property_district}")
    print(f"[SITUATION] GN Division: {report.grama_niladari_division}")
    print(f"[SITUATION] DS Division: {report.property_divisional_secretariat}")
    print(f"[SITUATION] Korale: {report.korale}")
    print(f"[SITUATION] Pradeshiya Sabha: {report.pradeshiya_sabha}")

    if not (report.property_village or report.property_district):
        print("[SITUATION] No location data found, returning None")
        return None

    parts = []

    prefix = "The property"
    if report.assessment_number:
        assessment_formatted = format_no_field("Assessment", report.assessment_number, include_label=False)
        prefix += f" to be valued is situated bearing {assessment_formatted}"
        if report.land_traditional_name:
            prefix += f" {report.land_traditional_name}"
    elif report.land_traditional_name:
        prefix += f" is situated at {report.land_traditional_name}"
    else:
        prefix += " is situated"

    if report.property_village:
        if " is situated" in prefix and prefix.endswith("situated"):
            parts.append(f"in {report.property_village} village")
        else:
            parts.append(f" in {report.property_village} village")

    if report.property_number:
        property_no_formatted = format_no_field("", report.property_number, include_label=False)
        parts.append(f"in {property_no_formatted}")

    direction_suffix = ""
    if report.location_direction:
        direction_suffix = f"-{report.location_direction}"

    if report.grama_niladari_division:
        cleaned = clean_spelling_errors(report.grama_niladari_division)
        gn_text = append_label_if_missing(
            cleaned,
            "Grama Niladari division",
            variants=["grama niladari division", "Grama Niladari Division", "GN division", "GN Division"]
        )
        if direction_suffix and "Grama Niladari division" in gn_text:
            gn_text = gn_text.replace(" Grama Niladari division", f"{direction_suffix} Grama Niladari division")
        elif direction_suffix:
            gn_text = f"{gn_text}{direction_suffix}"
        parts.append(gn_text)

    if report.property_divisional_secretariat:
        cleaned = clean_spelling_errors(report.property_divisional_secretariat)
        ds_text = append_label_if_missing(
            cleaned,
            "Divisional Secretariat",
            variants=[
                "divisional secretariat division",
                "Divisional Secretariat Division",
                "divisional secretariat",
                "DS division",
                "DS Division"
            ]
        )
        if "division" in ds_text.lower():
            parts.append(f"within the {ds_text} of")
        else:
            parts.append(f"within the {ds_text} division of")

    if report.hathpaththuwa:
        cleaned = clean_spelling_errors(report.hathpaththuwa)
        hathpaththuwa_text = append_label_if_missing(cleaned, "Hathpaththuwa", variants=["hathpaththuwa", "hatpattu"])
        parts.append(f"in {hathpaththuwa_text}")

    if report.korale:
        cleaned = clean_spelling_errors(report.korale)
        korale_text = append_label_if_missing(cleaned, "Korale", variants=["korale"])
        parts.append(f"in {korale_text}")

    if report.is_municipal_limit and report.property_district:
        district_cleaned = clean_spelling_errors(report.property_district)
        district_text = append_label_if_missing(district_cleaned, "District", variants=["district"])
        parts.append(f"within the Municipal Council limit of {district_text}")
    elif report.pradeshiya_sabha:
        cleaned = clean_spelling_errors(report.pradeshiya_sabha)
        ps_text = append_label_if_missing(cleaned, "Pradeshiya Sabha", variants=["pradeshiya sabha", "PS"])
        parts.append(f"of {ps_text}")

    if report.property_district and not report.is_municipal_limit:
        cleaned = clean_spelling_errors(report.property_district)
        district_text = append_label_if_missing(cleaned, "District", variants=["district"])
        parts.append(f"in {district_text}")

    if report.property_province:
        cleaned = clean_spelling_errors(report.property_province)
        province_text = append_label_if_missing(cleaned, "Province", variants=["province"])
        parts.append(province_text)

    if parts:
        parts.append("of Sri Lanka")

    if parts:
        situation_text = prefix + " " + " ".join(parts) + "."
    else:
        smart_address = generate_smart_address(report)
        if smart_address:
            situation_text = f"The property is situated at {smart_address}."
        else:
            print("[SITUATION] No situation text could be generated")
            return None

    print(f"[SITUATION] Generated text: {situation_text}")
    return situation_text


def generate_smart_address(report: models.Report) -> Optional[str]:
    """
    Generate formatted property address from address components.
    """
    components = []

    if report.property_number:
        components.append(report.property_number)

    if report.property_village:
        components.append(f"{report.property_village} Village")

    if report.grama_niladari_division:
        components.append(f"{report.grama_niladari_division} Grama Niladari Division")

    if hasattr(report, 'property_divisional_secretariat') and report.property_divisional_secretariat:
        components.append(f"{report.property_divisional_secretariat} Divisional Secretariat Division")

    if report.hathpaththuwa:
        components.append(report.hathpaththuwa)

    if report.korale:
        components.append(report.korale)

    if report.pradeshiya_sabha:
        components.append(report.pradeshiya_sabha)

    if report.property_district:
        components.append(f"{report.property_district} District")

    if report.property_province:
        components.append(report.property_province)

    if not components:
        return None

    return ", ".join(components)


def generate_access_text(report: models.Report) -> Optional[str]:
    """Generate ACCESS section text from access directions data"""
    print(f"[ACCESS] Report ID: {report.id}")
    print(f"[ACCESS] Directions Text: {report.access_directions_text}")
    print(f"[ACCESS] Starting Point: {report.access_starting_point_name}")
    print(f"[ACCESS] Distance: {report.access_distance_km}")
    print(f"[ACCESS] Map Image URL: {report.location_map_image_data}")

    if not report.access_directions_text:
        print("[ACCESS] No access directions text found, returning None")
        return None

    print(f"[ACCESS] Returning access text: {report.access_directions_text}")
    return report.access_directions_text


def generate_locality_description(report: models.Report) -> Optional[str]:
    """Generate LOCALITY section text from locality data"""
    print(f"[LOCALITY] Report ID: {report.id}")
    print(f"[LOCALITY] Description Text: {report.locality_description_text}")
    print(f"[LOCALITY] Major Town: {report.major_town_name} ({report.distance_to_major_town_km} km)")
    print(f"[LOCALITY] Nearby Facilities: {len(report.nearby_facilities) if report.nearby_facilities else 0}")

    if not report.locality_description_text:
        print("[LOCALITY] No locality description text found, returning None")
        return None

    print(f"[LOCALITY] Returning locality text: {report.locality_description_text}")
    return report.locality_description_text


def generate_boundary_summary_text(report: models.Report) -> Optional[str]:
    """
    Generate professional boundary summary sentence from boundary types.
    """
    boundary_type_labels = {
        'brick_walls': 'brick masonry parapet walls',
        'barbed_wire': 'barbed wire fence',
        'live_fence': 'live fence',
        'concrete_posts': 'concrete posts',
        'iron_gate': 'iron gate',
        'rubble_foundation': 'rubble masonry foundation',
        'chain_link': 'chain link fence',
        'wooden_fence': 'wooden fence',
        'stone_wall': 'stone wall',
        'hedge': 'hedge'
    }

    entrance_labels = {
        'auto_roller_gate': 'an Auto roller gate',
        'iron_gate': 'an Iron gate',
        'wooden_gate': 'a Wooden gate',
        'sliding_gate': 'a Sliding gate',
        'swing_gate': 'a Swing gate',
        'no_gate': None
    }

    parts = []
    parts.append("The boundaries referred above are in accordance with those shown in plan and are well defined")

    boundary_types_per_dir = report.boundary_types_per_direction or {}
    physical_types = report.physical_boundaries_types or []

    if boundary_types_per_dir:
        type_to_directions: dict = {}
        directions_order = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']

        for direction in directions_order:
            b_type = boundary_types_per_dir.get(direction)
            if b_type:
                if b_type not in type_to_directions:
                    type_to_directions[b_type] = []
                type_to_directions[b_type].append(direction)

        boundary_descriptions = []
        for b_type, directions in type_to_directions.items():
            type_label = boundary_type_labels.get(b_type, b_type)
            dir_labels = [d for d in directions]

            if len(dir_labels) == 8:
                dir_text = "on all eight sides"
            elif len(dir_labels) == 4:
                main_dirs = {'north', 'south', 'east', 'west'}
                if set(dir_labels) == main_dirs:
                    dir_text = "on all four sides"
                else:
                    dir_text = "on the " + ", ".join(dir_labels[:-1]) + f" and {dir_labels[-1]}"
            elif len(dir_labels) == 1:
                dir_text = f"on the {dir_labels[0]}"
            else:
                dir_text = "on the " + ", ".join(dir_labels[:-1]) + f" and {dir_labels[-1]}"

            boundary_descriptions.append(f"demarcated by {type_label} {dir_text}")

        if boundary_descriptions:
            parts.append(" and " + ", ".join(boundary_descriptions))

    elif physical_types:
        type_labels = [boundary_type_labels.get(t, t) for t in physical_types[:3]]

        if 'rubble_foundation' in physical_types:
            main_types = [t for t in type_labels if 'rubble' not in t]
            if main_types:
                parts.append(f" and demarcated by {main_types[0]} constructed on rubble masonry foundation on the north, east, south and the west")
            else:
                parts.append(f" and demarcated by rubble masonry foundation on all sides")
        elif type_labels:
            parts.append(f" and demarcated by {', '.join(type_labels)}")

    parts.append(".")

    entrance_type = report.entrance_type
    if entrance_type and entrance_type != 'no_gate':
        entrance_label = entrance_labels.get(entrance_type)
        if entrance_label:
            parts.append(f" There is {entrance_label} entrance to the property.")

    result = "".join(parts)
    return result if result != "The boundaries referred above are in accordance with those shown in plan and are well defined." else None
