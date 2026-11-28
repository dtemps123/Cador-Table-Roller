#!/usr/bin/env python3
"""Job Board & Rumor Mill workshop for Eccentric East (2014 5e).
Requires Tkinter and the user's installed TableRoller / DiceRollBackend.
"""
import sys
import argparse
import json
import os
import re
import tempfile
from datetime import date as real_date
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.append("/Users/dtemples/DnD/Tools/DnD-Table-Roller")
from TableRoller import roll_on_table
from campaign_records import allocate, matches

HERE = Path(__file__).resolve().parent
REGIONS = {'Blackvein':'BV','Thornhollow':'TH','Redvale':'RV','Westbridge':'WB','Wayward League':'WL'}
PREFIX = {'Job':'J','Rumor':'R'}
JOB_STATUS = ('Unposted template','Open','Claimed','In Progress','Completed','Resolved by Others','Expired','Withdrawn','Superseded')
RUMOR_STATUS = ('Unposted template','Uninvestigated','Partially Investigated','Confirmed','Disproven','Outdated','Resolved')
RELIABILITY = ('Undetermined','Accurate','Incomplete','Distorted','False','Fabricated')
# field, label, multiline/choices; statuses of rumors may be combined manually.
JOB_FIELDS = [
 ('title','Title',False),('date_posted','Date posted (in-game)',False),('date_posted_real','Date posted (real-world)',False),('job_board','Job board / posting location',False),
 ('employer','Employer',False),('posting','Public posting',True),('objective','Objective / hidden details',True),
 ('location','Adventure location',False),('reward','Reward',False),('npcs','Potential NPCs',True),('factions','Factions',True),
 ('related_plots','Related plot IDs',True),('related_locations','Related location IDs',True),
 ('expiration_conditions','Expiration conditions',True),('status','Status',JOB_STATUS),
 ('developments','Developments',True),('date_retired','Date retired (in-game)',False),('date_retired_real','Date retired (real-world)',False),('outcome_and_consequences','Outcome and consequences',True)]
RUMOR_FIELDS = [
 ('title','Title',False),('date_introduced','Date introduced (in-game)',False),('date_introduced_real','Date introduced (real-world)',False),('rumor','Original rumor',True),
 ('first_lead','First lead (DM reference)',True),('place_of_circulation','Place of circulation',False),
 ('source','Source / informant',False),('dissemination','Dissemination / recipients',True),
 ('reliability','Reliability',RELIABILITY),('underlying_truth','Underlying truth',True),('factions','Factions',True),('npcs','NPCs',True),
 ('related_plots','Related plot IDs',True),('related_locations','Related location IDs',True),('status','Status (may combine)',RUMOR_STATUS),
 ('developments','Developments / subsequent reports',True),('related_rumors_and_jobs','Related rumor / job IDs',True),('archived','Archived? (Yes / No)',('No','Yes'))]
FIELDS={'Job':JOB_FIELDS,'Rumor':RUMOR_FIELDS}
COUNT_TABLES={('Job','Initial'):'initial-job-count',('Rumor','Initial'):'initial-rumor-count',('Job','Monthly'):'monthly-job-add-count',('Rumor','Monthly'):'monthly-rumor-add-count'}

def roll(table, directory):
    from TableRoller import roll_on_table
    return roll_on_table(table,tables_dir=str(directory),verbose=False)

def table_name(kind, region):
    return ('job-board-' if kind=='Job' else 'rumor-mill-')+region.lower().replace(' ','-')

def id_key(kind):return 'job_id' if kind=='Job' else 'rumor_id'

def blank_record(kind,region,date=''):
    r={id_key(kind):'', 'record_type':kind.lower(),'region':region,'source_table':'','source_row':'','source_page':''}
    r.update({k:'' for k,_,_ in FIELDS[kind]})
    if kind=='Job':r.update(status='Open',date_posted=date,date_posted_real=real_date.today().isoformat(),job_board=region)
    else:r.update(status='Uninvestigated',reliability='Undetermined',date_introduced=date,date_introduced_real=real_date.today().isoformat(),place_of_circulation=region,archived='No')
    return r

