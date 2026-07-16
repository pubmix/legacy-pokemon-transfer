"""Generation I party Pokemon parsing."""

from __future__ import annotations

from legacy_migration.errors import ParseError
from legacy_migration.gen1.constants import (
    PARTY_DATA_LENGTH,
    PARTY_DATA_OFFSET,
    PARTY_MAX_COUNT,
    PARTY_NAME_LENGTH,
    PARTY_NICKNAMES_OFFSET,
    PARTY_OT_NAMES_OFFSET,
    PARTY_RECORD_LENGTH,
    PARTY_RECORDS_OFFSET,
    PARTY_SPECIES_LIST_OFFSET,
    PARTY_SPECIES_TERMINATOR,
    PARTY_SPECIES_TERMINATOR_OFFSET,
)
from legacy_migration.gen1.species import GEN1_SPECIES_NAMES
from legacy_migration.gen1.text_codec import decode_gen1_text
from legacy_migration.models import PokemonLocation, PokemonRecord


def _slice_checked(data: bytes, offset: int, length: int, field_name: str) -> bytes:
    if offset < 0 or length < 0 or offset + length > len(data):
        raise ParseError(f"{field_name} range 0x{offset:04X}+{length} is outside the save.")
    return data[offset : offset + length]


def _read_u16(raw: bytes, offset: int) -> int:
    return int.from_bytes(raw[offset : offset + 2], byteorder="big")


def _read_u24(raw: bytes, offset: int) -> int:
    return int.from_bytes(raw[offset : offset + 3], byteorder="big")


def parse_party_pokemon(data: bytes) -> tuple[PokemonRecord, ...]:
    """Parse the current party Pokemon records from a Generation I save."""
    _slice_checked(data, PARTY_DATA_OFFSET, PARTY_DATA_LENGTH, "party data")
    party_count = data[PARTY_DATA_OFFSET]
    if party_count > PARTY_MAX_COUNT:
        raise ParseError(f"Invalid party count {party_count}; expected 0..{PARTY_MAX_COUNT}.")

    terminator = data[PARTY_SPECIES_TERMINATOR_OFFSET]
    shared_warnings: list[str] = []
    if terminator != PARTY_SPECIES_TERMINATOR:
        shared_warnings.append(
            "Party species list terminator is not 0xFF; party data may be inconsistent."
        )

    records: list[PokemonRecord] = []
    for index in range(party_count):
        species_from_list = data[PARTY_SPECIES_LIST_OFFSET + index]
        record_offset = PARTY_RECORDS_OFFSET + (index * PARTY_RECORD_LENGTH)
        raw_record = _slice_checked(
            data, record_offset, PARTY_RECORD_LENGTH, f"party Pokemon {index + 1}"
        )

        warnings = list(shared_warnings)
        species_from_record = raw_record[0]
        if species_from_record != species_from_list:
            warnings.append(
                "Species ID in party list does not match species ID in Pokemon record."
            )

        nickname_offset = PARTY_NICKNAMES_OFFSET + (index * PARTY_NAME_LENGTH)
        ot_name_offset = PARTY_OT_NAMES_OFFSET + (index * PARTY_NAME_LENGTH)
        nickname, nickname_warnings = decode_gen1_text(
            _slice_checked(data, nickname_offset, PARTY_NAME_LENGTH, "party nickname")
        )
        original_trainer, ot_warnings = decode_gen1_text(
            _slice_checked(data, ot_name_offset, PARTY_NAME_LENGTH, "party OT name")
        )
        warnings.extend(f"Nickname: {warning}" for warning in nickname_warnings)
        warnings.extend(f"Original trainer: {warning}" for warning in ot_warnings)

        species_name = GEN1_SPECIES_NAMES.get(species_from_record)
        if species_name is None:
            warnings.append(f"Unknown or unsupported species index 0x{species_from_record:02X}.")

        records.append(
            PokemonRecord(
                local_id=f"party-{index + 1}",
                species_index=species_from_record,
                species_name=species_name,
                nickname=nickname,
                original_trainer=original_trainer,
                trainer_id=_read_u16(raw_record, 0x0C),
                level=raw_record[0x21],
                experience=_read_u24(raw_record, 0x0E),
                moves=tuple(raw_record[0x08:0x0C]),
                current_hp=_read_u16(raw_record, 0x01),
                status=raw_record[0x04],
                determinant_values=_read_u16(raw_record, 0x1B),
                stat_experience={
                    "hp": _read_u16(raw_record, 0x11),
                    "attack": _read_u16(raw_record, 0x13),
                    "defense": _read_u16(raw_record, 0x15),
                    "speed": _read_u16(raw_record, 0x17),
                    "special": _read_u16(raw_record, 0x19),
                },
                source_location=PokemonLocation(
                    kind="party",
                    source_offset=record_offset,
                    party_slot=index + 1,
                ),
                raw_record_hex=raw_record.hex(),
                parsing_warnings=tuple(warnings),
            )
        )

    return tuple(records)
