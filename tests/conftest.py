from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from legacy_migration.gen1.constants import (  # noqa: E402
    CURRENT_BOX_DATA_OFFSET,
    GEN1_SAVE_SIZE,
    MAIN_CHECKSUM_END_INCLUSIVE,
    MAIN_CHECKSUM_OFFSET,
    MAIN_CHECKSUM_START,
    PARTY_DATA_OFFSET,
    PARTY_NAME_LENGTH,
    PARTY_NICKNAMES_OFFSET,
    PARTY_OT_NAMES_OFFSET,
    PARTY_RECORDS_OFFSET,
    PARTY_SPECIES_LIST_OFFSET,
    PARTY_SPECIES_TERMINATOR_OFFSET,
    PLAYER_ID_OFFSET,
    PLAYER_NAME_OFFSET,
)
from legacy_migration.gen1.constants import (  # noqa: E402
    STORED_BOX_OFFSETS as GEN1_STORED_BOX_OFFSETS,
)
from legacy_migration.gen1.text_codec import encode_fixture_text  # noqa: E402
from legacy_migration.gen2.constants import (  # noqa: E402
    CRYSTAL_LAYOUT,
    GEN2_SAVE_SIZE,
    GOLD_SILVER_LAYOUT,
    PRIMARY_CHECKSUM_START,
    Gen2Layout,
)
from legacy_migration.gen2.constants import (  # noqa: E402
    PLAYER_NAME_LENGTH as GEN2_PLAYER_NAME_LENGTH,
)
from legacy_migration.gen2.constants import (  # noqa: E402
    PLAYER_NAME_OFFSET as GEN2_PLAYER_NAME_OFFSET,
)
from legacy_migration.gen2.constants import (  # noqa: E402
    STORED_BOX_OFFSETS as GEN2_STORED_BOX_OFFSETS,
)
from legacy_migration.gen2.constants import (  # noqa: E402
    TRAINER_ID_OFFSET as GEN2_TRAINER_ID_OFFSET,
)

FIXTURES = ROOT / "tests" / "fixtures"


def _put_u16_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 8) & 0xFF
    data[offset + 1] = value & 0xFF


def _put_u16_le(data: bytearray, offset: int, value: int) -> None:
    data[offset] = value & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF


def _put_u24_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 16) & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF
    data[offset + 2] = value & 0xFF


def _refresh_gen1_main_checksum(data: bytearray) -> None:
    checksum = 0xFF
    for value in data[MAIN_CHECKSUM_START : MAIN_CHECKSUM_END_INCLUSIVE + 1]:
        checksum = (checksum - value) & 0xFF
    data[MAIN_CHECKSUM_OFFSET] = checksum


def _refresh_gen2_primary_checksum(data: bytearray, layout: Gen2Layout) -> None:
    checksum = sum(data[PRIMARY_CHECKSUM_START : layout.primary_checksum_end_inclusive + 1])
    _put_u16_le(data, layout.primary_checksum_offset, checksum & 0xFFFF)


