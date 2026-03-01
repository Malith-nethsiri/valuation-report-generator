"""
Deed, certification, title block, and applicant text generators.
"""
from typing import Optional, List, Dict
import logging

from .. import models
from ..utils import append_label_if_missing, clean_spelling_errors, format_no_field
from .formatting import format_currency_words
from .situation_text import generate_smart_address

logger = logging.getLogger(__name__)


def generate_simplified_certification_text(
    valuer_name: str,
    valuer_designation: str,
    lot_number: Optional[str],
    plan_number: Optional[str],
    plan_date: Optional[str],
    licensed_surveyor_name: Optional[str],
    deeds: Optional[List[dict]],
    property_identification_type: Optional[str]
) -> str:
    """
    Generate simplified single-paragraph certification text.
    """
    cert_text = f"I, {valuer_name}, {valuer_designation}, do hereby certify that the property inspected by me and valued above is identical to "

    property_id = None

    if not property_identification_type:
        if plan_number and deeds and len(deeds) > 0:
            property_identification_type = "plan_and_deed"
        elif plan_number:
            property_identification_type = "plan"
        elif deeds and len(deeds) > 0:
            property_identification_type = "deed"

    if property_identification_type in ["plan", "plan_and_deed"]:
        if plan_number:
            if lot_number and lot_number.strip():
                plan_ref = format_no_field("Plan", plan_number)
                property_id = f"the property depicted as Lot {lot_number} in {plan_ref}"
            else:
                plan_ref = format_no_field("Plan", plan_number)
                property_id = f"the property depicted as {plan_ref}"

            if plan_date:
                property_id += f" dated {plan_date}"

            if licensed_surveyor_name:
                property_id += f" made by {licensed_surveyor_name}, Licensed Surveyor"

    if not property_id and property_identification_type in ["deed", "plan_and_deed", "certificate_of_sale"]:
        has_deed = isinstance(deeds, list) and len(deeds) > 0
        if has_deed:
            deed = deeds[0]
            deed_number = deed.get('deed_number', '') if isinstance(deed, dict) else getattr(deed, 'deed_number', '')
            deed_type = deed.get('deed_type', 'Deed') if isinstance(deed, dict) else getattr(deed, 'deed_type', 'Deed')
            deed_date = deed.get('deed_date', '') if isinstance(deed, dict) else getattr(deed, 'deed_date', '')

            if deed_number:
                property_id = f"the property described in {deed_type} No. {deed_number}"
                if deed_date:
                    property_id += f" dated {deed_date}"

    if not property_id:
        property_id = "the property described in this report"

    cert_text += property_id + "."
    return cert_text


# DEPRECATED: Keep for backward compatibility with old code
def generate_certificate_of_identity_text(
    property_identification_type: Optional[str],
    plan_number: Optional[str],
    plan_date: Optional[str],
    deeds: Optional[List[dict]],
    licensed_surveyor_name: Optional[str] = None
) -> Optional[str]:
    """
    DEPRECATED: Use generate_simplified_certification_text instead.
    """
    if not property_identification_type:
        if plan_number and deeds and len(deeds) > 0:
            property_identification_type = "plan_and_deed"
        elif plan_number:
            property_identification_type = "plan"
        elif deeds and len(deeds) > 0:
            property_identification_type = "deed"
        else:
            return None

    base_text = "I certify that the property inspected by me is identical to the property described in "

    has_deed = isinstance(deeds, list) and len(deeds) > 0
    deed_text = ""
    if has_deed:
        deed = deeds[0]
        deed_number = deed.get('deed_number', '') if isinstance(deed, dict) else getattr(deed, 'deed_number', '')
        deed_type = deed.get('deed_type', 'Deed') if isinstance(deed, dict) else getattr(deed, 'deed_type', 'Deed')
        deed_date = deed.get('deed_date', '') if isinstance(deed, dict) else getattr(deed, 'deed_date', '')

        if deed_number:
            deed_text = f"{deed_type} No. {deed_number}"
            if deed_date:
                deed_text += f" dated {deed_date}"

    if property_identification_type == "plan":
        if not plan_number:
            return None
        plan_ref = format_no_field("Plan", plan_number)
        text = base_text + plan_ref
        if plan_date:
            text += f" dated {plan_date}"
        if licensed_surveyor_name:
            text += f" made by {licensed_surveyor_name}, Licensed Surveyor"
        text += "."
        return text

    elif property_identification_type == "deed":
        if not deed_text:
            return None
        return base_text + deed_text + "."

    elif property_identification_type == "plan_and_deed":
        if not deed_text and not plan_number:
            return None

        if not deed_text and plan_number:
            plan_ref = format_no_field("Plan", plan_number)
            text = base_text + plan_ref
            if plan_date:
                text += f" dated {plan_date}"
            if licensed_surveyor_name:
                text += f" made by {licensed_surveyor_name}, Licensed Surveyor"
            text += "."
            return text

        if deed_text and not plan_number:
            return base_text + deed_text + "."

        plan_ref = format_no_field("Plan", plan_number)
        text = base_text + deed_text + " and identified in " + plan_ref
        if plan_date:
            text += f" dated {plan_date}"
        if licensed_surveyor_name:
            text += f" made by {licensed_surveyor_name}, Licensed Surveyor"
        text += "."
        return text

    elif property_identification_type == "certificate_of_sale":
        if not deed_text:
            return None
        return base_text + deed_text + "."

    return None


