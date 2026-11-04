import bpy,json,math,sys,colorsys
from mathutils import Vector,Matrix
model='fallen_dreg__80E1AFCF';inc='80E1AFCF'
root='/Users/qf/Downloads/Rising-Guardian-2026-11-01/models/'+model
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=f'{root}/{model}.fbx')
R=Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Rotation(-math.pi/2,4,'X')@Matrix.Scale(100,4)
for o in list(bpy.data.objects):
    if o.parent is None: o.matrix_world=R@o.matrix_world
bpy.context.view_layer.update()
mats=sorted({m.name.split('.')[0] for m in bpy.data.materials})
out={'tris':[]}
dg=bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type!='MESH': continue
    vis= o.name.split('_')[0]==inc and 'InternalGeom' not in o.name
    o.hide_render=not vis
    if not vis: continue
    me=o.evaluated_get(dg).to_mesh(); mw=o.matrix_world
    for p in me.polygons:
        mn=o.material_slots[p.material_index].material.name.split('.')[0] if o.material_slots else '?'
        c=mw@p.center; n=(mw.to_3x3()@p.normal).normalized()
        out['tris'].append([round(c.x,4),round(c.y,4),round(c.z,4),round(n.x,3),round(n.y,3),round(n.z,3),mn,o.name])
json.dump(out,open('/tmp/dreg_src_tris.json','w'))
# material id render
import random
used=sorted({t[6] for t in out['tris']})
for i,mn in enumerate(used):
    r,g,b=((1,0,0) if mn in ("80E12DD0","80E12F18") else (0.5,0.5,0.5))
    for m in bpy.data.materials:
        if m.name.split('.')[0]==mn: m.diffuse_color=(r,g,b,1)
print('USED',[(i,mn,sum(1 for t in out['tris'] if t[6]==mn)) for i,mn in enumerate(used)])
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='FLAT';sc.display.shading.color_type='MATERIAL'
sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=800
pts=[Vector(t[:3]) for t in out['tris']];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)])
print('BBOX',list(lo),list(hi))
cam=bpy.data.cameras.new('c');cam.type='ORTHO';co=bpy.data.objects.new('c',cam);sc.collection.objects.link(co);sc.camera=co
ctr=(lo+hi)/2;size=max(hi-lo)*1.12;cam.ortho_scale=size;cam.clip_start=size*.01;cam.clip_end=size*30
for tag,d in {'front':(0,1,0.05),'back':(0,-1,0.05)}.items():
    dv=Vector(d).normalized();co.location=ctr+dv*size*4;co.rotation_euler=(-dv).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f'/tmp/dreg_matid_{tag}.png';bpy.ops.render.render(write_still=True)
