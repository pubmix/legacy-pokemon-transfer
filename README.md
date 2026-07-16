# Legacy Pokemon Migration POC

This repository is a software-only proof of concept for safely reading legacy
Pokemon save files and producing traceable offline migration-candidate data.

The long-term product idea is a preservation-oriented workflow:

```text
Original Pokemon cartridge
-> Chromatic or another documented save source
-> read-only save extraction
-> save-file verification
-> Pokemon selection
-> offline migration-candidate package
-> possible future official review/conversion path
```

This project implements only the early software layer. It does not connect to
Pokemon HOME, Nintendo, The Pokemon Company, or any private service. It does not
generate files for injection into modern games. It does not modify cartridges or
source `.sav` files.

## How To Explain The Prototype

The short version:

> This prototype proves that, given raw bytes from a legacy Pokemon save file,
> we can read those bytes safely, identify the save shape, validate important
> structure, parse known fields, and report what was found without altering the
> original save.

The important nuance:

> It is not a migration tool yet. It is a read-only parser and verification
> foundation that could later support an official, approved migration process if
> such a process existed.

The hardware story:

> The intended future hardware platform is the ModRetro Chromatic. This
> milestone does not require a live Chromatic connection. Instead, the software
> uses a replaceable save-source interface so a future Chromatic integration
> could provide the same raw save bytes that a local `.sav` file provides today.

## What Works Today

The current milestone supports read-only `inspect`, `list-pokemon`, and
`export` workflows for synthetic or known-safe English/Western Generation I and
Generation II `.sav` files:

- opens a local source save in binary read-only mode
- uses a replaceable `SaveSource` interface, currently implemented by
  `FileSaveSource`
- copies save bytes into memory before parsing
- validates the expected 32 KiB save size
- calculates SHA-256 for traceability
- detects supported Gen I or Gen II save shapes with honest confidence
- decodes English legacy text fields
- parses trainer name and trainer ID
- validates documented checksums where implemented
- validates current party count and species-list terminators
- parses current party Pokemon records
- optionally parses supported Gen I and Gen II current/stored PC box records
- displays full Gen I and Gen II species names from Bulbasaur through Celebi
- decodes nicknames and original trainer names
- prints stable local IDs such as `party-1`
- exports selected party or boxed Pokemon into offline migration-candidate packages
- re-hashes the source save after export and aborts if the source changed

Current game coverage is intentionally conservative:

- Generation I: English/Western Red, Blue, and Yellow-compatible 32 KiB saves
- Generation II: English/Western Gold/Silver-compatible 32 KiB saves
- Generation II: English/Western Crystal-compatible 32 KiB saves

Real cartridge-save support should not be claimed until the parser has been
tested against valid known-good saves for each game. The included fixtures are
synthetic and are not complete representative gameplay saves.

## Current CLI Examples

## Desktop UI

There is also a simple local desktop UI:

```powershell
outputs\run_legacy_migration_ui.cmd
```

The UI lets you choose a `.sav`, inspect it, list party and supported box
Pokemon, select records, and export a migration-candidate package.

You can also launch it through Python:

```powershell
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m legacy_migration.ui
```

Inspect a save:

```powershell
legacy-migration inspect tests/fixtures/sample_gen1.sav
legacy-migration inspect tests/fixtures/sample_gold_silver.sav
legacy-migration inspect tests/fixtures/sample_crystal.sav
```

List currently supported party and boxed Pokemon:

```powershell
legacy-migration list-pokemon tests/fixtures/sample_gen1.sav
legacy-migration list-pokemon tests/fixtures/sample_gen1.sav --include-boxes
legacy-migration list-pokemon tests/fixtures/sample_gold_silver.sav
legacy-migration list-pokemon tests/fixtures/sample_crystal.sav
legacy-migration list-pokemon tests/fixtures/sample_crystal.sav --include-boxes
```

Export a selected party or boxed Pokemon:

```powershell
legacy-migration export tests/fixtures/sample_crystal.sav --pokemon-id party-1 --output outputs
legacy-migration export tests/fixtures/sample_crystal.sav --pokemon-id party-1 --include-boxes --output outputs
```

If `legacy-migration` is not on PATH, use module form:

```powershell
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m legacy_migration.cli inspect tests/fixtures/sample_crystal.sav
```

Example inspect output:

```text
File: sample_gen1.sav
Source: file
Source read-only: True
Size: 32768 bytes
SHA-256: ...
Format: Generation I Pokemon save
Game: Red/Blue/Yellow-compatible
Detection confidence: probable
Trainer: TEST
Trainer ID: 12345
Validation: PASS
Warnings: 2
- Red, Blue, and Yellow cannot be reliably distinguished from save data alone.
- Language/region is inferred from the supported layout, not confirmed by a save label.
```

Example party listing:

```text
ID       Location  Nickname  Species  Level  OT    Trainer ID  Warnings
-------  --------  --------  -------  -----  ----  ----------  --------
party-1  Party 1   SPARKY    Pikachu  5      TEST  12345       0
```

## Architecture

The code is split so future save sources, UI layers, and export formats can be
added without rewriting the parser.

