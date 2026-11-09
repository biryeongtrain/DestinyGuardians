#!/usr/bin/env python3
"""W327 special/heavy legendary authored block models; exclusive group 2 driver."""
from pathlib import Path
import sys,json,importlib.util,subprocess,hashlib,os
ROOT=Path(__file__).resolve().parents[3]
IDS='trustee succession heritage deliverance iterative_loop forbearance brigands_law apex_predator palmyra_b commemoration circular_logic cataclysmic'.split()
REG=Path('/tmp/destiny-perks-20261106/candidates/final-registry.json')
def art(w):return ROOT/'art/weapons/w327'/w
def source(w):
 if REG.exists():return Path(next(r for r in json.loads(REG.read_text()) if r['id']==w)['blend_paths'][0])
 return Path(json.loads((art(w)/'source-evaluation.json').read_text())['source'])
def setup():
 spec=importlib.util.spec_from_file_location('kit',ROOT/'scripts/art/w325/kit.py'); k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
 k.ROOT=ROOT;k.ASSETS=ROOT/'src/main/resources/assets/destiny';k.REG=REG;k.RIPS=Path('/tmp/destiny-perks-20261106/rips')
 if not REG.exists():k.reg=lambda w:json.loads((art(w)/'manifest.json').read_text())
 k.art=art
 k.atlas_path=lambda w:k.ASSETS/f'textures/item/weapon/w327/{w}.png'; k.hud_path=lambda w:k.ASSETS/f'textures/item/hud/w327/ammo_{w}.png'
 # Source albedo contributes filtered material detail, while authored roles reconstruct the default finish.
 import math
 from PIL import Image,ImageFilter
 k.Baker.KINDS.update({
  'steel':dict(field=.17,grain='brushed',amp=6,detail=.8,rim=.32),
  'metal':dict(field=.12,grain='brushed',amp=5,detail=.7,rim=.24),
  'paint':dict(field=.008,grain='fine',amp=1,detail=.65,rim=.085,plate=False),
  'bone':dict(field=.085,grain='fine',amp=1,detail=1.2,rim=.22),
  'gold':dict(field=.18,grain='brushed',amp=4,detail=.85,rim=.36,border=True),
  'rubber':dict(field=.025,grain='cross',amp=5,detail=.4,rim=.045),
  'ceramic':dict(field=.07,grain='fine',amp=2,detail=1.0,rim=.16)})
 k.SEAM=20;k.GRAIN=.5
 def init(self,w):
  self.wid=w;self.D=k.load_design(w);D=self.D;self.T=D.T;self.A=D.ATLAS
  self.special=D.special;self.clear=lambda e,f:False;self.is_mag=D.is_magazine;self.fallback=(96,96,96,255);self.grade=lambda c:tuple(round(v) for v in c)
  cache=Path('/tmp/destiny-perks-20261106/group2-cache')/w
  if not (cache/'manifest.json').exists():raise RuntimeError('Missing source projection cache; run group2.py source '+w+' from preserved .blend first')
  man=json.loads((cache/'manifest.json').read_text());self.views={key:k.View(cache,key,man) for key in man['views']};self.occ=max(man['hi'][i]-man['lo'][i] for i in range(3))*.08
  ee=D.elements();lo=[min(e['from'][i] for e in ee) for i in range(3)];hi=[max(e['to'][i] for e in ee) for i in range(3)];sl=man['lo'];sh=man['hi'];xlong=w in ('iterative_loop','commemoration','circular_logic')
  def mapping(name,p):
   nz=(p[2]-lo[2])/(hi[2]-lo[2]);ny=(p[1]-lo[1])/(hi[1]-lo[1]);nx=(p[0]-lo[0])/(hi[0]-lo[0])
   if xlong:return (sh[0]-nz*(sh[0]-sl[0]),sl[1]+nx*(sh[1]-sl[1]),sl[2]+ny*(sh[2]-sl[2]))
   return (sl[0]+nx*(sh[0]-sl[0]),sl[1]+nz*(sh[1]-sl[1]),sl[2]+ny*(sh[2]-sl[2]))
  if getattr(D,"REVISION",0)<3:D.model2world=mapping
  else:self.occ=.09
 k.Baker.__init__=init
 original_materialize=k.Baker.materialize
 def finish(self,faces):
  if self.wid=='brigands_law' and getattr(self.D,'REVISION',0)>=3:
   import importlib.util
   spec=importlib.util.spec_from_file_location('brigand_v3_finish',art(self.wid)/'v3_finish.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.finish(self,faces,k);return
  # The supplied Apex tube shader is corrupt; do not project its diagnostic grid into ivory.
  if self.wid=='apex_predator':
   for n,f,img,clear,e,others,painted in faces:
    if e['role']!='shell':continue
    px=img.load()
    for i in range(img.width):
     for j in range(img.height):
      if painted[i][j]:continue
      r,g,b,a=px[i,j];valid=r>60 and g>60 and .8<r/(g+1)<1.3 and b<r*.95;v=round(128+max(-24,min(24,((.299*r+.587*g+.114*b)-140)*.4))) if valid else 128;px[i,j]=(v,v,v,a)
  originals={(n,f):img.copy() for n,f,img,*_ in faces};original_materialize(self,faces)
  for n,f,img,clear,e,others,painted in faces:
   if clear:continue
   material=self.material_of(e,f);mat=self.D.MATERIALS.get(material,{}) if isinstance(material,str) else material;kind=mat.get('kind') if mat else None
   w,h=img.size;px=img.load();raw_rgb=originals[n,f].convert('RGB');raw_px=raw_rgb.load();raw=raw_rgb.convert('L');blur=raw.filter(ImageFilter.GaussianBlur(max(1,self.T*.12)));rp=raw.load();bp=blur.load()
   for i in range(1,w-1):
    for j in range(1,h-1):
     if painted[i][j]:continue
     c=px[i,j];factor=1
     if kind in ('steel','metal','gold') and f in ('east','west','up'):
      v=(j+.5)/h;factor=.88+.29*math.exp(-((v-.31)/.14)**2)+.06*math.exp(-((v-.8)/.05)**2)
     elif kind=='bone':
      relief=rp[i,j]-bp[i,j];factor=1+max(-.13,min(.08,relief/320))
      rc=raw_px[i,j]
      if self.wid=='brigands_law' and rc[2]>rc[0]*1.1 and rc[2]>rc[1]*1.05 and rc[2]-rc[0]>8 and sum(rc)<450:
       c=tuple(self.D.MATERIALS['accent']['color'])+(c[3],);factor=.96+max(-.08,min(.08,relief/500))
     px[i,j]=tuple(max(0,min(255,round(v*factor))) for v in c[:3])+(c[3],)
 k.Baker.materialize=finish
 return k

def evaluate(w):
 import bpy,mathutils
 p=source(w);out=art(w);out.mkdir(parents=True,exist_ok=True)
 deps=bpy.context.evaluated_depsgraph_get()
 objs=[]
 for o in bpy.data.objects:
  if o.type=='MESH':
   eo=o.evaluated_get(deps);pts=[eo.matrix_world@mathutils.Vector(v) for v in eo.bound_box]
   objs.append(dict(name=o.name,vertices=len(eo.data.vertices),bounds=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],materials=[m.name for m in o.data.materials if m]))
 meta=dict(source=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),evaluation='Actual .blend opened in isolated headless Blender with --disable-autoexec; evaluated depsgraph',objects=objs,actions=[dict(name=a.name,frames=list(a.frame_range),slots=[s.identifier for s in getattr(a,'slots',[])]) for a in bpy.data.actions],armatures={o.name:[dict(name=b.name,head=list(o.matrix_world@b.head_local),tail=list(o.matrix_world@b.tail_local)) for b in o.data.bones] for o in bpy.data.objects if o.type=='ARMATURE'})
 (out/'source-evaluation.json').write_text(json.dumps(meta,indent=1))
 cache=Path('/tmp/destiny-perks-20261106/group2-cache')/w;cache.mkdir(parents=True,exist_ok=True)
 link=out/'proj_cache'
 if not link.exists():link.symlink_to(cache,target_is_directory=True)
 sys.argv=['extract','--',str(cache),os.environ.get('W327_SOURCE_PPM','420')]
 code=(ROOT/'scripts/art/w325/extract_projection_cache.py').read_text().replace('sc.cycles.samples = 16','sc.cycles.samples = 4')
 ns={'__name__':'__main__'};exec(compile(code,'source_extractor','exec'),ns)
 # source oblique, from the same evaluated scene and actual read-only source.
 sc=ns['sc'];co=ns['co'];cam=ns['cam'];c=mathutils.Vector(ns['ctr']);ext=max(ns['hi'][i]-ns['lo'][i] for i in range(3))
 d=mathutils.Vector((.4,1,.35) if w in ('iterative_loop','commemoration','circular_logic') else (1,-.55,.35)).normalized();co.location=c+d*max(3,ext*3);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=ext*1.15
 sc.render.resolution_x=1000;sc.render.resolution_y=600;sc.view_layers[0].material_override=None;ns['rewire_albedo']();sc.view_settings.view_transform='Standard';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.cycles.samples=8
 review=out/'review';review.mkdir(exist_ok=True);sc.render.filepath=str(review/'source_oblique.png');bpy.ops.render.render(write_still=True)
 from shutil import copy2
 for name in ['px','nx','py','ny','pz','nz']:copy2(cache/f'{name}_albedo.png',review/f'source_{name}.png')

