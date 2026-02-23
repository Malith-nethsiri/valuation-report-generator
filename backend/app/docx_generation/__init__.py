from .helpers import (
    to_float,
    safe_get_json_field,
    safe_get_array_item,
    safe_parse_json_string,
    safe_get_nested,
)
from .formatting import (
    format_material_list,
    format_currency,
    format_currency_words,
    format_currency_aligned,
    format_room_count,
    round_for_say,
)
from .styling import (
    add_border_to_paragraph,
    MAP_IMAGE_WIDTH ,
    MAP_IMAGE_MAX_HEIGHT,
    PROPERTY_PHOTO_WIDTH,
    PROPERTY_PHOTO_HEIGHT,
    IMAGE_SPACING_BEFORE,
    IMAGE_SPACING_AFTER ,
    MAJOR_SECTION_SPACE_BEFORE ,
    MAJOR_SECTION_SPACE_AFTER ,

    SUBSECTION_SPACE_BEFORE ,
    SUBSECTION_SPACE_AFTER ,

    BODY_PARA_SPACE_BEFORE ,
    BODY_PARA_SPACE_AFTER ,

    INLINE_FIELD_SPACE_BEFORE ,
    INLINE_FIELD_SPACE_AFTER ,

    SUBHEADING_SPACE_BEFORE ,
    SUBHEADING_SPACE_AFTER ,

    INDENTED_CONTENT_SPACE_BEFORE ,
    INDENTED_CONTENT_SPACE_AFTER ,
    INDENTED_CONTENT_LEFT_INDENT ,

    BOUNDARY_LIST_SPACE_AFTER ,
    ACCOMMODATION_ROOM_SPACE_AFTER,

    FONT_SIZE_DOCUMENT_TITLE ,
    FONT_SIZE_SECTION_HEADING ,
    FONT_SIZE_SUBSECTION_HEADING ,

    FONT_SIZE_BODY ,
    FONT_SIZE_INLINE_LABEL,
    FONT_SIZE_VALUATION ,

    FONT_SIZE_TABLE_HEADER,
    FONT_SIZE_TABLE_CELL ,
    FONT_SIZE_INVOICE_TOTAL ,

    FONT_SIZE_CAPTION ,
    FONT_SIZE_BANK_HEADER,
    FONT_SIZE_BANK_DETAILS,
    FONT_SIZE_SIGNATURE,
    FONT_SIZE_CERTIFICATION,
)
from .images import calculate_image_dimensions, apply_letterbox_to_image

from .paragraph_builders import (
    add_section_heading, format_building_valuation_2line,
    add_market_value_line, add_value_rounded_line, format_addon_compact,
    add_inline_field, add_subsection_paragraph
)

__all__ = [
    "to_float", "safe_get_json_field", "safe_get_array_item", "safe_parse_json_string", "safe_get_nested",
    "format_material_list", "format_currency", "format_currency_words", "format_currency_aligned",
    "format_room_count", "round_for_say",
    "add_border_to_paragraph", "calculate_image_dimensions", "apply_letterbox_to_image",
    "add_section_heading", "format_building_valuation_2line", "add_market_value_line",
    "add_value_rounded_line", "format_addon_compact", "add_inline_field", "add_subsection_paragraph",
    # New submodule generators
    "generate_single_property_docx", "generate_multi_property_report_docx",
    "generate_vehicle_report_docx", "generate_property_sections", "generate_invoice_section",
]

# Lazy imports of new generator modules (avoid circular imports at package load time)
def generate_single_property_docx(report, user=None):
    from .single_property_generator import generate_single_property_docx as _fn
    return _fn(report, user)

def generate_multi_property_report_docx(report, user=None):
    from .multi_property_generator import generate_multi_property_report_docx as _fn
    return _fn(report, user)

def generate_vehicle_report_docx(report, user=None):
    from .vehicle_generator import generate_vehicle_report_docx as _fn
    return _fn(report, user)

def generate_property_sections(doc, prop, report, user):
    from .property_section_generator import generate_property_sections as _fn
    return _fn(doc, prop, report, user)

def generate_invoice_section(doc, invoice_data, user, report=None):
    from .invoice_generator import generate_invoice_section as _fn
    return _fn(doc, invoice_data, user, report)
