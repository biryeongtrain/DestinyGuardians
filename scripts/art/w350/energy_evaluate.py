import bpy,json,sys,mathutils,os,hashlib
wid,out=sys.argv[sys.argv.index('--')+1:];os.makedirs(out,exist_ok=True)
sc=bpy.context.scene
sc.render.use_compositing=False
sc.render.use_sequencer=False
def unexclude(lc):
 lc.exclude=False;lc.hide_viewport=False
 for x in lc.children:unexclude(x)
unexclude(bpy.context.view_layer.layer_collection)
for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.lower().startswith(('plane','boneshape'))]
pts=[o.matrix_world@mathutils.Vector(c) for o in meshes for c in o.bound_box]
lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
data={'blend':bpy.data.filepath,'sha256':hashlib.sha256(open(bpy.data.filepath,'rb').read()).hexdigest(),'lo':lo,'hi':hi,'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials if m]} for o in meshes],'armatures':[{'name':o.name,'bones':[{'name':b.name,'head':list(o.matrix_world@b.head_local),'tail':list(o.matrix_world@b.tail_local)} for b in o.data.bones]} for o in bpy.data.objects if o.type=='ARMATURE'],'actions':[{'name':a.name,'range':list(a.frame_range),'slots':[s.identifier for s in getattr(a,"slots",[])]} for a in bpy.data.actions],'images':[{'name':i.name,'path':i.filepath,'size':list(i.size)} for i in bpy.data.images]}
data['activeActions']=[{'object':o.name,'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'nla':[t.name for t in o.animation_data.nla_tracks] if o.animation_data else []} for o in bpy.data.objects]
data['actionChannels']=[]
for a in bpy.data.actions:
 channels=[]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    channels += [{'path':f.data_path,'index':f.array_index,'keys':len(f.keyframe_points)} for f in bag.fcurves]
 data['actionChannels'].append({'action':a.name,'channelCount':len(channels),'allUvChannels':all(c['path'].startswith('uv_layers') for c in channels),'channelSha256':hashlib.sha256(json.dumps(channels,sort_keys=True).encode()).hexdigest(),'sampleChannels':channels[:12]})
data['evaluatedFrames']=[]
for frame in [1,25,50]:
 sc.frame_set(frame)
 data['evaluatedFrames'].append({'frame':frame,'armatures':{o.name:{b.name:[list(row) for row in b.matrix] for b in o.pose.bones} for o in bpy.data.objects if o.type=='ARMATURE'}})
sc.frame_set(1)
json.dump(data,open(out+'/source-evaluation.json','w'),indent=2)
for o in bpy.data.objects:
 if o not in meshes:o.hide_render=True
for o in meshes:o.hide_render=False;o.hide_set(False)
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True
sc.render.resolution_x=1200;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc.world=sc.world or bpy.data.worlds.new("SourceReview");sc.world.color=(.18,.18,.18);sc.render.film_transparent=False
cam=bpy.data.cameras.new('W327_owned_camera');cam.type='ORTHO';co=bpy.data.objects.new('W327_owned_camera',cam);sc.collection.objects.link(co);sc.camera=co
c=mathutils.Vector([(lo[i]+hi[i])/2 for i in range(3)]);ext=max(hi[i]-lo[i] for i in range(3))*1.15
for name,vec in [('side',(0,1,0) if wid=='graviton_lance' else (1,0,0)),('oblique',(.65,1,.45) if wid=='graviton_lance' else (1,-.65,.45)),('top',(0,0,1))]:
 d=mathutils.Vector(vec).normalized();co.location=c+d*max(ext*3,3);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=ext;cam.clip_end=1000;sc.render.filepath=out+'/source_'+name+'.png';bpy.ops.render.render(write_still=True)
