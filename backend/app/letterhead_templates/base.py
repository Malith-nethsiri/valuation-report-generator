"""
Base classes for letterhead templates.
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from docx import Document
    from ..models import User, Report


class TemplateMetadata:
    """Metadata for a letterhead template."""

    def __init__(self, template_id: str, name: str, description: str, category: str = "professional"):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.category = category

    def to_dict(self):
        """Convert metadata to dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
        }


class BaseLetterheadTemplate(ABC):
    """Abstract base class for all letterhead templates."""

    @abstractmethod
    def get_metadata(self) -> TemplateMetadata:
        """Get template metadata."""
        pass

    @abstractmethod
    def render_letterhead(self, doc: 'Document', user: 'User', report: 'Report') -> None:
        """
        Render the letterhead into the document.

        Args:
            doc: python-docx Document instance
            user: User model instance with profile data
            report: Report model instance with report data
        """
        pass
