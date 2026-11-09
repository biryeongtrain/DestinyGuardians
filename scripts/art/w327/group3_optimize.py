"""W327 group C: preserve authored solids while removing triangle-adapter inflation.
Only coplanar facets of the same semantic part and material are combined. The
native rectangle contains an exact polygon-union alpha mask, never a filled slab.
"""
import math,re,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('g3_triangle',ROOT/'scripts/mesh/native_triangle_elements_w115.py');tri=importlib.util.module_from_spec(spec);spec.loader.exec_module(tri)
def root_name(n):
 return re.sub(r'_(?:cap[01]_\d+|edge\d+[ab]|\d+_\d+[ab]|\d+[ab]?)$','',n)
def optimize(s):
 names={t['name'] for t in s.authored_triangles}
 old=s.e
 boxes=[e for e in old if e['name'].rsplit('_',1)[0] not in names]
 groups={}
 for t in s.authored_triangles:
  a,b,c=t['vertices'];normal=tri.cross(tri.sub(b,a),tri.sub(c,a));length=tri.norm(normal)
  if length<1e-10:continue
  normal=tri.unit(normal)
  if next(v for v in normal if abs(v)>1e-8)<0:normal=tri.mul(normal,-1)
  key=(root_name(t['name']),t['role'],*(round(v,7) for v in normal),round(tri.dot(normal,a),6))
  groups.setdefault(key,[]).append(t)
 planes=[];records=[]
 for ix,(key,ts) in enumerate(groups.items()):
  vertices=[p for t in ts for p in t['vertices']]
  # One common basis for material projection and the alpha contour.
  a,b=max([(t['vertices'][i],t['vertices'][(i+1)%3]) for t in ts for i in range(3)],key=lambda ab:math.dist(*ab))
  u=tri.unit(tri.sub(b,a));normal=tri.unit(tri.cross(u,tri.sub(max(vertices,key=lambda p:tri.norm(tri.cross(u,tri.sub(p,a)))),a)));v=tri.unit(tri.cross(normal,u))
  coords=[[(tri.dot(tri.sub(p,a),u),tri.dot(tri.sub(p,a),v)) for p in t['vertices']] for t in ts]
  xs=[p[0] for poly in coords for p in poly];ys=[p[1] for poly in coords for p in poly];x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys);w=x1-x0;h=y1-y0
  origin=tri.add(a,tri.add(tri.mul(u,x0),tri.mul(v,y0)));center=tri.add(origin,tri.add(tri.mul(u,w/2),tri.mul(v,h/2)));angles=tri.euler_zyx(u,v,normal)
  error=max(abs(tri.dot(tri.sub(p,origin),normal)) for p in vertices);assert error<1e-5,(key,error)
  name=key[0]+'_plane'+str(ix)
  polys=[[( (x-x0)/w,1-(y-y0)/h) for x,y in poly] for poly in coords]
  e={'name':name,'from':[center[0]-w/2,center[1]-h/2,center[2]],'to':[center[0]+w/2,center[1]+h/2,center[2]],'rotation':{'origin':list(center),**dict(zip('xyz',angles))},'faces':{'south':{},'north':{}},'_polygons':polys}
  planes.append(e);s.roles[name]=key[1];records.append({'name':name,'source_triangles':[t['name'] for t in ts],'vertices':[t['vertices'] for t in ts],'plane_error':error})
 s.e=boxes+planes;s.authored_polygons=records
 s.optimization={'before_elements':len(old),'after_elements':len(s.e),'preserved_solid_cuboids':len(boxes),'authored_triangles':len(s.authored_triangles),'masked_polygon_planes':len(planes),'max_plane_error':max(r['plane_error'] for r in records),'method':'same semantic part/material coplanar polygon unions; original authored vertices retained; no filled contour rectangle'}
 return s
