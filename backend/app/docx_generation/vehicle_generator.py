"""
Vehicle valuation report DOCX generation.
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

from .text_generators import (
    generate_title_block, get_pronoun, add_signature_block,
    generate_simplified_certification_text,
)

# ===== VEHICLE REPORT GENERATION =====

def generate_vehicle_report_docx(report: models.Report, user: models.User) -> BytesIO:
    """
    Generate a formatted DOCX file for a vehicle valuation report.

    Args:
        report: Report model instance with vehicle data
        user: User model instance

    Returns:
        BytesIO object containing the DOCX document
    """
    try:
        # Create a new Document
        doc = Document()

        # ===== LETTERHEAD =====
        template_id = user.preferred_letterhead_template or 'classic'
        template = get_template(template_id)
        template.render_letterhead(doc, user, report)

        # Get primary vehicle
        vehicle = report.primary_vehicle
        if not vehicle:
            # Try to get from associations
            if report.vehicle_associations and len(report.vehicle_associations) > 0:
                vehicle = report.vehicle_associations[0].vehicle
            else:
                raise ValueError("No vehicle found for this report")

        # ===== TITLE BLOCK =====
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title_para.add_run("VEHICLE VALUATION REPORT")
        title_run.bold = True
        title_run.font.size = Pt(14)
        title_run.font.underline = True

        # Vehicle identification line
        vehicle_desc = f"{vehicle.make or 'Unknown'} {vehicle.model or ''} ({vehicle.registration_number or 'Unregistered'})"
        desc_para = doc.add_paragraph()
        desc_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        desc_run = desc_para.add_run(vehicle_desc)
        desc_run.bold = True
        desc_run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== HEADER INFORMATION =====
        header_table = doc.add_table(rows=6, cols=2)
        header_table.style = 'Table Grid'

        header_data = [
            ("Purpose of Valuation", report.valuation_purpose or "Market Value Assessment"),
            ("Requested By", report.applicant_full_name or ""),
            ("Report Date", report.report_date or ""),
            ("Inspection Date", report.inspection_date or ""),
            ("Folio Number", report.folio_number or ""),
            ("Inspection Place", report.inspection_place or ""),
        ]

        for i, (label, value) in enumerate(header_data):
            row = header_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            # Bold the label
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== VEHICLE IDENTIFICATION SECTION =====
        id_heading = doc.add_paragraph()
        id_heading_run = id_heading.add_run("1. VEHICLE IDENTIFICATION")
        id_heading_run.bold = True
        id_heading_run.font.size = Pt(12)

        id_table = doc.add_table(rows=14, cols=2)
        id_table.style = 'Table Grid'

        id_data = [
            ("Registration Number", vehicle.registration_number),
            ("Provincial Council", vehicle.provincial_council),
            ("Class of Vehicle", vehicle.class_of_vehicle),
            ("Make", vehicle.make),
            ("Model", vehicle.model),
            ("Year of Manufacture", str(vehicle.year_of_manufacture) if vehicle.year_of_manufacture else ""),
            ("Date of First Registration", vehicle.date_of_first_registration),
            ("Body Colour", vehicle.body_colour),
            ("Chassis Number", vehicle.chassis_number),
            ("Engine Number", vehicle.engine_number),
            ("Cylinder Capacity", f"{vehicle.cylinder_capacity} cc" if vehicle.cylinder_capacity else ""),
            ("Fuel Type", vehicle.fuel_type),
            ("Mileage", f"{vehicle.mileage:,} {vehicle.mileage_unit or 'km'}" if vehicle.mileage else ""),
            ("Country of Origin", vehicle.country_of_origin),
        ]

        for i, (label, value) in enumerate(id_data):
            row = id_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== ENGINE & TRANSMISSION SECTION =====
        engine_heading = doc.add_paragraph()
        engine_heading_run = engine_heading.add_run("2. ENGINE & TRANSMISSION")
        engine_heading_run.bold = True
        engine_heading_run.font.size = Pt(12)

        engine_table = doc.add_table(rows=6, cols=2)
        engine_table.style = 'Table Grid'

        engine_data = [
            ("Engine Type", vehicle.engine_type),
            ("Transmission", vehicle.transmission),
            ("Wheel Drive", vehicle.wheel_drive),
            ("Running Condition", vehicle.running_condition),
            ("Engine Condition", vehicle.engine_condition),
            ("Gear Box Condition", vehicle.gear_box_condition),
        ]

        for i, (label, value) in enumerate(engine_data):
            row = engine_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== BODY & CONDITION SECTION =====
        body_heading = doc.add_paragraph()
        body_heading_run = body_heading.add_run("3. BODY & CONDITION")
        body_heading_run.bold = True
        body_heading_run.font.size = Pt(12)

        body_table = doc.add_table(rows=5, cols=2)
        body_table.style = 'Table Grid'

        body_data = [
            ("Body Condition", vehicle.body_condition),
            ("Chassis Condition", vehicle.chassis_condition),
            ("Upholstery Condition", vehicle.upholstery_condition),
            ("Underside Condition", vehicle.underside_condition),
            ("Clutch Status", vehicle.clutch_status),
        ]

        for i, (label, value) in enumerate(body_data):
            row = body_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== PARTS AVAILABILITY SECTION =====
        parts_heading = doc.add_paragraph()
        parts_heading_run = parts_heading.add_run("4. PARTS AVAILABILITY")
        parts_heading_run.bold = True
        parts_heading_run.font.size = Pt(12)

        parts_table = doc.add_table(rows=3, cols=2)
        parts_table.style = 'Table Grid'

        parts_data = [
            ("Body Parts", vehicle.body_parts_status),
            ("Engine Parts", vehicle.engine_parts_status),
            ("Accessories", vehicle.accessories_status),
        ]

        for i, (label, value) in enumerate(parts_data):
            row = parts_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== BRAKES & SAFETY SECTION =====
        brakes_heading = doc.add_paragraph()
        brakes_heading_run = brakes_heading.add_run("5. BRAKES & SAFETY")
        brakes_heading_run.bold = True
        brakes_heading_run.font.size = Pt(12)

        brakes_table = doc.add_table(rows=4, cols=2)
        brakes_table.style = 'Table Grid'

        brakes_data = [
            ("Foot Brake Condition", vehicle.foot_brake_condition),
            ("Disc Brake", "Available" if vehicle.disc_brake_available else "Not Available"),
            ("Parking Brake Condition", vehicle.parking_brake_condition),
            ("ABS", "Available" if vehicle.abs_available else "Not Available"),
        ]

        for i, (label, value) in enumerate(brakes_data):
            row = brakes_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== FEATURES SECTION =====
        features = safe_get_json_field(vehicle, 'features', {})
        if features:
            features_heading = doc.add_paragraph()
            features_heading_run = features_heading.add_run("6. FEATURES & AMENITIES")
            features_heading_run.bold = True
            features_heading_run.font.size = Pt(12)

            features_list = []
            if features.get('air_condition'):
                features_list.append("Air Condition")
            if features.get('dual_air_condition'):
                features_list.append("Dual Air Condition")
            if features.get('power_mirror'):
                features_list.append("Power Mirror")
            if features.get('power_window'):
                features_list.append("Power Window")
            if features.get('power_steering'):
                features_list.append("Power Steering")
            if features.get('airbag'):
                features_list.append(f"Airbag (x{features.get('num_airbags', 1)})")

            if features_list:
                features_para = doc.add_paragraph()
                features_para.add_run("Available Features: ").bold = True
                features_para.add_run(", ".join(features_list))

            if features.get('seats'):
                seats_para = doc.add_paragraph()
                seats_para.add_run("Seating Capacity: ").bold = True
                seats_para.add_run(str(features.get('seats')))

            if features.get('doors'):
                doors_para = doc.add_paragraph()
                doors_para.add_run("Number of Doors: ").bold = True
                doors_para.add_run(str(features.get('doors')))

        doc.add_paragraph()  # Spacing

        # ===== TYRES SECTION =====
        tyres = safe_get_json_field(vehicle, 'tyres', {})
        if tyres:
            tyres_heading = doc.add_paragraph()
            tyres_heading_run = tyres_heading.add_run("7. TYRES")
            tyres_heading_run.bold = True
            tyres_heading_run.font.size = Pt(12)

            tyres_table = doc.add_table(rows=5, cols=3)
            tyres_table.style = 'Table Grid'

            # Header row
            tyres_table.rows[0].cells[0].text = ""
            tyres_table.rows[0].cells[1].text = "Front"
            tyres_table.rows[0].cells[2].text = "Rear"
            for cell in tyres_table.rows[0].cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.bold = True

            front = tyres.get('front', {})
            rear = tyres.get('rear', {})

            tyre_rows = [
                ("Brand", front.get('brand', ''), rear.get('brand', '')),
                ("Size", front.get('size', ''), rear.get('size', '')),
                ("Tread %", f"{front.get('tread_percent', '')}%" if front.get('tread_percent') else "", f"{rear.get('tread_percent', '')}%" if rear.get('tread_percent') else ""),
                ("Condition", front.get('condition', ''), rear.get('condition', '')),
            ]

            for i, (label, front_val, rear_val) in enumerate(tyre_rows, start=1):
                row = tyres_table.rows[i]
                row.cells[0].text = label
                row.cells[1].text = str(front_val) if front_val else ""
                row.cells[2].text = str(rear_val) if rear_val else ""
                for para in row.cells[0].paragraphs:
                    for run in para.runs:
                        run.font.bold = True

            # Spare tyre and replacement
            spare_para = doc.add_paragraph()
            spare_para.add_run("Spare Tyre: ").bold = True
            spare_para.add_run("Available" if tyres.get('spare_available') else "Not Available")

            if tyres.get('need_replacement'):
                replace_para = doc.add_paragraph()
                replace_para.add_run("Note: ").bold = True
                replace_para.add_run("Tyres need replacement")

        doc.add_paragraph()  # Spacing

        # ===== ELECTRICAL & LIGHTS SECTION =====
        electrical = safe_get_json_field(vehicle, 'electrical', {})
        lights = safe_get_json_field(vehicle, 'lights', {})

        if electrical or lights:
            elec_heading = doc.add_paragraph()
            elec_heading_run = elec_heading.add_run("8. ELECTRICAL & LIGHTS")
            elec_heading_run.bold = True
            elec_heading_run.font.size = Pt(12)

            if electrical:
                elec_para = doc.add_paragraph()
                elec_para.add_run("Electrical System: ").bold = True
                elec_items = []
                if electrical.get('starter'):
                    elec_items.append("Starter ✓")
                if electrical.get('horn'):
                    elec_items.append("Horn ✓")
                if electrical.get('wiper'):
                    elec_items.append("Wiper ✓")
                if electrical.get('battery_condition'):
                    elec_items.append(f"Battery ({electrical.get('battery_condition')})")
                elec_para.add_run(", ".join(elec_items) if elec_items else "N/A")

            if lights:
                lights_para = doc.add_paragraph()
                lights_para.add_run("Lights: ").bold = True
                light_items = []
                if lights.get('head'):
                    light_items.append("Head ✓")
                if lights.get('dim'):
                    light_items.append("Dim ✓")
                if lights.get('signal'):
                    light_items.append("Signal ✓")
                if lights.get('parking'):
                    light_items.append("Parking ✓")
                if lights.get('reverse'):
                    light_items.append("Reverse ✓")
                if lights.get('meter'):
                    light_items.append("Meter ✓")
                lights_para.add_run(", ".join(light_items) if light_items else "N/A")

        doc.add_paragraph()  # Spacing

        # ===== HISTORY SECTION =====
        history_heading = doc.add_paragraph()
        history_heading_run = history_heading.add_run("9. HISTORY & REPAIRS")
        history_heading_run.bold = True
        history_heading_run.font.size = Pt(12)

        history_table = doc.add_table(rows=4, cols=2)
        history_table.style = 'Table Grid'

        history_data = [
            ("Accident History", "Yes" if vehicle.has_accidents else "No"),
            ("Repair History", "Yes" if vehicle.has_repairs else "No"),
            ("Repairs Needed Within Year", "Yes" if vehicle.needs_repairs_within_year else "No"),
            ("Body Parts Replaced", "Yes" if vehicle.body_parts_replaced else "No"),
        ]

        for i, (label, value) in enumerate(history_data):
            row = history_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # ===== VALUATION SECTION =====
        val_heading = doc.add_paragraph()
        val_heading_run = val_heading.add_run("10. VALUATION")
        val_heading_run.bold = True
        val_heading_run.font.size = Pt(12)

        val_table = doc.add_table(rows=4, cols=2)
        val_table.style = 'Table Grid'

        val_data = [
            ("Purchase Price", f"Rs. {to_float(vehicle.purchase_price):,.2f}" if vehicle.purchase_price else ""),
            ("Brand New Price", f"Rs. {to_float(vehicle.brand_new_price):,.2f}" if vehicle.brand_new_price else ""),
            ("Market Value", f"Rs. {to_float(vehicle.market_value):,.2f}" if vehicle.market_value else ""),
            ("Forced Sale Value", f"Rs. {to_float(vehicle.forced_sale_value):,.2f}" if vehicle.forced_sale_value else ""),
        ]

        for i, (label, value) in enumerate(val_data):
            row = val_table.rows[i]
            row.cells[0].text = label
            row.cells[1].text = str(value) if value else ""
            for paragraph in row.cells[0].paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = FONT_SIZE_BODY
            for paragraph in row.cells[1].paragraphs:
                for run in paragraph.runs:
                    run.font.size = FONT_SIZE_BODY

        doc.add_paragraph()  # Spacing

        # Valuation Summary
        if vehicle.valuation_summary:
            summary_para = doc.add_paragraph()
            summary_para.add_run("Valuation Summary: ").bold = True
            summary_para.add_run(vehicle.valuation_summary)

        doc.add_paragraph()  # Spacing

        # ===== OFFICE USE SECTION (Conditional) =====
        if report.is_office_use:
            office_data = safe_get_json_field(vehicle, 'office_data', {})
            if office_data:
                office_heading = doc.add_paragraph()
                office_heading_run = office_heading.add_run("FOR OFFICE USE ONLY")
                office_heading_run.bold = True
                office_heading_run.font.size = Pt(12)

                office_table = doc.add_table(rows=3, cols=2)
                office_table.style = 'Table Grid'

                office_rows = [
                    ("Civil No", office_data.get('civil_no', '')),
                    ("Military No", office_data.get('military_no', '')),
                    ("Approval Position", office_data.get('approval_position', '')),
                ]

                for i, (label, value) in enumerate(office_rows):
                    row = office_table.rows[i]
                    row.cells[0].text = label
                    row.cells[1].text = str(value) if value else ""

            # Past Valuations Table
            past_valuations = safe_get_json_field(vehicle, 'past_valuations', [])
            if past_valuations:
                past_heading = doc.add_paragraph()
                past_heading.paragraph_format.space_before = Pt(12)
                past_heading_run = past_heading.add_run("Previous Assessment")
                past_heading_run.bold = True
                past_heading_run.font.size = Pt(11)

                past_table = doc.add_table(rows=len(past_valuations) + 1, cols=5)
                past_table.style = 'Table Grid'

                # Header row
                headers = ["S/N", "Vehicle No - Civil", "Vehicle No - Military", "Year", "Value (Rs)"]
                for j, header in enumerate(headers):
                    past_table.rows[0].cells[j].text = header
                    for para in past_table.rows[0].cells[j].paragraphs:
                        for run in para.runs:
                            run.font.bold = True

                # Data rows
                for i, pv in enumerate(past_valuations, start=1):
                    past_table.rows[i].cells[0].text = str(pv.get('serial', i))
                    past_table.rows[i].cells[1].text = str(pv.get('civil_no', ''))
                    past_table.rows[i].cells[2].text = str(pv.get('military_no', ''))
                    past_table.rows[i].cells[3].text = str(pv.get('year', ''))
                    past_table.rows[i].cells[4].text = f"Rs. {to_float(pv.get('value')):,.2f}" if pv.get('value') else ""

        doc.add_paragraph()  # Spacing

        # ===== VEHICLE PHOTOS =====
        vehicle_photos = safe_get_json_field(vehicle, 'vehicle_photos', [])
        if vehicle_photos:
            photos_heading = doc.add_paragraph()
            photos_heading_run = photos_heading.add_run("VEHICLE PHOTOGRAPHS")
            photos_heading_run.bold = True
            photos_heading_run.font.size = Pt(12)

            for photo in vehicle_photos:
                image_data = photo.get('image_data', '')
                caption = photo.get('caption', '')

                if image_data:
                    try:
                        # Handle base64 data URL
                        if ',' in image_data:
                            image_data = image_data.split(',')[1]

                        import base64
                        image_bytes = base64.b64decode(image_data)
                        image_stream = BytesIO(image_bytes)

                        # Add image
                        doc.add_picture(image_stream, width=Inches(4))

                        # Add caption if exists
                        if caption:
                            cap_para = doc.add_paragraph()
                            cap_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            cap_run = cap_para.add_run(caption)
                            cap_run.font.italic = True
                            cap_run.font.size = Pt(10)

                        doc.add_paragraph()  # Spacing
                    except Exception as img_error:
                        logger.warning(f"Could not add vehicle photo: {img_error}")

        # ===== SIGNATURE SECTION =====
        doc.add_paragraph()
        doc.add_paragraph()
        sig_para = doc.add_paragraph()
        sig_para.paragraph_format.space_before = Pt(24)
        sig_para.add_run("_" * 40)

        date_para = doc.add_paragraph()
        date_para.add_run("Date: _________________")

        sig_label = doc.add_paragraph()
        sig_label_run = sig_label.add_run("Signature")
        sig_label_run.font.italic = True

        # Save to BytesIO
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        logger.info("[DOCX] Vehicle report generated successfully")
        return buffer

    except Exception as e:
        logger.error(f"[DOCX] Error generating vehicle report: {str(e)}")
        import traceback
        logger.error(f"[DOCX] Traceback: {traceback.format_exc()}")
        raise


