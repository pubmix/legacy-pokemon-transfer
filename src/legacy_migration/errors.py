"""Custom exceptions for controlled parser and CLI failures."""


class LegacyMigrationError(Exception):
    """Base class for expected application errors."""


class SaveReadError(LegacyMigrationError):
    """Raised when a save file cannot be read safely."""


class UnsupportedSaveError(LegacyMigrationError):
    """Raised when the save file is not a supported format for this milestone."""


class ParseError(LegacyMigrationError):
    """Raised when required save data cannot be parsed safely."""


class ExportError(LegacyMigrationError):
    """Raised when a migration package cannot be exported safely."""

