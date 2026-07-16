"""Trainer parsing for Generation I Red/Blue/Yellow-compatible saves."""

from __future__ import annotations

from legacy_migration.errors import ParseError
from legacy_migration.gen1.constants import (
    BADGES_OFFSET,
    PLAYER_ID_LENGTH,
    PLAYER_ID_OFFSET,
    PLAYER_NAME_LENGTH,
    PLAYER_NAME_OFFSET,
)
from legacy_migration.gen1.text_codec import decode_gen1_text
from legacy_migration.models import RawOffset, Trainer


def _slice_checked(data: bytes, offset: int, length: int, field_name: str) -> bytes:
    if offset < 0 or length < 0 or offset + length > len(data):
        raise ParseError(f"{field_name} range 0x{offset:04X}+{length} is outside the save.")
    return data[offset : offset + length]


def parse_trainer(data: bytes) -> Trainer:
    """Parse the trainer fields in scope for milestone one."""
    raw_name = _slice_checked(data, PLAYER_NAME_OFFSET, PLAYER_NAME_LENGTH, "trainer name")
    name, name_warnings = decode_gen1_text(raw_name)
    raw_id = _slice_checked(data, PLAYER_ID_OFFSET, PLAYER_ID_LENGTH, "trainer ID")
    trainer_id = int.from_bytes(raw_id, byteorder="big")
    badges = data[BADGES_OFFSET] if len(data) > BADGES_OFFSET else None

    return Trainer(
        name=name,
        trainer_id=trainer_id,
        badges=badges,
        raw_offsets={
            "name": RawOffset(PLAYER_NAME_OFFSET, PLAYER_NAME_LENGTH),
            "trainer_id": RawOffset(PLAYER_ID_OFFSET, PLAYER_ID_LENGTH),
        },
        warnings=name_warnings,
    )
