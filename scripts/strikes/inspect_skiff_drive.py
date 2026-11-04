"""Inspect/render the supplied Dusk skiff shader scene in an isolated Blender process.
blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python this.py -- SOURCE OUTPUT
Never saves the source .blend. Relinks image paths in memory only.
"""
import sys,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector

source, output = map(Path,sys.argv[sys.argv.index('--')+1:])
blend=source/'House of Dusk_Skiff.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend))
output.mkdir(parents=True,exist_ok=True)
images=[]
for image in bpy.data.images:
    old=image.filepath
    basename=old.replace('\\','/').rsplit('/',1)[-1]
    local=source/basename
    if local.is_file():image.filepath=str(local);image.reload()
    images.append(dict(name=image.name,originalPath=old,resolvedPath=image.filepath,
                       packed=bool(image.packed_file),size=list(image.size),loaded=bool(image.size[0])))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']
materials=[]
def nodes(tree):
    return [dict(name=n.name,type=n.bl_idname,
                 group=n.node_tree.name if n.type=='GROUP' and n.node_tree else None,
                 image=n.image.name if n.type=='TEX_IMAGE' and n.image else None)
            for n in tree.nodes]
for material in bpy.data.materials:
    materials.append(dict(name=material.name,nodes=nodes(material.node_tree) if material.node_tree else []))
report=dict(blend=str(blend),sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),blender=bpy.app.version_string,
            images=images,materials=materials,nodeGroups={g.name:nodes(g) for g in bpy.data.node_groups},
            meshes=[dict(name=o.name,vertices=len(o.data.vertices),polygons=len(o.data.polygons),
                         hidden=o.hide_render,materials=[s.material.name if s.material else None for s in o.material_slots]) for o in meshes],
            rigs=[dict(name=o.name,bones=[dict(name=b.name,parent=b.parent.name if b.parent else None,
                                            head=list(o.matrix_world@b.head_local)) for b in o.data.bones]) for o in rigs])
(output/'scene-audit.json').write_text(json.dumps(report,indent=2)+'\n')
visible=[o for o in meshes if not o.hide_render]
points=[o.matrix_world@Vector(c) for o in visible for c in o.bound_box]
low=Vector([min(p[i] for p in points) for i in range(3)]);high=Vector([max(p[i] for p in points) for i in range(3)])
center=(low+high)/2;extent=max(high-low)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.image_settings.media_type='IMAGE';scene.render.image_settings.file_format='PNG'
scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.world=bpy.data.worlds.new('SkiffInspectionWorld');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.15,.2,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
for obj in list(bpy.data.objects):
    if obj.type=='LIGHT':obj.hide_render=True
camera_data=bpy.data.cameras.new('SkiffInspectionCamera');camera=bpy.data.objects.new('SkiffInspectionCamera',camera_data)
scene.collection.objects.link(camera);camera.location=center+Vector((.9,-1.3,.65))*extent
camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='ORTHO';camera_data.ortho_scale=extent*1.15;scene.camera=camera
camera_data.clip_end=max(1000,extent*10);camera_data.clip_start=max(.0001,extent*.0001)
for name,offset,strength in [('Key',(.3,-.5,1),14),('Fill',(-.7,.2,.5),8)]:
    light=bpy.data.lights.new('SkiffInspection'+name,'AREA');light.energy=extent*extent*strength;light.size=extent*.65
    obj=bpy.data.objects.new(light.name,light);scene.collection.objects.link(obj);obj.location=center+Vector(offset)*extent
    obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='Standard'
scene.render.filepath=str(output/'source-shader-preview.png');bpy.ops.render.render(write_still=True)
print('SKIFF_DRIVE_INSPECTED',len(meshes),'meshes',[(o.name,len(o.data.bones)) for o in rigs],
      'missing images',[i['name'] for i in images if not i['loaded']])
