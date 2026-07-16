"""English/Western Generation II party Pokemon parsing."""

from __future__ import annotations

from legacy_migration.errors import ParseError
from legacy_migration.gen1.text_codec import decode_gen1_text
from legacy_migration.gen2.constants import (
    BOX_LENGTH,
    BOX_MAX_COUNT,
    BOX_NAME_LENGTH,
    BOX_NICKNAMES_RELATIVE_OFFSET,
    BOX_OT_NAMES_RELATIVE_OFFSET,
    BOX_RECORD_LENGTH,
    BOX_RECORDS_RELATIVE_OFFSET,
    BOX_SPECIES_TERMINATOR,
    PARTY_LENGTH,
    PARTY_MAX_COUNT,
    PARTY_NAME_LENGTH,
    PARTY_RECORD_LENGTH,
    PARTY_SPECIES_TERMINATOR,
    STORED_BOX_OFFSETS,
    Gen2Layout,
)
from legacy_migration.gen2.species import GEN2_SPECIES_NAMES
from legacy_migration.models import PokemonLocation, PokemonRecord


def _slice_checked(data: bytes, offset: int, length: int, field_name: str) -> bytes:
    if offset < 0 or length < 0 or offset + length > len(data):
        raise ParseError(f"{field_name} range 0x{offset:04X}+{length} is outside the save.")
    return data[offset : offset + length]


def _read_u16(raw: bytes, offset: int) -> int:
    return int.from_bytes(raw[offset : offset + 2], byteorder="big")


def _read_u24(raw: bytes, offset: int) -> int:
    return int.from_bytes(raw[offset : offset + 3], byteorder="big")


