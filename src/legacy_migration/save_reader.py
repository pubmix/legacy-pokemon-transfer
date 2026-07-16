"""Save-source abstractions with read-only local-file support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from legacy_migration.errors import SaveReadError
from legacy_migration.hashing import sha256_bytes
from legacy_migration.models import SourceMetadata


class SaveSource(ABC):
    """Interface for any source that can provide raw save bytes."""

    @abstractmethod
    def read_save(self) -> bytes:
        """Return a copy of the raw save bytes."""

    @abstractmethod
    def get_source_metadata(self) -> SourceMetadata:
        """Return metadata about the save source, not the parsed save."""

    @abstractmethod
    def is_read_only(self) -> bool:
        """Return whether this source promises not to mutate cartridge/save data."""


class FileSaveSource(SaveSource):
    """Read a local `.sav` file using binary read-only mode."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def read_save(self) -> bytes:
        """Read the local save into memory without opening it for writes."""
        try:
            with self.path.open("rb") as handle:
                return bytes(handle.read())
        except OSError as exc:
            raise SaveReadError(f"Could not read save file: {self.path}") from exc

    def get_source_metadata(self) -> SourceMetadata:
        """Return file-source metadata without parsing the save."""
        return SourceMetadata(
            source_type="file",
            display_name=self.path.name,
            is_read_only=self.is_read_only(),
            details={"path": str(self.path)},
        )

    def is_read_only(self) -> bool:
        """Local file source opens the file only in read-only mode."""
        return True


class ChromaticSaveSource(SaveSource):
    """Placeholder for a future documented ModRetro Chromatic integration.

    The desktop app expects this class to eventually receive the exact raw save
    bytes from a supported Chromatic firmware/service boundary. No USB, serial,
    debug, or service protocol is assumed here.
    """

    def read_save(self) -> bytes:
        """Chromatic save transfer is intentionally not implemented yet."""
        raise SaveReadError(
            "Chromatic save transfer is not implemented; no documented interface is configured."
        )

    def get_source_metadata(self) -> SourceMetadata:
        """Return placeholder metadata for the future Chromatic source."""
        return SourceMetadata(
            source_type="chromatic",
            display_name="ModRetro Chromatic cartridge save source",
            is_read_only=self.is_read_only(),
            details={"status": "placeholder; interface not documented"},
        )

    def is_read_only(self) -> bool:
        """Future Chromatic integration must remain read-only for this application."""
        return True


def read_source_with_hash(source: SaveSource) -> tuple[bytes, str, SourceMetadata]:
    """Read any save source into memory and return bytes, SHA-256, and metadata."""
    if not source.is_read_only():
        raise SaveReadError("Refusing to read from a mutable save source.")
    data = source.read_save()
    return data, sha256_bytes(data), source.get_source_metadata()


def read_save_bytes(path: Path) -> bytes:
    """Read a local save file as bytes using the file source implementation."""
    return FileSaveSource(path).read_save()


def read_save_with_hash(path: Path) -> tuple[bytes, str]:
    """Read a local save into memory and return its SHA-256 digest."""
    data, digest, _metadata = read_source_with_hash(FileSaveSource(path))
    return data, digest
