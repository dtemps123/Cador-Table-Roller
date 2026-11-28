#!/usr/bin/env python3
"""Eccentric East NPC Workshop. Python 3 + Tkinter + installed TableRoller.

Run: python eccentric_east_npc_gui.py [--tables-dir PATH]
Place the extracted eccentric-east-npc-tables directory beside this script,
or select it in the GUI. Existing JSON tables are never modified.
"""
import sys
import argparse
import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

sys.path.append("/Users/dtemples/DnD/Tools/DnD-Table-Roller")
from TableRoller import roll_on_table
from campaign_records import HERE, allocate, choose_record, atomic_json, matches

REGIONS = ("Blackvein", "Thornhollow", "Redvale", "Westbridge")
DEPTHS = ("Incidental", "Supporting", "Major")
DEFAULT_TABLES = Path(__file__).resolve().parent / "npc-generation-tables"

# key, label, text height, can reroll
SECTIONS = {
    "Identity": [
        ("name", "Name", 1, True),
        ("ancestry", "Ancestry", 1, True),
        ("alignment", "Alignment", 1, False),
        ("age", "Age", 1, False),
        ("occupation", "Occupation", 1, True),
        ("origin", "Origin", 2, True),
        ("current_location", "Current location", 1, False),
        ("affiliation", "Affiliation", 2, False),
    ],
    "Characterization": [
        ("appearance", "Appearance", 3, True),
        ("portrayal", "Portrayal", 5, True),
        ("motivations", "Motivations", 3, True),
        ("personal_circumstances", "Personal circumstances", 4, True),
    ],
    "History & politics": [
        ("viewpoint_of_the_war", "Viewpoint of the war", 5, True),
        ("war_consequences", "Personal consequences of the war", 3, True),
        ("viewpoint_of_the_frontier", "Viewpoint of the frontier", 4, True),
        ("relationships", "Relationships", 4, False),
    ],
    "Source & status": [
        ("record_status", "Record status", 2, False),
        ("source_reference", "Source reference", 3, False),
        ("source_profile", "Source biography / excerpt", 12, False),
        ("adventure_hooks", "Adventure hooks", 4, False),
    ],
    "Campaign records": [
        ("knowledge_and_rumors", "Knowledge and rumors", 5, False),
        ("stat_block", "Stat block / reference", 3, False),
        ("first_encounter", "First encounter", 3, False),
        ("subsequent_interactions_and_developments", "Subsequent interactions and developments", 7, False),
    ],
}
FIELDS = tuple(f[0] for group in SECTIONS.values() for f in group)


def result_text(result):
    """Unwrap TableRoller's external-table labels; retain multi-result content."""
    if isinstance(result, dict):
        if len(result) == 1:
            return result_text(next(iter(result.values())))
        return "\n".join(f"{k}: {result_text(v)}" for k, v in result.items())
    if isinstance(result, list):
        return "\n".join(result_text(v) for v in result)
    return "" if result is None else str(result)


def roll(table, directory):
    # Lazy import: saved NPCs can still be opened and edited without the roller.
    from TableRoller import roll_on_table
    return result_text(roll_on_table(table, tables_dir=str(directory), verbose=False))


def war_table(origin, preference):
    if preference != "Auto (origin)":
        return "npc-war-viewpoint-" + preference.lower()
    if origin.strip().lower().startswith("northern cador"):
        return "npc-war-viewpoint-north"
    if origin.strip().lower().startswith("southern cador"):
        return "npc-war-viewpoint-south"
    return "npc-war-viewpoint-neutral"


def roll_field(key, record, directory, region, name_style="Either",
               noble=False, war="Auto (origin)", frontier="Cadorian"):
    def r(table):
        return roll(table, directory)

    if key == "name":
        if noble:
            given = {"Either": "npc-noble-given-name", "Masculine": "npc-noble-name-masculine",
                     "Feminine": "npc-noble-name-feminine"}[name_style]
        else:
            given = {"Either": "npc-given-name", "Masculine": "npc-name-masculine",
                     "Feminine": "npc-name-feminine"}[name_style]
        # Even noble given names use the ordinary surname pool as a starting point.
        return f"{r(given)} {r('npc-surname')}"
    if key == "portrayal":
        return f"Personality: {r('npc-personality')}\nMannerism: {r('npc-mannerism')}"
    if key == "viewpoint_of_the_war":
        return r(war_table(record.get("origin", ""), war))
    if key == "viewpoint_of_the_frontier":
        return r("npc-indigenous-viewpoint" if frontier == "Indigenous" else "npc-frontier-viewpoint")
    tables = {
        "ancestry": "npc-ancestry", "origin": "npc-origin",
        "occupation": "npc-occupation-" + region.lower(),
        "appearance": "npc-appearance", "motivations": "npc-motivation",
        "personal_circumstances": "npc-personal-circumstance",
        "war_consequences": "npc-war-consequences",
    }
    return r(tables[key])


