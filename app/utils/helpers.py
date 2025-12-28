import re
from typing import Optional


def format_phone_number(phone: str) -> str:
    """
    Format phone number to digits only (for WhatsApp API)
    Removes +, -, spaces, parentheses
    """
    return re.sub(r"[^\d]", "", phone)


def is_valid_phone_number(phone: str) -> bool:
    """Validate phone number (10-15 digits)"""
    formatted = format_phone_number(phone)
    return 10 <= len(formatted) <= 15


def format_currency(amount: float) -> str:
    """Format amount as currency (RM)"""
    return f"RM {amount:,.2f}"


def validate_sst_number(sst_no: str) -> bool:
    """Validate SST registration number (basic check)"""
    if not sst_no:
        return False
    # Malaysian SST format: ST followed by numbers (e.g., ST00123456789)
    pattern = r"^ST\d{10,12}$"
    return re.match(pattern, sst_no.upper()) is not None
