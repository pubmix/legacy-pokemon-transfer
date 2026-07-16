from __future__ import annotations

from pathlib import Path

from legacy_migration.gen2.detection import detect_gen2_save


def test_detects_crystal_fixture_from_checksum_layout() -> None:
    data = Path("tests/fixtures/sample_crystal.sav").read_bytes()

    result = detect_gen2_save(data)

    assert result.supported is True
    assert result.confidence == "probable"
    assert result.game == "Crystal-compatible"
    assert result.layout is not None


def test_detects_gold_silver_fixture_from_checksum_layout() -> None:
    data = Path("tests/fixtures/sample_gold_silver.sav").read_bytes()

    result = detect_gen2_save(data)

    assert result.supported is True
    assert result.confidence == "probable"
    assert result.game == "Gold/Silver-compatible"
    assert result.layout is not None
