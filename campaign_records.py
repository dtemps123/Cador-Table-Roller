"""Shared local record storage and searchable Tkinter record picker."""
import json, re, tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HERE = Path(__file__).resolve().parent

def atomic_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False, suffix='.tmp') as f:
            tmp = Path(f.name); json.dump(data, f, ensure_ascii=False, indent=4); f.write('\n')
        tmp.replace(path)
    finally:
        if tmp and tmp.exists(): tmp.unlink()

def records(root):
    for p in sorted(Path(root).rglob('*.json')):
        if p.name.startswith('.'): continue
        try:
            d = json.loads(p.read_text(encoding='utf-8'))
            if isinstance(d, dict): yield p, d
        except (OSError, ValueError): continue

def allocate(root, folder, prefix, key, data):
    """Reserve a new immutable ID, checking all subdirectories and a durable counter.
    Single-writer workflow: do not run concurrent writers against the same library.
    """
    root=Path(root); folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    cp=root/'.id-counters.json'; counters=json.loads(cp.read_text()) if cp.exists() else {}
    n=int(counters.get(prefix,0))
    for p,d in records(root):
        ident=d.get(key,p.stem)
        if isinstance(ident,str) and re.fullmatch(re.escape(prefix)+r'-\d+',ident): n=max(n,int(ident.rsplit('-',1)[1]))
    while True:
        n+=1; ident=f'{prefix}-{n:03d}'; p=folder/(ident+'.json'); data[key]=ident
        try:
            with p.open('x',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=4);f.write('\n')
            break
        except FileExistsError: continue
    counters[prefix]=n; atomic_json(cp,counters)
    return p

def matches(data, field, query):
    value=data if field=='All fields' else data.get(field,'')
    return all(term in json.dumps(value,ensure_ascii=False).casefold() for term in query.casefold().split())

def choose_record(parent, root, fields, id_key, name_key='name'):
    """Search field values, then select a file; arbitrary legacy JSON can also be opened."""
    dlg=tk.Toplevel(parent);dlg.title('Search campaign records');dlg.geometry('850x560');dlg.transient(parent);dlg.grab_set()
    rootvar=tk.StringVar(value=str(root)); query=tk.StringVar(); field=tk.StringVar(value='All fields'); result=[]; paths={}
    top=ttk.Frame(dlg,padding=8);top.pack(fill='x')
    ttk.Entry(top,textvariable=rootvar).pack(side='left',fill='x',expand=True)
    def browse():
        p=filedialog.askdirectory(parent=dlg,initialdir=rootvar.get());
        if p:rootvar.set(p);refresh()
    ttk.Button(top,text='Directory…',command=browse).pack(side='left')
    bar=ttk.Frame(dlg,padding=8);bar.pack(fill='x')
    ttk.Combobox(bar,textvariable=field,values=('All fields',*fields),state='readonly',width=25).pack(side='left')
    ttk.Entry(bar,textvariable=query).pack(side='left',fill='x',expand=True,padx=5)
    tree=ttk.Treeview(dlg,columns=('name','folder'),show='tree headings',selectmode='browse');tree.heading('#0',text='ID');tree.heading('name',text='Name / title');tree.heading('folder',text='Folder');tree.column('#0',width=100);tree.column('name',width=360);tree.column('folder',width=170);tree.pack(fill='both',expand=True,padx=8)
    status=tk.StringVar();ttk.Label(dlg,textvariable=status).pack(anchor='w',padx=8)
    def refresh(*_):
        tree.delete(*tree.get_children());paths.clear()
        for p,d in records(rootvar.get()):
            if not matches(d,field.get(),query.get()):continue
            node=tree.insert('','end',text=d.get(id_key,p.stem),values=(d.get(name_key) or d.get('faction') or p.stem,p.parent.name));paths[node]=p
        status.set(f'{len(paths)} matching records')
    def select(*_):
        if tree.selection():result.append(paths[tree.selection()[0]]);dlg.destroy()
    def open_file():
        p=filedialog.askopenfilename(parent=dlg,initialdir=rootvar.get(),filetypes=[('JSON','*.json')]);
        if p:result.append(Path(p));dlg.destroy()
    buttons=ttk.Frame(dlg,padding=8);buttons.pack(fill='x');ttk.Button(buttons,text='Load selected',command=select).pack(side='left');ttk.Button(buttons,text='Open other JSON…',command=open_file).pack(side='left',padx=5);ttk.Button(buttons,text='Cancel',command=dlg.destroy).pack(side='right')
    tree.bind('<Double-1>',select);query.trace_add('write',refresh);field.trace_add('write',refresh);refresh();parent.wait_window(dlg)
    return result[0] if result else None
