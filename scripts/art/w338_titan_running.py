#!/usr/bin/env python3
"""R3 Titan run-only retarget; source files/main are read only.

Blender -b --factory-startup Titan_Running_R3.blend --python this-file -- --inspect
python3 this-file --export
No gameplay speed changes; only 12 direction loops and owned evidence/resources.
"""
import argparse
import bisect
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
MAIN=Path('/Users/qf/IdeaProjects/DestinyGuardians')
SOURCE=Path('/Users/qf/Downloads/Destiny-Super-Idle-Movement-2026-11-07-R3-Titan-Running')
OUT=ROOT/'art/animation/w338/titan_running'
TEMP=Path('/tmp/w338-titan-running/evaluation')
NAMESPACE=uuid.UUID('78be783c-15b2-4d06-85d2-c7a9d16530cf')
FAMILIES=[('unarmed_fists_candidate','w229_titan_arc'),('hammer_of_sol','w229_titan_solar'),('unarmed_fists_candidate','w229_titan_void')]


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def uid(s):return str(uuid.uuid5(NAMESPACE,s))


def helpers():
    spec=importlib.util.spec_from_file_location('w332_readonly_retarget',MAIN/'scripts/art/w332_super_motion_sources.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def reconstruct(data,sample,motion):
    """Absolute parent-local TRS already includes bind/rest. Add it exactly once."""
    world=[]
    for index,trs in enumerate(sample):
        x,y,z,qx,qy,qz,qw,sx,sy,sz=trs
        norm=math.sqrt(qx*qx+qy*qy+qz*qz+qw*qw)
        matrix=motion.w197.qmatrix([qw/norm,qx/norm,qy/norm,qz/norm])
        for row in range(3):
            for col,scale in enumerate([sx,sy,sz]):matrix[row][col]*=scale
            matrix[row][3]=[x,y,z][row]
        parent=data['parents'][index]
        assert parent<index
        world.append(motion.h15.mm(world[parent],matrix)if parent>=0 else matrix)
    return dict(zip(data['bones'],world))


def sample(data,t,module):
    index=min(len(data['times'])-1,max(0,bisect.bisect_right(data['times'],t)-1))
    other=min(index+1,len(data['times'])-1)
    span=data['times'][other]-data['times'][index]
    f=0 if span==0 else(t-data['times'][index])/span
    values=[]
    for a,b in zip(data['samples'][index],data['samples'][other]):
        qa=[a[6],a[3],a[4],a[5]];qb=[b[6],b[3],b[4],b[5]]
        rotation=module.w197.slerp(module.w197.qmatrix(qa),module.w197.qmatrix(qb),f)
        q=module.w197.quat(rotation)
        values.append([a[i]*(1-f)+b[i]*f for i in range(3)]+[q[1],q[2],q[3],q[0]]+[a[i]*(1-f)+b[i]*f for i in range(7,10)])
    return reconstruct(data,values,module)


def spine_positions(p,matrices,rest,model,module):
    h19,h15,w197,C=module.h19,module.h15,module.w197,module.C
    fk=h19.fk(model,p);point=lambda m,n:[m[n][i][3]for i in range(3)]
    positions={}
    for target,parent,source,source_parent in [('pw_waist','phip_hip','A252A6A2','C7C0BA6E'),('pc_chest','pw_waist','A352A6A2','A252A6A2')]:
        transport=h15.mm(w197.rotation(matrices[source_parent]),h19.inverse_rotation(w197.rotation(rest[source_parent])))
        expected=h19.vector(transport,h19.sub(point(rest,source),point(rest,source_parent)))
        delta=h19.mul(h19.vector(C,h19.sub(h19.sub(point(matrices,source),point(matrices,source_parent)),expected)),14.5)
        positions[target]=h19.vector(h19.inverse_rotation(w197.rotation(fk[parent])),delta)
    return positions


def source_residual(matrices,rest,child,parent,module):
    h19,h15,w197=module.h19,module.h15,module.w197
    pt=lambda m,n:[m[n][i][3]for i in range(3)]
    transport=h15.mm(w197.rotation(matrices[parent]),h19.inverse_rotation(w197.rotation(rest[parent])))
    return h19.sub(h19.sub(pt(matrices,child),pt(matrices,parent)),h19.vector(transport,h19.sub(pt(rest,child),pt(rest,parent))))


def solve_source_arm(model,p,positions,side,target,item_rotation,matrices,rest,module):
    h15,h19,w197=module.h15,module.h19,module.w197
    groups={g['name']:g for g in model['groups']}
    upper,fore,item,chain=(('pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67'])if side=='left'else('pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA']))
    fk=module.motion.fk_positions(model,p,positions);shoulder=h19.point(fk[upper],[0,0,0])
    offset_x=groups[item]['origin'][0]-groups[fore]['origin'][0]
    l1=h19.norm(h19.sub(groups[fore]['origin'],groups[upper]['origin']))
    longitudinal=groups[fore]['origin'][1]-groups[item]['origin'][1]
    l2=math.hypot(longitudinal,offset_x)
    delta=h19.sub(target,shoulder);distance=h19.norm(delta);along=h19.unit(delta)
    assert abs(l1-l2)<distance<l1+l2,(side,distance)
    center=(l1*l1-l2*l2+distance*distance)/(2*distance);radius=math.sqrt(max(0,l1*l1-center*center))
    frame=module.motion.source_bend_frame(matrices,rest,chain)
    normal=h19.vector(module.C,[frame[i][0]for i in range(3)])
    pole=h19.cross(along,normal);pole=h19.unit(h19.sub(pole,h19.mul(along,h19.dot(pole,along))))
    elbow=h19.add(shoulder,h19.add(h19.mul(along,center),h19.mul(pole,radius)))
    down=h19.unit(h19.sub(elbow,shoulder));end=h19.sub(target,elbow)
    bend=math.acos(max(-1,min(1,h19.dot(end,down)/longitudinal)))
    perpendicular=h19.unit(h19.sub(end,h19.mul(down,h19.dot(end,down))))
    y=h19.mul(down,-1);z0=h19.mul(perpendicular,-1);x0=h19.cross(y,z0)
    swivel=-math.atan2(offset_x,longitudinal*math.sin(bend))
    x=h19.add(h19.mul(x0,math.cos(swivel)),h19.mul(z0,math.sin(swivel)))
    z=h19.add(h19.mul(x0,-math.sin(swivel)),h19.mul(z0,math.cos(swivel)))
    world=[[x[i],y[i],z[i],0]for i in range(3)]+[[0,0,0,1]]
    p[upper]=h19.sub(h19.euler(h15.mm(h19.inverse_rotation(w197.rotation(fk['pc_chest'])),world)),groups[upper].get('rotation',[0,0,0]))
    bind_frame=module.motion.source_bend_frame(rest,rest,chain)
    roll_matrix=h15.mm(h19.inverse_rotation(frame),h15.mm(w197.rotation(matrices[chain[1]]),h15.mm(h19.inverse_rotation(w197.rotation(rest[chain[1]])),bind_frame)))
    q=w197.quat(roll_matrix);roll=2*math.atan2(q[2],q[0])
    p[fore]=h19.euler(h15.mm(h15.rot([math.degrees(bend),0,0]),h15.rot([0,math.degrees(roll),0])))
    fk=module.motion.fk_positions(model,p,positions)
    local_target=h19.vector(h19.inverse_rotation(w197.rotation(fk[fore])),h19.sub(target,h19.point(fk[fore],[0,0,0])))
    positions[item]=h19.sub(local_target,h19.sub(groups[item]['origin'],groups[fore]['origin']))
    module.motion.local(model,p,item,item_rotation)
    actual=module.motion.fk_positions(model,p,positions)[item]
    error=h19.norm(h19.sub(h19.point(actual,[0,0,0]),target))
    q0,q1=w197.quat(item_rotation),w197.quat(w197.rotation(actual))
    angular=math.degrees(2*math.acos(min(1,abs(sum(a*b for a,b in zip(q0,q1))))))
    assert error<1e-6 and angular<1e-4 and abs(local_target[0])<2 and abs(local_target[2])<2,(side,error,angular,local_target)
    return error,angular


