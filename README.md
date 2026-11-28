# Cador Table Roller — Eccentric East

Campaign Handbook DRAFT v0.4 (2026-11-27), Legendarium v1.0 (2026-11-25), and the subsequent accepted campaign-record conventions. This revision modifies the working archive supplied by the DM; the original scripts, table folder names, user-specific TableRoller import and Git history are retained.

## Start the workshops

From the repository root, with Python 3 (3.9+), Tkinter, and your existing TableRoller / DiceRollBackend installation:

```sh
python eccentric_east_npc_gui.py
python eccentric_east_faction_encounter_gui.py
python eccentric_east_job_and_rumor_gui.py
python eccentric_east_campaign_record_gui.py
# Open the last workshop directly on the plot editor:
python eccentric_east_campaign_record_gui.py --kind Plot
```

The three existing applications retain:

```python
sys.path.append("/Users/dtemples/DnD/Tools/DnD-Table-Roller")
from TableRoller import roll_on_table
```

The backend is **not bundled or replaced**. Use your installed DiceRollBackend and TableRoller. If using another machine, set `PYTHONPATH` to the backend directory or amend the existing path. The editors for locations and plots do not require a dice backend. All paths default relative to the scripts, not the current working directory. Existing `--tables-dir` overrides remain supported. The NPC and encounter applications also accept `--records-dir`; the opportunity workshop retains `--logs-dir`. The record workshop's `--records-dir` is intended for a single record kind at a time.

## Directory layout

```text
Cador-Table-Roller/
├── eccentric_east_npc_gui.py
├── eccentric_east_faction_encounter_gui.py
├── eccentric_east_job_and_rumor_gui.py
├── eccentric_east_campaign_record_gui.py
├── campaign_records.py
├── npc-generation-tables/             # 41 original tables
├── faction-encounter-tables/          # 24 tables, incl. 5 narration tables + d100 check
├── jobs-and-rumors-tables/            # 17 tables, incl. staff commissions and intro scenarios
├── npc-records/
│   ├── base-npcs/                     # 141 indexed NPCs + 4 example NPCs
│   └── added-npcs/                    # newly generated / authored NPCs
├── faction-encounter-records/         # E-###.json, initially empty
├── job-and-rumor-records/
│   ├── base-jobs/                     # 80 regional + 8 staff commission templates
│   ├── base-rumors/                   # 80 regional rumor templates
│   ├── added-jobs/                    # custom jobs and repeated postings
│   └── added-rumors/                  # custom rumors and repeated circulation
├── faction-plot-records/              # P-001 through P-010; draft, not advanced
├── adventure-location-records/        # illustrative L-RV-001; more to be scaffolded
└── .git/                             # existing history retained
```

There are 82 JSON roll tables. `.gitkeep` files preserve empty directories and `.id-counters.json` files retain the highest assigned IDs. All campaign record folders and counters are Git-trackable. The old `/opportunity-logs/` ignore rule was removed. The supplied archive is a working tree update, not a remote push or a new commit. New and modified files have been staged for review. Once satisfied, commit your changes locally and continue using your own Git workflow. Future record saves are not automatically staged or committed.

## NPC workshop

Use **Generate NPC** for a random incidental, supporting, or major NPC; individual fields can be rerolled. **Search / load** opens a searchable library containing both base and added NPCs. Select a field (name, affiliation, location, biography, etc.) or search all fields, then double-click a result. Save updates the existing record; saving a new NPC allocates the next permanent `N-###` ID in `added-npcs`. Duplicate creates a new record with a new ID rather than overwriting the original.

The base roster includes every one of the 141 indexed people, including historical/deceased/missing individuals, plus Otis Wainwright, Martha Pritchard, Dorrin Hammerfell, and Amos Bridger. `N-001` is Amos to preserve the previously drafted record example. Other IDs are assigned in roster order. Source & status shows provenance, extracted biographical/contextual text, and staff adventure hooks. Some source excerpts are partial or include contextual material rather than a full biography; blank individual traits are intentional, not randomized. Suggested alignments retain their asterisk. The v0.4 staff entries supersede the earlier Legendarium names/alignments. Illustrative NPCs are labeled as such and are not assumed encountered.

## Wilderness Travel & Encounter workshop

