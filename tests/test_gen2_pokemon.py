from __future__ import annotations

from pathlib import Path

from legacy_migration.gen1.text_codec import encode_fixture_text
from legacy_migration.gen2.constants import CRYSTAL_LAYOUT, GOLD_SILVER_LAYOUT, STORED_BOX_OFFSETS
from legacy_migration.gen2.pokemon import parse_gen2_box_pokemon, parse_gen2_party_pokemon
from legacy_migration.gen2.species import GEN2_SPECIES_NAMES


def _put_u16_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 8) & 0xFF
    data[offset + 1] = value & 0xFF


def _put_u24_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 16) & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF
    data[offset + 2] = value & 0xFF


def _crystal_fixture_with_boxed_sentret() -> bytes:
    data = bytearray(Path("tests/fixtures/sample_crystal.sav").read_bytes())
    for empty_box_offset in (CRYSTAL_LAYOUT.current_box_offset, *STORED_BOX_OFFSETS):
        data[empty_box_offset] = 0
        data[empty_box_offset + 1] = 0xFF

    box_offset = 0x4000
    data[box_offset] = 1
    data[box_offset + 1] = 161
    data[box_offset + 2] = 0xFF

    record_offset = box_offset + 0x16
    data[record_offset] = 161
    data[record_offset + 1] = 0
    data[record_offset + 2] = 33
    data[record_offset + 3] = 45
    data[record_offset + 4] = 0
    data[record_offset + 5] = 0
    _put_u16_be(data, record_offset + 0x06, 12345)
    _put_u24_be(data, record_offset + 0x08, 64)
    _put_u16_be(data, record_offset + 0x0B, 0)
    _put_u16_be(data, record_offset + 0x0D, 0)
    _put_u16_be(data, record_offset + 0x0F, 0)
    _put_u16_be(data, record_offset + 0x11, 0)
    _put_u16_be(data, record_offset + 0x13, 0)
    data[record_offset + 0x15] = 0xAA
    data[record_offset + 0x16] = 0xAA
    data[record_offset + 0x17] = 35
    data[record_offset + 0x18] = 30
    data[record_offset + 0x19] = 0
    data[record_offset + 0x1A] = 0
    data[record_offset + 0x1B] = 70
    data[record_offset + 0x1C] = 0
    data[record_offset + 0x1D] = 0x85
    data[record_offset + 0x1E] = 0x81
    data[record_offset + 0x1F] = 2

    ot_offset = box_offset + 0x16 + (20 * 0x20)
    nickname_offset = ot_offset + (20 * 0x0B)
    data[ot_offset : ot_offset + 0x0B] = encode_fixture_text("KRIS", 0x0B)
    data[nickname_offset : nickname_offset + 0x0B] = encode_fixture_text("SENTRET", 0x0B)
    return bytes(data)


def test_parses_crystal_party_fixture() -> None:
    data = Path("tests/fixtures/sample_crystal.sav").read_bytes()

    records = parse_gen2_party_pokemon(data, CRYSTAL_LAYOUT)

    assert len(records) == 1
    record = records[0]
    assert record.local_id == "party-1"
    assert record.species_name == "Chikorita"
    assert record.nickname == "LEAFY"
    assert record.original_trainer == "KRIS"
    assert record.trainer_id == 12345
    assert record.level == 5


def test_gen2_species_table_covers_full_national_dex_range() -> None:
    assert GEN2_SPECIES_NAMES[1] == "Bulbasaur"
    assert GEN2_SPECIES_NAMES[151] == "Mew"
    assert GEN2_SPECIES_NAMES[152] == "Chikorita"
    assert GEN2_SPECIES_NAMES[251] == "Celebi"


def test_parses_gold_silver_party_fixture() -> None:
    data = Path("tests/fixtures/sample_gold_silver.sav").read_bytes()

    records = parse_gen2_party_pokemon(data, GOLD_SILVER_LAYOUT)

    assert len(records) == 1
    record = records[0]
    assert record.local_id == "party-1"
    assert record.species_name == "Cyndaquil"
    assert record.nickname == "BLAZE"
    assert record.original_trainer == "GOLD"
    assert record.trainer_id == 12345
    assert record.level == 5


def test_parses_crystal_stored_box_fixture() -> None:
    data = _crystal_fixture_with_boxed_sentret()

    records = parse_gen2_box_pokemon(data, CRYSTAL_LAYOUT)

    assert len(records) == 1
    record = records[0]
    assert record.local_id == "box-1-1"
    assert record.source_location.box_number == 1
    assert record.source_location.box_slot == 1
    assert record.species_name == "Sentret"
    assert record.nickname == "SENTRET"
    assert record.original_trainer == "KRIS"
    assert record.trainer_id == 12345
    assert record.level == 2
    assert record.current_hp is None
