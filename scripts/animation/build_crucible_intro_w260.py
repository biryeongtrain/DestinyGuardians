#!/usr/bin/env python3
"""W260 Trials candidate intro: isolated Blender evaluation and Steve retarget.

Evaluate (never saves or writes source):
  Blender --background --factory-startup --disable-autoexec --python THIS --
    --evaluate --source-root HANDOFF --samples /private/tmp/.../evaluated-source.json
Convert with python3 -B THIS --root CHECKOUT --samples JSON --output-root OUTPUT.
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
TAGS = ('80B7BBC8','80B7BBCA','80B7BBCC','80B7BBD0','80B7BBD4','80B7BBDB')
SOURCE_GROUP = Path('animations/trials_scene_body_72')
PACK = 'src/main/resources/destiny/animation/crucible_intro_w260.animation.json'
TIMING = 'src/main/resources/destiny/animation/crucible_intro_w260.timing.json'
PROVENANCE = 'art/crucible/w260/intro-provenance.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def evaluate(args):
    import bpy
    source = args.source_root.resolve()
    output = args.samples.resolve()
    if output.is_relative_to(source): raise ValueError('SSD/source is read-only')
    if not bpy.app.background or bpy.context.preferences.filepaths.use_scripts_auto_execute:
        raise RuntimeError('Require headless Blender --factory-startup --disable-autoexec')
    paths = [Path('HANDOFF.md'), Path('AUDIO-CUES.json'), SOURCE_GROUP/'source.blend',
             SOURCE_GROUP/'clips.json', SOURCE_GROUP/'bone-map.json', SOURCE_GROUP/'inspection.json']
    hashes = {str(p):sha(source/p) for p in paths}
    bpy.ops.wm.open_mainfile(filepath=str(source/SOURCE_GROUP/'source.blend'), use_scripts=False)
    rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    assert len(rigs) == 1
    rig = rigs[0]
    assert len(rig.data.bones) == 72
    assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
    scene = bpy.context.scene
    assert scene.render.fps / scene.render.fps_base == 30
    group = {'source':str(SOURCE_GROUP/'source.blend'),'sha256':hashes[str(SOURCE_GROUP/'source.blend')],
        'matrixWorld':[list(r) for r in rig.matrix_world],'scale':list(rig.scale),
        'rotation':list(rig.rotation_euler),'sceneFps':30,
        'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,
                  'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]}
                 for b in rig.data.bones], 'clips':[]}
    rig.animation_data_create()
    for track in rig.animation_data.nla_tracks: track.mute = True
    for tag in TAGS:
        actions = [a for a in bpy.data.actions if tag in a.name]
        assert len(actions) == 1, (tag, [a.name for a in actions])
        action = actions[0]
        rig.animation_data.action = action
        slots = [s for s in action.slots if s.target_id_type == 'OBJECT']
        assert len(slots) <= 1, ('Ambiguous action slot', action.name)
        if slots: rig.animation_data.action_slot = slots[0]
        first,last = map(float, action.frame_range)
        assert [first,last] == [1.,446.], (tag,first,last)
        frames=[]
        for frame in range(1,447):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            ev = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
            joints = {b.name:[list(r) for r in b.matrix] for b in ev.pose.bones}
            assert all(math.isfinite(v) for m in joints.values() for row in m for v in row)
            frames.append({'frame':frame,'joints':joints})
        group['clips'].append({'tag':tag,'action':action.name,'slot':slots[0].identifier if slots else None,
            'firstFrame':first,'lastFrame':last,'fps':30,'durationSeconds':(last-first)/30,
            'actualFrameRange':[first,last],'frames':frames})
        print('EVALUATED',tag,len(frames),'frames x',len(rig.data.bones),'bones',flush=True)
    assert hashes == {str(p):sha(source/p) for p in paths}, 'Source drift during evaluation'
    result={'schemaVersion':1,'sourceRoot':str(source),'sourceHashes':hashes,
        'blenderVersion':bpy.app.version_string,'sampleSpace':'armature_object',
        'autoexecDisabled':True,'sampleCountPerClip':446,'groups':[group]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
    print('W260_SOURCE_COMPLETE', output, flush=True)


# Retarget math adapted from W259; evaluation and root translation are W260-specific.
def xyz(m):return [m[i][3] for i in range(3)]

def convert(v):return h19.vector(C,v)

def local(pose,name,desired):
 actual=h19.fk(model,pose)[name]
 now=h15.rot(h19.add(GROUPS[name].get('rotation',[0]*3),pose[name]))
 parent=h15.mm(w197.rotation(actual),h19.inverse_rotation(now))
 pose[name]=h19.sub(h19.euler(h15.mm(h19.inverse_rotation(parent),desired)),GROUPS[name].get('rotation',[0]*3))

def pose(g,frame,normals):
 # Move evaluated pelvis orientation to the common parent of hip AND thighs.
 # Descendant desired world rotations remain source-derived, preventing double spin.
 p=h15.zero();m=frame['joints'];points={n:xyz(v) for n,v in m.items()};bones={b['name']:b for b in g['bones']}
 local(p,'player_root',h15.mm(C,h15.mm(w197.rotation(m['C7C0BA6E']),h15.mm(h19.inverse_rotation(w197.rotation(bones['C7C0BA6E']['matrix'])),h19.inverse_rotation(C)))))
 for target,source in [('phip_hip','C7C0BA6E'),('pw_waist','A252A6A2'),('pc_chest','A352A6A2'),('h_ph_head','7E92D640')]:
  desired=h15.mm(C,h15.mm(w197.rotation(m[source]),h15.mm(h19.inverse_rotation(w197.rotation(bones[source]['matrix'])),h19.inverse_rotation(C))))
  local(p,target,desired)
 for upper,lower,chain in [('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]:
  down=h19.unit(h19.sub(points[chain[1]],points[chain[0]]))
  lower_dir=h19.unit(h19.sub(points[chain[2]],points[chain[1]]))
  bend=math.degrees(math.acos(max(-1,min(1,h19.dot(down,lower_dir)))))
  x=normals[chain[0]];y=h19.mul(down,-1);z=h19.cross(x,y)
  frame=[[x[i],y[i],z[i],0] for i in range(3)]+[[0,0,0,1]]
  # Flip anatomical X and Z together: negative-X knee bend, sole faces forward.
  frame=h15.mm(frame,h15.rot([0,180,0]))
  local(p,upper,h15.mm(C,frame));p[lower]=[-bend,0,0]
 for side,upper,fore,item,chain in [('left','pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67']),('right','pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA'])]:
  shoulder=h19.point(h19.fk(model,p)[upper],[0,0,0]);a=h19.norm(h19.sub(GROUPS[fore]['origin'],GROUPS[upper]['origin']));b=h19.norm(h19.sub(GROUPS[item]['origin'],GROUPS[fore]['origin']))
  u=convert(h19.unit(h19.sub(points[chain[1]],points[chain[0]])));v=convert(h19.unit(h19.sub(points[chain[2]],points[chain[1]])))
  delta=h19.add(h19.mul(u,a),h19.mul(v,b));distance=h19.norm(delta)
  if distance>10.9:delta=h19.mul(delta,10.9/distance)
  # At a straight source elbow u is parallel to delta, so raw-u bias has no
  # defined side. The transported source bend plane remains well-defined.
  bias=convert(h19.cross(h19.unit(h19.sub(points[chain[1]],points[chain[0]])),normals[chain[0]]))
  h19.solve_arm(model,p,side,h19.add(shoulder,delta),bias)
 return p

def unwrap(frames):
 previous=None
 for _,p in frames:
  if previous:
   for n in p:
    x,y,z=p[n]
    candidates=[[v+360*round((old-v)/360) for v,old in zip(family,previous[n])] for family in ([x,y,z],[x+180,180-y,z+180])]
    p[n]=min(candidates,key=lambda q:sum((a-b)**2 for a,b in zip(q,previous[n])))
  else:
   # Choose an equivalent compact initial family before preserving accumulated turns.
   for n in p:
    x,y,z=p[n]
    families=[[((v+180)%360)-180 for v in family] for family in ([x,y,z],[x+180,180-y,z+180])]
    p[n]=min(families,key=lambda q:sum(v*v for v in q))
  previous=p

def source_rotation(g, frame, bone):
 rest = next(b['matrix'] for b in g['bones'] if b['name'] == bone)
 return h15.mm(C, h15.mm(w197.rotation(frame['joints'][bone]),
     h15.mm(h19.inverse_rotation(w197.rotation(rest)), h19.inverse_rotation(C))))

def angle_error(a, b):
 delta = h15.mm(h19.inverse_rotation(a), b)
 return math.degrees(math.acos(max(-1, min(1, (sum(delta[i][i] for i in range(3)) - 1) / 2))))

def stable_normals(c, chain):
 # A collinear joint has no geometric bend plane. Fill only those samples
 # from bracketing source planes transported in the upper bone's own frame.
 # This retains the evaluated source twist during fully extended intervals.
 rotations=[]; directions=[]; normals=[]; repaired=[]
 for f in c['frames']:
  a,b,d=[xyz(f['joints'][n]) for n in chain]
  u=h19.unit(h19.sub(b,a));v=h19.unit(h19.sub(d,b))
  cross=h19.cross(u,v)
  rotations.append(w197.rotation(f['joints'][chain[0]]));directions.append(u)
  normals.append(h19.unit(cross) if h19.norm(cross)>1e-4 else None)
 valid=[i for i,n in enumerate(normals) if n is not None]
 assert valid, ('Entire source chain is collinear',c['tag'],chain)
 for i,n in enumerate(normals):
  if n is not None:continue
  before=max((j for j in valid if j<i),default=valid[0])
  after=min((j for j in valid if j>i),default=valid[-1])
  a=h19.vector(h19.inverse_rotation(rotations[before]),normals[before])
  b=h19.vector(h19.inverse_rotation(rotations[after]),normals[after])
  alpha=0 if before==after else (i-before)/(after-before)
  dot=max(-1,min(1,h19.dot(a,b)))
  if dot>.9995:
   mixed=h19.unit(h19.add(h19.mul(a,1-alpha),h19.mul(b,alpha)))
  else:
   angle=math.acos(dot)
   tangent=h19.sub(b,h19.mul(a,dot))
   if h19.norm(tangent)<1e-8:
    axis=min(([1,0,0],[0,1,0],[0,0,1]),key=lambda v:abs(h19.dot(v,a)))
    tangent=h19.cross(a,axis)
   tangent=h19.unit(tangent)
   mixed=h19.add(h19.mul(a,math.cos(angle*alpha)),h19.mul(tangent,math.sin(angle*alpha)))
  world=h19.vector(rotations[i],mixed)
  normals[i]=h19.unit(h19.sub(world,h19.mul(directions[i],h19.dot(world,directions[i]))))
  repaired.append({'sampleIndex':i,'sourceFrame':c['frames'][i]['frame'],
      'bracketingSampleIndices':[before,after]})
 return normals,repaired


def convert_assets(args):
    global h15,h19,w197,C,model,GROUPS
    root=args.root.resolve()
    output=(args.output_root or root).resolve()
    data=json.loads(args.samples.read_text())
    source=Path(data['sourceRoot']).resolve()
    if output.is_relative_to(source): raise ValueError('Source tree is read-only')
    sys.path.insert(0,str(root/'scripts'))
    import build_hunter_animation_h15 as h15
    import build_hunter_animation_h19 as h19
    import build_hunter_source_w197 as w197
    C=w197.C
    model_path=root/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'
    model=json.loads(model_path.read_text())
    GROUPS={g['name']:g for g in model['groups']}
    assert data['autoexecDisabled'] and data['sampleSpace']=='armature_object'
    assert len(data['groups'])==1
    g=data['groups'][0]
    assert len(g['bones'])==72 and [c['tag'] for c in g['clips']]==list(TAGS)
    assert data['sourceHashes']=={p:sha(source/p) for p in data['sourceHashes']}, 'Source drift'
    reference=root/'art/weapons/w197/hunter-source-motion.json'
    old=json.loads(reference.read_text())['bones']
    bones={b['name']:b for b in g['bones']}
    assert old.keys()==bones.keys()
    rest_difference=max(abs(old[n]['restMatrix'][i][j]-bones[n]['matrix'][i][j])
        for n in bones for i in range(4) for j in range(4))
    assert rest_difference<1e-5, ('Source rig differs',rest_difference)
    # Existing armature basis, explicit proportional distance conversion. This is
    # a retarget decision, NOT a claim that the outer FBX .01 wrapper is game units.
    source_height=bones['C7C0BA6E']['head'][2]
    target_height=GROUPS['phip_hip']['origin'][1]
    units=target_height/source_height
    clips=[]; summaries=[]
    for c in g['clips']:
        assert len(c['frames'])==446 and c['actualFrameRange']==[1.,446.]
        normals={}; repairs={}
        for chain in [['9F0FD28C','8BD44A3F','B9B9E05D'],['695DAF09','35B14D1B','0F8B505D'],
                      ['D1232BA2','897A1504','8C83CB67'],['17025F50','A3781DCD','DE9D6BEA']]:
            normals[chain[0]],repairs[chain[0]]=stable_normals(c,chain)
        frames=[(round((f['frame']-1)/30,9),pose(g,f,{n:vs[i] for n,vs in normals.items()}))
                for i,f in enumerate(c['frames'])]
        unwrap(frames)
        name='h15_intro_'+c['tag'].lower()
        clip=h15.clip(model,name,frames,root_positions={},linear_root=True)
        clip['length']=445/30
        clip['snapping']=30
        # Preserve all 446 source anchors, including pre-entry off-stage travel.
        # Land the last pose on the target floor once; do NOT floor-fit every frame
        # (which erases the source's vertical motion and landing interval).
        end_pose=frames[-1][1]
        end_hip=xyz(h19.fk(model,end_pose)['phip_hip'])
        end_hip[1]+=h15.floor_y(model,end_pose)
        end_source=xyz(c['frames'][-1]['joints']['C7C0BA6E'])
        positions=[]
        for (_,p),f in zip(frames,c['frames']):
            delta=h19.mul(convert(h19.sub(xyz(f['joints']['C7C0BA6E']),end_source)),units)
            desired=h19.add(end_hip,delta)
            positions.append(h19.sub(desired,xyz(h19.fk(model,p)['phip_hip'])))
        max_step=0
        for animator in clip['animators'].values():
            previous=None; position_index=0
            for k in animator['keyframes']:
                k['interpolation']='linear'
                if k['channel']=='position':
                    k['data_points']=[dict(zip('xyz',positions[position_index]))]
                    position_index+=1
                else:
                    values=[k['data_points'][0][a] for a in 'xyz']
                    if previous is not None:max_step=max(max_step,max(abs(a-b) for a,b in zip(values,previous)))
                    previous=values
                k['data_points'][0]={a:round(float(v),7) for a,v in k['data_points'][0].items()}
                if abs(k['time']-445/30)<1e-8:k['time']=445/30
        # Cheap generation invariants only; runtime/targeted testing is master-owned.
        assert all(math.isfinite(v) for a in clip['animators'].values()
            for k in a['keyframes'] for v in k['data_points'][0].values())
        floor_clearance=[pos[1]-h15.floor_y(model,p) for (_,p),pos in zip(frames,positions)]
        summary={'name':name,'sourceTag':c['tag'],'action':c['action'], 'sourceFrameRange':[1,446],
            'sourceFrameCount':446,'sourceFps':30,'durationSeconds':445/30,
            'sourceSampleCountSeconds':446/30,'roundedClipTicks':297,'entryTicks':1,
            'sourceTranslationUnitsToModelUnits':units,
            'sourcePelvisRange':[[min(xyz(f['joints']['C7C0BA6E'])[i] for f in c['frames']),
                                  max(xyz(f['joints']['C7C0BA6E'])[i] for f in c['frames'])] for i in range(3)],
            'targetRootPositionRange':[[min(p[i] for p in positions),max(p[i] for p in positions)] for i in range(3)],
            'targetLowestSkinRange':[min(floor_clearance),max(floor_clearance)],
            'maxAdjacentEulerStepDegrees':max_step,
            'collinearSourceJointRepairs':{n:r for n,r in repairs.items() if r}}
        clips.append(clip); summaries.append(summary)
        print('RETARGET',name,'446 poses',round(clip['length'],9),'seconds',
              'maxEulerStep',round(max_step,4),flush=True)
    cues=json.loads((source/'AUDIO-CUES.json').read_text())
    helpers=['scripts/build_hunter_animation_h15.py','scripts/build_hunter_animation_h19.py',
        'scripts/build_hunter_source_w197.py','scripts/animation/build_hunter_dodge_w259.py',
        'scripts/animation/sample_class_ability_w255.py']
    manifest={'schemaVersion':1,'classification':'Trials scene candidate; not a complete original general 6v6 intro',
        'sourceRoot':str(source),'sourceHashes':data['sourceHashes'],
        'generatorHashes':{'scripts/animation/build_crucible_intro_w260.py':sha(Path(__file__)),
            **{p:sha(root/p) for p in helpers}},
        'evaluation':{'blenderVersion':data['blenderVersion'],'autoexecDisabled':True,
            'sourceBlendOpenedDirectly':True,'sampleSpace':'armature_object',
            'sourceHashBeforeAfterEqual':True,'samplesSha256':sha(args.samples),
            'bones':72,'clips':6,'samplesPerClip':446,'savedSourceBlend':False},
        'target':{'rig':str(model_path.relative_to(root)),'rigSha256':sha(model_path),
            'basis':C,'maxRestMatrixDifference':rest_difference,
            'sourceRigReference':str(reference.relative_to(root)),'sourceRigReferenceSha256':sha(reference),
            'axes':'source +X forward +Y left +Z up => target +X right +Y up -Z forward; outer FBX wrapper excluded',
            'rotation':'W259 source/rest torso and pelvis; geometric thigh/knee; elbow IK to Steve segment lengths; transported collinear bend planes; equivalent Euler-family unwrap',
            'translation':'full evaluated pelvis trajectory, proportional to target/source bind pelvis height, anchored to final target hip and final-pose floor. Early underground/off-stage samples are preserved, not clamped or claimed to be recovered actor placement.',
            'skin':'existing PlayerAnimations profile skin; rigid Steve segments, not 72-bone skinned mesh',
            'targetAnimatedBones':len(h15.BONES),
            'samplePolicy':'all446 source anchors at30Hz; SourceAnimationGrid compiles linear keys to40Hz; server owns20TPS playback. No speed compression.'},
        'clips':summaries,
        'authored':{'actorPlacements':True,'cameraShots':True,'representativeSelection':True,
            'clipToPlayerSlotMapping':True,'introMapLeadTicks':100,
            'sourceCameraOrActorPlacementRecovered':False},
        'runtime':{'clipPrefix':'h15_intro_','registrationOwner':'master HunterModelAssets',
            'participantLimit':None,'representativeActorsPerTeam':3,
            'mapLeadTicks':100,'bodyDurationSeconds':445/30,'bodyTicksIncludingEntry':298,
            'minimumTotalTicks':398,'recommendedPhaseTicks':400,
            'gameModeMutation':False,'inventoryMutation':False,
            'actorPositionPolicy':'intro exposes actorPlacements; Runtime applies them before opening cameras and owns position/gamemode restoration on leave/cancel/phase exit. Intro never changes player position or inventory.',
            'cameraIntegration':'Runtime-owned camera adapter; CameraViews filtering must route BetterModel packets and restore view; do not set real spectator gamemode'},
        'audio':{'packedFiles':[], 'selected':None,
            'javelin4Candidates':[c for c in cues if c['sound']=='80D52B6B'],
            'trialsFxCandidates':[c for c in cues if c['sound'] in ['80A60679','80A6067D','80A6067B']],
            'selection':'Javelin-4 event80D52B6B has C1/C2/C3 stereo alternatives. Audition and choose one; original branch/random/loop graph unresolved. Local duration2 is not a trim instruction.',
            'fxPolicy':'5channel Trials stems require channel-layout verified downmix; frame0 belongs to auxiliary event clips; 72bone clip/actor mapping unconfirmed. Excluded from pack.',
            'excluded':'enter_pose names have no confirmed PvP link; do not pack all65 files'},
        'limitations':['Trials/general6v6 linkage unconfirmed','source actor placement/camera/FOV/cuts unresolved',
            '4bone and2bone auxiliary clips excluded; roles unconfirmed',
            'source pre-entry travel may start underground or far off-stage; camera staging needs native review',
            'target rigid skin cannot reproduce fingers, cloth, original armor, particles or original weapon binding'],
        'verification':{'generation':'finite matrices and numeric keys; exact six actions x446 frames; source hashes unchanged; known72bone bind verified',
            'targetedTests':'see worker return targeted-checks.json; this generation record does not certify runtime tests','compile':'master integration','nativeVision':'not run; master only',
            'audioListening':'not performed; candidates only'}}
    timing={'schemaVersion':1,'mapLeadTicks':100,'clips':[{'name':s['name'],
        'durationSeconds':s['durationSeconds'],'entryTicks':1} for s in summaries]}
    for rel,obj in [(PACK,{'animations':clips}),(TIMING,timing),(PROVENANCE,manifest)]:
        raw=(json.dumps(obj,indent=2 if rel==PROVENANCE else None,
            separators=None if rel==PROVENANCE else (',',':'),allow_nan=False)+'\n').encode()
        path=output/rel
        if args.verify:
            assert path.read_bytes()==raw, ('Reproduction differs',path)
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print('W260_RETARGET_COMPLETE',output,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluate',action='store_true')
    parser.add_argument('--source-root',type=Path)
    parser.add_argument('--samples',type=Path,required=True)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output-root',type=Path)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    if args.evaluate:
        if args.source_root is None: parser.error('--source-root required with --evaluate')
        evaluate(args)
    else: convert_assets(args)

if __name__ == '__main__': main()
