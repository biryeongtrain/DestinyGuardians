#!/usr/bin/env python3
"""Pin base Mulligan's real trait sockets and the user DDC row16."""
import argparse,json,re,html,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
invpath=Path('/tmp/destiny-weapons-w30/bungie-items.json');poolpath=Path('/tmp/destiny-weapons-w60/bungie-plugsets.json');ddcpath=Path('/private/tmp/destiny-w190/ddc-perks.html')
read=lambda p:json.loads(p.read_text());inv=read(invpath);pools=read(poolpath);cat=read(a.root/'src/main/resources/destiny/weapons/w40-characteristics.json');base=3513791699
assert inv[str(base)]['displayProperties']['name']=='Mulligan' and inv[str(base)]['itemTypeDisplayName']=='Trait'
assert hashlib.sha256(ddcpath.read_bytes()).hexdigest()=='8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437'
rolls=[];proof=[]
for w in cat:
 if w['exotic']:continue
 item=inv[str(w['bungieHash'])];s=item['sockets'];indices=sorted({i for c in s['socketCategories'] if c['socketCategoryHash']==4241085061 for i in c['socketIndexes']})
 for i in indices:
  e=s['socketEntries'][i];pool=pools.get(str(e.get('randomizedPlugSetHash')), {})
  if pool.get('isFakePlugSet') is not False:continue
  matches=[x for x in pool.get('reusablePlugItems',[]) if x.get('plugItemHash')==base and x.get('currentlyCanRoll') is True]
  if matches:
   assert len(matches)==1
   r={'id':w['id'],'hash':w['bungieHash'],'socket':i,'perkHash':base,'plugSetHash':e['randomizedPlugSetHash']};rolls.append(r);proof.append({'roll':r,'socketEntry':e,'matchingPlug':matches[0]})
assert len(rolls)==2
plain=lambda x:html.unescape(re.sub('<[^>]*>',' ',x)).strip()
rows=[r for r in re.findall(r'<tr\b[^>]*>.*?</tr>',ddcpath.read_text(),re.S) if any(plain(c)=='Mulligan' for c in re.findall(r'<td\b[^>]*>.*?</td>',r,re.S))]
assert len(rows)==1;row=rows[0];text=plain(row);assert '35%' in text and '20%' in text and 'Miss' in text
resource={'stage':'W194','perk':{'id':'mulligan','hash':base,'primaryChancePercent':35,'otherChancePercent':20,'generatedRounds':1},'weapons':rolls}
source={'date':'2026-10-27','manifestVersion':read(Path('/tmp/destiny-weapons-w60/manifest.json'))['Response']['version'],'definition':inv[str(base)],'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [invpath,poolpath,ddcpath]},'ddc':{'row':150,'url':'https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278','html':row,'text':text},'socketProofs':proof,'enhancedExcluded':True,'mapping':'Only actually paid supported hitscan emissions with no eligible living-entity geometry contact may roll once after all pellets. A wall contact counts as a miss; an eligible entity contact counts as a hit even when damage is rejected. Actual generated loaded reward is capped at base magazine capacity, not a reload or reserve transfer. Uniform integer percentile RNG is local sampling policy. Source owner/stack/roll validity is checked before grant; duplicate tokens are consumed without reroll.'}
for rel,d in [('src/main/resources/destiny/weapons/w194-mulligan.json',resource),('art/weapons/w194/mulligan/source.json',source)]:
 dest=a.root/rel;out=json.dumps(d,indent=2,ensure_ascii=False)+'\n'
 if a.verify:assert dest.read_text()==out,rel
 else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(out)
print('Mulligan: 2 exact base sockets, DDC row150; '+('verified' if a.verify else 'written'))