def source_floor(model,p,positions,module):
    fk=module.motion.fk_positions(model,p,positions);groups={g['uuid']:g for g in model['groups']};elements={e['uuid']:e for e in model['elements']};ys=[]
    def walk(nodes,parent):
        for node in nodes:
            if isinstance(node,str):
                element=elements.get(node,{})
                if element.get('name')!='skin':continue
                origin=parent['origin'];matrix=fk[parent['name']]
                for x in (element['from'][0],element['to'][0]):
                    for y in (element['from'][1],element['to'][1]):
                        for z in (element['from'][2],element['to'][2]):ys.append(module.h19.point(matrix,[x-origin[0],y-origin[1],z-origin[2]])[1])
            else:
                group=groups[node['uuid']];walk(node['children'],group)
    walk(model['outliner'],None)
    return-min(ys)



def selections(family):
    entries={e['role']:e for e in read(SOURCE/'CATALOG.json')['clips']if e['family']==family}
    return {direction:entries['sprint_forward_a'if direction=='forward'else 'run_'+direction]
            for direction in ['forward','backward','left','right']}


def inspect():
    import bpy
    module=helpers();path=SOURCE/'motions/Titan_Running_R3.blend';before=sha(path)
    assert Path(bpy.data.filepath).resolve()==path.resolve()
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_create()
    for track in rig.animation_data.nla_tracks:track.mute=True
    inventory={'source_revision':'R3','path':str(path),'sha256':before,'blender':bpy.app.version_string,
        'armature':rig.name,'armatureWorld':[list(v)for v in rig.matrix_world],
        'boneCount':len(rig.data.bones),'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None}for b in rig.data.bones],
        'actions':[{'name':a.name,'range':list(a.frame_range),'slots':[{'identifier':x.identifier,'target':x.target_id_type}for x in a.slots]}for a in bpy.data.actions],
        'directSampleComparisons':[]}
    selected={e['action']:e for family,_ in FAMILIES for e in selections(family).values()}
    # Both preferred A clips and B alternatives are checked, without rendering all32 actions.
    for family,_ in FAMILIES:
        e=next(x for x in read(SOURCE/'CATALOG.json')['clips']if x['family']==family and x['role']=='sprint_forward_b');selected[e['action']]=e
    for name,entry in selected.items():
        action=next(a for a in bpy.data.actions if a.name==name or a.name.endswith(name))
        rig.animation_data.action=action
        if action.slots:rig.animation_data.action_slot=action.slots[0]
        data=read(SOURCE/entry['sample_file']);comparisons=[]
        assert abs((action.frame_range[1]-action.frame_range[0])/30-data['duration'])<1e-6
        for index in sorted({0,len(data['times'])//2,len(data['times'])-1}):
            frame=action.frame_range[0]+data['times'][index]*30
            bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
            evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get());restored=reconstruct(data,data['samples'][index],module)
            error=max(abs(evaluated.pose.bones[n].matrix[row][col]-mat[row][col])for n,mat in restored.items()for row in range(4)for col in range(4))
            assert error<3e-5,(name,index,error)
            comparisons.append({'seconds':data['times'][index],'maxMatrixComponentError':error})
        inventory['directSampleComparisons'].append({'action':action.name,'samples':comparisons,'bake':entry['bake']})
    assert len(inventory['actions'])==32 and len(rig.data.bones)==72 and sha(path)==before
    write(OUT/'blend-evaluation.json',inventory)
    print('R3 actual .blend:32actions/72bones;',len(selected),'selected A/B + directional start/mid/end TRS checked; source hash unchanged',flush=True)


def full_pose(model,matrices,rest,module):
    """Absolute source limb directions, never an idle-calibrated ready handpoint.

    Target anatomy has wider shoulders and longer forearms than the source. Retain
    actual shoulder/elbow/wrist directions, adapt each segment to its target bind
    length, and carry source clavicle residual and chest/pelvis deformation.
    """
    h15,h19,w197,C=module.h15,module.h19,module.w197,module.C
    p=module.stable_pose(model,matrices,rest)
    positions=spine_positions(p,matrices,rest,model,module)
    fk=h19.fk(model,p);pt=lambda n:[matrices[n][i][3]for i in range(3)]
    groups={g['name']:g for g in model['groups']}
    pelvis=h19.mul(h19.vector(C,source_residual(matrices,rest,'C7C0BA6E','1A5C68E5',module)),14.5)
    positions['phip_hip']=pelvis
    for target,source in [('prl_right_leg','9F0FD28C'),('pll_left_leg','695DAF09')]:
        offset=h19.sub(groups[target]['origin'],groups['phip_hip']['origin'])
        socket=h19.sub(h19.vector(w197.rotation(fk['phip_hip']),offset),offset)
        residual=h19.mul(h19.vector(C,source_residual(matrices,rest,source,'C7C0BA6E',module)),14.5)
        positions[target]=h19.add(pelvis,h19.add(socket,residual))
    for target,source in [('pla_left_arm','D1232BA2'),('pra_right_arm','17025F50')]:
        delta=h19.mul(h19.vector(C,source_residual(matrices,rest,source,'A352A6A2',module)),14.5)
        positions[target]=h19.vector(h19.inverse_rotation(w197.rotation(fk['pc_chest'])),delta)
    fk=module.motion.fk_positions(model,p,positions);metrics={'reachCorrectionUnits':0,'wristPositionErrorUnits':0,'wristRotationErrorDegrees':0}
    chest=w197.rotation(fk['pc_chest']);chest_point=h19.point(fk['pc_chest'],[0,0,0]);source_chest=w197.rotation(matrices['A352A6A2'])
    for side,upper,fore,item,chain in [('left','pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67']),('right','pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA'])]:
        a,b,c=chain
        u=h19.vector(C,h19.unit(h19.sub(pt(b),pt(a))));v=h19.vector(C,h19.unit(h19.sub(pt(c),pt(b))))
        l1=h19.norm(h19.sub(groups[fore]['origin'],groups[upper]['origin']));l2=h19.norm(h19.sub(groups[item]['origin'],groups[fore]['origin']))
        displacement=h19.add(h19.mul(u,l1),h19.mul(v,l2));original=list(displacement)
        if h19.norm(displacement)>10.9:displacement=h19.mul(h19.unit(displacement),10.9)
        target=h19.add(h19.point(fk[upper],[0,0,0]),displacement)
        rotation=w197.rotation(fk[item])
        error,angle=solve_source_arm(model,p,positions,side,target,rotation,matrices,rest,module)
        metrics['reachCorrectionUnits']=max(metrics['reachCorrectionUnits'],h19.norm(h19.sub(original,displacement)))
        metrics['wristPositionErrorUnits']=max(metrics['wristPositionErrorUnits'],error);metrics['wristRotationErrorDegrees']=max(metrics['wristRotationErrorDegrees'],angle)
        # These absolute chest-relative vectors expose a return to ready-pose bias.
        metrics[side+'SourceChestRelativeMeters']=h19.vector(h19.inverse_rotation(source_chest),h19.sub(pt(c),pt('A352A6A2')))
        metrics[side+'TargetChestRelativeUnits']=h19.vector(h19.inverse_rotation(chest),h19.sub(target,chest_point))
    return p,positions,metrics


