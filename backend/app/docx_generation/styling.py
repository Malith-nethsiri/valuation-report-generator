from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
from matplotlib.pylab import size

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

# ===== FONT SIZE CONFIGURATION =====
# Standardized font sizes (10-14pt range) for professional reports

# Document title and headings
FONT_SIZE_DOCUMENT_TITLE = Pt(14)        # "VALUATION REPORT" title
FONT_SIZE_SECTION_HEADING = Pt(13)       # Major sections (1.0, 2.0, 3.0...)
FONT_SIZE_SUBSECTION_HEADING = Pt(12)    # Subsections (4.1, 4.2...)

# Body content
FONT_SIZE_BODY = Pt(12)                  # Standard body text
FONT_SIZE_INLINE_LABEL = Pt(12)          # Bold labels in inline fields
FONT_SIZE_VALUATION = Pt(12)             # Valuation calculation lines

# Tables
FONT_SIZE_TABLE_HEADER = Pt(12)          # Table header cells
FONT_SIZE_TABLE_CELL = Pt(11)            # Table content cells
FONT_SIZE_INVOICE_TOTAL = Pt(12)         # Invoice subtotals and totals

# Other elements
FONT_SIZE_CAPTION = Pt(10)               # Image/photo captions
FONT_SIZE_BANK_HEADER = Pt(12)           # Bank account section header
FONT_SIZE_BANK_DETAILS = Pt(11)          # Bank account details
FONT_SIZE_SIGNATURE = Pt(12)             # Signature line and label
FONT_SIZE_CERTIFICATION = Pt(12)         # Certification text


def add_border_to_paragraph(paragraph: Paragraph, border_position: str = "bottom", size: int = 12, color: str = "000000"):
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
