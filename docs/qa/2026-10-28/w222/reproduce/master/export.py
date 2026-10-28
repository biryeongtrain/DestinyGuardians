"""Read-only original Blender source61 evaluator; separate background process only."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path('/Users/qf/IdeaProjects/DestinyGuardians')
OUT=Path('/private/tmp/destiny-w222-source')
GROUPS={'bow_6239be39': 'biting_winds', 'scout_rifle_e4c9ea6c': 'long_arm', 'glaive_f9784d8f': 'nezarec_s_whisper'}
EXTRA={'leftShoulder':'D1232BA2','rightShoulder':'17025F50'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mat(m):return [list(row) for row in m]
def run():
 assert bpy.app.background
 report={'schemaVersion':1,'blenderVersion':bpy.app.version_string,'exporterSha256':sha(Path(__file__)),'space':'armature_object','matrixConvention':'row-major, column vectors; evaluated pose.bones.matrix, no matrix_world application','groups':{}}
 seen={}
 for group,weapon in GROUPS.items():
  cp=ROOT/'art/weapons/w205/rigs'/f'{group}.json';cache=json.loads(cp.read_text());blend=Path(cache['sourceBlend']);folder=blend.parents[1]
  paths={'sourceBlend':blend,'sourceMap':folder/'source-map.json','boneMap':folder/'bone-map.json','cache':cp}
  hashes={k:sha(p) for k,p in paths.items()};seen.update({str(p):hashes[k] for k,p in paths.items()})
  for k in ('sourceBlend','sourceMap','boneMap'):assert hashes[k]==cache[k+'Sha256'],(group,k,'cache provenance mismatch')
  bpy.ops.wm.open_mainfile(filepath=str(blend),load_ui=False,use_scripts=False)
  scene=bpy.context.scene;rigs=[o for o in scene.objects if o.type=='ARMATURE'];assert len(rigs)==1
  rig=rigs[0];names={**cache['names'],**EXTRA};bones={}
  for side in ('left','right'):
   sh,el,wr=[rig.data.bones[names[side+x]] for x in ('Shoulder','Elbow','Wrist')]
   assert wr.parent==el and el.parent==sh
   assert sh.parent.name=={'left':'038E2D3A','right':'A9D76416'}[side]
  for label,name in names.items():
   b=rig.data.bones[name];bones[label]={'name':name,'parent':b.parent.name if b.parent else None,'restMatrix':mat(b.matrix_local)}
  entry={'weapon':weapon,'paths':{k:str(v) for k,v in paths.items()},'inputSha256':hashes,'objects':[{'name':o.name,'type':o.type} for o in scene.objects],'fps':scene.render.fps,'fpsBase':scene.render.fps_base,'matrixWorld':mat(rig.matrix_world),'bones':bones,'actions':{}}
  cache['names']=names
  for tag,old in cache['actions'].items():
   actions=[a for a in bpy.data.actions if tag in a.name];assert len(actions)==1,(group,tag)
   a=actions[0];assert len(a.slots)==1
   rig.animation_data_create();rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
   assert list(a.frame_range)==[old['start'],old['end']]
   def evaluate(frame):
    scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
    e=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return {k:mat(e.pose.bones[n].matrix) for k,n in names.items()}
   errors=[]
   for f in old['frames']:
    joints=evaluate(f['frame']);errors.append(max(abs(m[i][j]-joints[k][i][j]) for k,m in f['joints'].items() for i in range(4) for j in range(4)))
   assert max(errors)<1e-5,(group,tag,max(errors))
   n=61 if len(old['frames'])>1 else 1
   frames=[]
   for i in range(n):
    progress=i/(n-1) if n>1 else 0.;frame=old['start']+(old['end']-old['start'])*progress
    frames.append({'progress':progress,'frame':frame,'joints':evaluate(frame)})
   cache['actions'][tag]={**old,'action':a.name,'frames':frames}
   entry['actions'][tag]={'action':a.name,'slot':a.slots[0].identifier,'sourceNames':old['sourceNames'],'sourceFrameRange':list(a.frame_range),'priorSamples':len(old['frames']),'samples':n,'maxExistingCacheJointAbsError':max(errors)}
  cache['w222Source61']={'exporterSha256':report['exporterSha256'],'blenderVersion':bpy.app.version_string,'shoulders':'evaluated original Blender shoulder->elbow->wrist','reloadSamples':61,'timing':'uniform normalized samples, original source range; gameplay duration unchanged','cameraExported':False}
  (OUT/(group+'.json')).write_text(json.dumps(cache,separators=(',',':'))+'\n')
  report['groups'][group]=entry
 for path,before in seen.items():assert sha(Path(path))==before,('input changed',path)
 report['allInputsUnchanged']=True
 (OUT/'source-review.json').write_text(json.dumps(report,indent=2)+'\n')
 print('W222_SOURCE61 '+json.dumps({g:v['actions'] for g,v in report['groups'].items()}))
run()
