from __future__ import annotations

from pathlib import Path

from legacy_migration.hashing import sha256_bytes, sha256_file
from legacy_migration.save_reader import read_save_with_hash


def test_hash_before_and_after_read_is_identical() -> None:
    fixture = Path("tests/fixtures/sample_gen1.sav")

    before = sha256_file(fixture)
    data, digest = read_save_with_hash(fixture)
    after = sha256_file(fixture)

    assert digest == before == after
    assert sha256_bytes(data) == digest

