"""Typed data models shared by parsers and presentation layers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceMetadata:
    """Metadata about where raw save bytes came from."""

    source_type: str
    display_name: str
    is_read_only: bool
    details: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationCheck:
    """One validation check result."""

    name: str
    status: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    """Structured validation status for a save."""

    overall_status: str
    checks: tuple[ValidationCheck, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class SaveMetadata:
    """Metadata derived from the source save without mutating it."""

    source_filename: str
    file_size: int
    sha256: str
    detected_game: str
    detected_region: str
    parser_version: str
    validation_status: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RawOffset:
    """Location of a parsed field in the original save bytes."""

    offset: int
    length: int


@dataclass(frozen=True)
class Trainer:
    """Trainer fields parsed for the first milestone."""

    name: str
    trainer_id: int
    play_time: str | None = None
    badges: int | None = None
    pokedex_owned_count: int | None = None
    pokedex_seen_count: int | None = None
    raw_offsets: dict[str, RawOffset] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PokemonLocation:
    """Source location for a Pokemon record."""

    kind: str
    source_offset: int
    party_slot: int | None = None
    box_number: int | None = None
    box_slot: int | None = None


@dataclass(frozen=True)
class PokemonRecord:
    """Parsed Pokemon fields with raw bytes preserved for later export."""

    local_id: str
    species_index: int
    species_name: str | None
    nickname: str | None
    original_trainer: str | None
    trainer_id: int | None
    level: int | None
    experience: int | None
    moves: tuple[int, ...]
    current_hp: int | None
    status: int | None
    determinant_values: int | None
    stat_experience: dict[str, int]
    source_location: PokemonLocation
    raw_record_hex: str
    parsing_warnings: tuple[str, ...] = ()
