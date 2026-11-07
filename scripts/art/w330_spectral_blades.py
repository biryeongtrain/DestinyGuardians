#!/usr/bin/env python3
"""W330 read-only Blender evaluation and isolated Spectral clip output. Never writes shared runtime assets."""
import hashlib
import json
import math
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'art/animation/w330/spectral_blades'
SOURCE = Path('/Users/qf/Downloads/Destiny-Light-Abilities-2026-10-28/Destiny-Light-Abilities-2026-10-28/animations/hunter_spectral_blades')
MAIN = Path('/Users/qf/IdeaProjects/DestinyGuardians')
CLIPS = {'start':'80A8AAC4', 'start_air':'80A8AAD0', 'attack':'80A8AAC8',
    'attack2':'80A8AAC7', 'attack3':'80A8AAC5', 'attack_air':'80A8AAF8',
    'attack3_air':'80A8AAE5', 'heavy':'80A8B4F5', 'heavy_air':'80A8B55A'}
TAGS = list(CLIPS.values())
sys.dont_write_bytecode = True
sys.path.insert(0, str(MAIN/'scripts'))
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_source_w197 as w197
C = w197.C


def local(model, p, name, desired):
    groups = {g['name']:g for g in model['groups']}
    actual = h19.fk(model,p)[name]
    now = h15.rot(h19.add(groups[name].get('rotation',[0,0,0]),p[name]))
    parent = h15.mm(w197.rotation(actual),h19.inverse_rotation(now))
    p[name] = h19.sub(h19.euler(h15.mm(h19.inverse_rotation(parent),desired)),groups[name].get('rotation',[0,0,0]))


def pose(model, matrices, rest):
    p = h15.zero()
    points = {n:[m[i][3]for i in range(3)]for n,m in matrices.items()}
    bind = h19.fk(model,p)
    groups = {g['name']:g for g in model['groups']}
    def orientation(source,target):
        delta = h15.mm(C,h15.mm(w197.rotation(matrices[source]),h15.mm(h19.inverse_rotation(w197.rotation(rest[source])),h19.inverse_rotation(C))))
        return h15.mm(delta,w197.rotation(bind[target]))
    for target,source in [('phip_hip','C7C0BA6E'),('pw_waist','A252A6A2'),('pc_chest','A352A6A2'),('h_ph_head','7E92D640')]:
        local(model,p,target,orientation(source,target))
    for upper,lower,chain in [('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]:
        frame,bend = w197.leg_frame(points,chain)
        local(model,p,upper,h15.mm(C,h15.mm(frame,h15.rot([0,180,0]))))
        p[lower]=[-bend,0,0]
    for side,upper,fore,item,chain in [('left','pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67']),('right','pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA'])]:
        shoulder=h19.point(h19.fk(model,p)[upper],[0,0,0])
        a=h19.norm(h19.sub(groups[fore]['origin'],groups[upper]['origin']))
        b=h19.norm(h19.sub(groups[item]['origin'],groups[fore]['origin']))
        u=h19.vector(C,h19.unit(h19.sub(points[chain[1]],points[chain[0]])))
        v=h19.vector(C,h19.unit(h19.sub(points[chain[2]],points[chain[1]])))
        delta=h19.add(h19.mul(u,a),h19.mul(v,b))
        if h19.norm(delta)>10.9: delta=h19.mul(h19.unit(delta),10.9)
        h19.solve_arm(model,p,side,h19.add(shoulder,delta),u)
        # Preserve source wrist orientation independently from the shorter Steve
        # arm IK. Equipment remains attached to each existing item pivot.
        local(model,p,item,orientation(chain[2],item))
    return p


def continuous(p,previous):
    for name,angles in p.items():
        if previous is None: continue
        x,y,z=angles
        candidates=[]
        for representation in ([x,y,z],[x+180,180-y,z+180]):
            candidates.append([v+360*round((old-v)/360)for v,old in zip(representation,previous[name])])
        p[name]=min(candidates,key=lambda a:sum((v-old)**2 for v,old in zip(a,previous[name])))
    return p


