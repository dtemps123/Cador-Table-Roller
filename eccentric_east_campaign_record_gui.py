#!/usr/bin/env python3
"""Local editors for persistent adventure locations and Living Frontier plots.
No automated plot advancement or invented adventure locations.
"""
import argparse, json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from campaign_records import HERE, allocate, atomic_json, choose_record

SCHEMAS={
 'Location': ('location_id','adventure-location-records',('name','region','hex_coordinates','site_type','history','current_state','inhabitants','danger_level','points_of_interest','discovery','discoverability','related_plots','development_status','developments','related_records','record_status','source_reference')),
 'Plot': ('plot_id','faction-plot-records',('name','region','current_state','active_faction_objectives','possible_next_developments','adventure_intersections','developments','last_updated','status','related_records','source_reference','source_profile')),
}
REGIONS={'Blackvein':'BV','Thornhollow':'TH','Redvale':'RV','Westbridge':'WB','Qasari Lands':'QS','Eastern Highlands':'EH','Southern Deserts':'SD','Subterranean Realms':'ST','Wayward League':'WL'}
OPTIONS={'region':tuple(REGIONS),'discoverability':('Obvious','Concealed','Secret','Conditional'),'development_status':('Scaffolded','Partially prepared','Ready to run'),'status':('Draft — campaign not initialized','Active','Resolved','Dormant')}
SHORT={'name','region','hex_coordinates','site_type','danger_level','discoverability','development_status','last_updated','status','record_status','source_reference'}

class RecordEditor:
    def __init__(self,root,kind='Location',records_dir=None):
        self.root=root;self.kind=tk.StringVar(value=kind);self.override=Path(records_dir) if records_dir else None;self.path=None;self.extra={};self.baseline={};self.widgets={};self.current_kind=kind
        root.title('Eccentric East — Campaign Record Workshop');root.geometry('970x760');root.minsize(650,480)
        bar=ttk.Frame(root,padding=8);bar.pack(fill='x');ttk.Label(bar,text='Record type').pack(side='left');combo=ttk.Combobox(bar,textvariable=self.kind,values=list(SCHEMAS),state='readonly',width=14);combo.pack(side='left',padx=4);combo.bind('<<ComboboxSelected>>',self.change_kind)
        for label,cmd in [('New blank',self.new),('Search / load…',self.open),('Save',self.save),('Duplicate',self.duplicate)]:ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=4)
        self.header=tk.StringVar();ttk.Label(root,textvariable=self.header,padding=8,font=('TkDefaultFont',14,'bold')).pack(anchor='w')
        frame=ttk.Frame(root);frame.pack(fill='both',expand=True,padx=8);self.canvas=tk.Canvas(frame,highlightthickness=0);self.canvas.pack(side='left',fill='both',expand=True);sb=ttk.Scrollbar(frame,command=self.canvas.yview);sb.pack(side='right',fill='y');self.canvas.configure(yscrollcommand=sb.set);self.form=ttk.Frame(self.canvas);self.window=self.canvas.create_window((0,0),window=self.form,anchor='nw');self.form.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')));self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.window,width=e.width));self.status=tk.StringVar();ttk.Label(root,textvariable=self.status,padding=6,wraplength=900).pack(fill='x');root.protocol('WM_DELETE_WINDOW',self.close);self.display(None,{})
    def spec(self):return SCHEMAS[self.current_kind]
    def directory(self):return self.override or HERE/self.spec()[1]
    def display(self,path,data):
        self.path=Path(path) if path else None;self.extra=dict(data);self.widgets={};key,folder,fields=self.spec()
        for child in self.form.winfo_children():child.destroy()
        self.form.columnconfigure(1,weight=1)
        for i,k in enumerate(fields):
            ttk.Label(self.form,text=k.replace('_',' ').title(),wraplength=180).grid(row=i,column=0,sticky='nw',padx=8,pady=4)
            value=data.get(k,'');value=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
            if k in OPTIONS and not (self.current_kind=='Plot' and k=='region'):w=ttk.Combobox(self.form,values=OPTIONS[k]);w.set(value)
            elif k in SHORT:w=ttk.Entry(self.form);w.insert(0,value)
            else:w=tk.Text(self.form,height=5,wrap='word',undo=True);w.insert('1.0',value)
            w.grid(row=i,column=1,sticky='ew',padx=8,pady=4);self.widgets[k]=w
        self.baseline=self.collect();self.header.set(f'{data.get(key,"New unsaved record")} — {self.current_kind}');self.canvas.yview_moveto(0)
    def collect(self):
        d=dict(self.extra)
        for k,w in self.widgets.items():d[k]=w.get('1.0','end-1c') if isinstance(w,tk.Text) else w.get()
        return d
    def confirm(self):
        if self.collect()==self.baseline:return True
        ans=messagebox.askyesnocancel('Unsaved changes','Save this record before continuing?',parent=self.root);return False if ans is None else self.save() if ans else True
    def change_kind(self,event=None):
        new=self.kind.get();self.kind.set(self.current_kind)
        if self.confirm():self.current_kind=new;self.kind.set(new);self.display(None,{})
    def new(self):
        if self.confirm():self.display(None,{})
    def open(self):
        if not self.confirm():return
        key,_,fields=self.spec();p=choose_record(self.root,self.directory(),(key,*fields),key)
        if p:
            try:
                d=json.loads(Path(p).read_text(encoding='utf-8'))
                if key not in d:raise ValueError(f'Record must contain {key}.')
                self.display(p,d);self.status.set(f'Loaded {p.name}.')
            except Exception as exc:messagebox.showerror('Record workshop',str(exc),parent=self.root)
    def save(self,duplicate=False):
        try:
            d=self.collect();key,_,fields=self.spec()
            if not d['name'].strip():raise ValueError('Enter a name.')
            if self.path is None or duplicate:
                prefix='P' if self.current_kind=='Plot' else 'L-'+REGIONS[d['region']]
                p=allocate(self.directory(),self.directory(),prefix,key,d)
            else:p=self.path;atomic_json(p,d)
            self.display(p,d);self.status.set(f'Saved {p.name}.');return True
        except Exception as exc:messagebox.showerror('Record workshop',str(exc),parent=self.root);return False
    def duplicate(self):
        if messagebox.askyesno('Duplicate record','Create a separate record with a new ID?',parent=self.root):self.save(True)
    def close(self):
        if self.confirm():self.root.destroy()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--kind',choices=SCHEMAS,default='Location');parser.add_argument('--records-dir',type=Path);args=parser.parse_args();root=tk.Tk();RecordEditor(root,args.kind,args.records_dir);root.mainloop()
