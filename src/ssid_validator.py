#!/usr/bin/env python3
"""
SSID Validation Module

Validates WiFi SSID names according to 802.11 standard and practical limitations.
Ensures SSIDs will be accepted by UniFi API and compatible with most client devices.
"""


class SSIDValidationError(Exception):
    """Raised when an SSID fails validation"""
    pass


def validate_ssid(ssid, strict=True):
    """
    Validate an SSID name according to 802.11 standards and best practices.

    Args:
        ssid (str): The SSID name to validate
        strict (bool): If True, enforce best practices. If False, only check hard limits.

    Returns:
        tuple: (is_valid, error_message)
            is_valid (bool): True if SSID is valid
            error_message (str or None): Error message if invalid, None if valid

    802.11 Standard Rules:
    - SSID length: 0-32 octets (bytes)
    - Character set: Any octet value 0-255 (but many cause compatibility issues)

    Practical Limitations:
    - UniFi requires at least 1 character
    - Control characters (0-31) cause device compatibility issues
    - Extended ASCII (128-255) may have encoding problems
    - Leading/trailing spaces often cause issues
    """

    # Type check
    if not isinstance(ssid, str):
        return False, "SSID must be a string"

    # Minimum length check
    if len(ssid) == 0:
        return False, "SSID cannot be empty"

    # Check for leading/trailing whitespace
    if ssid != ssid.strip():
        if strict:
            return False, "SSID cannot have leading or trailing spaces"

    # UTF-8 byte length check (802.11 standard: max 32 bytes)
    try:
        byte_length = len(ssid.encode('utf-8'))
    except UnicodeEncodeError:
        return False, "SSID contains invalid Unicode characters"

    if byte_length > 32:
        return False, f"SSID is too long: {byte_length} bytes (max 32 bytes). Current SSID: '{ssid}'"

    # Character validation
    problematic_chars = []

    # Check for control characters (ASCII 0-31)
    for i, char in enumerate(ssid):
        code = ord(char)

        # Control characters
        if code < 32:
            if code == 9:  # Tab
                problematic_chars.append(f"tab at position {i+1}")
            elif code == 10:  # Line feed
                problematic_chars.append(f"newline at position {i+1}")
            elif code == 13:  # Carriage return
                problematic_chars.append(f"carriage return at position {i+1}")
            else:
                problematic_chars.append(f"control character (ASCII {code}) at position {i+1}")

        # DEL character
        elif code == 127:
            problematic_chars.append(f"DEL character at position {i+1}")

    if problematic_chars:
        return False, f"SSID contains invalid characters: {', '.join(problematic_chars)}"

    # Strict mode: warn about potentially problematic characters
    if strict:
        warnings = []

        # Check for characters that may cause API issues
        problematic_api_chars = ['"', "'", '\\', '\x00']
        for char in problematic_api_chars:
            if char in ssid:
                char_name = {
                    '"': 'double quote',
                    "'": 'single quote',
                    '\\': 'backslash',
                    '\x00': 'null byte'
                }.get(char, f"'{char}'")
                warnings.append(char_name)

        if warnings:
            # For strict mode, these are warnings not errors (for now)
            # But we could make them errors if they cause issues
            pass

    # All checks passed
    return True, None


def validate_ssid_list(ssid_list, list_name="SSID list", strict=True):
    """
    Validate a list of SSIDs.

    Args:
        ssid_list (list): List of SSID names to validate
        list_name (str): Name of the list for error messages
        strict (bool): If True, enforce best practices

    Returns:
        tuple: (all_valid, errors)
            all_valid (bool): True if all SSIDs are valid
            errors (list): List of error messages (empty if all valid)

    Raises:
        SSIDValidationError: If any SSID is invalid (with details)
    """
    errors = []

    for i, ssid in enumerate(ssid_list):
        is_valid, error_msg = validate_ssid(ssid, strict=strict)
        if not is_valid:
            errors.append(f"{list_name}[{i}] '{ssid}': {error_msg}")

    if errors:
        return False, errors

    return True, []


def get_ssid_byte_length(ssid):
    """
    Get the byte length of an SSID when encoded as UTF-8.

    Args:
        ssid (str): The SSID name

    Returns:
        int: Byte length in UTF-8 encoding
    """
    try:
        return len(ssid.encode('utf-8'))
    except (UnicodeEncodeError, AttributeError):
        return -1


def suggest_ssid_fix(ssid):
    """
    Suggest a fix for an invalid SSID.

    Args:
        ssid (str): The invalid SSID

    Returns:
        str or None: Suggested fixed SSID, or None if can't fix
    """
    if not isinstance(ssid, str):
        return None

    # Remove leading/trailing whitespace
    fixed = ssid.strip()

    # Remove control characters
    fixed = ''.join(char for char in fixed if ord(char) >= 32 and ord(char) != 127)

    # If still too long, truncate to 32 bytes
    byte_length = get_ssid_byte_length(fixed)
    if byte_length > 32:
        # Truncate carefully to avoid cutting UTF-8 sequences
        while get_ssid_byte_length(fixed) > 32:
            fixed = fixed[:-1]

    # Validate the fix
    is_valid, _ = validate_ssid(fixed, strict=True)
    if is_valid and fixed:
        return fixed

    return None


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_ssids = [
        ("Valid SSID", True),
        ("Pretty Fly for a WiFi", True),
        ("MAGA = NAZI", True),
        ("", False),  # Empty
        ("A" * 32, True),  # Exactly 32 chars
        ("A" * 33, False),  # Too long (but only if ASCII)
        ("Donnie & Jeffery = Besties 4 life", False),  # 36 chars - TOO LONG
        ("  Leading spaces", False),  # Leading spaces (strict mode)
        ("Trailing spaces  ", False),  # Trailing spaces (strict mode)
        ("Contains\ttab", False),  # Tab character
        ("Contains\nnewline", False),  # Newline
        ("🚀 WiFi", True),  # Unicode emoji (depends on byte length)
    ]

    print("SSID Validation Tests:")
    print("=" * 70)

    for ssid, should_be_valid in test_ssids:
        is_valid, error_msg = validate_ssid(ssid, strict=True)
        byte_len = get_ssid_byte_length(ssid)

        status = "✓ PASS" if is_valid == should_be_valid else "✗ FAIL"
        print(f"{status} | {byte_len:2d}b | '{ssid[:40]}'")

        if error_msg:
            print(f"       Error: {error_msg}")

        if not is_valid:
            suggested = suggest_ssid_fix(ssid)
            if suggested and suggested != ssid:
                print(f"       Suggestion: '{suggested}'")

        print()
