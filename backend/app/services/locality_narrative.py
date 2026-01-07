"""
AI-powered narrative generation service for locality descriptions in valuation reports.
Uses Claude API to generate professional, contextual locality descriptions.
"""
import os
from typing import Dict, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv
from ..docx_generator import format_list_with_grammar

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


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

    Args:
        All locality-related data fields

    Returns:
        Generated narrative text or None if generation fails
    """
    if not ANTHROPIC_API_KEY:
        print("[LOCALITY_NARRATIVE] Warning: ANTHROPIC_API_KEY not set")
        return None

    try:
        client = Anthropic(api_key=ANTHROPIC_API_KEY)

        # Build the context for AI
        context_parts = []

        # Location context
        if property_village:
            context_parts.append(f"Property Village: {property_village}")
        if divisional_secretariat:
            context_parts.append(f"Divisional Secretariat: {divisional_secretariat}")
        if pradeshiya_sabha:
            context_parts.append(f"Pradeshiya Sabha: {pradeshiya_sabha}")
        if property_district:
            context_parts.append(f"District: {property_district}")

        # Distance to major town
        if major_town_name and distance_to_major_town_km:
            context_parts.append(f"\nDistance to {major_town_name}: {distance_to_major_town_km} km")

        # Nearby facilities
        if nearby_facilities:
            facilities_text = format_facilities_list(nearby_facilities)
            context_parts.append(f"\nNearby Facilities:{facilities_text}")

        # Infrastructure
        infrastructure_items = []
        if has_electricity:
            infrastructure_items.append("main electricity")
        if water_supply_type:
            water_labels = {
                "Pipe-borne (NWSDB)": "pipe-borne water (NWSDB)",
                "Well": "well water",
                "Bore/Tube Well": "bore/tube well water",
                "Rainwater Harvesting": "rainwater harvesting",
                # Backward compatibility for old values
                "pipe_borne_water": "pipe-borne water",
                "bore_water": "bore water",
                "well_water": "well water"
            }
            # Handle both string (legacy) and array (new) formats
            if isinstance(water_supply_type, str):
                # Legacy single value
                infrastructure_items.append(water_labels.get(water_supply_type, water_supply_type))
            elif isinstance(water_supply_type, list):
                # New multi-select array
                mapped_values = [
                    water_labels.get(wtype, wtype.lower())
                    for wtype in water_supply_type
                ]
                infrastructure_items.append(format_list_with_grammar(mapped_values))
        if telecommunication_types:
            if "landline" in telecommunication_types:
                infrastructure_items.append("telephone services")
            if "mobile_coverage" in telecommunication_types:
                infrastructure_items.append("mobile coverage")
        if internet_types:
            if "fiber" in internet_types:
                infrastructure_items.append("fiber internet")
            elif "mobile_data" in internet_types:
                infrastructure_items.append("mobile internet")

        if infrastructure_items:
            context_parts.append(f"\nInfrastructure Available: {', '.join(infrastructure_items)}")

        # Public transport
        if has_public_transport:
            transport_parts = ["Public transport is available"]
            if public_transport_routes:
                transport_parts.append(f"Routes: {public_transport_routes}")
            if public_transport_frequency:
                transport_parts.append(f"Frequency: {public_transport_frequency}")
            context_parts.append(f"\nPublic Transport: {' | '.join(transport_parts)}")

        # Area characteristics
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

        if development_level:
            dev_labels = {
                "well_developed": "well-developed",
                "developing": "developing",
                "moderate": "moderately developed",
                "undeveloped": "undeveloped"
            }
            context_parts.append(f"Development Level: {dev_labels.get(development_level, development_level)}")

        if predominant_building_type:
            building_labels = {
                "Single Storey Residential": "single storey residential",
                "Multi Storey Residential": "multi storey residential",
                "Apartments": "apartments",
                "Commercial Buildings": "commercial buildings",
                "Mixed": "mixed-use buildings",
                # Backward compatibility
                "single_storey_residential": "single storey residential",
                "multi_storey_residential": "multi storey residential",
                "apartments": "apartments",
                "commercial_buildings": "commercial buildings",
                "mixed": "mixed-use buildings"
            }
            # Handle both string (legacy) and array (new) formats
            if isinstance(predominant_building_type, str):
                # Legacy single value
                context_parts.append(f"Predominant Buildings: {predominant_building_type}")
            elif isinstance(predominant_building_type, list):
                # New multi-select array
                mapped_buildings = [
                    building_labels.get(btype, btype.lower())
                    for btype in predominant_building_type
                ]
                formatted = format_list_with_grammar(mapped_buildings)
                context_parts.append(f"Predominant Buildings: {formatted}")

        # Tourism
        if is_tourist_area and tourist_attractions_nearby:
            context_parts.append(f"\nTourism: This is a tourist area. Nearby attractions: {tourist_attractions_nearby}")

        # Create the full context
        full_context = "\n".join(context_parts)

        # Construct the prompt
        prompt = f"""You are writing the LOCALITY section for a professional property valuation report in Sri Lanka.

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

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",  # Claude 3.5 Haiku (same as other services)
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the generated text
        if message.content and len(message.content) > 0:
            narrative = message.content[0].text.strip()
            print(f"[LOCALITY_NARRATIVE] Successfully generated narrative ({len(narrative)} chars)")
            return narrative
        else:
            print("[LOCALITY_NARRATIVE] No content in Claude response")
            return None

    except Exception as e:
        print(f"[LOCALITY_NARRATIVE] Error generating narrative: {str(e)}")
        return None
