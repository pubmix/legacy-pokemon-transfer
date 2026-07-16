# Chromatic MRUpdater Notes

MRUpdater appears relevant to future Chromatic integration, but it should be
treated carefully because it includes write-capable cartridge tooling.

## Local Findings

Observed local executable:

- `C:\Users\jerem\Downloads\MRUpdater.exe`
- signed by `MODRETRO, INC.`
- PyInstaller-based application

Embedded components observed by passive string inspection:

- `flashing_tool.chromaticv2`
- `flashing_tool.openfpga_loader`
- `esptool`
- `serial`
- `usb.backend.libusb1`
- `libhidapi`
- `libusb`
- `openFPGALoader.exe`
- `GowinUSBCableDriverV5_for_win7+.exe`
- `cartclinic.cartridge_read`
- `cartclinic.cartridge_write`
- `cartclinic.save_to_rom`
- `libpyretro.cartclinic.cart_api`
- `libpyretro.cartclinic.comms.session`
- `libpyretro.cartclinic.protocol.cmd`
- generated UI screens including `cc_save_screen`

Cached firmware files observed:

- `C:\Users\jerem\AppData\Local\Temp\firmware\chromatic\current\v4.2.zip`
  - `v4.2/mcu/v0.13.4.bin`
  - `v4.2/fpga/v18.8_20251224.fs`
- `C:\Users\jerem\AppData\Local\Temp\firmware\chromatic\cartclinic\v1.1.zip`
  - `cart_clinic_250412.fs`

MRUpdater logs show:

- Chromatic device detection using VID/PID `0x33aa:0120`
- firmware detection, including firmware `v4.2`
- downloading and loading Cart Clinic firmware
- Cart Clinic flows that write homebrew ROMs to cartridges
- write-capable operations such as flash-type detection, sector erase, and bank
  writing

## Interpretation

MRUpdater is useful context because it strongly suggests ModRetro has a
Chromatic-side "Cart Clinic" mode with a desktop communication path. Embedded
module names indicate read-related code exists (`cartclinic.cartridge_read`) and
the UI appears to include a save screen (`cc_save_screen`).

However, the local logs inspected so far do not confirm a completed read-only
save export flow for original Game Boy or Game Boy Color cartridge SRAM. They do
confirm write-capable cartridge flows, so this project must not blindly invoke
MRUpdater internals.

## Safe Integration Boundary

The migration prototype should continue to accept only immutable raw save bytes
through `SaveSource`.

A future MRUpdater/Chromatic integration should be allowed only if it can be
made explicitly read-only:

```text
MRUpdater / Cart Clinic / supported Chromatic interface
-> read cartridge save bytes only
-> write bytes to a user-chosen .sav file or return bytes to ChromaticSaveSource
-> legacy_migration parser
```

Do not use:

- cartridge write flows
- sector erase flows
- homebrew ROM writing
- firmware flashing as part of ordinary save parsing
- undocumented/private protocol calls without permission

## Next Research Tasks

- Open MRUpdater manually and inspect whether Cart Clinic exposes a save backup
  or cartridge read/export feature.
- If it can export a `.sav`, use that exported file with this project through
  `FileSaveSource`.
- If ModRetro documents a read-only API or CLI, implement a separate
  `ChromaticSaveSource` adapter around that documented interface.
- Keep MRUpdater write-capable behavior out of the migration parser and tests.

