"""R2-only Hunter full composed locomotion retarget. Run using an owned background Blender process.
R1 package/mappings/upper-mask results are excluded. Originals and installed/runtime files are read-only.
"""
import argparse,copy,gzip,hashlib,importlib.util,json,math,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
from mathutils import Matrix,Vector
C=Matrix(((0,-1,0,0),(0,0,1,0),(-1,0,0,0),(0,0,0,1)))
NAMESPACE=uuid.UUID('65a153c2-7336-4de1-a8f4-533600000002')
BODY={'phip_hip':'C7C0BA6E','pw_waist':'A252A6A2','pc_chest':'A352A6A2','h_ph_head':'7E92D640'}
LIMBS=[('pra_right_arm','prfa_right_forearm',['17025F50','A3781DCD','DE9D6BEA']),('pla_left_arm','plfa_left_forearm',['D1232BA2','897A1504','8C83CB67']),('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]
ITEMS={'pri_right_item':'DE9D6BEA','pli_left_item':'8C83CB67'}
MAP={**BODY,**ITEMS,**{a:ns[0]for a,b,ns in LIMBS},**{b:ns[1]for a,b,ns in LIMBS}}
SELECTED=set(MAP.values())|{n for _,_,ns in LIMBS for n in ns}|{'1A5C68E5','6B138432','9D7EE73A','A152A6A2','0D4EBB10','A9D76416','038E2D3A'}
def uid(s):return str(uuid.uuid5(NAMESPACE,s))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def vec(v):return[float(x)for x in v]
def mat(m):return[vec(r)for r in m]
def axis(m):return Matrix(m).to_quaternion().normalized().to_matrix().to_4x4()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def frame(x,y):
 y=Vector(y).normalized();x=Vector(x);x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized();return Matrix((x,y,z)).transposed().to_4x4()
def nearest(a,prev):
 if prev is None:return a
 variants=[a,[a[0]+180,180-a[1],a[2]+180]];options=[[x+360*round((y-x)/360)for x,y in zip(v,prev)]for v in variants];return min(options,key=lambda v:sum((x-y)**2 for x,y in zip(v,prev)))
def sample_target(clip,t,h19):
 pose,root=h19.sample(clip,t);positions={}
 for b in clip['animators'].values():
  ks=sorted((k for k in b['keyframes']if k['channel']=='position'),key=lambda k:k['time'])
  if not ks or b['name']=='player_root':continue
  a=max((k for k in ks if k['time']<=t),key=lambda k:k['time'],default=ks[0]);z=min((k for k in ks if k['time']>=t),key=lambda k:k['time'],default=ks[-1]);f=(t-a['time'])/(z['time']-a['time'])if z['time']>a['time']else 0
  positions[b['name']]=[(1-f)*a['data_points'][0][v]+f*z['data_points'][0][v]for v in 'xyz']
 return pose,positions,root

def main(args):
 assert bpy.app.background,'Use independent headless Blender'
 repo=Path(args.repo_root);package=Path(args.source_root);out=Path(args.output);cache=Path(args.cache);out.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
 assert package.name.endswith('-R2')and Path(bpy.data.filepath).name=='Guardian_Super_Composed_R2.blend'
 sys.path.insert(0,str(repo/'scripts'));import build_hunter_animation_h15 as h15;import build_hunter_animation_h19 as h19
 spec=importlib.util.spec_from_file_location('art_helpers',repo/'scripts/art/w330_arc_staff.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
 modelPath=repo/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel';model=json.loads(modelPath.read_text());groups={g['name']:g for g in model['groups']};parents={}
 def walk(ns,parent=None):
  for n in ns:
   if isinstance(n,str):continue
   name=next(g['name']for g in model['groups']if g['uuid']==n['uuid']);parents[name]=parent;walk(n['children'],name)
 walk(model['outliner'])
 def fk(p,positions,root=0):return arc.articulation_fk(model,p,positions,root,h15)
 identity=h15.zero();restTarget=fk(identity,{});rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_create();rest={b.name:mat(b.matrix_local)for b in rig.data.bones}
 frozenPaths=[repo/'src/main/resources/destiny/animation/arc_staff_w330.animation.json',repo/'src/main/resources/destiny/animation/spectral_blades_w330.animation.json',repo/'src/main/resources/destiny/animation/super_motion_w332.animation.json'];frozen={str(p):sha(p)for p in frozenPaths}
 inputs=[Path(bpy.data.filepath),package/'README.md',package/'HANDOFF.md',package/'CATALOG.json',package/'families/spectral_blades.json',package/'families/arc_staff_candidate.json',modelPath,repo/'scripts/art/w330_arc_staff.py',repo/'src/main/resources/destiny/animation/hunter_w199.animation.json',repo/'art/animation/w330/spectral_blades/spectral_blades_w330.animation.json'];hashes={str(p):sha(p)for p in inputs}
 jobs=[];families={};beforeClips={}
 for family,prefix in [('spectral_blades','w230_hunter_spectral_blades'),('arc_staff_candidate','h15_super_arc')]:
  d=json.loads((package/'families'/f'{family}.json').read_text());families[family]=d
  resource=inputs[-1]if family=='spectral_blades'else inputs[-2];old=json.loads(resource.read_text());beforeClips[family]=next(c for c in old['animations']if c['name']==prefix+'_move')
  for role in ['idle','move_forward_v1','move_backward_v1','move_left_v1','move_right_v1']:
   entry=next(c for c in d['clips']if c['role']==role);direction=role.replace('_v1','');name=(prefix+'_idle'if family=='spectral_blades'else prefix)if direction=='idle'else prefix+'_'+direction
   jobs.append({'family':family,'direction':direction,'name':name,'source':entry})
 sampled={};inventory=[]
 for job in jobs:
  entry=job['source'];action=bpy.data.actions.get(entry['action']);assert action,entry['action'];rig.animation_data.action=action
  if action.slots:rig.animation_data.action_slot=action.slots[0]
  start,end=map(float,action.frame_range);length=(end-start)/30;assert abs(length-entry['duration'])<1e-7;rows=[]
  for i in range(round(length*60)+1):
   t=i/60;f=start+t*30;bpy.context.scene.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update();evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());rows.append({'time':round(t,9),'matrices':{n:mat(evaluated.pose.bones[n].matrix)for n in SELECTED}})
  sampled[entry['action']]={'length':length,'rows':rows};inventory.append({'action':action.name,'slot':action.slots[0].identifier,'frames':[start,end],'seconds':length,'actual_evaluated_poses':len(rows)})
 with gzip.open(cache/'actual-composed-world-samples.json.gz','wt')as f:json.dump(sampled,f,separators=(',',':'))
 def floor(p,positions):
  transforms=fk(p,positions);heights=[]
  for n in ['prfl_right_foreleg','plfl_left_foreleg']:
   m=Matrix(transforms[n])
   for x in [-1.875,1.875]:
    for z in [-1.875,1.875]:heights.append((m@Vector((x,-5.625,z))).y)
  return -min(heights)
 sourceLeg=sum((Matrix(rest[b]).translation-Matrix(rest[a]).translation).length for a,b in [('9F0FD28C','8BD44A3F'),('8BD44A3F','B9B9E05D')]);pelvisScale=11.125/sourceLeg
 def local_delta(m,child,parent):
  cur=Matrix(m[parent]).inverted()@Matrix(m[child]).translation;ref=Matrix(rest[parent]).inverted()@Matrix(rest[child]).translation
  return C.to_3x3()@axis(rest[parent]).to_3x3()@(cur-ref)*16
 clips=[];audit=[];reviews=[]
 for job in jobs:
  entry=job['source'];family=job['family'];rows=sampled[entry['action']]['rows'];length=sampled[entry['action']]['length'];prepared=[];gripShifts=[];residuals=[]
  refRows=sampled[next(j['source']['action']for j in jobs if j['family']==family and j['direction']=='idle')]['rows'];ref=refRows[0]['matrices'];refPoints={n:C.to_3x3()@Matrix(m).translation for n,m in ref.items()}
  gripAxis=(refPoints['8C83CB67']-refPoints['DE9D6BEA']).normalized();shaftReference=frame((C@axis(ref['DE9D6BEA'])).to_3x3()@Vector((1,0,0)),gripAxis)
  for row in rows:
   m=row['matrices'];points={n:C.to_3x3()@Matrix(v).translation for n,v in m.items()};p=h15.zero();positions={};worlds={}
   for target,bone in BODY.items():worlds[target]=C@axis(m[bone])@axis(rest[bone]).inverted()@C.inverted()
   for upper,lower,chain in LIMBS:
    for target,a,b in [(upper,chain[0],chain[1]),(lower,chain[1],chain[2])]:
     down=(points[b]-points[a]).normalized();pred=C@axis(m[a])@axis(rest[a]).inverted()@C.inverted();worlds[target]=frame(pred.to_3x3()@Vector((1,0,0)),-down)
   for target,bone in MAP.items():
    parent=parents[target]
    if parent and parent in MAP:positions[target]=vec(local_delta(m,bone,MAP[parent]))
   positions['phip_hip']=vec(local_delta(m,'C7C0BA6E','1A5C68E5')*(pelvisScale/16))
   # Wrist/ankle links keep target lengths; only collapsed clavicle/spine/neck channel deltas translate pivots.
   for n in ['prfa_right_forearm','plfa_left_forearm','prfl_right_foreleg','plfl_left_foreleg','pri_right_item','pli_left_item']:
    if n in positions:positions[n]=[0,0,0]
   for n in ['phip_hip','pw_waist','pc_chest','h_ph_head','prl_right_leg','prfl_right_foreleg','pll_left_leg','plfl_left_foreleg']:
    cur=fk(p,positions);parent=parents[n];r=axis(cur[parent])if parent else Matrix.Identity(4);p[n]=h19.sub(h19.euler(mat(r.inverted()@worlds[n])),groups[n].get('rotation',[0,0,0]))
   cur=fk(p,positions);chest=Vector(h19.point(cur['pc_chest'],[0,0,0]));wrists={side:chest+(points[bone]-points['A352A6A2'])*16 for side,bone in [('right','DE9D6BEA'),('left','8C83CB67')]}
   shoulders={side:Vector(h19.point(cur[n],[0,0,0]))for side,n in [('right','pra_right_arm'),('left','pla_left_arm')]};shift=Vector((0,0,0))
   for _ in range(24):
    for side in ['right','left']:
     center=shoulders[side]-wrists[side];d=shift-center
     if d.length>10.9:shift=center+d.normalized()*10.9
   gripShifts.append(shift.length)
   for side,upper,fore,item,bones in [('right','pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA']),('left','pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67'])]:
    s=shoulders[side];target=wrists[side]+shift;l1=5.5;a=groups[item]['origin'][0]-groups[fore]['origin'][0];longitudinal=groups[fore]['origin'][1]-groups[item]['origin'][1];l2=math.hypot(a,longitudinal);delta=target-s;distance=delta.length;along=delta.normalized();center=(l1*l1-l2*l2+distance*distance)/(2*distance);radius=math.sqrt(max(0,l1*l1-center*center))
    sourceElbow=chest+(points[bones[1]]-points['A352A6A2'])*16+shift;bias=sourceElbow-s;swivel=bias-along*bias.dot(along)
    if swivel.length<1e-5:swivel=worlds[upper].to_3x3()@Vector((1,0,0));swivel-=along*swivel.dot(along)
    elbow=s+along*center+swivel.normalized()*radius
    desiredUpper=worlds[upper];actualUpper=desiredUpper.to_3x3()@Vector((0,-l1,0));upperR=actualUpper.rotation_difference(elbow-s).to_matrix().to_4x4()@desiredUpper
    desiredFore=worlds[fore];actualFore=desiredFore.to_3x3()@Vector((a,-longitudinal,0));foreR=actualFore.rotation_difference(target-elbow).to_matrix().to_4x4()@desiredFore
    parentR=axis(fk(p,positions)[parents[upper]]);p[upper]=h19.sub(h19.euler(mat(parentR.inverted()@upperR)),groups[upper].get('rotation',[0,0,0]));p[fore]=h19.sub(h19.euler(mat(upperR.inverted()@foreR)),groups[fore].get('rotation',[0,0,0]))
    if family=='arc_staff_candidate'and side=='right':itemR=C@axis(m[bones[2]])@axis(ref[bones[2]]).inverted()@C.inverted()@shaftReference
    else:itemR=C@axis(m[bones[2]])@axis(rest[bones[2]]).inverted()@C.inverted()@axis(restTarget[item])
    p[item]=h19.sub(h19.euler(mat(foreR.inverted()@itemR)),groups[item].get('rotation',[0,0,0]));actual=Vector(h19.point(fk(p,positions)[item],[0,0,0]));residuals.append((actual-target).length)
   root=floor(p,positions);cur=fk(p,positions,root);prepared.append({'time':row['time'],'pose':p,'positions':positions,'rootY':root,'fk':cur})
  name=job['name'];animators={}
  for bone in identity:
   keys=[];prev=None;prevQ=None
   for f in prepared:
    angles=nearest(f['pose'][bone],prev);q=Matrix(h15.rot(angles)).to_quaternion().normalized()
    if prevQ is not None and prevQ.dot(q)<0:q.negate()
    prev=angles;prevQ=q.copy();keys.append({'uuid':uid(name+'/'+bone+'/r/'+str(f['time'])),'channel':'rotation','time':f['time'],'interpolation':'linear','data_points':[dict(zip('xyz',[round(v,7)for v in angles]))],'destiny_quaternion':[round(q.x,10),round(q.y,10),round(q.z,10),round(q.w,10)]})
   if bone=='player_root':
    for f in prepared:keys.append({'uuid':uid(name+'/root/p/'+str(f['time'])),'channel':'position','time':f['time'],'interpolation':'linear','data_points':[{'x':0,'y':round(f['rootY'],7),'z':0}]})
   elif any(Vector(f['positions'].get(bone,(0,0,0))).length>.00001 for f in prepared):
    for f in prepared:keys.append({'uuid':uid(name+'/'+bone+'/p/'+str(f['time'])),'channel':'position','time':f['time'],'interpolation':'linear','data_points':[dict(zip('xyz',[round(v,7)for v in f['positions'].get(bone,(0,0,0))]))]})
   if bone in ITEMS:
    for t in [0,round(length,9)]:keys.append({'uuid':uid(name+'/'+bone+'/s/'+str(t)),'channel':'scale','time':t,'interpolation':'linear','data_points':[dict.fromkeys('xyz',1)]})
   animators[groups[bone]['uuid']]={'name':bone,'type':'bone','keyframes':keys}
  clips.append({'name':name,'uuid':uid(name),'length':round(length,9),'loop':'loop','snapping':60,'destiny_quaternion_sampling':True,'destiny_entry_blend_ticks':1,'destiny_exit_blend_ticks':2,'destiny_source_family':family,'destiny_source_action':entry['action'],'destiny_source_base':entry['base'],'destiny_source_layers':entry['bake']['layers'],'destiny_source_period_seconds':length,'animators':animators})
  seam=max(math.degrees(axis(prepared[0]['fk'][b]).to_quaternion().rotation_difference(axis(prepared[-1]['fk'][b]).to_quaternion()).angle)for b in identity)
  foots=[[Vector(h19.point(f['fk'][n],[0,-5.625,0]))for n in ['prfl_right_foreleg','plfl_left_foreleg']]for f in prepared];velocities=[]
  for k in [0,1]:
   heights=sorted(r[k].y for r in foots);threshold=heights[max(0,int(len(heights)*.3)-1)]
   for aa,bb in zip(foots,foots[1:]):
    if aa[k].y<=threshold+.05 and bb[k].y<=threshold+.05:velocities.append((bb[k]-aa[k])*60/16)
  inferred=-sum(velocities,Vector((0,0,0)))/len(velocities)if velocities else Vector((0,0,0));inferred.y=0
  direction=('move_forward'if abs(inferred.z)>abs(inferred.x)and inferred.z<0 else'move_backward'if abs(inferred.z)>abs(inferred.x)else'move_right'if inferred.x>0 else'move_left')if inferred.length>.03 else'idle'
  audit.append({'clip':name,'source_family':family,'source_action':entry['action'],'source_composition':entry,'length_seconds':length,'source_attribution':'R2 named_conditional weapon05943777 void_blades; latest explicit user choice supersedes ACC99940'if family=='spectral_blades'else'R2 group37 shared staff candidate, not exact confirmed Arc Staff state','old_upper_mask_used':False,'source_full_body_arms_and_grip':True,'max_coherent_hand_reach_shift_units':max(gripShifts),'max_wrist_IK_residual_units':max(residuals),'loop_world_rotation_gap_degrees':seam,'loop_root_y_gap_units':abs(prepared[-1]['rootY']-prepared[0]['rootY']),'estimated_target_stance_move_xyz_mps':vec(inferred),'estimated_target_direction':direction,'root_world_displacement_exported':[0,0]})
  if job['direction']=='move_forward':reviews.append((job,rows,prepared))
 dump(out/'super_locomotion_hunter_w336.animation.json',{'schema_version':1,'source_revision':'R2','animations':clips})
 dump(out/'manifest.json',{'source_revision':'R2','status':'full R2 composed source retarget candidate; native acceptance pending','actual_blend':bpy.data.filepath,'source_package':str(package),'blender':bpy.app.version_string,'source_input_sha256':hashes,'frozen_action_resources_sha256':frozen,'actual_actions':inventory,'rig_bones':len(rig.data.bones),'library_action_count':len(bpy.data.actions),'armature_world_after_evaluation':mat(rig.matrix_world),'space':'Actual evaluated armature-object matrices include rest. Source rest is used only to compute retarget deltas, never added twice. Root/world displacement is not exported; source pelvis-relative sway remains visual.','pelvis_translation_units_per_source_meter':pelvisScale,'retarget':'Pelvis sway scales by measured target/source leg-length ratio. Coupled hips/spine/neck/clavicle translations and full rotations; both arms/forearms retain source twist by minimal swing correction to voxel arm lengths, no frozen old-ready upper mask. Hand paths move together only if required by target reach.','limitations':'Rig has no independent fingers/ankles; composed driver/preset omissions remain the R2 catalog limitations, not a full original-game runtime claim. Arc candidate still unconfirmed.','superseded':'R1 generated data and prior ACC99940 selection are quarantined privately; neither is a production input.','clips':audit})
 for p,digest in{**hashes,**frozen}.items():assert sha(p)==digest,'Read-only source drift '+p
 render_review(out,model,reviews,beforeClips,fk,h15,h19)
 print('R2_HUNTER_EXPORTED',[(r['clip'],r['length_seconds'],r['max_coherent_hand_reach_shift_units'],r['max_wrist_IK_residual_units'],r['estimated_target_direction'])for r in audit])

