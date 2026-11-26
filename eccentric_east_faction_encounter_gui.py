#!/usr/bin/env python3
"""Eccentric East regional faction encounter workshop.
Python 3, Tkinter, and the installed TableRoller package.
Run: python eccentric_east_encounter_gui.py [--tables-dir PATH]
"""
import sys
import argparse
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import tempfile

sys.path.append("/Users/dtemples/DnD/Tools/DnD-Table-Roller")
from TableRoller import roll_on_table

REGIONS = {
    'Blackvein': 'blackvein', 'Thornhollow': 'thornhollow',
    'Redvale': 'redvale', 'Westbridge': 'westbridge',
    'Southern Deserts': 'southern-deserts', 'Eastern Highlands': 'eastern-highlands',
    'Subterranean Realms': 'subterranean-realms',
}
REGION_NOTES = {
    'Southern Deserts': 'Eastway and Copper Spurs entries represent desert-margin activity, not established deep-desert presences.',
    'Subterranean Realms': 'Use only in deep mountain passages and occupied lost dwarven holds. The Illithid Colony remains provisional.',
}
DEFAULT_TABLES = Path(__file__).resolve().parent / 'faction-encounter-tables'
REGIONAL_FIELDS = ('faction', 'potential_npcs', 'composition')
MODIFIERS = {'activity': 'encounter-activity', 'disposition': 'encounter-disposition', 'npc_presence': 'encounter-npc-presence'}
FIELDS = ('region', 'faction', 'potential_npcs', 'composition', 'activity', 'disposition', 'npc_presence', 'selected_npcs', 'location', 'date', 'notes')


def result_text(value):
    if isinstance(value, dict):
        if len(value) == 1:
            return result_text(next(iter(value.values())))
        return '\n'.join(f'{k}: {result_text(v)}' for k, v in value.items())
    if isinstance(value, list):
        return '\n'.join(result_text(v) for v in value)
    return '' if value is None else str(value)


def roll(table, directory):
    from TableRoller import roll_on_table
    return roll_on_table(table, tables_dir=str(directory), verbose=False)


def parse_faction(value):
    """Parse a regional result, preserving the Handbook's lists as text."""
    labels = {'Faction': 'faction', 'Potential NPCs': 'potential_npcs', 'Encounter composition': 'composition'}
    record = {}
    for line in result_text(value).splitlines():
        label, sep, val = line.partition(':')
        if sep and label in labels:
            record[labels[label]] = val.strip()
    if set(record) != set(REGIONAL_FIELDS):
        raise ValueError('Regional table result must have Faction, Potential NPCs and Encounter composition labels.')
    return record


def roll_faction(region, directory):
    return parse_faction(roll('faction-encounter-' + REGIONS[region], directory))


def available_factions(region, directory):
    path = Path(directory) / ('faction-encounter-' + REGIONS[region] + '.json')
    with path.open(encoding='utf-8') as file:
        data = json.load(file)
    found = {}
    for value in data['results'].values():
        row = parse_faction(value)
        found[row['faction']] = row
    return found


def blank_record(region='Blackvein'):
    record = dict.fromkeys(FIELDS, '')
    record['region'] = region
    return record


def generate_record(region, directory):
    record = blank_record(region)
    record.update(roll_faction(region, directory))
    for key, table in MODIFIERS.items():
        record[key] = result_text(roll(table, directory))
    return record


def read_record(path):
    with Path(path).open(encoding='utf-8') as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError('An encounter file must contain a JSON object.')
    if not data.get('region') in REGIONS:
        raise ValueError('Encounter file must specify one of the seven supported regions.')
    record = blank_record(data['region'])
    for key in FIELDS:
        value = data.get(key, '')
        if value is not None and not isinstance(value, str):
            raise ValueError(f'Field {key!r} must contain text or null.')
        record[key] = value or ''
    return record, {k: v for k, v in data.items() if k not in FIELDS}