ADS_VERSIONS=dict(aishas_embrace=153,hollow_words=153,null_composure=153,dead_man_walking_xx7463=153,hammerhead=151,first_in_last_out=148,deafening_whisper=149,bellowing_giant=150,pyroclastic_flow=150,line_in_the_sand=150)
RELOAD_VERSIONS=dict(aishas_embrace=213,bite_of_the_fox=214,hollow_words=217,null_composure=217,deafening_whisper=220,dead_man_walking_xx7463=219,bellowing_giant=218,pyroclastic_flow=221,hammerhead=207,line_in_the_sand=218)
def ads_source(w,k):
 base=k.reg(w)['base'];md=k.ASSETS/'models'
 if base in ADS_VERSIONS:
  v=ADS_VERSIONS[base];p=md/f'weapon_sight_w{v}/{base}_body.json'
  if not p.exists():p=md/f'weapon_sight_w{v}/{base}_20_native.json'
 else:p=md/f'weapon_reload_w{RELOAD_VERSIONS[base]}_{base}/{base}_body.json'
 seen=[]
 while True:
  seen.append(str(p.relative_to(ROOT)));d=json.loads(p.read_text())
  if d.get('elements'):return p,d['elements'],seen
  p=md/(d['parent'].split(':',1)[1]+'.json')
