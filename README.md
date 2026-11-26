# Eccentric East — Regional Faction Encounter Tables

Source: Eccentric East Campaign Handbook, DRAFT v0.2 (261125), PDF pp. 71–78.

## Contents

- `faction-encounter-{region}.json`: seven weighted d20 regional tables. Each result preserves the faction, potential NPCs and encounter composition from the Handbook. Weighted ranges are expanded to individual keys, as required by TableRoller.
- `encounter-activity.json`: d12 nature of the encounter.
- `encounter-disposition.json`: 2d6 initial disposition (not a uniform d11).
- `encounter-npc-presence.json`: d20 named NPC presence.
- `encounter-type.json`: optional d20 encounter type, conditional on an encounter already occurring. It does not set an encounter frequency.
- `encounter-{region}.json`: seven composite tables with four external-table references each. They roll the region, activity, initial disposition and NPC presence independently.

Region suffixes: `blackvein`, `thornhollow`, `redvale`, `westbridge`, `southern-deserts`, `eastern-highlands`, `subterranean-realms`.

## Use with TableRoller

Keep these 18 JSON files in one directory. The source tables remain independent; the composite tables only reference them.

```python
from TableRoller import roll_on_table

folder = './eccentric-east-encounter-tables'
print(roll_on_table('faction-encounter-redvale', tables_dir=folder, verbose=False))
print(roll_on_table('encounter-redvale', tables_dir=folder, verbose=False))
```

## GUI

Place `eccentric_east_encounter_gui.py` alongside the table directory. With TableRoller and its DiceRollBackend dependency installed, and Tkinter available, run:

```sh
python eccentric_east_encounter_gui.py
```

Or supply `--tables-dir /path/to/tables`. The directory can also be selected in the GUI. The Encounter tab lets you roll a complete encounter, choose a faction manually, edit the output, and reroll faction (including candidate NPCs and composition), activity, disposition or NPC presence. Candidate NPCs are not guaranteed participants; choose actual participants according to their circumstances. Rerolling faction or NPC presence clears the actual NPC selection so it can be reconsidered. The Campaign record tab provides date, location and notes/outcome. Save or load individual encounter JSON records; keep those records outside the table directory. The Table roller tab rolls individual and composite tables independently. The encounter-type roll is optional and does not alter the faction record.

## Adjudication notes

The southern-desert Eastway and Copper Spurs entries concern proposed desert-margin activity. Use the subterranean table only in deep mountain passages and occupied lost dwarven holds. The Illithid Colony is provisional and its named NPC entry remains TBD. Encounter composition lists are possibilities, not group sizes, stat blocks or guarantees. Disposition and NPC presence should be adjusted by the DM to fit motivations, reputation and circumstances. No travel encounter frequency or automatic combat difficulty has been introduced.

## Validation

Tested against the unmodified TableRoller.py from the supplied archive using a substitute DiceRollBackend (the actual dice dependency was not included). All 203 keyed outcomes and 28 external references checked; 700 generated encounters and 700 composite rolls passed. Tkinter initialization, rerolls, manual faction selection, region change, table rolling and JSON round-trip smoke tested using a virtual Linux display. Native macOS appearance and the installed dice package were not tested.