def parse_row(raw,kind,region,date=''):
    while isinstance(raw,dict) and len(raw)==1:raw=next(iter(raw.values()))
    if not isinstance(raw,str):raise ValueError('Expected a labeled text result from a regional table.')
    labels=dict(line.split(': ',1) for line in raw.splitlines() if ': ' in line)
    r=blank_record(kind,region,date)
    r.update(title=labels['Title'],source_table=table_name(kind,region),source_row=labels['Source row'],source_page=labels['Source page'])
    if kind=='Job':
        npcs,sep,factions=labels['NPCs and factions involved'].partition(';')
        r.update(posting=labels['Posting'],job_board=labels['Posted at'],npcs=npcs.strip(),factions=factions.strip())
        if region=='Wayward League':r['employer']=npcs.strip()
    else:r.update(rumor=labels['Rumor'],first_lead=labels['First lead'])
    return r

def read_record(path):
    r=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(r,dict):raise ValueError('Record must be a JSON object.')
    kind={'job':'Job','rumor':'Rumor'}.get(r.get('record_type'))
    if not kind:
        if 'job_id' in r and 'rumor_id' not in r:kind='Job'
        elif 'rumor_id' in r and 'job_id' not in r:kind='Rumor'
        else:raise ValueError('Record needs a job_id or rumor_id.')
    region=r.get('region')
    if region not in REGIONS:raise ValueError('Record must identify a supported region.')
    d=blank_record(kind,region);d.update(r);d['record_type']=kind.lower()
    for k in ('date_posted_real','date_introduced_real'):
        if k in d and k not in r:d[k]=''
    ident=d[id_key(kind)]
    if not isinstance(ident,str) or not re.fullmatch(rf'{PREFIX[kind]}-(?:BV|TH|RV|WB|WL)-\d+',ident):raise ValueError('Invalid record ID.')
    for k,_,_ in FIELDS[kind]:
        if d[k] is None:d[k]=''
        elif not isinstance(d[k],str):raise ValueError(f'Expected text in {k}.')
    return d

def atomic_json(path,record):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.record-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=4);f.write('\n')
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

class Store:
    """One campaign directory, individual logs, durable monotonic counters."""
    def __init__(self,path):self.path=Path(path).expanduser().resolve();self.path.mkdir(parents=True,exist_ok=True)
    def records(self):
        good=[];bad=[]
        for p in sorted(self.path.rglob('*.json')):
            if p.name.startswith('.'):continue
            try:good.append((p,read_record(p)))
            except Exception as exc:bad.append((p,str(exc)))
        return good,bad
    def used_rows(self,kind,region):
        return {str(r.get('source_row')) for _,r in self.records()[0] if r.get('source_table')==table_name(kind,region) and r.get('status')!='Unposted template'}
    def create(self,r):
        kind=r['record_type'].title();key=id_key(kind);prefix=f'{PREFIX[kind]}-{REGIONS[r["region"]]}'
        # An authored template is a reserved, unposted record. Activate it in place
        # on its first use, preserving any DM edits. Repeated postings get new IDs.
        if r.get('source_table'):
            for path,old in self.records()[0]:
                if old.get('status')=='Unposted template' and old.get('source_table')==r.get('source_table') and old.get('source_row')==r.get('source_row'):
                    old['status']=r['status']
                    for k in ('date_posted','date_posted_real','date_introduced','date_introduced_real'):
                        if k in r:old[k]=r[k]
                    r.clear();r.update(old);atomic_json(path,r);return path
        sub='added-'+('jobs' if kind=='Job' else 'rumors')
        return allocate(self.path,self.path/sub,prefix,key,r)