def adscheck(w):
 k=setup();p,base,chain=ads_source(w,k);es=json.loads(k.skin_path(w).read_text())['parts'];skin=[e for part in es.values() for e in part]
 def top(els,z):
  ys=[]
  for e in els:
   if e.get('faces') and all(f.get('texture')!='#0' for f in e['faces'].values()):continue
   c=k._corners(e)
   if max(v[2] for v in c)<z or min(v[2] for v in c)>z+.25 or max(v[0] for v in c)<6.6 or min(v[0] for v in c)>9.4:continue
   ys.append(max(v[1] for v in c))
  return max(ys) if ys else None
 zs=[v[2] for e in base for v in k._corners(e)];z=min(zs)+(max(zs)-min(zs))/3;bad=[]
 while z<max(zs):
  a,b=top(base,z),top(skin,z)
  if b is not None and (a is None or b>a+.15):bad.append(dict(z=round(z,3),skin_top=round(b,3),base_top=None if a is None else round(a,3)))
  z+=.25
 report=dict(id=w,base=k.reg(w)['base'],ads_source_chain=chain,method='Conservative 0.25px slices in center x 6.6..9.4, rear two-thirds; active WeaponAimPresentation source; assembled moving parts included',status='PASS' if not bad else 'REVIEW',above_profile=bad,native_vision='NOT_RUN_BY_WORKER',reload_motion='Inherited base poses, not original ripped animation')
 (art(w)/'adscheck.json').write_text(json.dumps(report,indent=1)+'\n');print(w,report['status'],len(bad),chain[-1])

