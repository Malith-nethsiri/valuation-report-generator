"""
Letterhead template registry.
"""

from typing import List
from .base import TemplateMetadata, BaseLetterheadTemplate
from .classic import ClassicTemplate
from .modern import ModernTemplate
from .minimal import MinimalTemplate
from .executive import ExecutiveTemplate
from .compact import CompactTemplate
from .premium import PremiumTemplate

# Default template ID
DEFAULT_TEMPLATE = "classic"

# Template instances registry
_TEMPLATE_INSTANCES = {
    'classic': ClassicTemplate(),
    'modern': ModernTemplate(),
    'minimal': MinimalTemplate(),
    'executive': ExecutiveTemplate(),
    'compact': CompactTemplate(),
    'premium': PremiumTemplate(),
}


def get_all_templates() -> List[TemplateMetadata]:
    """
    Get all available letterhead templates.

    Returns:
        List of TemplateMetadata objects
    """
    return [template.get_metadata() for template in _TEMPLATE_INSTANCES.values()]


def get_template_ids() -> List[str]:
    """
    Get list of all template IDs.

    Returns:
        List of template ID strings
    """
    return list(_TEMPLATE_INSTANCES.keys())


def get_template(template_id: str) -> BaseLetterheadTemplate:
    """
    Get a template instance by ID.

    Args:
        template_id: The template ID to retrieve

    Returns:
        BaseLetterheadTemplate instance

    Raises:
        ValueError: If template_id is not recognized
    """
    template = _TEMPLATE_INSTANCES.get(template_id)
    if template is None:
        # Default to classic if unknown template
        return _TEMPLATE_INSTANCES[DEFAULT_TEMPLATE]
    return template
