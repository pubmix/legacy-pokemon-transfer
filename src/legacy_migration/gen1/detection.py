"""Honest, conservative detection for Generation I save files."""

from __future__ import annotations

from dataclasses import dataclass

from legacy_migration.gen1.constants import GEN1_SAVE_SIZE


@dataclass(frozen=True)
class DetectionResult:
    """Detection result with explicit confidence."""

    supported: bool
    confidence: str
    format_name: str
    game: str
    region: str
    warnings: tuple[str, ...] = ()


def detect_save(data: bytes) -> DetectionResult:
    """Detect whether bytes look like a supported first-milestone save."""
    if len(data) != GEN1_SAVE_SIZE:
        return DetectionResult(
            supported=False,
            confidence="unsupported",
            format_name="Unsupported save size",
            game="unknown",
            region="unknown",
            warnings=(f"Expected 32768 bytes, got {len(data)} bytes.",),
        )

    return DetectionResult(
        supported=True,
        confidence="probable",
        format_name="Generation I Pokemon save",
        game="Red/Blue/Yellow-compatible",
        region="English/North American layout assumed",
        warnings=(
            "Red, Blue, and Yellow cannot be reliably distinguished from save data alone.",
            "Language/region is inferred from the supported layout, not confirmed by a save label.",
        ),
    )
