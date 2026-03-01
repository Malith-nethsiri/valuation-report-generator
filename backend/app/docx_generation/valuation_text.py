"""
Legal aspects and land valuation text generators.
"""
from typing import Any, List, Dict, Optional, Union
import logging

from .helpers import safe_get_json_field, safe_get_array_item

logger = logging.getLogger(__name__)
Deed_Type = Union[Dict[str, Any], Any]


# ===== LEGAL ASPECTS PARAGRAPH GENERATORS =====

def generate_ownership_paragraph(report: Any) -> str:
    """
    Generate professional ownership paragraph with graceful handling of missing data.
    """
    parts: list[str] = []

    deeds = safe_get_json_field(report, 'deeds', [])
    has_deed = bool(deeds)
    has_plan = bool(safe_get_json_field(report, 'plan_number', None))

    owner_name = safe_get_json_field(report, 'applicant_full_name', None)

    if not owner_name:
        owner_name = "[Applicant Name Not Provided]"

    if getattr(report, 'title_search_conducted', None) == 'No' or \
       getattr(report, 'pedigree_search_conducted', None) == 'No':
        parts.append("I did not search regarding the history and pedigree of the property.")

    if has_deed and owner_name:
        deed: Deed_Type = safe_get_array_item(deeds, 0, {})
        deed_type: str = deed.get('deed_type', 'transfer deed') if isinstance(deed, dict) else getattr(deed, 'deed_type', 'transfer deed')
        deed_number = deed.get('deed_number', '') if isinstance(deed, dict) else getattr(deed, 'deed_number', '')
        deed_date = deed.get('deed_date', '') if isinstance(deed, dict) else getattr(deed, 'deed_date', '')
        notary_name = deed.get('notary_name', '') if isinstance(deed, dict) else getattr(deed, 'notary_name', '')
        notary_location = deed.get('notary_location', '') if isinstance(deed, dict) else getattr(deed, 'notary_location', '')

        ownership_stmt = f"{owner_name} claims ownership to the property"

        if deed_number and deed_date:
            ownership_stmt += f" by {deed_type} No:{deed_number} dated {deed_date}"
        else:
            ownership_stmt += f" by {deed_type}"

        if notary_name and notary_location:
            ownership_stmt += f" attested by {notary_name} notary public in {notary_location} district"
        elif notary_name:
            ownership_stmt += f" attested by {notary_name} notary public"

        ownership_stmt += "."
        parts.append(ownership_stmt)

    elif has_plan and owner_name:
        plan_number = report.plan_number
        plan_date = getattr(report, 'plan_date', '')
        surveyor = getattr(report, 'licensed_surveyor_name', '')

        ownership_stmt = f"{owner_name} claims ownership to the property by transfer deed for the property identified as per the Survey Plan No: {plan_number}"

        if plan_date:
            ownership_stmt += f" dated {plan_date}"
        if surveyor:
            ownership_stmt += f" prepared by {surveyor}"

        ownership_stmt += "."
        parts.append(ownership_stmt)

    property_encumbered = getattr(report, 'property_encumbered', None)
    if property_encumbered == 'Yes':
        encumbrance_type = getattr(report, 'encumbrance_type', 'encumbrance')
        encumbrance_details = getattr(report, 'encumbrance_details', '')

        if encumbrance_type == 'Mortgage' and encumbrance_details:
            parts.append(f"This property is already mortgaged to {encumbrance_details}.")
        elif encumbrance_type == 'Life Interest' and encumbrance_details:
            parts.append(f"This property has a life interest held by {encumbrance_details}.")
        else:
            parts.append(f"This property has {encumbrance_type.lower()} encumbrance.")

    ownership_type = getattr(report, 'ownership_type', 'freehold')
    valuation_basis = getattr(report, 'valuation_basis_note', None)

    if not valuation_basis:
        if property_encumbered == 'Yes':
            valuation_basis = "free from all legal encumbrance"
        else:
            valuation_basis = "free from all encumbrances"

    valuation_stmt = f"I valued {ownership_type.lower()} interest of the property {valuation_basis}."
    parts.append(valuation_stmt)

    if not parts or len(parts) == 1:
        return f"I did not search regarding the history and pedigree of the property. Valuation is based on {ownership_type.lower()} title {valuation_basis}."

    return " ".join(parts)


