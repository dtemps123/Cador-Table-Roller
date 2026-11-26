# Eccentric East NPC generation tables

Compatible with the supplied DnD-Table-Roller `TableRoller.py` format. All 41 JSON files are separate; keep them in the same table directory for external references. No backend changes required.

Copy the folder into your roller repository. From that repository (with your normal DiceTools dependency installed):

```python
from TableRoller import roll_on_table

tables_dir = "eccentric-east-npc-tables"
print(roll_on_table("npc-appearance", tables_dir=tables_dir, verbose=False))
print(roll_on_table("npc-redvale-major", tables_dir=tables_dir, verbose=False))
```

Use `npc-{blackvein,thornhollow,redvale,westbridge}-{incidental,supporting,major}` as the 12 composite entry points. Each references the underlying attribute tables with `external-table:<table-name>`. These reproduce the earlier interactive workshop: major NPCs add war consequences and frontier viewpoint; select the appropriate `npc-war-viewpoint-north`, `npc-war-viewpoint-south`, or `npc-war-viewpoint-neutral` separately according to background and allegiance. The existing backend does not support conditional dispatch based on a previously rolled sibling result. The Cadorian name and origin tables are intended for settlers, not automatic generation of every indigenous culture. Adjust incompatible results as needed.

Weighted rolls are expanded to individual keys (including all 100 ancestry outcomes). Regional occupation roll 20 references `npc-unusual-occupation`. The name selectors reference the respective masculine/feminine tables.

Reference material (noble titles, naming conventions, Ghosts of the War, stat block suggestions) has also been made rollable for convenience; select a relevant entry rather than interpreting these as demographic probabilities.

Validation: every direct keyed result and every file reference checked, with 100 additional randomized rolls per file using the unmodified TableRoller.py and a substitute RollMultiDice function. DiceTools itself was not included in the supplied archive.

## Files

- `npc-ancestry.json`
- `npc-appearance.json`
- `npc-blackvein-incidental.json`
- `npc-blackvein-major.json`
- `npc-blackvein-supporting.json`
- `npc-frontier-viewpoint.json`
- `npc-ghosts-of-the-war.json`
- `npc-given-name.json`
- `npc-indigenous-viewpoint.json`
- `npc-mannerism.json`
- `npc-motivation.json`
- `npc-name-feminine.json`
- `npc-name-masculine.json`
- `npc-naming-conventions.json`
- `npc-noble-given-name.json`
- `npc-noble-name-feminine.json`
- `npc-noble-name-masculine.json`
- `npc-noble-titles.json`
- `npc-occupation-blackvein.json`
- `npc-occupation-redvale.json`
- `npc-occupation-thornhollow.json`
- `npc-occupation-westbridge.json`
- `npc-origin.json`
- `npc-personal-circumstance.json`
- `npc-personality.json`
- `npc-redvale-incidental.json`
- `npc-redvale-major.json`
- `npc-redvale-supporting.json`
- `npc-stat-block-reference.json`
- `npc-surname.json`
- `npc-thornhollow-incidental.json`
- `npc-thornhollow-major.json`
- `npc-thornhollow-supporting.json`
- `npc-unusual-occupation.json`
- `npc-war-consequences.json`
- `npc-war-viewpoint-neutral.json`
- `npc-war-viewpoint-north.json`
- `npc-war-viewpoint-south.json`
- `npc-westbridge-incidental.json`
- `npc-westbridge-major.json`
- `npc-westbridge-supporting.json`
