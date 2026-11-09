"""Krait-only ADS framing over unchanged source-proportioned geometry.
The donor camera sat ~5cm from Krait's tall rear stock. Aim over its authored
front sight with a small whole-weapon pitch and a safe eye-to-sight distance.
No HIP, reload, body, UV, or shared generator is changed.
"""
import argparse,copy,json,math,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def build(source_root=ROOT):
 assets=source_root/'src/main/resources/assets/destiny'
 output=ROOT/'src/main/resources/assets/destiny/models/weapon_sight_w151'
 output.mkdir(parents=True,exist_ok=True)
 hip=json.loads((assets/'models/weapon/auto_rifle/steelfeather_repeater.json').read_text())['display']
 two_hand=runpy.run_path(str(source_root/'scripts/build_weapons_w30.py'))['two_hand_display']
 anchor=[8,13.98,2.0];angle=6.;scale=.9;distance=1.10
 a=math.radians(angle);y=(anchor[1]-8)*math.cos(a)-(anchor[2]-8)*math.sin(a);z=(anchor[1]-8)*math.sin(a)+(anchor[2]-8)*math.cos(a)
 target={'rotation':[angle,0,0],'translation':[-8.96,round(8.32-scale*y,6),round(16*(.72-distance)-scale*z,6)],'scale':[scale]*3}
 outputs=[]
 for frame in range(21):
  display=copy.deepcopy(hip)
  for context in ['firstperson_righthand','firstperson_lefthand']:
   for k in ['rotation','translation','scale']:
    display[context][k]=[round(v+(q-v)*frame/20,6) for v,q in zip(hip[context][k],target[k])]
  for style in ['native','twohand']:
   parent='destiny:weapon/auto_rifle/krait' if frame==0 else 'destiny:weapon_sight_w151/krait_body'
   doc={'parent':parent,'display':display if style=='native' else two_hand(display,'auto_rifle')}
   p=output/f'krait_{frame:02}_{style}.json';p.write_text(json.dumps(doc,indent=2)+'\n');outputs.append(p)
 return outputs,{'sight_anchor':anchor,'pitch_degrees':angle,'scale':scale,'eye_to_sight_meters':distance,'target_display':target,'native_qa':'pending master'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,default=ROOT);args=ap.parse_args();paths,report=build(args.source_root);print(json.dumps(report,indent=2));print('Wrote',len(paths),'Krait-only ADS leaves')
