import re


def _validate_password_common(password: str) -> str:
    from ..auth import validate_password_strength
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_msg)
    return password


def sanitize_dangerous_characters(value: str) -> str:
    """Remove dangerous characters that could be used for injection attacks"""
    if not value:
        return value
    dangerous_chars = ['<', '>', '{', '}', '(', ')', ';']
    for char in dangerous_chars:
        value = value.replace(char, '')
    return value.strip()


def validate_sri_lankan_nic(value: str) -> bool:
    """Validate Sri Lankan NIC format (old: 9 digits + V/X, new: 12 digits)"""
    if not value:
        return True
    old_pattern = r'^\d{9}[VvXx]$'
    new_pattern = r'^\d{12}$'
    return bool(re.match(old_pattern, value) or re.match(new_pattern, value))


def validate_passport(value: str) -> bool:
    """Validate passport format (6-12 alphanumeric characters) - INTERNATIONAL SUPPORT"""
    if not value:
        return True
    value = value.strip()
    pattern = r'^[A-Z0-9]{6,12}$'
    return bool(re.match(pattern, value.upper()))


def validate_date_format(value: str) -> bool:
    """
    Validate date format DD-MM-YYYY.
    Returns True if valid or empty, False otherwise.
    """
    if not value:
        return True
    value = value.strip()
    pattern = r'^(\d{2})-(\d{2})-(\d{4})$'
    match = re.match(pattern, value)
    if not match:
        return False
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False
    if year < 1900 or year > 2100:
        return False
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        days_in_month[1] = 29
    if day > days_in_month[month - 1]:
        return False
    return True


def normalize_date_format(value: str) -> str:
    """
    Normalize date to DD-MM-YYYY format.
    Handles common input formats: DD/MM/YYYY, DD.MM.YYYY, YYYY-MM-DD
    """
    if not value:
        return value
    value = value.strip()
    if re.match(r'^\d{2}-\d{2}-\d{4}$', value):
        return value
    match = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', value)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.match(r'^(\d{2})\.(\d{2})\.(\d{4})$', value)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', value)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return value


def validate_id_number(id_type: str, id_number: str) -> tuple[bool, str]:
    """
    Validate ID number based on ID type.
    Returns (is_valid, error_message).
    """
    if not id_number:
        return True, ""
    if not id_type:
        return True, ""
    id_number = id_number.strip()
    id_type_upper = id_type.upper()
    if id_type_upper == 'NIC':
        if not validate_sri_lankan_nic(id_number):
            return False, "Invalid NIC format. Use old format (9 digits + V/X) or new format (12 digits)"
    elif id_type_upper == 'PASSPORT':
        if not validate_passport(id_number):
            return False, "Invalid passport format. Must be 6-12 alphanumeric characters"
    elif id_type_upper == 'OTHER':
        if len(id_number) < 3:
            return False, "ID number must be at least 3 characters"
    return True, ""
