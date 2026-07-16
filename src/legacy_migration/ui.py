"""Small Tkinter desktop UI for the local migration POC."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from legacy_migration.cli import (
    ParsedSaveContext,
    _build_save_metadata,
    _format_record_location,
    _parse_pokemon_records,
    _parse_trainer,
    _read_supported_save,
)
from legacy_migration.errors import LegacyMigrationError
from legacy_migration.hashing import sha256_file
from legacy_migration.migration_package import export_migration_package
from legacy_migration.models import PokemonRecord

LOGGER = logging.getLogger(__name__)

DEFAULT_SAVE = Path()
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "Legacy Pokemon Transfer Exports"


class MigrationApp(tk.Tk):
    """Minimal desktop shell over the read-only parser/export workflow."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Legacy Pokemon Migration POC")
        self.geometry("1040x700")
        self.minsize(920, 600)

        self.save_path_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.status_var = tk.StringVar(value="Choose a save file, then inspect it.")
        self.include_boxes_var = tk.BooleanVar(value=True)

        self.context: ParsedSaveContext | None = None
        self.records_by_id: dict[str, PokemonRecord] = {}

        self._build_widgets()

    def _build_widgets(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        file_frame = ttk.LabelFrame(outer, text="Source Save", padding=10)
        file_frame.grid(row=0, column=0, sticky="ew")
        file_frame.columnconfigure(0, weight=1)

        save_entry = ttk.Entry(file_frame, textvariable=self.save_path_var)
        save_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(file_frame, text="Browse...", command=self._browse_save).grid(row=0, column=1)
        ttk.Button(file_frame, text="Inspect", command=self._inspect_save).grid(
            row=0, column=2, padx=(8, 0)
        )

        options_frame = ttk.Frame(outer)
        options_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        ttk.Checkbutton(
            options_frame,
            text="Include supported PC boxes",
            variable=self.include_boxes_var,
            command=self._refresh_records_if_loaded,
        ).pack(side=tk.LEFT)

        info_frame = ttk.LabelFrame(outer, text="Inspection", padding=10)
        info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        self.info_text = tk.Text(info_frame, height=9, wrap=tk.WORD)
        self.info_text.grid(row=0, column=0, sticky="ew")
        self.info_text.configure(state=tk.DISABLED)

        table_frame = ttk.LabelFrame(outer, text="Pokemon Records", padding=10)
        table_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("id", "location", "nickname", "species", "level", "ot", "trainer_id", "warnings")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="extended"
        )
        headings = {
            "id": "ID",
            "location": "Location",
            "nickname": "Nickname",
            "species": "Species",
            "level": "Level",
            "ot": "OT",
            "trainer_id": "Trainer ID",
            "warnings": "Warnings",
        }
        widths = {
            "id": 110,
            "location": 140,
            "nickname": 130,
            "species": 130,
            "level": 70,
            "ot": 120,
            "trainer_id": 100,
            "warnings": 80,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor=tk.W)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        export_frame = ttk.LabelFrame(outer, text="Export", padding=10)
        export_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        export_frame.columnconfigure(0, weight=1)
        ttk.Entry(export_frame, textvariable=self.output_dir_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(export_frame, text="Browse...", command=self._browse_output).grid(
            row=0, column=1
        )
        ttk.Button(export_frame, text="Export Selected", command=self._export_selected).grid(
            row=0, column=2, padx=(8, 0)
        )

        status_label = ttk.Label(outer, textvariable=self.status_var, anchor=tk.W)
        status_label.grid(row=5, column=0, sticky="ew", pady=(10, 0))

    def _browse_save(self) -> None:
        filename = filedialog.askopenfilename(
            title="Choose a Pokemon save file",
            filetypes=(("Save files", "*.sav"), ("All files", "*.*")),
        )
        if filename:
            self.save_path_var.set(filename)

    def _browse_output(self) -> None:
        dirname = filedialog.askdirectory(title="Choose an output directory")
        if dirname:
            self.output_dir_var.set(dirname)

    def _set_info(self, lines: list[str]) -> None:
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, "\n".join(lines))
        self.info_text.configure(state=tk.DISABLED)

    def _inspect_save(self) -> None:
        try:
            save_path = Path(self.save_path_var.get())
            self.context = _read_supported_save(save_path)
            trainer = _parse_trainer(self.context)
            metadata = _build_save_metadata(self.context, trainer)
            lines = [
                f"File: {metadata.source_filename}",
                f"Source read-only: {self.context.source_metadata.is_read_only}",
                f"Size: {metadata.file_size} bytes",
            ]
            if self.context.source_size != len(self.context.data):
                lines.append(f"Parsed save bytes: {len(self.context.data)} bytes")
            lines.extend(
                [
                    f"SHA-256: {metadata.sha256}",
                    f"Format: {self.context.format_name}",
                    f"Game: {metadata.detected_game}",
                    f"Detection confidence: {self.context.confidence}",
                    f"Trainer: {trainer.name}",
                    f"Trainer ID: {trainer.trainer_id}",
                    f"Validation: {metadata.validation_status}",
                    f"Warnings: {len(metadata.warnings)}",
                ]
            )
            lines.extend(f"- {warning}" for warning in metadata.warnings)
            self._set_info(lines)
            self._load_records()
            self.status_var.set(f"Loaded {len(self.records_by_id)} Pokemon record(s).")
        except (LegacyMigrationError, OSError) as exc:
            self.context = None
            self.records_by_id.clear()
            self._clear_table()
            self.status_var.set("Could not inspect save.")
            messagebox.showerror("Inspect Failed", str(exc))

    def _refresh_records_if_loaded(self) -> None:
        if self.context is not None:
            self._load_records()

    def _load_records(self) -> None:
        if self.context is None:
            return
        records = _parse_pokemon_records(
            self.context,
            include_boxes=self.include_boxes_var.get(),
        )
        self.records_by_id = {record.local_id: record for record in records}
        self._clear_table()
        for record in records:
            species = record.species_name or f"0x{record.species_index:02X}"
            self.tree.insert(
                "",
                tk.END,
                iid=record.local_id,
                values=(
                    record.local_id,
                    _format_record_location(record),
                    record.nickname or "",
                    species,
                    str(record.level) if record.level is not None else "",
                    record.original_trainer or "",
                    str(record.trainer_id) if record.trainer_id is not None else "",
                    str(len(record.parsing_warnings)),
                ),
            )

    def _clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _export_selected(self) -> None:
        if self.context is None:
            messagebox.showwarning("No Save Loaded", "Inspect a save before exporting.")
            return
        selected_ids = tuple(self.tree.selection())
        if not selected_ids:
            messagebox.showwarning("No Pokemon Selected", "Select one or more Pokemon records.")
            return

        try:
            trainer = _parse_trainer(self.context)
            metadata = _build_save_metadata(self.context, trainer)
            selected_records = tuple(self.records_by_id[record_id] for record_id in selected_ids)
            output_dir = Path(self.output_dir_var.get())
            package_dir = export_migration_package(
                output_dir=output_dir,
                save_metadata=metadata,
                validation_report=self.context.validation,
                selected_records=selected_records,
            )
            after_digest = sha256_file(Path(self.save_path_var.get()))
            if after_digest != self.context.digest:
                raise LegacyMigrationError(
                    "Critical safety failure: source save hash changed during export. "
                    f"Before {self.context.digest}, after {after_digest}."
                )
            self.status_var.set(f"Exported package: {package_dir}")
            messagebox.showinfo(
                "Export Complete",
                f"Package created:\n{package_dir}\n\nSource SHA-256 verified unchanged.",
            )
        except (KeyError, LegacyMigrationError, OSError) as exc:
            self.status_var.set("Export failed.")
            messagebox.showerror("Export Failed", str(exc))


def main() -> int:
    """Run the Tkinter UI."""
    logging.basicConfig(level=logging.WARNING)
    app = MigrationApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
