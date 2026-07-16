from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture

from legacy_migration.cli import main
from legacy_migration.gen1.constants import (
    CURRENT_BOX_DATA_OFFSET,
    MAIN_CHECKSUM_END_INCLUSIVE,
    MAIN_CHECKSUM_OFFSET,
    MAIN_CHECKSUM_START,
)
from legacy_migration.gen1.constants import (
    STORED_BOX_OFFSETS as GEN1_STORED_BOX_OFFSETS,
)
from legacy_migration.gen1.text_codec import encode_fixture_text
from legacy_migration.gen2.constants import CRYSTAL_LAYOUT, STORED_BOX_OFFSETS


def _put_u16_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 8) & 0xFF
    data[offset + 1] = value & 0xFF


def _put_u24_be(data: bytearray, offset: int, value: int) -> None:
    data[offset] = (value >> 16) & 0xFF
    data[offset + 1] = (value >> 8) & 0xFF
    data[offset + 2] = value & 0xFF


def _refresh_gen1_main_checksum(data: bytearray) -> None:
    checksum = 0xFF
    for value in data[MAIN_CHECKSUM_START : MAIN_CHECKSUM_END_INCLUSIVE + 1]:
        checksum = (checksum - value) & 0xFF
    data[MAIN_CHECKSUM_OFFSET] = checksum


def _write_crystal_fixture_with_boxed_sentret(path: Path) -> None:
    data = bytearray(Path("tests/fixtures/sample_crystal.sav").read_bytes())
    for empty_box_offset in (CRYSTAL_LAYOUT.current_box_offset, *STORED_BOX_OFFSETS):
        data[empty_box_offset] = 0
        data[empty_box_offset + 1] = 0xFF

    box_offset = 0x4000
    data[box_offset] = 1
    data[box_offset + 1] = 161
    data[box_offset + 2] = 0xFF
    record_offset = box_offset + 0x16
    data[record_offset] = 161
    data[record_offset + 1] = 0
    data[record_offset + 2] = 33
    data[record_offset + 3] = 45
    _put_u16_be(data, record_offset + 0x06, 12345)
    _put_u24_be(data, record_offset + 0x08, 64)
    data[record_offset + 0x15] = 0xAA
    data[record_offset + 0x16] = 0xAA
    data[record_offset + 0x17] = 35
    data[record_offset + 0x18] = 30
    data[record_offset + 0x1B] = 70
    data[record_offset + 0x1D] = 0x85
    data[record_offset + 0x1E] = 0x81
    data[record_offset + 0x1F] = 2
    ot_offset = box_offset + 0x16 + (20 * 0x20)
    nickname_offset = ot_offset + (20 * 0x0B)
    data[ot_offset : ot_offset + 0x0B] = encode_fixture_text("KRIS", 0x0B)
    data[nickname_offset : nickname_offset + 0x0B] = encode_fixture_text("SENTRET", 0x0B)
    path.write_bytes(data)


def _write_gen1_fixture_with_boxed_charmander(path: Path) -> None:
    data = bytearray(Path("tests/fixtures/sample_gen1.sav").read_bytes())
    data[CURRENT_BOX_DATA_OFFSET] = 0
    data[CURRENT_BOX_DATA_OFFSET + 1] = 0xFF
    for empty_box_offset in GEN1_STORED_BOX_OFFSETS:
        data[empty_box_offset] = 0
        data[empty_box_offset + 1] = 0xFF

    box_offset = GEN1_STORED_BOX_OFFSETS[0]
    data[box_offset] = 1
    data[box_offset + 1] = 0xB0
    data[box_offset + 2] = 0xFF
    record_offset = box_offset + 0x16
    data[record_offset] = 0xB0
    _put_u16_be(data, record_offset + 0x01, 19)
    data[record_offset + 0x03] = 5
    data[record_offset + 0x08] = 10
    data[record_offset + 0x09] = 45
    _put_u16_be(data, record_offset + 0x0C, 12345)
    _put_u24_be(data, record_offset + 0x0E, 125)
    data[record_offset + 0x1B] = 0xAA
    data[record_offset + 0x1C] = 0xAA
    data[record_offset + 0x1D] = 35
    data[record_offset + 0x1E] = 25
    ot_offset = box_offset + 0x2AA
    nickname_offset = box_offset + 0x386
    data[ot_offset : ot_offset + 0x0B] = encode_fixture_text("TEST", 0x0B)
    data[nickname_offset : nickname_offset + 0x0B] = encode_fixture_text("CHAR", 0x0B)
    _refresh_gen1_main_checksum(data)
    path.write_bytes(data)


def test_inspect_cli_prints_fixture(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["inspect", "tests/fixtures/sample_gen1.sav"])

    output = capsys.readouterr().out
    assert code == 0
    assert "File: sample_gen1.sav" in output
    assert "Source: file" in output
    assert "Source read-only: True" in output
    assert "Size: 32768 bytes" in output
    assert "Game: Red/Blue/Yellow-compatible" in output
    assert "Trainer: TEST" in output
    assert "Trainer ID: 12345" in output
    assert "Validation: PASS" in output


