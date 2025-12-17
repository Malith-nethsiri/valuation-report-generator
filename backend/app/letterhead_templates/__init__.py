"""
Letterhead template registry.
"""

from typing import List
from .base import TemplateMetadata, BaseLetterheadTemplate

# Default template ID
DEFAULT_TEMPLATE = "classic"

# Hardcoded template metadata for now
_TEMPLATE_METADATA = [
    TemplateMetadata(
        template_id="classic",
        name="Classic Professional",
        description="Traditional centered layout with dual borders",
        category="traditional"
    ),
    TemplateMetadata(
        template_id="modern",
        name="Modern Professional",
        description="Contemporary left-aligned design with clean lines",
        category="modern"
    ),
    TemplateMetadata(
        template_id="minimal",
        name="Minimal Elegant",
        description="Ultra-clean centered design without borders",
        category="minimal"
    ),
    TemplateMetadata(
        template_id="executive",
        name="Executive Bold",
        description="Bold centered layout with double-line borders",
        category="executive"
    ),
    TemplateMetadata(
        template_id="compact",
        name="Compact Professional",
        description="Space-efficient layout with smaller fonts",
        category="compact"
    ),
    TemplateMetadata(
        template_id="premium",
        name="Premium Signature",
        description="Sophisticated left-aligned with decorative elements",
        category="premium"
    ),
]


def get_all_templates() -> List[TemplateMetadata]:
    """
    Get all available letterhead templates.

    Returns:
        List of TemplateMetadata objects
    """
    return _TEMPLATE_METADATA


def get_template_ids() -> List[str]:
    """
    Get list of all template IDs.

    Returns:
        List of template ID strings
    """
    return [t.template_id for t in _TEMPLATE_METADATA]


def get_template(template_id: str) -> str:
    """
    Get a template by ID.
    For now, just returns the template_id if valid, raises exception otherwise.

    Args:
        template_id: The template ID to retrieve

    Returns:
        The template ID (placeholder until full implementation)

    Raises:
        ValueError: If template_id is not recognized
    """
    valid_ids = get_template_ids()
    if template_id not in valid_ids:
        raise ValueError(f"Template '{template_id}' not found. Valid templates: {valid_ids}")
    return template_id
