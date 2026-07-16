"""English Generation I text decoding."""

from __future__ import annotations

from legacy_migration.gen1.constants import TEXT_TERMINATOR

ENGLISH_CHAR_TABLE: dict[int, str] = {
    0x7F: " ",
    **{0x80 + index: char for index, char in enumerate("ABCDEFGHIJKLMNOP")},
    **{0x90 + index: char for index, char in enumerate("QRSTUVWXYZ")},
    0x9A: "(",
    0x9B: ")",
    0x9C: ":",
    0x9D: ";",
    0x9E: "[",
    0x9F: "]",
    **{0xA0 + index: char for index, char in enumerate("abcdefghijklmnop")},
    **{0xB0 + index: char for index, char in enumerate("qrstuvwxyz")},
    0xBA: "e",
    0xBB: "'d",
    0xBC: "'l",
    0xBD: "'s",
    0xBE: "'t",
    0xBF: "'v",
    0xE0: "'",
    0xE3: "-",
    0xE6: "?",
    0xE7: "!",
    0xE8: ".",
    0xEF: "♂",
    0xF1: "x",
    0xF2: ".",
    0xF3: "/",
    0xF4: ",",
    0xF5: "♀",
    **{0xF6 + index: char for index, char in enumerate("0123456789")},
}


def decode_gen1_text(raw: bytes, *, stop_at_terminator: bool = True) -> tuple[str, tuple[str, ...]]:
    """Decode English Generation I bytes, escaping unknown values visibly."""
    decoded: list[str] = []
    warnings: list[str] = []

    for index, value in enumerate(raw):
        if stop_at_terminator and value == TEXT_TERMINATOR:
            return "".join(decoded), tuple(warnings)
        if value in ENGLISH_CHAR_TABLE:
            decoded.append(ENGLISH_CHAR_TABLE[value])
            continue
        escaped = f"\\x{value:02X}"
        decoded.append(escaped)
        warnings.append(f"Undecodable byte {escaped} at text offset +{index}.")

    if stop_at_terminator:
        warnings.append("Missing Generation I text terminator 0x50.")

    return "".join(decoded), tuple(warnings)


def encode_fixture_text(text: str, length: int) -> bytes:
    """Encode a small ASCII fixture name with a terminator for synthetic tests."""
    reverse = {value: key for key, value in ENGLISH_CHAR_TABLE.items() if len(value) == 1}
    encoded = bytearray()
    for char in text:
        if char not in reverse:
            raise ValueError(f"Unsupported fixture character: {char!r}")
        encoded.append(reverse[char])
    if len(encoded) >= length:
        raise ValueError("Fixture text is too long for terminated field.")
    encoded.append(TEXT_TERMINATOR)
    encoded.extend([TEXT_TERMINATOR] * (length - len(encoded)))
    return bytes(encoded)

