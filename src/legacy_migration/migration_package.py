"""Offline migration-candidate package export."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from legacy_migration import PARSER_VERSION, __version__
from legacy_migration.errors import ExportError
from legacy_migration.hashing import sha256_bytes
from legacy_migration.models import PokemonRecord, SaveMetadata, ValidationReport

PACKAGE_FORMAT_NAME = "legacy-pokemon-migration-candidate"
PACKAGE_FORMAT_VERSION = "0.1"


def ensure_new_output_path(path: Path) -> None:
    """Prevent accidental overwrite of a migration package path."""
    if path.exists():
        raise ExportError(f"Output path already exists and will not be overwritten: {path}")


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _pokemon_payload(record: PokemonRecord) -> dict[str, object]:
    payload = asdict(record)
    payload["raw_record_sha256"] = sha256_bytes(bytes.fromhex(record.raw_record_hex))
    return payload


def export_migration_package(
    *,
    output_dir: Path,
    save_metadata: SaveMetadata,
    validation_report: ValidationReport,
    selected_records: tuple[PokemonRecord, ...],
) -> Path:
    """Create an offline migration-candidate package for selected Pokemon records."""
    if not selected_records:
        raise ExportError("At least one Pokemon record must be selected for export.")

    output_dir.mkdir(parents=True, exist_ok=True)
    package_id = str(uuid4())
    package_dir = output_dir / f"migration_{package_id}"
    ensure_new_output_path(package_dir)

    selected_ids = [record.local_id for record in selected_records]
    raw_hashes = {
        record.local_id: sha256_bytes(bytes.fromhex(record.raw_record_hex))
        for record in selected_records
    }

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "detected_format": save_metadata.detected_game,
        "offline_prototype_notice": (
            "This package is an offline preservation prototype and is not compatible "
            "with Pokemon HOME."
        ),
        "operation_type": "read_only",
        "package_format_name": PACKAGE_FORMAT_NAME,
        "package_format_version": PACKAGE_FORMAT_VERSION,
        "package_id": package_id,
        "parser_version": PARSER_VERSION,
        "raw_selected_record_hashes": raw_hashes,
        "selected_pokemon_ids": selected_ids,
        "source_save_hash": save_metadata.sha256,
        "source_save_size": save_metadata.file_size,
        "tool_version": __version__,
        "validation_result": save_metadata.validation_status,
        "warnings": list(save_metadata.warnings),
    }

    try:
        (package_dir / "source").mkdir(parents=True)
        (package_dir / "selected").mkdir()
        (package_dir / "reports").mkdir()

        _write_json(package_dir / "manifest.json", manifest)
        _write_json(package_dir / "source" / "save_metadata.json", asdict(save_metadata))
        (package_dir / "source" / "original_save.sha256").write_text(
            save_metadata.sha256 + "\n", encoding="utf-8"
        )
        _write_json(
            package_dir / "selected" / "pokemon.json",
            [_pokemon_payload(record) for record in selected_records],
        )
        (package_dir / "selected" / "pokemon_raw.bin").write_bytes(
            b"".join(bytes.fromhex(record.raw_record_hex) for record in selected_records)
        )
        _write_json(package_dir / "reports" / "validation_report.json", asdict(validation_report))
        (package_dir / "README.txt").write_text(
            "\n".join(
                [
                    "Legacy Pokemon Migration Candidate Package",
                    "",
                    "This is an offline preservation prototype package.",
                    "It is not an official Pokemon product.",
                    "It is not compatible with Pokemon HOME.",
                    "It is not intended for direct injection into any modern game.",
                    "",
                    f"Package ID: {package_id}",
                    f"Source save SHA-256: {save_metadata.sha256}",
                    f"Selected Pokemon IDs: {', '.join(selected_ids)}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    except OSError as exc:
        raise ExportError(f"Could not write migration package: {package_dir}") from exc

    return package_dir
