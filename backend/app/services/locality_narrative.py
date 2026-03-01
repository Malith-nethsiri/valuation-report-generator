"""
AI-powered narrative generation service for locality descriptions in valuation reports.
Uses Claude API to generate professional, contextual locality descriptions.
"""
from typing import Dict, List, Optional, Any
from ..utils.text_helpers import format_list_with_grammar
from .anthropic_client import get_anthropic_client, is_anthropic_configured
from .base_narrative import BaseNarrativeService
from .narrative_constants import format_water_supply


def format_facilities_list(facilities: List[Dict]) -> str:
    """Format facilities data into a readable list for the AI prompt."""
    if not facilities:
        return "No specific facilities data provided."

    # Group facilities by type
    facilities_by_type = {}
    for facility in facilities:
        if not facility.get("selected", False):
            continue

        facility_type = facility.get("type", "other")
        if facility_type not in facilities_by_type:
            facilities_by_type[facility_type] = []

        facilities_by_type[facility_type].append(facility)

    # Format as text
    lines = []
    for facility_type, items in facilities_by_type.items():
        type_label = facility_type.replace("_", " ").title()
        lines.append(f"\n{type_label}:")
        for item in items:
            name = item.get("name", "Unknown")
            distance = item.get("distance_km", 0)
            lines.append(f"  - {name} ({distance} km)")

    return "\n".join(lines)


class LocalityNarrativeService(BaseNarrativeService):
    """
    Service for generating professional locality descriptions for Sri Lankan valuation reports.
    Extends BaseNarrativeService with locality-specific prompt engineering.
    """

    def get_service_name(self) -> str:
        return "LOCALITY_NARRATIVE"

    def get_max_tokens(self) -> int:
        return 1024

    def get_temperature(self) -> float:
        # Locality uses default (no explicit temperature in original)
        return 1.0

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build the locality narrative prompt from input data."""
        context_parts = []

        # Location context
        property_village = data.get('property_village')
        if property_village:
            context_parts.append(f"Property Village: {property_village}")

        divisional_secretariat = data.get('divisional_secretariat')
        if divisional_secretariat:
            context_parts.append(f"Divisional Secretariat: {divisional_secretariat}")

        pradeshiya_sabha = data.get('pradeshiya_sabha')
        if pradeshiya_sabha:
            context_parts.append(f"Pradeshiya Sabha: {pradeshiya_sabha}")

        property_district = data.get('property_district')
        if property_district:
            context_parts.append(f"District: {property_district}")

        # Distance to major town
        major_town_name = data.get('major_town_name')
        distance_to_major_town_km = data.get('distance_to_major_town_km')
        if major_town_name and distance_to_major_town_km:
            context_parts.append(f"\nDistance to {major_town_name}: {distance_to_major_town_km} km")

        # Nearby facilities
        nearby_facilities = data.get('nearby_facilities')
        if nearby_facilities:
            facilities_text = format_facilities_list(nearby_facilities)
            context_parts.append(f"\nNearby Facilities:{facilities_text}")

        # Infrastructure
        infrastructure_items = []
        if data.get('has_electricity'):
            infrastructure_items.append("main electricity")

        water_supply_type = data.get('water_supply_type')
        if water_supply_type:
            formatted = format_water_supply(water_supply_type)
            if formatted:
                infrastructure_items.append(formatted)

        telecommunication_types = data.get('telecommunication_types') or []
        if "landline" in telecommunication_types:
            infrastructure_items.append("telephone services")
        if "mobile_coverage" in telecommunication_types:
            infrastructure_items.append("mobile coverage")

        internet_types = data.get('internet_types') or []
        if "fiber" in internet_types:
            infrastructure_items.append("fiber internet")
        elif "mobile_data" in internet_types:
            infrastructure_items.append("mobile internet")

        if infrastructure_items:
            context_parts.append(f"\nInfrastructure Available: {', '.join(infrastructure_items)}")

        # Public transport
        if data.get('has_public_transport'):
            transport_parts = ["Public transport is available"]
            public_transport_routes = data.get('public_transport_routes')
            if public_transport_routes:
                transport_parts.append(f"Routes: {public_transport_routes}")
            public_transport_frequency = data.get('public_transport_frequency')
            if public_transport_frequency:
                transport_parts.append(f"Frequency: {public_transport_frequency}")
            context_parts.append(f"\nPublic Transport: {' | '.join(transport_parts)}")

        # Area characteristics
        area_type = data.get('area_type')
        if area_type:
            area_labels = {
                "residential": "residential",
                "commercial": "commercial",
                "industrial": "industrial",
                "mixed": "mixed residential and commercial",
                "agricultural": "agricultural",
                "tourist": "tourist"
            }
            context_parts.append(f"\nArea Type: {area_labels.get(area_type, area_type)}")

        development_level = data.get('development_level')
        if development_level:
            dev_labels = {
                "well_developed": "well-developed",
                "developing": "developing",
                "moderate": "moderately developed",
                "undeveloped": "undeveloped"
            }
            context_parts.append(f"Development Level: {dev_labels.get(development_level, development_level)}")

        predominant_building_type = data.get('predominant_building_type')
        if predominant_building_type:
            building_labels = {
                "Single Story Residential": "single story residential",
                "Multi Story Residential": "multi story residential",
                "Apartments": "apartments",
                "Commercial Buildings": "commercial buildings",
                "Mixed": "mixed-use buildings",
                "single_storey_residential": "single story residential",
                "multi_storey_residential": "multi story residential",
                "apartments": "apartments",
                "commercial_buildings": "commercial buildings",
                "mixed": "mixed-use buildings"
            }
            if isinstance(predominant_building_type, str):
                context_parts.append(f"Predominant Buildings: {predominant_building_type}")
            elif isinstance(predominant_building_type, list):
                mapped_buildings = [
                    building_labels.get(btype, btype.lower())
                    for btype in predominant_building_type
                ]
                formatted = format_list_with_grammar(mapped_buildings)
                context_parts.append(f"Predominant Buildings: {formatted}")

        # Tourism
        is_tourist_area = data.get('is_tourist_area')
        tourist_attractions_nearby = data.get('tourist_attractions_nearby')
        if is_tourist_area and tourist_attractions_nearby:
            context_parts.append(f"\nTourism: This is a tourist area. Nearby attractions: {tourist_attractions_nearby}")

        full_context = "\n".join(context_parts)

        return f"""You are writing the LOCALITY section for a professional property valuation report in Sri Lanka.

