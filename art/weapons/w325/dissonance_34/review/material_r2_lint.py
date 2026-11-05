"""Same-normal coplanar polygon check and material assignment coverage for the owned six designs."""
import sys,math,json
from pathlib import Path
root=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(root/'scripts/art/w325'));import kit
ids=['dissonance_34','requiem_si2','roderic_c','vinegaroon_2si','furina_2mg','whip_scorpion_3mg','traveler_s_chosen']
def area(p):return sum(p[i-1][0]*p[i][1]-p[i][0]*p[i-1][1] for i in range(len(p)))/2
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def clip(poly,other):
 if area(other)<0:other=other[::-1]
 for a,b in zip(other,other[1:]+other[:1]):
  if not poly:break
  out=[]
  for c,d in zip(poly,poly[1:]+poly[:1]):
   fc,fd=cross(a,b,c),cross(a,b,d)
   if fc>=-1e-8:out.append(c)
   if (fc>=0)!=(fd>=0):
    t=fc/(fc-fd);out.append((c[0]+t*(d[0]-c[0]),c[1]+t*(d[1]-c[1])))
  poly=out
 return abs(area(poly)) if len(poly)>=3 else 0
for wid in ids:
 d=kit.load_design(wid);es=d.elements();groups={};fallback=[];errors=[]
 for e in es:
  for fn in kit.FACE_AXES:
   if not isinstance(d.material(e['name'],fn),dict):fallback.append([e['name'],fn])
   normal=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e));pts=[kit.face_point(e,fn,s,t) for s,t in [(0,0),(1,0),(1,1),(0,1)]]
   plane=sum(normal[i]*pts[0][i] for i in range(3));keep=[i for i in range(3) if i!=max(range(3),key=lambda i:abs(normal[i]))]
   key=tuple(round(v,4) for v in normal)+(round(plane,4),)
   poly=[tuple(p[i] for i in keep) for p in pts]
   for n,old in groups.get(key,[]):
    overlap=clip(poly,old)
    if overlap>1e-4:errors.append((n,e['name'],fn,round(overlap,5)))
   groups.setdefault(key,[]).append((e['name'],poly))
 print(wid,'elements',len(es),'unassigned_materials',len(fallback),'coplanar',len(errors),errors[:12])
 (root/'art/weapons/w325'/wid/'review/material_r2_lint.json').write_text(json.dumps({'element_total':len(es),'unassigned_material_faces':fallback,'coplanar_same_normal_pairs':errors},indent=2))