The original regional faction generator and modifiers remain available. The Travel tab provides one d100 check per leg: outbound 10% per travel day, return 5%, maximum 100%. Enter whole travel days; adjudicate partial days at the table as desired. On success, the conditional d20 table is rolled: faction 1–8, creature 9–14, terrain/weather 15–18, supernatural/magical 19–20. A faction encounter automatically rolls its regional identity, activity, disposition and named NPC presence. Other types produce editable drafts, not automatic combat statistics. Additional DM-selected encounters remain possible. Choose the encounter region in the main control bar and narration region separately. Southern Deserts is the appropriate faction table for Qasari travel; the Qasari Lands have their own narration table. Narration is independent of encounters and does not imply an adventure hook. Only save encounters of lasting significance.

Campaign record and Outcome & consequences tabs include the agreed template fields, plus the existing faction composition and modifier fields. Search / load searches all saved records by field values. Save assigns `E-###` filenames; duplicates receive new IDs. Old `notes` are preserved separately for compatibility.

## Job Board & Rumor Mill workshop

The 160 regional authored entries and eight permanent-staff commissions are preloaded as **Unposted template** records. They are **not** starting job boards or player-known rumors. Their IDs are reserved up front (for example, J-BV-001 is Blackvein source row 1). Filter the library by type, region, template/activated state, and any field value. Activate a template manually, or use Roll & create log / Initial batch / Monthly additions; the first use activates the original authored record in place, preserving DM edits, and sets the date/status. If repeats are allowed, subsequent uses get new IDs in added-jobs or added-rumors. A new manually authored record is also saved in the added folder. Unposted templates are excluded from used-row counts and retirement counts; copying player-facing text requires activation. Activating is a local change only; it does not send a message or post to Discord. The first 20 IDs per regional job/rumor prefix (and eight WL jobs) are reserved. New manually authored or repeated records use the next unused identifier.

The original 3d6 initial jobs, 2d6 initial rumors, and 1d6 monthly additions/retirement counts are retained. Retirement remains an adjudication decision; no jobs are automatically completed or removed. The initial and monthly batch buttons apply only to the four marquisates. Guildhall commissions use `J-WL-###`; manually created guildhall rumors use `R-WL-###`. There is no automatic WL turnover. Both in-game and real-world dates are available; the real-world posting/introduction date defaults to the local date when a record is activated or created. Retirement dates are entered manually. `Roll reference table…` provides independent access to the introductory scenario table and other reference rolls, without creating a job or rumor.

## Campaign Record workshop

Edit/search/create wilderness locations and faction plots. The ten plot files contain the established inciting events, faction objectives and possible progression, but are marked **Draft — campaign not initialized** with no update date. There is no automated plot advancement. The illustrative Bridger's Crossing record retains L-RV-001 and links to N-001 and P-002; its hex is intentionally unset. Use location IDs with BV, TH, RV, WB, WL, QS, EH, SD, ST, and permanent P-### for plots. The region determines the prefix on first save; changes of region do not change the ID. No new adventure site is invented by the generator: use the editor to scaffold locations from actual map placement and adventure preparation.

## Storage and migration

All records are plain UTF-8 JSON objects. Search is case-insensitive and matches field values (multiple words may be entered). Existing unknown fields are retained. Newly saved files are named by permanent record ID. A legacy NPC or encounter without an ID is saved as a new record in the corresponding default library; the original is not deleted. Legacy records with an ID opened from another folder can be edited in place. Old opportunity logs can be opened individually, or selected via `--logs-dir`; back up your existing records before copying them into the new library. If an old J/R ID conflicts with an authored template, keep the old record in a separate import folder until you have reconciled the IDs and their cross-references. Do not overwrite files or manually reset counters. The shipped archive did not include pre-existing campaign logs.

These are **single-writer local DM tools**, not a concurrent database. Do not have multiple instances saving the same library simultaneously; reconcile Git conflicts before continuing. The ID counter and existing records are checked on allocation. Related-record fields contain IDs as editable text; automatic referential validation and a shared live database are deliberately not implemented.

## Validation and known boundaries

All 82 tables, including 1,097 keyed outcomes, were exercised using the original TableRoller.py from the project's DnD-Table-Roller archive and a temporary stand-in for the missing DiceRollBackend package. The stand-in is not included in this repository. All four applications (five editor modes) passed Tkinter initialization and save/load/generation smoke tests using a virtual Linux display. Additional tests verified seeded template activation, repeat allocation, case-insensitive search, monotonic counters, and travel chance boundaries. Actual installed DiceRollBackend and native macOS/Tk appearance still require verification on the DM's computer.

Pending campaign work: faction-specific stat block archetypes, finalized cartography and geographical reconciliation, further adventure location scaffolding and published-adventure adaptations, and initializing the actual opening world state, jobs and rumors. None of those unresolved design decisions have been invented by the software.
