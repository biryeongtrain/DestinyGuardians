"""Actual evaluated Blender source or authored cuboids, identical neutral material/camera/light.
No source files saved. Only transparent reticle/glass planes excluded from source comparison.
"""
import bpy,math,mathutils,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_contours import triangulate
args=sys.argv[sys.argv.index('--')+1:];mode,design,out=args[:3];D=json.loads(Path(design).read_text());m=D['source_mapping'];verts=[];polys=[]
def mb(p):return ((8-p[0])/16,p[2]/16,p[1]/16)
def rot(r):
 if not r:return mathutils.Matrix.Identity(3)
 ang=[r['angle'] if k==r['axis'] else 0 for k in 'xyz'] if 'axis' in r else [r.get(k,0) for k in 'xyz']
 return mathutils.Matrix.Rotation(math.radians(ang[2]),3,'Z')@mathutils.Matrix.Rotation(math.radians(ang[1]),3,'Y')@mathutils.Matrix.Rotation(math.radians(ang[0]),3,'X')
if mode=='source':
 deps=bpy.context.evaluated_depsgraph_get()
 for ob in list(bpy.data.objects):
  if ob.type!='MESH':continue
  names=[ma.name.lower() for ma in ob.data.materials if ma]
  if any(n in ('ret','reticle','radial','glass') for n in names):continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();base=len(verts)
  for v in me.vertices:
   p=ev.matrix_world@v.co;u=m['res'][0]/2+(p.y-m['centre'][1])*m['ppm'];vv=m['res'][1]/2-(p.z-m['centre'][2])*m['ppm'];verts.append(mb((8+p.x*m['sx'],m['y0']-vv*m['q'],m['z0']+u*m['q'])))
  polys += [tuple(base+i for i in p.vertices) for p in me.polygons];ev.to_mesh_clear()
else:
 for e in D['elements']:
  r=e.get('rotation');M=rot(r);o=mathutils.Vector(r['origin']) if r else mathutils.Vector((0,0,0));base=len(verts)
  cs=[M@(mathutils.Vector([e['to'][i] if n>>i&1 else e['from'][i] for i in range(3)])-o)+o for n in range(8)];verts += [mb(p) for p in cs]
  polys += [tuple(base+i for i in face) for face in [(3,2,0,1),(6,7,5,4),(2,6,4,0),(7,3,1,5),(2,3,7,6),(4,5,1,0)]]
if mode!='source':
 for solid in D.get('contours',[]):
  if 'mesh_faces' in solid:
   base=len(verts);verts += [mb(p) for p in solid['vertices']]
   for face in solid['mesh_faces']:
    for ids in triangulate([solid['vertices'][i] for i in face]):polys.append(tuple(base+face[i] for i in ids))
   continue
  pts=solid['vertices'];ex=solid.get('extrude',[0,0,0]);back=solid.get('back_vertices') or [[p[i]+ex[i] for i in range(3)] for p in pts];nn=len(pts);base=len(verts);verts += [mb(p) for p in pts]+[mb(p) for p in back]

  for ids in triangulate(pts):polys.append(tuple(base+i for i in reversed(ids)));polys.append(tuple(base+nn+i for i in ids))
  for i in range(nn):j=(i+1)%nn;polys.append((base+i,base+j,base+nn+j,base+nn+i))
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob)
me=bpy.data.meshes.new('comparison_geometry');me.from_pydata(verts,[],polys);ob=bpy.data.objects.new('comparison',me);bpy.context.scene.collection.objects.link(ob)
mat=bpy.data.materials.new('neutral_same_material');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.43,.43,.43,1);bs.inputs['Roughness'].default_value=.85;me.materials.append(mat)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard';sc.render.film_transparent=False;w=bpy.data.worlds.new('comparison_world');sc.world=w;w.use_nodes=True;w.node_tree.nodes['Background'].inputs[0].default_value=(.45,.47,.5,1);w.node_tree.nodes['Background'].inputs[1].default_value=.7
for ang,en in [((.9,.2,.5),2.2),((-.5,-.4,.3),.8),((2.6,.3,-2.5),.6)]:
 l=bpy.data.lights.new('comparison_sun','SUN');l.energy=en;o=bpy.data.objects.new('comparison_sun',l);sc.collection.objects.link(o);o.rotation_euler=ang
lo=[min(v[i] for v in verts) for i in range(3)];hi=[max(v[i] for v in verts) for i in range(3)];c=mathutils.Vector([(lo[i]+hi[i])/2 for i in range(3)]);cam=bpy.data.cameras.new('comparison_camera');cam.type='ORTHO';co=bpy.data.objects.new('comparison_camera',cam);sc.collection.objects.link(co);sc.camera=co;sc.render.resolution_x=1200;sc.render.resolution_y=800
camera_records={};camera_file=Path(out).parent/'source_camera.json';fixed=json.loads(camera_file.read_text()) if mode!='source' and camera_file.exists() else {}
for key,dd in {'side':(-1,0,0),'quarter':(-.7,.45,-.45),'front':(0,1,0),'top':(0,0,-1)}.items():
 d=mathutils.Vector(dd).normalized();co.location=c-d*3;co.rotation_euler=d.to_track_quat('-Z','Y').to_euler();M=co.rotation_euler.to_matrix().transposed();pp=[M@(mathutils.Vector(v)-c) for v in verts];rw=max(v.x for v in pp)-min(v.x for v in pp);rh=max(v.y for v in pp)-min(v.y for v in pp);co.location+=co.rotation_euler.to_matrix()@mathutils.Vector(((min(v.x for v in pp)+max(v.x for v in pp))/2,(min(v.y for v in pp)+max(v.y for v in pp))/2,0));cam.ortho_scale=max(rw,rh*1.5)*1.12;cam.clip_start=.001;cam.clip_end=100;
 if key in fixed:
  co.location=fixed[key]['location'];co.rotation_euler=fixed[key]['rotation'];cam.ortho_scale=fixed[key]['scale']
 camera_records[key]=dict(location=list(co.location),rotation=list(co.rotation_euler),scale=cam.ortho_scale)
 sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.filepath=f'{out}_{key}.png';bpy.ops.render.render(write_still=True)

if mode=='source':camera_file.write_text(json.dumps(camera_records,indent=1)+'\n')