def write_record(path, record, extras=None):
    path = Path(path)
    data = dict(extras or {})
    data.update({key: record.get(key, '') for key in FIELDS})
    payload = json.dumps(data, indent=4, ensure_ascii=False) + '\n'
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.encounter-', suffix='.tmp', delete=False) as file:
            temp = Path(file.name)
            file.write(payload)
        temp.replace(path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


class EncounterGUI:
    def __init__(self, root, directory=DEFAULT_TABLES):
        self.root = root
        root.title('Eccentric East — Regional Faction Encounters')
        root.geometry('1000x760')
        root.minsize(760, 580)
        self.directory = tk.StringVar(value=str(directory))
        self.region = tk.StringVar(value='Blackvein')
        self.status = tk.StringVar(value='Choose a region, then roll or select a faction.')
        self.region_note = tk.StringVar()
        self.path = None
        self.extras = {}
        self.fields = {}
        self.baseline = blank_record()
        self.faction_choice = tk.StringVar()
        self.table_choice = tk.StringVar()
        self.table_type = tk.StringVar(value='Not rolled')
        self._make_widgets()
        self.refresh_tables()
        self.set_record(self.baseline)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.bind('<Control-s>', lambda _: self.save())
        root.bind('<Control-o>', lambda _: self.open_record())
        root.bind('<Command-s>', lambda _: self.save())
        root.bind('<Command-o>', lambda _: self.open_record())

    def _make_widgets(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill='both', expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(4, weight=1)
        ttk.Label(outer, text='Regional Faction Encounters', font=('TkDefaultFont', 17, 'bold')).grid(row=0, column=0, sticky='w')
        top = ttk.Frame(outer)
        top.grid(row=1, column=0, sticky='ew', pady=(8, 5))
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text='Table directory').grid(row=0, column=0, sticky='w', padx=(0, 8))
        entry = ttk.Entry(top, textvariable=self.directory)
        entry.grid(row=0, column=1, sticky='ew')
        entry.bind('<Return>', lambda _: self.refresh_tables())
        ttk.Button(top, text='Browse…', command=self.browse).grid(row=0, column=2, padx=(6, 0))
        ttk.Button(top, text='Refresh', command=self.refresh_tables).grid(row=0, column=3, padx=(6, 0))
        controls = ttk.Frame(outer)
        controls.grid(row=2, column=0, sticky='ew', pady=5)
        ttk.Label(controls, text='Region').pack(side='left', padx=(0, 6))
        combo = ttk.Combobox(controls, textvariable=self.region, values=list(REGIONS), state='readonly', width=24)
        combo.pack(side='left')
        combo.bind('<<ComboboxSelected>>', self.region_changed)
        ttk.Button(controls, text='Roll encounter', command=self.generate).pack(side='left', padx=6)
        ttk.Button(controls, text='New blank', command=self.new_blank).pack(side='left')
        files = ttk.Frame(outer)
        files.grid(row=3, column=0, sticky='ew', pady=(0, 8))
        for label, cmd in [('Open JSON…', self.open_record), ('Save', self.save), ('Save as…', self.save_as), ('Copy encounter', self.copy_record)]:
            ttk.Button(files, text=label, command=cmd).pack(side='left', padx=(0, 5))
        tabs = ttk.Notebook(outer)
        tabs.grid(row=4, column=0, sticky='nsew')
        encounter = ttk.Frame(tabs, padding=8)
        notes = ttk.Frame(tabs, padding=8)
        roller = ttk.Frame(tabs, padding=8)
        tabs.add(encounter, text='Encounter')
        tabs.add(notes, text='Campaign record')
        tabs.add(roller, text='Table roller')
        for tab in (encounter, notes, roller):
            tab.columnconfigure(1, weight=1)
        choose = ttk.Frame(encounter)
        choose.grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 4))
        ttk.Label(choose, text='Choose faction:').pack(side='left')
        self.faction_combo = ttk.Combobox(choose, textvariable=self.faction_choice, state='readonly', width=35)
        self.faction_combo.pack(side='left', padx=6)
        ttk.Button(choose, text='Use faction', command=self.choose_faction).pack(side='left')
        ttk.Label(encounter, textvariable=self.region_note, wraplength=710, foreground='#8b6330').grid(row=1, column=0, columnspan=3, sticky='w')
        for i, (key, label, height) in enumerate([
            ('faction', 'Faction', 1), ('potential_npcs', 'Potential NPCs', 2),
            ('composition', 'Encounter composition', 3), ('activity', 'Activity', 2),
            ('disposition', 'Initial disposition', 2), ('npc_presence', 'Named NPC presence', 2),
            ('selected_npcs', 'NPCs actually present', 2),
        ], 2):
            cmd = self.reroll_faction if key == 'faction' else (lambda k=key: self.reroll_modifier(k)) if key in MODIFIERS else None
            self.add_field(encounter, i, key, label, height, cmd)
        ttk.Label(encounter, text='NPC candidates and composition are suggestions, not guaranteed participants or encounter counts.\nAdjust the disposition and named NPC presence to suit faction motivations and the circumstances.', wraplength=760, justify='left').grid(row=9, column=0, columnspan=3, sticky='w', pady=(5, 0))
        self.add_field(notes, 0, 'date', 'In-game date', 1)
        self.add_field(notes, 1, 'location', 'Encounter location', 2)
        self.add_field(notes, 2, 'notes', 'Notes / outcome', 15)
        notes.rowconfigure(2, weight=1)
        ttk.Label(roller, text='Roll any table independently (including composite regional tables).').grid(row=0, column=0, columnspan=3, sticky='w', pady=4)
        self.table_combo = ttk.Combobox(roller, textvariable=self.table_choice, state='readonly', width=42)
        self.table_combo.grid(row=1, column=0, columnspan=2, sticky='ew')
        ttk.Button(roller, text='Roll table', command=self.roll_any).grid(row=1, column=2, padx=6)
        ttk.Button(roller, text='Roll encounter type', command=self.roll_type).grid(row=2, column=0, sticky='w', pady=6)
        ttk.Label(roller, textvariable=self.table_type, wraplength=540).grid(row=2, column=1, columnspan=2, sticky='w', padx=6)
        ttk.Label(roller, text='Optional: encounter type is conditional on an encounter already being triggered.', wraplength=750).grid(row=3, column=0, columnspan=3, sticky='w')
        self.table_output = tk.Text(roller, wrap='word', height=18, undo=True)
        self.table_output.grid(row=4, column=0, columnspan=2, sticky='nsew', pady=6)
        scroll = ttk.Scrollbar(roller, command=self.table_output.yview)
        scroll.grid(row=4, column=2, sticky='nsw', pady=6)
        self.table_output.configure(yscrollcommand=scroll.set)
        roller.rowconfigure(4, weight=1)
        ttk.Button(roller, text='Copy result', command=lambda: self.copy(self.table_output.get('1.0', 'end-1c'))).grid(row=5, column=0, sticky='w')
        ttk.Label(outer, textvariable=self.status, wraplength=900).grid(row=5, column=0, sticky='ew', pady=(8, 0))

    def add_field(self, parent, row, key, label, height, command=None):
        ttk.Label(parent, text=label, wraplength=155).grid(row=row, column=0, sticky='nw', padx=(0, 8), pady=4)
        widget = tk.Text(parent, height=height, width=45, wrap='word', undo=True)
        widget.grid(row=row, column=1, sticky='nsew', pady=3)
        self.fields[key] = widget
        if command:
            ttk.Button(parent, text='Reroll', command=command).grid(row=row, column=2, sticky='n', padx=(8, 0), pady=3)

    def put(self, key, value):
        widget = self.fields[key]
        widget.delete('1.0', 'end')
        widget.insert('1.0', value)

    def get(self, key):
        return self.fields[key].get('1.0', 'end-1c')

    def record(self):
        return {'region': self.region.get(), **{k: self.get(k) for k in self.fields}}

    def set_record(self, record):
        self.region.set(record['region'])
        for key in self.fields:
            self.put(key, record.get(key, ''))
        self.refresh_factions()
        self.faction_choice.set(record.get('faction', ''))

    def report_error(self, exc):
        messagebox.showerror('Encounter roller', str(exc), parent=self.root)

    def browse(self):
        directory = filedialog.askdirectory(initialdir=self.directory.get(), parent=self.root)
        if directory:
            self.directory.set(directory)
            self.refresh_tables()

    def refresh_factions(self):
        self.region_note.set(REGION_NOTES.get(self.region.get(), ''))
        try:
            choices = list(available_factions(self.region.get(), self.directory.get()))
        except (OSError, ValueError, KeyError, TypeError):
            choices = []
        self.faction_combo.configure(values=choices)
        if self.faction_choice.get() not in choices:
            self.faction_choice.set(choices[0] if choices else '')

    def refresh_tables(self):
        tables = sorted(p.stem for p in Path(self.directory.get()).glob('*.json'))
        self.table_combo.configure(values=tables)
        if self.table_choice.get() not in tables:
            self.table_choice.set('encounter-type' if 'encounter-type' in tables else (tables[0] if tables else ''))
        self.refresh_factions()
        self.status.set(f'{len(tables)} JSON tables found.' if tables else 'No JSON tables found. Browse to the extracted table directory.')

    def confirm_replace(self):
        if self.record() == self.baseline:
            return True
        answer = messagebox.askyesnocancel('Unsaved changes', 'Save changes to the current encounter first?', parent=self.root)
        if answer is None:
            return False
        return self.save() if answer else True

    def region_changed(self, event=None):
        # The new region is the setting for the next encounter. Do not mix old faction data with it.
        new = self.region.get()
        old = self._record_region
        self.region.set(old)
        if not self.confirm_replace():
            return
        self.path, self.extras = None, {}
        self.baseline = blank_record(new)
        self.set_record(self.baseline)
        self.status.set(f'{new}: ready to roll.')

    @property
    def _record_region(self):
        return self.baseline['region']

    def generate(self):
        if not self.confirm_replace():
            return
        try:
            record = generate_record(self.region.get(), self.directory.get())
        except Exception as exc:
            self.report_error(exc)
            return
        self.path, self.extras = None, {}
        self.baseline = blank_record(record['region'])
        self.set_record(record)
        self.status.set('Encounter rolled. Adjust details or save the result.')

    def new_blank(self):
        if self.confirm_replace():
            self.path, self.extras = None, {}
            self.baseline = blank_record(self.region.get())
            self.set_record(self.baseline)
            self.status.set('Blank encounter.')

    def apply_faction(self, row):
        for key, value in row.items():
            self.put(key, value)
        self.put('selected_npcs', '')
        self.faction_choice.set(row['faction'])
        self.status.set('Faction updated; candidate NPCs and composition updated together. Review other fields.')

    def reroll_faction(self):
        try:
            self.apply_faction(roll_faction(self.region.get(), self.directory.get()))
        except Exception as exc:
            self.report_error(exc)

    def choose_faction(self):
        try:
            self.apply_faction(available_factions(self.region.get(), self.directory.get())[self.faction_choice.get()])
        except Exception as exc:
            self.report_error(exc)

    def reroll_modifier(self, key):
        try:
            self.put(key, result_text(roll(MODIFIERS[key], self.directory.get())))
            if key == 'npc_presence':
                self.put('selected_npcs', '')
            self.status.set(f'Rerolled {key.replace("_", " ")}.')
        except Exception as exc:
            self.report_error(exc)

    def roll_any(self):
        try:
            value = roll(self.table_choice.get(), self.directory.get())
            # Keep the display labels of composite subtables.
            if isinstance(value, list):
                output = '\n\n'.join('\n'.join(f'{k}:\n{result_text(v)}' for k, v in item.items()) if isinstance(item, dict) else result_text(item) for item in value)
            else:
                output = result_text(value)
            self.table_output.delete('1.0', 'end')
            self.table_output.insert('1.0', output)
        except Exception as exc:
            self.report_error(exc)

    def roll_type(self):
        try:
            self.table_type.set(result_text(roll('encounter-type', self.directory.get())))
        except Exception as exc:
            self.report_error(exc)

    def open_record(self):
        if not self.confirm_replace():
            return
        path = filedialog.askopenfilename(filetypes=[('JSON files', '*.json'), ('All files', '*')], parent=self.root)
        if not path:
            return
        try:
            record, extras = read_record(path)
        except Exception as exc:
            self.report_error(exc)
            return
        self.path, self.extras = Path(path), extras
        self.baseline = record.copy()
        self.set_record(record)
        self.status.set(f'Loaded {self.path.name}. No rolls performed.')

    def save(self):
        if self.path is None:
            return self.save_as()
        return self.save_to(self.path)

    def save_as(self):
        name = self.get('faction').strip() or 'encounter'
        filename = ''.join(c if c.isalnum() or c in '-_' else '-' for c in name) + '.json'
        path = filedialog.asksaveasfilename(defaultextension='.json', initialfile=filename, filetypes=[('JSON files', '*.json')], parent=self.root)
        return self.save_to(path) if path else False

    def save_to(self, path):
        try:
            record = self.record()
            write_record(path, record, self.extras)
            self.path = Path(path)
            self.baseline = record.copy()
            self.status.set(f'Saved {self.path.name}.')
            return True
        except Exception as exc:
            self.report_error(exc)
            return False

    def copy(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.set('Copied to clipboard.')

    def copy_record(self):
        record = self.record()
        self.copy('\n'.join(f'{key.replace("_", " ").title()}: {record[key]}' for key in FIELDS if record[key]))

    def close(self):
        if self.confirm_replace():
            self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tables-dir', type=Path, default=DEFAULT_TABLES)
    args = parser.parse_args()
    root = tk.Tk()
    EncounterGUI(root, args.tables_dir)
    root.mainloop()


if __name__ == '__main__':
    main()
