#!/usr/bin/env python3
"""W118 Hammerhead r5: source-fitted rotated panels and clean source palette.

Pure bundled Python regeneration. design.json contains explicit native geometry,
source component provenance and baked source albedo. --verify is read-only.
Native element rotations use Rz*Ry*Rx, NOT ItemTransform's XYZ convention.
"""
import argparse,base64,copy,hashlib,io,itertools,json,math,uuid,zlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
ART='art/weapons/w115/hammerhead/'
ASSET='src/main/resources/assets/destiny/'
GENERATOR='scripts/generate_surface_w115_hammerhead.py'
TEST='scripts/qa/test_surface_w115_hammerhead.py'
WORKER='docs/qa/2026-10-25/w118/hammerhead-worker.md'
TEXTURE=ASSET+'textures/item/weapon/w115/hammerhead.png'
PARTS=('body','magazine','cover')
MODEL_PATHS={p:ASSET+f'models/weapon_surface_w115/hammerhead_{p}.json' for p in PARTS}
OWNED={GENERATOR,TEST,ART+'design.json',ART+'manifest.json',ART+'review.md',ART+'inspection.bbmodel',ART+'comparison.png',WORKER,TEXTURE,*MODEL_PATHS.values()}
GENERATED={TEXTURE,*MODEL_PATHS.values(),ART+'inspection.bbmodel',ART+'comparison.png',ART+'manifest.json'}
FACES={'north':(3,2,0,1),'south':(6,7,5,4),'west':(2,6,4,0),'east':(7,3,1,5),'up':(2,3,7,6),'down':(4,5,1,0)}
NORMALS={'north':(0,0,-1),'south':(0,0,1),'west':(-1,0,0),'east':(1,0,0),'up':(0,1,0),'down':(0,-1,0)}

def encode(v):return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',optimize=False);return b.getvalue()
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'destiny:w118:hammerhead:r5:'+s))
def rotation(r):
 x,y,z=[math.radians(r.get(a,0)) for a in 'xyz'];cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def vertices(e):
 v=np.array([[e['to' if mask>>a&1 else 'from'][a] for a in range(3)] for mask in range(8)])
 if 'rotation' in e:
  o=np.array(e['rotation']['origin']);v=(v-o)@rotation(e['rotation']).T+o
 return v