def generate_street_lines_paragraph(report) -> str:
    """
    Generate street lines paragraph with contextual information.
    """
    status = getattr(report, 'street_lines_status', 'not affected')
    status_lower = status.lower()

    parts = []
    parts.append(f"Street lines are {status_lower} to the property.")

    impact_desc = getattr(report, 'street_lines_impact_description', None)
    if impact_desc:
        parts.append(impact_desc)

    is_municipal = getattr(report, 'is_municipal_limit', False)
    municipal_context = "within Municipal Council Limits" if is_municipal else "outside Municipal Council Limits"

    gazette_ref = getattr(report, 'street_lines_gazette_ref', None)
    gazette_date = getattr(report, 'street_lines_gazette_date', None)

    if gazette_ref and gazette_date:
        parts.append(f"Properties located {municipal_context} are subject to street line regulations as per Gazette No: {gazette_ref} dated {gazette_date}.")
    else:
        if status_lower == 'not affected':
            parts.append("Street lines are affected to the properties which are located along roads within Municipal Council Limits and imposed by a gazette.")
        else:
            parts.append(f"Properties located {municipal_context} are subject to street line regulations.")

    return " ".join(parts)


def generate_building_limits_paragraph(report) -> str:
    """
    Generate building limits paragraph with approval and distance information.
    """
    status = getattr(report, 'building_limits_status', 'not affected')
    status_lower = status.lower()

    parts = []
    parts.append(f"Building limits are {status_lower} to the property.")

    plan_approved = getattr(report, 'building_plan_approved', None)
    approval_authority = getattr(report, 'building_approval_authority', None)

    if plan_approved == 'Yes':
        if approval_authority:
            parts.append(f"Building Plan approved by {approval_authority}.")
        else:
            parts.append("Building Plan approved by the local authority.")

    distance = getattr(report, 'building_distance_from_road', None)
    if distance:
        parts.append(f"Building limit is {distance} from the access road.")

    within_limits = getattr(report, 'building_within_limits', None)
    if within_limits == 'Yes':
        parts.append("Existing building is located inside of the building limits in accordance with the approved building plan.")
    elif within_limits == 'No':
        parts.append("Existing building is located outside of the building limits.")

    plan_ref = getattr(report, 'building_plan_reference', None)
    if plan_ref and plan_approved == 'Yes':
        parts.append(f"Building plan reference: {plan_ref}.")

    return " ".join(parts)


def generate_local_authority_paragraph(report) -> str:
    """
    Generate local authority paragraph with rating and administrative information.
    """
    custom_text = getattr(report, 'local_authority_data', None)
    if custom_text and len(custom_text) > 50:
        return custom_text

    parts = []

    pradeshiya_sabha = getattr(report, 'pradeshiya_sabha', None)
    district = getattr(report, 'property_district', None)
    province = getattr(report, 'property_province', None)

    if pradeshiya_sabha or district or province:
        location_parts = []
        if pradeshiya_sabha:
            location_parts.append(pradeshiya_sabha)
        if district:
            location_parts.append(f"{district} District")
        if province:
            location_parts.append(f"{province} Province")
        parts.append(", ".join(location_parts) + ".")

    is_rated = getattr(report, 'local_authority_rated', None)

    if is_rated == 'Yes':
        parts.append("This area has been rated for the local levy of taxes.")
        tax_levy = getattr(report, 'local_authority_tax_levy', None)
        if tax_levy:
            parts.append(tax_levy)
        assessment_num = getattr(report, 'assessment_number', None)
        if assessment_num:
            parts.append(f"Assessment No: {assessment_num}.")
    elif is_rated == 'No':
        parts.append("This area has not been rated for the local levy of taxes.")

    if not parts and custom_text:
        return custom_text

    return " ".join(parts)


def generate_rent_act_paragraph(report) -> str:
    """
    Generate rent act effectiveness paragraph.
    """
    status = getattr(report, 'rent_act_effectiveness', 'Not affected')

    status_map = {
        'Not affected': "This property is not affected by the rent act.",
        'Subject to Rent Act No. 7 of 1972': "This property is subject to the rent act of No. 7 of 1972.",
        'Subject to Rent Act Amendment No. 26 of 2002': "This property is subject to the rent act of No. 7 of 1972 (Amendment No. 26 of 2002).",
        'Partially affected': "This property is partially affected by the rent control regulations."
    }

    return status_map.get(status, "This property is not affected by the rent act.")


# ===== LAND VALUES PARAGRAPH GENERATORS =====