def export():
    module=helpers();h15,h19,w197=module.h15,module.h19,module.w197
    model_path=MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel';model=read(model_path);groups={g['name']:g for g in model['groups']}
    clips=[];reports=[];reviews=[]
    for family,prefix in FAMILIES:
        for direction,entry in selections(family).items():
            data=read(SOURCE/entry['sample_file']);length=data['duration']
            rest={n:[data['rest_armature_matrices_row_major'][i][row*4:row*4+4]for row in range(4)]for i,n in enumerate(data['bones'])}
            times=[i/40 for i in range(math.floor(length*40+1e-8)+1)]
            if abs(times[-1]-length)>1e-8:times.append(length)
            frames=[];previous=None;allmetrics=[]
            for t in times:
                matrices=sample(data,t,module);p,positions,metrics=full_pose(model,matrices,rest,module)
                p=module.motion.continuous(p,previous);previous=p;root=source_floor(model,p,positions,module)
                frames.append({'seconds':t,'pose':p,'positions':positions,'rootY':root,'source':matrices});allmetrics.append(metrics)
            name=prefix+'_move_'+direction
            clip={'uuid':uid(name),'name':name,'loop':'loop','override':False,'length':length,'snapping':40,'destiny_quaternion_sampling':True,'source_revision':'R3',
                'destiny_locomotion_family':family,'destiny_source_family':family,'destiny_source_composed_action':entry['action'],'destiny_source_base':entry['base'],'destiny_source_period_seconds':length,
                'destiny_floating_locomotion':False,'destiny_direction_provisional':True,'animators':{}}
            for bone in h15.BONES:
                keys=[];last=None
                for f in frames:
                    t=f['seconds'];q=w197.quat(h15.rot(f['pose'][bone]))
                    if last is not None and sum(a*b for a,b in zip(last,q))<0:q=[-v for v in q]
                    last=q;assert abs(sum(v*v for v in q)-1)<1e-6
                    keys.append({'uuid':uid(f'{name}/{bone}/{t}/r'),'channel':'rotation','time':t,'interpolation':'linear','data_points':[dict(zip(['x','y','z'],f['pose'][bone]))],'destiny_quaternion':[q[1],q[2],q[3],q[0]]})
                    if bone=='player_root'or bone in f['positions']:
                        xyz=[0,f['rootY'],0]if bone=='player_root'else f['positions'][bone]
                        keys.append({'uuid':uid(f'{name}/{bone}/{t}/p'),'channel':'position','time':t,'interpolation':'linear','data_points':[dict(zip(['x','y','z'],xyz))]})
                    if bone in ['pri_right_item','pli_left_item']:keys.append({'uuid':uid(f'{name}/{bone}/{t}/s'),'channel':'scale','time':t,'interpolation':'linear','data_points':[{'x':1,'y':1,'z':1}]})
                clip['animators'][groups[bone]['uuid']]={'name':bone,'type':'bone','rotation_global':False,'quaternion_interpolation':True,'keyframes':keys}
            clips.append(clip)
            seam=max(math.degrees(2*math.acos(min(1,abs(sum(a*b for a,b in zip(w197.quat(h15.rot(frames[0]['pose'][bone])),w197.quat(h15.rot(frames[-1]['pose'][bone]))))))))for bone in h15.BONES)
            assert seam<2,(name,seam)
            reports.append({'clip':name,'family':family,'direction':direction,'sourceAction':entry['action'],'sourceBase':entry['base'],'sourcePeriodSeconds':length,
                'sourceSampleFile':entry['sample_file'],'sourceSampleSha256':sha(SOURCE/entry['sample_file']),'bake':entry['bake'],'omittedDrivers':entry.get('omitted_from_neutral_bake',[]),
                'mapping':'deliberate user mapping of same unarmed running to Sentinel; not Sentinel-exclusive source'if prefix.endswith('void')else 'Fists candidate binding; final active-super selection unproven'if prefix.endswith('arc')else 'Hammer named state group32',
                'loopRotationSeamDegrees':seam,'samples':len(frames),'metrics':{key:max(m[key]for m in allmetrics)for key in ['reachCorrectionUnits','wristPositionErrorUnits','wristRotationErrorDegrees']},
                'absoluteChestRelativeWristReview':allmetrics[0],
                'sourceChestRelativeSwingMeters':{side:[max(m[side+'SourceChestRelativeMeters'][a]for m in allmetrics)-min(m[side+'SourceChestRelativeMeters'][a]for m in allmetrics)for a in range(3)]for side in ['left','right']},
                'targetChestRelativeSwingUnits':{side:[max(m[side+'TargetChestRelativeUnits'][a]for m in allmetrics)-min(m[side+'TargetChestRelativeUnits'][a]for m in allmetrics)for a in range(3)]for side in ['left','right']}})
            if direction=='forward':reviews.append((family,prefix,frames))
    payload={'schema_version':1,'source_revision':'R3','animations':clips}
    write(OUT/'titan_running_w338.animation.json',payload)
    runtime=ROOT/'src/main/resources/destiny/animation/titan_running_w338.animation.json';runtime.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OUT/'titan_running_w338.animation.json',runtime)
    manifest={'task':'W338 R3 Titan run-only overlay','source_revision':'R3','sourcePackage':str(SOURCE),'sourceFiles':{n:sha(SOURCE/n)for n in ['README.md','HANDOFF.md','CATALOG.json','FILE-HASHES.json','motions/Titan_Running_R3.blend']},
        'coordinateBasis':module.C,'coordinatePolicy':'Use sampled armature-space matrices verified directly against .blend; source values are meters/game Xforward,Yside,Zup. Do not reapply armature_world/rest; C maps to target X=-sourceY,Y=sourceZ,Z=-sourceX once.',
        'helpers':{str(path.relative_to(MAIN)):sha(path)for path in [MAIN/'scripts/art/w332_super_motion_sources.py',MAIN/'scripts/art/w330_spectral_blades.py']},
        'mathProvenance':'W336 baseline helper snapshot SHA3f98ee73391ae95519a75512453d44da4f4e2476aeb65ecfdfba185429f44dbc; copied reconstruction/spine/IK/floor only; no dynamic dependency on concurrent R2/Maul generator',
        'directBlendEvaluation':'blend-evaluation.json','clipCount':len(clips),'clips':reports,'targetRigSha256':sha(model_path),
        'retarget':'source absolute shoulder/elbow/wrist anatomical directions scaled to target segment lengths, actual per-frame wrist orientation and source clavicle/pelvis/spine/head/legs; no idle-calibrated wrist/ready handpoint, no frozen upperbody mask',
        'sampling':'supplied composed20Hz parent-local absolute TRS (rest included exactly once);40Hz quaternion interpolation + exact endpoint; full original30fps source period, no speed compression',
        'root':'source root XZ omitted; target root XZ zero; visual floor normalization and source residual body translations only',
        'selection':'forward point4 A preferred; B evaluated briefly, same period and catalogue hand swing; lateral/backward CATALOG run_* point1, family-specific direction order',
        'guard':'Selected run clips use constant original weapon_offset/grip only; neutral walking guard51=0/52=1 preset not used',
        'limits':['active Fists-of-Havoc→unarmed selection remains candidate','Sentinel uses same unarmed R3 run by explicit user mapping; not Sentinel-exclusive proven source','gait labels inferred from source motion; source2/4m/s thresholds are examples and unused','source final IK/procedural layers/props/VFX not reproduced; native current Hammer/Shield prop grip/orientation and transitions pending master'],
        'unchanged':['all other R2loops','idle','cast','attack','dodge','gameplay speed','contact/audio','weapon geometry','2tick display interpolation'],
        'nativeAcceptance':'pending root idle→4directions→stop→attack→run return for all3; no client/server/lease touched'}
    write(OUT/'manifest.json',manifest);review(reviews,model,module)
    print('R3 exported12loops; runtime mirror SHA',sha(runtime),'max seam',max(r['loopRotationSeamDegrees']for r in reports),flush=True)


