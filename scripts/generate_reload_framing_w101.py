#!/usr/bin/env python3
"""W101 active reload framing. Keeps W100 geometry and every original idle context.

Authored view composition, not recovered animation. Native PNG acceptance is external.
"""
import argparse,copy,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'src/main/resources/assets/destiny'
ART=ROOT/'art/weapons/w101'
KEY='weapon_reload_w101/the_recluse'
KEYS=[
 (0,[0,0,0],[0,0,0],[0,0,0]),
 (.12,[4,-10,-14],[-2,4,-1],[0,0,0]),
 (.24,[8,-20,-28],[-4.5,8,-2],[.3,-1.5,0]),
 (.40,[8,-22,-32],[-4.5,8,-2],[.5,-4.2,.3]),
 (.52,[7,-20,-30],[-4.5,8,-2],[.5,-4.2,.3]),
 (.68,[6,-18,-28],[-4.5,8,-2],[.2,-1.8,.1]),
 (.78,[8,-16,-26],[-4.2,7.5,-1.8],[0,0,0]),
 (.86,[5,-10,-16],[-2.5,4.5,-1],[0,0,0]),
 (1,[0,0,0],[0,0,0],[0,0,0]),
]
PINS={
 'scripts/generate_reload_models_w100.py':'aef69a0be0a2b4f84c87ff33ce4ca56faf637dcb24b34806293b34b4ea21e97c',
 'art/weapons/w100/manifest.json':'f4ddf971ef78211072931a73448e6ec3fd3f2431075d07743685dbaa62b19713',
}
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def generate():
 for p,h in PINS.items():assert sha((ROOT/p).read_bytes())==h,p
 old=runpy.run_path(str(ROOT/'scripts/generate_reload_models_w100.py'))
 for p,h in old['ORIGINALS'].items():assert sha((ROOT/p).read_bytes())==h,p
 for part in ('body','magazine'):
  p=f'src/main/resources/assets/destiny/models/weapon_reload_w100/the_recluse_{part}.json'
  assert sha((ROOT/p).read_bytes())==json.loads((ROOT/'art/weapons/w100/manifest.json').read_bytes())['assetSha256'][p]
 old['sample'].__globals__['KEYS']=KEYS
 sample=old['sample'];rotate=old['rotate']
 twohand=runpy.run_path(str(ROOT/'scripts/build_weapons_w30.py'))['two_hand_display']
 original=json.loads((ASSETS/'models/weapon/submachine_gun/the_recluse.json').read_bytes())
 two=json.loads((ASSETS/'models/weapon/submachine_gun/the_recluse_twohand.json').read_bytes())['display']
 item=json.loads((ASSETS/'items/weapon/the_recluse.json').read_bytes())
 out={};entries=[]
 for frame in range(21):
  rot,trans,offset=sample(frame/20);parts={}
  for part in ('body','magazine'):
   display=copy.deepcopy(original['display'])
   if frame not in (0,20):
    for context in ('firstperson_righthand','firstperson_lefthand'):
     pose=display[context]
     pose['rotation']=[round(v+rot[i],6) for i,v in enumerate(pose['rotation'])]
     delta=rotate(offset,pose['rotation']) if part=='magazine' else [0,0,0]
     pose['translation']=[round(v+trans[i]+delta[i]*pose['scale'][i],6) for i,v in enumerate(pose['translation'])]
   for grip in ('native','twohand'):
    current=display if grip=='native' else (two if frame in (0,20) else twohand(display,'submachine_gun'))
    key=f'{KEY}_{frame:02}_{part}_{grip}'
    out[ASSETS/f'models/{key}.json']=enc({'parent':f'destiny:weapon_reload_w100/the_recluse_{part}','display':current})
    parts[part,grip]={'type':'minecraft:model','model':'destiny:'+key}
  def composite(grip):return {'type':'minecraft:composite','models':[parts['body',grip],parts['magazine',grip]]}
  entries.append({'threshold':frame/20,'model':{'type':'minecraft:condition','property':'minecraft:custom_model_data','index':0,'on_true':composite('twohand'),'on_false':composite('native')}})
 wrapper=copy.deepcopy(item)
 wrapper['model']={'type':'minecraft:select','property':'minecraft:display_context','cases':[{'when':['firstperson_righthand','firstperson_lefthand'],'model':{'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':1,'entries':entries,'fallback':item['model']}}],'fallback':item['model']}
 out[ASSETS/f'items/{KEY}.json']=enc(wrapper)
 assert len(out)==85
 out[ART/'manifest.json']=enc({'stage':'W101','generator':'scripts/generate_reload_framing_w101.py','generatorSha256':sha(Path(__file__).read_bytes()),'assets':85,'frames':21,'keyframes':KEYS,'baselinePins':PINS,'originalPins':old['ORIGINALS'],'geometryParents':['destiny:weapon_reload_w100/the_recluse_body','destiny:weapon_reload_w100/the_recluse_magazine'],'originalCubes':217,'authoredApproximation':True,'handIK':False,'nativeVisibilityAccepted':False,'gameplayChanged':False,'sha256':{str(p.relative_to(ROOT)):sha(v) for p,v in out.items()}})
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');args=ap.parse_args()
 outputs=generate()
 for p,data in outputs.items():
  assert p.is_relative_to(ART) or p.is_relative_to(ASSETS/'models/weapon_reload_w101') or p.is_relative_to(ASSETS/'items/weapon_reload_w101')
  if args.verify:assert p.is_file() and p.read_bytes()==data,p
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} W101 files')
