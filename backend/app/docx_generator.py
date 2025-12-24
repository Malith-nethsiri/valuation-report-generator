from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement, parse_xml
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Optional, Any
from decimal import Decimal
import requests
import json
import logging
from . import models
from .utils import append_label_if_missing, clean_spelling_errors, format_no_field
from .letterhead_templates import get_template

# Setup logging
logger = logging.getLogger(__name__)

# ===== NUMERIC TYPE CONVERTER =====
def to_float(value: Any) -> float:
    """
    Safely convert any numeric type (Decimal, int, float, str) to float.
    Handles None and returns 0.0.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    return float(value if value else 0)

# ===== DEFENSIVE DATA ACCESS HELPERS =====
# These functions prevent crashes from None/missing data in report generation

def safe_get_json_field(obj: Any, field_name: str, default: Any = None) -> Any:
    """
    Safely get JSON field from model object with None check.

    Args:
        obj: SQLAlchemy model object
        field_name: Name of the field to retrieve
        default: Default value if field is None or doesn't exist

    Returns:
        Field value or default
    """
    try:
        value = getattr(obj, field_name, default)
        return value if value is not None else default
    except Exception as e:
        logger.warning(f"Error accessing field '{field_name}': {e}")
        return default


def safe_get_array_item(arr: Any, index: int, default: Any = None) -> Any:
    """
    Safely get array item with bounds checking.

    Args:
        arr: Array/list to access
        index: Index to retrieve
        default: Default value if index out of bounds or arr is None

    Returns:
        Array item or default
    """
    if not arr or not isinstance(arr, (list, tuple)):
        return default
    if 0 <= index < len(arr):
        item = arr[index]
        return item if item is not None else default
    return default


def safe_parse_json_string(json_str: Any, default: Any = None) -> Any:
    """
    Safely parse JSON string with error handling.

    Args:
        json_str: JSON string or already-parsed object
        default: Default value if parsing fails

    Returns:
        Parsed JSON or default
    """
    if not json_str:
        return default
    try:
        return json.loads(json_str) if isinstance(json_str, str) else json_str
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"JSON parse error: {e}")
        return default


def safe_get_nested(obj: Any, *keys, default: Any = None) -> Any:
    """
    Safely traverse nested dict/object structure.

    Args:
        obj: Object to traverse
        *keys: Keys to traverse (can be dict keys or object attributes)
        default: Default value if any key is missing or None

    Returns:
        Nested value or default

    Example:
        safe_get_nested(report, 'boundaries', 'north', 'description', default='')
    """
    current = obj
    for key in keys:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(key)
        else:
            current = getattr(current, key, None)
        if current is None:
            return default
    return current

# ===== IMAGE CONFIGURATION CONSTANTS =====
# All measurements in inches
MAP_IMAGE_WIDTH = 3.5           # Google Maps image width (75% of original 4.5")
MAP_IMAGE_MAX_HEIGHT = 2.75     # Google Maps maximum height
PROPERTY_PHOTO_WIDTH = 2.0      # Property photo width (uniform sizing)
PROPERTY_PHOTO_HEIGHT = 2.0     # Property photo height (uniform sizing - square)
IMAGE_SPACING_BEFORE = Pt(6)    # Standard spacing before images
IMAGE_SPACING_AFTER = Pt(6)     # Standard spacing after images

# ===== SPACING CONFIGURATION FOR A4 PRINTING =====
# Professional spacing optimized for A4 hardcopy printing
# All measurements in points (pt)

# Major section spacing (1.0, 2.0, 3.0, etc.)
MAJOR_SECTION_SPACE_BEFORE = Pt(10)      # Reduced from 12pt for tighter layout
MAJOR_SECTION_SPACE_AFTER = Pt(3)        # Reduced from 4-6pt for consistency

# Subsection spacing (4.1, 4.2, etc.)
SUBSECTION_SPACE_BEFORE = Pt(8)          # Reduced from 12pt
SUBSECTION_SPACE_AFTER = Pt(3)           # Consistent with major sections

# Body paragraph spacing
BODY_PARA_SPACE_BEFORE = Pt(0)           # No change (tight by default)
BODY_PARA_SPACE_AFTER = Pt(3)            # Reduced from 4-6pt for consistency

# Inline field spacing (for "heading: content" format)
INLINE_FIELD_SPACE_BEFORE = Pt(3)        # Compact spacing for inline fields
INLINE_FIELD_SPACE_AFTER = Pt(3)         # Compact spacing for inline fields

# Subheading spacing (bold labels within sections like "Accommodation")
SUBHEADING_SPACE_BEFORE = Pt(4)          # Moderate spacing before subheadings
SUBHEADING_SPACE_AFTER = Pt(2)           # Minimal spacing after subheadings

# Indented content spacing
INDENTED_CONTENT_SPACE_BEFORE = Pt(0)    # No spacing before indented content
INDENTED_CONTENT_SPACE_AFTER = Pt(2)     # Minimal spacing after indented content
INDENTED_CONTENT_LEFT_INDENT = Inches(0.4)  # Standard indent for lists

# Special spacing
BOUNDARY_LIST_SPACE_AFTER = Pt(2)        # Spacing after boundary list items
ACCOMMODATION_ROOM_SPACE_AFTER = Pt(2)   # Spacing after room details
OPENING_SECTION_SPACE_AFTER = Pt(3)      # Spacing after opening sections

def add_border_to_paragraph(paragraph, border_position="bottom", size=12, color="000000"):
    """Add a border to a paragraph"""
    p = paragraph._element
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')

    border = OxmlElement(f'w:{border_position}')
    border.set(qn('w:val'), 'single')
    border.set(qn('w:sz'), str(size))
    border.set(qn('w:space'), '1')
    border.set(qn('w:color'), color)

    pBdr.append(border)
    pPr.append(pBdr)

def calculate_image_dimensions(image_stream, max_width: float, max_height: float):
    """
    Calculate image dimensions maintaining aspect ratio within constraints.

    Args:
        image_stream: BytesIO object containing image data
        max_width: Maximum width in inches
        max_height: Maximum height in inches

    Returns:
        dict with 'width' and 'height' in Inches, or None if only one dimension needed
    """
    try:
        from PIL import Image

        # Get current position and reset after reading
        current_pos = image_stream.tell()
        image_stream.seek(0)

        # Open image to get dimensions
        img = Image.open(image_stream)
        img_width, img_height = img.size

        # Reset stream position
        image_stream.seek(current_pos)

        # Calculate aspect ratio
        aspect_ratio = img_width / img_height

        # Calculate dimensions that fit within max constraints
        # Try fitting by width first
        fitted_width = max_width
        fitted_height = fitted_width / aspect_ratio

        # If height exceeds max, fit by height instead
        if fitted_height > max_height:
            fitted_height = max_height
            fitted_width = fitted_height * aspect_ratio

        return {
            'width': Inches(fitted_width),
            'height': Inches(fitted_height)
        }
    except Exception as e:
        print(f"[DOCX] Could not calculate image dimensions: {e}")
        # Fallback to just width constraint
        return {'width': Inches(max_width)}


def apply_letterbox_to_image(image_stream, target_width: float, target_height: float):
    """
    Apply letterbox/pillarbox to image to achieve uniform dimensions.
    Maintains aspect ratio by adding borders to fill the target size.

    Args:
        image_stream: BytesIO object containing image data
        target_width: Target width in inches
        target_height: Target height in inches

    Returns:
        BytesIO with letterboxed image, or original stream if processing fails
    """
    try:
        from PIL import Image, ImageOps

        # Save current position
        current_pos = image_stream.tell()
        image_stream.seek(0)

        # Open image
        img = Image.open(image_stream)

        # Convert to RGB if necessary (handles RGBA, P, etc.)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Calculate target size in pixels (assuming 96 DPI)
        DPI = 96
        target_width_px = int(target_width * DPI)
        target_height_px = int(target_height * DPI)

        # Calculate aspect ratios
        img_aspect = img.width / img.height
        target_aspect = target_width_px / target_height_px

        # Determine scaling: fit within target dimensions
        if img_aspect > target_aspect:
            # Image is wider - scale by width
            new_width = target_width_px
            new_height = int(target_width_px / img_aspect)
        else:
            # Image is taller - scale by height
            new_height = target_height_px
            new_width = int(target_height_px * img_aspect)

        # Resize image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Add padding to reach exact target dimensions
        # Calculate padding
        pad_width = (target_width_px - new_width) // 2
        pad_height = (target_height_px - new_height) // 2

        # Create new image with white background
        letterboxed = Image.new('RGB', (target_width_px, target_height_px), (255, 255, 255))
        letterboxed.paste(img_resized, (pad_width, pad_height))

        # Save to BytesIO
        output_stream = BytesIO()
        letterboxed.save(output_stream, format='JPEG', quality=90)
        output_stream.seek(0)

        print(f"[DOCX] Letterboxed image to {target_width}x{target_height} inches")
        return output_stream

    except Exception as e:
        print(f"[DOCX] Error applying letterbox: {e}")
        # Return original stream on error
        image_stream.seek(current_pos)
        return image_stream


def add_section_heading(doc, section_number: str, section_title: str):
    """
    Add a hierarchically numbered section heading.

    Args:
        doc: Document object
        section_number: Section number (e.g., "1.0", "4.7.1")
        section_title: Section title text (e.g., "SITUATION", "PHOTOGRAPHS")

    Returns:
        Paragraph object containing the heading
    """
    # Determine if this is a major section (X.0) or subsection (X.Y)
    is_subsection = '.' in section_number and section_number.count('.') >= 1 and not section_number.endswith('.0')

    # Add spacing before section
    spacing_para = doc.add_paragraph()
    if is_subsection:
        spacing_para.paragraph_format.space_before = SUBSECTION_SPACE_BEFORE
    else:
        spacing_para.paragraph_format.space_before = MAJOR_SECTION_SPACE_BEFORE
    spacing_para.paragraph_format.space_after = Pt(0)

    # Create heading paragraph
    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
    heading.paragraph_format.space_before = Pt(0)
    if is_subsection:
        heading.paragraph_format.space_after = SUBSECTION_SPACE_AFTER
    else:
        heading.paragraph_format.space_after = MAJOR_SECTION_SPACE_AFTER
    heading.paragraph_format.line_spacing = 0.9

    # Add section number and title
    heading_text = f"{section_number}. {section_title}"
    heading_run = heading.add_run(heading_text)
    heading_run.bold = True
    heading_run.font.size = Pt(10)
    heading_run.font.color.rgb = RGBColor(0, 0, 0)

    return heading


def format_material_list(materials: List[str], labels_dict: Dict[str, str]) -> str:
    """
    Format a list of materials intelligently with proper grammar (Oxford comma).

    Args:
        materials: List of material keys (e.g., ['asbestos', 'tile', 'metal'])
        labels_dict: Dictionary mapping keys to display labels

    Returns:
        Formatted string with proper grammar

    Examples:
        - 1 item: "asbestos sheets"
        - 2 items: "asbestos sheets and tiles"
        - 3+ items: "asbestos sheets, tiles and metal sheets" (Oxford comma)
    """
    if not materials:
        return ""

    # Get display labels for all materials
    labeled_materials = [labels_dict.get(m, m) for m in materials]

    if len(labeled_materials) == 1:
        return labeled_materials[0]
    elif len(labeled_materials) == 2:
        return f"{labeled_materials[0]} and {labeled_materials[1]}"
    else:
        # Oxford comma format: "A, B, C and D"
        return ", ".join(labeled_materials[:-1]) + f" and {labeled_materials[-1]}"


def format_currency(value: float) -> str:
    """
    Format currency with thousand separators and 2 decimal places.

    Args:
        value: Numeric value to format

    Returns:
        Formatted string like "Rs. 10,000,000.00"
    """
    if value is None:
        return "N/A"
    return f"Rs. {value:,.2f}"


def round_for_say(value: float) -> float:
    """
    Round value for 'Say' convention in professional valuations.

    Professional valuations often round the final value to a reasonable amount:
    - 10M+: Round to nearest 100K
    - 1M - 10M: Round to nearest 50K
    - 100K - 1M: Round to nearest 10K
    - Below 100K: Round to nearest 1K

    Args:
        value: Value to round

    Returns:
        Rounded value
    """
    if value >= 10_000_000:  # 10M+
        return round(value / 100_000) * 100_000  # Round to nearest 100K
    elif value >= 1_000_000:  # 1M - 10M
        return round(value / 50_000) * 50_000  # Round to nearest 50K
    elif value >= 100_000:  # 100K - 1M
        return round(value / 10_000) * 10_000  # Round to nearest 10K
    else:
        return round(value / 1_000) * 1_000  # Round to nearest 1K


def add_inline_field(doc, label: str, content: str,
                    space_before=None, space_after=None) -> None:
    """
    Add a single-line field in format "Label: content" (inline format).

    Args:
        doc: Document object
        label: Bold label text (e.g., "Floor area")
        content: Content text (e.g., "1250 square feet approximately.")
        space_before: Override default spacing before (optional)
        space_after: Override default spacing after (optional)

    Example output:
        "Floor area: 1250 square feet approximately."
        (where "Floor area:" is bold and rest is regular)
    """
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    para.paragraph_format.space_before = space_before if space_before is not None else INLINE_FIELD_SPACE_BEFORE
    para.paragraph_format.space_after = space_after if space_after is not None else INLINE_FIELD_SPACE_AFTER
    para.paragraph_format.line_spacing = 0.9

    # Add bold label
    label_run = para.add_run(f"{label}: ")
    label_run.bold = True
    label_run.font.size = Pt(9)
    label_run.font.color.rgb = RGBColor(0, 0, 0)

    # Add regular content
    content_run = para.add_run(content)
    content_run.font.size = Pt(9)
    content_run.font.color.rgb = RGBColor(0, 0, 0)


def add_subsection_paragraph(doc, label: str, heading: str, content: str,
                             space_before=None, space_after=None) -> None:
    """
    Add a paragraph with subsection label for narrative content.

    Args:
        doc: Document object
        label: Subsection label (e.g., "(a)", "(b)")
        heading: Section heading (e.g., "Ownership", "Street lines")
        content: Paragraph content text
        space_before: Override default spacing before (optional)
        space_after: Override default spacing after (optional)

    Example output:
        "(a). Ownership:
        Mr. D Indika Harshana Perera claims ownership to the property..."
    """
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    para.paragraph_format.space_before = space_before if space_before is not None else INLINE_FIELD_SPACE_BEFORE
    para.paragraph_format.space_after = space_after if space_after is not None else INLINE_FIELD_SPACE_AFTER
    para.paragraph_format.line_spacing = 0.9

    # Add bold label and heading
    label_run = para.add_run(f"{label}. {heading}:\n")
    label_run.bold = True
    label_run.font.size = Pt(9)
    label_run.font.color.rgb = RGBColor(0, 0, 0)

    # Add paragraph content
    content_run = para.add_run(content)
    content_run.font.size = Pt(9)
    content_run.font.color.rgb = RGBColor(0, 0, 0)


# ===== LEGAL ASPECTS PARAGRAPH GENERATORS =====

def generate_ownership_paragraph(report) -> str:
    """
    Generate professional ownership paragraph with graceful handling of missing data.

    Template adapts based on available data:
    - Full deed info: Complete ownership statement with deed details
    - Survey plan only: Ownership based on plan identification
    - Minimal data: Fallback to valuation basis statement
    """
    parts = []

    # Determine property identification method - USE SAFE HELPERS
    deeds = safe_get_json_field(report, 'deeds', [])
    has_deed = isinstance(deeds, list) and len(deeds) > 0
    has_plan = bool(safe_get_json_field(report, 'plan_number', None))

    # Owner name (use applicant if available) - USE SAFE HELPER
    owner_name = safe_get_json_field(report, 'applicant_full_name', None)

    # Fallback to placeholder if no owner name
    if not owner_name:
        owner_name = "[Applicant Name Not Provided]"

    # Title/pedigree search statement
    if getattr(report, 'title_search_conducted', None) == 'No' or \
       getattr(report, 'pedigree_search_conducted', None) == 'No':
        parts.append("I did not search regarding the history and pedigree of the property.")

    # Main ownership statement
    if has_deed and owner_name:
        # Deed-based ownership - USE SAFE ARRAY ACCESS
        deed = safe_get_array_item(deeds, 0, {})
        # Handle both dict and object formats
        deed_type = deed.get('deed_type', 'transfer deed') if isinstance(deed, dict) else getattr(deed, 'deed_type', 'transfer deed')
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
        # Plan-based ownership
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

    # Encumbrance statement
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

    # Valuation basis statement
    ownership_type = getattr(report, 'ownership_type', 'freehold')
    valuation_basis = getattr(report, 'valuation_basis_note', None)

    if not valuation_basis:
        if property_encumbered == 'Yes':
            valuation_basis = "free from all legal encumbrance"
        else:
            valuation_basis = "free from all encumbrances"

    valuation_stmt = f"I valued {ownership_type.lower()} interest of the property {valuation_basis}."
    parts.append(valuation_stmt)

    # Fallback for minimal data
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

    # Main status statement
    parts.append(f"Street lines are {status_lower} to the property.")

    # Impact description if provided
    impact_desc = getattr(report, 'street_lines_impact_description', None)
    if impact_desc:
        parts.append(impact_desc)

    # Municipal context
    is_municipal = getattr(report, 'is_municipal_limit', False)
    municipal_context = "within Municipal Council Limits" if is_municipal else "outside Municipal Council Limits"

    # Gazette reference if available
    gazette_ref = getattr(report, 'street_lines_gazette_ref', None)
    gazette_date = getattr(report, 'street_lines_gazette_date', None)

    if gazette_ref and gazette_date:
        parts.append(f"Properties located {municipal_context} are subject to street line regulations as per Gazette No: {gazette_ref} dated {gazette_date}.")
    else:
        # Generic explanatory statement
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

    # Main status statement
    parts.append(f"Building limits are {status_lower} to the property.")

    # Building plan approval
    plan_approved = getattr(report, 'building_plan_approved', None)
    approval_authority = getattr(report, 'building_approval_authority', None)

    if plan_approved == 'Yes':
        if approval_authority:
            parts.append(f"Building Plan approved by {approval_authority}.")
        else:
            parts.append("Building Plan approved by the local authority.")

    # Distance from road
    distance = getattr(report, 'building_distance_from_road', None)
    if distance:
        parts.append(f"Building limit is {distance} from the access road.")

    # Building within limits
    within_limits = getattr(report, 'building_within_limits', None)
    if within_limits == 'Yes':
        parts.append("Existing building is located inside of the building limits in accordance with the approved building plan.")
    elif within_limits == 'No':
        parts.append("Existing building is located outside of the building limits.")

    # Plan reference
    plan_ref = getattr(report, 'building_plan_reference', None)
    if plan_ref and plan_approved == 'Yes':
        parts.append(f"Building plan reference: {plan_ref}.")

    return " ".join(parts)


def generate_local_authority_paragraph(report) -> str:
    """
    Generate local authority paragraph with rating and administrative information.
    """
    # Check if user provided custom free-text (backward compatibility)
    custom_text = getattr(report, 'local_authority_data', None)
    if custom_text and len(custom_text) > 50:  # User wrote a full paragraph
        return custom_text

    parts = []

    # Administrative location
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

    # Rating status
    is_rated = getattr(report, 'local_authority_rated', None)

    if is_rated == 'Yes':
        parts.append("This area has been rated for the local levy of taxes.")

        # Tax levy details
        tax_levy = getattr(report, 'local_authority_tax_levy', None)
        if tax_levy:
            parts.append(tax_levy)

        # Assessment number
        assessment_num = getattr(report, 'assessment_number', None)
        if assessment_num:
            parts.append(f"Assessment No: {assessment_num}.")
    elif is_rated == 'No':
        parts.append("This area has not been rated for the local levy of taxes.")

    # Fallback to custom text if no structured data
    if not parts and custom_text:
        return custom_text

    return " ".join(parts)


def generate_rent_act_paragraph(report) -> str:
    """
    Generate rent act effectiveness paragraph.
    """
    status = getattr(report, 'rent_act_effectiveness', 'Not affected')

    # Direct mapping from dropdown options
    status_map = {
        'Not affected': "This property is not affected by the rent act.",
        'Subject to Rent Act No. 7 of 1972': "This property is subject to the rent act of No. 7 of 1972.",
        'Subject to Rent Act Amendment No. 26 of 2002': "This property is subject to the rent act of No. 7 of 1972 (Amendment No. 26 of 2002).",
        'Partially affected': "This property is partially affected by the rent control regulations."
    }

    return status_map.get(status, "This property is not affected by the rent act.")


# ===== NARRATIVE GENERATION HELPER FUNCTIONS =====

def _synthesize_location_context(locations: List[str]) -> str:
    """
    Synthesize location context from comparable location descriptions.

    Extracts common patterns and generates appropriate location phrase
    for land values narrative.

    Args:
        locations: List of location descriptions from comparable properties

    Returns:
        Synthesized location context string (e.g., "located in this area",
        "located fronting main highway", "located in Rambukkana area")

    Examples:
        >>> _synthesize_location_context([])
        'in this area'
        >>> _synthesize_location_context(['Rambukkana town', 'Rambukkana center'])
        'located in Rambukkana area'
        >>> _synthesize_location_context(['Fronting Kurunegala Highway'])
        'located fronting Kurunegala Highway'
    """
    if not locations:
        return "in this area"

    # Filter out empty locations
    valid_locations = [loc.strip() for loc in locations if loc and loc.strip()]

    if not valid_locations:
        return "in this area"

    # If single location
    if len(valid_locations) == 1:
        return f"located in {valid_locations[0]}"

    # Find common words (case-insensitive)
    from collections import Counter

    # Tokenize all locations
    all_words = []
    for loc in valid_locations:
        # Extract significant words (ignore common words)
        words = loc.lower().replace(',', '').split()
        all_words.extend(words)

    # Find most common significant words
    word_counts = Counter(all_words)

    # Common stop words to ignore
    stop_words = {'in', 'the', 'a', 'an', 'of', 'to', 'and', 'or', 'near', 'at', 'from', 'this', 'that'}
    significant_words = {word: count for word, count in word_counts.items()
                         if count >= len(valid_locations) * 0.5 and word not in stop_words}

    if significant_words:
        # Use most common word as area reference
        common_area = max(significant_words, key=significant_words.get)
        return f"located in {common_area.title()} area"

    # Check for highway/road frontage mentions
    combined = " ".join(valid_locations).lower()
    if 'highway' in combined:
        # Try to extract highway name if possible
        for loc in valid_locations:
            if 'highway' in loc.lower():
                # Try to extract highway name
                words = loc.split()
                for i, word in enumerate(words):
                    if 'highway' in word.lower() and i > 0:
                        return f"located fronting {' '.join(words[max(0,i-2):i+1])}"
                return "located fronting main highway"

    if 'road' in combined:
        # Check if specific road name is mentioned
        for loc in valid_locations:
            if 'road' in loc.lower() and '-' in loc:
                # Might be like "Kurunegala-Puttalam road"
                return f"located fronting {loc}"
        return "located with road access in this area"

    # Generic fallback
    return "located in this village"


def generate_land_values_paragraph(comparables: List[dict]) -> str:
    """
    Generate professional land values paragraph from comparable properties data.

    Groups comparables by property type and generates narrative description
    following Sri Lankan valuation report conventions.

    Args:
        comparables: List of comparable property dictionaries with keys:
            - property_type: 'Commercial' | 'Residential' | 'Agricultural'
            - location_description: str
            - extent: float (perches)
            - rate_per_perch: float (LKR)

    Returns:
        Formatted paragraph(s) describing land values in natural language.
        Returns empty string if no valid comparables.

    Examples:
        >>> comps = [
        ...     {'property_type': 'Residential', 'extent': 15, 'rate_per_perch': 50000,
        ...      'location_description': 'Rambukkana town'},
        ...     {'property_type': 'Residential', 'extent': 20, 'rate_per_perch': 60000,
        ...      'location_description': 'Rambukkana center'}
        ... ]
        >>> generate_land_values_paragraph(comps)
        'Residential building blocks in extent about 15 – 20 Perches located in Rambukkana area
         are being sold at rates ranging from Rs.50,000/= to Rs.60,000/= Per Perch...'
    """
    # Edge case: Empty or None
    if not comparables:
        return ""

    # Filter out invalid comparables (zero values)
    valid_comparables = [
        c for c in comparables
        if c.get('extent', 0) > 0 and c.get('rate_per_perch', 0) > 0
    ]

    if not valid_comparables:
        return "Insufficient comparable property data available for market analysis."

    # Handle single comparable specially
    if len(valid_comparables) == 1:
        comp = valid_comparables[0]
        prop_type = comp.get('property_type', 'Residential')

        # Property type descriptors
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

    # Group by property type
    property_groups = {}
    for comp in valid_comparables:
        prop_type = comp.get('property_type', 'Residential')
        if prop_type not in property_groups:
            property_groups[prop_type] = []
        property_groups[prop_type].append(comp)

    # Property type ordering
    type_order = ['Residential', 'Commercial', 'Agricultural']

    paragraphs = []

    for prop_type in type_order:
        if prop_type not in property_groups:
            continue

        group = property_groups[prop_type]

        # Calculate ranges
        extents = [c['extent'] for c in group]
        rates = [c['rate_per_perch'] for c in group]

        min_extent = min(extents)
        max_extent = max(extents)
        min_rate = min(rates)
        max_rate = max(rates)

        # Format extent range
        if min_extent == max_extent:
            extent_str = f"about {min_extent:.0f} Perches"
        else:
            extent_str = f"about {min_extent:.0f} – {max_extent:.0f} Perches"

        # Format rate range with proper currency formatting
        def format_rate(rate):
            # Format with thousands separator and /= suffix
            return f"Rs.{rate:,.0f}/="

        if min_rate == max_rate:
            rate_str = f"{format_rate(min_rate)} Per Perch"
        else:
            rate_str = f"{format_rate(min_rate)} to {format_rate(max_rate)} Per Perch"

        # Extract location context
        locations = [c.get('location_description', '') for c in group]
        location_context = _synthesize_location_context(locations)

        # Determine property type descriptor
        type_descriptors = {
            'Residential': 'Residential building blocks',
            'Commercial': 'Commercial building blocks',
            'Agricultural': 'Agricultural land parcels'
        }
        property_descriptor = type_descriptors.get(prop_type, 'Building blocks')

        # Calculate rate variance for contextual phrase
        rate_variance = ((max_rate - min_rate) / min_rate * 100) if min_rate > 0 else 0

        if rate_variance < 20:
            context_phrase = "showing stable market conditions"
        elif rate_variance > 50:
            context_phrase = "depending upon the location, topography and nature of the property and convenience etc."
        else:
            context_phrase = "to be influenced by factors affecting the property market"

        # Construct paragraph
        paragraph = (
            f"{property_descriptor} in extent {extent_str} {location_context} "
            f"are being sold at rates ranging from {rate_str}, {context_phrase}."
        )

        paragraphs.append(paragraph)

    return " ".join(paragraphs)


def get_pronoun(title: Optional[str], ownership_text: Optional[str] = None) -> Dict[str, str]:
    """
    Determine pronouns based on title.
    Returns: {'subject': 'he'/'she', 'object': 'him'/'her', 'possessive': 'his'/'her'}
    """
    if not title:
        return {'subject': 'he', 'object': 'him', 'possessive': 'his'}

    title_lower = title.lower().strip()

    # Female titles
    if title_lower in ['mrs.', 'mrs', 'miss.', 'miss', 'ms.', 'ms']:
        return {'subject': 'she', 'object': 'her', 'possessive': 'her'}

    # Default to male
    return {'subject': 'he', 'object': 'him', 'possessive': 'his'}

def generate_title_block(report: models.Report) -> str:
    """Generate the title block with support for plan/deed/certificate identification types"""
    lines = []
    lines.append("VALUATION REPORT")
    lines.append("of")

    # Determine identification type (with backward compatibility for old reports)
    id_type = report.property_identification_type
    if not id_type:
        # Infer type from existing data for old reports
        if report.plan_number:
            id_type = "plan"
        elif report.deeds:
            # Old reports with deed data
            id_type = "deed"
        else:
            # Fallback to plan-style if nothing is detected
            id_type = "plan"

    # Generate title based on identification type
    if id_type == "plan":
        # Plan-based title (original format)
        lot_desc = report.property_lot_description or '[Lot Description]'
        plan_num = report.plan_number or '[Plan Number]'
        plan_formatted = format_no_field("Plan", plan_num)
        prop_desc = f"The Property Depicted as {lot_desc} in {plan_formatted}"
        lines.append(prop_desc)

        # Add plan date and surveyor line
        plan_date = report.plan_date or '[Date]'
        surveyor = report.licensed_surveyor_name or '[Surveyor Name]'
        plan_info = f"Dated {plan_date} made by {surveyor} Licensed Surveyor."
        lines.append(plan_info)
    else:
        # Address-based title for deed/certificate (no plan info line)
        address = generate_smart_address(report) or '[Property Address]'
        prop_desc = f"The Property Depicted as {address}"
        lines.append(prop_desc)

    return lines

def generate_applicant_statement(report: models.Report) -> str:
    """Generate the applicant statement paragraph with smart grammar"""

    # Build applicant full description
    applicant_desc = f"{report.applicant_title or ''} {report.applicant_full_name or '[Applicant Name]'}".strip()

    # ID information
    id_no_formatted = format_no_field("", report.applicant_id_number or '[ID Number]', include_label=False)
    id_info = f"holder {report.applicant_id_type or 'Passport'} {id_no_formatted}"

    # Address parts
    address_parts = []
    if report.applicant_address_line1:
        address_parts.append(report.applicant_address_line1)
    if report.applicant_address_line2:
        address_parts.append(report.applicant_address_line2)
    if report.applicant_district:
        cleaned = clean_spelling_errors(report.applicant_district)
        district_text = append_label_if_missing(cleaned, "District", variants=["district"])
        address_parts.append(district_text)
    if report.applicant_province:
        address_parts.append(report.applicant_province)
    if report.applicant_country:
        address_parts.append(report.applicant_country)

    address_str = ", ".join(address_parts) if address_parts else "[Address]"

    # Get pronouns
    pronouns = get_pronoun(report.applicant_title, report.property_ownership)

    # Build ownership text
    if report.property_ownership:
        ownership_text = report.property_ownership
    else:
        ownership_text = f"owned by {pronouns['object']}"

    # Property type
    property_type = report.property_type_valued or "immovable property"

    # Valuation type
    valuation_type = report.valuation_type or "Market Value"

    # Build paragraph
    paragraph1 = f"This Valuation Report is furnished at the request of {applicant_desc} {id_info} of {address_str}."

    # Second part - wishes to know
    wish_text = f"{applicant_desc} wishes to know the {valuation_type} of {property_type} {ownership_text} in the Democratic Socialist Republic of Sri Lanka."

    # Handle additional owners if any
    if report.has_additional_owner == "yes" and report.additional_owner_names:
        wish_text = wish_text.replace(f"{ownership_text}", f"{ownership_text} & {pronouns['possessive']} family {report.additional_owner_names}")

    return [paragraph1, wish_text]

def generate_deed_description(deeds: Optional[List[Dict]]) -> Optional[str]:
    """Generate deed description text if deeds are provided"""
    if not deeds or len(deeds) == 0:
        return None

    deed_parts = []
    for deed in deeds:
        deed_type = deed.get('deed_type', 'Deed')
        deed_num = deed.get('deed_number', '[Number]')
        deed_date = deed.get('deed_date', '[Date]')

        deed_no_formatted = format_no_field("", deed_num, include_label=False)
        deed_text = f"{deed_type} {deed_no_formatted} dated {deed_date}"

        # Add notary info if available
        if deed.get('notary_name') or deed.get('notary_location'):
            notary_parts = []
            if deed.get('notary_name'):
                notary_parts.append(f"attested by {deed['notary_name']} Notary Public")
            if deed.get('notary_location'):
                cleaned = clean_spelling_errors(deed['notary_location'])
                location_text = append_label_if_missing(cleaned, "District", variants=["district"])
                notary_parts.append(f"in {location_text}")
            if notary_parts:
                deed_text += " " + " ".join(notary_parts)

        deed_parts.append(deed_text)

    if len(deed_parts) == 1:
        return f"requesting a Valuation Report of the immovable properties described in schedules of {deed_parts[0]}."
    else:
        # Multiple deeds - join with &
        deeds_text = " & schedule of ".join(deed_parts)
        return f"requesting a Valuation Report of the immovable properties described in schedules of {deeds_text}."

def generate_submission_statement(report: models.Report) -> Optional[str]:
    """Generate submission destination statement with optional purpose and recipient position"""
    if not report.submission_organization:
        return None

    org_text = ""

    # Add recipient position if available
    if report.submission_recipient_position:
        org_text = f"{report.submission_recipient_position}, "

    org_text += report.submission_organization

    # Add address if available
    if report.submission_address:
        org_text += f", {report.submission_address}"

    statement = f"This Valuation Report is to be submitted to {org_text}"

    # Add purpose if available
    if report.valuation_purpose:
        statement += f" for the purpose of {report.valuation_purpose}"

    statement += "."
    return statement

def generate_situation_text(report: models.Report) -> Optional[str]:
    """
    Generate SITUATION section text from property location data
    Following professional Sri Lankan valuation report format
    """
    print(f"[SITUATION] Report ID: {report.id}")
    print(f"[SITUATION] Village: {report.property_village}")
    print(f"[SITUATION] District: {report.property_district}")
    print(f"[SITUATION] GN Division: {report.grama_niladari_division}")
    print(f"[SITUATION] DS Division: {report.property_divisional_secretariat}")
    print(f"[SITUATION] Korale: {report.korale}")
    print(f"[SITUATION] Pradeshiya Sabha: {report.pradeshiya_sabha}")

    # Need at least some basic location info
    if not (report.property_village or report.property_district):
        print("[SITUATION] No location data found, returning None")
        return None

    # Build the comprehensive situation text parts
    parts = []

    # Start with "The property is situated"
    # Handle Assessment Number if municipal/urban property
    prefix = "The property"
    if report.assessment_number:
        assessment_formatted = format_no_field("Assessment", report.assessment_number, include_label=False)
        prefix += f" to be valued is situated bearing {assessment_formatted}"
        if report.property_name:
            prefix += f" {report.property_name}"
    elif report.property_name:
        prefix += f" is situated at {report.property_name}"
    else:
        prefix += " is situated"

    # Add village information
    if report.property_village:
        if " is situated" in prefix and prefix.endswith("situated"):
            parts.append(f"in {report.property_village} village")
        else:
            parts.append(f" in {report.property_village} village")

    # Add property number (ward/lot number)
    if report.property_number:
        property_no_formatted = format_no_field("", report.property_number, include_label=False)
        parts.append(f"in {property_no_formatted}")

    # Add location direction if available (e.g., "north-east")
    direction_suffix = ""
    if report.location_direction:
        direction_suffix = f"-{report.location_direction}"

    # Add Grama Niladari Division (with intelligent label handling)
    if report.grama_niladari_division:
        cleaned = clean_spelling_errors(report.grama_niladari_division)
        gn_text = append_label_if_missing(
            cleaned,
            "Grama Niladari division",
            variants=["grama niladari division", "Grama Niladari Division", "GN division", "GN Division"]
        )
        # Inject direction suffix before "Grama Niladari division" if it exists
        if direction_suffix and "Grama Niladari division" in gn_text:
            gn_text = gn_text.replace(" Grama Niladari division", f"{direction_suffix} Grama Niladari division")
        elif direction_suffix:
            # If variant was used, just prepend the direction
            gn_text = f"{gn_text}{direction_suffix}"
        parts.append(gn_text)

    # Add Divisional Secretariat (with intelligent label handling)
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
        # Add "division of" wrapper, but check if "division" is already in the text
        if "division" in ds_text.lower():
            parts.append(f"within the {ds_text} of")
        else:
            parts.append(f"within the {ds_text} division of")

    # Add Korale (with intelligent label handling)
    if report.korale:
        cleaned = clean_spelling_errors(report.korale)
        korale_text = append_label_if_missing(cleaned, "Korale", variants=["korale"])
        parts.append(f"in {korale_text}")

    # Add Pradeshiya Sabha or Municipal Council (with intelligent label handling)
    if report.is_municipal_limit and report.property_district:
        district_cleaned = clean_spelling_errors(report.property_district)
        district_text = append_label_if_missing(district_cleaned, "District", variants=["district"])
        parts.append(f"within the Municipal Council limit of {district_text}")
    elif report.pradeshiya_sabha:
        cleaned = clean_spelling_errors(report.pradeshiya_sabha)
        ps_text = append_label_if_missing(cleaned, "Pradeshiya Sabha", variants=["pradeshiya sabha", "PS"])
        parts.append(f"of {ps_text}")

    # Add District (only if not in municipal limit, with intelligent label handling)
    if report.property_district and not report.is_municipal_limit:
        cleaned = clean_spelling_errors(report.property_district)
        district_text = append_label_if_missing(cleaned, "District", variants=["district"])
        parts.append(f"in {district_text}")

    # Add Province (with intelligent label handling)
    if report.property_province:
        cleaned = clean_spelling_errors(report.property_province)
        province_text = append_label_if_missing(cleaned, "Province", variants=["province"])
        parts.append(province_text)

    # Add "of Sri Lanka" at the end
    if parts:
        parts.append("of Sri Lanka")

    # Assemble the complete sentence
    if parts:
        situation_text = prefix + " " + " ".join(parts) + "."
    else:
        # Fallback to smart address if no detailed location data
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

    Format: [Property Number], [Village] Village, [GN Division] Grama Niladari Division,
            [DS Division] Divisional Secretariat Division, [District] District, [Province]

    Only includes components that are present.
    """
    components = []

    # Property number (e.g., "No: 1202")
    if report.property_number:
        components.append(report.property_number)

    # Village name
    if report.property_village:
        components.append(f"{report.property_village} Village")

    # Grama Niladari Division
    if report.grama_niladari_division:
        components.append(f"{report.grama_niladari_division} Grama Niladari Division")

    # Divisional Secretariat (if available)
    if hasattr(report, 'property_divisional_secretariat') and report.property_divisional_secretariat:
        components.append(f"{report.property_divisional_secretariat} Divisional Secretariat Division")

    # Korale (if available)
    if report.korale:
        components.append(report.korale)

    # Pradeshiya Sabha (if available)
    if report.pradeshiya_sabha:
        components.append(report.pradeshiya_sabha)

    # District (usually required)
    if report.property_district:
        components.append(f"{report.property_district} District")

    # Province
    if report.property_province:
        components.append(report.property_province)

    if not components:
        return None

    # Join with commas
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
    Example output: "The boundaries referred above are in accordance with those shown in plan
    and are well defined and demarcated by brick masonry parapet walls constructed on rubble
    masonry foundation on the north, east, south and the west. There is an Auto roller gate
    entrance to the property."
    """
    # Map boundary type IDs to readable labels
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

    # Entrance type labels
    entrance_labels = {
        'auto_roller_gate': 'an Auto roller gate',
        'iron_gate': 'an Iron gate',
        'wooden_gate': 'a Wooden gate',
        'sliding_gate': 'a Sliding gate',
        'swing_gate': 'a Swing gate',
        'no_gate': None
    }

    parts = []

    # Opening statement
    parts.append("The boundaries referred above are in accordance with those shown in plan and are well defined")

    # Determine boundary types per direction or use general physical boundaries
    boundary_types_per_dir = report.boundary_types_per_direction or {}
    physical_types = report.physical_boundaries_types or []

    if boundary_types_per_dir:
        # Group directions by boundary type
        type_to_directions = {}
        directions_order = ['north', 'east', 'south', 'west']

        for direction in directions_order:
            b_type = boundary_types_per_dir.get(direction)
            if b_type:
                if b_type not in type_to_directions:
                    type_to_directions[b_type] = []
                type_to_directions[b_type].append(direction)

        # Build description for each boundary type group
        boundary_descriptions = []
        for b_type, directions in type_to_directions.items():
            type_label = boundary_type_labels.get(b_type, b_type)
            dir_labels = [d for d in directions]

            if len(dir_labels) == 4:
                dir_text = "on all four sides"
            elif len(dir_labels) == 1:
                dir_text = f"on the {dir_labels[0]}"
            else:
                # Format as "north, east and south"
                dir_text = "on the " + ", ".join(dir_labels[:-1]) + f" and {dir_labels[-1]}"

            boundary_descriptions.append(f"demarcated by {type_label} {dir_text}")

        if boundary_descriptions:
            parts.append(" and " + ", ".join(boundary_descriptions))

    elif physical_types:
        # Use general physical boundary types
        type_labels = [boundary_type_labels.get(t, t) for t in physical_types[:3]]

        if 'rubble_foundation' in physical_types:
            # Special case: "brick walls constructed on rubble foundation"
            main_types = [t for t in type_labels if 'rubble' not in t]
            if main_types:
                parts.append(f" and demarcated by {main_types[0]} constructed on rubble masonry foundation on the north, east, south and the west")
            else:
                parts.append(f" and demarcated by rubble masonry foundation on all sides")
        elif type_labels:
            parts.append(f" and demarcated by {', '.join(type_labels)}")

    parts.append(".")

    # Add entrance/gate information
    entrance_type = report.entrance_type
    if entrance_type and entrance_type != 'no_gate':
        entrance_label = entrance_labels.get(entrance_type)
        if entrance_label:
            parts.append(f" There is {entrance_label} entrance to the property.")

    result = "".join(parts)
    return result if result != "The boundaries referred above are in accordance with those shown in plan and are well defined." else None


def format_list_with_grammar(items: List[str]) -> str:
    """
    Format a list of items with proper Oxford comma grammar.

    Examples:
        ['item1'] -> 'item1'
        ['item1', 'item2'] -> 'item1 and item2'
        ['item1', 'item2', 'item3'] -> 'item1, item2, and item3'
    """
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        return ", ".join(items[:-1]) + f", and {items[-1]}"


def render_construction_details(doc, building: Dict) -> None:
    """
    Render construction materials section for a building.
    Uses professional sentence-based format for new data structure.
    Maintains backward compatibility with old format.
    """
    construction = building.get('construction_materials', {})
    if not construction:
        return

    sentences = []

    # NEW FORMAT: Check for new enhanced structure
    roof_details = construction.get('roof_details', {})
    wall_details = construction.get('wall_details', {})
    floor_details = construction.get('floor_details', {})

    # Roof Construction (NEW FORMAT)
    if roof_details and (roof_details.get('structure_type') or roof_details.get('covering_material')):
        roof_parts = []

        structure_type = roof_details.get('structure_type')
        if structure_type:
            structure_labels = {
                'timber_frame': 'timber frame',
                'steel_trusses': 'steel trusses',
                'concrete_slab': 'concrete slab',
                'rcc_flat': 'RCC flat',
                'prefab_trusses': 'prefabricated trusses',
                'mixed': 'mixed construction'
            }
            roof_parts.append(structure_labels.get(structure_type, structure_type.replace('_', ' ')))

        covering_materials = roof_details.get('covering_material', [])
        if covering_materials:
            covering_labels = {
                'asbestos_sheets': 'asbestos sheets',
                'clay_tiles': 'clay tiles',
                'concrete_tiles': 'concrete tiles',
                'metal_sheets': 'metal sheets',
                'concrete_flat': 'concrete flat',
                'cadjans': 'cadjans',
                'shingles': 'shingles'
            }
            covering_list = [covering_labels.get(m, m.replace('_', ' ')) for m in covering_materials]
            if covering_list:
                roof_parts.append(f"covered with {format_list_with_grammar(covering_list)}")

        additional = roof_details.get('additional_details')
        if additional:
            roof_parts.append(additional.lower() if additional else '')

        if roof_parts:
            sentences.append(f"The roof is constructed with {' '.join(roof_parts)}.")

    # Wall Construction (NEW FORMAT)
    if wall_details and wall_details.get('material'):
        wall_parts = []

        material = wall_details.get('material')
        if material:
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
            wall_parts.append(material_labels.get(material, material.replace('_', ' ')))

        finishes = wall_details.get('finish', [])
        if finishes:
            finish_labels = {
                'cement_plaster_painted': 'cement plaster and painted',
                'lime_plaster': 'lime plaster',
                'tiles': 'tiles',
                'exposed_brick': 'exposed brick',
                'color_washed': 'color washed',
                'textured': 'textured finish',
                'unfinished': 'unfinished'
            }
            finish_list = [finish_labels.get(f, f.replace('_', ' ')) for f in finishes]
            if finish_list:
                wall_parts.append(f"finished with {format_list_with_grammar(finish_list)}")

        if wall_parts:
            sentences.append(f"The walls are {' '.join(wall_parts)}.")

    # Floor Construction (NEW FORMAT)
    if floor_details and floor_details.get('material'):
        floor_materials = floor_details.get('material', [])
        if floor_materials:
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
            material_list = [material_labels.get(m, m.replace('_', ' ')) for m in floor_materials]

            floor_sentence = f"The floor is {format_list_with_grammar(material_list)} rendered"

            quality = floor_details.get('finish_quality')
            if quality:
                quality_labels = {'basic': 'basic', 'standard': 'good', 'premium': 'premium'}
                floor_sentence += f" with {quality_labels.get(quality, quality)} quality finish"

            sentences.append(f"{floor_sentence}.")

    # Ceiling (KEEP EXISTING - works for both old and new format)
    ceiling = construction.get('ceiling_type', '')
    if ceiling and ceiling != 'none':
        ceiling_labels = {
            'gypsum_board': 'gypsum board',
            'plywood': 'plywood',
            'asbestos': 'asbestos',
            'pvc': 'PVC panels',
            'timber': 'timber planks'
        }
        sentences.append(f"The ceiling is finished with {ceiling_labels.get(ceiling, ceiling.replace('_', ' '))}.")

    # Doors & Windows (NEW FORMAT)
    doors_windows = construction.get('doors_windows_details', {})
    if doors_windows:
        dw_parts = []

        # Windows
        window_frame = doors_windows.get('window_frame_material', [])
        window_glass = doors_windows.get('window_glass_type', [])
        window_security = doors_windows.get('window_security', [])

        if window_frame or window_glass or window_security:
            window_parts = []

            if window_frame:
                frame_labels = {
                    'timber': 'timber',
                    'aluminum': 'aluminum',
                    'upvc': 'UPVC',
                    'steel': 'steel'
                }
                frame_list = [frame_labels.get(f, f) for f in window_frame]
                window_parts.append(f"{format_list_with_grammar(frame_list)} frame windows")

            if window_glass:
                glass_labels = {
                    'clear': 'clear glass',
                    'tinted': 'tinted glass',
                    'frosted': 'frosted glass',
                    'double_glazing': 'double glazing'
                }
                glass_list = [glass_labels.get(g, g) for g in window_glass]
                window_parts.append(f"with {format_list_with_grammar(glass_list)}")

            if window_security:
                security_labels = {
                    'burglar_bars': 'burglar bars',
                    'grills': 'security grills',
                    'security_mesh': 'security mesh'
                }
                security_list = [security_labels.get(s, s) for s in window_security]
                window_parts.append(f"fitted with {format_list_with_grammar(security_list)}")

            if window_parts:
                dw_parts.append(f"The building has {' '.join(window_parts)}.")

        # Doors
        main_door = doors_windows.get('main_door_material')
        internal_door = doors_windows.get('internal_door_material')
        door_security = doors_windows.get('door_security', [])

        if main_door or internal_door:
            door_parts = []

            if main_door:
                main_door_labels = {
                    'solid_timber': 'solid timber',
                    'panel_door': 'timber panel',
                    'metal': 'metal',
                    'upvc': 'UPVC',
                    'glass': 'glass'
                }
                door_parts.append(f"main door is {main_door_labels.get(main_door, main_door.replace('_', ' '))}")

            if internal_door:
                internal_door_labels = {
                    'timber': 'solid timber',
                    'flush_doors': 'flush doors',
                    'panel_doors': 'panel doors',
                    'hollow_core': 'hollow core'
                }
                door_parts.append(f"internal doors are {internal_door_labels.get(internal_door, internal_door.replace('_', ' '))}")

            door_sentence = f"The {' and '.join(door_parts)}"

            if door_security:
                security_labels = {
                    'deadbolt': 'deadbolt locks',
                    'security_locks': 'security locks',
                    'door_chain': 'door chains',
                    'multi_point': 'multi-point locking systems'
                }
                security_list = [security_labels.get(s, s) for s in door_security]
                door_sentence += f" with {format_list_with_grammar(security_list)}"

            dw_parts.append(f"{door_sentence}.")

        sentences.extend(dw_parts)

    # BACKWARD COMPATIBILITY: Fall back to old format if new format not available
    if not sentences:
        # Old format handling (existing logic)
        parts = []

        # Foundation (old)
        foundation = construction.get('foundation_type', '')
        if foundation:
            foundation_labels = {
                'rubble_masonry': 'Rubble masonry',
                'concrete_strip': 'Concrete strip',
                'pile': 'Pile',
                'raft': 'Raft',
                'pad': 'Pad foundation'
            }
            parts.append(f"Foundation: {foundation_labels.get(foundation, foundation.replace('_', ' ').title())}")

        # Walls (old)
        wall = construction.get('wall_construction', {})
        if wall:
            wall_parts = []
            material = wall.get('material', '')
            if material:
                wall_material_labels = {
                    'brick_masonry': 'brick masonry',
                    'cement_block': 'cement block',
                    'stone': 'stone masonry',
                    'rcc_columns': 'RCC columns',
                    'cadjan': 'cadjan',
                    'timber': 'timber frame'
                }
                wall_parts.append(wall_material_labels.get(material, material.replace('_', ' ')))

            thickness = wall.get('thickness', '')
            if thickness:
                thickness_labels = {
                    '4_5_inch': '4.5 inch',
                    '9_inch': '9 inch',
                    '13_5_inch': '13.5 inch'
                }
                wall_parts.append(thickness_labels.get(thickness, thickness.replace('_', ' ')))

            finish = wall.get('finish', '')
            if finish:
                finish_labels = {
                    'plastered_painted': 'plastered and painted',
                    'fair_faced': 'fair-faced',
                    'textured': 'textured finish'
                }
                wall_parts.append(finish_labels.get(finish, finish.replace('_', ' ')))

            if wall_parts:
                parts.append(f"Walls: {', '.join(wall_parts)}")

        # Roof (old)
        roof = construction.get('roof_structure', '')
        if roof:
            roof_labels = {
                'timber_frame': 'Timber frame',
                'steel_trusses': 'Steel trusses',
                'rcc_slab': 'RCC slab',
                'cadjan': 'Cadjan'
            }
            parts.append(f"Roof: {roof_labels.get(roof, roof.replace('_', ' ').title())}")

        # Ceiling (old - already handled above)

        if parts:
            construction_text = "; ".join(parts) + "."
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            para.paragraph_format.line_spacing = 0.9
            run = para.add_run(construction_text)
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0, 0, 0)
            return

    # Render new format as standalone paragraph (no label)
    if sentences:
        construction_text = " ".join(sentences)
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
        para.paragraph_format.line_spacing = 0.9
        run = para.add_run(construction_text)
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0, 0, 0)


def render_utilities_services(doc, building: Dict) -> None:
    """
    Render utilities and services section for a building.
    Includes water, electricity, sewage, parking, security, and amenities.
    """
    utilities = building.get('utilities_services', {})
    if not utilities:
        return

    parts = []

    # Water supply
    water = utilities.get('water_supply', '')
    if water:
        water_labels = {
            'pipe_borne': 'pipe-borne water (NWSDB)',
            'well': 'well water',
            'tube_well': 'tube well'
        }
        parts.append(water_labels.get(water, water.replace('_', ' ')))

    # Sewage system
    sewage = utilities.get('sewage_system', '')
    if sewage:
        sewage_labels = {
            'municipal_sewer': 'municipal sewage system',
            'septic_tank': 'septic tank',
            'none': 'no sewage system'
        }
        if sewage != 'none':
            parts.append(sewage_labels.get(sewage, sewage.replace('_', ' ')))

    # Electricity
    elec = utilities.get('electricity', {})
    if elec:
        source = elec.get('source', '')
        if source:
            source_text = 'CEB electricity' if source == 'ceb' else f'{source.title()} electricity'
            if elec.get('three_phase'):
                source_text += ' (three-phase connection)'
            parts.append(source_text)

    # Parking
    parking = utilities.get('parking', {})
    covered = int(to_float(parking.get('covered_spaces')))
    uncovered = int(to_float(parking.get('uncovered_spaces')))
    total_parking = covered + uncovered
    if total_parking > 0:
        parking_text = f"parking for {total_parking} vehicle{'s' if total_parking != 1 else ''}"
        if covered > 0 and uncovered > 0:
            parking_text += f" ({covered} covered, {uncovered} open)"
        elif covered > 0:
            parking_text += " (covered)"
        parts.append(parking_text)

    # Security features
    security = utilities.get('security_features', [])
    if security:
        security_labels = {
            'boundary_wall': 'boundary wall',
            'main_gate': 'main gate',
            'cctv': 'CCTV surveillance',
            'security_lights': 'security lighting'
        }
        security_list = [security_labels.get(s, s.replace('_', ' ')) for s in security]
        if security_list:
            parts.append(", ".join(security_list))

    # Amenities
    amenities = utilities.get('amenities', {})
    amenity_list = []
    if amenities.get('air_conditioning'):
        amenity_list.append('air conditioning')
    if amenities.get('built_in_wardrobes'):
        amenity_list.append('built-in wardrobes')
    if amenities.get('modern_kitchen'):
        amenity_list.append('modern kitchen fittings')
    if amenity_list:
        parts.append(", ".join(amenity_list))

    # Hot water system
    hot_water = utilities.get('hot_water_system', '')
    if hot_water and hot_water != 'none':
        hot_water_labels = {
            'electric_geyser': 'electric geyser',
            'solar_heater': 'solar water heater',
            'gas_heater': 'gas water heater'
        }
        parts.append(hot_water_labels.get(hot_water, hot_water.replace('_', ' ')))

    if parts:
        # Capitalize first letter
        utilities_text = "; ".join(parts)
        utilities_text = utilities_text[0].upper() + utilities_text[1:] + "."
        add_inline_field(doc, "Utilities and services", utilities_text)


def generate_user_data_docx(report: models.Report, user: models.User = None) -> BytesIO:
    """
    Generate a formatted DOCX file from report and user data with comprehensive error handling.

    Args:
        report: Report model instance
        user: Optional user model (uses report.user if not provided)

    Returns:
        BytesIO object containing the DOCX document

    Raises:
        ValueError: If report data is incomplete or malformed
        AttributeError: If required fields are missing
        TypeError: If data types are incorrect
    """
    try:
        # Use the user from the report relationship if not provided
        if user is None:
            user = report.user

        # Create a new Document
        doc = Document()

        # ===== LETTERHEAD =====
        # Use template system for letterhead rendering
        template_id = user.preferred_letterhead_template or 'classic'
        template = get_template(template_id)
        template.render_letterhead(doc, user, report)

        # ===== OPENING SECTION =====

        # Generate and add title block (centered)
        title_lines = generate_title_block(report)
        for i, line in enumerate(title_lines):
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = Pt(0)
            para.paragraph_format.line_spacing = 0.9
            run = para.add_run(line)
            if i == 0:  # "VALUATION REPORT"
                run.bold = True
                run.font.size = Pt(11)
            elif i == 2:  # Property description line
                run.bold = True
                run.font.size = Pt(9)
            else:
                run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0, 0, 0)

        # Add spacing before applicant statements
        spacing_para1 = doc.add_paragraph()
        spacing_para1.paragraph_format.space_before = Pt(8)
        spacing_para1.paragraph_format.space_after = Pt(0)

        # Add applicant statements (justified)
        applicant_statements = generate_applicant_statement(report)
        for statement in applicant_statements:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            para.paragraph_format.line_spacing = 0.9
            run = para.add_run(statement)
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0, 0, 0)

        # Add deed/certificate description ONLY if not plan-based identification
        # (Plan-based reports don't show the deed sentence for cleaner appearance)
        should_show_deed_sentence = (
            report.property_identification_type in ['deed', 'certificate_of_sale']
            and report.has_deed_info == "yes"
            and report.deeds
        )

        # Backward compatibility: Old reports (NULL type) with deed data should show sentence
        if not report.property_identification_type and report.has_deed_info == "yes" and report.deeds:
            should_show_deed_sentence = True

        if should_show_deed_sentence:
            deed_text = generate_deed_description(report.deeds)
            if deed_text:
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                para.paragraph_format.line_spacing = 0.9
                run = para.add_run(deed_text)
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0, 0, 0)

        # Add submission statement
        submission_text = generate_submission_statement(report)
        if submission_text:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.space_before = Pt(0)
            para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            para.paragraph_format.line_spacing = 0.9
            run = para.add_run(submission_text)
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0, 0, 0)

        # Add inspection date
        if report.inspection_date:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.space_before = Pt(6)
            para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            para.paragraph_format.line_spacing = 0.9
            run = para.add_run(f"Date of Inspection: {report.inspection_date}")
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0, 0, 0)

        # Add special note if applicable
        if report.has_special_note == "yes" and report.special_note_text:
            # Note label
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.space_before = Pt(6)
            para.paragraph_format.space_after = SUBHEADING_SPACE_AFTER
            para.paragraph_format.line_spacing = 0.9
            run = para.add_run("Note:")
            run.bold = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0, 0, 0)

            # Note text
            note_para = doc.add_paragraph()
            note_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            note_para.paragraph_format.space_before = Pt(0)
            note_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            note_para.paragraph_format.line_spacing = 0.9
            note_run = note_para.add_run(report.special_note_text)
            note_run.font.size = Pt(9)
            note_run.font.color.rgb = RGBColor(0, 0, 0)

        # ===== 1.0 SITUATION SECTION (First after opening) =====
        situation_text = generate_situation_text(report)
        if situation_text:
            # Add numbered section heading
            add_section_heading(doc, "1.0", "SITUATION")

            # SITUATION text
            situation_para = doc.add_paragraph()
            situation_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            situation_para.paragraph_format.space_before = Pt(0)
            situation_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            situation_para.paragraph_format.line_spacing = 0.9
            situation_run = situation_para.add_run(situation_text)
            situation_run.font.size = Pt(9)
            situation_run.font.color.rgb = RGBColor(0, 0, 0)

        # ===== 2.0 ACCESS SECTION (After SITUATION) =====
        access_text = generate_access_text(report)
        locality_text = generate_locality_description(report)

        if access_text:
            # Add numbered section heading
            add_section_heading(doc, "2.0", "ACCESS")

            # ACCESS text
            access_para = doc.add_paragraph()
            access_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            access_para.paragraph_format.space_before = Pt(0)
            access_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            access_para.paragraph_format.line_spacing = 0.9
            access_run = access_para.add_run(access_text)
            access_run.font.size = Pt(9)
            access_run.font.color.rgb = RGBColor(0, 0, 0)

            # Add coordinates paragraph if available
            if report.property_latitude and report.property_longitude:
                # Add small spacing
                coord_para = doc.add_paragraph()
                coord_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                coord_para.paragraph_format.space_before = Pt(6)
                coord_para.paragraph_format.space_after = Pt(6)
                coord_para.paragraph_format.line_spacing = 0.9

                # Coordinate label (bold)
                coord_label = coord_para.add_run("Property Location Coordinates: ")
                coord_label.bold = True
                coord_label.font.size = Pt(9)
                coord_label.font.color.rgb = RGBColor(0, 0, 0)

                # Coordinate values (format to 6 decimal places)
                lat_value = float(report.property_latitude)
                lng_value = float(report.property_longitude)
                coord_text = coord_para.add_run(f"{lat_value:.6f}, {lng_value:.6f}")
                coord_text.font.size = Pt(9)
                coord_text.font.color.rgb = RGBColor(0, 0, 0)

            # Add map image if available (embedded within ACCESS section)
            if report.location_map_image_data:
                try:
                    # Fetch the image from URL
                    map_url = report.location_map_image_data
                    print(f"[DOCX] Fetching map image from: {map_url}")

                    response = requests.get(map_url, timeout=30)
                    if response.status_code == 200:
                        # Add spacing before map
                        map_spacing_para = doc.add_paragraph()
                        map_spacing_para.paragraph_format.space_before = IMAGE_SPACING_BEFORE
                        map_spacing_para.paragraph_format.space_after = Pt(0)

                        # Add map image
                        map_para = doc.add_paragraph()
                        map_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        map_para.paragraph_format.space_before = Pt(0)
                        map_para.paragraph_format.space_after = IMAGE_SPACING_AFTER

                        # Add image with calculated dimensions (maintains aspect ratio)
                        image_stream = BytesIO(response.content)
                        dimensions = calculate_image_dimensions(
                            image_stream,
                            MAP_IMAGE_WIDTH,
                            MAP_IMAGE_MAX_HEIGHT
                        )
                        map_para.add_run().add_picture(image_stream, **dimensions)

                        print(f"[DOCX] Successfully added map image to document")
                    else:
                        print(f"[DOCX] Failed to fetch map image: HTTP {response.status_code}")
                except Exception as e:
                    print(f"[DOCX] Error adding map image: {str(e)}")
                    # Continue without map if error occurs

        # NOTE: LOCALITY section moved to 6.0 (after PHOTOGRAPHS)

        # ===== 3.0 IDENTIFICATION OF PROPERTY SECTION =====
        # This section appears if any property header data is available
        has_property_header_data = (
            report.land_traditional_name or
            report.land_extent_formatted or
            report.boundaries or
            report.physical_boundaries_types or
            report.physical_boundaries_description or
            report.boundaries_summary_text
        )

        if has_property_header_data:
            # Add numbered section heading
            add_section_heading(doc, "3.0", "IDENTIFICATION OF PROPERTY")

            # Traditional Land Name
            if report.land_traditional_name:
                name_para = doc.add_paragraph()
                name_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                name_para.paragraph_format.space_before = Pt(0)
                name_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                name_para.paragraph_format.line_spacing = 0.9
                name_label = name_para.add_run("Name of Land: ")
                name_label.bold = True
                name_label.font.size = Pt(9)
                name_label.font.color.rgb = RGBColor(0, 0, 0)
                name_value = name_para.add_run(f'"{report.land_traditional_name}"')
                name_value.font.size = Pt(9)
                name_value.font.color.rgb = RGBColor(0, 0, 0)

            # Survey Plan Information
            if report.property_lot_description and report.plan_number:
                plan_para = doc.add_paragraph()
                plan_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                plan_para.paragraph_format.space_before = Pt(0)
                plan_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                plan_para.paragraph_format.line_spacing = 0.9
                plan_label = plan_para.add_run("Survey Plan: ")
                plan_label.bold = True
                plan_label.font.size = Pt(9)
                plan_label.font.color.rgb = RGBColor(0, 0, 0)

                plan_text = f"{report.property_lot_description} in Plan No: {report.plan_number}"
                if report.plan_date:
                    plan_text += f" dated {report.plan_date}"
                if report.licensed_surveyor_name:
                    plan_text += f" made by {report.licensed_surveyor_name}, Licensed Surveyor"
                plan_text += "."

                plan_value = plan_para.add_run(plan_text)
                plan_value.font.size = Pt(9)
                plan_value.font.color.rgb = RGBColor(0, 0, 0)

            # Land Extent
            if report.land_extent_formatted:
                extent_para = doc.add_paragraph()
                extent_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                extent_para.paragraph_format.space_before = Pt(0)
                extent_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                extent_para.paragraph_format.line_spacing = 0.9
                extent_label = extent_para.add_run("Extent: ")
                extent_label.bold = True
                extent_label.font.size = Pt(9)
                extent_label.font.color.rgb = RGBColor(0, 0, 0)

                extent_text = report.land_extent_formatted
                if report.land_extent_hectares:
                    extent_text += f" [{report.land_extent_hectares:.4f} Hectares]"
                if report.land_extent_square_meters:
                    extent_text += f" [{report.land_extent_square_meters:.2f} m²]"

                extent_value = extent_para.add_run(extent_text)
                extent_value.font.size = Pt(9)
                extent_value.font.color.rgb = RGBColor(0, 0, 0)

            # Boundaries - Enhanced Format with all details
            if report.boundaries:
                # Add spacing before boundaries
                boundaries_spacing = doc.add_paragraph()
                boundaries_spacing.paragraph_format.space_before = SUBHEADING_SPACE_BEFORE
                boundaries_spacing.paragraph_format.space_after = SUBHEADING_SPACE_AFTER

                # Boundaries subheading
                boundaries_heading = doc.add_paragraph()
                boundaries_heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
                boundaries_heading.paragraph_format.space_before = Pt(0)
                boundaries_heading.paragraph_format.space_after = SUBHEADING_SPACE_AFTER
                boundaries_heading.paragraph_format.line_spacing = 0.9
                boundaries_heading_run = boundaries_heading.add_run("Boundaries:")
                boundaries_heading_run.bold = True
                boundaries_heading_run.font.size = Pt(9)
                boundaries_heading_run.font.color.rgb = RGBColor(0, 0, 0)

                # Physical boundary type labels mapping
                boundary_type_labels = {
                    'brick_walls': 'Brick Walls',
                    'barbed_wire': 'Barbed Wire Fence',
                    'live_fence': 'Live Fence',
                    'concrete_posts': 'Concrete Posts',
                    'iron_gate': 'Iron Gate',
                    'rubble_foundation': 'Rubble Foundation',
                    'chain_link': 'Chain Link Fence',
                    'wooden_fence': 'Wooden Fence',
                    'stone_wall': 'Stone Wall',
                    'hedge': 'Hedge',
                    'none': 'None'
                }

                # Enhanced format for each boundary direction
                directions = ['north', 'south', 'east', 'west']
                direction_labels = ['North', 'South', 'East', 'West']

                # SAFE: Get boundaries with None check
                boundaries = safe_get_json_field(report, 'boundaries', {})
                if not boundaries:
                    boundaries = {}

                for direction, label in zip(directions, direction_labels):
                    boundary_data = boundaries.get(direction, {}) if isinstance(boundaries, dict) else {}

                    # Main description line: "North  : Lot 7"
                    boundary_line = f"{label:<6} : "
                    boundary_text = boundary_data.get('description') or 'Not specified'

                    # Create paragraph for main boundary description
                    boundary_para = doc.add_paragraph()
                    boundary_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    boundary_para.paragraph_format.space_before = Pt(0)
                    boundary_para.paragraph_format.space_after = Pt(1)
                    boundary_para.paragraph_format.line_spacing = 0.9
                    boundary_para.paragraph_format.left_indent = Inches(0.5)

                    boundary_run = boundary_para.add_run(boundary_line + boundary_text)
                    boundary_run.font.size = Pt(9)
                    boundary_run.font.color.rgb = RGBColor(0, 0, 0)

                    # Additional boundary details (if any)
                    additional_details = []

                    # Physical Boundary Type (from boundary_types_per_direction)
                    boundary_types_per_dir = report.boundary_types_per_direction or {}
                    physical_type = boundary_types_per_dir.get(direction)
                    if physical_type:
                        type_label = boundary_type_labels.get(physical_type, physical_type.replace('_', ' ').title())
                        additional_details.append(f"Type: {type_label}")

                    # Length (optional)
                    length = boundary_data.get('length')
                    if length:
                        additional_details.append(f"Length: {length}")

                    # Adjoins (optional)
                    adjoins = boundary_data.get('adjoins')
                    if adjoins:
                        additional_details.append(f"Adjoins: {adjoins}")

                    # Additional Notes (optional)
                    notes = boundary_data.get('notes')
                    if notes:
                        additional_details.append(f"Notes: {notes}")

                    # Render additional details as sub-items if any exist
                    if additional_details:
                        for detail in additional_details:
                            detail_para = doc.add_paragraph()
                            detail_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            detail_para.paragraph_format.space_before = Pt(0)
                            detail_para.paragraph_format.space_after = Pt(1)
                            detail_para.paragraph_format.line_spacing = 0.9
                            detail_para.paragraph_format.left_indent = Inches(0.75)  # Extra indent for sub-details

                            detail_run = detail_para.add_run(f"  • {detail}")
                            detail_run.font.size = Pt(8)
                            detail_run.font.color.rgb = RGBColor(80, 80, 80)  # Slightly gray for secondary info

                    # Add small spacing after each boundary direction
                    if additional_details:
                        spacing_para = doc.add_paragraph()
                        spacing_para.paragraph_format.space_before = Pt(0)
                        spacing_para.paragraph_format.space_after = Pt(2)

            # Boundary Summary Sentence (Professional description)
            # Use stored text or auto-generate from boundary types per direction
            boundary_summary = report.boundaries_summary_text
            if not boundary_summary and (report.boundary_types_per_direction or report.physical_boundaries_types):
                boundary_summary = generate_boundary_summary_text(report)

            if boundary_summary:
                summary_para = doc.add_paragraph()
                summary_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                summary_para.paragraph_format.space_before = Pt(6)
                summary_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                summary_para.paragraph_format.line_spacing = 0.9
                summary_run = summary_para.add_run(boundary_summary)
                summary_run.font.size = Pt(9)
                summary_run.font.color.rgb = RGBColor(0, 0, 0)


        # ===== 4.0 DESCRIPTION OF PROPERTY SECTION =====
        # Check if there's any property description data
        has_description_data = (
            report.land_description_text or
            report.land_shape or
            report.soil_type or
            report.water_table_depth or
            report.flood_risk or
            report.buildings or
            report.occupier_name
        )

        if has_description_data:
            # Add numbered section heading
            add_section_heading(doc, "4.0", "DESCRIPTION OF PROPERTY")

            # === LAND DESCRIPTION ===
            # Use auto-generated text if available, otherwise build from individual fields
            if report.land_description_text:
                land_para = doc.add_paragraph()
                land_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                land_para.paragraph_format.space_before = Pt(0)
                land_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                land_para.paragraph_format.line_spacing = 0.9
                land_run = land_para.add_run(report.land_description_text)
                land_run.font.size = Pt(9)
                land_run.font.color.rgb = RGBColor(0, 0, 0)
            else:
                # Build land description from individual fields
                land_parts = []

                # Shape and type
                if report.land_shape:
                    shape_labels = {
                        'rectangular': 'rectangular', 'square': 'square', 'triangular': 'triangular',
                        'irregular': 'irregular', 'L_shaped': 'L-shaped', 'trapezoidal': 'trapezoidal'
                    }
                    land_parts.append(f"The land is {shape_labels.get(report.land_shape, report.land_shape)} in shape")

                if report.land_type:
                    type_labels = {
                        'flat': 'flat terrain', 'sloped': 'sloped terrain', 'hilly': 'hilly terrain',
                        'waterfront': 'waterfront', 'paddy': 'paddy land', 'garden': 'garden land'
                    }
                    if land_parts:
                        land_parts.append(f"with {type_labels.get(report.land_type, report.land_type)}")
                    else:
                        land_parts.append(f"The land has {type_labels.get(report.land_type, report.land_type)}")

                # Land level
                if report.land_level:
                    level_labels = {
                        'above_road': 'above road level', 'at_road': 'at road level',
                        'below_road': 'below road level', 'varied': 'varied levels'
                    }
                    land_parts.append(f"and is {level_labels.get(report.land_level, report.land_level)}")
                    if report.land_level_difference:
                        land_parts.append(f"by approximately {report.land_level_difference} feet")

                # Soil type
                if report.soil_type:
                    soil_labels = {
                        'sandy': 'sandy', 'clay': 'clay', 'loam': 'loam', 'laterite': 'laterite',
                        'rocky': 'rocky', 'gravel': 'gravel', 'alluvial': 'alluvial'
                    }
                    land_parts.append(f". The soil is {soil_labels.get(report.soil_type, report.soil_type)}")

                # Water table
                if report.water_table_depth:
                    land_parts.append(f"with water table at approximately {report.water_table_depth} feet depth")

                # Risks
                risk_parts = []
                if report.flood_risk and report.flood_risk != 'none':
                    risk_labels = {'low': 'low', 'moderate': 'moderate', 'high': 'high', 'very_high': 'very high'}
                    risk_parts.append(f"flood risk is {risk_labels.get(report.flood_risk, report.flood_risk)}")
                if report.inundation_risk and report.inundation_risk != 'none':
                    risk_labels = {'low': 'low', 'moderate': 'moderate', 'high': 'high', 'very_high': 'very high'}
                    risk_parts.append(f"inundation risk is {risk_labels.get(report.inundation_risk, report.inundation_risk)}")
                if report.earth_slip_risk and report.earth_slip_risk != 'none':
                    risk_labels = {'low': 'low', 'moderate': 'moderate', 'high': 'high', 'very_high': 'very high'}
                    risk_parts.append(f"earth slip risk is {risk_labels.get(report.earth_slip_risk, report.earth_slip_risk)}")

                if risk_parts:
                    land_parts.append(". The " + ", ".join(risk_parts))

                # Land condition
                if report.land_condition:
                    condition_labels = {
                        'well_maintained': 'well maintained', 'developed': 'developed',
                        'undeveloped': 'undeveloped', 'overgrown': 'overgrown', 'cleared': 'cleared'
                    }
                    land_parts.append(f". The land is {condition_labels.get(report.land_condition, report.land_condition)}")

                if land_parts:
                    land_text = " ".join(land_parts)
                    if not land_text.endswith("."):
                        land_text += "."

                    land_para = doc.add_paragraph()
                    land_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    land_para.paragraph_format.space_before = Pt(0)
                    land_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                    land_para.paragraph_format.line_spacing = 0.9
                    land_run = land_para.add_run(land_text)
                    land_run.font.size = Pt(9)
                    land_run.font.color.rgb = RGBColor(0, 0, 0)

            # === BUILDING DETAILS (Direct numbering: 4.1, 4.2, 4.3) ===
            if report.buildings and len(report.buildings) > 0:
                for idx, building in enumerate(report.buildings):
                    building_number = f"4.{idx + 1}"
                    building_name = building.get('building_name', f'Building {idx + 1}')

                    # Add building subsection heading
                    add_section_heading(doc, building_number, building_name)

                    # === CONSTRUCTION DETAILS (STANDALONE PARAGRAPH - NO LABEL) ===
                    # This comes FIRST, directly under the building heading
                    render_construction_details(doc, building)

                    # === PROFESSIONAL STRUCTURED FORMAT (All buildings) ===

                    # Opening paragraph: Construction materials and general description
                    building_desc_parts = []

                    # Use custom description text if provided
                    if building.get('building_description_text'):
                        opening_para = doc.add_paragraph()
                        opening_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        opening_para.paragraph_format.space_before = Pt(0)
                        opening_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                        opening_para.paragraph_format.line_spacing = 0.9
                        opening_run = opening_para.add_run(building.get('building_description_text'))
                        opening_run.font.size = Pt(9)
                        opening_run.font.color.rgb = RGBColor(0, 0, 0)
                    else:
                        # Build opening description from materials
                        roof_types = building.get('roof_types', [])
                        wall_types = building.get('wall_types', [])
                        floor_types = building.get('floor_types', [])

                        if roof_types or wall_types or floor_types:
                            desc_text = "This is constructed with "

                            # Roof
                            if roof_types:
                                roof_labels = {
                                    'asbestos': 'asbestos sheets', 'tile': 'tiles',
                                    'metal': 'metal sheets', 'concrete': 'concrete flat',
                                    'cadjan': 'cadjans', 'zinc': 'zinc sheets'
                                }
                                roof_text = format_material_list(roof_types, roof_labels)
                                desc_text += f"{roof_text} on "

                            # Roof structure
                            stories = building.get('stories', 1)
                            if stories == 1:
                                desc_text += "timber frame roof "
                            else:
                                desc_text += f"{stories} storey structure "

                            # Walls
                            if wall_types:
                                wall_labels = {
                                    'brick': 'brick masonry', 'cement_block': 'cement block',
                                    'stone': 'stone', 'mud': 'mud', 'timber': 'timber',
                                    'cadjan': 'cadjan', 'rcc_columns': 'RCC columns',
                                    'rubble_masonry': 'rubble masonry'
                                }
                                wall_text = format_material_list(wall_types, wall_labels)
                                desc_text += f"supported by {wall_text} walls "

                            # Foundation/floor
                            if floor_types:
                                floor_labels = {
                                    'cement': 'cement', 'tile': 'tiles', 'terrazzo': 'terrazzo',
                                    'timber': 'timber', 'granite': 'granite', 'earth': 'earth',
                                    'concrete': 'concrete'
                                }
                                floor_text = format_material_list(floor_types, floor_labels)
                                desc_text += f"and the floor is {floor_text} rendered"

                            desc_text += "."

                            opening_para = doc.add_paragraph()
                            opening_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                            opening_para.paragraph_format.space_before = Pt(0)
                            opening_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                            opening_para.paragraph_format.line_spacing = 0.9
                            opening_run = opening_para.add_run(desc_text)
                            opening_run.font.size = Pt(9)
                            opening_run.font.color.rgb = RGBColor(0, 0, 0)

                    # === ACCOMMODATION ===
                    floors = building.get('floors', [])
                    if floors:
                        accom_heading = doc.add_paragraph()
                        accom_heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        accom_heading.paragraph_format.space_before = SUBHEADING_SPACE_BEFORE
                        accom_heading.paragraph_format.space_after = SUBHEADING_SPACE_AFTER
                        accom_heading.paragraph_format.line_spacing = 0.9
                        accom_run = accom_heading.add_run("Accommodation")
                        accom_run.bold = True
                        accom_run.font.size = Pt(9)
                        accom_run.font.color.rgb = RGBColor(0, 0, 0)

                        # Process each floor
                        for floor in floors:
                            floor_name = floor.get('floor_name', 'Ground Floor')
                            floor_area = floor.get('floor_area', 0)
                            accommodation_summary = floor.get('accommodation_summary')

                            # NEW FORMAT: Use accommodation summary if available
                            if accommodation_summary:
                                room_parts = []

                                # Helper function to convert number to words for 1-10
                                def number_to_word(n):
                                    words = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
                                            6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
                                    return words.get(n, str(n))

                                # Build room counts list
                                if accommodation_summary.get('bedrooms', 0) > 0:
                                    count = accommodation_summary['bedrooms']
                                    room_parts.append(f"{number_to_word(count)} bedroom{'s' if count != 1 else ''}")

                                if accommodation_summary.get('bathrooms', 0) > 0:
                                    count = accommodation_summary['bathrooms']
                                    room_parts.append(f"{number_to_word(count)} bathroom{'s' if count != 1 else ''}")

                                if accommodation_summary.get('living_rooms', 0) > 0:
                                    count = accommodation_summary['living_rooms']
                                    room_parts.append(f"{number_to_word(count)} living room{'s' if count != 1 else ''}")

                                if accommodation_summary.get('dining_rooms', 0) > 0:
                                    count = accommodation_summary['dining_rooms']
                                    room_parts.append(f"{number_to_word(count)} dining room{'s' if count != 1 else ''}")

                                if accommodation_summary.get('kitchens', 0) > 0:
                                    count = accommodation_summary['kitchens']
                                    room_parts.append(f"{number_to_word(count)} kitchen{'s' if count != 1 else ''}")

                                if accommodation_summary.get('pantries', 0) > 0:
                                    count = accommodation_summary['pantries']
                                    room_parts.append(f"{number_to_word(count)} {'pantries' if count != 1 else 'pantry'}")

                                if accommodation_summary.get('verandahs', 0) > 0:
                                    count = accommodation_summary['verandahs']
                                    room_parts.append(f"{number_to_word(count)} verandah{'s' if count != 1 else ''}")

                                if accommodation_summary.get('balconies', 0) > 0:
                                    count = accommodation_summary['balconies']
                                    room_parts.append(f"{number_to_word(count)} {'balconies' if count != 1 else 'balcony'}")

                                if accommodation_summary.get('garages', 0) > 0:
                                    count = accommodation_summary['garages']
                                    room_parts.append(f"{number_to_word(count)} garage{'s' if count != 1 else ''}")

                                if accommodation_summary.get('store_rooms', 0) > 0:
                                    count = accommodation_summary['store_rooms']
                                    room_parts.append(f"{number_to_word(count)} store room{'s' if count != 1 else ''}")

                                if accommodation_summary.get('other_rooms', 0) > 0:
                                    count = accommodation_summary['other_rooms']
                                    room_parts.append(f"{number_to_word(count)} other room{'s' if count != 1 else ''}")

                                if room_parts:
                                    # Create professional sentence
                                    floor_para = doc.add_paragraph()
                                    floor_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                                    floor_para.paragraph_format.space_before = Pt(0)
                                    floor_para.paragraph_format.space_after = Pt(2)
                                    floor_para.paragraph_format.line_spacing = 0.9
                                    floor_para.paragraph_format.left_indent = INDENTED_CONTENT_LEFT_INDENT

                                    floor_text = f"The {floor_name} comprises {format_list_with_grammar(room_parts)}."

                                    floor_run = floor_para.add_run(floor_text)
                                    floor_run.font.size = Pt(9)
                                    floor_run.font.color.rgb = RGBColor(0, 0, 0)

                            # OLD FORMAT: Backward compatibility for old data without accommodation_summary
                            else:
                                rooms = floor.get('rooms', [])
                                if rooms:
                                    floor_rooms = []
                                    floor_total_area = 0

                                    for room in rooms:
                                        room_name = room.get('room_name', 'Room')
                                        room_count = room.get('count', 1)
                                        room_length = room.get('length')
                                        room_width = room.get('width')

                                        # Calculate room area if dimensions provided
                                        if room_length and room_width:
                                            room_area = float(room_length) * float(room_width)
                                            floor_total_area += room_area * room_count
                                            if room_count > 1:
                                                floor_rooms.append(f"{room_count} {room_name}s: {room_area:.0f} square feet each")
                                            else:
                                                floor_rooms.append(f"{room_name}: {room_area:.0f} square feet")
                                        else:
                                            if room_count > 1:
                                                floor_rooms.append(f"{room_count} {room_name}s")
                                            else:
                                                floor_rooms.append(room_name)

                                    if floor_rooms:
                                        # Add floor paragraph with indentation
                                        floor_para = doc.add_paragraph()
                                        floor_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                                        floor_para.paragraph_format.space_before = Pt(0)
                                        floor_para.paragraph_format.space_after = Pt(2)
                                        floor_para.paragraph_format.line_spacing = 0.9
                                        floor_para.paragraph_format.left_indent = INDENTED_CONTENT_LEFT_INDENT

                                        floor_text = f"{floor_name}: {', '.join(floor_rooms)}"

                                        floor_run = floor_para.add_run(floor_text)
                                        floor_run.font.size = Pt(9)
                                        floor_run.font.color.rgb = RGBColor(0, 0, 0)

                    # === CONVENIENCES ===
                    conveniences = building.get('conveniences', [])
                    if conveniences:
                        conv_heading = doc.add_paragraph()
                        conv_heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        conv_heading.paragraph_format.space_before = SUBHEADING_SPACE_BEFORE
                        conv_heading.paragraph_format.space_after = SUBHEADING_SPACE_AFTER
                        conv_heading.paragraph_format.line_spacing = 0.9
                        conv_run = conv_heading.add_run("Conveniences")
                        conv_run.bold = True
                        conv_run.font.size = Pt(9)
                        conv_run.font.color.rgb = RGBColor(0, 0, 0)

                        conv_para = doc.add_paragraph()
                        conv_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        conv_para.paragraph_format.space_before = Pt(0)
                        conv_para.paragraph_format.space_after = Pt(2)
                        conv_para.paragraph_format.line_spacing = 0.9
                        conv_para.paragraph_format.left_indent = INDENTED_CONTENT_LEFT_INDENT

                        conv_labels = {
                            'electricity': 'Electricity', 'water': 'Water service by well',
                            'pipe_water': 'Pipe-borne water', 'telephone': 'Telephone',
                            'internet': 'Internet', 'ac': 'Air conditioning',
                            'hot_water': 'Hot water', 'sewage': 'Sewage system',
                            'septic': 'Septic tank', 'gas': 'Gas connection',
                            'solar': 'Solar panels', 'generator': 'Generator backup'
                        }
                        conv_list = [conv_labels.get(c, c.replace('_', ' ').title()) for c in conveniences]
                        conv_para.add_run(", ".join(conv_list) + ".").font.size = Pt(9)

                    # === FLOOR AREA (STRUCTURED BREAKDOWN FORMAT) ===
                    floors = building.get('floors', [])
                    total_area = building.get('total_floor_area', 0)
                    if floors and (total_area or any(f.get('floor_area', 0) > 0 for f in floors)):
                        # Add "Floor Area" label (bold, inline)
                        floor_area_para = doc.add_paragraph()
                        floor_area_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        floor_area_para.paragraph_format.space_before = INLINE_FIELD_SPACE_BEFORE
                        floor_area_para.paragraph_format.space_after = Pt(2)
                        floor_area_para.paragraph_format.line_spacing = 0.9

                        label_run = floor_area_para.add_run("Floor area:")
                        label_run.bold = True
                        label_run.font.size = Pt(9)
                        label_run.font.color.rgb = RGBColor(0, 0, 0)

                        # Add each floor's area (indented)
                        for floor in floors:
                            floor_name = floor.get('floor_name', 'Floor')
                            floor_area = floor.get('floor_area', 0)

                            if floor_area and floor_area > 0:
                                floor_line_para = doc.add_paragraph()
                                floor_line_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                                floor_line_para.paragraph_format.space_before = Pt(0)
                                floor_line_para.paragraph_format.space_after = Pt(1)
                                floor_line_para.paragraph_format.line_spacing = 0.9
                                floor_line_para.paragraph_format.left_indent = Inches(0.5)

                                floor_line_run = floor_line_para.add_run(f"{floor_name}: {floor_area:,.0f} square feet")
                                floor_line_run.font.size = Pt(9)
                                floor_line_run.font.color.rgb = RGBColor(0, 0, 0)

                        # Add total (indented)
                        if total_area and total_area > 0:
                            total_para = doc.add_paragraph()
                            total_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            total_para.paragraph_format.space_before = Pt(0)
                            total_para.paragraph_format.space_after = INLINE_FIELD_SPACE_AFTER
                            total_para.paragraph_format.line_spacing = 0.9
                            total_para.paragraph_format.left_indent = Inches(0.5)

                            total_run = total_para.add_run(f"Total: {total_area:,.0f} square feet")
                            total_run.bold = True
                            total_run.font.size = Pt(9)
                            total_run.font.color.rgb = RGBColor(0, 0, 0)

                    # === AGE AND CONDITION (INLINE FORMAT) ===
                    age_desc = building.get('age_description', '')
                    condition = building.get('condition', '')
                    if age_desc or condition:
                        condition_labels = {
                            'excellent': 'excellent',
                            'good': 'good',
                            'fair': 'fair',
                            'poor': 'poor',
                            'dilapidated': 'dilapidated'
                        }

                        parts = []
                        if age_desc:
                            parts.append(f"{age_desc} old")
                        if condition:
                            parts.append(f"condition is {condition_labels.get(condition, condition)}")

                        age_text = "; ".join(parts) + "." if parts else "Information not provided."

                        add_inline_field(doc, "Age and condition", age_text)

                    # === UTILITIES AND SERVICES ===
                    render_utilities_services(doc, building)

                    # === OCCUPATION (SENTENCE FORMAT WITH SUBHEADING) ===
                    if report.occupier_name:
                        occupier_text = f"The property is occupied by {report.occupier_name}"
                        if report.occupier_relationship:
                            rel_labels = {
                                'owner': 'the owner',
                                'tenant': 'a tenant',
                                'family_member': 'a family member',
                                'caretaker': 'caretaker'
                            }
                            occupier_text += f" who is {rel_labels.get(report.occupier_relationship, report.occupier_relationship)}"
                        occupier_text += "."

                        add_inline_field(
                            doc,
                            "Occupation",
                            occupier_text,
                            space_after=Pt(6)
                        )

                    # === BUILDING PHOTOS (3-column grid layout - NO SUBHEADING) ===
                    building_photos = building.get('building_photos', [])
                    if building_photos and len(building_photos) > 0:
                        # Sort photos by order
                        sorted_photos = sorted(building_photos, key=lambda x: x.get('order', 0))

                        # Modern flexible photo grid layout using tables for proper caption alignment
                        import base64
                        import re
                        import math

                        num_photos = len(sorted_photos)
                        photos_per_row = 3

                        # Process photos in rows
                        idx = 0
                        while idx < num_photos:
                            # Determine how many photos in this row
                            remaining = num_photos - idx
                            if remaining >= photos_per_row:
                                photos_in_row = photos_per_row
                            elif remaining == 1 and idx > 0:
                                # Last single photo - center it
                                photos_in_row = 1
                            else:
                                # 2 photos or first row - use all remaining
                                photos_in_row = remaining

                            # Create a table for this row of photos with captions
                            table = doc.add_table(rows=2, cols=photos_in_row)
                            table.alignment = WD_TABLE_ALIGNMENT.CENTER

                            # Remove table borders
                            for row in table.rows:
                                for cell in row.cells:
                                    cell.width = Inches(6.5 / photos_in_row)
                                    # Remove all borders
                                    tc = cell._element
                                    tcPr = tc.get_or_add_tcPr()
                                    tcBorders = parse_xml(
                                        r'<w:tcBorders %s>'
                                        r'<w:top w:val="none"/>'
                                        r'<w:left w:val="none"/>'
                                        r'<w:bottom w:val="none"/>'
                                        r'<w:right w:val="none"/>'
                                        r'</w:tcBorders>' % nsdecls('w')
                                    )
                                    tcPr.append(tcBorders)

                            # Add photos to first row of table
                            for i in range(photos_in_row):
                                if idx >= num_photos:
                                    break

                                photo = sorted_photos[idx]
                                try:
                                    image_data = photo.get('image_data', '')
                                    caption = photo.get('caption', '')

                                    if not image_data or not image_data.startswith('data:image'):
                                        idx += 1
                                        continue

                                    # Decode base64 image
                                    base64_match = re.search(r'base64,(.+)', image_data)
                                    if not base64_match:
                                        idx += 1
                                        continue

                                    base64_data = base64_match.group(1)
                                    image_bytes = base64.b64decode(base64_data)
                                    image_stream = BytesIO(image_bytes)

                                    # Use uniform 2-inch width for all photos
                                    img_width = Inches(2.0)

                                    dimensions = calculate_image_dimensions(
                                        image_stream,
                                        img_width,
                                        PROPERTY_PHOTO_HEIGHT
                                    )

                                    # Add image to table cell
                                    image_stream.seek(0)
                                    cell = table.rows[0].cells[i]
                                    cell_para = cell.paragraphs[0]
                                    cell_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    cell_para.add_run().add_picture(image_stream, **dimensions)

                                    # Add caption to second row
                                    caption_cell = table.rows[1].cells[i]
                                    caption_para = caption_cell.paragraphs[0]
                                    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    caption_para.paragraph_format.space_before = Pt(2)
                                    caption_para.paragraph_format.space_after = Pt(2)

                                    caption_text = f"Fig. {idx + 1}"
                                    if caption:
                                        caption_text += f": {caption}"

                                    caption_run = caption_para.add_run(caption_text)
                                    caption_run.font.size = Pt(7)
                                    caption_run.font.italic = True
                                    caption_run.font.color.rgb = RGBColor(60, 60, 60)

                                    print(f"[DOCX] Added building photo {idx + 1} for {building_name}")

                                except Exception as e:
                                    print(f"[DOCX] Error adding photo {idx + 1}: {str(e)}")

                                idx += 1

                            # Add spacing after photo table
                            spacing_para = doc.add_paragraph()
                            spacing_para.paragraph_format.space_after = Pt(8)

                        # Add final spacing after all photos
                        final_spacing = doc.add_paragraph()
                        final_spacing.paragraph_format.space_after = IMAGE_SPACING_AFTER

                    # === ADDITIONAL STRUCTURES ===
                    additional_structures = building.get('additional_structures_description', '')
                    if additional_structures and additional_structures.strip():
                        # Add subheading
                        add_structures_heading = doc.add_paragraph()
                        add_structures_heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        add_structures_heading.paragraph_format.space_before = SUBHEADING_SPACE_BEFORE
                        add_structures_heading.paragraph_format.space_after = SUBHEADING_SPACE_AFTER
                        add_structures_heading.paragraph_format.line_spacing = 0.9
                        add_structures_run = add_structures_heading.add_run("Additional Structures")
                        add_structures_run.bold = True
                        add_structures_run.font.size = Pt(9)
                        add_structures_run.font.color.rgb = RGBColor(0, 0, 0)

                        # Add description paragraph
                        structures_para = doc.add_paragraph()
                        structures_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        structures_para.paragraph_format.space_before = Pt(0)
                        structures_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                        structures_para.paragraph_format.line_spacing = 0.9
                        structures_para.paragraph_format.left_indent = INDENTED_CONTENT_LEFT_INDENT

                        structures_run = structures_para.add_run(additional_structures.strip())
                        structures_run.font.size = Pt(9)
                        structures_run.font.color.rgb = RGBColor(0, 0, 0)

        # ===== 5.0 LOCALITY SECTION (Moved to last position) =====
        if locality_text:
            # Add numbered section heading
            add_section_heading(doc, "5.0", "LOCALITY")

            # LOCALITY text (now a single concise paragraph from updated AI prompt)
            locality_para = doc.add_paragraph()
            locality_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            locality_para.paragraph_format.space_before = Pt(0)
            locality_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            locality_para.paragraph_format.line_spacing = 0.9
            locality_run = locality_para.add_run(locality_text)
            locality_run.font.size = Pt(9)
            locality_run.font.color.rgb = RGBColor(0, 0, 0)

        # ===== 6.0 LEGAL ASPECTS =====
        # Show section if any legal aspect data exists (including new extended fields)
        has_legal_data = (
            report.ownership_type or report.street_lines_status or report.building_limits_status or
            report.local_authority_data or report.rent_act_effectiveness or
            # Extended fields
            report.title_search_conducted or report.property_encumbered or
            report.street_lines_gazette_ref or report.building_plan_approved or
            report.local_authority_rated
        )

        if has_legal_data:
            add_section_heading(doc, "6.0", "LEGAL ASPECTS")

            # (a) Ownership - Generate professional paragraph
            if report.ownership_type or hasattr(report, 'deeds') or hasattr(report, 'plan_number'):
                ownership_para = generate_ownership_paragraph(report)
                add_subsection_paragraph(doc, "(a)", "Ownership", ownership_para)

            # (b) Street lines - Generate contextual paragraph
            if report.street_lines_status:
                street_para = generate_street_lines_paragraph(report)
                add_subsection_paragraph(doc, "(b)", "Street lines", street_para)

            # (c) Building limits - Generate detailed paragraph
            if report.building_limits_status:
                building_para = generate_building_limits_paragraph(report)
                add_subsection_paragraph(doc, "(c)", "Building limits", building_para)

            # (d) Local authority data - Generate administrative paragraph
            if report.local_authority_data or report.pradeshiya_sabha or report.local_authority_rated:
                authority_para = generate_local_authority_paragraph(report)
                add_subsection_paragraph(doc, "(d)", "Local authority data", authority_para)

            # (e) Rent act effectiveness - Generate regulation paragraph
            if report.rent_act_effectiveness:
                rent_para = generate_rent_act_paragraph(report)
                add_subsection_paragraph(doc, "(e)", "Rent act effectiveness", rent_para)

            doc.add_paragraph()  # Spacing

        # ===== 7.0 LAND VALUES IN THE AREA =====
        if report.comparable_properties:
            add_section_heading(doc, "7.0", "LAND VALUES IN THE AREA")

            # Parse JSON if needed
            # SAFE: Parse JSON with error handling
            comparables = safe_parse_json_string(report.comparable_properties, [])

            if comparables:
                # Generate paragraph from comparables
                land_values_text = generate_land_values_paragraph(comparables)

                if land_values_text:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.space_after = Pt(6)
                    run = p.add_run(land_values_text)
                    run.font.size = Pt(9)

                    # Add average rate note
                    avg_rate = sum(c.get('rate_per_perch', 0) for c in comparables) / len(comparables) if comparables else 0
                    if avg_rate > 0:
                        p = doc.add_paragraph()
                        p.paragraph_format.space_before = Pt(6)
                        p.paragraph_format.space_after = Pt(6)
                        run = p.add_run(f"Average Rate: LKR {avg_rate:,.2f} per perch")
                        run.font.bold = True
                        run.font.size = Pt(9)

            if report.land_market_analysis:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.space_after = Pt(12)
                run = p.add_run(report.land_market_analysis)
                run.font.size = Pt(9)

            doc.add_paragraph()

        # ===== 8.0 VALUATION =====
        if report.valuation_total_land_value or report.valuation_buildings_data:
            add_section_heading(doc, "8.0", "VALUATION OF THE PROPERTY")

            # === VALUATION BREAKDOWN ===

            # Land valuation line
            if report.valuation_total_land_value:
                extent = report.valuation_land_extent or report.land_extent_perches or 0
                rate = report.valuation_rate_per_perch or 0
                land_value = report.valuation_total_land_value

                p = doc.add_paragraph()
                text = f"Land – {extent:,.2f} perches @ {format_currency(rate)} per perch = {format_currency(land_value)}"
                run = p.add_run(text)
                run.font.size = Pt(10)
                p.paragraph_format.space_after = Pt(4)

            # Buildings valuation
            total_depreciated_buildings_value = 0
            buildings_insurance_values = []  # Store per-building insurance values

            if report.valuation_buildings_data:
                # SAFE: Parse JSON with error handling
                buildings_data = safe_parse_json_string(report.valuation_buildings_data, [])

                for idx, bldg in enumerate(buildings_data, 1):
                    building_name = bldg.get('building_name', f'Building {idx}')
                    subtotal = bldg.get('subtotal', 0)

                    # Calculate total floor area from components
                    components = bldg.get('components', [])
                    total_floor_area = sum(comp.get('floor_area', 0) for comp in components)

                    # Calculate average rate per sq.ft
                    avg_rate = subtotal / total_floor_area if total_floor_area > 0 else 0

                    # Building main line
                    p = doc.add_paragraph()
                    text = f"{building_name} – {total_floor_area:,.0f} sq.ft @ {format_currency(avg_rate)} per square foot = {format_currency(subtotal)}"
                    run = p.add_run(text)
                    run.font.size = Pt(10)
                    p.paragraph_format.space_after = Pt(2)

                    # Check if depreciation data exists
                    has_depreciation = bldg.get('depreciation_amount') is not None and to_float(bldg.get('depreciation_amount', 0)) > 0

                    if has_depreciation:
                        # Show depreciation breakdown
                        depreciation_rate = to_float(bldg.get('depreciation_rate_percent', 0))
                        depreciation_amount = to_float(bldg.get('depreciation_amount', 0))
                        depreciated_value = to_float(bldg.get('depreciated_value', subtotal))

                        # Depreciation line
                        p_dep = doc.add_paragraph()
                        p_dep.paragraph_format.left_indent = Inches(0.3)
                        text_dep = f"Less: Depreciation @ {depreciation_rate:.2f}% = {format_currency(depreciation_amount)}"
                        run_dep = p_dep.add_run(text_dep)
                        run_dep.font.size = Pt(9)
                        run_dep.font.color.rgb = RGBColor(0, 0, 0)  # Black color
                        p_dep.paragraph_format.space_after = Pt(2)

                        # Depreciated value line
                        p_val = doc.add_paragraph()
                        p_val.paragraph_format.left_indent = Inches(0.3)
                        text_val = f"Depreciated Value = {format_currency(depreciated_value)}"
                        run_val = p_val.add_run(text_val)
                        run_val.font.size = Pt(9)
                        run_val.font.bold = True
                        run_val.font.color.rgb = RGBColor(0, 0, 0)  # Black color
                        p_val.paragraph_format.space_after = Pt(6)

                        building_value = depreciated_value
                    else:
                        # Use replacement cost directly (no depreciation) - backward compatible
                        building_value = to_float(subtotal)

                    total_depreciated_buildings_value += building_value
                    # Insurance always uses replacement cost (undepreciated)
                    buildings_insurance_values.append({
                        'name': building_name,
                        'value': to_float(subtotal)  # Replacement cost for insurance
                    })

            # Add-ons
            total_addons_value = 0
            if report.valuation_addons:
                # SAFE: Parse JSON with error handling
                addons = safe_parse_json_string(report.valuation_addons, [])

                if addons:
                    p = doc.add_paragraph()
                    run = p.add_run("Add-ons:")
                    run.font.size = Pt(10)
                    p.paragraph_format.space_before = Pt(6)
                    p.paragraph_format.space_after = Pt(3)

                    for addon in addons:
                        p = doc.add_paragraph()
                        p.paragraph_format.left_indent = Inches(0.2)
                        text = f"- {addon.get('description', '')} = {format_currency(addon.get('value', 0))}"
                        run = p.add_run(text)
                        run.font.size = Pt(10)
                        p.paragraph_format.space_after = Pt(2)
                        total_addons_value += to_float(addon.get('value', 0))

                    doc.add_paragraph()  # Spacing

            # Calculate Open Market Value
            land_value = to_float(report.valuation_total_land_value)
            market_value_calculated = land_value + to_float(total_depreciated_buildings_value) + to_float(total_addons_value)
            market_value_rounded = round_for_say(market_value_calculated)

            # Open Market Value with "Say"
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)

            # Add tab stop at 6 inches for right alignment
            tab_stops = p.paragraph_format.tab_stops
            tab_stops.add_tab_stop(Inches(6.0), WD_TAB_ALIGNMENT.RIGHT)

            # Add text with tab character for proper alignment
            text = f"Open Market Value of the property\tSay = {format_currency(market_value_rounded)}"
            run = p.add_run(text)
            run.font.bold = True
            run.font.size = Pt(9)
            p.paragraph_format.space_after = Pt(18)

            # === REMARKS & CONCLUSION ===
            p = doc.add_paragraph()
            run = p.add_run("REMARKS & CONCLUSION")
            run.font.bold = True
            run.font.underline = True
            run.font.size = Pt(9)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)

            forced_sale_percentage = report.valuation_forced_sale_percentage or 90
            forced_sale_value = market_value_rounded * (forced_sale_percentage / 100)

            remarks_text = (
                f"In my opinion, the Current Open Market Value of the property is a sum of "
                f"{format_currency(market_value_rounded)} only, free of all encumbrances and considering the "
                f"real estate market behavior in the locality I place the Forced Sale Value "
                f"of the property at {forced_sale_percentage:.0f}% which is {format_currency(forced_sale_value)} only."
            )

            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run = p.add_run(remarks_text)
            run.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(18)

            # === SUMMARY OF THE VALUATION ===
            p = doc.add_paragraph()
            run = p.add_run("SUMMARY OF THE VALUATION")
            run.font.bold = True
            run.font.underline = True
            run.font.size = Pt(9)
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)

            # Open Market Value
            p = doc.add_paragraph()
            tab_stops = p.paragraph_format.tab_stops
            tab_stops.add_tab_stop(Inches(3.5), WD_TAB_ALIGNMENT.LEFT)
            tab_stops.add_tab_stop(Inches(3.7), WD_TAB_ALIGNMENT.LEFT)
            text = f"Open Market Value of the property\t:\t{format_currency(market_value_rounded)}"
            run = p.add_run(text)
            run.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(3)

            # Forced Sale Value
            p = doc.add_paragraph()
            tab_stops = p.paragraph_format.tab_stops
            tab_stops.add_tab_stop(Inches(3.5), WD_TAB_ALIGNMENT.LEFT)
            tab_stops.add_tab_stop(Inches(3.7), WD_TAB_ALIGNMENT.LEFT)
            text = f"Forced Sale Value of the property\t:\t{format_currency(forced_sale_value)}"
            run = p.add_run(text)
            run.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(3)

            # Insurance Value (per building)
            p = doc.add_paragraph()
            run = p.add_run("Insurance Value")
            run.font.size = Pt(10)
            p.paragraph_format.space_after = Pt(2)

            for building_ins in buildings_insurance_values:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.3)
                tab_stops = p.paragraph_format.tab_stops
                tab_stops.add_tab_stop(Inches(3.2), WD_TAB_ALIGNMENT.LEFT)
                tab_stops.add_tab_stop(Inches(3.4), WD_TAB_ALIGNMENT.LEFT)
                text = f"{building_ins['name']}\t:\t{format_currency(building_ins['value'])}"
                run = p.add_run(text)
                run.font.size = Pt(10)
                p.paragraph_format.space_after = Pt(2)

            doc.add_paragraph()  # Final spacing

        # ===== 9.0 CERTIFICATION =====
        if report.certification_text or report.certification_valuer_name:
            add_section_heading(doc, "9.0", "CERTIFICATION")

            # Certification text (multi-paragraph)
            if report.certification_text:
                for paragraph_text in report.certification_text.split('\n\n'):
                    if paragraph_text.strip():
                        p = doc.add_paragraph()
                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        p.paragraph_format.space_after = Pt(6)
                        run = p.add_run(paragraph_text.strip())
                        run.font.size = Pt(9)

            # Certificate of Identity
            if report.certificate_survey_plan_ref:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)

                run = p.add_run("\nCertificate of Identity:\n")
                run.font.bold = True
                run.font.size = Pt(9)

                run = p.add_run(f"I certify that the property inspected by me is identical to the property described in ")
                run.font.size = Pt(9)

                # Add deed reference if available
                deeds = safe_get_json_field(report, 'deeds', [])
                has_deed = isinstance(deeds, list) and len(deeds) > 0
                if has_deed:
                    deed = deeds[0]
                    deed_number = deed.get('deed_number', '') if isinstance(deed, dict) else getattr(deed, 'deed_number', '')
                    deed_type = deed.get('deed_type', 'deed') if isinstance(deed, dict) else getattr(deed, 'deed_type', 'deed')
                    deed_date = deed.get('deed_date', '') if isinstance(deed, dict) else getattr(deed, 'deed_date', '')

                    if deed_number:
                        run = p.add_run(f"{deed_type} No. {deed_number}")
                        run.font.bold = True
                        run.font.size = Pt(9)

                        if deed_date:
                            run = p.add_run(f" dated {deed_date}")
                            run.font.size = Pt(9)

                        run = p.add_run(" and identified in ")
                        run.font.size = Pt(9)

                # Add plan reference
                run = p.add_run(f"{report.certificate_survey_plan_ref}")
                run.font.bold = True
                run.font.size = Pt(9)

                if report.certificate_survey_plan_date:
                    run = p.add_run(f" dated {report.certificate_survey_plan_date}")
                    run.font.size = Pt(9)

                run = p.add_run(".")
                run.font.size = Pt(9)

            # Signature block
            doc.add_paragraph("\n\n")

            p = doc.add_paragraph("_" * 40)  # Signature line
            p.paragraph_format.space_before = Pt(24)

            if report.certification_valuer_name:
                p = doc.add_paragraph()
                run = p.add_run(report.certification_valuer_name)
                run.font.bold = True
                run.font.size = Pt(9)

            if report.certification_valuer_designation:
                p = doc.add_paragraph(report.certification_valuer_designation)
                for run in p.runs:
                    run.font.size = Pt(9)

            if report.certification_date:
                p = doc.add_paragraph(report.certification_date)
                for run in p.runs:
                    run.font.size = Pt(9)

            doc.add_paragraph()

        # ===== SAVE DOCUMENT =====
        # This MUST be outside the certification block!
        logger.info("[DOCX] About to save document to BytesIO")
        # Save to BytesIO
        file_stream = BytesIO()
        logger.info("[DOCX] Created BytesIO stream")
        doc.save(file_stream)
        logger.info("[DOCX] Document saved to stream")
        file_stream.seek(0)
        logger.info("[DOCX] Stream position reset to 0")

        # Safety check
        if file_stream is None or file_stream.getvalue() == b'':
            raise ValueError("Generated document is empty or None")

        logger.info(f"Document generated successfully, size: {len(file_stream.getvalue())} bytes")
        return file_stream

    except AttributeError as e:
        logger.error(f"Missing required field in report generation: {e}", exc_info=True)
        raise ValueError(f"Report data incomplete: Missing field - {str(e)}")
    except IndexError as e:
        logger.error(f"Array access error in report generation: {e}", exc_info=True)
        raise ValueError(f"Report data malformed: Array indexing error - {str(e)}")
    except TypeError as e:
        logger.error(f"Type error in report data: {e}", exc_info=True)
        raise ValueError(f"Report data has incorrect types: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in DOCX generation: {e}", exc_info=True)
        raise

def get_filename_for_user(report: models.Report) -> str:
    """Generate a safe filename for the report document"""
    # Use applicant name if available, otherwise use valuer name
    name = report.applicant_full_name if report.applicant_full_name else report.user.full_name
    # Clean the name for use in filename
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_type = report.report_type.replace('_', '-')
    return f"{report_type}_{safe_name}_{timestamp}.docx"
