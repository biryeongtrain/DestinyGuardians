#!/usr/bin/env python3
"""W332 original Shadowshot/Nova Warp/Daybreak visual payloads; headless Blender only.

Open each original source.blend with --background --factory-startup, then pass
--python this-script -- --group shadowshot|nova_warp|daybreak. Does not save the source,
change the player rig, write runtime resources, or alter gameplay contact times.
"""
import argparse
import gzip
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
LIGHT=Path('/Users/qf/Downloads/Destiny-Light-Abilities-2026-10-28/Destiny-Light-Abilities-2026-10-28/animations')
spec=importlib.util.spec_from_file_location('spectral_w330_readonly_helpers',MAIN/'scripts/art/w330_spectral_blades.py')
motion=importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion)
h15,h19,w197,C=motion.h15,motion.h19,motion.w197,motion.C
NAMESPACE=uuid.UUID('21450cea-1871-42ed-8a92-bbcc3bfb1113')

GROUPS={
 'shadowshot':('hunter_shadowshot',{
    'h15_super_void_attack':('80A8AD97',False),
    'h15_super_void_attack_air':('80A8AD8A',False)}),
 'nova_warp':('warlock_nova_warp',{
    'w230_warlock_nova_warp_charge_idle':('80A8A99C',True),
    'w230_warlock_nova_warp_charge_exit':('80A8A99D',False)}),
 'daybreak':('warlock_daybreak',{
    'w229_warlock_solar_start_air':('80A8A973',False)})}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def uid(s):return str(uuid.uuid5(NAMESPACE,s))