def get_pronoun(title: Optional[str]) -> Dict[str, str]:
    """
    Determine pronouns based on title.
    Returns: {'subject': 'he'/'she', 'object': 'him'/'her', 'possessive': 'his'/'her'}
    """
    if not title:
        return {'subject': 'he', 'object': 'him', 'possessive': 'his'}

    title_lower = title.lower().strip()

    if title_lower in ['mrs.', 'mrs', 'miss.', 'miss', 'ms.', 'ms']:
        return {'subject': 'she', 'object': 'her', 'possessive': 'her'}

    return {'subject': 'he', 'object': 'him', 'possessive': 'his'}


def generate_title_block(report: models.Report) -> list:
    """Generate the title block with support for plan/deed/certificate identification types"""
    lines = []
    lines.append("VALUATION REPORT")
    lines.append("of")

    id_type = report.property_identification_type
    if not id_type:
        if report.plan_number:
            id_type = "plan"
        elif report.deeds:
            id_type = "deed"
        else:
            id_type = "plan"

    if id_type == "plan" or id_type == "plan_and_deed":
        lot_desc = report.lot_number or '[Lot Number]'

        lot_desc_stripped = lot_desc.strip()
        prefixes_to_remove = ['plan no', 'plan no:', 'lot plan no', 'lot plan no:']
        lot_desc_lower = lot_desc_stripped.lower()
        for prefix in prefixes_to_remove:
            if lot_desc_lower.startswith(prefix):
                lot_desc = lot_desc_stripped[len(prefix):].strip()
                break

        if not lot_desc.lower().startswith('lot'):
            lot_desc = f"Lot {lot_desc}"

        plan_num = report.plan_number or '[Plan Number]'
        plan_formatted = format_no_field("Plan", plan_num)

        plan_date = report.plan_date or '[Date]'
        prop_desc = f"The Property Depicted as {lot_desc} in {plan_formatted} Dated {plan_date}"
        lines.append(prop_desc)

        surveyor = report.licensed_surveyor_name or '[Surveyor Name]'
        plan_info = f"made by {surveyor} Licensed Surveyor."
        lines.append(plan_info)

    elif id_type == "deed":
        deed_type = "Deed"
        deed_number = "[Deed Number]"
        deed_date = "[Date]"

        if report.deeds and isinstance(report.deeds, list) and len(report.deeds) > 0:
            first_deed = report.deeds[0]
            deed_type = first_deed.get('deed_type', 'Deed')
            deed_number = first_deed.get('deed_number', '[Deed Number]')
            deed_date = first_deed.get('deed_date', '[Date]')
        else:
            logger.warning(f"[DOCX] Report {report.id} has deed identification type but no deed data")

        deed_number_formatted = format_no_field("", deed_number, include_label=False)
        prop_desc = f"The Property Depicted as described in {deed_type} No. {deed_number_formatted} dated {deed_date}"
        lines.append(prop_desc)

    elif id_type == "certificate_of_sale":
        deed_number = "[Certificate Number]"
        deed_date = "[Date]"

        if report.deeds and isinstance(report.deeds, list) and len(report.deeds) > 0:
            first_deed = report.deeds[0]
            deed_number = first_deed.get('deed_number', '[Certificate Number]')
            deed_date = first_deed.get('deed_date', '[Date]')
        else:
            logger.warning(f"[DOCX] Report {report.id} has certificate_of_sale identification type but no deed data")

        cert_number_formatted = format_no_field("", deed_number, include_label=False)
        prop_desc = f"The Property Depicted as described in Certificate of Sale No. {cert_number_formatted} dated {deed_date}"
        lines.append(prop_desc)

    else:
        address = generate_smart_address(report) or '[Property Address]'
        prop_desc = f"The Property Depicted as {address}"
        lines.append(prop_desc)

    return lines


