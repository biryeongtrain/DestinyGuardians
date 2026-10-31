import bpy,json,math
from mathutils import Vector,Euler
from pathlib import Path
root=Path(__file__).resolve().parents[2]
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
img=bpy.data.images.load(str(root/"src/main/resources/assets/destiny/textures/item/tutorial/ghost.png"))
for file in (root/"src/main/resources/assets/destiny/models/tutorial/ghost").glob("*.json"):
 mat=bpy.data.materials.new(file.stem);mat.use_nodes=True;nodes=mat.node_tree.nodes;bsdf=nodes.get("Principled BSDF");tex=nodes.new("ShaderNodeTexImage");tex.image=img;tex.interpolation="Closest";mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"]);mat.node_tree.links.new(tex.outputs["Alpha"],bsdf.inputs["Alpha"]);bsdf.inputs["Roughness"].default_value=.65
 if file.stem.startswith("eye"):
  mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Emission Color"]);bsdf.inputs["Emission Strength"].default_value=2
 verts=[];faces=[];uvs=[]
 for e in json.loads(file.read_text())["elements"]:
  a=e["from"];b=e["to"];r=e["rotation"];o=Vector(r["origin"]);rot=Euler(tuple(math.radians(r[k]) for k in "xyz"),"XYZ").to_matrix()
  ps=[(a[0],a[1],a[2]),(b[0],a[1],a[2]),(b[0],b[1],b[2]),(a[0],b[1],b[2])];start=len(verts)
  for p in ps: verts.append(tuple((rot@(Vector(p)-o)+o-Vector((8,8,8)))/16))
  faces.append(tuple(range(start,start+4)));u,v,U,V=e["faces"]["south"]["uv"];uvs.extend([(u/16,1-V/16),(U/16,1-V/16),(U/16,1-v/16),(u/16,1-v/16)])
 mesh=bpy.data.meshes.new(file.stem);mesh.from_pydata(verts,[],faces);mesh.uv_layers.new()
 for i,uv in enumerate(uvs):mesh.uv_layers.active.data[i].uv=uv
 ob=bpy.data.objects.new(file.stem,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(mat)
scene=bpy.context.scene;scene.render.engine="CYCLES";scene.cycles.samples=24;scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100
scene.world.color=(.14,.14,.14)
bpy.ops.object.camera_add(location=(.5,.26,1.6));camera=bpy.context.object;camera.rotation_euler=(-camera.location).to_track_quat("-Z","Y").to_euler();camera.data.type="ORTHO";camera.data.ortho_scale=1.3;scene.camera=camera
for loc,power,size in [((1,2,3),160,3),((-2,0,1),90,2)]:
 bpy.ops.object.light_add(type="AREA",location=loc);bpy.context.object.data.energy=power;bpy.context.object.data.shape="DISK";bpy.context.object.data.size=size;bpy.context.object.rotation_euler=(-bpy.context.object.location).to_track_quat("-Z","Y").to_euler()
scene.render.filepath=str(root/"docs/qa/2026-10-31/w280/model-preview.png");bpy.ops.render.render(write_still=True)