def test_inspect_cli_prints_crystal_fixture(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["inspect", "tests/fixtures/sample_crystal.sav"])

    output = capsys.readouterr().out
    assert code == 0
    assert "File: sample_crystal.sav" in output
    assert "Format: Generation II Pokemon save" in output
    assert "Game: Crystal-compatible" in output
    assert "Trainer: KRIS" in output
    assert "Trainer ID: 12345" in output
    assert "Validation: PASS" in output


def test_inspect_cli_accepts_crystal_fixture_with_rtc_tail(
    capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    source = Path("tests/fixtures/sample_crystal.sav").read_bytes()
    save_path = tmp_path / "sample_crystal_with_rtc_tail.sav"
    save_path.write_bytes(source + bytes(range(48)))

    code = main(["inspect", str(save_path)])

    output = capsys.readouterr().out
    assert code == 0
    assert "Size: 32816 bytes" in output
    assert "Parsed save bytes: 32768 bytes" in output
    assert "48 trailing bytes" in output
    assert "Game: Crystal-compatible" in output
    assert "Trainer: KRIS" in output


def test_inspect_cli_prints_gold_silver_fixture(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["inspect", "tests/fixtures/sample_gold_silver.sav"])

    output = capsys.readouterr().out
    assert code == 0
    assert "File: sample_gold_silver.sav" in output
    assert "Format: Generation II Pokemon save" in output
    assert "Game: Gold/Silver-compatible" in output
    assert "Trainer: GOLD" in output
    assert "Trainer ID: 12345" in output
    assert "Validation: PASS" in output


def test_cli_returns_nonzero_on_critical_failure(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["inspect", "tests/fixtures/truncated.sav"])

    captured = capsys.readouterr()
    assert code == 2
    assert "Error:" in captured.err


def test_list_pokemon_cli_prints_party_fixture(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["list-pokemon", "tests/fixtures/sample_gen1.sav"])

    output = capsys.readouterr().out
    assert code == 0
    assert "party-1" in output
    assert "Party 1" in output
    assert "SPARKY" in output
    assert "Pikachu" in output
    assert "TEST" in output
    assert "12345" in output


def test_list_pokemon_cli_prints_crystal_fixture(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["list-pokemon", "tests/fixtures/sample_crystal.sav"])

    output = capsys.readouterr().out
    assert code == 0
    assert "party-1" in output
    assert "Party 1" in output
    assert "LEAFY" in output
    assert "Chikorita" in output
    assert "KRIS" in output
    assert "12345" in output


def test_list_pokemon_cli_prints_gold_silver_fixture(capsys) -> None:  # type: ignore[no-untyped-def]
    code = main(["list-pokemon", "tests/fixtures/sample_gold_silver.sav"])

    output = capsys.readouterr().out
    assert code == 0
    assert "party-1" in output
    assert "Party 1" in output
    assert "BLAZE" in output
    assert "Cyndaquil" in output
    assert "GOLD" in output
    assert "12345" in output


def test_list_pokemon_cli_includes_box_records(
    capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    save_path = tmp_path / "boxed.sav"
    _write_crystal_fixture_with_boxed_sentret(save_path)

    code = main(["list-pokemon", str(save_path), "--include-boxes"])

    output = capsys.readouterr().out
    assert code == 0
    assert "party-1" in output
    assert "box-1-1" in output
    assert "Box 1 Slot 1" in output
    assert "SENTRET" in output
    assert "Sentret" in output


def test_list_pokemon_cli_includes_gen1_box_records(
    capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    save_path = tmp_path / "boxed_gen1.sav"
    _write_gen1_fixture_with_boxed_charmander(save_path)

    code = main(["list-pokemon", str(save_path), "--include-boxes"])

    output = capsys.readouterr().out
    assert code == 0
    assert "party-1" in output
    assert "box-1-1" in output
    assert "Box 1 Slot 1" in output
    assert "CHAR" in output
    assert "Charmander" in output


def test_export_cli_can_select_box_records(
    capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    save_path = tmp_path / "boxed.sav"
    output_dir = tmp_path / "packages"
    _write_crystal_fixture_with_boxed_sentret(save_path)

    code = main(
        [
            "export",
            str(save_path),
            "--pokemon-id",
            "box-1-1",
            "--include-boxes",
            "--output",
            str(output_dir),
        ]
    )

    output = capsys.readouterr().out
    assert code == 0
    assert "Selected Pokemon: box-1-1" in output


def test_export_cli_can_select_gen1_box_records(
    capsys: CaptureFixture[str], tmp_path: Path
) -> None:
    save_path = tmp_path / "boxed_gen1.sav"
    output_dir = tmp_path / "packages"
    _write_gen1_fixture_with_boxed_charmander(save_path)

    code = main(
        [
            "export",
            str(save_path),
            "--pokemon-id",
            "box-1-1",
            "--include-boxes",
            "--output",
            str(output_dir),
        ]
    )

    output = capsys.readouterr().out
    assert code == 0
    assert "Selected Pokemon: box-1-1" in output
