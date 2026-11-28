# Regional encounters and wilderness travel

Source: Campaign Handbook v0.4, pp. 35–36, 102–116.

- Seven regional `faction-encounter-{region}.json` d20 tables.
- Seven `encounter-{region}.json` composite tables (region, activity, disposition, NPC presence).
- Three independent modifiers and the conditional `encounter-type.json` (40/30/20/10 distribution).
- `travel-encounter-check.json` d100, with travel probability applied by the GUI.
- Five `travel-narration-{region}.json` d20 tables; 100 verbatim narration entries.

Run `python eccentric_east_faction_encounter_gui.py` from the repository root. The Travel tab checks one leg at a time. All existing regional compositions remain suggestions rather than predetermined encounter sizes or challenges. Use the independent table roller for manual rolls. See the root README for details and record storage.
