#!/usr/bin/env python3
"""Launch the Eccentric East DM workshops using the current Python interpreter."""
import subprocess
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

HERE = Path(__file__).resolve().parent
WORKSHOPS = (
    ('npc', 'Frontier NPC Workshop', 'Generate, search, and maintain NPC records.', 'eccentric_east_npc_gui.py', ()),
    ('encounter', 'Wilderness Travel & Encounters', 'Roll travel checks, narration and faction encounters; record significant events.', 'eccentric_east_faction_encounter_gui.py', ()),
    ('opportunity', 'Job Board & Rumor Mill', 'Generate, activate, search and update jobs and rumors.', 'eccentric_east_job_and_rumor_gui.py', ()),
    ('record', 'Wilderness Location Editor', 'Scaffold, search and update adventure locations.', 'eccentric_east_campaign_record_gui.py', ('--kind', 'Location')),
    ('record', 'Faction Plot Tracker', 'Maintain the ten living frontier conflicts and their developments.', 'eccentric_east_campaign_record_gui.py', ('--kind', 'Plot')),
)


def launch_command(script, args=()):
    path = HERE / script
    if not path.is_file():
        raise FileNotFoundError(path)
    return [sys.executable, str(path), *args]


class Launcher:
    def __init__(self, root):
        self.root = root
        self.children = {}
        self.buttons = {}
        root.title('Eccentric East — DM Workshop Launcher')
        root.minsize(620, 480)
        outer = ttk.Frame(root, padding=22)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='THE ECCENTRIC EAST', font=('TkDefaultFont', 20, 'bold')).pack(anchor='w')
        ttk.Label(outer, text='Cador Table Roller  •  DM Workshop Launcher', font=('TkDefaultFont', 12)).pack(anchor='w', pady=(2, 10))
        ttk.Separator(outer).pack(fill='x', pady=(0, 12))
        for key, name, description, script, args in WORKSHOPS:
            row = ttk.Frame(outer, padding=(0, 7))
            row.pack(fill='x')
            row.columnconfigure(0, weight=1)
            ttk.Label(row, text=name, font=('TkDefaultFont', 11, 'bold')).grid(row=0, column=0, sticky='w')
            ttk.Label(row, text=description, wraplength=475, justify='left').grid(row=1, column=0, sticky='w', pady=(3, 0))
            button = ttk.Button(row, text='Open', width=12, command=lambda k=key, s=script, a=args: self.open(k, s, a))
            button.grid(row=0, column=1, rowspan=2, padx=(14, 0))
            self.buttons.setdefault(key, []).append(button)
        ttk.Separator(outer).pack(fill='x', pady=12)
        self.status = tk.StringVar(value='Ready. Select a workshop to begin.')
        ttk.Label(outer, textvariable=self.status, wraplength=570).pack(anchor='w')
        ttk.Label(outer, text='Location and Plot share one editor; switch record type inside it.', wraplength=570).pack(anchor='w', pady=(6, 0))
        ttk.Button(outer, text='Close launcher', command=self.close).pack(anchor='e', pady=(12, 0))
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(300, self.poll)

    def open(self, key, script, args=()):
        self.poll_children()
        if key in self.children:
            self.status.set('This workshop is already open. Use its existing window.')
            return
        log = None
        try:
            command = launch_command(script, args)
            log = tempfile.TemporaryFile(mode='w+b')
            proc = subprocess.Popen(command, cwd=HERE, stderr=log)
        except (OSError, ValueError) as exc:
            if log is not None:
                log.close()
            messagebox.showerror('Unable to launch workshop', str(exc), parent=self.root)
            return
        self.children[key] = (proc, log, script)
        for button in self.buttons[key]:
            button.configure(state='disabled', text='Running')
        self.status.set(f'Opened {script}.')

    def poll_children(self):
        for key, (proc, log, script) in list(self.children.items()):
            code = proc.poll()
            if code is None:
                continue
            del self.children[key]
            for button in self.buttons[key]:
                button.configure(state='normal', text='Open')
            self.status.set(f'{script} closed.')
            if code:
                log.seek(0, 2)
                log.seek(max(0, log.tell() - 6000))
                detail = log.read().decode('utf-8', errors='replace').strip()
                messagebox.showerror('Workshop exited with an error',
                    f'{script} exited with code {code}.\n\n{detail or "Run the script directly in Terminal for details."}', parent=self.root)
            log.close()

    def poll(self):
        self.poll_children()
        self.root.after(300, self.poll)

    def close(self):
        # Workshops own their windows and unsaved changes. Never terminate them here.
        for _, log, _ in self.children.values():
            log.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    Launcher(root)
    root.mainloop()


if __name__ == '__main__':
    main()
