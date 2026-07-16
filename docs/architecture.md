# Architecture

The prototype separates file safety, parsing, validation, and presentation.

- `save_reader.py` defines the `SaveSource` abstraction and opens local source
  saves in binary read-only mode through `FileSaveSource`.
- `hashing.py` calculates source hashes without modifying source files.
- `gen1/` contains Generation I layout constants, detection, validation, text
  decoding, trainer parsing, and party Pokemon parsing.
- `gen2/` contains Generation II layout constants for Gold/Silver and Crystal,
  checksum detection, validation, trainer parsing, and party Pokemon parsing.
- `cli.py` presents parsed data without owning parser logic.
- `migration_package.py` is a placeholder boundary for later export work.

The parser returns structured models instead of untyped dictionaries so future
UI and export code can reuse the same data safely.

## Save Source Boundary

All parser, validation, UI, and export logic should consume raw bytes supplied
through this interface:

- `read_save() -> bytes`
- `get_source_metadata() -> SourceMetadata`
- `is_read_only() -> bool`

The current implementation is `FileSaveSource`, which reads a local `.sav` file
in binary read-only mode.

The intended future hardware platform is the ModRetro Chromatic. A future
`ChromaticSaveSource` may provide the same raw bytes after Chromatic firmware or
a supported desktop service exposes a documented way to read cartridge SRAM. No
communication protocol is assumed in this project: not USB, serial, debug, or
service APIs. The expected boundary is that Chromatic-side software performs the
hardware-specific cartridge access and hands the desktop application an immutable
byte sequence plus source metadata. From that point forward, the existing parser,
validation, UI, and export logic should remain unchanged.
