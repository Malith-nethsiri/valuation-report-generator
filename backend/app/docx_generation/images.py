from io import BytesIO
from docx.shared import Inches
from PIL import Image


def calculate_image_dimensions(image_stream: BytesIO, max_width: float, max_height: float):
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


def apply_letterbox_to_image(image_stream: BytesIO, target_width: float, target_height: float):
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
    current_pos = image_stream.tell()

    try:

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

