# Known Limitations

- Real Pokemon Red, Blue, Yellow, Gold, Silver, and Crystal save support has not
  yet been validated against known-good saves for each game.
- The parser currently handles file size, checksum validation, English legacy
  text decoding, trainer name, trainer ID, badge bytes, current party Pokemon
  records, and supported PC box Pokemon records.
- Pokedex counts and play time remain future work.
- Generation I and II PC box parsing is implemented for supported layouts, but
  should still be tested against saves with many boxed Pokemon.
- Detection cannot distinguish Red, Blue, and Yellow based on the save bytes
  alone.
- The synthetic fixtures are not copyrighted game data and are not complete
  representative gameplay saves.
- `ChromaticSaveSource` is only a placeholder. The project does not assume
  Chromatic currently exposes cartridge SRAM over USB or any other interface.
