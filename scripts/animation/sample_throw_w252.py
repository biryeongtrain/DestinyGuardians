import bpy,json,hashlib
from pathlib import Path
# Headless invocation preserves the user's Blender scene. SSD is read only.
src=Path('/Volumes/qf-ssd/Destiny-Light-Abilities-2026-10-28/animations/shared_grenade_throw/source.blend')
bpy.ops.wm.open_mainfile(filepath=str(src))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
actions=[a for a in bpy.data.actions if '80A8A67C' in a.name or '80A8A663' in a.name or '80A8A847' in a.name]
bones=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local)} for b in rig.data.bones]
out={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'bones':bones,'matrixWorld':[list(r) for r in rig.matrix_world],'clips':[]}
for a in actions:
 rig.animation_data_create();rig.animation_data.action=a
 if len(a.slots):rig.animation_data.action_slot=a.slots[0]
 frames=[]
 for i in range(61):
  f=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*i/60
  bpy.context.scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
  ev=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
  frames.append({'progress':i/60,'frame':f,'joints':{b.name:[list(r) for r in b.matrix] for b in ev.pose.bones}})
 out['clips'].append({'action':a.name,'frames':frames})
Path('/private/tmp/destiny-w252/throw-evaluated.json').write_text(json.dumps(out,separators=(',',':')))
print('W252_EVALUATED',len(actions),len(bones),rig.scale[:],rig.rotation_euler[:])
