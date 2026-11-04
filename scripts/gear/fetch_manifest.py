#!/usr/bin/env python3
"""Fetch the current Bungie manifest, audit every non-exotic catalog weapon's trait pools against the
implemented perk hashes, and download weapon/trait/engram icons. Output goes to a cache dir (default
/tmp/dg-loot); feed it to scripts/gear/import_bungie_icons.py. Read-only for the repository."""
import json, sys, os, urllib.request
CACHE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/dg-loot"
os.makedirs(CACHE, exist_ok=True); os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../..")
def fetch(url, path):
    if not os.path.exists(path): open(path, "wb").write(urllib.request.urlopen(url, timeout=120).read())
fetch("https://www.bungie.net/Platform/Destiny2/Manifest/", f"{CACHE}/manifest.json")
paths = json.load(open(f"{CACHE}/manifest.json"))["Response"]["jsonWorldComponentContentPaths"]["en"]
fetch("https://www.bungie.net" + paths["DestinyInventoryItemDefinition"], f"{CACHE}/items.json")
fetch("https://www.bungie.net" + paths["DestinyPlugSetDefinition"], f"{CACHE}/plugsets.json")

import re,collections,glob,concurrent.futures as cf
items=json.load(open(CACHE+'/items.json')); ps=json.load(open(CACHE+'/plugsets.json'))
ch=json.load(open('src/main/resources/destiny/weapons/w40-characteristics.json'))
src=open('src/main/java/kim/biryeong/destiny/weapon/WeaponPerks.java').read()
# implemented perk hashes: collect from rolls json files perkHash
import glob
impl=set()
for f in glob.glob('src/main/resources/destiny/weapons/*.json'):
    for m in re.finditer(r'"perkHash"\s*:\s*(\d+)',open(f).read()): impl.add(int(m.group(1)))
def traitplugs(h):
    it=items[str(h)]; out={}
    for i,s in enumerate(it.get('sockets',{}).get('socketEntries',[])):
        p=s.get('randomizedPlugSetHash') or s.get('reusablePlugSetHash')
        if not p: continue
        for pi in ps[str(p)]['reusablePlugItems']:
            d=items.get(str(pi['plugItemHash']))
            if not d or d.get('itemTypeDisplayName')!='Trait' or not pi.get('currentlyCanRoll',True): continue
            out.setdefault(i,{})[pi['plugItemHash']]=d['displayProperties']['name']
    return out
missing=collections.Counter(); per={}
names={}
for w in ch:
    if w['exotic']: continue
    tp=traitplugs(w['bungieHash'])
    per[w['id']]={s:{h:n for h,n in v.items()} for s,v in tp.items()}
    for s,v in tp.items():
        for h,n in v.items():
            names[h]=n
            if h not in impl: missing[(h,n)]+=1
json.dump({k:{str(s):{str(h):n for h,n in v.items()} for s,v in d.items()} for k,d in per.items()},open(CACHE+'/pools.json','w'),indent=1)
print('weapons',len(per),'distinct traits',len(names),'implemented',len([h for h in names if h in impl]),'missing',len(missing))
for (h,n),c in missing.most_common(): print(c,n,h)

ch=json.load(open('src/main/resources/destiny/weapons/w40-characteristics.json'))
pools=json.load(open(CACHE+'/pools.json'))
out=CACHE+'/icons'; os.makedirs(out,exist_ok=True)
jobs={}
for w in ch:
    d=items[str(w['bungieHash'])]['displayProperties']
    jobs['weapon_'+w['id']]=d.get('icon')
    wm=items[str(w['bungieHash'])].get('iconWatermark')
for v in pools.values():
    for s in v.values():
        for h in s: jobs['perk_'+h]=items[h]['displayProperties'].get('icon')
# engrams
for k,d in items.items():
    n=d.get('displayProperties',{}).get('name','')
    if n in ('Legendary Engram','Exotic Engram','Rare Engram','Prime Engram') and d.get('displayProperties',{}).get('icon') and 'eng_'+n not in jobs:
        jobs['engram_'+n.split()[0].lower()]=d['displayProperties']['icon']
jobs={k:v for k,v in jobs.items() if v}
def get(kv):
    k,v=kv; p=f'{out}/{k}.png'
    if not os.path.exists(p): open(p,'wb').write(urllib.request.urlopen('https://www.bungie.net'+v,timeout=30).read())
    return k
with cf.ThreadPoolExecutor(8) as ex: list(ex.map(get,jobs.items()))
json.dump(jobs,open(out+'/index.json','w'),indent=1)
print(len(jobs),[k for k in jobs if k.startswith('engram')])
