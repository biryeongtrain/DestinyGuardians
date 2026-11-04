#!/usr/bin/env python3
"""Assemble W115 authored surface parts without changing historical source assets.

Only full geometry replacements and the exact Polymer output migration manifest.
--verify is read-only; no Minecraft/DCC launch, mutation of originals or networking.
"""
from pathlib import Path
import argparse,copy,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'src/main/resources'
PINS={'assets/destiny/models/weapon/pulse_rifle/blast_furnace.json': 'f3922a28cc58de8c7a7f965ba3464aeb5841d1a53bde72bf74d58e48aca39706', 'assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_body.json': '1c92741af670629976269083b2c054efd6d9d28087da61e19b6226c255ff665a', 'assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_magazine.json': '32e31c399e609adaea4319ca17208420d0b62e44b624cc2de8e1742d4baa5397', 'assets/destiny/models/weapon/machine_gun/hammerhead.json': '7890eb2e60dc2a6547c7af7278a079b9e28575fd186683769c41f3c725c990bb', 'assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_body.json': '35fac0b51a7d6ece2b0f88bbf1820f7418cbc248391063b280dd3c2eb52d79e6', 'assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_magazine.json': 'e3558d5db3528e6637781d618ef80cd004d5faf937641497ef67423988b62d7e', 'assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_cover.json': 'b82174b32e72d7395d73d22960e6500398bfc6be6b87d7374909bad95193d57b'}
WEAPONS={'blast_furnace':('pulse_rifle',('body','magazine')), 'hammerhead':('machine_gun',('body','magazine','cover'))}
def dump(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def art_revision(weapon):
 value=json.loads((ROOT/f'art/weapons/w115/{weapon}/manifest.json').read_text())['revision']
 match=re.fullmatch(r'r?([2345])(?:[-_].*)?',str(value))
 assert match, ('Unknown reviewed art revision',weapon,value)
 return int(match.group(1))
def review_budget(weapon,revision):
 assert weapon in WEAPONS and revision in (2,3,4,5), ('Unknown reviewed budget',weapon,revision)
 # R5 explicitly allows BF source-plane fidelity up to6144faces; historical caps stay fixed.
 # Review allowance only, not a native limit or measured performance certificate.
 return 6144 if revision==5 or weapon=='hammerhead' and revision in (3,4) else 4608
def generate():
 outputs={};targets=[];revisions={weapon:art_revision(weapon) for weapon in WEAPONS}
 for path,digest in PINS.items():
  assert sha((RES/path).read_bytes())==digest, f'Historical input drift: {path}'
 for weapon,(family,parts) in WEAPONS.items():
  models=[json.loads((RES/f'assets/destiny/models/weapon_surface_w115/{weapon}_{part}.json').read_text()) for part in parts]
  textures=models[0]['textures']
  assert all(m['textures']==textures and m['elements'] and 'display' not in m and 'parent' not in m for m in models)
  elements=[e for m in models for e in m['elements']]
  assert len(elements)>=200, (weapon,'Preserve detailed source anatomy, not rejected R1 boxes',len(elements))
  # R3 Hammerhead retains 272 source components and moving feed geometry with
  # opaque cuboids: fewer alpha tears but 5966 actual emitted faces. Review cap,
  # not vanilla limit/performance certification; R2 and Blast Furnace stay4608.
  face_budget=review_budget(weapon,revisions[weapon])
  assert len(elements)<=2048 and sum(len(e['faces']) for e in elements)<=face_budget, (weapon,'Reviewed primitive/face budget exceeded, not an engine cap')
  assert len({e['name'] for e in elements})==len(elements), 'Named authored anatomy must be unique'
  old=f'assets/destiny/models/weapon/{family}/{weapon}.json'
  full=copy.deepcopy(json.loads((RES/old).read_text()))
  full['textures']=textures;full['elements']=elements;full['credit']='W115 R2 source-faithful detailed surfaces; Destiny design Bungie; poses unchanged'
  if revisions[weapon]==3:full['credit']='W116 R3 source-preserving clean rotated cuboids and selective contours; Destiny design Bungie; poses unchanged'
  if revisions[weapon]==4:full['credit']='W117 R4 source-fitted rotated cuboids and selective contours; Destiny design Bungie; poses unchanged'
  if revisions[weapon]==5:full['credit']='W118 R5 source-contour rotated cuboids and selective contours; Destiny design Bungie; poses unchanged'
  new=f'assets/destiny/models/weapon_surface_w115/{weapon}.json';raw=dump(full);outputs[RES/new]=raw
  targets.append(dict(path=old,sourceSha256=PINS[old],replacement=new,replacementSha256=sha(raw)))
  for part,model in zip(parts,models):
   old=f'assets/destiny/models/weapon_reload_w114_{weapon}/{weapon}_{part}.json'
   new=f'assets/destiny/models/weapon_surface_w115/{weapon}_{part}.json'
   targets.append(dict(path=old,sourceSha256=PINS[old],replacement=new,replacementSha256=sha((RES/new).read_bytes())))
 manifest=dict(schema=1,stage='W115',targets=targets,policy='Exactly seven geometry output substitutions. Canonical source, display transforms, item graphs, animation curves, stats and audio unchanged.')
 if any(v>=3 for v in revisions.values()):manifest['artRevisions']=revisions
 outputs[RES/'weapon_surface_w115/manifest.json']=dump(manifest)
 return outputs

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();outputs=generate()
 for p,b in outputs.items():
  if args.verify:assert p.is_file() and p.read_bytes()==b, f'Output drift: {p}'
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 print(json.dumps(dict(outputs=len(outputs),verified=args.verify,targets=7)))
if __name__=='__main__':main()