Based on the following data about the property location, write a SINGLE CONCISE PARAGRAPH that summarizes the locality information. The description must be factual, professional, and follow the formal style of Sri Lankan valuation reports.

Property Location Data:
{full_context}

CRITICAL INSTRUCTIONS:

Write ONE comprehensive paragraph that includes ALL of the following elements in a logical flow:

1. Location & Distance:
   - State the property's location (village, pradeshiya sabha/divisional secretariat, district)
   - Specify the EXACT distance to the nearest major town (use the km value provided)
   - Describe the area's character and development level concisely (e.g., "well-developed residential area", "commercial zone", "tourist area")

2. Nearby Facilities:
   - List 3-5 key facility NAMES with their distances in kilometers
   - Use format: "Nearby facilities include [Name1] at [X.X] km, [Name2] at [X.X] km, [Name3] at [X.X] km"
   - For tourist areas, use: "namely, [Resort1], [Resort2], [Resort3]"
   - End with: "and all important institutions are easily reachable" or similar

3. Infrastructure & Transport:
   - List infrastructure concisely: "Basic infrastructure such as electricity, [water type], and telecommunication services are available"
   - Mention public transport briefly: "Public transport operates along [route] with [frequency] frequency"

STYLE REQUIREMENTS:
- Professional, formal, and CONCISE language
- Write as ONE flowing paragraph, NOT bullet points
- Be specific with distances (use actual km values from data)
- Maximum length: 150-200 words (approximately 4-6 sentences)
- Prioritize factual information over descriptive details

EXAMPLE OF CONCISE PROFESSIONAL STYLE:
"The subject property is situated in [Village Name], [Divisional Secretariat], [District], located approximately [X.X] km from [Major Town]. The locality is a well-developed residential area with moderate population density. Nearby facilities include [Hospital Name] at [X.X] km, [Bank Name] at [X.X] km, [School Name] at [X.X] km, and all important institutions such as police stations, schools, and religious places are easily reachable. Basic infrastructure facilities such as main electricity, pipe-borne water, and telecommunication services are available in the area. Public transport services operate along [Route Name] with regular frequency, providing good connectivity to major towns."

Now generate the locality description as ONE concise paragraph using the provided data:"""


# Singleton instance for the service
_locality_narrative_service = LocalityNarrativeService()


async def generate_locality_narrative(
    property_village: Optional[str] = None,
    property_district: Optional[str] = None,
    divisional_secretariat: Optional[str] = None,
    pradeshiya_sabha: Optional[str] = None,
    distance_to_major_town_km: Optional[float] = None,
    major_town_name: Optional[str] = None,
    nearby_facilities: Optional[List[Dict]] = None,
    has_electricity: Optional[bool] = None,
    water_supply_type: Optional[str] = None,
    telecommunication_types: Optional[List[str]] = None,
    internet_types: Optional[List[str]] = None,
    has_public_transport: Optional[bool] = None,
    public_transport_routes: Optional[str] = None,
    public_transport_frequency: Optional[str] = None,
    area_type: Optional[str] = None,
    development_level: Optional[str] = None,
    predominant_building_type: Optional[str] = None,
    is_tourist_area: Optional[bool] = None,
    tourist_attractions_nearby: Optional[str] = None,
) -> Optional[str]:
    """
    Generate a professional locality description narrative using Claude AI.

    This function maintains backward compatibility while using the new BaseNarrativeService.
    """
    # Package parameters into data dict for the service
    data = {
        'property_village': property_village,
        'property_district': property_district,
        'divisional_secretariat': divisional_secretariat,
        'pradeshiya_sabha': pradeshiya_sabha,
        'distance_to_major_town_km': distance_to_major_town_km,
        'major_town_name': major_town_name,
        'nearby_facilities': nearby_facilities,
        'has_electricity': has_electricity,
        'water_supply_type': water_supply_type,
        'telecommunication_types': telecommunication_types,
        'internet_types': internet_types,
        'has_public_transport': has_public_transport,
        'public_transport_routes': public_transport_routes,
        'public_transport_frequency': public_transport_frequency,
        'area_type': area_type,
        'development_level': development_level,
        'predominant_building_type': predominant_building_type,
        'is_tourist_area': is_tourist_area,
        'tourist_attractions_nearby': tourist_attractions_nearby
    }

    return await _locality_narrative_service.generate(data)
