from __future__ import annotations

import json
from pathlib import Path

import pytest

from legacy_migration.cli import main
from legacy_migration.errors import ExportError
from legacy_migration.hashing import sha256_bytes
from legacy_migration.migration_package import ensure_new_output_path


def _package_path_from_output(output: str) -> Path:
    for line in output.splitlines():
        if line.startswith("Package: "):
            return Path(line.removeprefix("Package: "))
    raise AssertionError("Export output did not include a package path.")


def test_export_cli_creates_migration_candidate_package(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    code = main(
        [
            "export",
            "tests/fixtures/sample_crystal.sav",
            "--pokemon-id",
            "party-1",
            "--output",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    package_dir = _package_path_from_output(captured.out)
    assert package_dir.exists()
    assert (package_dir / "manifest.json").exists()
    assert (package_dir / "source" / "save_metadata.json").exists()
    assert (package_dir / "source" / "original_save.sha256").exists()
    assert (package_dir / "selected" / "pokemon.json").exists()
    assert (package_dir / "selected" / "pokemon_raw.bin").exists()
    assert (package_dir / "reports" / "validation_report.json").exists()
    assert (package_dir / "README.txt").exists()

    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    pokemon = json.loads((package_dir / "selected" / "pokemon.json").read_text(encoding="utf-8"))
    raw = (package_dir / "selected" / "pokemon_raw.bin").read_bytes()

    assert manifest["operation_type"] == "read_only"
    assert manifest["selected_pokemon_ids"] == ["party-1"]
    assert manifest["raw_selected_record_hashes"]["party-1"] == sha256_bytes(raw)
    assert pokemon[0]["local_id"] == "party-1"
    assert pokemon[0]["raw_record_sha256"] == sha256_bytes(raw)
    assert "not compatible with Pokemon HOME" in manifest["offline_prototype_notice"]


def test_export_cli_returns_nonzero_for_unknown_pokemon_id(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    code = main(
        [
            "export",
            "tests/fixtures/sample_crystal.sav",
            "--pokemon-id",
            "party-99",
            "--output",
            str(tmp_path),
        ]
    )

    captured = capsys.readouterr()
    assert code == 2
    assert "Pokemon ID(s) not found" in captured.err


def test_existing_export_directory_is_not_silently_overwritten(tmp_path: Path) -> None:
    existing = tmp_path / "migration_existing"
    existing.mkdir()

    with pytest.raises(ExportError):
        ensure_new_output_path(existing)
