"""Evaluate the original 72-bone .blend actions in an isolated headless process.
Run Blender --background --factory-startup --disable-autoexec --python THIS --
  --source-root /Volumes/qf-ssd/Destiny-Class-Ability-Motions-2026-10-30
  --output /private/tmp/destiny-w255/class-worker/evaluated-source.json
Never saves a .blend, mutates the SSD, or touches the user's live scene.
"""
import bpy,json,hashlib,math,argparse,sys
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-root',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
SOURCE=args.source_root.resolve()
OUT=args.output.resolve()
if OUT.is_relative_to(SOURCE): raise ValueError('Source tree is read-only')
if not bpy.app.background: raise RuntimeError('Use an isolated headless Blender process')
if bpy.context.preferences.filepaths.use_scripts_auto_execute: raise RuntimeError('Pass --disable-autoexec')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
index=json.loads((SOURCE/'CLIPS.json').read_text())
result={'blenderVersion':bpy.app.version_string,'sampleCountPerClip':61,'sourceRoot':str(SOURCE),'sampleSpace':'armature_object','autoexecDisabled':True,'sourceHashes':{},'groups':[]}
paths={Path('CLIPS.json'),Path('bone-map.json'),Path('README.md')}
for c in index:
 paths.update(Path(c[k]) for k in ('blend','fbx','contactSheet','preview'))
 paths.add(Path(c['blend']).parent/'clips.json')
result['sourceHashes']={str(p):sha(SOURCE/p) for p in sorted(paths)}
for relative in dict.fromkeys(c['blend'] for c in index):
 src=SOURCE/relative
 bpy.ops.wm.open_mainfile(filepath=str(src))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
 group={'source':relative,'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'matrixWorld':[list(r) for r in rig.matrix_world],'scale':list(rig.scale),'rotation':list(rig.rotation_euler),'sceneFps':bpy.context.scene.render.fps,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones],'clips':[]}
 for entry in (c for c in index if c['blend']==relative):
  action=bpy.data.actions[entry['action']]
  rig.animation_data_create();rig.animation_data.action=action
  if len(action.slots):rig.animation_data.action_slot=action.slots[0]
  if rig.animation_data.nla_tracks:
   for track in rig.animation_data.nla_tracks: track.mute=True
  frames=[]
  for i in range(61):
   f=entry['firstFrame']+(entry['lastFrame']-entry['firstFrame'])*i/60
   bpy.context.scene.frame_set(math.floor(f),subframe=f-math.floor(f));bpy.context.view_layer.update()
   ev=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
   frames.append({'frame':f,'joints':{b.name:[list(r) for r in b.matrix] for b in ev.pose.bones}})
  assert all(math.isfinite(v) for frame in frames for matrix in frame['joints'].values() for row in matrix for v in row)
  events=next(c['events'] for c in json.loads((src.parent/'clips.json').read_text()) if c['tag']==entry['tag'])
  group['clips'].append({**entry,'eventsUninterpreted':events,'actualFrameRange':list(action.frame_range),'frames':frames})
 result['groups'].append(group)
 print('EVALUATED',relative,len(rig.data.bones),len(group['clips']),flush=True)
assert result['sourceHashes']=={str(p):sha(SOURCE/p) for p in sorted(paths)}, 'Source changed during evaluation'
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,separators=(',',':'))+'\n')
print('W255_SOURCE_COMPLETE',sum(len(g['clips']) for g in result['groups']),flush=True)
