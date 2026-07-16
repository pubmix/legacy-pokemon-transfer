"""Validation checks for the first Generation I milestone."""

from __future__ import annotations

from legacy_migration.gen1.constants import (
    GEN1_SAVE_SIZE,
    MAIN_CHECKSUM_END_INCLUSIVE,
    MAIN_CHECKSUM_OFFSET,
    MAIN_CHECKSUM_START,
    PLAYER_ID_LENGTH,
    PLAYER_ID_OFFSET,
    PLAYER_NAME_LENGTH,
    PLAYER_NAME_OFFSET,
    TEXT_TERMINATOR,
)
from legacy_migration.models import ValidationCheck, ValidationReport


def _fits(data: bytes, offset: int, length: int) -> bool:
    return 0 <= offset <= len(data) and length >= 0 and offset + length <= len(data)


def calculate_main_checksum(data: bytes) -> int:
    """Calculate the documented 8-bit inverted main-data checksum."""
    total = sum(data[MAIN_CHECKSUM_START : MAIN_CHECKSUM_END_INCLUSIVE + 1])
    return (~total) & 0xFF


def validate_gen1_save(data: bytes) -> ValidationReport:
    """Run bounded first-milestone validation checks."""
    checks: list[ValidationCheck] = []
    warnings: list[str] = []
    errors: list[str] = []

    if len(data) == GEN1_SAVE_SIZE:
        checks.append(ValidationCheck("file_size", "PASS", "File is 32768 bytes."))
    else:
        message = f"Expected 32768 bytes, got {len(data)} bytes."
        checks.append(ValidationCheck("file_size", "FAIL", message))
        errors.append(message)

    unique_values = set(data)
    if len(data) == GEN1_SAVE_SIZE and unique_values <= {0x00, 0xFF}:
        message = (
            "File contains only 0x00/0xFF bytes and no plausible Pokemon save text data; "
            "this looks like a failed cartridge save dump or test pattern."
        )
        checks.append(ValidationCheck("content_plausibility", "FAIL", message))
        errors.append(message)
    elif len(data) == GEN1_SAVE_SIZE and TEXT_TERMINATOR not in data:
        message = (
            "File contains no legacy text terminator bytes; this is unlikely to be a "
            "valid English Generation I save."
        )
        checks.append(ValidationCheck("content_plausibility", "FAIL", message))
        errors.append(message)
    else:
        checks.append(
            ValidationCheck("content_plausibility", "PASS", "Basic byte-content check passed.")
        )

    required_ranges = {
        "player_name": (PLAYER_NAME_OFFSET, PLAYER_NAME_LENGTH),
        "trainer_id": (PLAYER_ID_OFFSET, PLAYER_ID_LENGTH),
        "main_checksum": (MAIN_CHECKSUM_OFFSET, 1),
    }
    for name, (offset, length) in required_ranges.items():
        if _fits(data, offset, length):
            checks.append(
                ValidationCheck(name, "PASS", f"Range 0x{offset:04X}+{length} is present.")
            )
        else:
            message = f"Range 0x{offset:04X}+{length} is outside the file."
            checks.append(ValidationCheck(name, "FAIL", message))
            errors.append(message)

    if _fits(data, MAIN_CHECKSUM_OFFSET, 1) and _fits(
        data, MAIN_CHECKSUM_START, MAIN_CHECKSUM_END_INCLUSIVE - MAIN_CHECKSUM_START + 1
    ):
        expected = data[MAIN_CHECKSUM_OFFSET]
        actual = calculate_main_checksum(data)
        if expected == actual:
            checks.append(ValidationCheck("main_checksum", "PASS", "Main-data checksum matches."))
        else:
            message = (
                f"Main-data checksum mismatch: stored 0x{expected:02X}, "
                f"calculated 0x{actual:02X}."
            )
            checks.append(ValidationCheck("main_checksum", "WARN", message))
            warnings.append(message)

    overall = "FAIL" if errors else "PASS"
    return ValidationReport(
        overall_status=overall,
        checks=tuple(checks),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