def _synthesize_location_context(locations: List[str]) -> str:
    """
    Synthesize location context from comparable location descriptions.
    """
    if not locations:
        return "in this area"

    valid_locations = [loc.strip() for loc in locations if loc and loc.strip()]

    if not valid_locations:
        return "in this area"

    if len(valid_locations) == 1:
        return f"located in {valid_locations[0]}"

    from collections import Counter

    all_words = []
    for loc in valid_locations:
        words = loc.lower().replace(',', '').split()
        all_words.extend(words)

    word_counts = Counter(all_words)
    stop_words = {'in', 'the', 'a', 'an', 'of', 'to', 'and', 'or', 'near', 'at', 'from', 'this', 'that'}
    significant_words = {word: count for word, count in word_counts.items()
                         if count >= len(valid_locations) * 0.5 and word not in stop_words}

    if significant_words:
        common_area = max(significant_words, key=significant_words.get)
        return f"located in {common_area.title()} area"

    combined = " ".join(valid_locations).lower()
    if 'highway' in combined:
        for loc in valid_locations:
            if 'highway' in loc.lower():
                words = loc.split()
                for i, word in enumerate(words):
                    if 'highway' in word.lower() and i > 0:
                        return f"located fronting {' '.join(words[max(0,i-2):i+1])}"
                return "located fronting main highway"

    if 'road' in combined:
        for loc in valid_locations:
            if 'road' in loc.lower() and '-' in loc:
                return f"located fronting {loc}"
        return "located with road access in this area"

    return "located in this village"


def generate_land_values_paragraph(comparables: List[dict]) -> str:
    """
    Generate professional land values paragraph from comparable properties data.
    """
    if not comparables:
        return ""

    valid_comparables = [
        c for c in comparables
        if c.get('extent', 0) > 0 and c.get('rate_per_perch', 0) > 0
    ]

    if not valid_comparables:
        return ""

    if len(valid_comparables) == 1:
        comp = valid_comparables[0]
        prop_type = comp.get('property_type', 'Residential')

        type_descriptors = {
            'Residential': 'Residential building blocks',
            'Commercial': 'Commercial building blocks',
            'Agricultural': 'Agricultural land parcels'
        }
        property_descriptor = type_descriptors.get(prop_type, 'Building blocks')

        location = comp.get('location_description', 'this area')
        extent = comp.get('extent', 0)
        rate = comp.get('rate_per_perch', 0)

        return (
            f"{property_descriptor} of about {extent:.0f} Perches "
            f"in {location} is valued at approximately Rs.{rate:,.0f}/= Per Perch."
        )

    property_groups: Dict[str, list] = {}
    for comp in valid_comparables:
        prop_type = comp.get('property_type', 'Residential')
        if prop_type not in property_groups:
            property_groups[prop_type] = []
        property_groups[prop_type].append(comp)

    type_order = ['Residential', 'Commercial', 'Agricultural']
    paragraphs = []

    for prop_type in type_order:
        if prop_type not in property_groups:
            continue

        group = property_groups[prop_type]

        extents = [c['extent'] for c in group]
        rates = [c['rate_per_perch'] for c in group]

        min_extent = min(extents)
        max_extent = max(extents)
        min_rate = min(rates)
        max_rate = max(rates)

        if min_extent == max_extent:
            extent_str = f"about {min_extent:.0f} Perches"
        else:
            extent_str = f"about {min_extent:.0f} – {max_extent:.0f} Perches"

        def format_rate(rate):
            return f"Rs.{rate:,.0f}/="

        if min_rate == max_rate:
            rate_str = f"{format_rate(min_rate)} Per Perch"
        else:
            rate_str = f"{format_rate(min_rate)} to {format_rate(max_rate)} Per Perch"

        locations = [c.get('location_description', '') for c in group]
        location_context = _synthesize_location_context(locations)

        type_descriptors = {
            'Residential': 'Residential building blocks',
            'Commercial': 'Commercial building blocks',
            'Agricultural': 'Agricultural land parcels'
        }
        property_descriptor = type_descriptors.get(prop_type, 'Building blocks')

        rate_variance = ((max_rate - min_rate) / min_rate * 100) if min_rate > 0 else 0

        if rate_variance < 20:
            context_phrase = "showing stable market conditions"
        elif rate_variance > 50:
            context_phrase = "depending upon the location, topography and nature of the property and convenience etc."
        else:
            context_phrase = "to be influenced by factors affecting the property market"

        paragraph = (
            f"{property_descriptor} in extent {extent_str} {location_context} "
            f"are being sold at rates ranging from {rate_str}, {context_phrase}."
        )

        paragraphs.append(paragraph)

    return " ".join(paragraphs)
