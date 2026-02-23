"""
File upload security validation utilities.

Validates uploaded files for correct type, size, and magic number.
"""
import os
from typing import Optional

from fastapi import HTTPException, UploadFile, status

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MAX_FILES_PER_UPLOAD = 10

ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/jpg',
    'application/pdf'
}

ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.jfif', '.png', '.webp', '.pdf'
}

# Mapping of magic number signatures to MIME types
MAGIC_NUMBER_SIGNATURES = {
    b'\xFF\xD8\xFF': 'image/jpeg',       # JPEG
    b'\x89PNG\r\n\x1a\n': 'image/png',   # PNG
    b'RIFF': 'image/webp',               # WEBP (needs additional check)
    b'%PDF': 'application/pdf',          # PDF
}


def verify_file_type_by_magic_number(file_content: bytes) -> Optional[str]:
    """
    Verify file type using magic number (file signature).

    Returns MIME type if valid, None otherwise.
    """
    for signature, mime_type in MAGIC_NUMBER_SIGNATURES.items():
        if file_content.startswith(signature):
            # Special handling for WEBP (check for WEBP after RIFF)
            if signature == b'RIFF' and len(file_content) >= 12:
                if file_content[8:12] == b'WEBP':
                    return mime_type
                else:
                    continue  # Not a WEBP file
            return mime_type

    return None


async def validate_upload_file(file: UploadFile) -> None:
    """
    Validate uploaded file for security.

    Checks:
    - File size (≤ 10MB)
    - File extension is allowed
    - Magic number matches extension (prevents file type spoofing)

    Raises HTTPException if validation fails.
    """
    # Read file content for validation
    file_content = await file.read()
    file_size = len(file_content)

    # Reset file pointer for later use
    await file.seek(0)

    # 1. Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File '{file.filename}' is too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB, got {file_size / (1024*1024):.2f}MB"
        )

    # 2. Check file extension
    filename_lower = file.filename.lower() if file.filename else ""
    file_ext = os.path.splitext(filename_lower)[1]

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' has unsupported extension '{file_ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 3. Verify magic number (actual file type)
    detected_mime = verify_file_type_by_magic_number(file_content)

    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' appears to be a different type than its extension suggests. File validation failed for security reasons."
        )

    # 4. Cross-check: ensure declared content type matches detected type
    if file.content_type and detected_mime:
        # Normalize content types (some browsers send image/jpg instead of image/jpeg)
        declared_type = file.content_type.lower()
        if declared_type == 'image/jpg':
            declared_type = 'image/jpeg'

        if declared_type != detected_mime and not (declared_type.startswith('image/') and detected_mime.startswith('image/')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}' type mismatch. Declared: {file.content_type}, Detected: {detected_mime}"
            )
