"""Conservative detection for English/Western Generation II saves."""

from __future__ import annotations

from dataclasses import dataclass

from legacy_migration.gen2.constants import (
    CRYSTAL_LAYOUT,
    GEN2_SAVE_SIZE,
    GOLD_SILVER_LAYOUT,
    Gen2Layout,
)
from legacy_migration.gen2.validation import primary_checksum_matches


@dataclass(frozen=True)
class Gen2DetectionResult:
    """Generation II detection result with explicit confidence."""

    supported: bool
    confidence: str
    format_name: str
    game: str
    region: str
    layout: Gen2Layout | None = None
    warnings: tuple[str, ...] = ()


def _unsupported(message: str) -> Gen2DetectionResult:
    return Gen2DetectionResult(
        supported=False,
        confidence="unsupported",
        format_name="Not detected as supported Generation II",
        game="unknown",
        region="unknown",
        warnings=(message,),
    )


def detect_gen2_save(data: bytes) -> Gen2DetectionResult:
    """Detect supported English/Western Gen II saves using size and checksum layout."""
    if len(data) != GEN2_SAVE_SIZE:
        return Gen2DetectionResult(
            supported=False,
            confidence="unsupported",
            format_name="Unsupported save size",
            game="unknown",
            region="unknown",
            warnings=(f"Expected 32768 bytes, got {len(data)} bytes.",),
        )

    matching_layouts = [
        layout
        for layout in (CRYSTAL_LAYOUT, GOLD_SILVER_LAYOUT)
        if primary_checksum_matches(data, layout)
    ]
    if not matching_layouts:
        return _unsupported("No supported Generation II primary checksum matched.")

    layout = matching_layouts[0]
    confidence = "probable" if len(matching_layouts) == 1 else "ambiguous"
    warnings = [
        f"{layout.game} support is newly implemented and should be verified "
        "against a known-good save.",
        "Language/region is inferred from the supported English/Western layout.",
    ]
    if len(matching_layouts) > 1:
        warnings.append(
            "Multiple Generation II checksum layouts matched; selected the first documented layout."
        )

    return Gen2DetectionResult(
        supported=True,
        confidence=confidence,
        format_name="Generation II Pokemon save",
        game=layout.game,
        region=layout.region,
        layout=layout,
        warnings=tuple(warnings),
    )
