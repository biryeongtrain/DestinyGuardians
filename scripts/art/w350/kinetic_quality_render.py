"""Actual emitted native item JSON, fixed source-equivalent camera, alpha respected."""
import bpy,sys,json,math,mathutils,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];wid=sys.argv[sys.argv.index('--')+1];ad=ROOT/'art/weapons/w350'/wid;out=ad/'review-r2';out.mkdir(exist_ok=True)
doc=json.loads((ad/'parts.json').read_text());els=sum(doc['parts'].values(),[])
for ob in list(bpy.data.objects):bpy.data.objects.remove(ob,do_unlink=True)
mat=bpy.data.materials.new('native item atlas');mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.8
tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/f'src/main/resources/assets/destiny/textures/item/weapon/w350/{wid}.png'));tex.interpolation='Closest';nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
FACES={'south':(6,7,5,4)};verts=[];polys=[];uvs=[]
for e in els:
 lo,hi=e['from'],e['to'];r=e['rotation'];origin=mathutils.Vector(r['origin']);M=mathutils.Euler(tuple(math.radians(r.get(k,0)) for k in 'xyz'),'XYZ').to_matrix();cs=[M@(mathutils.Vector([hi[i] if m>>i&1 else lo[i] for i in range(3)])-origin)+origin for m in range(8)]
 for f,fc in [('south',e['faces']['south'])]:
  u1,v1,u2,v2=fc['uv'];b=len(verts)
  for k,(u,v) in zip(FACES[f],((u1,v1),(u2,v1),(u2,v2),(u1,v2))):p=cs[k];verts.append((p[2],8-p[0],p[1]));uvs.append((u/16,1-v/16))
  polys.append((b,b+1,b+2,b+3))
me=bpy.data.meshes.new('actual native JSON surfaces');me.from_pydata(verts,[],polys);uv=me.uv_layers.new()
for li,loop in enumerate(me.loops):uv.data[li].uv=uvs[loop.vertex_index]
me.materials.append(mat);ob=bpy.data.objects.new('actual native JSON',me);bpy.context.scene.collection.objects.link(ob)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=12;sc.cycles.use_denoising=True;sc.cycles.transparent_max_bounces=32;sc.render.use_compositing=False;sc.render.use_sequencer=False;sc.view_settings.view_transform='Standard';sc.render.film_transparent=True
sc.world.use_nodes=True;bg=sc.world.node_tree.nodes['Background'];bg.inputs[0].default_value=(.3,.32,.34,1);bg.inputs[1].default_value=.8
for ang,en in [((.8,.2,.5),1.8),((-.5,-.4,.3),.7),((2.6,.3,-2.5),.6)]:
 l=bpy.data.lights.new('proof sun','SUN');l.energy=en;l.angle=.1;ob=bpy.data.objects.new('proof sun',l);sc.collection.objects.link(ob);ob.rotation_euler=ang
frame=json.loads((ad/'r2-authored-solids.json').read_text())['sourceFrame'];lo,hi,top,L,z0,yt=frame;u=L/(hi-lo)
# The original side camera projects 1200 pixels across its orthographic width.
center=mathutils.Vector((z0+(600-lo)*u,0,yt-(350-top)*u));scale=1200*u
cam=bpy.data.cameras.new('fixed source side frame');cam.type='ORTHO';cam.ortho_scale=scale;co=bpy.data.objects.new('fixed source side frame',cam);sc.collection.objects.link(co);sc.camera=co;sc.render.resolution_x=1200;sc.render.resolution_y=700;sc.render.resolution_percentage=100
for name,d in [('side',(0,-1,0)),('oblique',(-.65,-1,.45)),('opposite_oblique',(.65,1,.45)),('top',(0,0,1)),('front',(-1,0,0))]:
 d=mathutils.Vector(d).normalized();co.location=center+d*60;co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(out/('native_'+name+'.png'));bpy.ops.render.render(write_still=True)
evidence=dict(renderer='Blender Cycles rendering the actual native JSON rectangles and atlas alpha; not an in-game framebuffer',partsSHA256=hashlib.sha256((ad/'parts.json').read_bytes()).hexdigest(),textureSHA256=hashlib.sha256((ROOT/f'src/main/resources/assets/destiny/textures/item/weapon/w350/{wid}.png').read_bytes()).hexdigest(),views={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('native_*.png'))})
(ad/'render-evidence-r2.json').write_text(json.dumps(evidence,indent=2)+'\n')