def render_review(out,model,jobs,beforeClips,fk,h15,h19):
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
 def material(name,color):
  m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
 gray=material('unchanged player rig',(.4,.5,.6));orange=material('right arm',(.95,.5,.18));blue=material('left arm',(.2,.65,.95));cyan=material('source base joints',(.2,.9,.95));white=material('label',(.9,.95,1));parents={};groups={g['uuid']:g for g in model['groups']}
 def walk(ns,g=None):
  for n in ns:
   if isinstance(n,str):parents[n]=g
   else:walk(n['children'],n['uuid'])
 walk(model['outliner'])
 def point(v,col,row,scale=1/16):return Vector((v[0]*scale+col*2.5,-v[2]*scale,v[1]*scale+row*2.4))
 def label(text,col,row):
  d=bpy.data.curves.new('review label','FONT');d.body=text;d.size=.105;o=bpy.data.objects.new('review label',d);bpy.context.collection.objects.link(o);o.location=(col*2.5-1,-.8,row*2.4+2.05);o.rotation_euler=(math.pi/2,0,0);d.materials.append(white)
 def segment(a,b,r):
  delta=b-a
  if delta.length<1e-7:return
  bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=delta.length,location=(a+b)/2);o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=delta.to_track_quat('Z','Y');o.data.materials.append(cyan)
 def cubes(matrices,col,row):
  for e in model['elements']:
   g=groups[parents[e['uuid']]]
   if g['name']in['shadow','tag_name']:continue
   matrix=Matrix(matrices[g['name']]);origin=Vector(g['origin']);lo,hi=e['from'],e['to'];v=[]
   for x,y,z in [(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])]:v.append(point(matrix@Vector((x-origin.x,y-origin.y,z-origin.z,1)),col,row))
   mesh=bpy.data.meshes.new('unchanged cube');mesh.from_pydata(v,[],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(4,0,3,7)]);o=bpy.data.objects.new('unchanged cube',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(orange if g['name'].startswith(('pra_','prfa_'))else blue if g['name'].startswith(('pla_','plfa_'))else gray)
 for family,(job,rows,prepared)in enumerate(jobs):
  for phaseIndex,phase in enumerate([0,.25,.5]):
   col=family*3+phaseIndex;i=round((len(rows)-1)*phase);row=rows[i];points={n:C.to_3x3()@Matrix(m).translation for n,m in row['matrices'].items()}
   for chain in [['C7C0BA6E','A252A6A2','A352A6A2','7E92D640'],['A352A6A2','17025F50','A3781DCD','DE9D6BEA'],['A352A6A2','D1232BA2','897A1504','8C83CB67'],['C7C0BA6E','9F0FD28C','8BD44A3F','B9B9E05D'],['C7C0BA6E','695DAF09','35B14D1B','0F8B505D']]:
    for aa,bb in zip(chain,chain[1:]):segment(point(points[aa],col,2,1),point(points[bb],col,2,1),.018)
   old=beforeClips[job['family']];op,oz,oy=sample_target(old,phase*old['length'],h19);cubes(fk(op,oz,oy),col,1);cubes(prepared[i]['fk'],col,0)
   short='R2 named Spectral'if family==0 else'R2 Arc candidate';label(short+' source base '+str(round(row['time'],3))+'s',col,2);label('BEFORE accepted move',col,1);label('AFTER R2 full coupled pose',col,0)
 cameraData=bpy.data.cameras.new('owned review');camera=bpy.data.objects.new('owned review',cameraData);bpy.context.collection.objects.link(camera);camera.location=(6.25,-28,3.5);camera.rotation_euler=(Vector((6.25,0,3.5))-camera.location).to_track_quat('-Z','Y').to_euler();cameraData.type='ORTHO';cameraData.ortho_scale=15.4;scene=bpy.context.scene;scene.camera=camera;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=2100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD'
 if scene.world is None:scene.world=bpy.data.worlds.new('owned review')
 scene.world.color=(.018,.024,.036);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.render.filepath=str(out/'source-before-after.png');bpy.ops.render.render(write_still=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo-root',required=True);p.add_argument('--source-root',required=True);p.add_argument('--output',required=True);p.add_argument('--cache',required=True);main(p.parse_args(sys.argv[sys.argv.index('--')+1:]))