def parse_gen2_party_pokemon(data: bytes, layout: Gen2Layout) -> tuple[PokemonRecord, ...]:
    """Parse current party Pokemon records from a supported English/Western Gen II save."""
    _slice_checked(data, layout.party_offset, PARTY_LENGTH, "party data")
    party_count = data[layout.party_offset]
    if party_count > PARTY_MAX_COUNT:
        raise ParseError(
            f"Invalid Gen II party count {party_count}; expected 0..{PARTY_MAX_COUNT}."
        )

    terminator_offset = layout.party_species_list_offset + party_count
    shared_warnings: list[str] = []
    if data[terminator_offset] != PARTY_SPECIES_TERMINATOR:
        shared_warnings.append(
            "Party species list terminator after count is not 0xFF; party data may be inconsistent."
        )

    records: list[PokemonRecord] = []
    for index in range(party_count):
        species_from_list = data[layout.party_species_list_offset + index]
        record_offset = layout.party_records_offset + (index * PARTY_RECORD_LENGTH)
        raw_record = _slice_checked(
            data, record_offset, PARTY_RECORD_LENGTH, f"Gen II party Pokemon {index + 1}"
        )
        warnings = list(shared_warnings)
        species_from_record = raw_record[0]
        if species_from_record != species_from_list:
            warnings.append(
                "Species ID in party list does not match species ID in Pokemon record."
            )

        nickname_offset = layout.party_nicknames_offset + (index * PARTY_NAME_LENGTH)
        ot_name_offset = layout.party_ot_names_offset + (index * PARTY_NAME_LENGTH)
        nickname, nickname_warnings = decode_gen1_text(
            _slice_checked(data, nickname_offset, PARTY_NAME_LENGTH, "party nickname")
        )
        original_trainer, ot_warnings = decode_gen1_text(
            _slice_checked(data, ot_name_offset, PARTY_NAME_LENGTH, "party OT name")
        )
        warnings.extend(f"Nickname: {warning}" for warning in nickname_warnings)
        warnings.extend(f"Original trainer: {warning}" for warning in ot_warnings)

        species_name = GEN2_SPECIES_NAMES.get(species_from_record)
        if species_name is None:
            warnings.append(f"Unknown or unsupported species index 0x{species_from_record:02X}.")

        records.append(
            PokemonRecord(
                local_id=f"party-{index + 1}",
                species_index=species_from_record,
                species_name=species_name,
                nickname=nickname,
                original_trainer=original_trainer,
                trainer_id=_read_u16(raw_record, 0x06),
                level=raw_record[0x1F],
                experience=_read_u24(raw_record, 0x08),
                moves=tuple(raw_record[0x02:0x06]),
                current_hp=_read_u16(raw_record, 0x22),
                status=raw_record[0x20],
                determinant_values=_read_u16(raw_record, 0x15),
                stat_experience={
                    "hp": _read_u16(raw_record, 0x0B),
                    "attack": _read_u16(raw_record, 0x0D),
                    "defense": _read_u16(raw_record, 0x0F),
                    "speed": _read_u16(raw_record, 0x11),
                    "special": _read_u16(raw_record, 0x13),
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


def _parse_gen2_box_at(
    data: bytes,
    *,
    box_offset: int,
    box_number: int | None,
    label: str,
    local_id_prefix: str,
) -> tuple[PokemonRecord, ...]:
    _slice_checked(data, box_offset, BOX_LENGTH, f"{label} data")
    box_count = data[box_offset]
    if box_count > BOX_MAX_COUNT:
        raise ParseError(f"Invalid {label} count {box_count}; expected 0..{BOX_MAX_COUNT}.")

    terminator_offset = box_offset + 1 + box_count
    shared_warnings: list[str] = []
    if data[terminator_offset] != BOX_SPECIES_TERMINATOR:
        shared_warnings.append(
            f"{label} species list terminator after count is not 0xFF; "
            "box data may be inconsistent."
        )

    records: list[PokemonRecord] = []
    for index in range(box_count):
        species_from_list = data[box_offset + 1 + index]
        record_offset = box_offset + BOX_RECORDS_RELATIVE_OFFSET + (index * BOX_RECORD_LENGTH)
        raw_record = _slice_checked(
            data, record_offset, BOX_RECORD_LENGTH, f"{label} Pokemon {index + 1}"
        )
        warnings = list(shared_warnings)
        species_from_record = raw_record[0]
        if species_from_record != species_from_list:
            warnings.append(
                "Species ID in box list does not match species ID in Pokemon record."
            )

        nickname_offset = box_offset + BOX_NICKNAMES_RELATIVE_OFFSET + (index * BOX_NAME_LENGTH)
        ot_name_offset = box_offset + BOX_OT_NAMES_RELATIVE_OFFSET + (index * BOX_NAME_LENGTH)
        nickname, nickname_warnings = decode_gen1_text(
            _slice_checked(data, nickname_offset, BOX_NAME_LENGTH, "box nickname")
        )
        original_trainer, ot_warnings = decode_gen1_text(
            _slice_checked(data, ot_name_offset, BOX_NAME_LENGTH, "box OT name")
        )
        warnings.extend(f"Nickname: {warning}" for warning in nickname_warnings)
        warnings.extend(f"Original trainer: {warning}" for warning in ot_warnings)

        species_name = GEN2_SPECIES_NAMES.get(species_from_record)
        if species_name is None:
            warnings.append(f"Unknown or unsupported species index 0x{species_from_record:02X}.")

        records.append(
            PokemonRecord(
                local_id=f"{local_id_prefix}-{index + 1}",
                species_index=species_from_record,
                species_name=species_name,
                nickname=nickname,
                original_trainer=original_trainer,
                trainer_id=_read_u16(raw_record, 0x06),
                level=raw_record[0x1F],
                experience=_read_u24(raw_record, 0x08),
                moves=tuple(raw_record[0x02:0x06]),
                current_hp=None,
                status=None,
                determinant_values=_read_u16(raw_record, 0x15),
                stat_experience={
                    "hp": _read_u16(raw_record, 0x0B),
                    "attack": _read_u16(raw_record, 0x0D),
                    "defense": _read_u16(raw_record, 0x0F),
                    "speed": _read_u16(raw_record, 0x11),
                    "special": _read_u16(raw_record, 0x13),
                },
                source_location=PokemonLocation(
                    kind="box",
                    source_offset=record_offset,
                    box_number=box_number,
                    box_slot=index + 1,
                ),
                raw_record_hex=raw_record.hex(),
                parsing_warnings=tuple(warnings),
            )
        )

    return tuple(records)


def parse_gen2_current_box_pokemon(data: bytes, layout: Gen2Layout) -> tuple[PokemonRecord, ...]:
    """Parse the loaded/current PC box from a supported English/Western Gen II save."""
    return _parse_gen2_box_at(
        data,
        box_offset=layout.current_box_offset,
        box_number=None,
        label="current box",
        local_id_prefix="current-box",
    )


def parse_gen2_stored_box_pokemon(data: bytes) -> tuple[PokemonRecord, ...]:
    """Parse stored PC boxes 1-14 from a supported English/Western Gen II save."""
    records: list[PokemonRecord] = []
    for box_index, box_offset in enumerate(STORED_BOX_OFFSETS, start=1):
        records.extend(
            _parse_gen2_box_at(
                data,
                box_offset=box_offset,
                box_number=box_index,
                label=f"box {box_index}",
                local_id_prefix=f"box-{box_index}",
            )
        )
    return tuple(records)


def parse_gen2_box_pokemon(data: bytes, layout: Gen2Layout) -> tuple[PokemonRecord, ...]:
    """Parse current and stored PC boxes from a supported English/Western Gen II save."""
    return parse_gen2_current_box_pokemon(data, layout) + parse_gen2_stored_box_pokemon(data)
