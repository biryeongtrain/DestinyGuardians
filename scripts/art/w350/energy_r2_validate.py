"""Offline contracts for the R2 native geometry and authored hollow topology."""
import json,hashlib,math,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];A=ROOT/'src/main/resources/assets/destiny'
IDS=['sunshot','graviton_lance','jotunn']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def ray_hits(tris,py,pz):
 hits=0
 for t in tris:
  a,b,c=t['vertices'];den=(b[2]-c[2])*(a[1]-c[1])+(c[1]-b[1])*(a[2]-c[2])
  if abs(den)<1e-10:continue
  u=((b[2]-c[2])*(py-c[1])+(c[1]-b[1])*(pz-c[2]))/den
  v=((c[2]-a[2])*(py-c[1])+(a[1]-c[1])*(pz-c[2]))/den
  if min(u,v,1-u-v)>1e-6:hits+=1
 return hits
for w in IDS:
 art=ROOT/f'art/weapons/w350/{w}';out=art/'r2';d=json.loads((art/'geometry.json').read_text());elements=sum(d['parts'].values(),[])
 assert 0<len(elements)<=1000
 assert len({e['name'] for e in elements})==len(elements)
 for e in elements:
  assert all(a<=b for a,b in zip(e['from'],e['to']))
  assert sum(a<b for a,b in zip(e['from'],e['to']))>=2
  assert all(-16<=v<=32 for v in e['from']+e['to'])
  assert set(e)-{'name','from','to','rotation','faces','light_emission'}==set()
  for face in e['faces'].values():assert all(0<=v<=16 for v in face['uv'])
 full=json.loads((A/f'models/weapon_w350/{w}/full.json').read_text());assert full['elements']==elements
 assert json.loads((out/'model.json').read_text())==d
 ev=json.loads((art/'source-evaluation.json').read_text());assert sha(Path(ev['blend']))==ev['sha256']
 rig=json.loads((art/'rig-reload.json').read_text());assert len(rig['frames'])==61
 assert rig['frames'][0]['body']==rig['frames'][-1]['body'];assert rig['frames'][0]['magazine']==rig['frames'][-1]['magazine']
 assert rig['sourceHasReloadAction'] is False
 refs=0;parsed=0
 def walk(x):
  global refs
  if isinstance(x,list):
   for v in x:walk(v)
  if isinstance(x,dict):
   for k,v in x.items():
    if k in ['model','parent'] and isinstance(v,str) and v.startswith('destiny:'):
     assert (A/('models/'+v.split(':',1)[1]+'.json')).exists(),v;refs+=1
    else:walk(v)
 for p in A.rglob('*.json'):
  if w in p.parts or p.stem==w:walk(json.loads(p.read_text()));parsed+=1
 topology={}
 if w=='sunshot':
  tr=json.loads((out/'authored_solids.json').read_text())['triangles'];u=.020
  for label,px,py,openhole in [('diamond_front',259,260,True),('diamond_rear',334,260,True),('connecting_web',296,250,False)]:
   n=ray_hits(tr,3.5+(570-py)*u,-10+(px-80)*u);assert (n==0)==openhole,(label,n);topology[label]={'ray_hits':n,'expected_open':openhole}
 report=json.loads((out/'validation.json').read_text());report.update(standardNativeFields=True,uniqueNames=True,uvInRange=True,boundsInRange=True,fullEqualsBodyPlusMagazine=True,sourceBlendHashMatches=True,reloadPoses=61,authoredReload=True,endpointsRestoreIdentity=True,jsonFilesParsed=parsed,resolvedModelReferences=refs,topology=topology,actualClientPackLoad='pending',performance='not measured',framebuffer='not captured',generator='scripts/art/w350/energy_r2.py',generatorSha256=sha(ROOT/'scripts/art/w350/energy_r2.py'))
 put(out/'validation.json',report);put(art/'validation.json',report)
 manifest=json.loads((art/'manifest.json').read_text());manifest.update(revision=2,atlas=d['texture_size'],elements={k:len(v) for k,v in d['parts'].items()},element_total=len(elements),texels_per_px=23,generator=report['generator'],generator_sha256=report['generatorSha256'],method='authored closed semantic lofts and profiles; W327 native polygon-union adapter; no source mesh export',nativeAcceptance='pending master first Vision, delegated review, second Vision',outputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in [art/'geometry.json',A/f'textures/item/weapon/w350/{w}.png']})
 manifest.pop('hidden_faces',None);put(art/'manifest.json',manifest)
 (art/'DESIGN.md').write_text('# '+w+' — W350 revision 2\n\nInitial R1 cuboid drafts were rejected and are preserved under rejected-r1/. Revision 2 rebuilds source-shaped closed solids, crowned sections, physical apertures and material panels using the accepted W327 native polygon adapter. No source mesh vertices were converted. Native element count is '+str(len(elements))+'; this count is a budget check, not art or in-game acceptance.\n\nCalibrated read-only source projection, pinned Bungie base icon, and source side/oblique images guide the shapes and restrained face UV markings. Material previews use the actual exported native JSON and PNG. Offline renderer omits the coincident reverse plane only for rendering, matching the accepted W327 reviewer; the product contains both mirrored native faces. Sunshot diamond openings were ray-checked through the authored solids.\n\nSource .blend SHA and evaluated weapon bones/actions remain recorded. No source player wrist/elbow rig or reload action exists. All 61 reload poses and 21 aim poses are authored approximations; contact/pivot anchors were revised against the new geometry. 61 samples do not imply native continuous 60fps interpolation. Master still owns first Vision, delegated review/fixes and second Vision; pack load, hands, ADS, reload contact, third person, shots and 10–20 item observation remain unverified.\n')
 print(w,json.dumps(report),flush=True)
