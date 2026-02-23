"""
Single-property valuation report DOCX generation body.
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from io import BytesIO
from datetime import datetime
from typing import Any, List, Dict, Optional, Union
import requests
from .. import models
from ..utils import append_label_if_missing, clean_spelling_errors, format_no_field
from ..letterhead_templates import get_template
import logging

from .formatting import (
    format_currency, format_currency_words, format_currency_aligned,
    format_room_count, round_for_say, format_material_list,
)
from .paragraph_builders import (
    add_section_heading, add_market_value_line, add_value_rounded_line,
    add_inline_field, add_subsection_paragraph, format_building_valuation_2line, format_addon_compact,
)
from .styling import (
    add_border_to_paragraph,
    MAP_IMAGE_WIDTH, MAP_IMAGE_MAX_HEIGHT, PROPERTY_PHOTO_WIDTH, PROPERTY_PHOTO_HEIGHT,
    IMAGE_SPACING_BEFORE, IMAGE_SPACING_AFTER, MAJOR_SECTION_SPACE_BEFORE, MAJOR_SECTION_SPACE_AFTER,
    SUBSECTION_SPACE_BEFORE, SUBSECTION_SPACE_AFTER, BODY_PARA_SPACE_BEFORE, BODY_PARA_SPACE_AFTER,
    INLINE_FIELD_SPACE_BEFORE, INLINE_FIELD_SPACE_AFTER, SUBHEADING_SPACE_BEFORE, SUBHEADING_SPACE_AFTER,
    INDENTED_CONTENT_SPACE_BEFORE, INDENTED_CONTENT_SPACE_AFTER, INDENTED_CONTENT_LEFT_INDENT,
    BOUNDARY_LIST_SPACE_AFTER, ACCOMMODATION_ROOM_SPACE_AFTER,
    FONT_SIZE_DOCUMENT_TITLE, FONT_SIZE_SECTION_HEADING, FONT_SIZE_SUBSECTION_HEADING,
    FONT_SIZE_BODY, FONT_SIZE_INLINE_LABEL, FONT_SIZE_VALUATION,
    FONT_SIZE_TABLE_HEADER, FONT_SIZE_TABLE_CELL, FONT_SIZE_INVOICE_TOTAL,
    FONT_SIZE_CAPTION, FONT_SIZE_BANK_HEADER, FONT_SIZE_BANK_DETAILS,
    FONT_SIZE_SIGNATURE, FONT_SIZE_CERTIFICATION,
)
from .images import calculate_image_dimensions, apply_letterbox_to_image
from .helpers import (
    safe_get_json_field, safe_get_array_item, to_float, safe_parse_json_string, safe_get_nested,
)

logger = logging.getLogger(__name__)
Deed_Type = Union[Dict[str, Any], Any]

from .invoice_generator import generate_invoice_section
from .text_generators import (
    generate_ownership_paragraph, generate_street_lines_paragraph,
    generate_building_limits_paragraph, generate_local_authority_paragraph,
    generate_rent_act_paragraph, _synthesize_location_context,
    generate_land_values_paragraph, generate_simplified_certification_text,
    generate_certificate_of_identity_text, add_signature_block, get_pronoun,
    generate_title_block, generate_applicant_statement,
    generate_organization_side_introduction, generate_multi_property_concluding_statement,
    generate_deed_description, generate_submission_statement, generate_situation_text,
    generate_smart_address, generate_access_text, generate_locality_description,
    generate_boundary_summary_text, format_list_with_grammar,
)
from .building_renderer import (
    aggregate_accommodation_across_building, deduplicate_water_sources,
    render_construction_details, render_utilities_and_conveniences,
)

def generate_single_property_docx(report: models.Report, user: Optional[models.User] = None) -> BytesIO:
    """
    Generate a formatted DOCX file for a single-property valuation report.
    Called by generate_user_data_docx dispatcher after routing.
    """
    try:

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

            # Remove spacing between property description lines (lines 2 and 3)
            if i == 2 or i == 3:  # Property description lines
                para.paragraph_format.line_spacing = 1.0  # Single line spacing, no gap
            else:
                para.paragraph_format.line_spacing = 0.9

            run = para.add_run(line)
            if i == 0:  # "VALUATION REPORT"
                run.bold = True
                run.font.size = Pt(14)  # Updated from 11 to 14
                run.font.underline = True  # Add underline
            elif i == 2 or i == 3:  # Both property description lines
                run.bold = True
                run.font.size = FONT_SIZE_BODY
                run.font.underline = True  # Add underline for continuous block effect
            else:
                run.font.size = FONT_SIZE_BODY
                if i == 1:  # "of" line
                    run.font.underline = True  # Add underline for continuous block effect
            run.font.color.rgb = RGBColor(0, 0, 0)

        # Add spacing before applicant statements
        spacing_para1 = doc.add_paragraph()
        spacing_para1.paragraph_format.space_before = Pt(8)
        spacing_para1.paragraph_format.space_after = Pt(0)

        # Determine which introduction format to use based on request_type
        if report.request_type == 'organization_request':
            # Organization-side format
            org_intro_paragraphs = generate_organization_side_introduction(report)
            for statement in org_intro_paragraphs:
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                para.paragraph_format.line_spacing = 0.9

                # Parse label and value for proper formatting
                if ":-" in statement:
                    # This is a label-value pair (Applicant/Address/Contact No)
                    label, value = statement.split(":-", 1)

                    # Add bold label
                    run_label = para.add_run(label.strip())
                    run_label.font.size = FONT_SIZE_BODY
                    run_label.font.bold = True
                    run_label.font.color.rgb = RGBColor(0, 0, 0)

                    # Add separator with proper spacing
                    run_sep = para.add_run(" : ")
                    run_sep.font.size = FONT_SIZE_BODY
                    run_sep.font.color.rgb = RGBColor(0, 0, 0)

                    # Add value
                    run_value = para.add_run(value)
                    run_value.font.size = FONT_SIZE_BODY
                    run_value.font.color.rgb = RGBColor(0, 0, 0)
                else:
                    # This is the introductory paragraph (paragraph 1)
                    run = para.add_run(statement)
                    run.font.size = FONT_SIZE_BODY
                    run.font.color.rgb = RGBColor(0, 0, 0)
        else:
            # Client-side format (default for backward compatibility)
            applicant_statements = generate_applicant_statement(report)
            for statement in applicant_statements:
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                para.paragraph_format.line_spacing = 0.9
                run = para.add_run(statement)
                run.font.size = FONT_SIZE_BODY
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
                    run.font.size = FONT_SIZE_BODY
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
                run.font.size = FONT_SIZE_BODY
                run.font.color.rgb = RGBColor(0, 0, 0)

        # Add inspection date
        if report.inspection_date:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            para.paragraph_format.space_before = Pt(6)
            para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            para.paragraph_format.line_spacing = 0.9

            # Bold label
            run_label = para.add_run("Date of Inspection:")
            run_label.font.size = FONT_SIZE_BODY
            run_label.font.bold = True
            run_label.font.color.rgb = RGBColor(0, 0, 0)

            # Regular date value
            run_date = para.add_run(f" {report.inspection_date}")
            run_date.font.size = FONT_SIZE_BODY
            run_date.font.color.rgb = RGBColor(0, 0, 0)

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
            run.font.size = FONT_SIZE_BODY
            run.font.color.rgb = RGBColor(0, 0, 0)

            # Note text
            note_para = doc.add_paragraph()
            note_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            note_para.paragraph_format.space_before = Pt(0)
            note_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
            note_para.paragraph_format.line_spacing = 0.9
            note_run = note_para.add_run(report.special_note_text)
            note_run.font.size = FONT_SIZE_BODY
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
            situation_run.font.size = FONT_SIZE_BODY
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
            access_run.font.size = FONT_SIZE_BODY
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
                coord_label.font.size = FONT_SIZE_BODY
                coord_label.font.color.rgb = RGBColor(0, 0, 0)

                # Coordinate values (format to 6 decimal places)
                lat_value = float(report.property_latitude)
                lng_value = float(report.property_longitude)
                coord_text = coord_para.add_run(f"{lat_value:.6f}, {lng_value:.6f}")
                coord_text.font.size = FONT_SIZE_BODY
                coord_text.font.color.rgb = RGBColor(0, 0, 0)

            # Add map image if available (embedded within ACCESS section)
            if report.location_map_image_data:
                try:
                    # Fetch the image from URL
                    map_url = report.location_map_image_data
                    logger.info(f"[DOCX] Fetching map image from URL (length={len(map_url)})")
                    logger.debug(f"[DOCX] Map URL: {map_url[:200]}...")  # Log first 200 chars for debugging

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

                        logger.info(f"[DOCX] Successfully added map image to document (size={len(response.content)} bytes)")
                    else:
                        logger.warning(f"[DOCX] Failed to fetch map image: HTTP {response.status_code}")
                        logger.debug(f"[DOCX] Response body: {response.text[:500] if response.text else 'empty'}")
                except Exception as e:
                    logger.error(f"[DOCX] Error adding map image: {str(e)}")
                    # Continue without map if error occurs
            else:
                logger.info(f"[DOCX] No location_map_image_data available for report {report.id}")

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
                name_label.font.size = FONT_SIZE_BODY
                name_label.font.color.rgb = RGBColor(0, 0, 0)
                name_value = name_para.add_run(f'"{report.land_traditional_name}"')
                name_value.font.size = FONT_SIZE_BODY
                name_value.font.color.rgb = RGBColor(0, 0, 0)

            # Survey Plan Information
            if report.lot_number and report.plan_number:
                plan_para = doc.add_paragraph()
                plan_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                plan_para.paragraph_format.space_before = Pt(0)
                plan_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                plan_para.paragraph_format.line_spacing = 0.9
                plan_label = plan_para.add_run("Survey Plan: ")
                plan_label.bold = True
                plan_label.font.size = FONT_SIZE_BODY
                plan_label.font.color.rgb = RGBColor(0, 0, 0)

                # Extract just the lot number/identifier (remove "Plan No" prefix if present)
                lot_desc = report.lot_number.strip() if report.lot_number else ''

                # Remove common prefixes that shouldn't be in lot description
                prefixes_to_remove = ['plan no', 'plan no:', 'lot plan no', 'lot plan no:']
                lot_desc_lower = lot_desc.lower()
                for prefix in prefixes_to_remove:
                    if lot_desc_lower.startswith(prefix):
                        lot_desc = lot_desc[len(prefix):].strip()
                        break

                # Ensure lot description has "Lot" prefix
                if not lot_desc.lower().startswith('lot'):
                    lot_desc = f"Lot {lot_desc}"

                # Format as "Lot X in Plan No: Y dated [date] made by [surveyor], Licensed Surveyor"
                plan_formatted = format_no_field("Plan", report.plan_number)
                plan_text = f"{lot_desc} in {plan_formatted}"
                if report.plan_date:
                    plan_text += f" dated {report.plan_date}"
                if report.licensed_surveyor_name:
                    plan_text += f" made by {report.licensed_surveyor_name}, Licensed Surveyor"
                plan_text += "."

                plan_value = plan_para.add_run(plan_text)
                plan_value.font.size = FONT_SIZE_BODY
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
                extent_label.font.size = FONT_SIZE_BODY
                extent_label.font.color.rgb = RGBColor(0, 0, 0)

                extent_text = report.land_extent_formatted
                if report.land_extent_hectares:
                    extent_text += f" [{report.land_extent_hectares:.4f} Hectares]"
                if report.land_extent_square_meters:
                    extent_text += f" [{report.land_extent_square_meters:.2f} m²]"

                extent_value = extent_para.add_run(extent_text)
                extent_value.font.size = FONT_SIZE_BODY
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
                boundaries_heading_run.font.size = FONT_SIZE_BODY
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

                # Enhanced format for each boundary direction (4 main + 4 optional diagonal)
                directions = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest']
                direction_labels = ['North', 'North-East', 'East', 'South-East', 'South', 'South-West', 'West', 'North-West']

                # SAFE: Get boundaries with None check
                boundaries = safe_get_json_field(report, 'boundaries', {})
                if not boundaries:
                    boundaries = {}

                for direction, label in zip(directions, direction_labels):
                    boundary_data = boundaries.get(direction, {}) if isinstance(boundaries, dict) else {}

                    # Skip diagonal boundaries if they have no description
                    if direction in ['northeast', 'southeast', 'southwest', 'northwest']:
                        if not boundary_data or not boundary_data.get('description'):
                            continue

                    # Main description line: "North  : Lot 7" or "North-East: Lot 7"
                    boundary_line = f"{label:<11} : "
                    boundary_text = boundary_data.get('description') or 'Not specified'

                    # Create paragraph for main boundary description
                    boundary_para = doc.add_paragraph()
                    boundary_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    boundary_para.paragraph_format.space_before = Pt(0)
                    boundary_para.paragraph_format.space_after = Pt(1)
                    boundary_para.paragraph_format.line_spacing = 0.9
                    boundary_para.paragraph_format.left_indent = Inches(0.5)

                    boundary_run = boundary_para.add_run(boundary_line + boundary_text)
                    boundary_run.font.size = FONT_SIZE_BODY
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
                summary_run.font.size = FONT_SIZE_BODY
                summary_run.font.color.rgb = RGBColor(0, 0, 0)


        # ===== 4.0 DESCRIPTION OF PROPERTY SECTION =====
        # Check if there's any property description data
        # Split into land data vs building data for better bare land support
        has_land_data = (
            report.land_description_text or
            report.land_shape or
            report.soil_type or
            report.land_type or
            report.water_table_depth or
            report.flood_risk or
            report.ongoing_construction_notes or
            # Topographical features for bare land
            report.elevation_changes or
            report.drainage_pattern or
            report.vegetation_type or
            report.natural_features
        )

        has_building_data = (
            report.buildings and
            isinstance(report.buildings, list) and
            len(report.buildings) > 0 and
            report.report_type != 'bare_land'
        )

        has_occupier_data = report.occupier_name

        # Show section 4.0 if there's ANY property description data
        if has_land_data or has_building_data or has_occupier_data:
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
                land_run.font.size = FONT_SIZE_BODY
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
                    land_run.font.size = FONT_SIZE_BODY
                    land_run.font.color.rgb = RGBColor(0, 0, 0)

            # === DEVELOPMENT FEASIBILITY / ONGOING CONSTRUCTION (Bare Land Reports) ===
            if report.ongoing_construction_notes and report.report_type == 'bare_land':
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                p.paragraph_format.line_spacing = 0.9

                run = p.add_run("Development Feasibility: ")
                run.font.bold = True
                run.font.size = FONT_SIZE_BODY
                run.font.color.rgb = RGBColor(0, 0, 0)

                run = p.add_run(report.ongoing_construction_notes)
                run.font.size = FONT_SIZE_BODY
                run.font.color.rgb = RGBColor(0, 0, 0)

            # === TOPOGRAPHICAL FEATURES (Bare Land specific) ===
            if report.report_type == 'bare_land':
                topo_parts = []

                if report.elevation_changes:
                    topo_parts.append(f"elevation changes are {report.elevation_changes.replace('_', ' ')}")
                if report.drainage_pattern:
                    topo_parts.append(f"drainage pattern is {report.drainage_pattern.replace('_', ' ')}")
                if report.vegetation_type:
                    topo_parts.append(f"vegetation type is {report.vegetation_type.replace('_', ' ')}")
                if report.natural_features:
                    topo_parts.append(f"natural features include {report.natural_features}")

                if topo_parts:
                    topo_text = "The land has " + ", ".join(topo_parts) + "."
                    topo_para = doc.add_paragraph()
                    topo_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    topo_para.paragraph_format.space_before = Pt(4)
                    topo_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                    topo_para.paragraph_format.line_spacing = 0.9

                    topo_label = topo_para.add_run("Topographical Features: ")
                    topo_label.font.bold = True
                    topo_label.font.size = FONT_SIZE_BODY

                    topo_value = topo_para.add_run(topo_text)
                    topo_value.font.size = FONT_SIZE_BODY

            # === PROPERTY PHOTOS (Bare Land - embedded in Section 4.0) ===
            if report.report_type == 'bare_land' and report.property_photos:
                property_photos = safe_get_json_field(report, 'property_photos', [])

                if property_photos and len(property_photos) > 0:
                    # Sort photos by order
                    sorted_photos = sorted(property_photos, key=lambda x: x.get('order', 0))

                    # Import modules needed for photo processing
                    import base64
                    import re

                    num_photos = len(sorted_photos)
                    photos_per_row = 3

                    # Process photos in rows with same logic as building photos
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

                        # Remove table borders for clean look
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

                                # Handle both data URI and raw base64 formats
                                if image_data:
                                    # Check if it's a data URI
                                    if image_data.startswith('data:image'):
                                        # Extract base64 from data URI
                                        base64_match = re.search(r'base64,(.+)', image_data)
                                        if not base64_match:
                                            idx += 1
                                            continue
                                        base64_data = base64_match.group(1)
                                    else:
                                        # Assume it's raw base64
                                        base64_data = image_data

                                    # Decode image
                                    image_bytes = base64.b64decode(base64_data)
                                    image_stream = BytesIO(image_bytes)

                                    # Use uniform 2-inch width
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

                                    # Add caption to second row with proper styling
                                    caption_cell = table.rows[1].cells[i]
                                    caption_para = caption_cell.paragraphs[0]
                                    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    caption_para.paragraph_format.space_before = Pt(2)
                                    caption_para.paragraph_format.space_after = Pt(2)

                                    caption_text = f"Fig. {idx + 1}"
                                    if caption:
                                        caption_text += f": {caption}"

                                    caption_run = caption_para.add_run(caption_text)
                                    caption_run.font.size = FONT_SIZE_CAPTION
                                    caption_run.font.italic = True
                                    caption_run.font.color.rgb = RGBColor(60, 60, 60)

                                    logger.info(f"[DOCX] Added property photo {idx + 1}")

                            except Exception as e:
                                logger.error(f"[DOCX] Error adding property photo {idx + 1}: {str(e)}")

                            idx += 1

                        # Add spacing after photo table
                        spacing_para = doc.add_paragraph()
                        spacing_para.paragraph_format.space_after = Pt(8)

                    # Add final spacing after all photos
                    final_spacing = doc.add_paragraph()
                    final_spacing.paragraph_format.space_after = IMAGE_SPACING_AFTER

            # === BUILDING DETAILS (Direct numbering: 4.1, 4.2, 4.3) ===
            # Use has_building_data to avoid redundant checks and respect report_type
            if has_building_data:
                buildings = safe_get_json_field(report, 'buildings', [])
                for idx, building in enumerate(buildings):
                    building_number = f"4.{idx + 1}"
                    building_name = building.get('building_name', f'Building {idx + 1}')

                    # Add building subsection heading
                    add_section_heading(doc, building_number, building_name)

                    # === CONSTRUCTION DETAILS (STANDALONE PARAGRAPH - NO LABEL) ===
                    # This comes FIRST, directly under the building heading
                    render_construction_details(doc, building)

                    # === PROFESSIONAL STRUCTURED FORMAT (All buildings) ===

                    # Use custom description text if provided
                    if building.get('building_description_text'):
                        opening_para = doc.add_paragraph()
                        opening_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        opening_para.paragraph_format.space_before = Pt(0)
                        opening_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                        opening_para.paragraph_format.line_spacing = 0.9
                        opening_run = opening_para.add_run(building.get('building_description_text'))
                        opening_run.font.size = FONT_SIZE_BODY
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
                            opening_run.font.size = FONT_SIZE_BODY
                            opening_run.font.color.rgb = RGBColor(0, 0, 0)

                    # === ACCOMMODATION ===
                    # Check if building has accommodation data (new structure at building level or old structure at floor level)
                    has_new_building_format = building.get('accommodation_summary') is not None
                    floors = building.get('floors', [])
                    has_old_floor_format = any(floor.get('accommodation_summary') for floor in floors)

                    if has_new_building_format or has_old_floor_format:
                        # Get accommodation summary (supports both new and old structures)
                        aggregated_rooms = aggregate_accommodation_across_building(building)

                        room_parts = []

                        # Build room counts list from aggregated data using format_room_count()
                        if aggregated_rooms.get('bedrooms', 0) > 0:
                            count = aggregated_rooms['bedrooms']
                            room_parts.append(format_room_count(count, 'bedroom'))

                        if aggregated_rooms.get('bathrooms', 0) > 0:
                            count = aggregated_rooms['bathrooms']
                            room_parts.append(format_room_count(count, 'bathroom'))

                        if aggregated_rooms.get('living_rooms', 0) > 0:
                            count = aggregated_rooms['living_rooms']
                            room_parts.append(format_room_count(count, 'living room'))

                        if aggregated_rooms.get('dining_rooms', 0) > 0:
                            count = aggregated_rooms['dining_rooms']
                            room_parts.append(format_room_count(count, 'dining room'))

                        if aggregated_rooms.get('kitchens', 0) > 0:
                            count = aggregated_rooms['kitchens']
                            room_parts.append(format_room_count(count, 'kitchen'))

                        if aggregated_rooms.get('pantries', 0) > 0:
                            count = aggregated_rooms['pantries']
                            room_parts.append(format_room_count(count, 'pantry', 'pantries'))

                        if aggregated_rooms.get('verandahs', 0) > 0:
                            count = aggregated_rooms['verandahs']
                            room_parts.append(format_room_count(count, 'verandah'))

                        if aggregated_rooms.get('balconies', 0) > 0:
                            count = aggregated_rooms['balconies']
                            room_parts.append(format_room_count(count, 'balcony', 'balconies'))

                        if aggregated_rooms.get('garages', 0) > 0:
                            count = aggregated_rooms['garages']
                            room_parts.append(format_room_count(count, 'garage'))

                        if aggregated_rooms.get('store_rooms', 0) > 0:
                            count = aggregated_rooms['store_rooms']
                            room_parts.append(format_room_count(count, 'store room'))

                        if aggregated_rooms.get('other_rooms', 0) > 0:
                            count = aggregated_rooms['other_rooms']
                            room_parts.append(format_room_count(count, 'other room'))

                        if room_parts:
                            # Create single-line accommodation text
                            accommodation_text = f"The property comprises {format_list_with_grammar(room_parts)}."
                            add_inline_field(doc, "Accommodation", accommodation_text)


                    # === FLOOR AREA (CONDITIONAL FORMAT) ===
                    floors = building.get('floors', [])
                    total_area = building.get('total_floor_area', 0)
                    if floors and (total_area or any(f.get('floor_area', 0) > 0 for f in floors)):
                        # Filter floors with area > 0
                        floors_with_area = [f for f in floors if f.get('floor_area', 0) > 0]

                        if len(floors_with_area) == 1:
                            # SINGLE FLOOR: Use inline format
                            floor = floors_with_area[0]
                            floor_area = floor.get('floor_area', 0)
                            area_text = f"{floor_area:,.0f} square feet"
                            add_inline_field(doc, "Floor area", area_text)
                        else:
                            # MULTIPLE FLOORS: Use table format
                            # Add "Floor Area" label (bold, inline)
                            floor_area_para = doc.add_paragraph()
                            floor_area_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            floor_area_para.paragraph_format.space_before = INLINE_FIELD_SPACE_BEFORE
                            floor_area_para.paragraph_format.space_after = Pt(2)
                            floor_area_para.paragraph_format.line_spacing = 0.9

                            label_run = floor_area_para.add_run("Floor area:")
                            label_run.bold = True
                            label_run.font.size = FONT_SIZE_BODY
                            label_run.font.color.rgb = RGBColor(0, 0, 0)

                            # Add each floor's area (indented with aligned columns)
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

                                    # Use fixed-width padding for column alignment
                                    floor_name_padded = f"{floor_name:<25}"
                                    floor_line_run = floor_line_para.add_run(f"{floor_name_padded}{floor_area:>10,.0f} square feet")
                                    floor_line_run.font.size = FONT_SIZE_BODY
                                    floor_line_run.font.color.rgb = RGBColor(0, 0, 0)

                            # Add total (indented with aligned columns)
                            if total_area and total_area > 0:
                                total_para = doc.add_paragraph()
                                total_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                                total_para.paragraph_format.space_before = Pt(0)
                                total_para.paragraph_format.space_after = INLINE_FIELD_SPACE_AFTER
                                total_para.paragraph_format.line_spacing = 0.9
                                total_para.paragraph_format.left_indent = Inches(0.5)

                                # Use fixed-width padding for column alignment
                                total_padded = f"{'Total':<25}"
                                total_run = total_para.add_run(f"{total_padded}{total_area:>10,.0f} square feet")
                                total_run.bold = True
                                total_run.font.size = FONT_SIZE_BODY
                                total_run.font.color.rgb = RGBColor(0, 0, 0)

                    # === AGE AND CONDITION (INLINE FORMAT) ===
                    building_age = building.get('building_age')
                    condition = building.get('condition', '')
                    if building_age or condition:
                        condition_labels = {
                            'excellent': 'excellent',
                            'good': 'good',
                            'fair': 'fair',
                            'poor': 'poor',
                            'dilapidated': 'dilapidated'
                        }

                        parts = []
                        if building_age is not None and building_age > 0:
                            year_word = "year" if building_age == 1 else "years"
                            parts.append(f"{building_age} {year_word} old")
                        if condition:
                            parts.append(f"condition is {condition_labels.get(condition, condition)}")

                        age_text = "; ".join(parts) + "." if parts else "Information not provided."

                        add_inline_field(doc, "Age and condition", age_text)

                    # === UTILITIES AND CONVENIENCES ===
                    render_utilities_and_conveniences(doc, building)

                    # === OCCUPATION (BUILDING-LEVEL) ===
                    # Primary: Use building-level occupier data
                    if building.get('occupier_name'):
                        relationship = building.get('occupier_relationship')

                        # Special case for vacant buildings
                        if relationship == 'vacant':
                            occupier_text = "The building is currently vacant."
                        else:
                            occupier_text = f"The building is occupied by {building.get('occupier_name')}"

                            if relationship:
                                rel_labels = {
                                    'owner': 'the owner',
                                    'tenant': 'a tenant',
                                    'family_member': 'a family member',
                                    'caretaker': 'caretaker'
                                }
                                occupier_text += f" who is {rel_labels.get(relationship, relationship)}."
                            else:
                                occupier_text += "."

                        add_inline_field(doc, "Occupation", occupier_text, space_after=Pt(6))

                    # Fallback: Support old reports with property-level occupier
                    elif report.occupier_name:
                        occupier_text = f"The property is occupied by {report.occupier_name}"
                        if report.occupier_relationship:
                            rel_labels = {
                                'owner': 'the owner',
                                'tenant': 'a tenant',
                                'family_member': 'a family member',
                                'caretaker': 'caretaker'
                            }
                            occupier_text += f" who is {rel_labels.get(report.occupier_relationship, report.occupier_relationship)}."
                        else:
                            occupier_text += "."

                        add_inline_field(doc, "Occupation", occupier_text, space_after=Pt(6))

                    # === BUILDING PHOTOS (3-column grid layout - NO SUBHEADING) ===
                    building_photos = building.get('building_photos', [])
                    if building_photos and len(building_photos) > 0:
                        # Sort photos by order
                        sorted_photos = sorted(building_photos, key=lambda x: x.get('order', 0))

                        # Modern flexible photo grid layout using tables for proper caption alignment
                        import base64
                        import re


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
                                    caption_run.font.size = FONT_SIZE_CAPTION
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
                        add_structures_run.font.size = FONT_SIZE_BODY
                        add_structures_run.font.color.rgb = RGBColor(0, 0, 0)

                        # Add description paragraph
                        structures_para = doc.add_paragraph()
                        structures_para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        structures_para.paragraph_format.space_before = Pt(0)
                        structures_para.paragraph_format.space_after = BODY_PARA_SPACE_AFTER
                        structures_para.paragraph_format.line_spacing = 0.9
                        structures_para.paragraph_format.left_indent = INDENTED_CONTENT_LEFT_INDENT

                        structures_run = structures_para.add_run(additional_structures.strip())
                        structures_run.font.size = FONT_SIZE_BODY
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
            locality_run.font.size = FONT_SIZE_BODY
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

            # (b) Street lines - Generate contextual paragraph (SKIP for bare_land)
            if report.street_lines_status and report.report_type != 'bare_land':
                street_para = generate_street_lines_paragraph(report)
                add_subsection_paragraph(doc, "(b)", "Street lines", street_para)

            # (c) Building limits - Generate detailed paragraph (SKIP for bare_land)
            if report.building_limits_status and report.report_type != 'bare_land':
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
        # Show section if either comparables OR market analysis exists
        if report.comparable_properties or report.land_market_analysis:
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
                    run.font.size = FONT_SIZE_BODY

                    # Add average rate note
                    avg_rate = sum(c.get('rate_per_perch', 0) for c in comparables) / len(comparables) if comparables else 0
                    if avg_rate > 0:
                        p = doc.add_paragraph()
                        p.paragraph_format.space_before = Pt(6)
                        p.paragraph_format.space_after = Pt(6)
                        run = p.add_run(f"Average Rate: LKR {avg_rate:,.2f} per perch")
                        run.font.bold = True
                        run.font.size = FONT_SIZE_BODY

            if report.land_market_analysis:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.space_after = Pt(12)
                run = p.add_run(report.land_market_analysis)
                run.font.size = FONT_SIZE_BODY

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

                # Add tab stop for right alignment
                tab_stops = p.paragraph_format.tab_stops
                tab_stops.add_tab_stop(Inches(6.0), WD_TAB_ALIGNMENT.RIGHT)

                text = f"Land – {extent:,.2f} perches @ {format_currency(rate)} per perch\t= {format_currency_aligned(land_value)}"
                run = p.add_run(text)
                run.font.size = FONT_SIZE_VALUATION
                p.paragraph_format.space_after = Pt(3)

            # Buildings valuation (SKIP for bare_land)
            total_depreciated_buildings_value = 0
            buildings_insurance_values = []  # Store per-building insurance values

            if report.valuation_buildings_data and report.report_type != 'bare_land':
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

                    # Check if depreciation data exists
                    has_depreciation = bldg.get('depreciation_amount') is not None and to_float(bldg.get('depreciation_amount', 0)) > 0

                    if has_depreciation:
                        depreciation_rate = to_float(bldg.get('depreciation_rate_percent', 0))
                        depreciated_value = to_float(bldg.get('depreciated_value', subtotal))

                        # NEW FORMAT: 2-line building with inline depreciation
                        format_building_valuation_2line(
                            doc,
                            building_name,
                            total_floor_area,
                            avg_rate,
                            depreciation_rate,
                            depreciated_value
                        )

                        building_value = depreciated_value
                    else:
                        # No depreciation: Use single-line format (backward compatible)
                        p = doc.add_paragraph()

                        # Add tab stop for right alignment
                        tab_stops = p.paragraph_format.tab_stops
                        tab_stops.add_tab_stop(Inches(6.0), WD_TAB_ALIGNMENT.RIGHT)

                        text = f"{building_name} – {total_floor_area:,.0f} sq.ft @ {format_currency(avg_rate)} per square foot\t= {format_currency_aligned(subtotal)}"
                        run = p.add_run(text)
                        run.font.size = FONT_SIZE_VALUATION
                        p.paragraph_format.space_after = Pt(3)
                        building_value = to_float(subtotal)

                    total_depreciated_buildings_value += building_value
                    # Insurance always uses replacement cost (undepreciated)
                    buildings_insurance_values.append({
                        'name': building_name,
                        'value': to_float(subtotal)  # Replacement cost for insurance
                    })

            # Add-ons (NEW compact format)
            total_addons_value = 0
            if report.valuation_addons:
                # SAFE: Parse JSON with error handling
                addons = safe_parse_json_string(report.valuation_addons, [])

                if addons:
                    # No header, just show add-ons in compact format
                    for addon in addons:
                        format_addon_compact(
                            doc,
                            addon.get('description', 'Add-on'),
                            to_float(addon.get('value', 0))
                        )
                        total_addons_value += to_float(addon.get('value', 0))

            # Calculate market values
            land_value = to_float(report.valuation_total_land_value)
            market_value_calculated = land_value + to_float(total_depreciated_buildings_value) + to_float(total_addons_value)
            market_value_rounded = round_for_say(market_value_calculated)

            # Determine if we should show "Market Value of the property" section
            # SKIP for bare land with ONLY land value (no buildings, no add-ons)
            has_buildings_or_addons = (total_depreciated_buildings_value > 0) or (total_addons_value > 0)

            if has_buildings_or_addons:
                # Show "Market Value of the property" line (with double underline)
                add_market_value_line(doc, market_value_calculated, has_blank_before=True)

            # Always show "Value rounded off" line
            add_value_rounded_line(doc, market_value_rounded)

            # Check if valuation type is "Forced Sale Value" to show forced sale fields
            show_forced_sale = report.valuation_type == "Forced Sale Value"

            if show_forced_sale:
                # Calculate forced sale value for summary section
                forced_sale_percentage = report.valuation_forced_sale_percentage or 90
                forced_sale_value = market_value_rounded * (forced_sale_percentage / 100)

            # === SUMMARY OF THE VALUATION ===
            p = doc.add_paragraph()
            run = p.add_run("SUMMARY OF THE VALUATION")
            run.font.bold = True
            run.font.underline = True
            run.font.size = FONT_SIZE_BODY
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)

            # Open Market Value
            p = doc.add_paragraph()
            tab_stops = p.paragraph_format.tab_stops
            tab_stops.add_tab_stop(Inches(3.5), WD_TAB_ALIGNMENT.LEFT)
            tab_stops.add_tab_stop(Inches(3.7), WD_TAB_ALIGNMENT.LEFT)
            text = f"Open Market Value of the property\t:\t{format_currency(market_value_rounded)}"
            run = p.add_run(text)
            run.font.size = FONT_SIZE_VALUATION
            p.paragraph_format.space_after = Pt(3)

            # Forced Sale Value - only show when valuation type is "Forced Sale Value"
            if show_forced_sale:
                p = doc.add_paragraph()
                tab_stops = p.paragraph_format.tab_stops
                tab_stops.add_tab_stop(Inches(3.5), WD_TAB_ALIGNMENT.LEFT)
                tab_stops.add_tab_stop(Inches(3.7), WD_TAB_ALIGNMENT.LEFT)
                text = f"Forced Sale Value of the property\t:\t{format_currency(forced_sale_value)}"
                run = p.add_run(text)
                run.font.size = FONT_SIZE_VALUATION
                p.paragraph_format.space_after = Pt(3)

            # Insurance Value (NEW INLINE FORMAT) - Only show if there are buildings
            if buildings_insurance_values:
                for building_ins in buildings_insurance_values:
                    p = doc.add_paragraph()
                    tab_stops = p.paragraph_format.tab_stops
                    tab_stops.add_tab_stop(Inches(3.5), WD_TAB_ALIGNMENT.LEFT)
                    tab_stops.add_tab_stop(Inches(3.7), WD_TAB_ALIGNMENT.LEFT)
                    text = f"Insurance Value of the {building_ins['name']}\t:\t{format_currency(building_ins['value'])}"
                    run = p.add_run(text)
                    run.font.size = FONT_SIZE_VALUATION
                    p.paragraph_format.space_after = Pt(2)

                doc.add_paragraph()  # Final spacing

        # ===== 9.0 CERTIFICATION (SIMPLIFIED FORMAT) =====
        if report.certification_text or report.certification_valuer_name:
            add_section_heading(doc, "9.0", "CERTIFICATION")

            # Certification text - single paragraph
            if report.certification_text:
                # Use custom certification text if provided (override mode)
                cert_text = report.certification_text.strip()
            elif report.certification_valuer_name and report.certification_valuer_designation:
                # Auto-generate simplified certification
                cert_text = generate_simplified_certification_text(
                    valuer_name=report.certification_valuer_name,
                    valuer_designation=report.certification_valuer_designation,
                    lot_number=report.lot_number,
                    plan_number=report.plan_number,
                    plan_date=report.plan_date,
                    licensed_surveyor_name=report.licensed_surveyor_name,
                    deeds=safe_get_json_field(report, 'deeds', []),
                    property_identification_type=report.property_identification_type
                )
            else:
                # Fallback if no valuer info
                cert_text = "I hereby certify that I have personally inspected this property and the valuation stated herein represents my professional opinion of the market value as of the date of inspection."

            # Render certification paragraph
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(12)
            run = p.add_run(cert_text)
            run.font.size = FONT_SIZE_BODY

            # Signature block
            add_signature_block(
                doc=doc,
                user=user,
                valuer_name=report.certification_valuer_name,
                valuer_designation=report.certification_valuer_designation,
                certification_date=report.certification_date
            )

        # ===== INVOICE SECTION =====
        if report.invoice_data:
            logger.info("[DOCX] Generating invoice section")
            generate_invoice_section(doc, report.invoice_data, user, report)

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

