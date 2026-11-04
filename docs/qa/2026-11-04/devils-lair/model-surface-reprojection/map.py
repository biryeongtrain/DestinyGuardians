import bpy, numpy as np, json, sys, time
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path('/tmp/devils-thrall-baseline-20261104');O=Path('/tmp/devils-thrall-reproject-20261104')
m=json.loads((P/'dl_thrall.bbmodel').read_text());stats=json.loads((P/'thrall_stats.json').read_text());d=np.load(P/'thrall_mesh.npz');v=d['V'];UV=d['UV'];k=stats['k'];y0=stats['y0'];T=np.stack([v[...,0]*k,v[...,2]*k+y0,-v[...,1]*k],axis=-1)
bvh=BVHTree.FromPolygons(T.reshape(-1,3).tolist(),np.arange(T.size//3).reshape(-1,3).tolist(),all_triangles=True)
a=bpy.data.images.load(str(P/'thrall_render_atlas.png'));size=a.size[0];px=np.empty(size*size*4,dtype=np.float32);a.pixels.foreach_get(px);alpha=px.reshape(size,size,4)[::-1,:,3]
FAC={'north':(2,0,1,-1,-1),'south':(2,0,1,1,-1),'east':(0,2,1,-1,-1),'west':(0,2,1,1,-1),'up':(1,0,2,1,1),'down':(1,0,2,1,-1)}
xs=[];ys=[];uvs=[];distances=[];positions=[];start=time.time()
for e in m['elements']:
 for face,f in e['faces'].items():
  if f['texture'] is None:continue
  x0,y0t,x1,y1=map(int,f['uv']);rows,cols=np.nonzero(alpha[y0t:y1,x0:x1]>.5);da,ua,va,us,vs=FAC[face];lo=np.array(e['from']);hi=np.array(e['to']);u=(cols+.5)/(x1-x0);vv=(rows+.5)/(y1-y0t)
  if us<0:u=1-u
  if vs<0:vv=1-vv
  points=np.repeat(lo[None,:],len(rows),axis=0);points[:,ua]=lo[ua]+u*(hi[ua]-lo[ua]);points[:,va]=lo[va]+vv*(hi[va]-lo[va])
  for row,col,point in zip(rows,cols,points):
   loc,normal,idx,distance=bvh.find_nearest(Vector(point))
   tri=T[idx];q=np.asarray(loc)-tri[0];a0=tri[1]-tri[0];b0=tri[2]-tri[0];aa=a0@a0;ab=a0@b0;bb=b0@b0;den=aa*bb-ab*ab
   if abs(den)<1e-16:continue
   u=(bb*(a0@q)-ab*(b0@q))/den;vv=(aa*(b0@q)-ab*(a0@q))/den;uv=UV[idx,0]+u*(UV[idx,1]-UV[idx,0])+vv*(UV[idx,2]-UV[idx,0])
   positions.append(point);xs.append(col+x0);ys.append(row+y0t);uvs.append(uv);distances.append(distance)
np.savez_compressed(O/'mapping.npz',x=xs,y=ys,uv=uvs,distance=distances,position=positions)
print('mapped',len(xs),'seconds',time.time()-start,flush=True)
