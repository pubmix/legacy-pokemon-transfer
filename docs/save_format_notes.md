# Save Format Notes

This project currently implements a narrow parser milestone for English/Western
Generation I and Generation II save files. It does not yet claim validated
support for arbitrary real cartridge saves.

## Documentation Sources

Public technical documentation used for this milestone:

- Bulbapedia, "Save data structure (Generation I)":
  https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_I)
- Bulbapedia, "Character encoding (Generation I)":
  https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_I)
- Bulbapedia, "Save data structure (Generation II)":
  https://bulbapedia.bulbagarden.net/wiki/Save_data_structure_(Generation_II)
- Bulbapedia, "Pokemon data structure (Generation II)":
  https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_data_structure_(Generation_II)
- Data Crystal, "Pokemon Red and Blue/RAM map":
  https://datacrystal.tcrf.net/wiki/Pok%C3%A9mon_Red_and_Blue/RAM_map
- Data Crystal, "Pokemon Crystal/RAM map":
  https://datacrystal.tcrf.net/wiki/Pok%C3%A9mon_Crystal/RAM_map

## Generation I Assumptions

Implemented for English/Western Red, Blue, and Yellow-compatible saves:

- standard save files are 32 KiB (`0x8000`)
- SRAM is divided into four 8 KiB banks
- Bank 1 starts at `0x2000` and contains the main saved gameplay data
- player name is stored at save offset `0x2598` with an 11-byte text field
- player ID is stored at save offset `0x2605` as two big-endian bytes
- badge flags are stored at save offset `0x2602`
- current party data starts at save offset `0x2F2C`
- party Pokemon records are 44 bytes
- current PC box data starts at save offset `0x30C0`
- stored PC boxes 1-6 start at `0x4000`, `0x4462`, `0x48C4`, `0x4D26`,
  `0x5188`, and `0x55EA`
- stored PC boxes 7-12 start at `0x6000`, `0x6462`, `0x68C4`, `0x6D26`,
  `0x7188`, and `0x75EA`
- Gen I full box data records are `0x462` bytes per box
- Gen I boxed Pokemon records are 33 bytes
- main-data checksum is stored at `0x3523`
- checksum covers `0x2598..0x3522` inclusive with an inverted 8-bit sum
- English legacy text names are terminated by byte `0x50`

Detection limitation:

The raw save does not provide a simple authoritative label that distinguishes
Pokemon Red, Blue, and Yellow. This milestone therefore reports
`Red/Blue/Yellow-compatible` with probable confidence for correctly sized Gen I
fallback saves.

## Generation II Assumptions

Implemented for English/Western Gold, Silver, and Crystal-compatible saves:

- standard save files are 32 KiB (`0x8000`)
- Generation II saves include checksum-protected data areas
- trainer ID is stored at save offset `0x2008` as two big-endian bytes
- trainer name is stored at save offset `0x200B` with an 11-byte text field
- Gold/Silver current party data starts at save offset `0x288A`
- Crystal current party data starts at save offset `0x2865`
- party data contains count, species list, six party Pokemon records, six
  original-trainer names, and six nicknames
- party Pokemon records are 48 bytes
- PC Pokemon records are 32 bytes in the supported Gen II layouts
- Gold/Silver primary checksum covers `0x2009..0x2D68` and is stored little-endian
  at `0x2D69`
- Crystal primary checksum covers `0x2009..0x2B82` and is stored little-endian at
  `0x2D0D`

The current Gen II detection path first checks file size, then tries the
documented Crystal and Gold/Silver checksum layouts. If one layout matches, that
layout is used for trainer and party parsing. If neither checksum matches, the
file is not treated as a supported Gen II save.

## Current Pokemon Record Fields Parsed

Generation I party records currently parse:

- species index
- current HP
- status
- moves
- trainer ID
- experience
- stat experience
- determinant values
- level
- nickname
- original trainer name
- raw record bytes preserved as hex

Generation I PC box records currently parse:

- species index
- current HP
- box-level byte
- status
- moves
- trainer ID
- experience
- stat experience
- determinant values
- nickname
- original trainer name
- raw 33-byte boxed record bytes preserved as hex

Generation II party records currently parse:

- species index
- held-item-era byte is preserved in the raw record but not displayed yet
- moves
- trainer ID
- experience
- stat experience
- determinant values
- PP bytes are preserved in the raw record but not displayed yet
- friendship, Pokerus, and caught data are preserved in the raw record
- level
- status
- current HP
- nickname
- original trainer name
- raw record bytes preserved as hex

Generation II PC box records currently parse:

- species index
- moves
- trainer ID
- experience
- stat experience
- determinant values
- level
- nickname
- original trainer name
- raw 32-byte boxed record bytes preserved as hex

Boxed records do not store the same calculated battle stats/current HP fields
that party records store, so those fields are left empty in boxed output.

## Known Verification Gap

The included `.sav` fixtures are synthetic. They are useful for regression tests
and safety checks, but they do not prove compatibility with every real save
produced by original cartridges, emulators, or third-party dumpers. Known-good
real saves should be tested before describing any game as production-supported.