```text
src/legacy_migration/
|-- cli.py                  CLI commands and output formatting
|-- errors.py               Controlled exception types
|-- hashing.py              SHA-256 helpers
|-- models.py               Typed dataclasses shared across the app
|-- save_reader.py          SaveSource, FileSaveSource, Chromatic placeholder
|-- migration_package.py    Offline migration-candidate package export
|-- gen1/
|   |-- constants.py        Named Gen I offsets and record sizes
|   |-- detection.py        Conservative Gen I detection
|   |-- validation.py       Bounds and checksum validation
|   |-- text_codec.py       English legacy text decoding
|   |-- trainer.py          Trainer field parsing
|   |-- pokemon.py          Party Pokemon record parsing
|   |-- species.py          Gen I internal species-name table
|   `-- boxes.py            Current/stored PC box parsing
`-- gen2/
    |-- constants.py        Named Gen II layouts and record sizes
    |-- detection.py        Conservative Gen II checksum detection
    |-- validation.py       Bounds and checksum validation
    |-- species.py          Gen II species-name table
    |-- trainer.py          Trainer field parsing
    `-- pokemon.py          Party and PC box Pokemon record parsing
```

The main flow for `inspect` is:

```text
FileSaveSource
-> read_source_with_hash()
-> detect_gen2_save(), then Gen I fallback detection
-> selected generation validation
-> selected generation trainer parser
-> CLI report
```

The main flow for `list-pokemon` is:

```text
FileSaveSource
-> read_source_with_hash()
-> detect_gen2_save(), then Gen I fallback detection
-> selected generation validation
-> selected generation party parser, plus supported box parser when requested
-> CLI table
```

The main flow for `export` is:

```text
FileSaveSource
-> read_source_with_hash()
-> detect and validate save
-> parse party Pokemon, plus supported box Pokemon when requested
-> select requested local IDs
-> write migration package
-> re-hash original source file
-> report package path
```

## Save Source Boundary

The parser does not need to know whether bytes came from a local file, hardware,
or a future service. It only needs an object implementing:

```python
class SaveSource:
    def read_save(self) -> bytes: ...
    def get_source_metadata(self) -> SourceMetadata: ...
    def is_read_only(self) -> bool: ...
```

Implemented now:

- `FileSaveSource`: reads a local `.sav` file in binary read-only mode.

Reserved for later:

- `ChromaticSaveSource`: placeholder for a future documented ModRetro Chromatic
  integration.

The expected future boundary is that Chromatic-side firmware or an official
supported service performs hardware-specific cartridge access and hands this
desktop application immutable raw save bytes plus source metadata. This project
does not assume Chromatic currently exposes cartridge SRAM over USB, serial,
debug, or any service protocol.

## Data Safety Principles

The source save is treated as an irreplaceable artifact:

- source files are opened read-only
- source bytes are copied into memory before parsing
- hashes are calculated from the raw bytes
- parsing uses named offsets and explicit bounds checks
- uncertain detection facts are reported as warnings
- mutable save sources are rejected before reading
- no source `.sav` file is modified

Export re-hashes the source after package creation and aborts if the source hash
changes.

## Save Format Facts Used So Far

The current milestone uses public documentation for English/Western Generation I
and Generation II saves:

- standard Gen I and Gen II save size is 32 KiB (`0x8000`) for the supported
  English/Western layouts
- Gen I SRAM is divided into four 8 KiB banks
- Gen I player name is at save offset `0x2598`, length 11 bytes
- Gen I trainer ID is at save offset `0x2605`, length 2 bytes, big-endian
- Gen I badge flags are at save offset `0x2602`
- Gen I main-data checksum is stored at `0x3523`
- Gen I checksum covers `0x2598..0x3522` inclusive
- Gen I current box data starts at `0x30C0`
- Gen I stored PC boxes are in banks 2 and 3, each `0x462` bytes
- English legacy text strings terminate with `0x50`
- Gen II trainer ID is at save offset `0x2008`, length 2 bytes, big-endian
- Gen II trainer name is at save offset `0x200B`, length 11 bytes
- Gen II Crystal party data starts at `0x2865`
- Gen II Gold/Silver party data starts at `0x288A`
- Gen II party Pokemon records are 48 bytes
- Gen II primary checksum ranges differ between Gold/Silver and Crystal

More detail and source links live in `docs/save_format_notes.md`.

## Install For Development

Using the bundled Codex Python runtime:

```powershell
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pip install -e ".[dev]"
```

If Python 3.12 is on PATH:

```powershell
python -m pip install -e ".[dev]"
```

## Run Tests And Checks

```powershell
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m pytest -p no:cacheprovider
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m ruff check .
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m mypy src tests
```

## Test Fixtures

The sample `.sav` files in `tests/fixtures/` are synthetic 32 KiB binary
fixtures created for this prototype. They contain enough documented fields for
the current milestone:

- `sample_gen1.sav`: trainer `TEST`, one party Pikachu named `SPARKY`
- `sample_gold_silver.sav`: trainer `GOLD`, one party Cyndaquil named `BLAZE`
- `sample_crystal.sav`: trainer `KRIS`, one party Chikorita named `LEAFY`
- all supported fixtures use trainer ID `12345`
- supported fixtures include valid checksums for the synthetic bytes

`tests/fixtures/truncated.sav` is a deliberately invalid 5-byte fixture used to
verify controlled failure behavior.

No ROMs or copyrighted game data are included.

## What Remains Unimplemented

- full species and move interpretation
- Pokedex counts
- play time parsing
- real Chromatic integration
- validation against known-good real saves for Red, Blue, Yellow, Gold, Silver,
  and Crystal

## Legal And Safety Boundaries

Do not include ROMs in this repository. Do not download copyrighted ROM data.
Do not modify source `.sav` files. Do not write cartridge data, delete cartridge
data, bypass legality systems, connect to Pokemon HOME, or present this project
as an official Pokemon product.
