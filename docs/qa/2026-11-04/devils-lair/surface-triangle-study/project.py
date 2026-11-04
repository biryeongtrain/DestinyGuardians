"""Diagnostic high-to-low surface reprojection; preserves source shader pixels."""
import numpy as np,json,sys,math,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path.cwd();sys.path.insert(0,str(root/'scripts/mesh'))
from native_triangle_elements_w115 import split_triangle
out=Path(os.environ.get('DEVILS_TRIANGLE_DIR','/tmp/devils-triangle-projected'));cache=Path('/tmp/devils-drive-marauder-dual')
d=np.load(out/'surface.npz');hi=np.load(cache/'marauder_mesh.npz');stats=json.loads((cache/'marauder_stats.json').read_text());k=stats['k'];y0=stats['y0']
source=np.load(out/'source-rgba.npy');h,w=source.shape[:2]
V=d['V'];verts=np.stack([V[:,:,0]*k,V[:,:,2]*k+y0,-V[:,:,1]*k],axis=-1)*.5+8
parts=[]
for i,tri in enumerate(verts):
 for part in split_triangle(tri):parts.append((i,part))
meta=json.loads((out/'manifest.json').read_text());tile=meta['tile'];stride=tile+2;size=meta['atlasSize'];columns=size//stride
atlas=np.zeros((size,size,4),np.uint8);trees={};max_distance=0.;distances=[];ray_hits=0;ray_rejected=0
normal_ray='--normal-ray' in sys.argv
for bone in np.unique(d['BONE']):
 inds=np.flatnonzero(hi['BONE']==bone);tri=hi['V'][inds];uv=hi['UV'][inds]
 tree=BVHTree.FromPolygons([Vector(p) for p in tri.reshape(-1,3)],[(i*3,i*3+1,i*3+2) for i in range(len(tri))],all_triangles=True)
 basis=np.stack([tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]],axis=-1)
 transform=np.linalg.pinv(basis).transpose(0,2,1)@np.stack([uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]],axis=1)
 trees[str(bone)]=(tree,tri[:,0],uv[:,0],transform)
for index,(i,part) in enumerate(parts):
 tree,tri0,uv0,transform=trees[str(d['BONE'][i])];normal_low=Vector(np.cross(V[i,1]-V[i,0],V[i,2]-V[i,0])).normalized();tx=index%columns*stride+1;ty=index//columns*stride+1
 for row in range(tile):
  for col in range(row+1):
   u=(col+.5)/tile;v=(row+.5)/tile
   p=np.array(part['origin'])+u*part['width']*np.array(part['u'])+(1-v)*part['height']*np.array(part['v']);bb=(p-8)/.5
   raw=Vector((bb[0]/k,-bb[2]/k,(bb[1]-y0)/k));nearest=tree.find_nearest(raw)
   if nearest[0] is None:raise ValueError('No original source surface')
   at,normal,face,distance=nearest
   if normal_ray:
    hit=tree.ray_cast(raw+normal_low*.2,-normal_low,.4)
    if hit[0] is not None and hit[1].dot(normal_low)>.1:
     at,normal,face,_=hit;distance=(at-raw).length;ray_hits+=1
    else:ray_rejected+=1
   uv=uv0[face]+(np.array(at)-tri0[face])@transform[face]
   x=min(w-1,max(0,int(uv[0]*w)));y=min(h-1,max(0,int((1-uv[1])*h)))
   rgba=source[y,x].copy();rgba[3]=255 if rgba[3]>=128 else 0;atlas[ty+row,tx+col]=rgba
   distances.append(distance)
 if index%1000==0:print('Projected',index,'/',len(parts),flush=True)
np.save(out/'projected-atlas.npy',atlas)
(out/'projection.json').write_text(json.dumps(dict(samples=len(distances),distanceMetres=dict(p50=float(np.quantile(distances,.5)),p95=float(np.quantile(distances,.95)),max=float(max(distances))),sourceGrouping='same source bone only',normalRay=normal_ray,rayHits=ray_hits,rayFallbacks=ray_rejected,status='diagnostic, no runtime integration'),indent=2)+'\n')