def _write_gen1_fixture(path: Path) -> None:
    data = bytearray([0x50] * GEN1_SAVE_SIZE)
    data[PLAYER_NAME_OFFSET : PLAYER_NAME_OFFSET + PARTY_NAME_LENGTH] = encode_fixture_text(
        "TEST", PARTY_NAME_LENGTH
    )
    _put_u16_be(data, PLAYER_ID_OFFSET, 12345)

    data[PARTY_DATA_OFFSET] = 1
    data[PARTY_SPECIES_LIST_OFFSET] = 0x54
    data[PARTY_SPECIES_TERMINATOR_OFFSET] = 0xFF
    record_offset = PARTY_RECORDS_OFFSET
    data[record_offset] = 0x54
    _put_u16_be(data, record_offset + 0x01, 20)
    data[record_offset + 0x04] = 0
    data[record_offset + 0x08] = 84
    data[record_offset + 0x09] = 45
    _put_u16_be(data, record_offset + 0x0C, 12345)
    _put_u24_be(data, record_offset + 0x0E, 125)
    data[record_offset + 0x1B] = 0xAA
    data[record_offset + 0x1C] = 0xAA
    data[record_offset + 0x1D] = 30
    data[record_offset + 0x1E] = 25
    data[record_offset + 0x21] = 5

    data[PARTY_OT_NAMES_OFFSET : PARTY_OT_NAMES_OFFSET + PARTY_NAME_LENGTH] = encode_fixture_text(
        "TEST", PARTY_NAME_LENGTH
    )
    data[PARTY_NICKNAMES_OFFSET : PARTY_NICKNAMES_OFFSET + PARTY_NAME_LENGTH] = (
        encode_fixture_text("SPARKY", PARTY_NAME_LENGTH)
    )
    data[CURRENT_BOX_DATA_OFFSET] = 0
    data[CURRENT_BOX_DATA_OFFSET + 1] = 0xFF
    for box_offset in GEN1_STORED_BOX_OFFSETS:
        data[box_offset] = 0
        data[box_offset + 1] = 0xFF

    _refresh_gen1_main_checksum(data)
    path.write_bytes(data)


def _write_gen2_fixture(
    path: Path,
    *,
    layout: Gen2Layout,
    trainer: str,
    species: int,
    nickname: str,
    move_one: int,
) -> None:
    data = bytearray([0x50] * GEN2_SAVE_SIZE)
    _put_u16_be(data, GEN2_TRAINER_ID_OFFSET, 12345)
    data[GEN2_PLAYER_NAME_OFFSET : GEN2_PLAYER_NAME_OFFSET + GEN2_PLAYER_NAME_LENGTH] = (
        encode_fixture_text(trainer, GEN2_PLAYER_NAME_LENGTH)
    )

    data[layout.party_offset] = 1
    data[layout.party_species_list_offset] = species
    data[layout.party_species_list_offset + 1] = 0xFF
    record_offset = layout.party_records_offset
    data[record_offset] = species
    data[record_offset + 0x02] = move_one
    data[record_offset + 0x03] = 45
    _put_u16_be(data, record_offset + 0x06, 12345)
    _put_u24_be(data, record_offset + 0x08, 125)
    data[record_offset + 0x15] = 0xAA
    data[record_offset + 0x16] = 0xAA
    data[record_offset + 0x17] = 35
    data[record_offset + 0x18] = 25
    data[record_offset + 0x1F] = 5
    data[record_offset + 0x20] = 0
    _put_u16_be(data, record_offset + 0x22, 20)

    data[layout.party_ot_names_offset : layout.party_ot_names_offset + 0x0B] = (
        encode_fixture_text(trainer, 0x0B)
    )
    data[layout.party_nicknames_offset : layout.party_nicknames_offset + 0x0B] = (
        encode_fixture_text(nickname, 0x0B)
    )
    for box_offset in (layout.current_box_offset, *GEN2_STORED_BOX_OFFSETS):
        data[box_offset] = 0
        data[box_offset + 1] = 0xFF

    _refresh_gen2_primary_checksum(data, layout)
    path.write_bytes(data)


def _ensure_synthetic_fixtures() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    _write_gen1_fixture(FIXTURES / "sample_gen1.sav")
    _write_gen2_fixture(
        FIXTURES / "sample_crystal.sav",
        layout=CRYSTAL_LAYOUT,
        trainer="KRIS",
        species=152,
        nickname="LEAFY",
        move_one=33,
    )
    _write_gen2_fixture(
        FIXTURES / "sample_gold_silver.sav",
        layout=GOLD_SILVER_LAYOUT,
        trainer="GOLD",
        species=155,
        nickname="BLAZE",
        move_one=52,
    )
    (FIXTURES / "truncated.sav").write_bytes(bytes([1, 2, 3, 4, 5]))


_ensure_synthetic_fixtures()
