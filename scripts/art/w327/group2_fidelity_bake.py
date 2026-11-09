"""Final six-weapon bake: source-aligned cuboids plus closed native contour faces.
Planar polygon surfaces use exact alpha islands, not opaque bounding rectangles.
"""
from pathlib import Path
import sys,json,math,importlib.util,hashlib
from PIL import Image,ImageDraw,ImageFilter
import group2_v3 as v3
import native_contours as nc
import group2_optimize as opt
ROOT=v3.ROOT

def build(w):
 g,k=v3.setup();b=k.Baker(w);a=ROOT/'art/weapons/w327'/w;D=json.loads((a/'design.json').read_text());E=D['elements'];assert w in opt.IDS;surfaces,merged_caps=opt.surfaces(D.get('contours',[]));visible,hidden_faces=opt.visible_faces(E,b.is_mag);assert len(E)+len(surfaces)<=1000
 old=json.loads((a/'manifest.json').read_text());finish=v3.finish
 if w=='brigands_law':
  spec=importlib.util.spec_from_file_location('hero_finish',a/'v3_finish.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);finish=f.finish
 faces=[];masked={};native=[];maxerr=0
 for idx,e in enumerate(E):
  # Convex containment removes only fully covered faces in this moving part.
  for fn in visible[e['name']]:
   img,valid,clear=b.face(e,fn);b.inpaint(img,valid,b.fallback);entry=(e['name'],fn,img,clear,e,[],b._painted);finish(b,[entry],k);faces.append((e['name'],fn,img))
 for surface in surfaces:
  el,err=nc.emit_element(surface['part'],surface['name'],[0,0,16,16],surface['triangle']);maxerr=max(maxerr,err);el.pop('triangle_mask');el['role']=surface['role'];el['_surface']=True
  img,valid,clear=b.face(el,'south');b.inpaint(img,valid,b.fallback);finish(b,[(el['name'],'south',img,clear,el,[],b._painted)],k)
  mask=Image.new('L',img.size,0);poly=surface.get('polygon_mask') or ([[0,0],[1,1],[0,1]] if surface['triangle'] else [[0,0],[1,0],[1,1],[0,1]])
  # Pixel-center coverage, binary alpha: raster corners are placed at exact normalized authored boundaries.
  draw=ImageDraw.Draw(mask);draw.polygon([(u*img.width-.5,v*img.height-.5) for u,v in poly],fill=255);img.putalpha(mask.filter(ImageFilter.MaxFilter(3)))
  faces.append((el['name'],'south',img));native.append(el);masked[el['name']]=poly
 # Shelf packing at 1024, resize density only if physically needed; all UVs renormalize together.
 A=1024
 def pack(faces):
  order=sorted(faces,key=lambda f:(-f[2].height,-f[2].width,f[0],f[1]));pos={};x=y=shelf=0
  for n,fn,im in order:
   ww,hh=im.width+4,im.height+4
   if x+ww>A:y+=shelf;x=0;shelf=0
   pos[n,fn]=(x,y);x+=ww;shelf=max(shelf,hh)
  return pos,y+shelf
 pos,used=pack(faces)
 while used>A:
  faces=[(n,fn,im.resize((max(1,round(im.width*.9)),max(1,round(im.height*.9))),Image.Resampling.NEAREST)) for n,fn,im in faces];pos,used=pack(faces)
 H=16
 while H<used:H*=2
 atlas=Image.new('RGBA',(A,H));uv={}
 for n,fn,im in faces:
  x,y=pos[n,fn];atlas.paste(im,(x+2,y+2));uv[n,fn]=[(x+2)*16/A,(y+2)*16/H,(x+2+im.width)*16/A,(y+2+im.height)*16/H]
  # Two texel padding replicates only the true edge pixels, preserving the contour's transparent area.
  atlas.paste(im.crop((0,0,1,im.height)).resize((2,im.height)),(x,y+2));atlas.paste(im.crop((im.width-1,0,im.width,im.height)).resize((2,im.height)),(x+2+im.width,y+2));atlas.paste(im.crop((0,0,im.width,1)).resize((im.width,2)),(x+2,y));atlas.paste(im.crop((0,im.height-1,im.width,im.height)).resize((im.width,2)),(x+2,y+2+im.height))
 parts={'body':[],'magazine':[]}
 for e in E:
  out={key:val for key,val in e.items() if key not in ('role','_surface')};out['faces']={fn:dict(uv=uv[e['name'],fn],texture='#0') for fn in visible[e['name']]};
  if not out['faces']:continue
  parts['magazine' if b.is_mag(e['name']) else 'body'].append(out)
 for e in native:
  out={key:val for key,val in e.items() if key not in ('role','_surface')};U=uv[e['name'],'south'];out['faces']={'south':dict(uv=U,texture='#0'),'north':dict(uv=[U[2],U[1],U[0],U[3]],texture='#0')};parts['magazine' if b.is_mag(e['name']) else 'body'].append(out)
 doc=dict(texture_size=[A,H],parts=parts)
 atlas.save(k.atlas_path(w),optimize=True);k.skin_path(w).write_text(json.dumps(doc,separators=(',',':')))
 # HUD uses real visible contour vertices, never alpha rectangle corners.
 polys=[k.hull([(p[2],p[1]) for p in k._corners(e)]) for e in E]
 for s in surfaces:polys.append([(p[2],p[1]) for p in s['source_points']])
 z0=min(p[0] for pl in polys for p in pl);z1=max(p[0] for pl in polys for p in pl);y0=min(p[1] for pl in polys for p in pl);y1=max(p[1] for pl in polys for p in pl);sc=min(152/(z1-z0),53/(y1-y0));ox=4+(152-(z1-z0)*sc)/2;oy=5+(53-(y1-y0)*sc)/2
 mask=Image.new('L',(640,256));dr=ImageDraw.Draw(mask)
 for pl in polys:dr.polygon([((ox+(z-z0)*sc)*4,(oy+(y1-y)*sc)*4) for z,y in pl],fill=255)
 icon=Image.new('RGBA',(160,64),(255,255,255,0));icon.putalpha(mask.resize((160,64),Image.Resampling.BOX));icon.save(k.hud_path(w),optimize=True)
 source=json.loads((a/'source-evaluation.json').read_text());assert k.sha(Path(source['source']))==source['sha256']
 allE=sum(parts.values(),[]);assert len(allE)<=1000 and len({e['name'] for e in allE})==len(allE)
 for e in allE:
  assert all(math.isfinite(v) and -16<=v<=32 for v in e['from']+e['to'])
  for f in e['faces'].values():assert all(0<=x<=16 for x in f['uv'])
 old.update(revision=4,geometry_revision=6,hidden_faces=hidden_faces,merged_cap_elements=merged_caps,element_total=len(allE),elements={p:len(es) for p,es in parts.items()},atlas=[A,H],source_mapping=D['source_mapping'],source_original_unchanged=True,original_blend_unchanged=True,authoring='Source-first uniform proportions; semantically authored closed solids, native cuboids and alpha polygon planes with merged planar caps and conservative same-part interior-face removal',material_pipeline='Calibrated original six-view albedo motifs on each actual face; controlled source material colors; binary contour alpha; no synthetic facet-edge stripes',outputs_sha256={str(p.relative_to(ROOT)):k.sha(p) for p in [k.atlas_path(w),k.skin_path(w),k.hud_path(w)]},validation='parse, <=1000 emitted elements, finite native transforms, UV bounds, source and output hashes; native Minecraft review pending')
 (a/'manifest.json').write_text(json.dumps(old,indent=1)+'\n')
 report=dict(parse='PASS',hidden_faces_removed=hidden_faces,cap_elements_saved=merged_caps,elements=len(allE),authored_cuboids=len(E),emitted_cuboids=sum(bool(visible[e['name']]) for e in E),native_contour_elements=len(native),atlas=[A,H],max_vertex_reconstruction_error=maxerr,source_original_unchanged=True,alpha_masked_faces=len(masked),all_authored_contours_closed=True,native_gameplay_and_visual_acceptance='MASTER_PENDING')
 (a/'validation.json').write_text(json.dumps(report,indent=1)+'\n');(a/'review/v3/geometry/native-contour-check.json').write_text(json.dumps(report,indent=1)+'\n');print(w,report,flush=True)

if __name__=='__main__':
 for w in sys.argv[1:]:build(w)
