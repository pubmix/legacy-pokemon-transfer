from __future__ import annotations

from pathlib import Path

from legacy_migration.gen1.detection import detect_save


def test_detects_32768_byte_save_as_probable_gen1() -> None:
    data = Path("tests/fixtures/sample_gen1.sav").read_bytes()

    result = detect_save(data)

    assert result.supported is True
    assert result.confidence == "probable"
    assert result.game == "Red/Blue/Yellow-compatible"


def test_rejects_unsupported_file_size() -> None:
    result = detect_save(b"short")

    assert result.supported is False
    assert result.confidence == "unsupported"
