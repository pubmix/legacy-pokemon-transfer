"""Command-line interface for the legacy migration POC."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from legacy_migration import PARSER_VERSION
from legacy_migration.errors import LegacyMigrationError
from legacy_migration.gen1.boxes import parse_box_pokemon
from legacy_migration.gen1.detection import detect_save
from legacy_migration.gen1.pokemon import parse_party_pokemon
from legacy_migration.gen1.trainer import parse_trainer
from legacy_migration.gen1.validation import validate_gen1_save
from legacy_migration.gen2.constants import GEN2_SAVE_SIZE, Gen2Layout
from legacy_migration.gen2.detection import detect_gen2_save
from legacy_migration.gen2.pokemon import parse_gen2_box_pokemon, parse_gen2_party_pokemon
from legacy_migration.gen2.trainer import parse_gen2_trainer
from legacy_migration.gen2.validation import validate_gen2_save
from legacy_migration.hashing import sha256_file
from legacy_migration.migration_package import export_migration_package
from legacy_migration.models import (
    PokemonRecord,
    SaveMetadata,
    SourceMetadata,
    Trainer,
    ValidationReport,
)
from legacy_migration.save_reader import FileSaveSource, read_source_with_hash

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedSaveContext:
    """A detected and validated save plus the parser path selected for it."""

    data: bytes
    digest: str
    source_size: int
    source_metadata: SourceMetadata
    generation: str
    format_name: str
    game: str
    region: str
    confidence: str
    validation: ValidationReport
    detection_warnings: tuple[str, ...]
    gen2_layout: Gen2Layout | None = None


def _normalize_save_bytes(data: bytes) -> tuple[bytes, tuple[str, ...]]:
    """Return parser bytes and warnings for supported non-mutating source wrappers."""
    if len(data) == GEN2_SAVE_SIZE + 48:
        return data[:GEN2_SAVE_SIZE], (
            "Source file has 48 trailing bytes, likely emulator RTC metadata; "
            "parsing the first 32768 save bytes while preserving the source hash.",
        )
    return data, ()


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="legacy-migration")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a read-only Pokemon save.")
    inspect_parser.add_argument("save_path", type=Path)
    inspect_parser.set_defaults(func=inspect_command)

    list_parser = subparsers.add_parser(
        "list-pokemon", help="List parsed Pokemon from a read-only Pokemon save."
    )
    list_parser.add_argument("save_path", type=Path)
    list_parser.add_argument(
        "--include-boxes",
        action="store_true",
        help="Include supported PC box Pokemon records in addition to party records.",
    )
    list_parser.set_defaults(func=list_pokemon_command)

    export_parser = subparsers.add_parser(
        "export", help="Export selected Pokemon into an offline migration-candidate package."
    )
    export_parser.add_argument("save_path", type=Path)
    export_parser.add_argument(
        "--pokemon-id",
        action="append",
        required=True,
        help="Local Pokemon ID to export, such as party-1. May be provided more than once.",
    )
    export_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory where a new migration package directory will be created.",
    )
    export_parser.add_argument(
        "--include-boxes",
        action="store_true",
        help="Allow selecting supported PC box Pokemon IDs as well as party IDs.",
    )
    export_parser.set_defaults(func=export_command)

    return parser


def _read_supported_save(save_path: Path) -> ParsedSaveContext:
    """Read and validate a supported save before command-specific parsing."""
    source = FileSaveSource(save_path)
    source_data, digest, source_metadata = read_source_with_hash(source)
    data, normalization_warnings = _normalize_save_bytes(source_data)

    gen2_detection = detect_gen2_save(data)
    if gen2_detection.supported:
        if gen2_detection.layout is None:
            raise LegacyMigrationError("Generation II detection did not select a layout.")
        validation = validate_gen2_save(data, gen2_detection.layout)
        if validation.errors:
            raise LegacyMigrationError("; ".join(validation.errors))
        return ParsedSaveContext(
            data=data,
            digest=digest,
            source_size=len(source_data),
            source_metadata=source_metadata,
            generation="gen2",
            format_name=gen2_detection.format_name,
            game=gen2_detection.game,
            region=gen2_detection.region,
            confidence=gen2_detection.confidence,
            validation=validation,
            detection_warnings=normalization_warnings + gen2_detection.warnings,
            gen2_layout=gen2_detection.layout,
        )

    detection = detect_save(data)
    validation = validate_gen1_save(data)
    if not detection.supported:
        messages = tuple(gen2_detection.warnings) + tuple(detection.warnings)
        raise LegacyMigrationError("; ".join(messages))
    if validation.errors:
        raise LegacyMigrationError("; ".join(validation.errors))

    return ParsedSaveContext(
        data=data,
        digest=digest,
        source_size=len(source_data),
        source_metadata=source_metadata,
        generation="gen1",
        format_name=detection.format_name,
        game=detection.game,
        region=detection.region,
        confidence=detection.confidence,
        validation=validation,
        detection_warnings=normalization_warnings + detection.warnings,
    )


def _parse_trainer(context: ParsedSaveContext) -> Trainer:
    if context.generation == "gen1":
        return parse_trainer(context.data)
    if context.generation == "gen2" and context.gen2_layout is not None:
        return parse_gen2_trainer(context.data, context.gen2_layout)
    raise LegacyMigrationError("No trainer parser is available for this save.")


def _parse_pokemon_records(
    context: ParsedSaveContext, *, include_boxes: bool = False
) -> tuple[PokemonRecord, ...]:
    if context.generation == "gen1":
        records = parse_party_pokemon(context.data)
        if include_boxes:
            records += parse_box_pokemon(context.data)
        return records
    if context.generation == "gen2" and context.gen2_layout is not None:
        records = parse_gen2_party_pokemon(context.data, context.gen2_layout)
        if include_boxes:
            records += parse_gen2_box_pokemon(context.data, context.gen2_layout)
        return records
    raise LegacyMigrationError("No Pokemon parser is available for this save.")


def _format_record_location(record: PokemonRecord) -> str:
    location = record.source_location
    if location.kind == "party":
        return f"Party {location.party_slot}"
    if location.kind == "box" and location.box_number is None:
        return f"Current Box {location.box_slot}"
    if location.kind == "box":
        return f"Box {location.box_number} Slot {location.box_slot}"
    return location.kind


def _build_save_metadata(
    context: ParsedSaveContext, trainer: Trainer | None = None
) -> SaveMetadata:
    trainer_warnings = trainer.warnings if trainer is not None else ()
    warnings = context.detection_warnings + context.validation.warnings + trainer_warnings
    return SaveMetadata(
        source_filename=context.source_metadata.display_name,
        file_size=context.source_size,
        sha256=context.digest,
        detected_game=context.game,
        detected_region=context.region,
        parser_version=PARSER_VERSION,
        validation_status=context.validation.overall_status,
        warnings=warnings,
    )


def inspect_command(args: argparse.Namespace) -> int:
    """Run the inspect command."""
    context = _read_supported_save(args.save_path)
    trainer = _parse_trainer(context)
    metadata = _build_save_metadata(context, trainer)

    print(f"File: {metadata.source_filename}")
    print(f"Source: {context.source_metadata.source_type}")
    print(f"Source read-only: {context.source_metadata.is_read_only}")
    print(f"Size: {metadata.file_size} bytes")
    if context.source_size != len(context.data):
        print(f"Parsed save bytes: {len(context.data)} bytes")
    print(f"SHA-256: {metadata.sha256}")
    print(f"Format: {context.format_name}")
    print(f"Game: {metadata.detected_game}")
    print(f"Detection confidence: {context.confidence}")
    print(f"Trainer: {trainer.name}")
    print(f"Trainer ID: {trainer.trainer_id}")
    print(f"Validation: {metadata.validation_status}")
    print(f"Warnings: {len(metadata.warnings)}")
    for warning in metadata.warnings:
        print(f"- {warning}")

    return 0


def list_pokemon_command(args: argparse.Namespace) -> int:
    """Run the list-pokemon command for currently supported party records."""
    context = _read_supported_save(args.save_path)
    records = _parse_pokemon_records(context, include_boxes=args.include_boxes)

    headers = ["ID", "Location", "Nickname", "Species", "Level", "OT", "Trainer ID", "Warnings"]
    rows = []
    for record in records:
        species = record.species_name or f"0x{record.species_index:02X}"
        rows.append(
            [
                record.local_id,
                _format_record_location(record),
                record.nickname or "",
                species,
                str(record.level) if record.level is not None else "",
                record.original_trainer or "",
                str(record.trainer_id) if record.trainer_id is not None else "",
                str(len(record.parsing_warnings)),
            ]
        )

    if not rows:
        if args.include_boxes:
            print("No party or boxed Pokemon found.")
        else:
            print("No party Pokemon found.")
        return 0

    widths = [
        max(len(headers[column]), *(len(row[column]) for row in rows))
        for column in range(len(headers))
    ]
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))

    return 0


def export_command(args: argparse.Namespace) -> int:
    """Run the export command for selected parsed Pokemon records."""
    save_path: Path = args.save_path
    context = _read_supported_save(save_path)
    trainer = _parse_trainer(context)
    records = _parse_pokemon_records(context, include_boxes=args.include_boxes)
    by_id = {record.local_id: record for record in records}
    requested_ids = tuple(args.pokemon_id)
    missing_ids = [pokemon_id for pokemon_id in requested_ids if pokemon_id not in by_id]
    if missing_ids:
        available = ", ".join(sorted(by_id)) or "none"
        raise LegacyMigrationError(
            f"Pokemon ID(s) not found: {', '.join(missing_ids)}. Available IDs: {available}."
        )

    selected = tuple(by_id[pokemon_id] for pokemon_id in requested_ids)
    metadata = _build_save_metadata(context, trainer)
    package_dir = export_migration_package(
        output_dir=args.output,
        save_metadata=metadata,
        validation_report=context.validation,
        selected_records=selected,
    )

    after_digest = sha256_file(save_path)
    if after_digest != context.digest:
        raise LegacyMigrationError(
            "Critical safety failure: source save hash changed during export. "
            f"Before {context.digest}, after {after_digest}."
        )

    print(f"Package: {package_dir}")
    print(f"Selected Pokemon: {', '.join(requested_ids)}")
    print(f"Source SHA-256 verified unchanged: {context.digest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    try:
        return int(args.func(args))
    except LegacyMigrationError as exc:
        LOGGER.debug("Controlled failure", exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
