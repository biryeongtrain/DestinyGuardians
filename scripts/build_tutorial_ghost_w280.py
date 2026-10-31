"""Run in background Blender with the supplied Generalist blend open; never saves source.
Builds a compact, UV-sampled native 26.3 display model. Hover/open motion is procedural.
"""
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/mesh"))
from native_triangle_elements_w115 import split_triangle,to_element
A=ROOT/"src/main/resources/assets/destiny"
arm=bpy.data.objects["Ghost_Armature"]
arm.animation_data.action=bpy.data.actions["GHOST_idle_hover_80A8A444"]
arm.animation_data.action_slot=arm.animation_data.action.slots[0]
bpy.context.scene.frame_set(1)
dg=bpy.context.evaluated_depsgraph_get()
def center(o):
 e=o.evaluated_get(dg); m=e.to_mesh(); c=sum((e.matrix_world@v.co for v in m.vertices),Vector())/len(m.vertices); e.to_mesh_clear(); return c
origin=center(bpy.data.objects["InnerCore_Sphere"])
front=(center(bpy.data.objects["Eye_Lens_Emissive"])-origin).normalized()
up=Vector((0,0,1)); right=up.cross(front).normalized(); up=front.cross(right).normalized()
def convert(v):
 d=v-origin
 return [8+d.dot(right)*120,8+d.dot(up)*120,8+d.dot(front)*120]
parts=[]; palette=[]; image_cache={}
objects=sorted([o for o in bpy.data.objects if o.type=="MESH" and o.name.startswith(("OuterShell","InnerCore","Eye_"))],key=lambda o:o.name)
for obj in objects:
 key=obj.name.lower(); target=36 if key.startswith("outershell") else (20 if key.startswith("eye") else 72)
 e=obj.evaluated_get(dg); mesh=bpy.data.meshes.new_from_object(e); copy=bpy.data.objects.new("EXPORT_"+key,mesh); bpy.context.collection.objects.link(copy); copy.matrix_world=obj.matrix_world
 mod=copy.modifiers.new("runtime_budget","DECIMATE"); mesh.calc_loop_triangles(); mod.ratio=min(1,target/max(1,len(mesh.loop_triangles))); mod.use_collapse_triangulate=True
 bpy.context.view_layer.update(); ce=copy.evaluated_get(bpy.context.evaluated_depsgraph_get()); m=ce.to_mesh(); m.calc_loop_triangles(); elems=[]
 for tri in m.loop_triangles:
  verts=[convert(ce.matrix_world@m.vertices[i].co) for i in tri.vertices]
  mat=m.materials[tri.material_index] if len(m.materials)>tri.material_index else None
  color=[.7,.72,.74]
  if key.startswith("eye"): color=[.08,.88,1]
  elif mat and mat.node_tree:
   tex=next((n.image for n in mat.node_tree.nodes if n.type=="TEX_IMAGE" and n.image and "albedo" in n.image.name),None)
   if tex and m.uv_layers.active:
    if tex.name not in image_cache: image_cache[tex.name]=(list(tex.pixels[:]),tuple(tex.size))
    pix,(w,h)=image_cache[tex.name]; uv=sum((m.uv_layers.active.data[i].uv for i in tri.loops),Vector((0,0)))/3
    ix=(int(uv.x*w)%w+(int(uv.y*h)%h)*w)*4
    color=[max(.035,min(1,pix[ix+i]*.7)) for i in range(3)]
  try: triangles=split_triangle(verts)
  except ValueError: continue
  for p in triangles:
   idx=len(palette); palette.append(color); x=idx%32; y=idx//32
   uv=[x*.5,y*.5,(x+1)*.5,(y+1)*.5]
   el=to_element(p,key,uv); el["shade"]=not key.startswith("eye"); el["light_emission"]=15 if key.startswith("eye") else 0; elems.append(el)
 path=A/f"models/tutorial/ghost/{key}.json"; path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps({"ambientocclusion":False,"textures":{"0":"destiny:item/tutorial/ghost","particle":"destiny:item/tutorial/ghost"},"elements":elems},separators=(",",":")))
 ip=A/f"items/tutorial/ghost/{key}.json"; ip.parent.mkdir(parents=True,exist_ok=True); ip.write_text(json.dumps({"model":{"type":"minecraft:model","model":f"destiny:tutorial/ghost/{key}"}}))
 c=convert(center(obj)); parts.append({"name":key,"elements":len(elems),"radial":[(v-8)/16 for v in c]})
 ce.to_mesh_clear(); bpy.data.objects.remove(copy,do_unlink=True)
assert len(palette)<=1024,len(palette)
# 32x32 palette tiles; alpha triangle represents actual silhouette, not opaque quads.
size=2048; pixels=[0.]*(size*size*4)
for idx,col in enumerate(palette):
 tx=idx%32*64; ty=idx//32*64
 for y in range(64):
  for x in range(64):
   off=((size-1-(ty+y))*size+tx+x)*4
   pixels[off:off+4]=col+[1. if x<=y else 0.]
image=bpy.data.images.new("RuntimeGhostAtlas",width=size,height=size,alpha=True); image.pixels=pixels
p=A/"textures/item/tutorial/ghost.png"; p.parent.mkdir(parents=True,exist_ok=True); image.filepath_raw=str(p); image.file_format="PNG"; image.save()
report={"source_sha256":hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),"source_action":arm.animation_data.action.name,"root_removed":list(origin),"front":list(front),"parts":parts,"elements":len(palette),"motion":"procedural hover and radial shell opening; not extracted clip playback","texture":"source albedo sampled per reduced triangle; dye multiplied 0.7; no normal/gstack shader"}
(ROOT/"art/ghost/w280/model-manifest.json").write_text(json.dumps(report,indent=2))
print(json.dumps(report))
