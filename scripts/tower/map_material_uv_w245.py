import sys,json,time,struct,collections
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/tower'))
from tower_mesh import GLB,transform_bounds,overlaps
from voxelize_courtyard import surface_cells,barycentric_at_cells,Materials
from export_schematic import read_vox
import argparse
parser=argparse.ArgumentParser(description='Read-only original Courtyard geometry to existing exposed block UV mapping; no source deformation.')
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--source',type=Path,default=Path('/Volumes/qf-ssd/Tower-Courtyard-Assets-2026-10-28/maps/tower_courtyard.textured.glb'))
a=parser.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True);g=GLB(a.source)
lo=np.array([-25,64,-135]);hi=np.array([135,125,25]);dims=hi-lo+1
xyz,ids,palette=read_vox(ROOT/'src/main/resources/data/destiny/tower/courtyard.vox.gz')
source=np.zeros(dims+2,dtype=np.uint16);inside=np.all((xyz>=lo-1)&(xyz<=hi+1),axis=1);q=xyz[inside]-lo+1;source[tuple(q.T)]=ids[inside]+1
exposed=np.zeros(dims,dtype=bool)
for ax in range(3):
 for side in (0,2):
  sl=[slice(1,-1)]*3;sl[ax]=slice(0,-2) if side==0 else slice(2,None);exposed|=source[tuple(sl)]==0
occupied=source[1:-1,1:-1,1:-1]>0;selected=occupied&exposed
mg=np.full(dims,-1,dtype=np.int16);uvg=np.zeros(tuple(dims)+(2,),dtype=np.float32);ng=np.zeros(tuple(dims)+(3,),dtype=np.float32)
materials=Materials(g,{})
rows=collections.Counter();start=time.monotonic();last=start;cropnodes=[]
for ni,mi,world in g.world_instances():
 b0,b1=transform_bounds(*g.mesh_bounds(mi),world);b0=b0*2+[0,40,0];b1=b1*2+[0,40,0]
 if not overlaps(b0,b1,lo,hi+1):continue
 mesh=g.doc['meshes'][mi];node=g.doc['nodes'][ni];prims=[]
 if mesh.get('extras',{}).get('terrain'):raise ValueError('Terrain UV contract needs separate verification; this bake supports static Courtyard meshes only')
 for prim in mesh['primitives']:
  b0,b1=transform_bounds(*g.primitive_bounds(prim),world);b0=b0*2+[0,40,0];b1=b1*2+[0,40,0]
  if not overlaps(b0,b1,lo,hi+1):continue
  idx=prim.get('material',-1);opts=materials.options(idx,node.get('name',''),mesh.get('name',''));mat=materials.get(idx,opts)
  positions=g.accessor(prim['attributes']['POSITION']);pts=(positions@world[:3,:3].T+world[:3,3])*2+[0,40,0]
  triids=g.accessor(prim['indices']).reshape(-1,3);uv=g.accessor(prim['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in prim['attributes'] else None
  for st in range(0,len(triids),2048):
   ti=triids[st:st+2048];tri=pts[ti];ok=np.all(tri.max(1)>=lo,axis=1)&np.all(tri.min(1)<=hi+1,axis=1);tri=tri[ok];ti=ti[ok]
   for cells,tids in surface_cells(tri,lo,hi):
    loc=cells-lo;ok=selected[tuple(loc.T)];cells,tids,loc=cells[ok],tids[ok],loc[ok]
    if not len(cells):continue
    # Preserve source alpha visibility so transparent billboards cannot overwrite solid walls.
    _,visible=materials.color_cells(mat,tri[tids],cells,uv[ti[tids]] if uv is not None else None)
    cells,tids,loc=cells[visible],tids[visible],loc[visible]
    if not len(cells):continue
    flat=np.ravel_multi_index(loc.T,dims);_,rev=np.unique(flat[::-1],return_index=True);pick=len(flat)-1-rev;cells,tids,loc=cells[pick],tids[pick],loc[pick]
    weights=barycentric_at_cells(tri[tids],cells);sample=np.einsum('ni,nij->nj',weights,uv[ti[tids]]) if uv is not None else np.zeros((len(cells),2))
    n=np.cross(tri[tids,1]-tri[tids,0],tri[tids,2]-tri[tids,0]);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-12)
    mg[tuple(loc.T)]=idx;uvg[tuple(loc.T)]=sample;ng[tuple(loc.T)]=n;rows['assigned']+=len(cells)
  rows['primitives']+=1
 if time.monotonic()-last>15:print(dict(rows),round(time.monotonic()-start,1),flush=True);last=time.monotonic()
 cropnodes.append({'name':node.get('name',str(ni)), 'mesh':mi,'matrix':world.reshape(-1,order='F').tolist()})
mask=selected&(mg>=0);pos=np.column_stack(np.where(mask));mapped=mg[mask];names=[m['name']for m in g.doc['materials']]
np.savez_compressed(out/'geometry-uv.npz',xyz=pos+lo,material=mapped,uv=uvg[mask],normal=ng[mask],source_id=source[1:-1,1:-1,1:-1][mask]-1,palette=np.array(palette),materials=np.array(names))
c=collections.Counter(names[int(i)]for i in mapped);(out/'geometry-coverage.json').write_text(json.dumps(c.most_common(),indent=2))
# Original world geometry, cropped only by whole instance; no deformation or source writes.
doc=g.doc.copy();doc['nodes']=cropnodes;doc['scenes']=[{'nodes':list(range(len(cropnodes)))}];doc['scene']=0
for im in doc.get('images',[]):
 if 'uri' in im:im['uri']=str((g.path.parent/im['uri']).resolve())
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary=g.binary;binary+=b'\0'*((-len(binary))%4)
with (out/'source-crop.glb').open('wb')as f:f.write(struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(binary)));f.write(struct.pack('<II',len(js),0x4E4F534A));f.write(js);f.write(struct.pack('<II',len(binary),0x004E4942));f.write(binary)
print('DONE',dict(rows),'mapped',len(pos),'seconds',time.monotonic()-start,flush=True)