def generate_applicant_statement(report: models.Report) -> list:
    """Generate the applicant statement paragraph with smart grammar"""
    applicant_desc = f"{report.applicant_title or ''} {report.applicant_full_name or '[Applicant Name]'}".strip()

    if report.applicant_id_number and report.applicant_id_type:
        id_no_formatted = format_no_field("", report.applicant_id_number, include_label=False)
        id_info = f"holder {report.applicant_id_type} {id_no_formatted}"
    else:
        id_info = ""

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

    pronouns = get_pronoun(report.applicant_title)
    ownership_text = f"owned by {pronouns['object']}"

    property_type = report.property_type_valued or "immovable property"
    valuation_type = report.valuation_type or "Market Value"

    if id_info:
        paragraph1 = f"This Valuation Report is furnished at the request of {applicant_desc} {id_info} of {address_str}."
    else:
        paragraph1 = f"This Valuation Report is furnished at the request of {applicant_desc} of {address_str}."

    wish_text = f"{applicant_desc} wishes to know the {valuation_type} of {property_type} {ownership_text} in the Democratic Socialist Republic of Sri Lanka."

    if report.has_additional_owner == "yes" and report.additional_owner_names:
        wish_text = wish_text.replace(f"{ownership_text}", f"{ownership_text} & {pronouns['possessive']} family {report.additional_owner_names}")

    return [paragraph1, wish_text]


def generate_organization_side_introduction(report: models.Report) -> List[str]:
    """
    Generate organization-side introduction format.
    """
    paragraphs = []

    request_parts = []

    if report.submission_recipient_position:
        request_parts.append(report.submission_recipient_position)

    if report.submission_organization:
        request_parts.append(report.submission_organization)

    if report.submission_address:
        request_parts.append(report.submission_address)

    requester_text = ", ".join(request_parts) if request_parts else "[Requesting Organization]"

    purpose = report.valuation_purpose or "[purpose]"

    para1 = f"At the request of {requester_text}, I am furnishing a Valuation Report of the above property for the {purpose} purpose."
    paragraphs.append(para1)

    applicant_desc = f"{report.applicant_title or ''} {report.applicant_full_name or '[Applicant Name]'}".strip()

    id_text = ""
    if report.applicant_id_number and report.applicant_id_type:
        id_no_formatted = format_no_field("", report.applicant_id_number, include_label=False)
        id_text = f" holder {report.applicant_id_type} {id_no_formatted}"

    para2 = f"Applicant        :-{applicant_desc}{id_text}"
    paragraphs.append(para2)

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
    para3 = f"Address          :-{address_str}"
    paragraphs.append(para3)

    contact = report.applicant_contact_number or "[Contact Number]"
    para4 = f"Contact No       :-{contact}"
    paragraphs.append(para4)

    return paragraphs


def generate_multi_property_concluding_statement(
    report: models.Report,
    user: models.User,
    grand_total: float
) -> List[str]:
    """
    Generate concluding statement for multi-property CLIENT REQUEST reports.
    """
    if report.request_type != 'client_request':
        return []

    pronouns = get_pronoun(report.applicant_title)
    gender_pronoun = pronouns['possessive']

    title = report.applicant_title or "Mr."
    full_name = report.applicant_full_name or "[Applicant Name]"

    amount_words = format_currency_words(grand_total)

    statement = (
        f"Present Market Value of the Properties claimed by {title} {full_name} "
        f"& {gender_pronoun} family in the Democratic Socialist Republic of Sri Lanka "
        f"are in a sum of Lanka Rupees {amount_words} only."
    )

    honorific = user.honorific or ""
    valuer_name = user.full_name or "[Valuer Name]"
    designation = user.professional_designation or "[Professional Designation]"

    valuer_line = f"Vlr.{honorific} {valuer_name}".replace("  ", " ").strip()

    return [statement, valuer_line, designation]


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
        deeds_text = " & schedule of ".join(deed_parts)
        return f"requesting a Valuation Report of the immovable properties described in schedules of {deeds_text}."


def generate_submission_statement(report: models.Report) -> Optional[str]:
    """Generate submission destination statement with optional purpose and recipient position"""
    if not report.submission_organization:
        return None

    org_text = ""

    if report.submission_recipient_position:
        org_text = f"{report.submission_recipient_position}, "

    org_text += report.submission_organization

    if report.submission_address:
        org_text += f", {report.submission_address}"

    statement = f"This Valuation Report is to be submitted to {org_text}"

    if report.valuation_purpose:
        statement += f" for the purpose of {report.valuation_purpose}"

    statement += "."
    return statement