def review(records,model,module):
    """One bounded source vs R2-before vs R3-after body/arm sheet; native pending."""
    chains=[['phip_hip','pw_waist','pc_chest','h_ph_head'],['pc_chest','pla_left_arm','plfa_left_forearm','pli_left_item'],['pc_chest','pra_right_arm','prfa_right_forearm','pri_right_item'],['phip_hip','pll_left_leg','plfl_left_foreleg'],['phip_hip','prl_right_leg','prfl_right_foreleg']]
    source_chains=[['C7C0BA6E','A252A6A2','A352A6A2','7E92D640'],['A352A6A2','D1232BA2','897A1504','8C83CB67'],['A352A6A2','17025F50','A3781DCD','DE9D6BEA'],['C7C0BA6E','695DAF09','35B14D1B','0F8B505D'],['C7C0BA6E','9F0FD28C','8BD44A3F','B9B9E05D']]
    elements={e['uuid']:e for e in model['elements']};groups={g['uuid']:g for g in model['groups']}
    skin=[]
    def collect(nodes,parent=None):
        for node in nodes:
            if isinstance(node,str):
                e=elements.get(node,{})
                if e.get('name')=='skin':skin.append((parent,e))
            else:collect(node['children'],groups[node['uuid']])
    collect(model['outliner'])
    def body(fk,x0,y0,view,color):
        polygons=[]
        for group,e in skin:
            vertices=[module.h19.point(fk[group['name']],[x-group['origin'][0],y-group['origin'][1],z-group['origin'][2]])for x in [e['from'][0],e['to'][0]]for y in [e['from'][1],e['to'][1]]for z in [e['from'][2],e['to'][2]]]
            for face in [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]:
                pts=[vertices[i]for i in face];depth=sum(v[2]if view==0 else v[0]for v in pts)/4
                xy=' '.join(f'{x0+(v[0]if view==0 else-v[2])*3.8:.2f},{y0+220-v[1]*3.8:.2f}'for v in pts)
                polygons.append((depth,f'<polygon points="{xy}" fill="{color}" fill-opacity=".38" stroke="{color}" stroke-width=".65"/>'))
        return ''.join(v for _,v in sorted(polygons,key=lambda x:x[0]))
    old={c['name']:c for c in read(ROOT/'src/main/resources/destiny/animation/super_locomotion_classes_w336.animation.json')['animations']};rows=[]
    for row,(family,prefix,frames)in enumerate(records):
        y0=70+row*300;rows.append(f'<text x="12" y="{y0}" fill="white" font-size="17">{prefix} / {family} / forward A</text>')
        for col,fraction in enumerate([0,.25,.5,.75]):
            f=min(frames,key=lambda f:abs(f['seconds']-frames[-1]['seconds']*fraction));fk=module.motion.fk_positions(model,f['pose'],f['positions'],f['rootY'])
            clip=old[prefix+'_move_forward'];p=module.h15.zero();positions={};t=clip['length']*fraction
            for animator in clip['animators'].values():
                for channel,out in [('rotation',p),('position',positions)]:
                    keys=[k for k in animator['keyframes']if k['channel']==channel]
                    if keys:out[animator['name']]=[float(min(keys,key=lambda k:abs(k['time']-t))['data_points'][0][a])for a in ['x','y','z']]
            root=positions.pop('player_root',[0,0,0])[1];before=module.motion.fk_positions(model,p,positions,root)
            source={n:module.h19.vector(module.C,[f['source'][n][i][3]*14.5 for i in range(3)])for n in f['source']}
            floor=min(v[1]for v in source.values());source={n:[v[0],v[1]-floor,v[2]]for n,v in source.items()}
            for view in range(2):
                for kind,points,paths,color in [('source',source,source_chains,'#e4be5c'),('R2 before',{n:module.h19.point(m,[0,0,0])for n,m in before.items()},chains,'#7e8794'),('R3 after',{n:module.h19.point(m,[0,0,0])for n,m in fk.items()},chains,'#bd9feb')]:
                    offset={'source':-55,'R2 before':0,'R3 after':55}[kind];x0=115+col*510+view*235+offset
                    if kind!='source':rows.append(body(before if kind=='R2 before'else fk,x0,y0,view,color))
                    for chain in paths:
                        xy=' '.join(f'{x0+(points[n][0]if view==0 else-points[n][2])*3.8:.2f},{y0+220-points[n][1]*3.8:.2f}'for n in chain)
                        rows.append(f'<polyline points="{xy}" fill="none" stroke="{color}" stroke-width="2.5"/>')
            rows.append(f'<text x="{30+col*510}" y="{y0+250}" fill="white" font-size="14">phase{fraction:.2f} / front+side</text>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="2100" height="1000" viewBox="0 0 2100 1000"><rect width="2100" height="1000" fill="#17191e"/><text x="12" y="27" fill="white" font-size="19">R3 Titan runs | source gold / R2 before grey / R3 after violet | source joints + target skin geometry; native prop/appearance pending</text>'+''.join(rows)+'</svg>'
    path=OUT/'source-before-after.svg';path.write_text(svg);TEMP.mkdir(parents=True,exist_ok=True)
    subprocess.run(['qlmanage','-t','-s','2100','-o',str(TEMP),str(path)],check=True,capture_output=True)
    shutil.copyfile(TEMP/(path.name+'.png'),OUT/'source-before-after.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--inspect',action='store_true');parser.add_argument('--export',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else sys.argv[1:])
    if args.inspect:inspect()
    elif args.export:export()
    else:parser.error('choose --inspect or --export')
