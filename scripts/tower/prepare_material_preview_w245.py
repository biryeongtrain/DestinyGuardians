from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/tower'))
from tower_mesh import GLB
from material_shader_w245 import MaterialBaker

def prepare(source,materials,out):
 out.mkdir(parents=True,exist_ok=True);g=GLB(source);b=MaterialBaker(materials,allow_representative=True);bounds={}
 for mi in set(n['mesh']for n in g.doc['nodes']):
  if g.doc['meshes'][mi].get('extras',{}).get('terrain'):raise ValueError('Terrain UV contract unsupported')
  for prim in g.doc['meshes'][mi]['primitives']:
   if 'TEXCOORD_0' not in prim['attributes']:continue
   tag=g.doc['materials'][prim['material']]['name'];uv=g.accessor(prim['attributes']['TEXCOORD_0']);lo,hi=uv.min(0),uv.max(0)
   if tag in bounds:bounds[tag]=[np.minimum(bounds[tag][0],lo),np.maximum(bounds[tag][1],hi)]
   else:bounds[tag]=[lo,hi]
 rows={}
 for tag,(lo,hi) in bounds.items():
  r=b.recipes.get(tag,{})
  if not r.get('supported')or r.get('family')=='projected_decal':continue
  extent=np.maximum(hi-lo,1e-5);hi=lo+extent
  axis=(np.arange(512,dtype=np.float32)+.5)/512;u,v=np.meshgrid(axis,axis);uv=np.column_stack((lo[0]+u.ravel()*extent[0],lo[1]+v.ravel()*extent[1]));uv[:,1]=1-uv[:,1]
  rgb,valid=b.sample(tag,uv);im=np.column_stack((np.rint(np.clip(rgb,0,1)*255).astype(np.uint8),np.full(len(rgb),255,dtype=np.uint8))).reshape(512,512,4);file=out/('preview-'+tag+'.png');Image.fromarray(im).save(file);rows[tag]={'low':lo.tolist(),'high':hi.tolist(),'file':str(file.resolve()),'family':r.get('family'),'quality':'Representative static basecolor; missing vertex/world inputs where indicated; not source engine lighting'}
 (out/'preview-textures.json').write_text(json.dumps(rows,indent=2));print('baked',len(rows))
if __name__=='__main__':
 p=argparse.ArgumentParser(description='Bake a static Charm exported UV range to preview PNGs; no mesh or source mutation.');p.add_argument('--source',type=Path,required=True);p.add_argument('--materials',type=Path,default=Path('/Volumes/qf-ssd/Destiny-Tower-Materials-2026-10-29'));p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.source,a.materials,a.output)