def source(d):return json.loads(zlib.decompress(base64.b64decode(d['source_reference_zlib_base64'])))
def source_images(d):return {int(i):np.asarray(Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA')) for i,data in d['source_albedo_png_base64'].items()}
def verify_pins(d):
 for p,h in d['input_sha256'].items():
  if sha((ROOT/p).read_bytes())!=h:raise ValueError('Original reference drift: '+p)
 for p,h in d['raw_input_sha256'].items():
  if sha(Path(p).read_bytes())!=h:raise ValueError('Raw source drift: '+p)

def closest(points,triangles):
 """Exact point/triangle closest barycentrics, independent of original grid."""
 tv=np.asarray(triangles);a=tv[:,0];ab=tv[:,1]-a;ac=tv[:,2]-a
 d00=(ab*ab).sum(1);d01=(ab*ac).sum(1);d11=(ac*ac).sum(1);den=d00*d11-d01*d01
 result=[];bary=[];dist=[]
 for start in range(0,len(points),48):
  p=np.asarray(points[start:start+48]);q=p[:,None,:]-a[None,:,:]
  d20=np.einsum('bti,ti->bt',q,ab);d21=np.einsum('bti,ti->bt',q,ac)
  vb=(d11*d20-d01*d21)/np.maximum(den,1e-30);vc=(d00*d21-d01*d20)/np.maximum(den,1e-30);va=1-vb-vc
  weights=np.stack((va,vb,vc),axis=-1);project=a[None]+vb[...,None]*ab+vc[...,None]*ac
  best=((project-p[:,None])**2).sum(-1);inside=(va>=0)&(vb>=0)&(vc>=0)&(den>1e-20);best=np.where(inside,best,np.inf)
  for ia,ib in ((0,1),(1,2),(2,0)):
   u,v=tv[:,ia],tv[:,ib];edge=v-u;param=np.clip(np.einsum('bti,ti->bt',p[:,None]-u,edge)/np.maximum((edge*edge).sum(1),1e-30),0,1)
   projected=u+param[...,None]*edge;dd=((projected-p[:,None])**2).sum(-1);take=dd<best
   ew=np.zeros_like(weights);ew[:,:,ia]=1-param;ew[:,:,ib]=param;weights=np.where(take[...,None],ew,weights);best=np.minimum(best,dd)
  ix=best.argmin(1);rows=np.arange(len(p));result.extend(ix.tolist());bary.extend(weights[rows,ix].tolist());dist.extend(np.sqrt(best[rows,ix]).tolist())
 return np.array(result),np.array(bary),np.array(dist)

def compile_models(d,records):
 # Authored palette tiles only: no nearest-point source texture projection.
 size=d['atlas']['size'];tile=d['atlas']['tile_size'];gutter=d['atlas']['gutter'];atlas=np.zeros((size,size,4),dtype='uint8');islands={}
 for i,(material,color) in enumerate(d['palette'].items()):
  for kind in ('solid','triangle','grip'):
   slot=i*3+('solid','triangle','grip').index(kind);step=tile+2*gutter;x=(slot%7)*step+gutter;y=(slot//7)*step+gutter
   pixels=np.zeros((tile,tile,4),dtype='uint8');pixels[:,:,:3]=color;pixels[:,:,3]=255
   if kind=='triangle':
    u,v=np.meshgrid((np.arange(tile)+.5)/tile,(np.arange(tile)+.5)/tile);pixels[:,:,3]=np.where(u<=v,255,0)
   if kind=='grip':
    for row in (28,52,76,100):pixels[row:row+2,12:-12,:3]=np.maximum(np.array(color)-5,0)
   atlas[y-gutter:y+tile+gutter,x-gutter:x+tile+gutter]=np.pad(pixels,((gutter,gutter),(gutter,gutter),(0,0)),mode='edge')
   islands[material,kind]=[v*16/size for v in (x,y,x+tile,y+tile)]
 models={}
 for part,specs in d['parts'].items():
  elements=[]
  for spec in specs:
   e=copy.deepcopy(spec['geometry']);mat=spec['material']
   if spec['kind']=='triangle_plane':
    uv=islands[mat,'triangle'];e['faces']={'south':{'uv':uv,'texture':'#0'},'north':{'uv':[uv[2],uv[1],uv[0],uv[3]],'texture':'#0'}}
   else:
    uv=islands[mat,'grip' if mat=='rubber' else 'solid'];e['faces']={face:{'uv':uv,'texture':'#0'} for face in spec.get("visible_faces",FACES)}
   elements.append(e)
  models[part]={'credit':'W118 Hammerhead R5 source-fitted segmented rotated panels; clean authored source palette','textures':{'0':'destiny:item/weapon/w115/hammerhead','particle':'destiny:item/weapon/w115/hammerhead'},'elements':elements}
 return Image.fromarray(atlas),models

def inspection(d,models,atlas):
 elements=[];groups=[]
 for part,m in models.items():
  children=[]
  for e in m['elements']:
   item=copy.deepcopy(e);item.update(type='cube',uuid=uid(e['name']),box_uv=False,origin=[8,8,8])
   if 'rotation' in item:
    r=item.pop('rotation');item['origin']=r['origin'];item['rotation']=[r[a] for a in 'xyz']
   for f in item['faces'].values():f['texture']=0;f['uv']=[v*d['atlas']['size']/16 for v in f['uv']]
   # BB requires all editor face slots, including disabled sides on contour cards.
   for face in FACES:item['faces'].setdefault(face,{'uv':[0,0,0,0],'texture':None})
   elements.append(item);children.append(item['uuid'])
  groups.append({'name':part,'uuid':uid('group:'+part),'origin':d[part+'_pivot'],'rotation':[0,0,0],'children':children,'export':True})
 return {'meta':{'format_version':'4.10','model_format':'java_block','box_uv':False},'name':'Hammerhead W118 R5 source-fitted panels','resolution':{'width':d['atlas']['size'],'height':d['atlas']['size']},'elements':elements,'outliner':groups,'textures':[{'name':'hammerhead.png','id':'0','uuid':uid('texture'),'width':d['atlas']['size'],'height':d['atlas']['size'],'uv_width':d['atlas']['size'],'uv_height':d['atlas']['size'],'source':'data:image/png;base64,'+base64.b64encode(png(atlas)).decode()}],'destiny_w115':{'revision':'r5','nativeAccepted':False,'rotationOrder':'RzRyRx','coverPivot':d['cover_pivot']}}

def model_triangles(models,tex,d,opened=False):
 result=[];img=np.asarray(tex.convert('RGBA'))
 for part,m in models.items():
  for e in m['elements']:
   v=vertices(e);rot=rotation(e.get('rotation',{}))
   if opened and part=='cover':
    pivot=np.array(d['cover_pivot']);turn=rotation({'x':-92});v=(v-pivot)@turn.T+pivot;rot=turn@rot
   if opened and part=='magazine':v+=np.array([-2.8,-5.2,.8])
   for name,f in e['faces'].items():
    pts=v[list(FACES[name])];normal=rot@np.array(NORMALS[name]);u0,v0,u1,v1=f['uv'];uv=np.array([[u0,v0],[u1,v0],[u1,v1],[u0,v1]])/16
    for ix in ((0,1,2),(0,2,3)):result.append((pts[list(ix)],uv[list(ix)],img,normal))
 return result

def raw_triangles(records,images,d,opened=False):
 out=[]
 for t in records:
  v=np.array(t['points']);uv=np.array(t['uv']);uv[:,1]=1-uv[:,1]
  if opened and t['part']=='cover':
   pivot=np.array(d['cover_pivot']);v=(v-pivot)@rotation({'x':-92}).T+pivot
  if opened and t['part']=='magazine':v+=np.array([-2.8,-5.2,.8])
  n=np.cross(v[1]-v[0],v[2]-v[0]);length=np.linalg.norm(n)
  if length<1e-10:continue
  out.append((v,uv,images[t['albedo']],n/length))
 return out

def render(triangles,camera,extent,viewport,raw=False):
 width,height=viewport;cam=np.array(camera,dtype=float);cam/=np.linalg.norm(cam);right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right);center,scale=extent
 yy=np.linspace(0,1,height)[:,None,None];bg=np.broadcast_to(np.array([31,39,48])[None,None,:]*(1-yy)+np.array([20,26,34])[None,None,:]*yy,(height,width,3)).copy();depth=np.full((height,width),-np.inf)
 light=np.array([-.55,.8,-.35]);light/=np.linalg.norm(light)
 for p,uv,texture,normal in triangles:
  facing=normal@cam
  if not raw and facing<-1e-8:continue
  n=normal if facing>=0 else -normal
  screen=np.column_stack(((p@right-center[0])*scale+width/2,height/2-(p@up-center[1])*scale));z=p@cam;a,b,c=screen
  x0=max(0,int(math.floor(screen[:,0].min())));x1=min(width-1,int(math.ceil(screen[:,0].max())));y0=max(0,int(math.floor(screen[:,1].min())));y1=min(height-1,int(math.ceil(screen[:,1].max())))
  if x1<x0 or y1<y0:continue
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-10:continue
  gx,gy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);wa=((b[1]-c[1])*(gx-c[0])+(c[0]-b[0])*(gy-c[1]))/den;wb=((c[1]-a[1])*(gx-c[0])+(a[0]-c[0])*(gy-c[1]))/den;wc=1-wa-wb
  zz=wa*z[0]+wb*z[1]+wc*z[2];uvw=wa[...,None]*uv[0]+wb[...,None]*uv[1]+wc[...,None]*uv[2]
  th,tw=texture.shape[:2];tx=np.clip((uvw[...,0]*tw).astype(int),0,tw-1);ty=np.clip((uvw[...,1]*th).astype(int),0,th-1);sample=texture[ty,tx]
  visible=(wa>=-1e-7)&(wb>=-1e-7)&(wc>=-1e-7)&(zz>=depth[y0:y1+1,x0:x1+1])&(sample[:,:,3]>=128)
  shade=.48+.52*max(0,float(n@light));bg[y0:y1+1,x0:x1+1][visible]=(sample[:,:,:3]*shade)[visible];depth[y0:y1+1,x0:x1+1][visible]=zz[visible]
 return Image.fromarray(np.clip(bg,0,255).astype('uint8')),np.isfinite(depth)

def comparison(d,records,atlas,models):
 images=source_images(d);history=[d[k] for k in ('rejected_r1','frozen_r2','frozen_r3','frozen_r4')];textures=[Image.open(io.BytesIO(base64.b64decode(v['texture_png']))) for v in history];w,h=760,300
 rows=[('PROFILE',[-1,.12,-.015],False),('FRONT THREE-QUARTER',[-1,.6,-.65],False),('REAR THREE-QUARTER',[1,.55,.55],False),('HIGH / TOP: shroud and cover contour',[.17,1,.1],False),('ADS AXIS / rear-to-muzzle orthographic',[0,.19,1],False),('OPEN COVER / FEED REMOVED / relative W114 p=.48',[-1,.48,-.4],True),('DRUM CAPS ONLY / rear axial: contour and alpha seams',[0,.001,1],False),('DRUM CAPS ONLY / oblique: opaque rim and bevel joins',[.5,.4,1],False)]
 sheet=Image.new('RGB',(6*w,8*h+100),'#141c26');draw=ImageDraw.Draw(sheet);draw.text((16,10),'HAMMERHEAD R5 | OFFLINE TEXTURED + REAL ALPHA | original / rejected R1 / R2 / fitting-failed R3 / frozen R4 / R5 opaque original-ring caps',fill='#edf1f5')
 for col,title in enumerate(('ORIGINAL RAW:25,499 triangles','REJECTED R1:86 broad boxes','FROZEN REJECTED R2:1,635 elements','FITTING-FAILED R3:1,289 elements','FROZEN R4:1,305 elements',f'R5:{sum(len(m["elements"]) for m in models.values())} elements')):draw.text((col*w+16,34),title,fill='#e4d8cd')
 metrics={};details={};cap_names={s['name'] for ss in d['parts'].values() for s in ss if s['component'] in (45,46,47,48)};old_cap_names={s['name'] for s in d['r5_previous_cap_specs']}
 for row,(label,cam,opened) in enumerate(rows):
  rr=records;hist=history;current=models
  if row>=6:
   rr=[t for c in d['components'][45:49] for i in c['source_indices'] for t in [records[i]]]
   hist=[{'models':{p:dict(m,elements=[e for e in m['elements'] if e['name'] in old_cap_names]) for p,m in v['models'].items()}} for v in history]
   current={p:dict(m,elements=[e for e in m['elements'] if e['name'] in cap_names]) for p,m in models.items()}
  arrays=[raw_triangles(rr,images,d,opened),*[model_triangles(v['models'],tex,d,opened) for v,tex in zip(hist,textures)],model_triangles(current,atlas,d,opened)]
  camera=np.array(cam,dtype=float);camera/=np.linalg.norm(camera);right=np.cross([0,1,0],camera);right/=np.linalg.norm(right);up=np.cross(camera,right)
  ps=np.concatenate([t[0] for t in arrays[0]]);projection=np.column_stack((ps@right,ps@up));lo,hi=projection.min(0),projection.max(0);center=(lo+hi)/2;scale=min((w-65)/(hi[0]-lo[0]),(h-55)/(hi[1]-lo[1]));masks=[];rendered=[]
  for col,tris in enumerate(arrays):
   im,mask=render(tris,cam,(center,scale),(w,h),raw=col==0);sheet.paste(im,(col*w,60+row*h));masks.append(mask);rendered.append(np.asarray(im))
   if row>=6 and col in (1,2):draw.text((col*w+15,90+row*h),'Component IDs differ in R1/R2; see whole-model rows above',fill='#c7cdd5')
  def iou(a,b):return float(np.count_nonzero(a&b)/max(np.count_nonzero(a|b),1))
  item={'view':label,'source_pixels':int(masks[0].sum())};interior=masks[0].copy()
  for dx,dy in ((0,2),(0,-2),(2,0),(-2,0)):interior &= np.roll(masks[0],(dy,dx),(0,1))
  for col,key in enumerate(('r1','r2','r3','r4','r5'),1):
   item[key+'_iou']=iou(masks[0],masks[col]);item[key+'_missing_source_pixels']=int((masks[0]&~masks[col]).sum());item[key+'_interior_missing_pixels']=int((interior&~masks[col]).sum());item[key+'_opaque_black_mismatch_pixels']=int((masks[0]&masks[col]&(rendered[0].max(2)>30)&(rendered[col].max(2)<22)).sum())
  (metrics if row<6 else details)[str(row if row<6 else row-6)]=item;draw.text((12,66+row*h),label,fill='#edf1f5');draw.text((5*w+12,66+row*h),f'IoU {item["r5_iou"]:.3f} | interior missing {item["r5_interior_missing_pixels"]}',fill='#ffdfad')
  for col in range(1,6):draw.line((w*col,60+row*h,w*col,60+(row+1)*h),fill='#7e8793',width=1)
 draw.text((12,sheet.height-25),'OFFLINE ONLY | no native acceptance | frozen historical comparisons retained | original frame, components, belt and W114 pivots unchanged',fill='#c7cdd5')
 return png(sheet),metrics,details

def spatial_metrics(d,records,models):
 bycomp={i:[] for i in range(len(d['components']))};specs={s['name']:s for ss in d['parts'].values() for s in ss}
 for m in models.values():
  for e in m['elements']:bycomp[specs[e['name']]['component']].append(e)
 result={}
 for cid,c in enumerate(d['components']):
  raw=np.array([records[i]['points'] for i in c['source_indices']]);points=[];tri=[]
  for e in bycomp[cid]:
   spec=specs[e['name']]
   if spec['kind']=='triangle_plane':points.extend(spec['triangle_vertices']);tri.append(spec['triangle_vertices'])
   else:
    vv=vertices(e);points.extend(vv)
    for face in e["faces"]:
     ix=FACES[face]
     p=vv[list(ix)];points.append(p.mean(0));tri.extend((p[[0,1,2]].tolist(),p[[0,2,3]].tolist()))
  if not points:raise ValueError('Empty source component '+c['name'])
  pts=np.array(points);out=closest(pts,raw)[2];src=raw.reshape(-1,3);coverage=closest(src,np.array(tri))[2];bounds=np.array(c['bounds']);over=np.maximum(bounds[0]-pts,pts-bounds[1]);envelope=float(max(0,over.max()))
  result[str(cid)]={'component':c['name'],'elements':len(bycomp[cid]),'output_to_source_max':float(out.max()),'output_to_source_p95':float(np.quantile(out,.95)),'source_to_output_max':float(coverage.max()),'source_to_output_p95':float(np.quantile(coverage,.95)),'source_envelope_protrusion':envelope}
 return result

def generate():
 d=json.loads((ROOT/(ART+'design.json')).read_bytes());verify_pins(d);
 for p,h in d['r2_input_sha256'].items():
  if sha((ROOT/p).read_bytes())!=h:raise ValueError('Frozen R2 input drift: '+p)
 records=source(d);atlas,models=compile_models(d,records);comp,metrics,details=comparison(d,records,atlas,models)
 outputs={TEXTURE:png(atlas),ART+'inspection.bbmodel':encode(inspection(d,models,atlas)),ART+'comparison.png':comp,**{MODEL_PATHS[p]:encode(m) for p,m in models.items()}}
 hashes={p:sha(v) for p,v in outputs.items()}
 for p in sorted(OWNED-GENERATED):hashes[p]=sha((ROOT/p).read_bytes())
 counts={p:len(m['elements']) for p,m in models.items()};planes=sum(s['kind']=='triangle_plane' for specs in d['parts'].values() for s in specs);cubes=sum(counts.values())-planes
 actual=np.concatenate([np.array(s['triangle_vertices']) if s['kind']=='triangle_plane' else vertices(s['geometry']) for ss in d['parts'].values() for s in ss])
 manifest={'stage':'W118','revision':'r5','id':'hammerhead','part_counts':counts,'native_elements':sum(counts.values()),'alpha_triangle_planes':planes,'oriented_cuboids':cubes,'emitted_faces':sum(len(e['faces']) for m in models.values() for e in m['elements']),'source_triangles':len(records),'source_components':len(d['components']),'retained_source_components':len({s['component'] for specs in d['parts'].values() for s in specs}),'source_fitted_cuboids':cubes,'body_cover_triangle_planes':sum(s['kind']=='triangle_plane' for p,ss in d['parts'].items() if p!='magazine' for s in ss),'bounds':d['expected_bounds'],'actual_surface_bounds':[actual.min(0).tolist(),actual.max(0).tolist()],'bounds_policy':'bounds is the immutable original frame; independently check actual_surface_bounds within .02 and each original component envelope within .02.','review_budget':{'elements':2048,'faces':6144,'scope':'Master-reviewed Hammerhead budget, retained for R5; not an engine limit or measured performance acceptance.'},'cover_pivot':d['cover_pivot'],'rotation_order':'RzRyRx','fidelity_iou':metrics,'drum_detail_comparison':details,'spatial_deviation':spatial_metrics(d,records,models),'palette':d['palette'],'atlas_gutter':d['atlas']['gutter'],'r4_corrections':d['r4_corrections'],'r3_negative_control_spatial':d['frozen_r3']['spatial_deviation'],'frozen_r2_sha256':d['r2_input_sha256'],'changed_paths':sorted(OWNED),'output_sha256':dict(sorted(hashes.items())),'hash_policy':'All 11 other owned paths hashed; manifest self hash in external export inventory.','input_sha256':d['input_sha256'],'raw_input_sha256':d['raw_input_sha256'],'compiler_reference':d['compiler_reference'],'texture_size':[d['atlas']['size'],d['atlas']['size']],'native_accepted':False,'aesthetic_final':False,'r5_drum_refinement':d['r5_drum_refinement'],'surface_coherence_status':'R5 original-ring opaque drum shells; offline and native review remain distinct, no aesthetic-final acceptance.','limitations':d['limitations']}
 outputs[ART+'manifest.json']=encode(manifest);assert set(outputs)==GENERATED
 return outputs

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args();outputs=generate()
 for p,data in outputs.items():
  dest=ROOT/p
  if args.verify:
   if not dest.is_file() or dest.read_bytes()!=data:raise SystemExit('Generated drift: '+p)
  else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 m=json.loads(outputs[ART+'manifest.json']);print(('Verified' if args.verify else 'Generated')+f' 7 deterministic outputs; r5 {m["native_elements"]} elements / {m["emitted_faces"]} faces; {m["retained_source_components"]} source groups retained; IoU '+json.dumps(m['fidelity_iou']))
if __name__=='__main__':main()
