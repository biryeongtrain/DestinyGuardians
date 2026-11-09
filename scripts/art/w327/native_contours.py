"""Closed authored solids -> exact native 26.3 triangle/rectangle planes.
Source contours are authored vertices, not converted ripped meshes. All caps and perimeter faces exist.
"""
from pathlib import Path
import math,importlib.util
ROOT=Path(__file__).resolve().parents[3]
sp=importlib.util.spec_from_file_location('native_triangle',ROOT/'scripts/mesh/native_triangle_elements_w115.py');tri=importlib.util.module_from_spec(sp);sp.loader.exec_module(tri)
add=tri.add;sub=tri.sub;mul=tri.mul;dot=tri.dot;cross=tri.cross;norm=tri.norm;unit=tri.unit

def triangulate(points):
 # Project on the authored profile's most stable plane; ear clipping preserves concave cuts.
 normal=(0,0,0)
 for i in range(len(points)):normal=add(normal,cross(points[i],points[(i+1)%len(points)]))
 omit=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=omit];p=[(v[axes[0]],v[axes[1]]) for v in points]
 def area(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 signed=sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)));sgn=1 if signed>0 else -1
 remain=list(range(len(p)));out=[]
 while len(remain)>3:
  found=False
  for j,b in enumerate(remain):
   a=remain[j-1];c=remain[(j+1)%len(remain)];ar=sgn*area(p[a],p[b],p[c])
   if ar<1e-10:continue
   inside=False
   for v in remain:
    if v in (a,b,c):continue
    aa=[sgn*area(p[x],p[y],p[v]) for x,y in [(a,b),(b,c),(c,a)]]
    if min(aa)>1e-9:inside=True;break
   if inside:continue
   out.append((a,b,c));remain.pop(j);found=True;break
  if not found:
   # Collinear boundary vertices add no area but are kept in perimeter geometry.
   for j,b in enumerate(remain):
    if abs(area(p[remain[j-1]],p[b],p[remain[(j+1)%len(remain)]]))<1e-9:remain.pop(j);found=True;break
   if not found:raise ValueError('Non-simple authored contour / failed ear clipping')
 if len(remain)==3 and abs(area(*(p[i] for i in remain)))>1e-10:out.append(tuple(remain))
 return out

def stable(part):
 u,v=part['u'],part['v'];n=cross(u,v)
 part['rotation']=tri.euler_zyx(u,v,n)
 for actual,expected in [(tri.rotate((1,0,0),part['rotation']),u),(tri.rotate((0,1,0),part['rotation']),v)]:assert norm(sub(actual,expected))<1e-6,(actual,expected)
 return part

def triangle_parts(vertices):
 # Existing right triangles require one rectangle, not an unnecessary altitude split.
 for i in range(3):
  a=vertices[i];b=vertices[(i+1)%3];c=vertices[(i+2)%3];ab=sub(b,a);ac=sub(c,a)
  if abs(dot(ab,ac))<=1e-9*max(1,norm(ab)*norm(ac)):
   u,v=unit(ab),unit(ac);return [stable(dict(origin=a,u=u,v=v,width=norm(ab),height=norm(ac),rotation=tri.euler_zyx(u,v,cross(u,v)),vertices=(a,b,c)))]
 return [stable(p) for p in tri.split_triangle(vertices)]

def rect_part(a,b,d):
 uvec=sub(b,a);vvec=sub(d,a);u,v=unit(uvec),unit(vvec)
 assert abs(dot(u,v))<1e-7
 return stable(dict(origin=a,u=u,v=v,width=norm(uvec),height=norm(vvec),rotation=tri.euler_zyx(u,v,cross(u,v))))

def emit_element(part,name,uv,triangle):
 e=tri.to_element(part,name,uv);e['triangle_mask']=triangle
 # Independent actual Minecraft Euler reconstruction of all four rectangle corners.
 c=e['rotation']['origin'];ang=tuple(e['rotation'][a] for a in 'xyz');lo,hi=e['from'],e['to'];corners=[]
 for local in [(lo[0],hi[1],lo[2]),(hi[0],hi[1],lo[2]),(hi[0],lo[1],lo[2]),(lo[0],lo[1],lo[2])]:corners.append(add(tri.rotate(sub(local,c),ang),c))
 expected=[add(part['origin'],mul(part['v'],part['height'])),add(add(part['origin'],mul(part['v'],part['height'])),mul(part['u'],part['width'])),add(part['origin'],mul(part['u'],part['width'])),part['origin']]
 err=max(norm(sub(a,b)) for a,b in zip(corners,expected));assert err<1e-6,(name,err)
 return e,err

