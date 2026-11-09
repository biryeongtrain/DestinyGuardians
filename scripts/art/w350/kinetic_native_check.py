"""Targeted checks for the first native Vision corrections; no client operated."""
import sys,json,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'src/main/resources/assets/destiny'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
for w in sys.argv[1:] or ['crimson','thorn','outbreak_perfected']:
 ad=ROOT/'art/weapons/w350'/w;doc=json.load(open(ad/'parts.json'));es=sum(doc['parts'].values(),[]);assert len(es)<=1000
 for e in es:
  assert all(-16<=a<=b<=32 for a,b in zip(e['from'],e['to']));dims=sum(b>a for a,b in zip(e['from'],e['to']));assert dims in (2,3);assert len(e['faces'])==(2 if dims==2 else 6)
  assert all(0<=q<=16 for f in e['faces'].values() for q in f['uv'])
 report=json.load(open(ad/'native-review-first.json'));d=report['adsDisplay'];a=report['sightAnchor'];p=math.radians(d['rotation'][0]);s=d['scale'][0];yy=(a[1]-8)*math.cos(p)-(a[2]-8)*math.sin(p);zz=(a[1]-8)*math.sin(p)+(a[2]-8)*math.cos(p);camera=[.56+d['translation'][0]/16,-.52+(d['translation'][1]+s*yy)/16,-.72+(d['translation'][2]+s*zz)/16];assert abs(camera[0])<1e-8 and abs(camera[1])<1e-8;assert abs(camera[2]+report['projection']['eyeToSightMeters'])<1e-8
 assert sha(A/f'textures/item/weapon/w350/{w}.png')==report['atlasSHA256']
 manifest=json.load(open(ad/'manifest.json'))
 for rel,digest in manifest['outputsSha256'].items():assert sha(ROOT/rel)==digest,rel
 paths=set()
 for branch in ['items','models']:
  for ns in ['weapon_w350','weapon_aim_w350','weapon_reload_w350']:paths.update((A/branch/ns/w).rglob('*.json'))
 paths.update([A/f'items/weapon/{w}.json',A/f'items/weapon_aim_w350/{w}.json',A/f'items/weapon_reload_w350/{w}.json'])
 for path in paths:
  q=json.load(open(path))
  # Every direct model and parent reference is a physical resource.
  def walk(x):
   if isinstance(x,dict):
    for k,v in x.items():
     if k in ['model','parent'] and isinstance(v,str) and v.startswith('destiny:'):assert (A/'models'/(v.split(':',1)[1]+'.json')).is_file(),(path,v)
     walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(q)
 rig=json.load(open(ad/'rig.json'));assert len(rig['poses'])==61 and rig['poses'][0]['bodyDisplay']==rig['poses'][-1]['bodyDisplay'] and rig['poses'][0]['magazineDisplay']==rig['poses'][-1]['magazineDisplay']
 source=json.load(open(ad/'source-evaluation.json'));assert sha(Path(source['blend']))==source['sha256']
 captures=Path('/tmp/exotic-expansion-20261109/qa/native');report['reviewedCaptureSHA256']={p.name:sha(p) for p in sorted(captures.glob(f'first-{w}-*.png')) if ('reload-valid-' in p.name or p.name.endswith(('-hip-0.png','-third.png','-ads-end-0.png')))};assert len(report['reviewedCaptureSHA256'])==8
 report['targetedChecks']=dict(jsonGraphs=len(paths),modelReferences='PASS',boundsUV='PASS',atlasUnchanged='PASS',sourceBlendUnchanged='PASS',reloadEndpoints='PASS',projectedSightCameraMeters=camera,nativeSecondVision='PENDING MASTER')
 (ad/'native-review-first.json').write_text(json.dumps(report,indent=2)+'\n');print(w,'PASS',len(es),'elements; projected sight',camera)