def build(w):
 from shutil import copy2
 k=setup();k.Baker(w).build();p=art(w)/'manifest.json';m=json.loads(p.read_text());evaluation=json.loads((art(w)/'source-evaluation.json').read_text());design=json.loads((art(w)/'design.json').read_text())
 source_available=Path(evaluation['source']).exists();actual=k.sha(Path(evaluation['source'])) if source_available else evaluation['sha256'];assert actual==evaluation['sha256'],'Read-only Blender source drifted'
 icons=Path('/tmp/destiny-perks-20261106/official-icons');icon=icons/(w+'.jpg')
 if icon.exists():copy2(icon,art(w)/'review/official_icon.jpg')
 source_urls=json.loads((icons/'sources.json').read_text()) if (icons/'sources.json').exists() else {}
 base=k.reg(w)['base'];mp=RELOAD_VERSIONS.get(base);md=k.ASSETS/'models';reload_dir=md/(f'weapon_reload_w{mp}_{base}' if mp else f'weapon_insert_w208_{base}')
 import re
 frames=sorted({int(x) for p_ in reload_dir.glob('*.json') for x in re.findall(r'_(\d\d)(?:_|\.)',p_.name)})
 m.update(batch='W327',revision=design.get('revision',2),material_pipeline='Six calibrated source albedo/depth views, approximate affine layout mapping for filtered relief, authored finish role colors and directional metal highlights; static RGBA not dynamic PBR',authoring='Semantic block reconstruction; source-filtered detail with distinct steel/paint/rubber/bone/gold finishes and restrained 1-texel edges; baked RGBA finish, not dynamic PBR',original_blend_sha256=actual,original_blend=str(evaluation['source']),original_blend_unchanged=source_available,source_actions=len(evaluation['actions']),source_bones={n:[b['name'] for b in bs] for n,bs in evaluation['armatures'].items()},source_hand_rig='No wrist/elbow/hand animation in supplied source; static weapon rig only',official_icon_url=source_urls.get(w),official_icon_sha256=k.sha(icon) if icon.exists() else None,materials=design['materials'],reload_contract=dict(base=base,geometry_directory=str(reload_dir.relative_to(ROOT)),pose_indices=frames,source_motion_claim=False,contact_review='Offline source weapon/bone review and inherited base layout only; native hand/contact acceptance belongs to master Vision'),reticle='Inherited base overlay retained; physical sight adapted to active ADS profile',validation='See validation.json and adscheck.json; no in-game worker acceptance')
 if design.get('revision')==3:
  m.update(material_pipeline='Calibrated source-space mapping with separate six-face views; authored controlled palette; source navy ornament and carved seal preserved; no procedural broad gradients',authoring='Semantic V3 solid reconstruction: swept open bow, octagonal barrel and layered muzzle, sculpted raked grip, articulated lever and cutout guard. Native rotated cuboids, source-mapped per-face UV.',source_mapping=design['source_mapping'])
 p.write_text(json.dumps(m,indent=1,sort_keys=True)+'\n')
def surface_conflicts(es):
 bad=[]
 for i,a in enumerate(es):
  for b in es[i+1:]:
   if a['name'].startswith('mag_')!=b['name'].startswith('mag_'):continue
   for ax in range(3):
    for side in ['from','to']:
     if abs(a[side][ax]-b[side][ax])>1e-5:continue
     other=[j for j in range(3) if j!=ax];lo=[max(a['from'][j],b['from'][j]) for j in other];hi=[min(a['to'][j],b['to'][j]) for j in other]
     if not all(hi[j]-lo[j]>1e-5 for j in range(2)):continue
     pt=[0]*3;pt[ax]=a[side][ax]+(.001 if side=='to' else -.001)
     for j,k in enumerate(other):pt[k]=(lo[j]+hi[j])/2
     if any(all(o['from'][j]<pt[j]<o['to'][j] for j in range(3)) for o in es if o is not a and o is not b):continue
     bad.append([a['name'],b['name'],ax,side])
 return bad