def generate_record(directory, region, depth, **options):
    record = dict.fromkeys(FIELDS, "")
    record["current_location"] = region
    keys = ["name", "ancestry", "origin", "occupation", "appearance", "portrayal"]
    if depth in ("Supporting", "Major"):
        keys += ["motivations", "personal_circumstances"]
    if depth == "Major":
        keys += ["viewpoint_of_the_war", "war_consequences", "viewpoint_of_the_frontier"]
    for key in keys:
        record[key] = roll_field(key, record, directory, region, **options)
    return record


def read_record(path):
    with Path(path).open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("An NPC file must contain a JSON object.")
    record = {}
    for key in FIELDS:
        value = data.get(key, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            if key == "age" and isinstance(value, (int, float)) and not isinstance(value, bool):
                value = str(value)
            else:
                raise ValueError(f"Field '{key}' must contain text or null.")
        record[key] = value
    # Preserve fields from other tools, even when not editable in this workshop.
    extras = {key: val for key, val in data.items() if key not in FIELDS}
    return record, extras


def write_record(path, record, extras=None):
    path = Path(path)
    # Serialize first, then atomically replace the destination.
    data = dict(extras or {})
    data.update({key: record.get(key, "") for key in FIELDS})
    payload = json.dumps(data, indent=4, ensure_ascii=False) + "\n"
    import tempfile
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".npc-", suffix=".tmp", delete=False) as file:
            temp = Path(file.name)
            file.write(payload)
        temp.replace(path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


class NPCWorkshop:
    def __init__(self, root, tables_dir, records_dir=HERE / "npc-records"):
        self.root = root
        self.records_dir = Path(records_dir)
        self.path = None
        self.extras = {}
        self.widgets = {}
        self.saved = dict.fromkeys(FIELDS, "")
        self.tables_dir = tk.StringVar(value=str(tables_dir))
        self.region = tk.StringVar(value="Redvale")
        self.depth = tk.StringVar(value="Supporting")
        self.name_style = tk.StringVar(value="Either")
        self.noble = tk.BooleanVar(value=False)
        self.war = tk.StringVar(value="Auto (origin)")
        self.frontier = tk.StringVar(value="Cadorian")
        self.status = tk.StringVar(value="Ready — generate an NPC or open an existing record.")
        root.title("Eccentric East — NPC Workshop")
        root.geometry("1000x790")
        root.minsize(720, 540)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.build()

    def build(self):
        root = self.root
        menu = tk.Menu(root)
        file_menu = tk.Menu(menu, tearoff=False)
        for label, cmd, shortcut in [("New blank NPC", self.new, "Ctrl+N"),
                                     ("Open NPC…", self.open, "Ctrl+O"),
                                     ("Save NPC", self.save, "Ctrl+S"),
                                     ("Duplicate NPC…", self.save_as, "Ctrl+Shift+S")]:
            file_menu.add_command(label=label, command=cmd, accelerator=shortcut)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.close)
        menu.add_cascade(label="File", menu=file_menu)
        root.config(menu=menu)
        for key, cmd in [("n",self.new),("o",self.open),("s",self.save),("S",self.save_as)]:
            for modifier in ("Control", "Command") if root.tk.call("tk", "windowingsystem") == "aqua" else ("Control",):
                root.bind(f"<{modifier}-{key}>", lambda event, c=cmd: (c(), "break")[1])
        top = ttk.Frame(root, padding=(12, 10))
        top.pack(fill="x")
        ttk.Label(top, text="Frontier NPC Workshop", font=("TkDefaultFont", 18, "bold")).pack(anchor="w")
        ttk.Label(top, text="The Eccentric East • 3E-992").pack(anchor="w")
        pathbar = ttk.Frame(top)
        pathbar.pack(fill="x", pady=(10, 5))
        ttk.Label(pathbar, text="Table directory").pack(side="left", padx=(0, 8))
        ttk.Entry(pathbar, textvariable=self.tables_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(pathbar, text="Browse…", command=self.browse).pack(side="left", padx=(6, 0))
        settings = ttk.LabelFrame(top, text="Generation settings", padding=8)
        settings.pack(fill="x", pady=5)
        for col, (label, var, vals) in enumerate([
            ("Marquisate", self.region, REGIONS), ("Detail", self.depth, DEPTHS),
            ("Given name", self.name_style, ("Either", "Masculine", "Feminine")),
            ("War viewpoint", self.war, ("Auto (origin)", "North", "South", "Neutral")),
            ("Frontier viewpoint", self.frontier, ("Cadorian", "Indigenous")),
        ]):
            ttk.Label(settings, text=label).grid(row=0, column=col, sticky="w", padx=4)
            ttk.Combobox(settings, textvariable=var, values=vals, state="readonly", width=15).grid(row=1, column=col, sticky="ew", padx=4)
            settings.columnconfigure(col, weight=1)
        ttk.Checkbutton(settings, text="Use noble given names", variable=self.noble).grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=(5,0))
        bar = ttk.Frame(top)
        bar.pack(fill="x", pady=(5,0))
        for label, command in [("Generate NPC", self.generate), ("New blank", self.new),
                               ("Search / load…", self.open), ("Save", self.save),
                               ("Duplicate…", self.save_as)]:
            ttk.Button(bar, text=label, command=command).pack(side="left", padx=(0,6))
        ttk.Label(bar, text="All fields editable").pack(side="right")
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0,8))
        for title, fields in SECTIONS.items():
            page = ttk.Frame(self.tabs, padding=12)
            self.tabs.add(page, text=title)
            page.columnconfigure(1, weight=1)
            for row, (key, label, height, randomizable) in enumerate(fields):
                ttk.Label(page, text=label, wraplength=185).grid(row=row, column=0, sticky="nw", pady=4, padx=(0,10))
                frame = ttk.Frame(page)
                frame.grid(row=row, column=1, sticky="nsew", pady=4)
                widget = tk.Text(frame, height=height, width=40, wrap="word", undo=True, font="TkTextFont", padx=5, pady=3)
                scroll = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
                widget.configure(yscrollcommand=scroll.set)
                widget.pack(side="left", fill="both", expand=True)
                scroll.pack(side="right", fill="y")
                self.widgets[key] = widget
                if height > 1:
                    page.rowconfigure(row, weight=1)
                if randomizable:
                    ttk.Button(page, text="Reroll", command=lambda k=key: self.reroll(k)).grid(row=row, column=2, sticky="n", padx=(8,0), pady=4)
        self.build_browser()
        ttk.Label(root, textvariable=self.status, padding=(12,6), wraplength=940).pack(fill="x")

    def build_browser(self):
        page = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(page, text="Table roller")
        ttk.Label(page, text="Roll any JSON table independently; copy its result into an NPC field if desired.", wraplength=750).pack(anchor="w", pady=(0,8))
        row = ttk.Frame(page)
        row.pack(fill="x")
        self.table_name = tk.StringVar(value="npc-ghosts-of-the-war")
        self.table_combo = ttk.Combobox(row, textvariable=self.table_name)
        self.table_combo.pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Refresh list", command=self.refresh_tables).pack(side="left", padx=5)
        ttk.Button(row, text="Roll table", command=self.roll_selected).pack(side="left")
        self.table_output = tk.Text(page, wrap="word", height=12, font="TkTextFont", padx=6, pady=6)
        self.table_output.pack(fill="both", expand=True, pady=10)
        ttk.Button(page, text="Copy result", command=self.copy_result).pack(anchor="w")
        self.refresh_tables()

    def refresh_tables(self):
        directory = Path(self.tables_dir.get()).expanduser()
        self.table_combo.configure(values=sorted(p.stem for p in directory.glob("*.json")))

    def roll_selected(self):
        try:
            name = self.table_name.get().strip()
            if not name or Path(name).name != name or name in (".", ".."):
                raise ValueError("Enter a table name without a directory.")
            output = roll(name.removesuffix(".json"), self.directory())
            self.table_output.delete("1.0", "end")
            self.table_output.insert("1.0", output)
            self.status.set(f"Rolled {name}.")
        except Exception as exc:
            self.error(exc)

    def copy_result(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.table_output.get("1.0", "end-1c"))
        self.status.set("Table result copied.")

    def browse(self):
        directory = filedialog.askdirectory(parent=self.root, initialdir=self.tables_dir.get())
        if directory:
            self.tables_dir.set(directory)
            self.refresh_tables()
            self.status.set(f"Using tables in {directory}")

    def directory(self):
        directory = Path(self.tables_dir.get()).expanduser()
        if not directory.is_dir():
            raise FileNotFoundError(f"Table directory not found: {directory}\nChoose the extracted table folder using Browse.")
        return directory

    def options(self):
        return dict(name_style=self.name_style.get(), noble=self.noble.get(),
                    war=self.war.get(), frontier=self.frontier.get())

    def record(self):
        return {key: widget.get("1.0", "end-1c") for key, widget in self.widgets.items()}

    def set_field(self, key, value):
        widget = self.widgets[key]
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    def apply_record(self, record):
        for key in FIELDS:
            self.set_field(key, record.get(key, ""))
            self.widgets[key].edit_reset()
        self.tabs.select(0)

    def can_replace(self):
        if self.record() == self.saved:
            return True
        answer = messagebox.askyesnocancel("Unsaved changes", "Save changes to this NPC before continuing?", parent=self.root)
        if answer is None:
            return False
        return self.save() if answer else True

    def generate(self):
        if not self.can_replace():
            return
        try:
            record = generate_record(self.directory(), self.region.get(), self.depth.get(), **self.options())
        except Exception as exc:
            self.error(exc)
            return
        self.path, self.extras = None, {}
        self.saved = dict.fromkeys(FIELDS, "")
        self.apply_record(record)
        self.update_title()
        self.status.set(f"Generated {record['name']} — edit or reroll individual fields, then save.")

    def reroll(self, key):
        try:
            value = roll_field(key, self.record(), self.directory(), self.region.get(), **self.options())
        except Exception as exc:
            self.error(exc)
            return
        self.set_field(key, value)
        self.status.set(f"Rerolled {key.replace('_', ' ')}. Other fields unchanged.")

    def new(self):
        if not self.can_replace():
            return
        self.path, self.extras = None, {}
        self.saved = dict.fromkeys(FIELDS, "")
        self.apply_record(self.saved)
        self.update_title()
        self.status.set("Blank NPC — enter details or reroll individual fields.")

    def open(self):
        if not self.can_replace():
            return
        path = choose_record(self.root, self.records_dir, ("npc_id", *FIELDS), "npc_id")
        if not path:
            return
        try:
            record, extras = read_record(path)
        except Exception as exc:
            self.error(exc)
            return
        self.path, self.extras = Path(path), extras
        self.apply_record(record)
        self.saved = record.copy()
        location = record["current_location"].lower()
        for region in REGIONS:
            if region.lower() in location:
                self.region.set(region)
                break
        self.update_title()
        self.status.set(f"Loaded {path}. No random rolls performed.")

    def save(self):
        return self.save_to(self.path)

    def save_as(self):
        if self.path is not None and not messagebox.askyesno("Duplicate NPC", "Create a new NPC with a new ID?", parent=self.root): return False
        return self.save_to(None)

    def save_to(self, path):
        record = self.record()
        try:
            if not record['name'].strip(): raise ValueError('Enter an NPC name before saving.')
            data = dict(self.extras); data.update(record)
            if path is None or not data.get('npc_id'):
                path = allocate(self.records_dir, self.records_dir / 'added-npcs', 'N', 'npc_id', data)
            else:
                write_record(path, record, self.extras)
            self.extras = {k:v for k,v in data.items() if k not in FIELDS}
        except Exception as exc:
            self.error(exc); return False
        self.path, self.saved = Path(path), record.copy()
        self.update_title(); self.status.set(f"Saved {path}"); return True

    def update_title(self):
        self.root.title("Eccentric East — NPC Workshop" + (f" — {self.path.name}" if self.path else ""))

    def error(self, exc):
        messagebox.showerror("NPC Workshop", f"{type(exc).__name__}: {exc}", parent=self.root)
        self.status.set("Operation failed; existing NPC retained.")

    def close(self):
        if self.can_replace():
            self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES)
    parser.add_argument("--records-dir", type=Path, default=HERE / "npc-records")
    args = parser.parse_args()
    root = tk.Tk()
    NPCWorkshop(root, args.tables_dir, args.records_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
