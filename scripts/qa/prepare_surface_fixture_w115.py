#!/usr/bin/env python3
"""Build isolated-only A/B resource-pack fixtures. Never edits product assets or profiles."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,zipfile
ROOT=Path(__file__).resolve().parents[2];RES=ROOT/'src/main/resources'
def dump(v):return (json.dumps(v,separators=(',',':'))+'\n').encode()
def build():
 out={}
 for weapon,family in [('blast_furnace','pulse_rifle'),('hammerhead','machine_gun')]:
  for state,path in [('original',RES/f'assets/destiny/models/weapon/{family}/{weapon}.json'),('revised',RES/f'assets/destiny/models/weapon_surface_w115/{weapon}.json')]:
   key=weapon+'_'+state
   out[f'assets/w115qa/models/{key}.json']=path.read_bytes()
   out[f'assets/w115qa/items/{key}.json']=dump(dict(model=dict(type='minecraft:model',model='w115qa:'+key),hand_animation_on_swap=False))
 out['pack.mcmeta']=dump(dict(pack=dict(description='W115 isolated A/B fixtures only',min_format=[97,1],max_format=[97,1])))
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);args=p.parse_args();path=Path(args.out).resolve()
 assert path.parent.is_dir() and path.suffix=='.zip' and not path.exists(),'Require new file in existing isolated directory'
 assert str(path).startswith('/private/tmp/destiny-w115-native/'),'Only this batch isolated QA runtime is allowed'
 files=build()
 with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for name,data in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,10,25,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
 print(json.dumps(dict(files=len(files),path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
