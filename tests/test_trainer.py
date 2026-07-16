from __future__ import annotations

from pathlib import Path

from legacy_migration.gen1.trainer import parse_trainer
from legacy_migration.gen1.validation import validate_gen1_save


def test_parse_trainer_name_and_id_from_fixture() -> None:
    data = Path("tests/fixtures/sample_gen1.sav").read_bytes()

    trainer = parse_trainer(data)

    assert trainer.name == "TEST"
    assert trainer.trainer_id == 12345
    assert trainer.warnings == ()


def test_truncated_save_produces_validation_failure() -> None:
    report = validate_gen1_save(b"short")

    assert report.overall_status == "FAIL"
    assert report.errors


def test_low_content_pattern_save_produces_validation_failure() -> None:
    data = bytes([0x00, 0xFF]) * 0x4000

    report = validate_gen1_save(data)

    assert report.overall_status == "FAIL"
    assert any("failed cartridge save dump" in error for error in report.errors)
