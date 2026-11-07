#!/usr/bin/env python3
"""Read-only W336 R2 composed class locomotion export; R1 superseded.

Blender --background --factory-startup Guardian_Super_Composed_R2.blend --python this-file
  -- --inspect composed
python3 this-file --export (uses genuine20Hz parent-relative absolute TRS).
Only art/animation/w336/classes is written; raw/evaluation cache stays in /tmp.
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
SOURCE=Path('/Users/qf/Downloads/Destiny-Super-Idle-Movement-2026-11-07-R2')
OUT=ROOT/'art/animation/w336/classes'
TEMP=Path('/tmp/w336-super-locomotion/classes')
NAMESPACE=uuid.UUID('c16b6f35-0f23-47f0-85cd-e41c0fc814ef')
FAMILIES=[('fists_of_havoc_candidate','w229_titan_arc'),('hammer_of_sol','w229_titan_solar'),
 ('sentinel_shield','w229_titan_void'),('burning_maul','w230_titan_burning_maul'),
 ('daybreak','w229_warlock_solar'),('stormtrance','w229_warlock_arc'),('nova_warp','w230_warlock_nova_warp')]
MAUL_LOWER_GRIP_RAW_Y=5.25 # actual sleeve4.75..11.25; source wrists/body remain unchanged
ARMS=['pra_right_arm','prfa_right_forearm','pri_right_item','pla_left_arm','plfa_left_forearm','pli_left_item']


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


def selected_clips(family):
    spec=read(SOURCE/'families'/f'{family}.json')
    entries={c['role']:c for c in spec['clips']}
    if spec['source_type']=='floating':
        return spec,{'idle':entries['idle'],'move':entries['move'],'air':entries['idle']}
    return spec,{role:entries[role if role=='idle' else role+'_v0']for role in ['idle','move_forward','move_backward','move_left','move_right']}


def inspect(kind):
    import bpy
    module=helpers();TEMP.mkdir(parents=True,exist_ok=True)
    path=SOURCE/'motions/Guardian_Super_Composed_R2.blend'
    assert Path(bpy.data.filepath).resolve()==path.resolve()
    original_hash=sha(path)
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    rig.animation_data_create()
    for track in rig.animation_data.nla_tracks:track.mute=True
    inventory={'source_revision':'R2','path':str(path),'sha256':original_hash,'blender':bpy.app.version_string,
        'boneCount':len(rig.data.bones),'actions':[],'directSampleComparisons':[]}
    for action in bpy.data.actions:
        inventory['actions'].append({'name':action.name,'range':list(action.frame_range),
            'slots':[{'identifier':slot.identifier,'type':slot.target_id_type}for slot in action.slots]})
    selected={entry['action']:entry for family,prefix in FAMILIES for entry in selected_clips(family)[1].values()}
    for name,entry in sorted(selected.items()):
        action=next(a for a in bpy.data.actions if a.name==name or a.name.endswith(name))
        rig.animation_data.action=action
        if action.slots:rig.animation_data.action_slot=action.slots[0]
        data=read(SOURCE/entry['sample_file']);comparisons=[]
        for index in sorted({0,len(data['times'])//2,len(data['times'])-1}):
            frame=1+data['times'][index]*30
            bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
            evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
            restored=reconstruct(data,data['samples'][index],module)
            error=max(abs(evaluated.pose.bones[name].matrix[row][col]-matrix[row][col])for name,matrix in restored.items()for row in range(4)for col in range(4))
            assert error<3e-5,(name,index,error)
            comparisons.append({'seconds':data['times'][index],'maxMatrixComponentError':error})
        inventory['directSampleComparisons'].append({'action':action.name,'samples':comparisons,'bake':entry['bake']})
    assert len(inventory['actions'])==105 and len(rig.data.bones)==72 and sha(path)==original_hash
    write(TEMP/'R2-composed-blend-evaluation.json',inventory)
    print('R2 actual composed blend:105actions/72bones; selected',len(selected),'start/mid/end source TRS checked; source hash unchanged',flush=True)


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


def ready_pose(clip,bones):
    p={bone:[0,0,0]for bone in bones};positions={}
    for animator in clip['animators'].values():
        name=animator['name']
        for channel,destination in [('rotation',p),('position',positions)]:
            keys=[k for k in animator['keyframes']if k['channel']==channel]
            if keys:
                key=min(keys,key=lambda k:k['time'])
                destination[name]=[float(key['data_points'][0].get(axis,0))for axis in ['x','y','z']]
    return p,positions


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


def palm_geometry(model):
    groups={g['uuid']:g for g in model['groups']};elements={e['uuid']:e for e in model['elements']};result={}
    def walk(nodes):
        for node in nodes:
            if isinstance(node,str):continue
            group=groups[node['uuid']]
            if group['name']in ['prfa_right_forearm','plfa_left_forearm']:
                skin=next(elements[child]for child in node['children']if isinstance(child,str)and elements[child].get('name')=='skin')
                lo=[skin['from'][i]-group['origin'][i]for i in range(3)];hi=[skin['to'][i]-group['origin'][i]for i in range(3)]
                # Actual lower-arm skin has no separate finger joint. Its distal
                #1.5u slab is the visible palm volume, not the item-node origin.
                hi[1]=lo[1]+1.5
                result[group['name']]={'min':lo,'max':hi,'center':[(a+b)/2 for a,b in zip(lo,hi)]}
            walk(node['children'])
    walk(model['outliner']);return result


def fit_maul_shaft(model,p,positions,module):
    h15,h19,w197=module.h15,module.h19,module.w197
    mesh=read(MAIN/'src/main/resources/assets/destiny/models/class_ability/titan/burning_maul.json')
    shaft=next(e for e in mesh['elements']if e.get('name')=='continuous_heavy_shaft')
    display=mesh['display']['thirdperson_righthand']
    assert display['rotation']==[0,0,0]and display['scale']==[1,1,1]and display['translation']==[0,2,0]
    palms=palm_geometry(model);fk=module.motion.fk_positions(model,p,positions)
    left=h19.point(fk['plfa_left_forearm'],palms['plfa_left_forearm']['center'])
    right=h19.point(fk['prfa_right_forearm'],palms['prfa_right_forearm']['center'])
    axis=h19.unit(h19.sub(right,left));distance=h19.norm(h19.sub(right,left))
    # Lower left palm is inside the model's actual lower sleeve; the right upper
    # hand rests further along the same physical continuous shaft. Source hand
    # movement changes that upper grip naturally instead of stretching the mesh.
    lower_grip=MAUL_LOWER_GRIP_RAW_Y
    assert shaft['from'][1]<lower_grip<lower_grip+distance<shaft['to'][1],distance
    old=w197.rotation(fk['pri_right_item']);source_z=[old[i][2]for i in range(3)]
    z=h19.sub(source_z,h19.mul(axis,h19.dot(source_z,axis)))
    assert h19.norm(z)>.05,'Ambiguous source wrist roll; inspect before inventing an orientation'
    z=h19.unit(z);x=h19.unit(h19.cross(axis,z));z=h19.cross(x,axis)
    rotation=[[x[i],axis[i],z[i],0]for i in range(3)]+[[0,0,0,1]]
    # Actual model projection: raw-center8, thirdperson translation+2Y. Native
    # innerRy180 and BB/game XZ basis leave the centerline/+Y axis unchanged.
    node=h19.sub(left,h19.vector(rotation,[0,lower_grip-6,0]))
    fore=fk['prfa_right_forearm'];groups={g['name']:g for g in model['groups']}
    positions['pri_right_item']=h19.sub(h19.vector(h19.inverse_rotation(w197.rotation(fore)),h19.sub(node,h19.point(fore,[0,0,0]))),h19.sub(groups['pri_right_item']['origin'],groups['prfa_right_forearm']['origin']))
    module.motion.local(model,p,'pri_right_item',rotation)
    actual=module.motion.fk_positions(model,p,positions)['pri_right_item']
    start=h19.point(actual,[0,shaft['from'][1]-6,0]);end=h19.point(actual,[0,shaft['to'][1]-6,0])
    direction=h19.unit(h19.sub(end,start));maximum=0;hits=[]
    for name,point in [('plfa_left_forearm',left),('prfa_right_forearm',right)]:
        along=h19.dot(h19.sub(point,start),direction)
        closest=h19.add(start,h19.mul(direction,along));maximum=max(maximum,h19.norm(h19.sub(point,closest)))
        assert 0<along<h19.norm(h19.sub(end,start))
        # Independent segment-vs-actual distal skin box intersection, using
        # decoded mesh bounds rather than the IK target used to solve the arm.
        inv=h19.inverse_rotation(w197.rotation(fk[name]));origin=h19.point(fk[name],[0,0,0])
        a=h19.vector(inv,h19.sub(start,origin));b=h19.vector(inv,h19.sub(end,origin));lo,hi=0.,1.
        for dim in range(3):
            delta=b[dim]-a[dim];bounds=palms[name]
            if abs(delta)<1e-9:assert bounds['min'][dim]<=a[dim]<=bounds['max'][dim]
            else:
                t0=(bounds['min'][dim]-a[dim])/delta;t1=(bounds['max'][dim]-a[dim])/delta
                lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
        assert lo<=hi,(name,lo,hi)
        hits.append((hi-lo)*h19.norm(h19.sub(end,start)))
    assert maximum<1e-6
    return {'actualShaftPalmRadialErrorUnits':maximum,'upperRightGripRawY':lower_grip+distance,'lowerLeftGripRawY':lower_grip,'shaftThroughPalmMinimumLengthUnits':min(hits)}


def full_pose(model,matrices,rest,reference,calibration,module,maul=False):
    h15,h19,w197,C=module.h15,module.h19,module.w197,module.C
    p=module.stable_pose(model,matrices,rest)
    positions=spine_positions(p,matrices,rest,model,module)
    fk=h19.fk(model,p);pt=lambda m,n:[m[n][i][3]for i in range(3)]
    pelvis=h19.mul(h19.vector(C,source_residual(matrices,rest,'C7C0BA6E','1A5C68E5',module)),14.5)
    positions['phip_hip']=pelvis
    groups={g['name']:g for g in model['groups']}
    # Legs are root siblings in the fixed player rig. Carry both hip sockets with
    # the source pelvis rotation/translation instead of detaching them at root.
    for target,source in [('prl_right_leg','9F0FD28C'),('pll_left_leg','695DAF09')]:
        offset=h19.sub(groups[target]['origin'],groups['phip_hip']['origin'])
        socket=h19.sub(h19.vector(w197.rotation(fk['phip_hip']),offset),offset)
        residual=h19.mul(h19.vector(C,source_residual(matrices,rest,source,'C7C0BA6E',module)),14.5)
        positions[target]=h19.add(pelvis,h19.add(socket,residual))
    for target,source in [('pla_left_arm','D1232BA2'),('pra_right_arm','17025F50')]:
        delta=h19.mul(h19.vector(C,source_residual(matrices,rest,source,'A352A6A2',module)),14.5)
        positions[target]=h19.vector(h19.inverse_rotation(w197.rotation(fk['pc_chest'])),delta)
    fk=module.motion.fk_positions(model,p,positions);chest=w197.rotation(fk['pc_chest']);chest_pos=h19.point(fk['pc_chest'],[0,0,0])
    source_chest=w197.rotation(matrices['A352A6A2']);ref_chest=w197.rotation(reference['A352A6A2'])
    reference_fk=calibration
    # R2 source-reference/target-bind grip calibration is not an upper-body mask.
    # Every subsequent wrist displacement and rotation comes from R2 composition.
    axes=h15.mm(h19.inverse_rotation(w197.rotation(reference_fk['pc_chest'])),h15.mm(C,ref_chest))
    targets={};rotations={};relative_motion=0
    for side,item,source in [('left','pli_left_item','8C83CB67'),('right','pri_right_item','DE9D6BEA')]:
        ref_rel=h19.vector(h19.inverse_rotation(ref_chest),h19.sub(pt(reference,source),pt(reference,'A352A6A2')))
        now_rel=h19.vector(h19.inverse_rotation(source_chest),h19.sub(pt(matrices,source),pt(matrices,'A352A6A2')))
        change=h19.mul(h19.vector(axes,h19.sub(now_rel,ref_rel)),14.5);relative_motion=max(relative_motion,h19.norm(change))
        target_rel=h19.vector(h19.inverse_rotation(w197.rotation(reference_fk['pc_chest'])),h19.sub(h19.point(reference_fk[item],[0,0,0]),h19.point(reference_fk['pc_chest'],[0,0,0])))
        targets[side]=h19.add(chest_pos,h19.vector(chest,h19.add(target_rel,change)))
        if maul:
            # W337: absolute R2 anatomical wrist placement, not a rotation-only
            # FK reference plus deltas. Different limb proportions are handled
            # by the arm IK; this restores the correct source grip baseline.
            targets[side]=h19.add(chest_pos,h19.mul(h19.vector(C,h19.sub(pt(matrices,source),pt(matrices,'A352A6A2'))),14.5))
        now_local=h15.mm(h19.inverse_rotation(source_chest),w197.rotation(matrices[source]))
        ref_local=h15.mm(h19.inverse_rotation(ref_chest),w197.rotation(reference[source]))
        rotation_delta=h15.mm(axes,h15.mm(now_local,h15.mm(h19.inverse_rotation(ref_local),h19.inverse_rotation(axes))))
        reference_local=h15.mm(h19.inverse_rotation(w197.rotation(reference_fk['pc_chest'])),w197.rotation(reference_fk[item]))
        rotations[side]=h15.mm(chest,h15.mm(rotation_delta,reference_local))
    originals={side:list(v)for side,v in targets.items()}
    # Common projection retains the full R2 relative two-wrist trajectory while
    # fitting different player limb proportions. It never freezes either arm.
    for iteration in range(16):
        for side,upper in [('left','pla_left_arm'),('right','pra_right_arm')]:
            shoulder=h19.point(fk[upper],[0,0,0]);delta=h19.sub(targets[side],shoulder);distance=h19.norm(delta)
            bounded=min(10.9,max(.3,distance))
            if abs(distance-bounded)>1e-9:
                correction=h19.sub(h19.add(shoulder,h19.mul(h19.unit(delta),bounded)),targets[side])
                for which in targets:targets[which]=h19.add(targets[which],correction)
    grip_error=0;angular_error=0
    for side in ['left','right']:
        err,angle=solve_source_arm(model,p,positions,side,targets[side],rotations[side],matrices,rest,module)
        grip_error=max(grip_error,err);angular_error=max(angular_error,angle)
    pair_error=h19.norm(h19.sub(h19.sub(targets['left'],targets['right']),h19.sub(originals['left'],originals['right'])))
    metrics={'pelvisDisplacementUnits':h19.norm(pelvis),'wristSourceRelativeMotionUnits':relative_motion,'commonReachCorrectionUnits':h19.norm(h19.sub(targets['right'],originals['right'])),'pairTrajectoryResidualUnits':pair_error,'gripPositionErrorUnits':grip_error,'gripRotationErrorDegrees':angular_error}
    if maul:metrics.update(fit_maul_shaft(model,p,positions,module))
    return p,positions,metrics


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


def export(maul_only=False):
    module=helpers();h15,h19,w197=module.h15,module.h19,module.w197
    model=read(MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel');groups={g['name']:g for g in model['groups']}
    clips=[];reports=[];review_frames=[];allmetrics=[]
    selected_families=[('burning_maul','w230_titan_burning_maul')]if maul_only else FAMILIES
    for family,prefix in selected_families:
        spec,selected=selected_clips(family);floating=spec['source_type']=='floating'
        reference_data=read(SOURCE/selected['idle']['sample_file']);reference=reconstruct(reference_data,reference_data['samples'][0],module)
        reference_rest={n:[reference_data['rest_armature_matrices_row_major'][i][row*4:row*4+4]for row in range(4)]for i,n in enumerate(reference_data['bones'])}
        reference_pose=module.stable_pose(model,reference,reference_rest)
        reference_positions=spine_positions(reference_pose,reference,reference_rest,model,module)
        calibration=module.motion.fk_positions(model,reference_pose,reference_positions)
        for role,entry in selected.items():
            data=read(SOURCE/entry['sample_file']);length=data['duration']
            rest={n:[data['rest_armature_matrices_row_major'][i][row*4:row*4+4]for row in range(4)]for i,n in enumerate(data['bones'])}
            times=[i/40 for i in range(math.floor(length*40+1e-8)+1)]
            if abs(times[-1]-length)>1e-8:times.append(length)
            frames=[];previous=None
            for t in times:
                matrices=sample(data,t,module)
                p,positions,metrics=full_pose(model,matrices,rest,reference,calibration,module,family=='burning_maul')
                p=module.motion.continuous(p,previous);previous=p
                root=0 if floating else source_floor(model,p,positions,module)
                frames.append({'seconds':t,'pose':p,'positions':positions,'rootY':root});allmetrics.append(metrics)
            name=prefix+'_'+role
            clip={'uuid':uid(name),'name':name,'loop':'loop','override':False,'length':length,'snapping':40,'destiny_quaternion_sampling':True,'source_revision':'R2',
                'destiny_locomotion_family':family,'destiny_source_composed_action':entry['action'],'destiny_source_base':entry['base'],'destiny_source_period_seconds':length,
                'destiny_floating_locomotion':floating,'destiny_direction_provisional':role.startswith('move_'),'animators':{}}
            for bone in h15.BONES:
                keys=[];last=None
                for f in frames:
                    t=f['seconds'];q=w197.quat(h15.rot(f['pose'][bone]))
                    if last is not None and sum(a*b for a,b in zip(last,q))<0:q=[-v for v in q]
                    last=q
                    keys.append({'uuid':uid(f'{name}/{bone}/{t}/r'),'channel':'rotation','time':t,'interpolation':'linear','data_points':[dict(zip(['x','y','z'],f['pose'][bone]))],'destiny_quaternion':[q[1],q[2],q[3],q[0]]})
                    if bone=='player_root' or bone in f['positions']:
                        xyz=[0,f['rootY'],0]if bone=='player_root'else f['positions'][bone]
                        keys.append({'uuid':uid(f'{name}/{bone}/{t}/p'),'channel':'position','time':t,'interpolation':'linear','data_points':[dict(zip(['x','y','z'],xyz))]})
                    if bone in ['pri_right_item','pli_left_item']:keys.append({'uuid':uid(f'{name}/{bone}/{t}/s'),'channel':'scale','time':t,'interpolation':'linear','data_points':[{'x':1,'y':1,'z':1}]})
                clip['animators'][groups[bone]['uuid']]={'name':bone,'type':'bone','rotation_global':False,'quaternion_interpolation':True,'keyframes':keys}
            clips.append(clip)
            seam=max(math.degrees(2*math.acos(min(1,abs(sum(a*b for a,b in zip(w197.quat(h15.rot(frames[0]['pose'][bone])),w197.quat(h15.rot(frames[-1]['pose'][bone]))))))))for bone in h15.BONES)
            reports.append({'clip':name,'source_revision':'R2','family':family,'group':spec['group'],'bindingStatus':spec['binding_status'],'role':role,'sourceAction':entry['action'],'sourceBase':entry['base'],'bake':entry['bake'],'omittedDrivers':entry.get('omitted_from_neutral_bake',[]),'sourceSampleFile':entry['sample_file'],'sourceSampleSha256':sha(SOURCE/entry['sample_file']),'sourcePeriodSeconds':length,'inferredDirection':entry.get('inferred_direction'),'sourceLoopCandidate':entry['loop_candidate'],'loopRotationSeamDegrees':seam,'fullCoupledChannels':True,'gripPolicy':('W337 absolute R2 chest-relative wrists and source elbow/roll; actual mesh shaft +2Y display transform fitted to both distal skin palm volumes'if family=='burning_maul'else'source wrist/elbow trajectories calibrated only to R2 composed idle and existing item bind nodes; no older ready pose, frozen arms or R1 masks'),'floatingPreviewPreset':floating,'aliasOf':prefix+'_idle'if role=='air'else None})
            if role in ['idle','move_forward','move']:review_frames.append((family,role,frames[0],frames[len(frames)//2],model))
    if maul_only:
        baseline_path=MAIN/'art/animation/w336/classes/super_locomotion_classes_w336.animation.json'
        baseline_text=baseline_path.read_text();decoder=json.JSONDecoder();offset=baseline_text.index('[',baseline_text.index('"animations"'))+1
        replacements={c['name']:c for c in clips};ranges=[]
        while True:
            while baseline_text[offset].isspace()or baseline_text[offset]==',':offset+=1
            if baseline_text[offset]==']':break
            value,end=decoder.raw_decode(baseline_text,offset)
            if value['name']in replacements:
                rendered=json.dumps(replacements[value['name']],ensure_ascii=False,indent=2,allow_nan=False).replace('\n','\n    ')
                ranges.append((offset,end,rendered))
            offset=end
        assert len(ranges)==5
        for a,b,value in reversed(ranges):baseline_text=baseline_text[:a]+value+baseline_text[b:]
        (OUT/'super_locomotion_classes_w336.animation.json').write_text(baseline_text)
        baseline_manifest=read(MAIN/'art/animation/w336/classes/manifest.json')
        for index,record in enumerate(baseline_manifest['clips']):
            replacement=next((r for r in reports if r['clip']==record['clip']),None)
            if replacement:baseline_manifest['clips'][index]=replacement
        baseline_manifest['maulGripRevision']={'revision':'W337 actual mesh shaft / absolute R2 wrists','clips':list(replacements),'metricsMax':{k:max(m[k]for m in allmetrics)for k in allmetrics[0]if k!='shaftThroughPalmMinimumLengthUnits'},'metricsMin':{'shaftThroughPalmMinimumLengthUnits':min(m['shaftThroughPalmMinimumLengthUnits']for m in allmetrics)},'other26Clips':'raw per-clip JSON bytes preserved','nativeAcceptance':'pending master idle/4directions/attack-return review'}
        write(OUT/'manifest.json',baseline_manifest)
        print('W337 Maul-only physical grip corrected; untouched26clip byte ranges retained',baseline_manifest['maulGripRevision']['metricsMax'],flush=True)
        return
    write(OUT/'super_locomotion_classes_w336.animation.json',{'schema_version':1,'source_revision':'R2','animations':clips})
    evaluation=read(TEMP/'R2-composed-blend-evaluation.json')
    manifest={'task':'W336 R2 composed Titan/Warlock locomotion','source_revision':'R2','R1Status':'superseded; private evidence only, no R1 family table/layer decode/upperbody mask retained','sourcePackage':str(SOURCE),
        'sourceFiles':{n:sha(SOURCE/n)for n in ['README.md','HANDOFF.md','CATALOG.json','FILE-HASHES.json','motions/Guardian_Super_Composed_R2.blend','motions/Guardian_Super_Composed_R2.fbx']},
        'directBlendEvaluation':evaluation,'clipCount':len(clips),'clips':reports,'targetRigSha256':sha(MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'),
        'sampling':'R2 actual composed20Hz absolute parent-local TRS including rest, reconstruct hierarchy once; quaternion slerp40Hz + exact endpoint; full source periods, no time compression',
        'fullBody':'source pelvis/spine/head, hip socket position, legs, clavicle/shoulder, elbow and both wrists remain coupled. Source layer masks already baked by R2 Charm Apply/Evaluate, no extra upperbody mask or100% ad-hoc layer blend.',
        'grip':'R2 composed idle reference and existing target item bind nodes calibrate anatomical frame/hand spacing only; no older ready animation is used. Source wrist displacement/rotation and elbow plane drive each frame; common two-arm reach projection retains relative wrist trajectory; existing item pivot counter-transform keeps hand contact.',
        'root':'source global root travel omitted; root X/Z zero. Root-relative pelvis oscillation is visual per-bone motion, including original floating bob. Ground support visual floor normalization; floating vertical source body motion preserved without invented sway.',
        'sourceLimits':['Fists of Havoc uses R2 candidate binding, not confirmed exact active-super selection','Sentinel uses shared shield state, not exclusive complete Sentinel runtime','Stormtrance/Nova idle8D3 and move8AF are genuinely animated. Moving floating R2 preset weight1/30fps is preview policy, not decoded live speed→weight driver. Runtime uses actual displacement idle/move even airborne.','Original source props/final procedural IK/aim and some runtime driver weights remain absent; actual current mesh grip requires native acceptance.'],
        'unchanged':['cast','attack','dodge','RMB binding','contact','audio','clip periods','2tick display interpolation','rig geometry/UV'],
        'retargetMetricsMax':{k:max(m[k]for m in allmetrics)for k in allmetrics[0]},'nativeAcceptance':'pending master full R2 idle/move/direction/grip/float review'}
    write(OUT/'manifest.json',manifest);write(OUT/'families-selected.json',{family:read(SOURCE/'families'/f'{family}.json')for family,prefix in FAMILIES})
    review(review_frames,module)
    print('R2 classes exported',len(clips),'clips; max metrics',manifest['retargetMetricsMax'],flush=True)


def review(records,module):
    rows=[];chains=[['phip_hip','pw_waist','pc_chest','h_ph_head'],['pc_chest','pla_left_arm','plfa_left_forearm','pli_left_item'],['pc_chest','pra_right_arm','prfa_right_forearm','pri_right_item'],['phip_hip','pll_left_leg','plfl_left_foreleg'],['phip_hip','prl_right_leg','prfl_right_foreleg']]
    # One bounded review sheet: each family's idle and forward/static move midpoint.
    for row,(family,role,a,b,model)in enumerate(records):
        y0=45+row*145
        rows.append(f'<text x="12" y="{y0}" fill="white" font-size="17">{family} / {role}</text>')
        for col,f in enumerate([a,b]):
            fk=module.motion.fk_positions(model,f['pose'],f['positions'],f['rootY'])
            for view in range(2):
                for chain in chains:
                    coords=[]
                    for bone in chain:
                        p=module.h19.point(fk[bone],[0,0,0]);x=p[0]if view==0 else-p[2]
                        coords.append(f'{500+col*650+view*260+x*4:.2f},{y0+120-p[1]*4:.2f}')
                    rows.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="#cda9ed" stroke-width="3"/>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="2100" height="2100" viewBox="0 0 2100 2100"><rect width="2100" height="2100" fill="#17191e"/><text x="12" y="24" fill="white" font-size="19">W336 R2 composed class locomotion | first/midpoint + front/side | static FK review, native direction/grip acceptance pending</text>'+''.join(rows)+'</svg>'
    path=OUT/'representative-poses.svg';path.write_text(svg)
    subprocess.run(['qlmanage','-t','-s','2100','-o',str(TEMP),str(path)],check=True,capture_output=True)
    shutil.copyfile(TEMP/(path.name+'.png'),OUT/'representative-poses.png')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--inspect',choices=['composed']);parser.add_argument('--export',action='store_true');parser.add_argument('--maul-only',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else sys.argv[1:])
    if args.inspect:inspect(args.inspect)
    elif args.export:export(args.maul_only)
    else:parser.error('choose --inspect or --export')