def generate(kind,region,directory,store,date='',unused=True):
    name=table_name(kind,region)
    if region=='Wayward League' and kind=='Rumor':raise ValueError('Guildhall rumors are entered manually; no regional rumor table is prescribed.')
    if unused:
        # Uniformly sample unused entries using the existing backend, not a second RNG.
        from TableRoller import make_table_roll
        t=json.loads((Path(directory)/(name+'.json')).read_text(encoding='utf-8'))
        used=store.used_rows(kind,region)
        remaining=[v for k,v in t['results'].items() if k not in used]
        if not remaining:raise ValueError(f'No unused {kind.lower()} entries remain for {region}. Add new table entries or allow repeats.')
        raw=make_table_roll({'table':name+' (unused)','dice':f'1d{len(remaining)}','results':{str(i):v for i,v in enumerate(remaining,1)}},tables_dir=str(directory),verbose=False)
    else:raw=roll(name,directory)
    r=parse_row(raw,kind,region,date);p=store.create(r);return p,r

class Workshop:
    def __init__(self,root,tables,logs):
        self.root=root;root.title('Eccentric East — Job Boards & Rumor Mills');root.geometry('1200x790');root.minsize(850,540)
        self.tables=tk.StringVar(value=str(tables));self.logs=tk.StringVar(value=str(logs));self.kind=tk.StringVar(value='Job');self.region=tk.StringVar(value='Blackvein');self.date=tk.StringVar();self.unused=tk.BooleanVar(value=True);self.filter=tk.StringVar();self.filter_field=tk.StringVar(value='All fields');self.filter_state=tk.StringVar(value='All');self.filter_kind=tk.StringVar(value='All');self.filter_region=tk.StringVar(value='All');self.message=tk.StringVar(value='Ready.');self.record=None;self.path=None;self.widgets={};self.list_paths={};self.baseline=None
        top=ttk.Frame(root,padding=8);top.pack(fill='x')
        for i,(label,var) in enumerate([('Tables',self.tables),('Campaign logs',self.logs)]):
            ttk.Label(top,text=label).grid(row=i,column=0,sticky='w');ttk.Entry(top,textvariable=var).grid(row=i,column=1,sticky='ew',padx=5,pady=2);ttk.Button(top,text='Browse…',command=lambda v=var:self.browse(v)).grid(row=i,column=2)
        top.columnconfigure(1,weight=1)
        bar=ttk.Frame(root,padding=(8,0,8,5));bar.pack(fill='x')
        for label,var,values in [('Type',self.kind,('Job','Rumor')),('Region',self.region,tuple(REGIONS))]:
            ttk.Label(bar,text=label).pack(side='left',padx=(0,4));ttk.Combobox(bar,textvariable=var,values=values,state='readonly',width=15).pack(side='left',padx=(0,9))
        ttk.Label(bar,text='In-game date').pack(side='left');ttk.Entry(bar,textvariable=self.date,width=17).pack(side='left',padx=5)
        ttk.Checkbutton(bar,text='Unused entries only',variable=self.unused).pack(side='left',padx=5)
        actions=ttk.Frame(root,padding=(8,0,8,7));actions.pack(fill='x')
        for i,(label,fn) in enumerate([('Roll & create log',self.roll_one),('New blank',self.new_blank),('Initial batch',lambda:self.batch('Initial')),('Monthly additions',lambda:self.batch('Monthly')),('Retirement count',self.retirement),('Open JSON…',self.open_file),('Save',self.save),('Copy public text',self.copy_public),('Roll reference table…',self.reference_roll),('Activate template',self.activate_template)]):ttk.Button(actions,text=label,command=fn).grid(row=i//4,column=i%4,sticky='ew',padx=(0,4),pady=2)
        for i in range(4):actions.columnconfigure(i,weight=1)
        pane=ttk.Panedwindow(root,orient='horizontal');pane.pack(fill='both',expand=True,padx=8,pady=4)
        left=ttk.Frame(pane,padding=4);right=ttk.Frame(pane,padding=4);pane.add(left,weight=1);pane.add(right,weight=2)
        ttk.Label(left,text='Campaign log library',font=('TkDefaultFont',12,'bold')).pack(anchor='w')
        filters=ttk.Frame(left);filters.pack(fill='x',pady=4)
        for var,vals in [(self.filter_kind,('All','Job','Rumor')),(self.filter_region,('All',*REGIONS))]:ttk.Combobox(filters,textvariable=var,values=vals,state='readonly',width=11).pack(side='left',padx=2)
        ttk.Button(filters,text='Refresh',command=self.refresh).pack(side='right')
        ttk.Combobox(left,textvariable=self.filter_state,values=('All','Unposted templates','Activated records'),state='readonly').pack(fill='x',pady=2)
        ttk.Combobox(left,textvariable=self.filter_field,values=('All fields','job_id','rumor_id','region',*sorted({k for rows in FIELDS.values() for k,_,_ in rows})),state='readonly').pack(fill='x')
        ttk.Entry(left,textvariable=self.filter).pack(fill='x',pady=(0,4))
        tree_frame=ttk.Frame(left);tree_frame.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(tree_frame,columns=('title','status'),show='tree headings',selectmode='browse');self.tree.heading('#0',text='ID');self.tree.heading('title',text='Title');self.tree.heading('status',text='Status');self.tree.column('#0',width=100,minwidth=85);self.tree.column('title',width=220,minwidth=100);self.tree.column('status',width=105,minwidth=85);self.tree.pack(side='left',fill='both',expand=True)
        sy=ttk.Scrollbar(tree_frame,orient='vertical',command=self.tree.yview);sy.pack(side='right',fill='y');self.tree.configure(yscrollcommand=sy.set);self.tree.bind('<Double-1>',lambda e:self.open_selected());ttk.Button(left,text='Load selected record',command=self.open_selected).pack(fill='x',pady=4)
        for v in (self.filter,self.filter_kind,self.filter_region,self.filter_field,self.filter_state):v.trace_add('write',lambda *_:self.refresh())
        self.heading=ttk.Label(right,text='No record loaded',font=('TkDefaultFont',13,'bold'));self.heading.pack(anchor='w')
        self.provenance=ttk.Label(right,text='',wraplength=600);self.provenance.pack(anchor='w',pady=(0,5))
        self.canvas=tk.Canvas(right,highlightthickness=0);sb=ttk.Scrollbar(right,orient='vertical',command=self.canvas.yview);sb.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True);self.canvas.configure(yscrollcommand=sb.set)
        self.form=ttk.Frame(self.canvas);self.form_id=self.canvas.create_window((0,0),window=self.form,anchor='nw');self.form.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')));self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.form_id,width=e.width));root.bind_all('<MouseWheel>',self.wheel,add='+');root.bind_all('<Button-4>',self.wheel,add='+');root.bind_all('<Button-5>',self.wheel,add='+')
        ttk.Label(root,textvariable=self.message,relief='sunken',anchor='w',padding=5).pack(fill='x',side='bottom');root.protocol('WM_DELETE_WINDOW',self.close);root.bind('<Control-s>',lambda e:self.save());root.bind('<Command-s>',lambda e:self.save())
        self.refresh()
    def wheel(self,event):
        if str(event.widget).startswith(str(self.form)) and not isinstance(event.widget,tk.Text):
            delta=getattr(event,'delta',0); num=getattr(event,'num',0)
            step=-1 if num==4 or delta>0 else 1
            self.canvas.yview_scroll(step,'units')
            return 'break'
    def store(self):return Store(self.logs.get())
    def guarded(self,fn):
        try:return fn()
        except Exception as e:messagebox.showerror('Workshop',str(e),parent=self.root);self.message.set(str(e));return None
    def browse(self,var):
        p=filedialog.askdirectory(initialdir=var.get(),parent=self.root)
        if p:
            if var is self.logs and not self.confirm():return
            var.set(p)
            if var is self.logs:self.display(None,None);self.refresh()
    def refresh(self):
        try:rows,bad=self.store().records()
        except Exception as e:self.message.set(str(e));return
        self.tree.delete(*self.tree.get_children());self.list_paths={};q=self.filter.get().casefold()
        for p,r in rows:
            kind=r['record_type'].title();ident=r[id_key(kind)]
            if self.filter_kind.get() not in ('All',kind) or self.filter_region.get() not in ('All',r['region']):continue
            if self.filter_state.get()=='Unposted templates' and r['status']!='Unposted template':continue
            if self.filter_state.get()=='Activated records' and r['status']=='Unposted template':continue
            if q and not matches(r,self.filter_field.get(),q):continue
            node=self.tree.insert('', 'end',text=ident,values=(r['title'],r['status']));self.list_paths[node]=p
        if bad:self.message.set(f'{len(bad)} unreadable JSON file(s) skipped: {bad[0][0].name}: {bad[0][1]}')
    def collect(self):
        if self.record is None:return None
        r=dict(self.record)
        for k,w in self.widgets.items():r[k]=w.get('1.0','end-1c') if isinstance(w,tk.Text) else w.get()
        return r
    def confirm(self):
        if self.record is None or self.collect()==self.baseline:return True
        ans=messagebox.askyesnocancel('Unsaved edits','Save changes to this record first?',parent=self.root)
        return False if ans is None else (bool(self.save()) if ans else True)
    def display(self,path,r):
        for child in self.form.winfo_children():child.destroy()
        self.path=Path(path) if path else None;self.record=dict(r) if r else None;self.baseline=dict(r) if r else None;self.widgets={};self.canvas.yview_moveto(0)
        if not r:self.heading.configure(text='No record loaded');self.provenance.configure(text='');return
        kind=r['record_type'].title();self.kind.set(kind);self.region.set(r['region']);self.heading.configure(text=f'{r[id_key(kind)] or "New unsaved record"} — {kind} / {r["region"]}')
        self.provenance.configure(text=(f'Source: {r.get("source_table")} · row {r.get("source_row")} · Handbook p. {r.get("source_page")}' if r.get('source_table') else 'Manually created record'))
        self.form.columnconfigure(1,weight=1)
        for i,(k,label,mode) in enumerate(FIELDS[kind]):
            ttk.Label(self.form,text=label,wraplength=170).grid(row=i,column=0,sticky='nw',padx=(3,8),pady=4)
            if mode is True:w=tk.Text(self.form,height=4,wrap='word',undo=True,font=('TkDefaultFont',10));w.insert('1.0',r[k])
            elif isinstance(mode,tuple):w=ttk.Combobox(self.form,values=mode);w.set(r[k])
            else:w=ttk.Entry(self.form);w.insert(0,r[k])
            w.grid(row=i,column=1,sticky='ew',pady=4,padx=(0,5));self.widgets[k]=w
        self.message.set(f'Loaded {r[id_key(kind)] or "blank draft"}.')
    def save(self):
        def run():
            r=self.collect()
            if r is None:return False
            if not r['title'].strip():raise ValueError('Enter a title before saving.')
            if self.path is None:self.path=self.store().create(r)
            else:atomic_json(self.path,r)
            self.record=dict(r);self.baseline=dict(r);self.heading.configure(text=f'{r[id_key(r["record_type"].title())]} — {r["record_type"].title()} / {r["region"]}');self.refresh();self.message.set(f'Saved {self.path.name}');return True
        return self.guarded(run)
    def new_blank(self):
        if self.confirm():self.display(None,blank_record(self.kind.get(),self.region.get(),self.date.get()))
    def roll_one(self):
        if not self.confirm():return
        def run():
            p,r=generate(self.kind.get(),self.region.get(),self.tables.get(),self.store(),self.date.get(),self.unused.get());self.display(p,r);self.refresh();self.message.set(f'Created {p.name}. Edit details and save.')
        self.guarded(run)
    def batch(self,phase):
        if not self.confirm():return
        def run():
            kind,region=self.kind.get(),self.region.get();
            if region=='Wayward League':raise ValueError('Guildhall notices are issued as needed, not on the regional batch cadence.')
            n=int(roll(COUNT_TABLES[kind,phase],self.tables.get()));store=self.store()
            if not messagebox.askyesno(f'{phase} batch',f'{n} {kind.lower()} log(s) rolled for {region}. Create them now?',parent=self.root):return
            created=[];failure=''
            for _ in range(n):
                try:created.append(generate(kind,region,self.tables.get(),store,self.date.get(),self.unused.get()))
                except Exception as e:failure=str(e);break
            if created:self.display(*created[-1])
            self.refresh();self.message.set(f'Created {len(created)} of {n} logs. '+failure)
            if failure:messagebox.showwarning('Batch stopped',f'Created {len(created)} of {n}. {failure}',parent=self.root)
        self.guarded(run)
    def retirement(self):
        def run():
            if self.region.get()=='Wayward League':raise ValueError('Guildhall notices have no random retirement cadence.')
            n=int(roll('monthly-job-retire-count',self.tables.get()));rows=self.store().records()[0];eligible=[r for _,r in rows if r['record_type']=='job' and r['region']==self.region.get() and r['status']=='Open'];messagebox.showinfo('Monthly retirement',f'{self.region.get()}: rolled {n}. {len(eligible)} open jobs in the library. Retire up to {min(n,len(eligible))} appropriate jobs manually; record outcomes and plot consequences. No logs were changed.',parent=self.root)
        self.guarded(run)
    def open_selected(self):
        ids=self.tree.selection()
        if not ids:return
        path=self.list_paths[ids[0]]
        if self.confirm():self.guarded(lambda:self.display(path,read_record(path)))
    def open_file(self):
        if not self.confirm():return
        p=filedialog.askopenfilename(initialdir=self.logs.get(),filetypes=[('JSON','*.json')],parent=self.root)
        if p:self.guarded(lambda:self.display(p,read_record(p)))
    def copy_public(self):
        r=self.collect()
        if not r:return
        if r.get('status')=='Unposted template':
            messagebox.showinfo('Unposted template','Activate this record before copying player-facing text.',parent=self.root);return
        kind=r['record_type'].title();text=f'{r[id_key(kind)]} — {r["title"]}\n'+(f'{r["posting"]}\nPosted at: {r["job_board"]}\nReward: {r["reward"]}\nStatus: {r["status"]}' if kind=='Job' else r['rumor']);self.root.clipboard_clear();self.root.clipboard_append(text);self.message.set('Copied player-facing text (no hidden fields). Review before sharing.')
    def activate_template(self):
        def run():
            r=self.collect()
            if not r or r.get('status')!='Unposted template':raise ValueError('Load an unposted template first.')
            kind=r['record_type'].title();r['status']='Open' if kind=='Job' else 'Uninvestigated'
            k='date_posted' if kind=='Job' else 'date_introduced';r[k]=r[k] or self.date.get();r[k+'_real']=real_date.today().isoformat()
            atomic_json(self.path,r);self.display(self.path,r);self.refresh();self.message.set('Template activated locally; share it with players when appropriate.')
        self.guarded(run)
    def reference_roll(self):
        dlg=tk.Toplevel(self.root);dlg.title('Independent table roller');dlg.geometry('800x480');names=sorted(p.stem for p in Path(self.tables.get()).glob('*.json'));choice=tk.StringVar(value='wayward-league-introductory-scenarios');ttk.Combobox(dlg,textvariable=choice,values=names,state='readonly').pack(fill='x',padx=8,pady=8);out=tk.Text(dlg,wrap='word');out.pack(fill='both',expand=True,padx=8,pady=5)
        def run():
            try:
                value=roll(choice.get(),self.tables.get());out.delete('1.0','end');out.insert('1.0',value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2))
            except Exception as exc:messagebox.showerror('Table roller',str(exc),parent=dlg)
        ttk.Button(dlg,text='Roll (does not create records)',command=run).pack(pady=5)
    def close(self):
        if self.confirm():self.root.destroy()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tables-dir',type=Path,default=HERE/'jobs-and-rumors-tables');p.add_argument('--logs-dir',type=Path,default=HERE/'job-and-rumor-records');a=p.parse_args();root=tk.Tk();Workshop(root,a.tables_dir,a.logs_dir);root.mainloop()
if __name__=='__main__':main()
