# FlashGBX Setup For Save Dumping

FlashGBX is a third-party cartridge reader/writer application. In this project,
use it only to make read-only backup copies of save data from cartridges you
own. Do not use restore, erase, or ROM-writing features for this migration POC.

Official project:

- https://github.com/Lesserkuma/FlashGBX
- https://github.com/Lesserkuma/FlashGBX/releases

The FlashGBX README describes support for backing up save data from Game Boy and
Game Boy Advance cartridges, and lists compatible reader/writer hardware such as
GBxCart RW, GBFlash, Joey Jr, and Game Bub.

## Recommended Windows Install

1. Open the official releases page:
   https://github.com/Lesserkuma/FlashGBX/releases
2. Download the latest Windows 64-bit setup package.
3. Run the installer.
4. Allow the device driver install if Windows asks.
5. Launch FlashGBX.

Prefer the setup package over a portable zip for the first install because the
setup package is the most likely path to install the USB drivers needed by the
adapter.

## Safe Save-Dump Workflow

1. Insert your original Game Boy or Game Boy Color cartridge into the adapter.
2. Connect the adapter to USB.
3. Open FlashGBX.
4. Select or connect to your adapter hardware.
5. Confirm the cartridge is detected correctly.
6. Choose the save backup/read option only.
7. Save the dumped file into:

```text
incoming_saves/
```

Suggested filename examples:

```text
incoming_saves/pokemon_crystal_original_2026-07-15.sav
incoming_saves/pokemon_red_original_2026-07-15.sav
```

Avoid overwrite prompts. Keep every dump as a separate dated file until the
project has stronger verification tooling.

## Run This Project Against The Dump

From the project root:

```powershell
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m legacy_migration.cli inspect incoming_saves\pokemon_crystal_original_2026-07-15.sav
```

Then list party Pokemon:

```powershell
& "C:\Users\jerem\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m legacy_migration.cli list-pokemon incoming_saves\pokemon_crystal_original_2026-07-15.sav
```

## Important Boundaries

- Do not download ROMs.
- Do not dump or distribute ROM files for this project.
- Do not use FlashGBX restore, erase, or write functions for this POC.
- Keep the original `.sav` dump unchanged.
- Make a second dump and compare hashes before trusting a cartridge backup.

Recommended double-dump check:

```powershell
Get-FileHash incoming_saves\pokemon_crystal_original_2026-07-15.sav -Algorithm SHA256
Get-FileHash incoming_saves\pokemon_crystal_original_2026-07-15_second_dump.sav -Algorithm SHA256
```

If the hashes match, the dump is more likely to be stable. If they differ, stop
and troubleshoot the adapter, cartridge contacts, or driver setup before using
the save.