def encode(value):return(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def stable_pose(model,matrices,rest):
    """Use source joint-roll transport for bend poles near straight limbs.

    Cross(upper,lower) becomes ambiguous at extension. The source upper-joint
    quaternion still defines that plane, so transport the bind bend normal by
    that quaternion. This fixes target IK flips without filtering source motion.
    """
    p=h15.zero();groups={g['name']:g for g in model['groups']};bind=h19.fk(model,p)
    point=lambda m,n:[m[n][i][3]for i in range(3)]
    def delta(n):return h15.mm(w197.rotation(matrices[n]),h19.inverse_rotation(w197.rotation(rest[n])))
    def orientation(n,target):return h15.mm(C,h15.mm(delta(n),h15.mm(h19.inverse_rotation(C),w197.rotation(bind[target]))))
    def plane(chain):
        a,b,c=chain
        u0=h19.unit(h19.sub(point(rest,b),point(rest,a)))
        v0=h19.unit(h19.sub(point(rest,c),point(rest,b)))
        normal=h19.unit(h19.cross(u0,v0))
        return h19.vector(C,h19.vector(delta(a),normal))
    for target,n in [('phip_hip','C7C0BA6E'),('pw_waist','A252A6A2'),('pc_chest','A352A6A2'),('h_ph_head','7E92D640')]:
        motion.local(model,p,target,orientation(n,target))
    for upper,lower,chain in [('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]:
        a,b,c=chain
        u=h19.unit(h19.sub(point(matrices,b),point(matrices,a)))
        v=h19.unit(h19.sub(point(matrices,c),point(matrices,b)))
        y=h19.mul(h19.vector(C,u),-1);normal=plane(chain)
        x=h19.unit(h19.sub(normal,h19.mul(y,h19.dot(normal,y))))
        z=h19.cross(x,y)
        frame=[[x[i],y[i],z[i],0]for i in range(3)]+[[0,0,0,1]]
        motion.local(model,p,upper,h15.mm(frame,h15.rot([0,180,0])))
        p[lower]=[-math.degrees(math.acos(max(-1,min(1,h19.dot(u,v))))),0,0]
    for side,upper,fore,item,chain in [('left','pla_left_arm','plfa_left_forearm','pli_left_item',['D1232BA2','897A1504','8C83CB67']),('right','pra_right_arm','prfa_right_forearm','pri_right_item',['17025F50','A3781DCD','DE9D6BEA'])]:
        a,b,c=chain
        u=h19.vector(C,h19.unit(h19.sub(point(matrices,b),point(matrices,a))))
        v=h19.vector(C,h19.unit(h19.sub(point(matrices,c),point(matrices,b))))
        l1=h19.norm(h19.sub(groups[fore]['origin'],groups[upper]['origin']))
        l2=h19.norm(h19.sub(groups[item]['origin'],groups[fore]['origin']))
        displacement=h19.add(h19.mul(u,l1),h19.mul(v,l2))
        if h19.norm(displacement)>10.9:displacement=h19.mul(h19.unit(displacement),10.9)
        along=h19.unit(displacement)
        pole=h19.cross(along,plane(chain))
        shoulder=h19.point(h19.fk(model,p)[upper],[0,0,0])
        h19.solve_arm(model,p,side,h19.add(shoulder,displacement),pole)
        motion.local(model,p,item,orientation(c,item))
    return p


def make_clip(model,name,tag,frames,length,loop,source_length):
    groups={g['name']:g for g in model['groups']}
    result={'uuid':uid(name),'name':name,'loop':'once','override':False,'length':length,'snapping':60,
        'destiny_quaternion_sampling':True,'destiny_entry_blend_ticks':1,'destiny_exit_blend_ticks':2,
        'destiny_source_tag':tag,'destiny_source_duration_seconds':source_length,
        'destiny_contact_provisional':True,'destiny_gameplay_contact_policy':'unchanged existing runtime; no decoded source release/impact event',
        'destiny_static_source_hold':loop,'animators':{}}
    maxstep=0;largest=None
    for bone in h15.BONES:
        keys=[];last=None
        for f in frames:
            t,p=f['seconds'],f['targetPose']
            q=w197.quat(h15.rot(p[bone])) # w,x,y,z in target Blockbench frame
            if last is not None:
                dot=sum(x*y for x,y in zip(last,q))
                if dot<0:q=[-v for v in q];dot=-dot
                step=math.degrees(2*math.acos(min(1,dot)))
                if step>maxstep:maxstep=step;largest={'bone':bone,'seconds':t,'degrees':step}
            last=q
            assert abs(sum(v*v for v in q)-1)<1e-6
            keys.append({'uuid':uid(f'{name}/{bone}/{t}/r'),'channel':'rotation','time':t,'interpolation':'linear',
                'data_points':[dict(zip(['x','y','z'],p[bone]))], 'destiny_quaternion':[q[1],q[2],q[3],q[0]]})
            if bone=='player_root':keys.append({'uuid':uid(f'{name}/{bone}/{t}/p'),'channel':'position','time':t,'interpolation':'linear','data_points':[{'x':0,'y':f['rootY'],'z':0}]})
            if bone in ['pli_left_item','pri_right_item']:keys.append({'uuid':uid(f'{name}/{bone}/{t}/s'),'channel':'scale','time':t,'interpolation':'linear','data_points':[{'x':1,'y':1,'z':1}]})
        result['animators'][groups[bone]['uuid']]={'name':bone,'type':'bone','rotation_global':False,'quaternion_interpolation':True,'keyframes':keys}
    return result,largest


def review(out,group,model,records):
    chains=[['C7C0BA6E','A252A6A2','A352A6A2','7E92D640'],['A352A6A2','D1232BA2','897A1504','8C83CB67'],['A352A6A2','17025F50','A3781DCD','DE9D6BEA'],['C7C0BA6E','695DAF09','35B14D1B','0F8B505D'],['C7C0BA6E','9F0FD28C','8BD44A3F','B9B9E05D']]
    targets=[['phip_hip','pw_waist','pc_chest','h_ph_head'],['pc_chest','pla_left_arm','plfa_left_forearm','pli_left_item'],['pc_chest','pra_right_arm','prfa_right_forearm','pri_right_item'],['phip_hip','pll_left_leg','plfl_left_foreleg'],['phip_hip','prl_right_leg','prfl_right_foreleg']]
    colors=['#eeeeee','#e9bd50','#72bbee','#e9bd50','#72bbee']
    rows=[]
    for row,record in enumerate(records):
        y0=65+row*260;length=record['length']
        rows.append(f'<text x="20" y="{y0}" fill="white" font-size="17">{record["name"]} | {record["tag"]} | full source {record["sourceLength"]:.6f}s / hold {record["loop"]}</text>')
        for column,fraction in enumerate([0,.25,.55,1]):
            f=min(record['frames'],key=lambda f:abs(f['seconds']-length*fraction))
            m=f['matrices'];p=f['targetPose'];fk=h19.fk(model,p,f['rootY'])
            sourcepoints={n:h19.vector(C,[m[n][i][3]*14.5 for i in range(3)])for n in m}
            targetpoints={n:h19.point(matrix,[0,0,0])for n,matrix in fk.items()}
            x0=120+column*480
            rows.append(f'<text x="{x0-70}" y="{y0+25}" fill="#bbbbbb" font-size="15">{f["seconds"]:.3f}s / front + side</text>')
            for view in range(2):
                def project(v,offset):return(x0+offset+(v[0]if view==0 else-v[2])*5.1,y0+205-v[1]*5.1)
                for chain,color in zip(chains,colors):
                    coords=' '.join(f'{x:.2f},{y:.2f}'for x,y in [project(sourcepoints[n],view*210-55)for n in chain])
                    rows.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3"/>')
                for chain in targets:
                    coords=' '.join(f'{x:.2f},{y:.2f}'for x,y in [project(targetpoints[n],view*210+35)for n in chain])
                    rows.append(f'<polyline points="{coords}" fill="none" stroke="#d9a7ec" stroke-width="3"/>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="2050" height="2050" viewBox="0 0 2050 2050"><rect width="2050" height="2050" fill="#17191e"/><text x="20" y="28" fill="white" font-size="21">W332 '+group+' | direct source.blend / source white-gold-cyan vs target purple | static diagram, native acceptance pending</text>'+''.join(rows)+'</svg>'
    svg_path=out/'source-target-review.svg';svg_path.write_text(svg)
    # One representative review image per group, not a render/performance gate.
    temp=Path('/tmp/w332-super-review')/group;temp.mkdir(parents=True,exist_ok=True)
    subprocess.run(['qlmanage','-t','-s','2050','-o',str(temp),str(svg_path)],check=True,capture_output=True)
    shutil.copyfile(temp/(svg_path.name+'.png'),out/'source-target-review.png')


def main():
    import bpy
    parser=argparse.ArgumentParser();parser.add_argument('--group',choices=GROUPS,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    group,selected=GROUPS[args.group];source=LIGHT/group;out=ROOT/'art/animation/w332'/args.group
    out.mkdir(parents=True,exist_ok=True)
    before=sha(source/'source.blend')
    assert Path(bpy.data.filepath).resolve()==(source/'source.blend').resolve(),'Open the matching original blend first'
    rig_path=MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'
    model=json.loads(rig_path.read_text())
    armature=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    armature.animation_data_create()
    for track in armature.animation_data.nla_tracks:track.mute=True
    rest={b.name:[list(v)for v in b.matrix_local]for b in armature.data.bones}
    inventory={'source':str(source/'source.blend'),'sourceSha256':before,'blender':bpy.app.version_string,'armature':armature.name,
        'objectMatrix':[list(v)for v in armature.matrix_world],'boneCount':len(rest),
        'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'restMatrix':rest[b.name]}for b in armature.data.bones],
        'actions':[{'name':a.name,'range':list(a.frame_range),'slots':[{'identifier':s.identifier,'target':s.target_id_type}for s in a.slots]}for a in bpy.data.actions]}
    payload=[];records=[];summary=[]
    for name,(tag,loop)in selected.items():
        action=next(a for a in bpy.data.actions if tag in a.name)
        armature.animation_data.action=action
        if action.slots:armature.animation_data.action_slot=action.slots[0]
        start,end=map(float,action.frame_range);source_length=(end-start)/30
        length=2.0 if loop else source_length
        times=[i/60 for i in range(math.floor(length*60+1e-8)+1)]
        if abs(times[-1]-length)>1e-8:times.append(length)
        frames=[];previous=None
        for t in times:
            frame=start if loop else start+t*30
            bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame))
            evaluated=armature.evaluated_get(bpy.context.evaluated_depsgraph_get())
            matrices={b.name:[list(v)for v in b.matrix]for b in evaluated.pose.bones}
            p=motion.continuous(stable_pose(model,matrices,rest),previous);previous=p
            # No source translation is applied to the logical player. Shadowshot
            # already has a separately owned runtime lift/release contract.
            root=h15.floor_y(model,p)
            frames.append({'seconds':t,'sourceFrame':frame,'matrices':matrices,'targetPose':p,'rootY':root})
        clip,largest=make_clip(model,name,tag,frames,length,loop,source_length)
        payload.append(clip)
        records.append({'name':name,'tag':tag,'sourceLength':source_length,'length':length,'loop':loop,'frames':frames})
        summary.append({'name':name,'tag':tag,'action':action.name,'slot':action.slots[0].identifier if action.slots else None,
            'sourceFrameRange':[start,end],'sourceSeconds':source_length,'clipSeconds':length,'samples':len(frames),'sourceSinglePoseHold':loop,'clipLoop':'once',
            'holdPolicy':'one original source frame held for explicitly authored 2.0s once visual hold (max configured40tick charge support); no original duration claim'if loop else None,
            'largestLocalQuaternionStep':largest,'endpointPolicy':'literal source evaluated endpoint; no neutral envelope or PHASES retiming',
            'contactPolicy':'source release/impact event semantics unknown; keep existing gameplay contact; provisional visual mapping'})
    output=out/'super_motion_w332.animation.json';output.write_bytes(encode({'schema_version':1,'animations':payload}))
    (out/'blend-inspection.json').write_bytes(encode(inventory))
    (out/'evaluated-poses.json.gz').write_bytes(gzip.compress(encode(records),mtime=0))
    source_clips=json.loads((source/'clips.json').read_text())
    manifest={'status':'source visual candidate, parent native acceptance pending','sourceGroup':group,'sourceDirectory':str(source),
        'originalsReadOnly':True,'sourceFiles':{n:sha(source/n)for n in ['source.blend','clips.json','CLIPS.md','inspection.json']},
        'blender':bpy.app.version_string,'directEvaluation':True,'sampleHz':60,'targetRig':str(rig_path),'targetRigSha256':sha(rig_path),
        'rigGeometryChanged':False,'retargetHelper':{'path':'scripts/art/w330_spectral_blades.py','sha256':sha(MAIN/'scripts/art/w330_spectral_blades.py'),'modified':False},
        'coordinateBasis':C,'rotationConvention':'target Blockbench Rz*Ry*Rx; destiny_quaternion x,y,z,w before MC sign conversion; hemisphere continuous',
        'retarget':'existing16bone rig; independent source pelvis/waist/chest/head rotations; anatomical leg flex; source joint-quaternion transported bind bend planes avoid near-extension IK pole flips; reach-limited two-link arms; each source wrist rotation restored after IK; existing item pivots',
        'sourceLayerPolicy':'Nova charge sources are Additive layer; original runtime base-layer weights/state mixing are not decoded. This is directly evaluated source-derived standalone visual adaptation, not a claim of original game layer reconstruction.',
        'translation':'in place; zero horizontal root; target skin floor correction only; runtime ShadowshotLift/entity movement remains authoritative',
        'timing':'complete original30fps action span; resample60Hz + exact endpoint; no time compression/forced neutral; entry1/exit2 independent from W332 display interpolation2',
        'gameplay':'no release/impact event decoded; current release/contact/charge/recovery must be preserved by runtime integration; visual source mapping provisional',
        'clips':summary,'events':[c for c in source_clips if c['tag']in {t for t,l in selected.values()}],
        'missingPhases':'No charge-enter or separate air charge-exit in Nova Warp supplied group; no fabricated phase',
        'nativeQueue':['Shadowshot ground/air bow grip+nock/cheek/aim/release7tick and full1.3s recovery','Nova Warp hold->existing12tick blast->full charge_exit, new input after existing6tick recovery may blend-interrupt the visual','No detached held item, arm flip, skin overlap, neutral snap, or stale phase after cancellation']}
    if args.group=='daybreak':
        manifest['sourceLayerPolicy']='Selected air cast is Base layer, directly evaluated; no new attack/dodge phase or original game state-machine claim.'
        manifest['missingPhases']='This follow-up adds only original Daybreak air cast80A8A973; existing Shadowshot/Nova resources remain unchanged.'
        manifest['nativeQueue']=['Air activation selects w229_warlock_solar_start_air; preserve full1.566667s original action with entry1/exit2','Inspect sword hand grip, hip/chest rotation, original wrist roll and recovery to existing air carry','Ground cast/attack/dodge/gameplay timings remain outside this source-only delta']
    (out/'manifest.json').write_bytes(encode(manifest))
    review(out,args.group,model,records)
    assert sha(source/'source.blend')==before,'Original source drift'
    print(json.dumps({'group':group,'output':str(output),'sha256':sha(output),'clips':summary},indent=2),flush=True)


if __name__=='__main__':main()
