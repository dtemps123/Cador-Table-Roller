"""Run: python tests/validate_tables.py (with real TableRoller/DiceRollBackend installed)."""
import sys, json, re, tempfile, shutil
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.append('/Users/dtemples/DnD/Tools/DnD-Table-Roller')
import TableRoller as tr
import eccentric_east_faction_encounter_gui as enc
import eccentric_east_job_and_rumor_gui as opp
from campaign_records import allocate, matches

count=0
for p in sorted(ROOT.glob('*-tables/*.json')):
    data=json.loads(p.read_text(encoding='utf-8')); expr=data.get('dice',''); m=re.fullmatch(r'(\d+)d(\d+)',expr)
    if m and isinstance(data.get('results'),dict):
        a,b=map(int,m.groups());assert set(data['results'])=={str(n) for n in range(a,a*b+1)},p
        original=tr.dice.RollMultiDice
        for n in range(a,a*b+1):
            with patch.object(tr.dice,'RollMultiDice',side_effect=lambda x,n=n: n if x==expr else original(x)):
                tr.roll_on_table(p.stem,tables_dir=str(p.parent),verbose=False)
            count+=1
    else:tr.roll_on_table(p.stem,tables_dir=str(p.parent),verbose=False)
print(f'Validated {count} keyed outcomes across {len(list(ROOT.glob("*-tables/*.json")))} tables.')
for leg,days,expected in [('Outbound',0,0),('Outbound',3,30),('Return',3,15),('Return',20,100)]:
    with patch.object(tr.dice,'RollMultiDice',return_value=1):
        chance,roll,kind=enc.check_travel(days,leg,enc.DEFAULT_TABLES);assert chance==expected and bool(kind)==bool(expected)
with tempfile.TemporaryDirectory() as d:
    root=Path(d); path=allocate(root,root/'added','N','npc_id',{'name':'First'});path.unlink();path=allocate(root,root/'added','N','npc_id',{'name':'Second','affiliation':'Iron Spurs'});assert path.stem=='N-002';assert matches(json.loads(path.read_text()),'affiliation','iron spurs')
    # Isolated one-row seed library, independent of actual campaign state.
    store=opp.Store(root/'jobs');table=json.loads((ROOT/'jobs-and-rumors-tables/job-board-blackvein.json').read_text());raw=table['results']['1'];r=opp.parse_row(raw,'Job','Blackvein');r.update(job_id='J-BV-001',status='Unposted template');p=store.path/'base-jobs/J-BV-001.json';opp.atomic_json(p,r);assert not store.used_rows('Job','Blackvein')
    with patch.object(opp,'roll',return_value=raw):
        path,new=opp.generate('Job','Blackvein',ROOT/'jobs-and-rumors-tables',store,unused=False);assert path==p and new['status']=='Open';assert store.used_rows('Job','Blackvein')=={'1'}
        path,new=opp.generate('Job','Blackvein',ROOT/'jobs-and-rumors-tables',store,unused=False);assert path.stem=='J-BV-002' and path.parent.name=='added-jobs'
print('Travel boundaries, monotonic identifiers, search, template activation and repeat allocation passed.')
