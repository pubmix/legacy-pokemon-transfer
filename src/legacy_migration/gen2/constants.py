"""Named English/Western Generation II save-format constants."""

from __future__ import annotations

from dataclasses import dataclass

GEN2_SAVE_SIZE = 0x8000

TRAINER_ID_OFFSET = 0x2008
TRAINER_ID_LENGTH = 0x02
PLAYER_NAME_OFFSET = 0x200B
PLAYER_NAME_LENGTH = 0x0B

PARTY_LENGTH = 428
PARTY_MAX_COUNT = 6
PARTY_RECORD_LENGTH = 0x30
PARTY_NAME_LENGTH = 0x0B
PARTY_SPECIES_TERMINATOR = 0xFF

BOX_LENGTH = 0x450
BOX_MAX_COUNT = 20
BOX_RECORD_LENGTH = 0x20
BOX_NAME_LENGTH = 0x0B
BOX_SPECIES_TERMINATOR = 0xFF
BOX_RECORDS_RELATIVE_OFFSET = 0x16
BOX_OT_NAMES_RELATIVE_OFFSET = BOX_RECORDS_RELATIVE_OFFSET + (BOX_MAX_COUNT * BOX_RECORD_LENGTH)
BOX_NICKNAMES_RELATIVE_OFFSET = BOX_OT_NAMES_RELATIVE_OFFSET + (BOX_MAX_COUNT * BOX_NAME_LENGTH)
STORED_BOX_OFFSETS = (
    0x4000,
    0x4450,
    0x48A0,
    0x4CF0,
    0x5140,
    0x5590,
    0x59E0,
    0x6000,
    0x6450,
    0x68A0,
    0x6CF0,
    0x7140,
    0x7590,
    0x79E0,
)

PRIMARY_CHECKSUM_START = 0x2009


@dataclass(frozen=True)
class Gen2Layout:
    """Offsets that differ between English/Western Gen II save variants."""

    game: str
    region: str
    party_offset: int
    current_box_offset: int
    johto_badges_offset: int
    kanto_badges_offset: int
    primary_checksum_end_inclusive: int
    primary_checksum_offset: int

    @property
    def party_species_list_offset(self) -> int:
        return self.party_offset + 0x01

    @property
    def party_records_offset(self) -> int:
        return self.party_offset + 0x08

    @property
    def party_ot_names_offset(self) -> int:
        return self.party_records_offset + (PARTY_MAX_COUNT * PARTY_RECORD_LENGTH)

    @property
    def party_nicknames_offset(self) -> int:
        return self.party_ot_names_offset + (PARTY_MAX_COUNT * PARTY_NAME_LENGTH)


GOLD_SILVER_LAYOUT = Gen2Layout(
    game="Gold/Silver-compatible",
    region="English/Western Gold/Silver layout assumed",
    party_offset=0x288A,
    current_box_offset=0x2D6C,
    johto_badges_offset=0x23E4,
    kanto_badges_offset=0x23E5,
    primary_checksum_end_inclusive=0x2D68,
    primary_checksum_offset=0x2D69,
)

CRYSTAL_LAYOUT = Gen2Layout(
    game="Crystal-compatible",
    region="English/Western Crystal layout assumed",
    party_offset=0x2865,
    current_box_offset=0x2D10,
    johto_badges_offset=0x23E5,
    kanto_badges_offset=0x23E6,
    primary_checksum_end_inclusive=0x2B82,
    primary_checksum_offset=0x2D0D,
)
