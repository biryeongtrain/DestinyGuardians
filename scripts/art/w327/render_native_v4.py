"""Same-camera authored/native review, with actual native alpha silhouettes."""
import bpy,json,sys,math,mathutils
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
wid=sys.argv[sys.argv.index('--')+1];out=ROOT/'art/weapons/w327'/wid/'v4'
source_records=[]
if '--source-loaded' in sys.argv:
 deps=bpy.context.evaluated_depsgraph_get()
 for ob in list(bpy.data.objects):
  if ob.type!='MESH' or ob.name.startswith('Plane') or '.02.' in ob.name or ob.name in ('Eye','Reticle') or (wid=='nation_of_beasts' and ob.name.endswith('.00.001')):continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();source_records.append({'name':ob.name,'vertices':[list(ob.matrix_world@v.co) for v in me.vertices],'faces':[list(p.vertices) for p in me.polygons]});ev.to_mesh_clear()
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
contract=json.loads((out/'camera_contract.json').read_text())
mat=bpy.data.materials.new('constant proof grey');mat.use_nodes=True
bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.31,.36,.39,1);bs.inputs['Roughness'].default_value=.72
sources=[]
for rec in source_records:
 me=bpy.data.meshes.new(rec['name']);me.from_pydata(rec['vertices'],[],rec['faces']);me.materials.append(mat);ob=bpy.data.objects.new(rec['name'],me);bpy.context.scene.collection.objects.link(ob);sources.append(ob)
auth=[]
for rec in json.loads((out/'authored_geometry.json').read_text()):
 me=bpy.data.meshes.new(rec['name']);me.from_pydata(rec['vertices'],[],rec['faces']);me.materials.append(mat)
 ob=bpy.data.objects.new(rec['name'],me);bpy.context.scene.collection.objects.link(ob);auth.append(ob)
skin=json.loads((out/'native_skin.json').read_text())
native_mat=bpy.data.materials.new('native alpha proof');native_mat.use_nodes=True
nt=native_mat.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.31,.36,.39,1);bs.inputs['Roughness'].default_value=.72
tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(out/'native_atlas.png'));tex.interpolation='Closest'
nt.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
# One side per coincident plane in Blender; native's mirrored north is the reverse of south.
face_indices={'south':(6,7,5,4)}
verts=[];polys=[];uvs=[]
def unmap(p):return ((8-p[0])/35,(p[2]-8)/35,(p[1]-7.6)/35)
for e in [e for part in skin['parts'].values() for e in part]:
 lo,hi=e['from'],e['to'];r=e['rotation'];origin=mathutils.Vector(r['origin'])
 M=mathutils.Euler(tuple(math.radians(r.get(k,0)) for k in 'xyz'),'XYZ').to_matrix()
 corners=[M@(mathutils.Vector([hi[i] if m>>i&1 else lo[i] for i in range(3)])-origin)+origin for m in range(8)]
 uv=e['faces']['south']['uv'];u1,v1,u2,v2=uv;b=len(verts)
 for k,(u,v) in zip(face_indices['south'],((u1,v1),(u2,v1),(u2,v2),(u1,v2))):
  verts.append(unmap(corners[k]));uvs.append((u/16,1-v/16))
 polys.append((b,b+1,b+2,b+3))
me=bpy.data.meshes.new('native exported rectangles');me.from_pydata(verts,[],polys);uvl=me.uv_layers.new()
for li,loop in enumerate(me.loops):uvl.data[li].uv=uvs[loop.vertex_index]
me.materials.append(native_mat);native=bpy.data.objects.new('native exported rectangles',me);bpy.context.scene.collection.objects.link(native)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.cycles.transparent_max_bounces=32;sc.render.use_compositing=False;sc.render.use_sequencer=False
sc.view_settings.view_transform='Standard';sc.render.film_transparent=False
sc.world.use_nodes=True;bg=sc.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.075,.09,.11,1);bg.inputs[1].default_value=.6
for ang,en in [((.8,.2,.5),2.2),((-.5,-.4,.3),.8),((2.6,.3,-2.5),.6)]:
 light=bpy.data.lights.new('review soft sun','SUN');light.energy=en;light.angle=.10;light.use_shadow=True
 ob=bpy.data.objects.new('review soft sun',light);sc.collection.objects.link(ob);ob.rotation_euler=ang
cam=bpy.data.cameras.new('fixed source camera');cam.type='ORTHO';cam.ortho_scale=contract['orthographic_scale']
co=bpy.data.objects.new('fixed source camera',cam);sc.collection.objects.link(co);sc.camera=co
sc.render.resolution_x,sc.render.resolution_y=contract['resolution'];sc.render.resolution_percentage=100
center=mathutils.Vector(contract['source_center'])
views=[('side',(1,0,0)),('q',(1,-.6,.28)),('front',(0,-1,0)),('back',(0,1,0)),('rear',(-1,.65,.28))]
if '--quick' in sys.argv:views=[('q',(1,-.6,.28))]
for mode in (['native_material'] if '--quick' in sys.argv else (['source_neutral'] if sources else [])+['authored_neutral','native_neutral','native_material']):
 for ob in sources:ob.hide_render=mode!='source_neutral'
 for ob in auth:ob.hide_render=mode!='authored_neutral'
 native.hide_render=mode in ['source_neutral','authored_neutral']
 if mode=='native_material':nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 for name,d in views:
  d=mathutils.Vector(d).normalized();co.location=center+d*2;co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
  sc.render.filepath=str(out/(mode+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
