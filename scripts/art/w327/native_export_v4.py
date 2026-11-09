"""Bake authored planar polygons into native 26.3 cuboid faces with polygon alpha masks.
This extends the validated triangle-plane representation to planar polygon unions; holes stay alpha-clear.
All output uses standard from/to/rotation/faces fields. No vertices/mesh extension is emitted.
"""
import math,json,sys,importlib.util,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[3];spec=importlib.util.spec_from_file_location('kit',ROOT/'scripts/art/w325/kit.py');kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def mul(a,s):return tuple(x*s for x in a)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return mul(a,1/norm(a))
spec=importlib.util.spec_from_file_location('native',ROOT/'scripts/mesh/native_triangle_elements_w115.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
S=35.;OFFSET=(8.,7.6,8.)
def canonical(p):return (8-S*p[0],7.6+S*p[2],8+S*p[1])
def source(p):return ((8-p[0])/S,(p[2]-8)/S,(p[1]-7.6)/S)
def plane(rec):
 polys=[[canonical(v) for v in p] for p in rec['polygons']];allp=sum(polys,[])
 a,b=max([(p[i],p[(i+1)%len(p)]) for p in polys for i in range(len(p))],key=lambda q:norm(sub(q[1],q[0])));u=unit(sub(b,a))
 c=max(allp,key=lambda p:norm(cross(u,sub(p,a))))
 if norm(cross(u,sub(c,a)))<1e-9:return None
 n=unit(cross(u,sub(c,a)));v=unit(cross(n,u))
 coords=[[(dot(sub(p,a),u),dot(sub(p,a),v)) for p in poly] for poly in polys];minx=min(p[0] for poly in coords for p in poly);maxx=max(p[0] for poly in coords for p in poly);miny=min(p[1] for poly in coords for p in poly);maxy=max(p[1] for poly in coords for p in poly)
 origin=add(a,add(mul(u,minx),mul(v,miny)));w=maxx-minx;h=maxy-miny
 angles=native.euler_zyx(u,v,n);r=((0,0,0),list(zip('xyz',angles)))
 err=max(norm(sub(kit.rotate(basis,r),target)) for basis,target in [((1,0,0),u),((0,1,0),v),((0,0,1),n)])
 assert err<1e-7,(rec['name'],err,angles,u)
 p2=[[( (x-minx)/w, 1-(y-miny)/h) for x,y in poly] for poly in coords]
 projection_error=max(abs(dot(sub(actual,origin),n)) for poly in polys for actual in poly)
 vertex_error=max(norm(sub(add(origin,native.rotate((x-minx,y-miny,0),angles)),add(origin,add(mul(u,x-minx),mul(v,y-miny))))) for poly in coords for x,y in poly)
 assert vertex_error<1e-7,(rec['name'],vertex_error)
 assert projection_error<.001,(rec['name'],projection_error)
 return dict(projection_error=projection_error,vertex_error=vertex_error,name=rec['name'],origin=origin,u=u,v=v,n=n,w=w,h=h,polygons=p2,angles=angles,basis_error=err)
def color_for(w,name):
 if '/mag_' in name:return (80,84,88)
 if name.startswith('V4/grip'):
  return (71,65,49) if w=='igneous_hammer' else (30,34,37) if w=='eyasluna' else (209,200,173)
 if w=='nation_of_beasts':return (216,207,179) if 'trigger/' not in name else (73,76,78)
 if w=='eyasluna':return (165,42,44) if name.startswith('V4/barrel/shaped') else (73,82,88)
 return (62,59,56) if 'shell/' in name else (83,84,81)
def build(w):
 out=ROOT/'art/weapons/w327'/w/'v4';records=json.loads((out/'native_planes.json').read_text());faces=[p for rec in records if (p:=plane(rec)) is not None];assert len(faces)<=1000
 cache=out/'source_bake';man=json.loads((cache/'manifest.json').read_text());views={n:kit.View(cache,n,man) for n in man['views']}
 T=40;A=1024;jobs=[]
 for i,p in enumerate(faces):jobs.append((max(3,math.ceil(p['h']*T)),max(3,math.ceil(p['w']*T)),i,p))
 atlas=Image.new('RGBA',(A,A));neutral=Image.new('RGBA',(A,A));elements=[];x=y=2;row=0;coverage=[]
 for h,ww,ix,p in sorted(jobs,key=lambda j:-j[0]):
  if x+ww+4>A:x=2;y+=row+4;row=0
  assert y+h+4<A,(w,'atlas overflow',y,h)
  mask_hi=Image.new('L',(ww*4,h*4));draw=ImageDraw.Draw(mask_hi)
  for poly in p['polygons']:draw.polygon([(u*ww*4-.5,v*h*4-.5) for u,v in poly],fill=255)
  mask=mask_hi.resize((ww,h),Image.Resampling.BOX).point(lambda a:255 if a else 0).filter(ImageFilter.MaxFilter(3))
  # Conservative pixel-footprint coverage prevents cracks between adjacent alpha planes.
  # Genuine bores and negative spaces stay clear; no full rectangular substitution.
  pix=mask.load();tile=Image.new('RGBA',(ww,h));tp=tile.load();base=color_for(w,p['name']);normal=(-p['n'][0],p['n'][2],p['n'][1]);ax=max(range(3),key=lambda a:abs(normal[a]));view=views[('p' if normal[ax]>0 else 'n')+'xyz'[ax]]
  for px in range(ww):
   for py in range(h):
    if not pix[px,py]:continue
    # Mask coordinates and material projection share exactly the same 3D basis.
    point=add(p['origin'],add(mul(p['u'],(px+.5)/ww*p['w']),mul(p['v'],(1-(py+.5)/h)*p['h'])));wp=source(point);uu,vv=view.project(wp);rgb=view.sample(uu,vv);depth=view.depth_at(uu,vv)
    if rgb is None or depth is None or abs(depth-dot(wp,view.d))>.014:rgb=base
    if w=='nation_of_beasts':
     if '/mag_' in p['name']:rgb=base
     elif max(rgb)-min(rgb)>70 or sum(rgb)<200:rgb=base
    if w=='eyasluna' and not p['name'].startswith('V4/barrel/shaped') and max(rgb)-min(rgb)>70:rgb=base
    tp[px,py]=tuple(max(0,min(255,round(rgb[j]*.94+base[j]*.06+3))) for j in range(3))+(255,)
  # Source motifs stay spatially continuous; restricted local palette removes fine random grain.
  quant=tile.convert('RGB').quantize(colors=32,method=Image.Quantize.MEDIANCUT).convert('RGBA');quant.putalpha(mask);atlas.paste(quant,(x,y))
  nt=Image.new('RGBA',(ww,h),(128,138,143,255));nt.putalpha(mask);neutral.paste(nt,(x,y))
  center=add(p['origin'],add(mul(p['u'],p['w']/2),mul(p['v'],p['h']/2)));a=sub(center,(p['w']/2,p['h']/2,0));b=add(center,(p['w']/2,p['h']/2,0));uv=[x/A*16,y/A*16,(x+ww)/A*16,(y+h)/A*16]
  assert all(-16<=c<=32 for xyz in [a,b] for c in xyz)
  elements.append({'name':p['name']+'/surface'+str(ix),'from':list(a),'to':list(b),'rotation':{'origin':list(center),**dict(zip('xyz',p['angles']))},'faces':{'south':{'uv':uv,'texture':'#0'},'north':{'uv':[uv[2],uv[1],uv[0],uv[3]],'texture':'#0'}}})
  coverage.append({'name':p['name'],'opaque_pixels':sum(1 for c in mask.getdata() if c),'island_pixels':ww*h})
  x+=ww+4;row=max(row,h)
 skin={'texture_size':[A,A],'no_overlay':True,'parts':{'body':[e for e in elements if '/mag_' not in e['name']],'magazine':[e for e in elements if '/mag_' in e['name']]}}
 (out/'native_skin.json').write_text(json.dumps(skin,separators=(',',':'))+'\n');atlas.save(out/'native_atlas.png');neutral.save(out/'native_neutral.png')
 report={'degenerate_zero_area_planes_discarded':len(records)-len(faces),'elements':len(elements),'parts':{p:len(es) for p,es in skin['parts'].items()},'atlas':[A,A],'texels_per_model_px':T,'atlas_rows_used':y+row,'max_group_plane_projection_px':max(p['projection_error'] for p in faces),'max_reconstructed_polygon_vertex_error':max(p['vertex_error'] for p in faces),'max_rotation_basis_error':max(p['basis_error'] for p in faces),'native_fields':'standard zero-depth cuboid with two mirrored faces; polygon union alpha mask','alpha_islands':coverage,'source_to_canonical_matrix':[[-35,0,0,8],[0,0,35,7.6],[0,35,0,8],[0,0,0,1]],'uniform_scale':35,'acceptance':'offline native geometry/alpha comparison pending; in-game pending master'}
 (out/'native_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(w,len(elements),'native elements','atlas rows',y+row,'basis max',report['max_rotation_basis_error'],flush=True)
if __name__=='__main__':
 for w in sys.argv[1:]:build(w)
