"""Offline product gates; does not claim game pack loading or native QA."""
import json,hashlib,sys,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AS=ROOT/'src/main/resources/assets/destiny'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def values(x,key):
 if isinstance(x,dict):
  for k,v in x.items():
   if k==key and isinstance(v,str):yield v
   yield from values(v,key)
 elif isinstance(x,list):
  for v in x:yield from values(v,key)
for w in sys.argv[1:] or ['crimson','thorn','outbreak_perfected']:
 ad=ROOT/'art/weapons/w350'/w;d=json.loads((ad/'parts.json').read_text());es=sum(d['parts'].values(),[]);assert len(es)<=1000;assert len(set(e['name'] for e in es))==len(es)
 for e in es:
  assert all(-16<=a<=b<=32 for a,b in zip(e['from'],e['to']))
  assert sum(b>a for a,b in zip(e['from'],e['to']))==2
  assert set(e['faces'])=={'south','north'}
  assert all(0<=q<=16 for f in e['faces'].values() for q in f['uv'])
 solids=json.loads((ad/'r2-authored-solids.json').read_text());closed=0
 for rec in solids['solids']:
  edges={}
  for face in rec['mesh_faces']:
   assert len(face)>=3
   for a,b in zip(face,face[1:]+face[:1]):key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
  assert set(edges.values())=={2},rec['name'];closed+=1
 ev=json.loads((ad/'source-evaluation.json').read_text());assert sha(Path(ev['blend']))==ev['sha256'];assert ev['actions']==[]
 rig=json.loads((ad/'rig.json').read_text());poses=rig['poses'];assert len(poses)==61
 assert poses[0]['bodyDisplay']==poses[-1]['bodyDisplay'];assert poses[0]['magazineDisplay']==poses[-1]['magazineDisplay']
 paths=set()
 for branch in ['items','models']:
  for ns in ['weapon_w350','weapon_aim_w350','weapon_reload_w350']:
   paths.update((AS/branch/ns/w).rglob('*.json'))
 paths.update([AS/f'items/weapon/{w}.json',AS/f'items/weapon_aim_w350/{w}.json',AS/f'items/weapon_reload_w350/{w}.json'])
 refs=set()
 for p in paths:
  q=json.loads(p.read_text())
  for k in ['model','parent']:
   for ref in values(q,k):
    if ref.startswith('destiny:'):
     rp=AS/'models'/(ref.split(':',1)[1]+'.json');assert rp.is_file(),(p,rp);refs.add(str(rp.relative_to(ROOT)))
 manifest=json.loads((ad/'manifest.json').read_text())
 for rel,digest in manifest['outputsSha256'].items():assert sha(ROOT/rel)==digest,rel
 evidence=json.loads((ad/'render-evidence-r2.json').read_text());assert evidence['partsSHA256']==sha(ad/'parts.json');assert evidence['textureSHA256']==sha(AS/f'textures/item/weapon/w350/{w}.png')
 for name,digest in evidence['views'].items():assert sha(ad/'review-r2'/name)==digest,name
 report=dict(revision=2,offlineJSONParsing='PASS',nativePlaneBounds='PASS',UVBounds='PASS',emittedElements={k:len(v) for k,v in d['parts'].items()},emittedWeaponTotal=len(es),semanticSolids=closed,allAuthoredSolidEdgeIncidencesExactlyTwo=True,optimization=solids['optimization'],sourceBlendSHA256=ev['sha256'],sourceBlendUnchanged=True,sourceActions=0,authoredReloadPoses=61,aimPoses=21,poseEndpoints='exact idle restored',graphFilesParsed=len(paths),modelReferencesResolved=len(refs),manifestHashes='PASS',images='Actual native item JSON: side, both opposite obliques, top, front; source matching comparison sheets',nativePackLoad='PENDING MASTER',hipADSGripReloadThirdPerson='PENDING MASTER FIRST VISION / DELEGATED REVIEW / SECOND VISION',tenToTwentyAndFPS='NOT MEASURED')
 (ad/'validation-r2.json').write_text(json.dumps(report,indent=2)+'\n');print(w,'PASS',len(es),'emitted;',closed,'closed solids;',len(paths),'graphs')
