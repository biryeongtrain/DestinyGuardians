import bpy,json,mathutils,os
O='/tmp/exotic-expansion-20261109/whisper-r3/source-detail';os.makedirs(O,exist_ok=True)
meshes=[]
for o in bpy.data.objects:
 if o.type=='MESH' and not o.name.startswith(('Plane','CustomBone')):
  pts=[o.matrix_world@v.co for v in o.data.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
  meshes.append({'name':o.name,'lo':lo,'hi':hi,'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials if m]})
json.dump(meshes,open(O+'/mesh-bounds.json','w'),indent=2)
for m in bpy.data.materials:
 pass
 # print('MAT',m.name,[(n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else None) for n in m.node_tree.nodes] if m.use_nodes else None)
# print bounds

sc=bpy.context.scene;sc.render.use_compositing=False;sc.render.use_sequencer=False
helpers={b.custom_shape for a in bpy.data.objects if a.type=='ARMATURE' for b in a.pose.bones if b.custom_shape}
keep=[];hidden=[]
FX={'79B5EA80','6DB5EA80','6FB5EA80','7A30EB80','6DE8EA80','A6E1CF80','737EEB80','887EEB80'}
for o in bpy.data.objects:
 if o.type=='MESH' and o not in helpers and not o.name.startswith(('Plane','CustomBone')) and not any(m and m.name in FX for m in o.data.materials):keep.append(o);o.hide_render=False;o.hide_set(False)
 else:o.hide_render=True;hidden.append(o.name)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(.55,.55,.55);sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH'
sc.render.resolution_x=1200;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.world.color=(.18,.18,.18)
deps=bpy.context.evaluated_depsgraph_get();bounds=[]
for o in keep:
 ev=o.evaluated_get(deps);me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)];bounds.append(dict(name=o.name,lo=lo,hi=hi));ev.to_mesh_clear()
json.dump(dict(visible=bounds,hiddenFx=hidden),open(O+'/evaluated-solid-parts.json','w'),indent=2)
lo=[min(q['lo'][i] for q in bounds) for i in range(3)];hi=[max(q['hi'][i] for q in bounds) for i in range(3)]
cam=bpy.data.cameras.new('OwnedR3');cam.type='ORTHO';co=bpy.data.objects.new('OwnedR3',cam);sc.collection.objects.link(co);sc.camera=co
ev=json.load(open('/tmp/exotic-expansion-20261109/sources/whisper_of_the_worm/evaluation/source-evaluation.json'));lo=ev['lo'];hi=ev['hi'];C=mathutils.Vector([(lo[i]+hi[i])/2 for i in range(3)]);L=max(hi[i]-lo[i] for i in range(3))
for label,vec in [('side',(0,1,0)),('oblique',(.65,1,.45)),('opposite',(.65,-1,.45))]:
 v=mathutils.Vector(vec).normalized();co.location=C+v*L*3;co.rotation_euler=(-v).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=L*1.15;sc.render.filepath=O+'/solid_'+label+'.png';bpy.ops.render.render(write_still=True)
