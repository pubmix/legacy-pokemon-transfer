from __future__ import annotations

from pathlib import Path

from legacy_migration.gen2.constants import CRYSTAL_LAYOUT, GOLD_SILVER_LAYOUT
from legacy_migration.gen2.trainer import parse_gen2_trainer


def test_parses_crystal_trainer_fixture() -> None:
    data = Path("tests/fixtures/sample_crystal.sav").read_bytes()

    trainer = parse_gen2_trainer(data, CRYSTAL_LAYOUT)

    assert trainer.name == "KRIS"
    assert trainer.trainer_id == 12345


def test_parses_gold_silver_trainer_fixture() -> None:
    data = Path("tests/fixtures/sample_gold_silver.sav").read_bytes()

    trainer = parse_gen2_trainer(data, GOLD_SILVER_LAYOUT)

    assert trainer.name == "GOLD"
    assert trainer.trainer_id == 12345
