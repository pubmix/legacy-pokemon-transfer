from __future__ import annotations

from legacy_migration.gen1.constants import TEXT_TERMINATOR
from legacy_migration.gen1.text_codec import decode_gen1_text, encode_fixture_text


def test_decode_known_name_stops_at_terminator() -> None:
    raw = bytes([0x93, 0x84, 0x92, 0x93, TEXT_TERMINATOR, 0x80])

    decoded, warnings = decode_gen1_text(raw)

    assert decoded == "TEST"
    assert warnings == ()


def test_unknown_character_is_escaped() -> None:
    decoded, warnings = decode_gen1_text(bytes([0xC0, TEXT_TERMINATOR]))

    assert decoded == "\\xC0"
    assert warnings == ("Undecodable byte \\xC0 at text offset +0.",)


def test_missing_terminator_warns() -> None:
    decoded, warnings = decode_gen1_text(bytes([0x93, 0x84]))

    assert decoded == "TE"
    assert warnings == ("Missing Generation I text terminator 0x50.",)


def test_fixture_encoder_pads_with_terminators() -> None:
    raw = encode_fixture_text("TEST", 6)

    assert raw == bytes([0x93, 0x84, 0x92, 0x93, 0x50, 0x50])
