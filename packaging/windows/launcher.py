"""Windows executable entry point for PyInstaller builds."""

from __future__ import annotations

from legacy_migration.ui import main

if __name__ == "__main__":
    raise SystemExit(main())
