"""Validation checks for English/Western Generation II saves."""

from __future__ import annotations

from legacy_migration.gen2.constants import (
    GEN2_SAVE_SIZE,
    PARTY_LENGTH,
    PLAYER_NAME_LENGTH,
    PLAYER_NAME_OFFSET,
    PRIMARY_CHECKSUM_START,
    TRAINER_ID_LENGTH,
    TRAINER_ID_OFFSET,
    Gen2Layout,
)
from legacy_migration.models import ValidationCheck, ValidationReport


def _fits(data: bytes, offset: int, length: int) -> bool:
    return 0 <= offset <= len(data) and length >= 0 and offset + length <= len(data)


def calculate_primary_checksum(data: bytes, layout: Gen2Layout) -> int:
    """Calculate the documented 16-bit checksum for the selected Gen II layout."""
    checksum_range = data[PRIMARY_CHECKSUM_START : layout.primary_checksum_end_inclusive + 1]
    return sum(checksum_range) & 0xFFFF


def primary_checksum_matches(data: bytes, layout: Gen2Layout) -> bool:
    """Return whether the selected layout's primary checksum is present and valid."""
    if not _fits(data, layout.primary_checksum_offset, 2):
        return False
    if not _fits(
        data,
        PRIMARY_CHECKSUM_START,
        layout.primary_checksum_end_inclusive - PRIMARY_CHECKSUM_START + 1,
    ):
        return False
    stored = int.from_bytes(
        data[layout.primary_checksum_offset : layout.primary_checksum_offset + 2],
        byteorder="little",
    )
    return stored == calculate_primary_checksum(data, layout)


def validate_gen2_save(data: bytes, layout: Gen2Layout) -> ValidationReport:
    """Run bounded validation checks for a supported English/Western Gen II layout."""
    checks: list[ValidationCheck] = []
    warnings: list[str] = []
    errors: list[str] = []

    if len(data) == GEN2_SAVE_SIZE:
        checks.append(ValidationCheck("file_size", "PASS", "File is 32768 bytes."))
    else:
        message = f"Expected 32768 bytes, got {len(data)} bytes."
        checks.append(ValidationCheck("file_size", "FAIL", message))
        errors.append(message)

    required_ranges = {
        "trainer_id": (TRAINER_ID_OFFSET, TRAINER_ID_LENGTH),
        "player_name": (PLAYER_NAME_OFFSET, PLAYER_NAME_LENGTH),
        "party": (layout.party_offset, PARTY_LENGTH),
        "primary_checksum": (layout.primary_checksum_offset, 2),
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

    if _fits(data, layout.primary_checksum_offset, 2):
        stored = int.from_bytes(
            data[layout.primary_checksum_offset : layout.primary_checksum_offset + 2],
            byteorder="little",
        )
        actual = calculate_primary_checksum(data, layout)
        if stored == actual:
            checks.append(
                ValidationCheck("primary_checksum", "PASS", f"{layout.game} checksum matches.")
            )
        else:
            message = (
                f"{layout.game} checksum mismatch: stored 0x{stored:04X}, "
                f"calculated 0x{actual:04X}."
            )
            checks.append(ValidationCheck("primary_checksum", "FAIL", message))
            errors.append(message)

    overall = "FAIL" if errors else "PASS"
    return ValidationReport(
        overall_status=overall,
        checks=tuple(checks),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )
