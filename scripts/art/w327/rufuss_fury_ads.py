"""Rufus-only ADS vertical alignment; source geometry and all other poses remain.
Native capture showed donor y13.12 aiming through the opaque sight base.
The authored roof top is y14.04596242, so y14.16 clears it by .114 model units.
"""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DONOR='steelfeather_repeater';WID='rufuss_fury'
DONOR_SIGHT_Y=13.12;IRON_TOP_SIGHT_Y=14.16;SCALE=.9
DELTA_Y=-SCALE*(IRON_TOP_SIGHT_Y-DONOR_SIGHT_Y)
def build(source_root=ROOT):
 folder=Path('src/main/resources/assets/destiny/models/weapon_sight_w151');out=ROOT/folder;out.mkdir(parents=True,exist_ok=True);paths=[]
 for frame in range(21):
  for style in ['native','twohand']:
   source=source_root/folder/f'{DONOR}_{frame:02}_{style}.json'
   doc=json.loads(source.read_text().replace(DONOR,WID))
   for context in ['firstperson_righthand','firstperson_lefthand']:
    t=doc['display'][context]['translation'];t[1]=round(t[1]+DELTA_Y*frame/20,6)
   dest=out/f'{WID}_{frame:02}_{style}.json';dest.write_text(json.dumps(doc,indent=2)+'\n');paths.append(dest)
 return paths
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=Path,default=ROOT);args=ap.parse_args();print('Rufus ADS leaves',len(build(args.source_root)),'target Y',round(3.712+DELTA_Y,6))
