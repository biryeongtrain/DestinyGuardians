#!/usr/bin/env python3
"""Generate both official base Full Auto hashes and source provenance; no gameplay invocation."""
import argparse,hashlib,html,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
def read(p):return json.loads(Path(p).read_text())
invpath=Path('/tmp/destiny-weapons-w30/bungie-items.json');poolpath=Path('/tmp/destiny-weapons-w60/bungie-plugsets.json');ddcpath=Path('/private/tmp/destiny-w190/ddc-perks.html')
inv=read(invpath);pools=read(poolpath);catalog=read(a.root/'src/main/resources/destiny/weapons/w40-characteristics.json')
hashes={4267945040,2117683199};rolls=[];proof=[]
for w in catalog:
 if w['exotic']:continue
 item=inv[str(w['bungieHash'])];sockets=item['sockets']
 for i in sorted({n for c in sockets['socketCategories'] if c['socketCategoryHash']==4241085061 for n in c['socketIndexes']}):
  e=sockets['socketEntries'][i];pool=pools.get(str(e.get('randomizedPlugSetHash')), {})
  if pool.get('isFakePlugSet') is not False:continue
  for plug in pool.get('reusablePlugItems',[]):
   h=plug.get('plugItemHash')
   if h in hashes and plug.get('currentlyCanRoll') is True:
    r={'id':w['id'],'hash':w['bungieHash'],'socket':i,'perkHash':h,'plugSetHash':e['randomizedPlugSetHash']};rolls.append(r);proof.append({'roll':r,'socket':e,'matchingPlug':plug})
assert len(rolls)==10
row=next(r for r in re.findall(r'<tr\b[^>]*>.*?</tr>',ddcpath.read_text(),re.S) if any(html.unescape(re.sub('<[^>]+>','',c)).strip()=='Full Auto Trigger System' for c in re.findall(r'<td\b[^>]*>.*?</td>',r,re.S)))
txt=html.unescape(re.sub('<[^>]+>',' ',row));assert '0.9x Fire Recovery Delay' in txt and '+5 Stability' in txt
resource={'stage':'W191','perk':{'id':'full_auto_trigger_system','hashes':sorted(hashes),'shotgunRecoveryScalar':0.9,'legacyStabilityBonus':5,'legacyStabilityWeapons':['lonesome']},'weapons':rolls}
source={'date':'2026-10-27','manifestVersion':read('/tmp/destiny-weapons-w60/manifest.json')['Response']['version'],'perkDefinitions':{str(h):inv[str(h)] for h in sorted(hashes)},'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (invpath,poolpath,ddcpath)},'socketProofs':proof,'ddc':{'url':'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278','row':103,'text':txt,'html':row},'enhancedExcluded':True,'caveat':'DDC describes legacy +5 Stability informally (I guess); retained as provisional only on exact Lonesome. The Last Dance/Last Perdition are outside current catalog. Pinned manifest snapshot is not a refreshed whole manifest.'}
for name,obj in [('src/main/resources/destiny/weapons/w191-full-auto-trigger-system.json',resource),('art/weapons/w191/full-auto-trigger-system/source.json',source)]:
 dest=a.root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
print('Full Auto: 10 exact sockets, two base hashes; shotgun cadence scalar; legacy Lonesome Stability provisional per DDC.')
