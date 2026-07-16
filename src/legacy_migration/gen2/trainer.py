"""Trainer parsing for English/Western Generation II saves."""

from __future__ import annotations

from legacy_migration.errors import ParseError
from legacy_migration.gen1.text_codec import decode_gen1_text
from legacy_migration.gen2.constants import (
    PLAYER_NAME_LENGTH,
    PLAYER_NAME_OFFSET,
    TRAINER_ID_LENGTH,
    TRAINER_ID_OFFSET,
    Gen2Layout,
)
from legacy_migration.models import RawOffset, Trainer


def _slice_checked(data: bytes, offset: int, length: int, field_name: str) -> bytes:
    if offset < 0 or length < 0 or offset + length > len(data):
        raise ParseError(f"{field_name} range 0x{offset:04X}+{length} is outside the save.")
    return data[offset : offset + length]


def parse_gen2_trainer(data: bytes, layout: Gen2Layout) -> Trainer:
    """Parse Gen II trainer fields in scope for this milestone."""
    raw_name = _slice_checked(data, PLAYER_NAME_OFFSET, PLAYER_NAME_LENGTH, "trainer name")
    name, name_warnings = decode_gen1_text(raw_name)
    raw_id = _slice_checked(data, TRAINER_ID_OFFSET, TRAINER_ID_LENGTH, "trainer ID")
    trainer_id = int.from_bytes(raw_id, byteorder="big")
    johto_badges = data[layout.johto_badges_offset] if len(data) > layout.johto_badges_offset else 0
    kanto_badges = data[layout.kanto_badges_offset] if len(data) > layout.kanto_badges_offset else 0

    return Trainer(
        name=name,
        trainer_id=trainer_id,
        badges=(johto_badges << 8) | kanto_badges,
        raw_offsets={
            "name": RawOffset(PLAYER_NAME_OFFSET, PLAYER_NAME_LENGTH),
            "trainer_id": RawOffset(TRAINER_ID_OFFSET, TRAINER_ID_LENGTH),
        },
        warnings=name_warnings,
    )