def planar_polygon(points):
 # Keep a true planar authored face as one native rectangle with its own exact alpha contour.
 a=points[0];u=unit(sub(points[1],a));n=unit(cross(u,sub(points[2],a)));v=unit(cross(n,u))
 if max(abs(dot(sub(p,a),n)) for p in points)>1e-7:return None
 coords=[(dot(sub(p,a),u),dot(sub(p,a),v)) for p in points];lo=[min(p[i] for p in coords) for i in range(2)];hi=[max(p[i] for p in coords) for i in range(2)];w,h=hi[0]-lo[0],hi[1]-lo[1]
 origin=add(a,add(mul(u,lo[0]),mul(v,lo[1])));part=stable(dict(origin=origin,u=u,v=v,width=w,height=h,rotation=tri.euler_zyx(u,v,n)))
 return part,[[(p[0]-lo[0])/w,1-(p[1]-lo[1])/h] for p in coords]

def surfaces(contours):
 out=[]
 for solid in contours:
  if 'mesh_faces' in solid:
   vertices=solid['vertices']
   for j,face in enumerate(solid['mesh_faces']):
    pp=[vertices[i] for i in face]
    planar=planar_polygon(pp)
    if planar:
     part,mask=planar;out.append(dict(name=f"{solid['name']}/mesh{j}",part=part,triangle=False,polygon_mask=mask,role=solid['role'],source_points=pp));continue
    for t,ids in enumerate(triangulate(pp)):
     ps=[pp[i] for i in ids];part,mask=planar_polygon(ps)
     out.append(dict(name=f"{solid['name']}/mesh{j}_{t}",part=part,triangle=False,polygon_mask=mask,role=solid['role'],source_points=ps))
   continue
  front=[tuple(p) for p in solid['vertices']];back=[tuple(p) for p in solid.get('back_vertices',[])] or [add(p,solid['extrude']) for p in front];nn=len(front);caps=triangulate(front)
  for side,pts in [('front',front),('back',back)]:
   for j,ids in enumerate(caps):
    ps=[pts[i] for i in ids]
    for h,part in enumerate(triangle_parts(ps)):
     out.append(dict(name=f"{solid['name']}/{side}{j}_{h}",part=part,triangle=True,role=solid['role'],source_points=ps))
  for i in range(nn):
   j=(i+1)%nn;a,b,c,d=front[i],front[j],back[j],back[i]
   u,v=sub(b,a),sub(d,a)
   if abs(dot(unit(u),unit(v)))<1e-7 and norm(sub(add(b,v),c))<1e-7:
    out.append(dict(name=f"{solid['name']}/perimeter{i}",part=rect_part(a,b,d),triangle=False,role=solid['role'],source_points=[a,b,c,d]))
   else:
    for t,ps in enumerate([(a,b,c),(a,c,d)]):
     for h,part in enumerate(triangle_parts(ps)):out.append(dict(name=f"{solid['name']}/perimeter{i}_{t}_{h}",part=part,triangle=True,role=solid['role'],source_points=ps))
 return out

def neutral(D):
 surfaces_=surfaces(D.get('contours',[]));els=[];error=0
 if any('polygon_mask' in s for s in surfaces_):raise ValueError('Legacy neutral atlas only supports shared right-triangle islands; use group2_fidelity_bake output for per-face polygons.')
 for e in D['elements']:
  el={k:v for k,v in e.items() if k!='role'};el['faces']={f:dict(uv=[8,0,16,16],texture='#0') for f in ['north','south','east','west','up','down']};els.append(el)
 for surface in surfaces_:
  e,err=emit_element(surface['part'],surface['name'],[0,0,8,16] if surface['triangle'] else [8,0,16,16],surface['triangle']);error=max(error,err);e.pop('triangle_mask');els.append(e)
 assert len(els)<=1000,(len(els),'native cap')
 return dict(texture_size=[512,256],parts={'body':[e for e in els if not e['name'].startswith('mag_')],'magazine':[e for e in els if e['name'].startswith('mag_')]}),dict(actual_elements=len(els),cuboids=len(D['elements']),contour_solids=len(D.get('contours',[])),native_fragments=len(surfaces_),max_vertex_reconstruction_error=error,all_closed_contour_caps_and_perimeters=True)
