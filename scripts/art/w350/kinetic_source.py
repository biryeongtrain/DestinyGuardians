import bpy,json,sys,mathutils,os,hashlib
wid,out=sys.argv[sys.argv.index('--')+1:];os.makedirs(out,exist_ok=True)
sc=bpy.context.scene
sc.frame_set(sc.frame_start)

sc.render.use_compositing=False
sc.render.use_sequencer=False
def unexclude(lc):
 lc.exclude=False;lc.hide_viewport=False
 for x in lc.children:unexclude(x)
unexclude(bpy.context.view_layer.layer_collection)
for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('Plane')]
pts=[o.matrix_world@mathutils.Vector(c) for o in meshes for c in o.bound_box]
lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
data={'blend':bpy.data.filepath,'sha256':hashlib.sha256(open(bpy.data.filepath,'rb').read()).hexdigest(),'lo':lo,'hi':hi,'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials if m]} for o in meshes],'armatures':[{'name':o.name,'bones':[{'name':b.name,'head':list(o.matrix_world@b.head_local),'tail':list(o.matrix_world@b.tail_local)} for b in o.data.bones]} for o in bpy.data.objects if o.type=='ARMATURE'],'actions':[{'name':a.name,'range':list(a.frame_range),'slots':[s.identifier for s in a.slots]} for a in bpy.data.actions],'materials':[{'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m.node_tree else []} for m in bpy.data.materials],'images':[{'name':i.name,'path':i.filepath,'size':list(i.size)} for i in bpy.data.images]}
json.dump(data,open(out+'/source-evaluation.json','w'),indent=2)
for o in bpy.data.objects:
 if o not in meshes:o.hide_render=True
for o in meshes:o.hide_render=False;o.hide_set(False)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
sc.render.resolution_x=1200;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc.world.color=(.18,.18,.18);sc.render.film_transparent=False
cam=bpy.data.cameras.new('W350_owned_camera');cam.type='ORTHO';co=bpy.data.objects.new('W350_owned_camera',cam);sc.collection.objects.link(co);sc.camera=co
c=mathutils.Vector([(lo[i]+hi[i])/2 for i in range(3)]);ext=max(hi[i]-lo[i] for i in range(3))*1.15
for name,vec in [('side',(0,1,0) if wid!='thorn' else (1,0,0)),('oblique',(.65,1,.45) if wid!='thorn' else (1,-.65,.45)),('top',(0,0,1))]:
 d=mathutils.Vector(vec).normalized();co.location=c+d*max(ext*3,3);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=ext;cam.clip_end=1000;sc.render.filepath=out+'/source_'+name+'.png';bpy.ops.render.render(write_still=True)

# Read-only material-color evidence using the supplied shader Bake_Color when present.
import os
files={}
for dp,ds,fs in os.walk(os.path.dirname(bpy.data.filepath)):
 for fn in fs:files.setdefault(fn.lower(),os.path.join(dp,fn))
for im in bpy.data.images:
 if im.source=='FILE' and not os.path.exists(bpy.path.abspath(im.filepath)):
  f=files.get(os.path.basename(im.filepath.replace('\\','/')).lower())
  if f:im.filepath=f;im.reload()
for m in bpy.data.materials:
 if not m.node_tree:continue
 nt=m.node_tree;em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=m.diffuse_color
 groups=[n for n in nt.nodes if n.type=='GROUP' and n.node_tree and 'Bake_Color' in n.outputs]
 tex=[n for n in nt.nodes if n.type=='TEX_IMAGE' and n.image and any(k in n.image.name.lower() for k in ('diffuse','albedo'))]
 if groups:nt.links.new(groups[0].outputs['Bake_Color'],em.inputs[0])
 elif tex:nt.links.new(tex[0].outputs[0],em.inputs[0])
 for n in [n for n in nt.nodes if n.type=='OUTPUT_MATERIAL']:nt.links.new(em.outputs[0],n.inputs[0])
sc.render.engine='CYCLES';sc.cycles.samples=4;sc.cycles.use_denoising=False;sc.cycles.max_bounces=0;sc.cycles.device='CPU';sc.view_settings.view_transform='Standard';sc.render.film_transparent=True
for name,vec in [('side',(1,0,0) if wid=='thorn' else (0,1,0)),('oblique',(1,-.65,.45) if wid=='thorn' else (.65,1,.45)),('top',(0,0,1))]:
 d=mathutils.Vector(vec).normalized();co.location=c+d*max(ext*3,3);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=ext;sc.render.filepath=out+'/source_material_'+name+'.png';bpy.ops.render.render(write_still=True)
