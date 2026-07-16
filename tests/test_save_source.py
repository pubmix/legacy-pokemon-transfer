from __future__ import annotations

from pathlib import Path

import pytest

from legacy_migration.errors import SaveReadError
from legacy_migration.hashing import sha256_bytes
from legacy_migration.models import SourceMetadata
from legacy_migration.save_reader import (
    ChromaticSaveSource,
    FileSaveSource,
    SaveSource,
    read_source_with_hash,
)


def test_file_save_source_reads_read_only_bytes() -> None:
    source = FileSaveSource(Path("tests/fixtures/sample_gen1.sav"))

    data, digest, metadata = read_source_with_hash(source)

    assert len(data) == 32768
    assert digest == sha256_bytes(data)
    assert metadata.source_type == "file"
    assert metadata.display_name == "sample_gen1.sav"
    assert metadata.is_read_only is True


def test_mutable_source_is_rejected_before_reading() -> None:
    class MutableSource(SaveSource):
        def read_save(self) -> bytes:
            raise AssertionError("Mutable source should not be read.")

        def get_source_metadata(self) -> SourceMetadata:
            return SourceMetadata("test", "mutable", False)

        def is_read_only(self) -> bool:
            return False

    with pytest.raises(SaveReadError, match="mutable save source"):
        read_source_with_hash(MutableSource())


def test_chromatic_source_is_placeholder() -> None:
    source = ChromaticSaveSource()

    metadata = source.get_source_metadata()

    assert source.is_read_only() is True
    assert metadata.source_type == "chromatic"
    with pytest.raises(SaveReadError, match="not implemented"):
        source.read_save()
