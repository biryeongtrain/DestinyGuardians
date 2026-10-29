"""Headless Blender: evaluate original fire root, resample 61 poses; never save SSD sources."""
import bpy, json, csv, hashlib, math, sys
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',required=True,type=Path)
parser.add_argument('--source',type=Path,default=Path('/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return/clips'))
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
SOURCE=args.source.resolve()
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));import rig_arms_w205
routes,_=rig_arms_w205.load()
rows=list(csv.DictReader(open('/Volumes/qf-ssd/Destiny-Weapon-Fire-Check-2026-10-29/fire-clips.csv',encoding='utf-8-sig')))
C=Matrix(((0,-1,0),(0,0,1),(-1,0,0)))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
curves={};reports=[]
for group in dict.fromkeys(x['group'] for x in rows):
 folder=SOURCE/group;path=folder/'blender/source.blend';bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
 rig=max((o for o in bpy.data.objects if o.type=='ARMATURE'),key=lambda o:len(o.pose.bones))
 bone=next(x['name'] for x in json.loads((folder/'bone-map.json').read_text()) if x.get('weaponBone') and x.get('weaponBoneIndex')==0)
 clips={};report=dict(group=group,sourceBlend=str(path),sha256=sha(path),rig=rig.name,bones=len(rig.pose.bones),rootBone=bone,actions=[])
 for row in [x for x in rows if x['group']==group]:
  tag=row['tag'];matches=[a for a in bpy.data.actions if tag in a.name];assert len(matches)==1,(group,tag,[a.name for a in matches]);action=matches[0]
  rig.animation_data_create();rig.animation_data.action=action
  if len(action.slots):rig.animation_data.action_slot=action.slots[0]
  lo,hi=map(float,action.frame_range);duration=(hi-lo)/scene.render.fps
  assert abs(duration-float(row['duration']))<1e-5,(group,tag,duration,row['duration'])
  matrices=[]
  for i in range(61):
   f=lo+(hi-lo)*i/60;scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update()
   m=rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones[bone].matrix.copy();matrices.append(m)
  # Clips can start already kicked (notably HC ADS); their recovered endpoint is the reference.
  end=matrices[-1];r0=end.to_quaternion().to_matrix();samples=[];previous=Quaternion()
  for i,m in enumerate(matrices):
   weight=min(1,(duration*i/60)/(1/30));weight=weight*weight*(3-2*weight)
   shift=C@(m.translation-end.translation);rotation=(C@m.to_quaternion().to_matrix()@r0.transposed()@C.transposed()).to_quaternion().normalized()
   rotation=Quaternion().slerp(rotation,weight);shift*=weight
   if rotation.dot(previous)<0:rotation.negate()
   previous=rotation.copy()
   samples.append(dict(translation=[round(x,8) for x in shift],rotation=[round(rotation.x,8),round(rotation.y,8),round(rotation.z,8),round(rotation.w,8)]))
  samples[0]=dict(translation=[0.,0.,0.],rotation=[0.,0.,0.,1.]);samples[-1]=dict(translation=[0.,0.,0.],rotation=[0.,0.,0.,1.])
  clips[tag]=dict(duration=round(duration,8),samples=samples)
  report['actions'].append(dict(tag=tag,names=row['names'].split(';'),action=action.name,start=lo,end=hi,duration=duration,samples=61,maxTranslation=max(Vector(s['translation']).length for s in samples),maxDegrees=max(math.degrees(2*math.acos(min(1,abs(s['rotation'][3])))) for s in samples),sourceRootMatrices=[[[round(v,8) for v in row] for row in m] for m in matrices]))
 curves[group]=clips;reports.append(report);print('W242_EXTRACT '+json.dumps(dict(group=group,clips=len(clips))),flush=True)
weapons={};selected=[]
for weapon,data in routes.items():
 group=data['group'];rs=[x for x in rows if x['group']==group]
 if not rs:continue
 hip=next(x for x in rs if 'fire_1' in x['names'].split(';'))
 ads=next(x for x in rs if 'iron_sight_fire' in x['names'].split(';'))
 weapons[weapon]=dict(group=group,hip=hip['tag'],ads=ads['tag'])
 selected.append(dict(weapon=weapon,group=group,hip=hip['tag'],ads=ads['tag'],selection='current audited arm rig; first primary hip/ADS action in supplied CSV'))
asset=dict(schemaVersion=1,samplesPerClip=61,sourceUnitToView=1.,weapons=weapons,groups=curves)
(OUT/'w242-fire-motion.json').write_text(json.dumps(asset,separators=(',',':'),allow_nan=False)+'\n')
(OUT/'source-review.json').write_text(json.dumps(dict(blender=bpy.app.version_string,space='evaluated armature object; source X-forward Z-up -> view -Z-forward Y-up',conversion=[list(row) for row in C],neutral='clip endpoint; first 1/30s smooth onset; 61 evaluated poses, interpolation at runtime',sourceUnitToView=1.,sourceCameraExported=False,groups=reports,selections=selected),separators=(',',':'),allow_nan=False)+'\n')
print('W242_DONE',len(weapons),len(curves),len(rows),flush=True)
