#!/usr/bin/env python3
"""Extract base Well-Rounded sockets, user DDC, and historical handling curves."""
import argparse,json,hashlib,html,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
def read(p):return json.loads(Path(p).read_text())
invpath=Path('/tmp/destiny-weapons-w30/bungie-items.json');poolpath=Path('/tmp/destiny-weapons-w60/bungie-plugsets.json');ddcpath=Path('/private/tmp/destiny-w190/ddc-perks.html')
inv=read(invpath);pools=read(poolpath);cat=read(a.root/'src/main/resources/destiny/weapons/w40-characteristics.json');base=744594675
rolls=[];proof=[];curves=[];companions=[]
mapping={r['id']:r for r in read(a.root/'art/weapons/w43/extraction.json')['entries']};formulas=read(a.root/'art/weapons/w46/weapon_formulas.json')
providers={691659142:'pugilist',4071163871:'threat_detector',957782887:'snapshot',4082225868:'swashbuckler',591790007:'iron_reach',4104185692:'frenzy',11612903:'adrenaline_junkie'}
# Definition names resolve hashes; no assumption that an enhanced hash shares the base definition.
provider_names={'Pugilist':'pugilist','Threat Detector':'threat_detector','Snapshot Sights':'snapshot','Iron Reach':'iron_reach','Frenzy':'frenzy','Adrenaline Junkie':'adrenaline_junkie'}
providers={int(k):provider_names[d['displayProperties']['name']] for k,d in inv.items() if d.get('itemTypeDisplayName')=='Trait' and d.get('displayProperties',{}).get('name') in provider_names}
for w in cat:
 if w['exotic']:continue
 item=inv[str(w['bungieHash'])];s=item['sockets'];indices=sorted({i for c in s['socketCategories'] if c['socketCategoryHash']==4241085061 for i in c['socketIndexes']})
 matches=[]
 for i in indices:
  e=s['socketEntries'][i];pool=pools.get(str(e.get('randomizedPlugSetHash')), {})
  if pool.get('isFakePlugSet') is not False:continue
  plug=next((x for x in pool.get('reusablePlugItems',[]) if x.get('plugItemHash')==base and x.get('currentlyCanRoll') is True),None)
  if plug:
   r={'id':w['id'],'hash':w['bungieHash'],'socket':i,'perkHash':base,'plugSetHash':e['randomizedPlugSetHash']};rolls.append(r);matches.append(r);proof.append({'roll':r,'socket':e,'matchingPlug':plug})
 if not matches:continue
 m=mapping[w['id']];raw=formulas[m['family']]['cat'][m['category']]['handling'];c={'id':w['id'],'baseHandling':w['stats']['943549884']}
 for key in ('ready','stow','ads'):c[key]={k:raw[key].get(k,0.) for k in ('evpp','vpp','offset')}
 curves.append(c)
 for i in indices:
  if any(x['socket']==i for x in matches):continue
  e=s['socketEntries'][i];pool=pools.get(str(e.get('randomizedPlugSetHash')), {})
  if pool.get('isFakePlugSet') is not False:continue
  for plug in pool.get('reusablePlugItems',[]):
   h=plug.get('plugItemHash')
   if h in providers and plug.get('currentlyCanRoll') is True:companions.append({'id':w['id'],'perk':providers[h],'roll':{'id':w['id'],'hash':w['bungieHash'],'socket':i,'perkHash':h,'plugSetHash':e['randomizedPlugSetHash']}})
assert len(rolls)==5 and inv[str(base)]['itemTypeDisplayName']=='Trait'
row=next(r for r in re.findall(r'<tr\b[^>]*>.*?</tr>',ddcpath.read_text(),re.S) if any(html.unescape(re.sub('<[^>]+>','',c)).strip()=='Well-Rounded' for c in re.findall(r'<td\b[^>]*>.*?</td>',r,re.S)))
txt=html.unescape(re.sub('<[^>]+>',' ',row));assert '15 seconds' in txt and '+10' in txt and '+20' in txt
resource={'stage':'W192','perk':{'id':'well_rounded','hash':base,'durationTicks':300,'maximumStacks':2,'rangePerStack':10,'stabilityPerStack':10,'handlingPerStack':10},'weapons':rolls,'curves':curves,'coSelections':companions}
source={'date':'2026-10-27','manifestVersion':read('/tmp/destiny-weapons-w60/manifest.json')['Response']['version'],'definition':inv[str(base)],'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (invpath,poolpath,ddcpath)},'ddc':{'row':246,'url':'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278','html':row,'text':txt},'socketProofs':proof,'handlingCurves':curves,'coSelections':companions,'enhancedExcluded':True,'localMapping':'Grenade/Super only after accepted AbilityService use. Powered direct melee requires positive actual HP loss; one target per captured contact, no DoT/grenade/melee-input-only credits. Metres to blocks; raw historical handling curves are existing product approximation.'}
for rel,d in [('src/main/resources/destiny/weapons/w192-well-rounded.json',resource),('art/weapons/w192/well-rounded/source.json',source)]:
 dest=a.root/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
print('Well-Rounded:5 exact base sockets, DDC row246, raw historical handling and companion proofs')
