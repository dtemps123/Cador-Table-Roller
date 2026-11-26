# Eccentric East — Job Boards & Rumor Mills

## Install and run

Extract the ZIP alongside the other Eccentric East generators. It contains
`eccentric_east_opportunity_gui.py` and `eccentric-east-opportunity-tables/`.
With TableRoller and its DiceRollBackend dependency installed in your Python
environment (and Tkinter available):

```bash
python eccentric_east_opportunity_gui.py
# Optional paths:
python eccentric_east_opportunity_gui.py --tables-dir /path/to/tables --logs-dir /path/to/logs
```

The default logs directory is `opportunity-logs/` next to the script. Keep it
separate from the table directory. The GUI does not modify source tables.

## Table contents

The eight regional d20 tables transcribe all 80 jobs and 80 rumors from the
Campaign Handbook DRAFT v0.2 (261125), PDF pages 44–51 and 53–66 respectively.
Every result retains its source row and PDF page. Line breaks and column
layout are normalized. Two merged PDF text cells (Blackvein job 13 and
Thornhollow job 13) are separated back into their original columns. Original
wording, including source spellings such as Thalessa Namaris, is retained.

- `job-board-{blackvein,thornhollow,redvale,westbridge}.json`: full posting,
  posting location, and NPC/faction references.
- `rumor-mill-{blackvein,thornhollow,redvale,westbridge}.json`: original rumor
  and first lead. A first lead is not necessarily the source of the rumor.
- `job-board-any-region.json`, `rumor-mill-any-region.json`: optional d4
  region selectors using external-table references (each region is equally
  likely).
- `initial-job-count.json` (3d6), `initial-rumor-count.json` (2d6),
  `monthly-job-add-count.json` (1d6), `monthly-job-retire-count.json` (1d6),
  `monthly-rumor-add-count.json` (1d6): independent count tables reflecting
  the subsequently agreed management procedure.

Example backend calls (no GUI needed):

```python
from TableRoller import roll_on_table
folder = './eccentric-east-opportunity-tables'
print(roll_on_table('job-board-redvale', tables_dir=folder, verbose=False))
print(roll_on_table('rumor-mill-blackvein', tables_dir=folder, verbose=False))
```

## GUI workflow

1. Choose Job or Rumor, a region, and optionally the in-game date. Roll & create
   log immediately saves one result, assigns an ID, and opens it for editing.
2. Enter missing facts as appropriate; Save updates that same JSON file. New
   blank creates a manual draft; its ID is assigned at first save. The
   original source row remains attached to generated records for traceability.
3. Filter the log library by type, region, or search text. Double-click a row
   or select Load selected record. Open JSON can edit a log from another
   directory in place. Loading does not roll anything.
4. Initial batch and Monthly additions roll the appropriate count for the
   selected type and region, ask for confirmation, and save one log per result.
   Run separately for each region/type. Retirement count rolls 1d6 and reports
   how many open jobs are available. Choose the appropriate jobs yourself and
   record status, retirement date, outcome, and consequences. No jobs are
   retired automatically and faction trackers are not modified.
5. Copy public text copies the selected job posting, posting location, reward,
   and status, or the original rumor text, with its title and ID. It deliberately
   excludes first leads and DM-only fields. Review before sharing. Private
   rumors are not automatically disseminated; record recipients yourself.

Unused entries only is enabled by default. It filters previously logged
source rows (including retired or archived ones) and uses make_table_roll
from TableRoller to roll uniformly over the remaining entries. Each regional
source pool is finite (20). If it is exhausted, batch creation stops with a
count of records already created. Add new rows to your table and adjust the
normal dice expression, create a blank manual log, or deliberately disable
this option to reuse an entry. Disabling it restores ordinary with-replacement
rolls through roll_on_table. Do not reuse a source row number for a different
entry; append a new number instead.

## Log IDs and schema

IDs are sequential within record type and originating region: `J-BV-001`,
`R-BV-001`, `J-RV-001`, etc. Each file is named after its ID. The hidden
`.id-counters.json` file preserves the high-water marks between runs, including
when a log is removed. Back up this file along with all logs, and use one
campaign log directory and one active writer. Separate directories have
independent counters; IDs are not intended to be globally unique across
separate campaigns or synchronized writers. External logs opened for editing
are saved in place; put them in your campaign log directory to include them
in the library and duplicate-entry checks.

All log fields are editable except ID, type, region of origin, and source
provenance. IDs are not changed by editing or loading. Extra JSON keys are
preserved. Both record types include `record_type`, `region`, `source_table`,
`source_row`, `source_page`, and `title`. Values in the standard fields are
strings; empty values mean not yet established. The full record fields match
the earlier job/rumor log templates, with additions for provenance and the
rumor first lead and archived flag. Job NPC/faction columns are split at the
source semicolon; unlisted factions are left blank. Employer and reward are
not inferred from the posting location or NPC list. Rumor reliability defaults
to Undetermined, not a randomly chosen truth value. Statuses can be edited
manually, including combined rumor statuses. Editing a record does not
advance campaign plots.

## Validation

Tested against TableRoller.py extracted unchanged from DnD-Table-Roller.zip,
with a test substitute for the separate DiceRollBackend dependency (not
included in the archive). All 160 source rows, 200 external-reference rolls,
500 count rolls, and 160 unique log creations passed. Checked exhaustion,
repeat rolls, persisted counters, extra-field preservation, and Tkinter
save/load/edit, switching with unsaved changes, batch generation and public
text copying under a virtual Linux display. Not tested natively on macOS or
with the user's installed DiceRollBackend. The filtered roller requires
support for arbitrary positive dice sizes, such as 1d19; if the installed
dice backend does not support them, uncheck Unused entries only to use d20.
