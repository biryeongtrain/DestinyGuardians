#!/usr/bin/env python3
"""Build base Iron Reach from official socket data and user DDC; no gameplay/test invocation."""
import argparse, hashlib, html, json, re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
def load(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
inventory=Path('/tmp/destiny-weapons-w30/bungie-items.json')
plugsets=Path('/tmp/destiny-weapons-w60/bungie-plugsets.json')
ddc=Path('/private/tmp/destiny-w190/ddc-perks.html')
inv=load(inventory);pools=load(plugsets);base=591790007
catalog=load(a.root/'src/main/resources/destiny/weapons/w40-characteristics.json')
rolls=[];proof=[]
for weapon in catalog:
    item=inv[str(weapon['bungieHash'])]
    if item['inventory']['tierType']!=5 or weapon['exotic']:continue
    sockets=item['sockets']
    for index in {n for c in sockets['socketCategories'] if c['socketCategoryHash']==4241085061 for n in c['socketIndexes']}:
        entry=sockets['socketEntries'][index];pool=pools.get(str(entry.get('randomizedPlugSetHash')), {})
        if pool.get('isFakePlugSet') is not False:continue
        for plug in pool.get('reusablePlugItems',[]):
            if plug.get('plugItemHash')==base and plug.get('currentlyCanRoll') is True:
                roll={'id':weapon['id'],'hash':weapon['bungieHash'],'socket':index,'perkHash':base,'plugSetHash':entry['randomizedPlugSetHash']}
                rolls.append(roll);proof.append({'roll':roll,'traitCategory':4241085061,'socket':entry,'matchingPlug':plug})
assert [r['id'] for r in rolls]==['allied_demand']
row=next(x for x in re.findall(r'<tr\b[^>]*>.*?</tr>',ddc.read_text(),re.S) if 'Iron Reach' in x)
text=html.unescape(re.sub('<[^>]+>',' ',row))
assert '1662574278R128' in row and '+20 Range' in text and '-20' in text
stats=next(w for w in catalog if w['id']=='allied_demand')['stats']
b=next(w for w in load(a.root/'src/main/resources/destiny/weapons/w43-ballistics.json') if w['id']=='allied_demand')
resource={'stage':'W190','perk':{'id':'iron_reach','hash':base,'rangeBonus':20,'stabilityBonus':-20},'weapons':rolls,
          'range':{'base':stats['1240592695'],'offsetStart':b['offsetStart'],'vppStart':b['vppStart'],'offsetEnd':b['offsetEnd'],'vppEnd':b['vppEnd'],'floor':b['floor'],'precision':b['precision']}}
source={'date':'2026-10-27','perkDefinition':inv[str(base)],'officialManifest':load('/tmp/destiny-weapons-w60/manifest.json')['Response']['version'],
        'inputs':{str(x):sha(x) for x in (inventory,plugsets,ddc)},'socketProofs':proof,'ddc':{'url':'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278','row':129,'text':text,'html':row},
        'baseValuesVerifiedFromDDC':True,'enhancedExcluded':True,'rangeMapping':'Existing W43 historical curve; +20 range clamped0..100, meters→blocks; not new current-Destiny falloff measurement.'}
for name,obj in [('src/main/resources/destiny/weapons/w190-iron-reach.json',resource),('art/weapons/w190/iron-reach/source.json',source)]:
    dest=a.root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
print('Iron Reach: base +20Range/-20Stability; exact current official socket Allied Demand; DDC row129. No perk-specific tests.')
