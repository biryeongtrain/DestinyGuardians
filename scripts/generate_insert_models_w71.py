#!/usr/bin/env python3
"""Long Arm actual pair-reload sampled body poses. Original256cubes/UV retained.
Initial raises into a held loop; repeated insert cycles do not reset to HIP.
Return is cosmetic6ticks, not a gameplay firing gate. No source animation/hand IK.
"""
import argparse,copy,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/main/resources/assets/destiny';KEY='weapon_insert_w71/long_arm'
# Authored body response from observed raising/held slanted rifle and hand contact.
# Full decode video10.0..13.4s; exact angles/path occluded, natural exit not observed.
HOLD=([42,-10,-24],[-2.4,-.4,-.4])
KEYS={
 'initial':[(0,[0,0,0],[0,0,0]),(.15,[8,-2,-6],[-.4,-.1,-.1]),
            (.4,[35,-9,-22],[-2,-.4,-.4]),(.55,*HOLD),
            (.72,[43,-11,-25],[-2.35,-.2,-.5]),(.88,[45,-10,-22],[-2.4,0,-.3]),(1,*HOLD)],
 'loop':[(0,*HOLD),(.25,[40,-8,-26],[-2.2,-.3,-.4]),
         (.55,[43,-11,-25],[-2.35,-.2,-.5]),(.8,[45,-10,-22],[-2.4,0,-.3]),(1,*HOLD)],
 'return':[(0,*HOLD),(.35,[31,-7,-17],[-1.7,-.3,-.3]),(.7,[10,-3,-5],[-.5,-.1,-.1]),(1,[0,0,0],[0,0,0])]
}
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def sample(phase,p):
 if phase not in KEYS or not 0<=p<=1:raise ValueError((phase,p))
 for a,b in zip(KEYS[phase],KEYS[phase][1:]):
  if p<=b[0]:
   t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
   return [[round(x+(y-x)*t,6) for x,y in zip(a[j],b[j])] for j in [1,2]]
 raise ValueError((phase,p))
def generate():
 src=A/'models/weapon/scout_rifle/long_arm.json';item=A/'items/weapon/long_arm.json';transform=ROOT/'scripts/build_weapons_w30.py'
 original=json.loads(src.read_bytes());old=json.loads(item.read_bytes());twohand=runpy.run_path(str(transform))['two_hand_display']
 output={};entries=[]
 for phase_index,phase in enumerate(KEYS):
  for f in range(21):
   rotation,translation=sample(phase,f/20);display=copy.deepcopy(original['display'])
   for c in ['firstperson_righthand','firstperson_lefthand']:
    d=display[c];d['rotation']=[round(x+y,6) for x,y in zip(d['rotation'],rotation)]
    d['translation']=[round(x+y,6) for x,y in zip(d['translation'],translation)]
   parts={}
   for grip in ['native','twohand']:
    key=f'{KEY}_{phase}_{f:02}_{grip}'
    output[A/f'models/{key}.json']=encode(dict(parent='destiny:weapon/scout_rifle/long_arm',display=display if grip=='native' else twohand(display,'scout_rifle')))
    parts[grip]=dict(type='minecraft:model',model='destiny:'+key)
   entries.append(dict(threshold=phase_index*2+f/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=parts['twohand'],on_false=parts['native'])))
 wrapper=copy.deepcopy(old);wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=['firstperson_righthand','firstperson_lefthand'],model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=4,entries=entries,fallback=old['model']))],fallback=old['model'])
 output[A/f'items/{KEY}.json']=encode(wrapper)
 output[ROOT/'art/weapons/w71/manifest.json']=encode(dict(stage='W71',generator='scripts/generate_insert_models_w71.py',id='long_arm',bungieHash=8293111,phases=list(KEYS),framesPerPhase=21,progressFloatIndex=4,sourceCubes=len(original['elements']),compositeCubes=len(original['elements']),newGeometry=0,newTextures=0,returnTicks=6,returnBlocksGameplay=False,exactAnimationRip=False,handIK=False,originalsUnchanged=True,nativeGameplayVerified=False,keyframes=KEYS,limitations='Reference-informed body gesture only. No visible hand, cartridge props, articulated lever or extracted source rig. Return authored because reference exits via skill. 21 static samples, not render-frame interpolation.',inputSha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in [src,item,transform]},outputSha256={str(p.relative_to(ROOT)):sha(raw) for p,raw in output.items()}))
 return output
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();out=generate()
 for path,raw in out.items():
  if a.verify:
   if not path.is_file() or path.read_bytes()!=raw:raise SystemExit('W71 asset differs: '+str(path.relative_to(ROOT)))
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 print(f'{"Verified" if a.verify else "Generated"} {len(out)} W71 files')
