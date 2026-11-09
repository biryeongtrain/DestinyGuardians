"""Prepare authored V4 solids for native alpha-plane export; no source meshes are read."""
import bpy,bmesh,mathutils,json,sys,math,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];wid=sys.argv[sys.argv.index('--')+1];out=ROOT/'art/weapons/w327'/wid/'v4'
objects=[];max_planarization_displacement=0;max_planarization_residual=0
records=json.loads((out/'authored_geometry.json').read_text())
if wid=='eyasluna':
 # Join overlapping grip solids at their exact intersection, removing coincident interior
 # skins rather than covering cracks with an opaque plate. Exterior and palm bulge remain.
 pair=[]
 for rec in records:
  if rec['name'] not in ['V4/grip/frame','V4/grip/inset']:continue
  me=bpy.data.meshes.new(rec['name']);me.from_pydata(rec['vertices'],[],rec['faces']);bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();ob=bpy.data.objects.new(rec['name'],me);bpy.context.scene.collection.objects.link(ob);pair.append(ob)
 base,cut=pair;mod=base.modifiers.new('grip solid union','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=cut;bpy.context.view_layer.objects.active=base;bpy.ops.object.modifier_apply(modifier=mod.name)
 records=[r for r in records if r['name'] not in ['V4/grip/frame','V4/grip/inset']]+[{'name':'V4/grip/union','vertices':[list(v.co) for v in base.data.vertices],'faces':[list(p.vertices) for p in base.data.polygons]}]
 bpy.data.objects.remove(base,do_unlink=True);bpy.data.objects.remove(cut,do_unlink=True)
for rec in records:
 me=bpy.data.meshes.new(rec['name']);me.from_pydata(rec['vertices'],[],rec['faces']);bm=bmesh.new();bm.from_mesh(me)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.dissolve_limit(bm,angle_limit=.00001,verts=list(bm.verts),edges=list(bm.edges),delimit={'NORMAL'})
 bm.to_mesh(me);bm.free();me.update()
 # Coupled planarization keeps shared vertices identical: independently projecting quads
 # opens cracks. Only near-planar authored facets participate, and displacement is audited.
 original=np.array([list(v.co) for v in me.vertices],dtype=float);points=original.copy();constraints=[]
 for face in me.polygons:
  ix=list(face.vertices)
  if len(ix)<4:continue
  pp=points[ix];center=pp.mean(axis=0);n=np.linalg.svd(pp-center)[2][-1];dev=np.max(np.abs((pp-center)@n))
  if dev<.00030:constraints.append(ix)
 for iteration in range(220):
  acc=np.zeros_like(points);count=np.zeros(len(points));residual=0
  for ix in constraints:
   pp=points[ix];center=pp.mean(axis=0);n=np.linalg.svd(pp-center)[2][-1];d=(pp-center)@n;residual=max(residual,float(np.max(np.abs(d))));acc[ix]+=-d[:,None]*n;count[ix]+=1
  points+=acc/np.maximum(1,count)[:,None]
  if residual<2e-8:break
 displacement=float(np.max(np.linalg.norm(points-original,axis=1)));max_planarization_displacement=max(max_planarization_displacement,displacement);max_planarization_residual=max(max_planarization_residual,residual)
 for v,point in zip(me.vertices,points):v.co=point
 me.update();vv=[v.co.copy() for v in me.vertices];ff=[list(p.vertices) for p in me.polygons]
 lo=Vector([min(v[i] for v in vv) for i in range(3)]);hi=Vector([max(v[i] for v in vv) for i in range(3)])
 objects.append({'name':rec['name'],'mesh':me,'verts':vv,'faces':ff,'lo':lo,'hi':hi,'bvh':BVHTree.FromPolygons(vv,ff,all_triangles=False,epsilon=0)})
direction=Vector((.912371,.321419,.187139)).normalized()
def inside(o,p):
 if any(p[i]<o['lo'][i]+.000001 or p[i]>o['hi'][i]-.000001 for i in range(3)):return False
 at=p.copy();hits=0
 for _ in range(40):
  loc,normal,idx,dist=o['bvh'].ray_cast(at,direction,2)
  if loc is None:break
  hits+=1;at=loc+direction*.000001
 return hits%2==1
planes=[];hidden=0;nonplanar=0;input_faces=0;max_flatten_deviation=0;flattened=0
for o in objects:
 me=o['mesh'];me.calc_loop_triangles();tris={}
 for tri in me.loop_triangles:tris.setdefault(tri.polygon_index,[]).append([o['verts'][i] for i in tri.vertices])
 for ix,f in enumerate(o['faces']):
  input_faces+=1;pts=[o['verts'][i] for i in f];center=sum(pts,Vector())/len(pts);normal=me.polygons[ix].normal.copy()
  samples=[center]+pts+[(pts[i]+pts[(i+1)%len(pts)])*.5 for i in range(len(pts))]
  candidates=[other for other in objects if other is not o and ('/mag_' in other['name'])==('/mag_' in o['name']) and all(center[i]>other['lo'][i]-.0001 and center[i]<other['hi'][i]+.0001 for i in range(3))]
  if not o['name'].startswith('V4/grip') and candidates and all(any(inside(other,p+normal*.000015) and inside(other,p-normal*.000015) for other in candidates) for p in samples):hidden+=1;continue
  deviation=max(abs((p-center).dot(normal)) for p in pts);flat=deviation<.000010
  if flat and deviation>.000001:
   flattened+=1;max_flatten_deviation=max(max_flatten_deviation,deviation);pts=[p-normal*((p-center).dot(normal)) for p in pts]
  polys=[pts] if flat else tris[ix]
  if not flat:nonplanar+=1
  for poly in polys:
   planes.append({'name':o['name']+'/'+str(ix),'vertices':[list(p) for p in poly]})
# Co-planar pieces share a single masked native rectangle. Their polygon UNION preserves holes
# (e.g. annular cylinder end caps); no filled rectangular contour is substituted.
merged={}
for p in planes:
 vv=np.array(p['vertices'],dtype=float);a,b=max([(vv[i],vv[(i+1)%len(vv)]) for i in range(len(vv))],key=lambda pair:float(np.linalg.norm(pair[1]-pair[0])));u=b-a
 c=max(vv,key=lambda point:float(np.linalg.norm(np.cross(u,point-a))));n=np.cross(u,c-a);nn=np.linalg.norm(n)
 if nn<1e-14:continue
 n=n/nn;first=next((value for value in n if abs(value)>1e-6),1)
 if first<0:n=-n
 distance=float(n@vv[0]);name=p['name'].rsplit('/',1)[0];key=(name,*(round(c,5) for c in n),round(distance,6))
 g=merged.setdefault(key,{'name':name,'polygons':[]})
 g['polygons'].append(p['vertices'])
groups=list(merged.values())
(out/'native_planes.json').write_text(json.dumps(groups))
(out/'native_preparation.json').write_text(json.dumps({'coupled_planarization_max_source_displacement':max_planarization_displacement,'coupled_planarization_max_residual':max_planarization_residual,'authored_solids':len(objects),'faces_after_planar_dissolve':input_faces,'fully_internal_faces_removed':hidden,'nonplanar_faces_triangulated':nonplanar,'nearly_planar_facets_projected':flattened,'max_source_metre_projection':max_flatten_deviation,'max_canonical_projection_px':max_flatten_deviation*35,'visible_polygon_facets':len(planes),'native_polygon_planes':len(groups),'scope':'authored V4 exterior; coplanar polygon unions preserve bore holes; native alpha-plane validation still required'},indent=2))
print(wid,'faces',input_faces,'hidden',hidden,'nonplanar',nonplanar,'facets',len(planes),'native planes',len(groups))