def validate(w):
 k=setup();d=json.loads(k.skin_path(w).read_text());es=[e for p in d['parts'].values() for e in p];assert len(es)<=1000
 assert len({e['name'] for e in es})==len(es)
 conflicts=surface_conflicts(es);assert not conflicts,(w,conflicts)
 for e in es:
  assert all(-16<=e['from'][i]<e['to'][i]<=32 for i in range(3)),e['name']
  assert set(e['faces'])==set(k.FACE_AXES)
  for f in e['faces'].values():assert all(0<=v<=16 for v in f['uv']) and f['texture']=='#0'
 from PIL import Image
 im=Image.open(k.atlas_path(w));assert list(im.size)==d['texture_size'];assert max(im.size)<=1024
 report=dict(id=w,parse='PASS',strict_positive_boxes='PASS',unique_names='PASS',normalized_uv='PASS',actual_elements=len(es),parts={p:len(e) for p,e in d['parts'].items()},atlas=list(im.size),source_original_unchanged=json.loads((art(w)/'manifest.json').read_text())['original_blend_unchanged'],coplanar_exposed_pairs=len(conflicts),atlas_bytes=k.atlas_path(w).stat().st_size,skin_bytes=k.skin_path(w).stat().st_size,hud_bytes=k.hud_path(w).stat().st_size,native_pack_load='MASTER_PENDING',native_hand_ads_reload='MASTER_PENDING',native_10_20_display='MASTER_PENDING')
 (art(w)/'validation.json').write_text(json.dumps(report,indent=1)+'\n');print(w,'PASS',len(es),im.size)
def render(w):
 import tempfile
 k=setup();src=(ROOT/'scripts/art/w325/render_model.py').read_text()
 src=src.replace("co.rotation_euler = d_.to_track_quat('-Z', 'Y').to_euler(); cam.ortho_scale = ext", "co.rotation_euler = d_.to_track_quat('-Z', 'Y').to_euler(); M=co.rotation_euler.to_matrix().transposed(); pp=[M @ (mathutils.Vector(v)-c) for v in pts]; rw=max(v.x for v in pp)-min(v.x for v in pp); rh=max(v.y for v in pp)-min(v.y for v in pp); cam.ortho_scale=max(max(abs(v.x) for v in pp)*2,max(abs(v.y) for v in pp)*2*1200/700)*1.12")
 with tempfile.NamedTemporaryFile(mode='w',suffix='.py',prefix='w327-group2-render-',delete=False) as f:f.write(src);script=Path(f.name)
 try:
  out=art(w)/'review';out.mkdir(parents=True,exist_ok=True)
  subprocess.run([k.BLENDER,'--disable-autoexec','--factory-startup','-b','-t','2','--python',str(script),'--',str(out/w),str(k.skin_path(w)),str(k.atlas_path(w)),'west,east,top,q,front'],check=True)
 finally:script.unlink()
if __name__=='__main__':
 if '--blender-source' in sys.argv:evaluate(sys.argv[-1])
 else:
  k=setup();cmd=sys.argv[1];ids=sys.argv[2:] or IDS
  for w in ids:
   if cmd=='source':subprocess.run([k.BLENDER,'--disable-autoexec','-b',str(source(w)),'-t','2','--python',str(Path(__file__).resolve()),'--','--blender-source',w],check=True)
   elif cmd=='build':build(w)
   elif cmd=='render':render(w)
   elif cmd=='adscheck':adscheck(w)
   elif cmd=='contract':k.contract(w)
   elif cmd=='validate':validate(w)
