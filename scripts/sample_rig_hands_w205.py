"""Run in Blender: append source rigs into owned audit scene, sample FK matrices.
Never edits/saves SSD sources or the user's existing scene. Call sample(start,end).
"""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path('/Users/qf/IdeaProjects/DestinyGuardians')
SOURCE=Path('/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips')
OUT=ROOT/'art/weapons/w205/rigs'
SCENE='W205_SourceRig_Hands'
JOINTS={'leftElbow':'897A1504','leftWrist':'8C83CB67','rightElbow':'A3781DCD','rightWrist':'DE9D6BEA','utility':'80E9F09E'}
def sample(start,end):
 old=bpy.context.window.scene
 scene=bpy.data.scenes.get(SCENE) or bpy.data.scenes.new(SCENE)
 groups=sorted(p for p in SOURCE.iterdir() if (p/'blender/source.blend').exists())
 try:
  bpy.context.window.scene=scene
  for p in groups[start:end]:
   sm=json.loads((p/'source-map.json').read_text());bm=json.loads((p/'bone-map.json').read_text())
   root=next(b['name'] for b in bm if b.get('weaponBone') and b.get('weaponBoneIndex')==0)
   clips=sm['clips'];idle=next(c['tag'] for c in clips if c['names']==['idle'])
   ads=next((c['tag'] for c in clips if 'iron_sight_idle' in c['names']),None)
   reloads=[c['tag'] for c in clips if 'reload_full' in c['names']]
   tags=[idle]+([ads] if ads else [])+reloads
   with bpy.data.libraries.load(str(p/'blender/source.blend'),link=False) as (src,dst):
    dst.objects=src.objects
    dst.actions=[n for n in src.actions if any(t in n for t in tags)]
   rig=next(o for o in dst.objects if o.type=='ARMATURE');scene.collection.objects.link(rig);rig.name='W205_'+p.name
   names={**JOINTS,'weapon':root}
   actions={}
   for a in dst.actions:
    tag=next(t for t in tags if t in a.name)
    rig.animation_data_create();rig.animation_data.action=a
    if len(a.slots):rig.animation_data.action_slot=a.slots[0]
    astart,aend=map(float,a.frame_range);frames=[]
    for i in range(21 if tag in reloads else 1):
     t=i/20;f=astart+(aend-astart)*t;scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
     ev=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
     frames.append({'progress':t,'frame':f,'joints':{k:[list(row) for row in ev.pose.bones[n].matrix] for k,n in names.items() if n in ev.pose.bones}})
    actions[tag]={'action':a.name,'sourceNames':next(c['names'] for c in clips if c['tag']==tag),'start':astart,'end':aend,'frames':frames}
   out={'schemaVersion':1,'group':p.name,'space':'armature_object','matrixConvention':'row-major; column vectors','sourceBlend':str(p/'blender/source.blend'),'sourceBlendSha256':hashlib.sha256((p/'blender/source.blend').read_bytes()).hexdigest(),'sourceMapSha256':hashlib.sha256((p/'source-map.json').read_bytes()).hexdigest(),'boneMapSha256':hashlib.sha256((p/'bone-map.json').read_bytes()).hexdigest(),'weapons':[w['id'] for w in sm['weapons']],'fallback':sm['fallback'],'idle':idle,'ads':ads,'names':names,'actions':actions,'cameraExported':False}
   OUT.mkdir(parents=True,exist_ok=True);target=OUT/(p.name+'.json');target.write_text(json.dumps(out,separators=(',',':'))+'\n')
   print(json.dumps({'group':p.name,'actions':len(actions),'outputBytes':target.stat().st_size}))
 finally:bpy.context.window.scene=old
