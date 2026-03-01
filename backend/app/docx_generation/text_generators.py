"""
Text generators — re-exports from domain-specific submodules.

Public API is unchanged; callers that import from this module continue to work.
  - valuation_text:  legal aspects + land values
  - situation_text:  situation / location / access / locality / boundary
  - deed_text:       deed, certification, title block, applicant, org intro
  - signature_block: signature block
"""
from .valuation_text import (
    generate_ownership_paragraph,
    generate_street_lines_paragraph,
    generate_building_limits_paragraph,
    generate_local_authority_paragraph,
    generate_rent_act_paragraph,
    generate_land_values_paragraph,
)
from .situation_text import (
    generate_situation_text,
    generate_smart_address,
    generate_access_text,
    generate_locality_description,
    generate_boundary_summary_text,
)
from .deed_text import (
    generate_simplified_certification_text,
    generate_certificate_of_identity_text,
    get_pronoun,
    generate_title_block,
    generate_applicant_statement,
    generate_organization_side_introduction,
    generate_multi_property_concluding_statement,
    generate_deed_description,
    generate_submission_statement,
)
from .signature_block import add_signature_block

__all__ = [
    "generate_ownership_paragraph",
    "generate_street_lines_paragraph",
    "generate_building_limits_paragraph",
    "generate_local_authority_paragraph",
    "generate_rent_act_paragraph",
    "generate_land_values_paragraph",
    "generate_situation_text",
    "generate_smart_address",
    "generate_access_text",
    "generate_locality_description",
    "generate_boundary_summary_text",
    "generate_simplified_certification_text",
    "generate_certificate_of_identity_text",
    "get_pronoun",
    "generate_title_block",
    "generate_applicant_statement",
    "generate_organization_side_introduction",
    "generate_multi_property_concluding_statement",
    "generate_deed_description",
    "generate_submission_statement",
    "add_signature_block",
]