def review(model, samples):
    # Deliberately simple orthographic diagrams from directly evaluated poses;
    # not a native-client or final weapon-grip acceptance image.
    rows=[]
    chains=[['C7C0BA6E','A252A6A2','A352A6A2','7E92D640'],['A352A6A2','D1232BA2','897A1504','8C83CB67','C3BCA7CA'],['A352A6A2','17025F50','A3781DCD','DE9D6BEA','19AB4BEF'],['C7C0BA6E','695DAF09','35B14D1B','0F8B505D'],['C7C0BA6E','9F0FD28C','8BD44A3F','B9B9E05D']]
    targetchains=[['phip_hip','pw_waist','pc_chest','h_ph_head'],['pc_chest','pla_left_arm','plfa_left_forearm','pli_left_item'],['pc_chest','pra_right_arm','prfa_right_forearm','pri_right_item'],['phip_hip','pll_left_leg','plfl_left_foreleg'],['phip_hip','prl_right_leg','prfl_right_foreleg']]
    colors=['#eeeeee','#e5bb45','#65b8f0','#e5bb45','#65b8f0']
    for row,(phase,tag)in enumerate(CLIPS.items()):
        data=samples[tag]; length=data['length']
        y0=70+row*245
        rows.append(f'<text x="10" y="{y0}" fill="white" font-size="17">{phase} | {tag} | {length:.4f}s | source cyan/gold/white, target purple</text>')
        for col,fraction in enumerate([0,.2,.4,.65,1]):
            frame=min(data['frames'],key=lambda f:abs(f['seconds']-length*fraction))
            matrices=frame['matrices']; p=frame['targetPose']; root=frame['rootY']
            fk=h19.fk(model,p,root)
            sourcepoints={n:h19.vector(C,[m[i][3]*14.5 for i in range(3)])for n,m in matrices.items()}
            targetpoints={n:h19.point(m,[0,0,0])for n,m in fk.items()}
            cx=130+col*470
            rows.append(f'<text x="{cx-75}" y="{y0+22}" fill="#aaaaaa" font-size="14">{frame["seconds"]:.3f}s</text>')
            for view in range(2):
                def project(pt,offset):
                    horizontal=pt[0] if view==0 else -pt[2]
                    return (cx+offset+horizontal*4.7,y0+190-pt[1]*4.7)
                for chain,color in zip(chains,colors):
                    coords=' '.join(f'{x:.2f},{y:.2f}'for x,y in [project(sourcepoints[n],view*205-65)for n in chain])
                    rows.append(f'<polyline points="{coords}" stroke="{color}" stroke-width="3" fill="none"/>')
                for chain in targetchains:
                    coords=' '.join(f'{x:.2f},{y:.2f}'for x,y in [project(targetpoints[n],view*205+15)for n in chain])
                    rows.append(f'<polyline points="{coords}" stroke="#e0a4f0" stroke-width="3" fill="none"/>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="2300" viewBox="0 0 2400 2300"><rect width="2400" height="2300" fill="#17191e"/><text x="10" y="27" fill="white" font-size="20">W330 DIRECT BLEND EVALUATION / FRONT + SIDE / static retarget review, native acceptance pending</text>'+''.join(rows)+'</svg>'
    (OUT/'source-target-review.svg').write_text(svg)


def export(model, samples, inventory):
    output=[]; report=[]
    namespace=uuid.UUID('7c2ed6cb-a2d1-4bb7-a75f-7b1f4aa008d3')
    uid=lambda text:str(uuid.uuid5(namespace,text))
    groups={g['name']:g for g in model['groups']}
    for phase,tag in CLIPS.items():
        data=samples[tag]; length=data['length']; name='w230_hunter_spectral_blades_'+phase
        # Earliest large hand sweep peak is a visual timing candidate, not an
        # original decoded damage marker. Keep that distinction in runtime data.
        speeds=[]
        for a,b in zip(data['frames'],data['frames'][1:]):
            if b['seconds']>length*.72: break
            speed=max(h19.norm(h19.sub([b['matrices'][w][i][3]for i in range(3)],[a['matrices'][w][i][3]for i in range(3)]))/(b['seconds']-a['seconds'])for w in ['8C83CB67','DE9D6BEA'])
            speeds.append((speed,b['seconds']))
        peak=max(speeds)[0]
        contact=next(t for speed,t in speeds if speed>=peak*.9)
        clip={'uuid':uid(name),'name':name,'loop':'once','override':False,'length':length,'snapping':40,'destiny_quaternion_sampling':True,'destiny_contact_seconds':contact,'destiny_recovery_seconds':length,'destiny_entry_blend_ticks':1,'destiny_exit_blend_ticks':2,'destiny_contact_provisional':True,'animators':{}}
        maxstep=0; previousquat={}
        for bone in h15.BONES:
            keys=[]
            for f in data['frames']:
                t=f['seconds']; angles=f['targetPose'][bone]
                q=w197.quat(h15.rot(angles)) # w,x,y,z
                if bone in previousquat:
                    dot=sum(x*y for x,y in zip(q,previousquat[bone]))
                    if dot<0:q=[-v for v in q];dot=-dot
                    maxstep=max(maxstep,math.degrees(2*math.acos(min(1,dot))))
                previousquat[bone]=q
                key={'uuid':uid(f'{name}/{bone}/{t}/r'),'channel':'rotation','time':t,'interpolation':'linear','data_points':[dict(zip(['x','y','z'],angles))],'destiny_quaternion':[q[1],q[2],q[3],q[0]]}
                keys.append(key)
                if bone=='player_root':keys.append({'uuid':uid(f'{name}/{bone}/{t}/p'),'channel':'position','time':t,'interpolation':'linear','data_points':[{'x':0,'y':f['rootY'],'z':0}]})
                if bone in ['pri_right_item','pli_left_item']:keys.append({'uuid':uid(f'{name}/{bone}/{t}/s'),'channel':'scale','time':t,'interpolation':'linear','data_points':[{'x':1,'y':1,'z':1}]})
            clip['animators'][groups[bone]['uuid']]={'name':bone,'type':'bone','rotation_global':False,'quaternion_interpolation':True,'keyframes':keys}
        output.append(clip)
        report.append({'phase':phase,'clip':name,'tag':tag,'action':data['action'],'lengthSeconds':length,'sourceFrameRange':data['sourceFrameRange'],'sampleCount':len(data['frames']),'contactSeconds':contact,'contactSourceFrame':1+contact*30,'contactStatus':'provisional visual first high wrist-speed sweep, NOT decoded hit marker','maxQuaternionStepDegrees':maxstep,'endPosePreserved':True})
    existing=json.loads((MAIN/'src/main/resources/destiny/animation/classes_w230.animation.json').read_text())
    existing_move=next(c for c in existing['animations']if c['name']=='w230_hunter_spectral_blades_move')
    moving_bones={'player_root','phip_hip','prl_right_leg','prfl_right_foreleg','pll_left_leg','plfl_left_foreleg','cape_cape'}
    for phase,cast in [('idle','start'),('air','start_air'),('move','start')]:
        guard=samples[CLIPS[cast]]['frames'][-1]
        name='w230_hunter_spectral_blades_'+phase
        clip={'uuid':uid(name),'name':name,'loop':'loop','override':False,'length':.8,'snapping':40,'destiny_quaternion_sampling':True,'animators':{}}
        for bone in h15.BONES:
            keys=[]
            source_animator=next(a for a in existing_move['animators'].values()if a['name']==bone)
            channels={'rotation':[k for k in source_animator['keyframes']if k['channel']=='rotation'],'position':[k for k in source_animator['keyframes']if k['channel']=='position']}
            def sample_existing(channel,t):
                ks=channels[channel]
                if not ks:return [0,0,0]
                a=max((k for k in ks if k['time']<=t),key=lambda k:k['time'],default=ks[0])
                b=min((k for k in ks if k['time']>=t),key=lambda k:k['time'],default=ks[-1])
                ratio=0 if a['time']==b['time']else(t-a['time'])/(b['time']-a['time'])
                return [float(a['data_points'][0][axis])*(1-ratio)+float(b['data_points'][0][axis])*ratio for axis in ['x','y','z']]
            previous_q=None
            for index in range(33):
                t=index/40
                angles=sample_existing('rotation',t)if phase=='move'and bone in moving_bones else guard['targetPose'][bone]
                q=w197.quat(h15.rot(angles))
                if previous_q is not None and sum(x*y for x,y in zip(q,previous_q))<0:q=[-v for v in q]
                previous_q=q
                keys.append({'uuid':uid(f'{name}/{bone}/{t}/r'),'channel':'rotation','time':t,'interpolation':'linear','data_points':[dict(zip(['x','y','z'],angles))],'destiny_quaternion':[q[1],q[2],q[3],q[0]]})
                if bone=='player_root':
                    xyz=sample_existing('position',t)if phase=='move'else[0,guard['rootY'],0]
                    keys.append({'uuid':uid(f'{name}/{bone}/{t}/p'),'channel':'position','time':t,'interpolation':'linear','data_points':[dict(zip(['x','y','z'],xyz))]})
                if bone in ['pri_right_item','pli_left_item']:keys.append({'uuid':uid(f'{name}/{bone}/{t}/s'),'channel':'scale','time':t,'interpolation':'linear','data_points':[{'x':1,'y':1,'z':1}]})
            clip['animators'][groups[bone]['uuid']]={'name':bone,'type':'bone','rotation_global':False,'quaternion_interpolation':True,'keyframes':keys}
        output.append(clip)
        report.append({'phase':phase,'clip':name,'lengthSeconds':.8,'sourceGuardTag':CLIPS[cast],'sourceGuardFrame':samples[CLIPS[cast]]['sourceFrameRange'][1],'policy':'source final guard hold; mixed existing authored lower-body locomotion for move'if phase=='move'else'source final guard hold; no invented breathing animation'})
    (OUT/'spectral_blades_w330.animation.json').write_text(json.dumps({'schema_version':1,'animations':output},separators=(',',':'))+'\n')
    manifest={'source':'user-supplied Destiny-Light-Abilities-2026-10-28','sourceDirectory':str(SOURCE),'sourceBlendSha256':inventory['sourceSha256'],'blenderVersion':inventory['blenderVersion'],'sourceReadOnly':True,'targetRig':str(MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'),'targetRigSha256':sha(MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'),'coordinateBasis':'source +X forward,+Y left,+Z up -> target +X right,+Y up,-Z forward; exclude FBX outer 0.01 transform','rotationConvention':'Blockbench Rz*Ry*Rx; quaternions x,y,z,w; hemisphere continuous','sampling':'direct fractional-frame Blender evaluation at 40 Hz and exact final timestamp; original 30 fps action duration; no source speed compression; no neutral endpoint blend','sourceQuaternionHemisphereCheck':{tag:data['equivalentQuaternionHemisphereCorrections']for tag,data in samples.items()},'retarget':'unchanged segmented player rig; torso/head rest-relative rotation; anatomical legs; reach-limited two-link arm IK; each source wrist rest-relative rotation drives its own existing item pivot; no shared rig/geometry changes','rootMotion':'horizontal source locomotion omitted (runtime owns entity movement); ground skin floor support plus source ankle lift; air pelvis displacement relative source bind, bounded to +/-8 model units','nativeAcceptance':'parent first Vision baseline reviewed; replacement still awaits parent second Vision; static diagrams cannot certify native knife grip/contact','clips':report,'sourceFiles':[{'name':p.name,'sha256':sha(p)}for p in [SOURCE/'source.blend',SOURCE/'clips.json',SOURCE/'CLIPS.md']]}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    review(model,samples)
    print(json.dumps(report,indent=2),flush=True)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect():
    import bpy
    OUT.mkdir(parents=True, exist_ok=True)
    armature = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    armature.animation_data_create()
    for track in armature.animation_data.nla_tracks: track.mute = True
    inventory = {'sourceBlend': str(SOURCE / 'source.blend'), 'sourceSha256': sha(SOURCE / 'source.blend'),
        'blenderVersion': bpy.app.version_string, 'objects': [{'name':o.name, 'type':o.type} for o in bpy.data.objects],
        'armature':armature.name, 'matrixWorld':[list(v)for v in armature.matrix_world],
        'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'restMatrix':[list(v)for v in b.matrix_local]}for b in armature.data.bones],
        'actions':[]}
    for action in bpy.data.actions:
        inventory['actions'].append({'name':action.name,'frameRange':list(action.frame_range),
            'slots':[{'name':s.name_display,'identifier':s.identifier,'type':s.target_id_type}for s in action.slots]})
    samples = {}
    model=json.loads((MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel').read_text())
    rest={b.name:[list(v)for v in b.matrix_local]for b in armature.data.bones}
    for tag in TAGS:
        action = next(a for a in bpy.data.actions if tag in a.name)
        armature.animation_data.action = action
        if action.slots: armature.animation_data.action_slot = action.slots[0]
        # Only the separately owned in-memory action is adjusted. q and -q are
        # the exact same original keyed orientation; coherent hemispheres avoid
        # component-interpolation spins between them. Never save source.blend.
        bag=action.layers[0].strips[0].channelbag(action.slots[0])
        quaternion_channels={}
        for curve in bag.fcurves:
            if curve.data_path.endswith('rotation_quaternion'):
                quaternion_channels.setdefault(curve.data_path,{})[curve.array_index]=curve
        corrected=0
        for channels in quaternion_channels.values():
            if len(channels)!=4: continue
            previous_q=None
            for index in range(len(channels[0].keyframe_points)):
                q=[channels[i].keyframe_points[index].co.y for i in range(4)]
                if previous_q is not None and sum(x*y for x,y in zip(previous_q,q))<0:
                    for i in range(4):
                        key=channels[i].keyframe_points[index]
                        key.co.y=-key.co.y; key.handle_left.y=-key.handle_left.y; key.handle_right.y=-key.handle_right.y
                    q=[-v for v in q]; corrected+=1
                previous_q=q
        for channels in quaternion_channels.values():
            for curve in channels.values():curve.update()
        frames = []
        start,end=map(float,action.frame_range)
        length=(end-start)/30
        times=[i/40 for i in range(math.floor(length*40)+1)]
        if abs(times[-1]-length)>1e-8: times.append(length)
        previous=None
        for seconds in times:
            frame=start+seconds*30
            bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame))
            evaluated = armature.evaluated_get(bpy.context.evaluated_depsgraph_get())
            matrices={b.name:[list(v)for v in b.matrix]for b in evaluated.pose.bones}
            p=continuous(pose(model,matrices,rest),previous)
            previous=p
            if '_air' in next(k for k,v in CLIPS.items()if v==tag):
                root=max(-8,min(8,(matrices['C7C0BA6E'][2][3]-rest['C7C0BA6E'][2][3])*14.5))
            else:
                lift=max(0,min(matrices[n][2][3]for n in ['B9B9E05D','0F8B505D'])-min(rest[n][2][3]for n in ['B9B9E05D','0F8B505D']))
                root=h15.floor_y(model,p)+lift*14.5
            frames.append({'frame':frame,'seconds':seconds,'matrices':matrices,'targetPose':p,'rootY':root})
        samples[tag]={'action':action.name,'fps':30,'sourceFrameRange':[start,end],'length':length,'equivalentQuaternionHemisphereCorrections':corrected,'frames':frames}
    (OUT/'blend-inspection.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (OUT/'evaluated-source.json').write_text(json.dumps(samples,separators=(',',':'))+'\n')
    export(model,samples,inventory)
    print('W330 evaluated',armature.name,'bones',len(inventory['bones']),'actions',len(inventory['actions']),flush=True)


if __name__ == '__main__': inspect()
