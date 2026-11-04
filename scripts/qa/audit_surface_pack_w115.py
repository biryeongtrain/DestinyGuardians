#!/usr/bin/env python3
"""Verify actual generated W115 pack: seven replacements, nine additions, no other Destiny drift."""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RES=ROOT/'src/main/resources'
def sha(b):return hashlib.sha256(b).hexdigest()
def audit(old,new):
 manifest=json.loads((RES/'weapon_surface_w115/manifest.json').read_text())
 targets={r['path']:r for r in manifest['targets']}
 assert len(targets)==7
 added={r['replacement'] for r in targets.values()}|{'assets/destiny/textures/item/weapon/w115/'+i+'.png' for i in ('blast_furnace','hammerhead')}
 assert len(added)==9
 with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
  oldnames={n for n in a.namelist() if n.startswith('assets/destiny/') and not n.endswith('/')}
  newnames={n for n in b.namelist() if n.startswith('assets/destiny/') and not n.endswith('/')}
  assert not oldnames-newnames, sorted(oldnames-newnames)
  assert newnames-oldnames==added, sorted((newnames-oldnames)^added)
  changed={n for n in oldnames if a.read(n)!=b.read(n)}
  assert changed==set(targets), sorted(changed^set(targets))
  for path,row in targets.items():
   assert sha(a.read(path))==row['sourceSha256'], path
   assert sha(b.read(path))==row['replacementSha256'], path
   assert b.read(path)==b.read(row['replacement'])==(RES/row['replacement']).read_bytes()
  for path in added:assert b.read(path)==(RES/path).read_bytes(),path
  return dict(oldPackSha256=sha(Path(old).read_bytes()),newPackSha256=sha(Path(new).read_bytes()),
   oldDestinyFiles=len(oldnames),newDestinyFiles=len(newnames),changed=sorted(changed),added=sorted(added),unchanged=len(oldnames)-len(changed))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('old');p.add_argument('new');p.add_argument('--out',required=True);args=p.parse_args()
 result=audit(args.old,args.new);out=Path(args.out);assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(changed=len(result['changed']),added=len(result['added']),unchanged=result['unchanged'])))
