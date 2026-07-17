from __future__ import annotations

from pathlib import Path

import pytest

from legacy_migration.errors import ParseError
from legacy_migration.gen1.boxes import parse_box_pokemon
from legacy_migration.gen1.constants import (
    CURRENT_BOX_DATA_OFFSET,
    PARTY_DATA_OFFSET,
    STORED_BOX_OFFSETS,
)
from legacy_migration.gen1.pokemon import parse_party_pokemon
from legacy_migration.gen1.species import GEN1_SPECIES_NAMES
from legacy_migration.gen1.text_codec import encode_fixture_text


def _put_u16_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 8) & 0xFF
    data[offset + 1] = value & 0xFF


def _put_u24_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 16) & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF
    data[offset + 2] = value & 0xFF


def _gen1_fixture_with_boxed_charmander() -> bytes:
    data = bytearray(Path("tests/fixtures/sample_gen1.sav").read_bytes())
    data[CURRENT_BOX_DATA_OFFSET] = 0
    data[CURRENT_BOX_DATA_OFFSET + 1] = 0xFF
    for empty_box_offset in STORED_BOX_OFFSETS:
        data[empty_box_offset] = 0
        data[empty_box_offset + 1] = 0xFF

    box_offset = STORED_BOX_OFFSETS[0]
    data[box_offset] = 1
    data[box_offset + 1] = 0xB0
    data[box_offset + 2] = 0xFF

    record_offset = box_offset + 0x16
    data[record_offset] = 0xB0
    _put_u16_be(data, record_offset + 0x01, 19)
    data[record_offset + 0x03] = 5
    data[record_offset + 0x04] = 0
    data[record_offset + 0x08] = 10
    data[record_offset + 0x09] = 45
    _put_u16_be(data, record_offset + 0x0C, 12345)
    _put_u24_be(data, record_offset + 0x0E, 125)
    data[record_offset + 0x1B] = 0xAA
    data[record_offset + 0x1C] = 0xAA
    data[record_offset + 0x1D] = 35
    data[record_offset + 0x1E] = 25

    ot_offset = box_offset + 0x2AA
    nickname_offset = box_offset + 0x386
    data[ot_offset : ot_offset + 0x0B] = encode_fixture_text("TEST", 0x0B)
    data[nickname_offset : nickname_offset + 0x0B] = encode_fixture_text("CHAR", 0x0B)
    return bytes(data)


def test_parse_party_pokemon_from_fixture() -> None:
    data = Path("tests/fixtures/sample_gen1.sav").read_bytes()

    records = parse_party_pokemon(data)

    assert len(records) == 1
    record = records[0]
    assert record.local_id == "party-1"
    assert record.source_location.kind == "party"
    assert record.source_location.party_slot == 1
    assert record.nickname == "SPARKY"
    assert record.original_trainer == "TEST"
    assert record.species_index == 0x54
    assert record.species_name == "Pikachu"
    assert record.level == 5
    assert record.current_hp == 20
    assert record.trainer_id == 12345
    assert record.parsing_warnings == ()


def test_gen1_species_table_covers_internal_indices() -> None:
    assert GEN1_SPECIES_NAMES[0x99] == "Bulbasaur"
    assert GEN1_SPECIES_NAMES[0xB0] == "Charmander"
    assert GEN1_SPECIES_NAMES[0xB1] == "Squirtle"
    assert GEN1_SPECIES_NAMES[0x15] == "Mew"


def test_parses_gen1_stored_box_fixture() -> None:
    records = parse_box_pokemon(_gen1_fixture_with_boxed_charmander())

    assert len(records) == 1
    record = records[0]
    assert record.local_id == "box-1-1"
    assert record.source_location.box_number == 1
    assert record.source_location.box_slot == 1
    assert record.species_name == "Charmander"
    assert record.nickname == "CHAR"
    assert record.original_trainer == "TEST"
    assert record.trainer_id == 12345
    assert record.level == 5
    assert record.current_hp == 19
    assert record.parsing_warnings == ()


def test_gen1_box_parser_skips_uninitialized_stored_boxes() -> None:
    data = bytearray(_gen1_fixture_with_boxed_charmander())
    data[STORED_BOX_OFFSETS[1]] = 0xFF

    records = parse_box_pokemon(bytes(data))

    assert len(records) == 1
    assert records[0].local_id == "box-1-1"


def test_gen1_box_parser_skips_uninitialized_current_box() -> None:
    data = bytearray(_gen1_fixture_with_boxed_charmander())
    data[CURRENT_BOX_DATA_OFFSET] = 0xFF

    records = parse_box_pokemon(bytes(data))

    assert len(records) == 1
    assert records[0].local_id == "box-1-1"


def test_invalid_party_count_is_rejected() -> None:
    data = bytearray(Path("tests/fixtures/sample_gen1.sav").read_bytes())
    data[PARTY_DATA_OFFSET] = 7

    with pytest.raises(ParseError, match="Invalid party count"):
        parse_party_pokemon(bytes(data))
