#!/usr/bin/env python3
"""Read-only W80 official eligibility recomputation; no network or generated edits."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);args=a.parse_args()
 proof=json.loads((ROOT/'art/weapons/w80/references/official-eligibility.json').read_text())
 for pin in proof['sourcePins'].values():
  p=ROOT/pin['path'];assert sha(p)==pin['sha256'] and p.stat().st_size==pin['bytes'],p
 inventory=json.loads((ROOT/proof['sourcePins']['inventory']['path']).read_bytes())
 sets=json.loads((ROOT/proof['sourcePins']['plugSets']['path']).read_bytes())
 selected=json.loads((ROOT/proof['sourcePins']['selected']['path']).read_text())
 expected=set();socketCount=fieldCount=0
 for weapon in selected:
  row=inventory[str(weapon['bungieHash'])];sockets=row.get('sockets',{})
  traits={i for c in sockets.get('socketCategories',[]) if c['socketCategoryHash']==4241085061 for i in c['socketIndexes']}
  for i,socket in enumerate(sockets.get('socketEntries',[])):
   socketCount+=1
   for field in ('randomizedPlugSetHash','reusablePlugSetHash'):
    h=socket.get(field,0)
    if not h:continue
    fieldCount+=1;plugset=sets[str(h)]
    if any(p['plugItemHash']==3038247973 for p in plugset.get('reusablePlugItems',[])):
     assert i in traits and not plugset.get('isFakePlugSet',False)
     expected.add((weapon['id'],weapon['bungieHash'],i,3038247973,h))
 profile=json.loads((ROOT/'src/main/resources/destiny/weapons/w80-payload.json').read_text())
 actual={(r['id'],r['hash'],r['socket'],r['perkHash'],r['plugSetHash']) for r in profile['weapons']}
 assert expected==actual and len(expected)==5,(expected,actual)
 assert (len(selected),socketCount,fieldCount)==(63,678,627)
 p=profile['perk'];assert (p['convertedBodyFraction'],p['pveExplosionMultiplier'],p['radiusMeters'],p['radialFloor'])==(.5,1.3,3,.25)
 excerpt=ROOT/'art/weapons/w80/references/ddc-explosive-payload.json'
 assert p['mechanicsSource']['sha256']==sha(excerpt)
 d=json.loads(excerpt.read_text());assert p['mechanicsSource']['url']==d['sourceUrl']
 assert all(x in d['plainText'] for x in ('50%','30%','3 meters','(Base Ratio - 50%) / (1 - 50%)'))
 result=dict(stage='W80',selectedWeapons=len(selected),socketEntries=socketCount,referencedPlugSetFields=fieldCount,
  exactEligible=[list(x) for x in sorted(expected)],officialSourcePinsVerified=True,communityExcerptShaVerified=True,
  evidenceBoundary='Official pool eligibility plus retained community mechanics excerpt. Local radius mapping/attenuation/LOS/cap are not sourced original behavior. No native gameplay/render claim.')
 args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
