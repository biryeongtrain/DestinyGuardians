"""Evaluate the supplied .blend in an owned headless Blender process, retarget on the unchanged H15 rig.

Blender --background --factory-startup --disable-autoexec SOURCE.blend --python THIS.py --
  --repo-root READONLY_CURRENT_MAIN --output OWNED_NEW_ART_DIRECTORY
No source blend, installed model, shared animation resource or runtime code is written.
"""
import argparse, copy, gzip, hashlib, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
import bpy
from mathutils import Matrix, Vector, Quaternion

TAGS = {
    'h15_super_arc_start': '80A8A922',
    'h15_super_arc_start_air': '80A8A95C',
    'h15_super_arc_attack': '80A8A937',
    'h15_super_arc_attack_weak_2': '80A8A92A',
    'h15_super_arc_attack_weak_3': '80A8A92B',
    'h15_super_arc_attack_air': '80A8A92D',
}
DODGE_TAGS = {
    'h15_super_arc_dodge_forward': '80A8A938',
    'h15_super_arc_dodge_backward': '80A8A93C',
    'h15_super_arc_dodge_left': '80A8A93E',
    'h15_super_arc_dodge_right': '80A8A93F',
}
CONTACTS = {'80A8A937': 10/30, '80A8A92A': 8/30, '80A8A92B': 8/30, '80A8A92D': 8/30}
REPO = None

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def vec(v): return [float(x) for x in v]
def mat(m): return [vec(row) for row in m]
def euler(m): return [math.degrees(x) for x in Matrix(m).to_euler('XYZ')]
def rigid(m):
    q = Matrix(m).to_quaternion(); q.normalize()
    return q.to_matrix().to_4x4()
def axis(m): return rigid(m)
def write_json(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def sample(rig, action, selected, rate=60):
    rig.animation_data_create(); rig.animation_data.action = action
    if action.slots: rig.animation_data.action_slot = action.slots[0]
    start, end = map(float, action.frame_range)
    times = [i/rate for i in range(int(round((end-start)/30*rate))+1)]
    result = []
    for t in times:
        frame = start+t*30
        bpy.context.scene.frame_set(int(math.floor(frame)), subframe=frame%1)
        bpy.context.view_layer.update()
        evaluated = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        result.append({'seconds': round(t,9), 'source_frame': round(frame,6),
                       'matrices': {n: mat(evaluated.pose.bones[n].matrix) for n in selected}})
    return result

def main(args):
    global REPO
    if not bpy.app.background: raise RuntimeError('Use a separate background Blender process, never the user scene')
    REPO = Path(args.repo_root).resolve(); out = Path(args.output).resolve(); out.mkdir(parents=True, exist_ok=True)
    source = Path(bpy.data.filepath).resolve(); src = source.parent
    expected = ['source.blend','clips.json','CLIPS.md','playback-samples.json','hunter_arc_staff.fbx']
    hashes = {str(src/n): digest(src/n) for n in expected}
    ref_path = REPO/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'
    resource_path = REPO/'src/main/resources/destiny/animation/hunter_w199.animation.json'
    hashes[str(ref_path)] = digest(ref_path); hashes[str(resource_path)] = digest(resource_path)
    sys.path.insert(0, str(REPO/'scripts'))
    import build_hunter_animation_h15 as h15
    import build_hunter_animation_h19 as h19
    import build_hunter_animation_h20 as h20
    import build_hunter_source_w197 as old
    # Existing geometric IK keeps its double-precision analytic Euler conversion.
    # Quaternion export below handles representation continuity independently.
    model = json.loads(ref_path.read_text())
    ready, _ = h19.sample(next(c for c in model['animations'] if c['name']=='h15_super_arc'), 0)
    accepted = h19.fk(model, ready); groups = {g['name']: g for g in model['groups']}
    C = Matrix(old.C); Ci = C.inverted()
    rigs = [o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    if len(rigs)!=1: raise ValueError('Ambiguous source armature')
    rig = rigs[0]
    if rig.constraints or rig.animation_data and rig.animation_data.drivers: raise ValueError('Unexpected source drivers/constraints')
    selected = sorted(set(old.MAP.values()) | set(old.EXTRA) | {'6B138432','9D7EE73A'})
    actions = {a.name.split('|')[1]: a for a in bpy.data.actions if len(a.name.split('|'))>=3}
    exportTags=DODGE_TAGS if args.append_dodges else TAGS
    samples = {tag: sample(rig, actions[tag], selected) for tag in dict.fromkeys([*exportTags.values(),'80A8A922'])}
    reference = samples['80A8A922'][-1]['matrices']
    refs = {n: Matrix(m) for n,m in reference.items()}
    def point(m): return Vector((m[0][3],m[1][3],m[2][3]))
    def target_points(matrices): return {n: vec(C.to_3x3()@point(m)) for n,m in matrices.items()}
    refpoints = target_points(reference)
    refGrip = Vector(refpoints['8C83CB67'])-Vector(refpoints['DE9D6BEA'])
    refGripLength = refGrip.length; refGripAxis = refGrip.normalized()
    referenceFloor = min(reference[n][2][3] for n in ['6B138432','9D7EE73A'])
    legLength = (Vector(refpoints['9F0FD28C'])-Vector(refpoints['8BD44A3F'])).length + (Vector(refpoints['8BD44A3F'])-Vector(refpoints['B9B9E05D'])).length
    liftScale = 11.125/legLength
    bones = [{'name':b.name,'parent':b.parent.name if b.parent else None,'head':vec(b.head_local),
              'rest_matrix':mat(b.matrix_local)} for b in rig.data.bones]
    def world_delta(current, name): return C@axis(current[name])@axis(refs[name]).inverted()@Ci
    def mix_pose(a,b,w):
        result = copy.deepcopy(a)
        for n in a:
            qa = Matrix(h15.rot(a[n])).to_quaternion(); qb = Matrix(h15.rot(b[n])).to_quaternion()
            if qa.dot(qb)<0: qb.negate()
            result[n] = euler(qa.slerp(qb,w).to_matrix().to_4x4())
        return result
    def frame_from_xy(x,y):
        y=Vector(y).normalized();x=Vector(x);x=(x-y*x.dot(y)).normalized();z=x.cross(y).normalized();x=y.cross(z).normalized()
        return Matrix((x,y,z)).transposed().to_4x4()
    sourceGripFrame=frame_from_xy((C@axis(refs['DE9D6BEA'])).to_3x3()@Vector((1,0,0)),refGripAxis)
    previousPole={}
    def evaluate(row):
        current = {n:Matrix(m) for n,m in row['matrices'].items()}; points = target_points(row['matrices'])
        pt=lambda n:Vector(points[n])
        p = copy.deepcopy(ready); desired_world={}
        hipX=pt('9F0FD28C')-pt('695DAF09');shoulderX=pt('17025F50')-pt('D1232BA2')
        desired_world['phip_hip']=frame_from_xy(hipX,pt('A252A6A2')-pt('C7C0BA6E'))
        desired_world['pw_waist']=frame_from_xy(shoulderX,pt('A352A6A2')-pt('A252A6A2'))
        desired_world['pc_chest']=frame_from_xy(shoulderX,pt('0D4EBB10')-pt('A352A6A2'))
        desired_world['h_ph_head']=C@axis(current['7E92D640'])@axis(rig.data.bones['7E92D640'].matrix_local).inverted()@Ci
        for upper, lower, chain in [('prl_right_leg','prfl_right_foreleg',['9F0FD28C','8BD44A3F','B9B9E05D']),('pll_left_leg','plfl_left_foreleg',['695DAF09','35B14D1B','0F8B505D'])]:
            rf,rbend=old.leg_frame(refpoints,chain)
            down=(pt(chain[1])-pt(chain[0])).normalized(); lowerDown=(pt(chain[2])-pt(chain[1])).normalized()
            # The evaluated upper-leg quaternion transports its pole through a straight knee. A raw cross product flips at extension.
            pole=(world_delta(current,chain[0])@Matrix(rf)).to_3x3()@Vector((1,0,0))
            upperFrame=frame_from_xy(pole,-down)
            bend=math.degrees(math.acos(max(-1,min(1,down.dot(lowerDown)))))
            desired_world[upper]=upperFrame
            desired_world[lower]=upperFrame@Matrix(h15.rot([min(155,bend),0,0]))
        for target in ['phip_hip','pw_waist','pc_chest','h_ph_head','prl_right_leg','prfl_right_foreleg','pll_left_leg','plfl_left_foreleg']:
            actual = h19.fk(model,p)[target]
            local = Matrix(h15.rot(h19.add(groups[target].get('rotation',[0,0,0]),p[target])))
            parent = axis(actual)@local.inverted()
            p[target] = h19.sub(euler(parent.inverted()@desired_world[target]),groups[target].get('rotation',[0,0,0]))
        # Match original shoulder-elbow-wrist directions on the unchanged Minecraft limb proportions.
        for side,upper,chain in [('right','pra_right_arm',['17025F50','A3781DCD','DE9D6BEA']),('left','pla_left_arm',['D1232BA2','897A1504','8C83CB67'])]:
            u=(pt(chain[1])-pt(chain[0])).normalized(); v=(pt(chain[2])-pt(chain[1])).normalized()
            shoulder=Vector(h19.point(h19.fk(model,p)[upper],[0,0,0]));offset=u*5.5+v*5.66
            if offset.length>10.9:offset=offset.normalized()*10.9
            direction=offset.normalized();pole=u-direction*u.dot(direction)
            oldPole=previousPole.get(side)
            if oldPole is not None:
                oldPole=oldPole-direction*oldPole.dot(direction)
                if oldPole.length>.001:
                    oldPole.normalize()
                    if pole.length<.12:pole=oldPole
                    else:
                        pole.normalize();angle=oldPole.angle(pole)
                        limit=math.radians(35 if pole.length<.3 else 70)
                        if angle>limit:pole=Quaternion(oldPole.cross(pole).normalized(),limit)@oldPole if oldPole.cross(pole).length>.001 else oldPole
            if pole.length<.001:pole=Vector((1 if side=='right' else -1,0,.2))
            pole.normalize();previousPole[side]=pole.copy()
            h19.solve_arm(model,p,side,vec(shoulder+offset),vec(pole))
        item = world_delta(current,'DE9D6BEA')@sourceGripFrame
        delta = world_delta(current,'DE9D6BEA').to_3x3()
        sourceAxis = (delta@refGripAxis).normalized()
        separation = Vector(points['8C83CB67'])-Vector(points['DE9D6BEA'])
        axial = separation.dot(sourceAxis); radial = (separation-sourceAxis*axial).length
        offset = axial/refGripLength*6
        # Follow source one-hand releases; only adapt the left wrist to the shaft while source geometry actually grips it.
        weight = max(0,min(1,(.12-radial)/.08)) if .5<offset<11 else 0
        weight = weight*weight*(3-2*weight)
        correction = 0
        if weight>0:
            held = copy.deepcopy(p); matrices = h19.fk(model,held)
            wrist = Vector(h19.point(matrices['pri_right_item'],[0,0,0])); original = wrist.copy()
            handOffset = item.to_3x3()@Vector((0,offset,0))
            centers = [Vector(h19.point(matrices['pra_right_arm'],[0,0,0])),Vector(h19.point(matrices['pla_left_arm'],[0,0,0]))-handOffset]
            for _ in range(32):
                for center in centers:
                    d = wrist-center
                    if d.length>10.9: wrist = center+d.normalized()*10.9
            for side,upper,fore,end in [('right','pra_right_arm','prfa_right_forearm',wrist),('left','pla_left_arm','plfa_left_forearm',wrist+handOffset)]:
                bias = h19.sub(h19.point(matrices[fore],[0,0,0]),h19.point(matrices[upper],[0,0,0]))
                along = h19.unit(h19.sub(vec(end),h19.point(matrices[upper],[0,0,0])))
                if h19.norm(h19.sub(bias,h19.mul(along,h19.dot(bias,along))))<.01: bias=[1 if side=='right' else -1,-1,.2]
                h19.solve_arm(model,held,side,vec(end),bias)
            p = mix_pose(p,held,weight); correction=(wrist-original).length*weight
        h20.aim_right(model,p,mat(item))
        headCorrection=0;headRemaining=False
        sourceFloor = min(row['matrices'][n][2][3] for n in ['6B138432','9D7EE73A'])
        lift = max(0,sourceFloor-referenceFloor)*liftScale
        rootY = h15.floor_y(model,p)+lift
        return p,rootY,{'grip_weight':weight,'source_grip_radial_m':radial,'grip_offset_units':offset,'reach_correction_units':correction,'source_lift_units':lift,'head_clearance_correction_units':headCorrection,'head_overlap_remaining':headRemaining}
    def continuous_clearance(frames):
        # Choose a smooth correction path only inside local overlap windows with three-pose entry/exit shoulders.
        geom=[]
        def overlaps(g,translation):
            head,inv,wrist,shaft,_,_,_=g;w=inv@(wrist+translation);v=inv.to_3x3()@shaft;lo,hi=-12.0,18.0
            for j in range(3):
                mn=(-4.05,.0-.3,-4.05)[j];mx=(4.05,7.8,4.05)[j]
                if abs(v[j])<1e-8:
                    if w[j]<mn or w[j]>mx:return False
                else:
                    a,b=sorted(((mn-w[j])/v[j],(mx-w[j])/v[j]));lo=max(lo,a);hi=min(hi,b)
            return lo<=hi
        for pose,rootY,metrics in frames:
            fk=h19.fk(model,pose);head=Matrix(fk['h_ph_head']);w=Vector(h19.point(fk['pri_right_item'],[0,0,0]));shaft=Matrix(fk['pri_right_item']).to_3x3()@Vector((0,1,0))
            centers=[Vector(h19.point(fk['pra_right_arm'],[0,0,0]))-w]
            if metrics['grip_weight']>.9:centers.append(Vector(h19.point(fk['pla_left_arm'],[0,0,0]))-Vector(h19.point(fk['pli_left_item'],[0,0,0])))
            geom.append((head,head.inverted(),w,shaft,centers,fk,Matrix(fk['pc_chest']).to_3x3()))
        active=[i for i,g in enumerate(geom) if overlaps(g,Vector((0,0,0)))];windows=[]
        for i in active:
            a=max(0,i-3);b=min(len(frames)-1,i+3)
            if windows and a<=windows[-1][1]+1:windows[-1][1]=max(windows[-1][1],b)
            else:windows.append([a,b])
        translations=[Vector((0,0,0)) for _ in frames]
        import numpy as np
        directions=[Vector(v).normalized() for v in [(x,y,z) for x in (-1,0,1) for y in (-1,0,1) for z in (-1,0,1) if x or y or z]]
        for i in range(72):
            y=1-2*(i+.5)/72;r=math.sqrt(1-y*y);angle=i*math.pi*(3-math.sqrt(5));directions.append(Vector((r*math.cos(angle),y,r*math.sin(angle))))
        # Only each overlap run and its three neighboring poses participate. Discrete local continuity, no source motion retime.
        candidates=[Vector((0,0,0))]+[n*r for r in [.625,1.25,1.875,2.5,3.125,3.75,4.375,5.0] for n in directions]
        coords=np.array([vec(v) for v in candidates],dtype=np.float64);radii=np.linalg.norm(coords,axis=1)
        changes=np.sum((coords[:,None,:]-coords[None,:,:])**2,axis=2);transition=changes.copy();transition[changes>1.75**2]=np.inf
        for start,end in windows:
            costs=np.full(len(candidates),np.inf);costs[radii<=1.75]=radii[radii<=1.75]**2 if start else radii[radii<=1.75]*.01
            if start==0:costs=radii*.01
            histories=[]
            for i in range(start,end+1):
                g=geom[i];valid=np.array([not overlaps(g,v) and all((v-center).length<=10.9 for center in g[4]) for v in candidates])
                if i==start:
                    costs+=radii*.04;costs[~valid]=np.inf;histories.append(None);continue
                total=costs[:,None]+transition;previous=np.argmin(total,axis=0);costs=total[previous,np.arange(len(candidates))]+radii*.04;costs[~valid]=np.inf;histories.append(previous)
            if end<len(frames)-1:costs[radii>1.75]=np.inf
            choice=int(np.argmin(costs))
            if not np.isfinite(costs[choice]):raise RuntimeError('No local continuous clearance path '+str((start,end)))
            for i in range(end,start-1,-1):
                translations[i]=candidates[choice].copy()
                if i>start:choice=int(histories[i-start][choice])
        for i,(pose,rootY,metrics) in enumerate(frames):
            delta=translations[i];metrics['head_clearance_correction_units']=delta.length
            metrics['head_overlap_remaining']=overlaps(geom[i],delta)
            if delta.length<1e-7:continue
            fk=geom[i][5];desiredItem=Matrix(fk['pri_right_item'])
            for side,upper,fore,itemName in [('right','pra_right_arm','prfa_right_forearm','pri_right_item'),('left','pla_left_arm','plfa_left_forearm','pli_left_item')]:
                if side=='left' and metrics['grip_weight']<=.9:continue
                wrist=Vector(h19.point(fk[itemName],[0,0,0]));bias=h19.sub(h19.point(fk[fore],[0,0,0]),h19.point(fk[upper],[0,0,0]))
                h19.solve_arm(model,pose,side,vec(wrist+delta),bias)
            h20.aim_right(model,pose,mat(desiredItem))
        return frames
    clips=[]; audit=[]; preview={}
    for name,tag in exportTags.items():
        rows=samples[tag]; previousPole.clear(); frames=continuous_clearance([evaluate(row) for row in rows]); length=rows[-1]['seconds']
        animators={}; maxEuler=0; maxQuat=0
        for bone in ready:
            keys=[]; previousEuler=None; previousQ=None
            for row,(pose,rootY,metrics) in zip(rows,frames):
                rotation=pose[bone]
                if previousEuler is not None:
                    candidates=[]
                    for v in [rotation,[rotation[0]+180,180-rotation[1],rotation[2]+180]]:
                        candidates.append([a+360*round((b-a)/360) for a,b in zip(v,previousEuler)])
                    rotation=min(candidates,key=lambda v:sum((a-b)**2 for a,b in zip(v,previousEuler)))
                    maxEuler=max(maxEuler,max(abs(a-b) for a,b in zip(rotation,previousEuler)))
                q=Matrix(h15.rot(rotation)).to_quaternion();q.normalize()
                if previousQ is not None:
                    if q.dot(previousQ)<0:q.negate()
                    maxQuat=max(maxQuat,math.degrees(previousQ.rotation_difference(q).angle))
                previousEuler=rotation;previousQ=q.copy()
                key={'channel':'rotation','time':row['seconds'],'interpolation':'linear','uuid':h15.uid('w330/'+name+'/'+bone+'/'+str(row['seconds'])),
                     'data_points':[dict(zip('xyz',[round(v,7) for v in rotation]))],
                     'destiny_quaternion':[round(q.x,10),round(q.y,10),round(q.z,10),round(q.w,10)]}
                keys.append(key)
                if bone=='player_root': keys.append({'channel':'position','time':row['seconds'],'interpolation':'linear','uuid':h15.uid('w330/'+name+'/root/'+str(row['seconds'])),'data_points':[{'x':0,'y':round(rootY,7),'z':0}]})
            if bone in ['pri_right_item','pli_left_item']:
                for time in [0,length]:keys.append({'channel':'scale','time':time,'interpolation':'linear','uuid':h15.uid('w330/'+name+'/'+bone+'/scale/'+str(time)),'data_points':[dict.fromkeys('xyz',1)]})
            animators[groups[bone]['uuid']]={'name':bone,'type':'bone','keyframes':keys}
        clip={'name':name,'uuid':h15.uid('w330/'+name),'length':length,'loop':'once','snapping':60,
              'destiny_quaternion_sampling':True,'destiny_entry_blend_ticks':1,'destiny_exit_blend_ticks':2,'animators':animators}
        if tag in CONTACTS:clip.update(destiny_contact_seconds=CONTACTS[tag],destiny_recovery_seconds=length,destiny_contact_provisional=True)
        if args.append_dodges:clip['destiny_recovery_seconds']=length
        clips.append(clip)
        speeds=[]
        for a,b in zip(rows,rows[1:]):
            pa=Vector(target_points(a['matrices'])['DE9D6BEA']);pb=Vector(target_points(b['matrices'])['DE9D6BEA'])
            speeds.append((b['seconds'],(pb-pa).length/(b['seconds']-a['seconds'])))
        peak=max(speeds,key=lambda v:v[1])
        audit.append({'clip':name,'source_tag':tag,'action':actions[tag].name,'slot':actions[tag].slots[0].identifier,'source_frames':list(actions[tag].frame_range),
                      'length_seconds':length,'keys_per_rotation':len(rows),'max_adjacent_euler_degrees':maxEuler,'max_adjacent_quaternion_degrees':maxQuat,
                      'right_hand_peak_speed_time':peak[0],'right_hand_peak_speed_m_s':peak[1],
                      'provisional_contact_seconds':CONTACTS.get(tag),'contact_note':'Provisional geometric first-swing beat, not decoded damage. weak2 .266667 uses first fast sweep; opaque event .733333 remains unclassified.',
                      'head_clearance_corrected_frames':sum(f[2]['head_clearance_correction_units']>.001 for f in frames),'max_head_clearance_correction_units':max(f[2]['head_clearance_correction_units'] for f in frames),'head_overlap_remaining_frames':[rows[i]['seconds'] for i,f in enumerate(frames) if f[2]['head_overlap_remaining']],
                      'max_source_lift_units':max(f[2]['source_lift_units'] for f in frames),
                      'max_reach_correction_units':max(f[2]['reach_correction_units'] for f in frames),
                      'source_two_hand_frames':sum(f[2]['grip_weight']>.9 for f in frames),
                      'start_wrist':vec(h19.point(h19.fk(model,frames[0][0],frames[0][1])['pri_right_item'],[0,0,0])),
                      'end_wrist':vec(h19.point(h19.fk(model,frames[-1][0],frames[-1][1])['pri_right_item'],[0,0,0]))})
        if args.append_dodges:
            positions=[Vector(target_points(row['matrices'])['1A5C68E5']) for row in rows]
            pelvis=[Vector(target_points(row['matrices'])['C7C0BA6E']) for row in rows]
            velocities=[((b-a).length*60,rows[i+1]['seconds']) for i,(a,b) in enumerate(zip(positions,positions[1:]))]
            peak=max(v[0] for v in velocities)
            moving=[time for speed,time in velocities if speed>max(.03,peak*.1)]
            if moving:
                clip['destiny_motion_start_seconds']=max(0,moving[0]-1/60)
                clip['destiny_motion_end_seconds']=moving[-1]
                clip['destiny_motion_provisional']=True
            audit[-1]['source_pedestal_delta_target_basis']=vec(positions[-1]-positions[0])
            audit[-1]['source_pelvis_delta_target_basis']=vec(pelvis[-1]-pelvis[0])
            audit[-1]['source_pedestal_xz_extent']=[[min(v[j] for v in positions),max(v[j] for v in positions)] for j in [0,2]]
            audit[-1]['source_pelvis_xz_extent']=[[min(v[j] for v in pelvis),max(v[j] for v in pelvis)] for j in [0,2]]
            audit[-1]['motion_cue_note']='Provisional 10%-of-peak evaluated pedestal translation speed, not a decoded gameplay event.'
            audit[-1]['motion_start_seconds']=clip.get('destiny_motion_start_seconds')
            audit[-1]['motion_end_seconds']=clip.get('destiny_motion_end_seconds')
        preview[name]={'rows':rows,'frames':frames}
    if args.append_dodges:
        path=out/'arc_staff_w330.animation.json';base=json.loads(path.read_text());existing=copy.deepcopy(base['animations'])
        assert not any(c['name'] in exportTags for c in existing),'Dodge clips already exist; use a clean captured baseline'
        base['animations'].extend(clips);write_json(path,base)
        assert json.loads(path.read_text())['animations'][:len(existing)]==existing
        write_json(out/'w331-dodge-manifest.json',{'status':'direct-source candidate awaiting master native dodge acceptance','blender':bpy.app.version_string,
            'source_blend':str(source),'input_sha256':hashes,'fps':30,'sampling_fps':60,'clips':audit,
            'timing':'Original32frames /31intervals at30fps; no retime, entry1/exit2, no generic dodge substitution.',
            'translation':'Source horizontal root is measured for direction provenance, kept visually in place so runtime owns actual dodge movement.',
            'rig_geometry_uv_changed':False,'existing_six_clips_preserved':True,'review':'Single forward source/retarget proxy image; direct depsgraph source action/slot evaluated for all4directions.'})
        write_json(out/'w331-dodge-source-review.json',{'space':'evaluated armature object matrices; read-only .blend, same C basis as W330',
            'actions':[{'tag':tag,'action':actions[tag].name,'slot':actions[tag].slots[0].identifier,'frames':list(actions[tag].frame_range)} for tag in exportTags.values()],
            'representative_samples':{tag:[rows[0],rows[len(rows)//2],rows[-1]] for tag,rows in samples.items() if tag in exportTags.values()}})
        for path,sha in hashes.items():
            if digest(path)!=sha:raise RuntimeError('Read-only source drift: '+path)
        review(out,model,preview,h15,h19,C,refGripAxis,refs,['h15_super_arc_dodge_forward'])
        print('W331_ARC_DODGE_APPENDED',len(clips),out);return
    root={'schema_version':1,'model':'guardian_hunter_w330_arc_candidate','destiny_deploy_swing_seconds':13/30,'animations':clips}
    write_json(out/'arc_staff_w330.animation.json',root)
    write_json(out/'action-audit.json',audit)
    with gzip.open(out/'headless-source-samples.json.gz','wt') as f:json.dump({'space':'evaluated armature object; outer FBX scale retained separately','object_matrix':mat(rig.matrix_world),'bones':bones,'clips':samples},f,separators=(',',':'))
    manifest={'status':'candidate awaiting master first/second native Vision acceptance','blender':bpy.app.version_string,'source_blend':str(source),
              'input_sha256':hashes,'source_fps':30,'sample_fps':60,'target_rig':str(ref_path),'target_groups':len(model['groups']),
              'rig_geometry_uv_changed':False,'head_clearance':'Local overlap runs plus 3-pose shoulders: locally continuous avoidance direction, three-pose entry/exit shoulders and 1.75u/pose vector-step bound. Right wrist/staff and established two-hand grip translate together. Source shaft direction/head rotation/duration unchanged.','basis':old.C,'quaternion_order':'[x,y,z,w], same BB Euler frame; Rz(z)*Ry(y)*Rx(x), intrinsic XYZ; no MC sign conversion',
              'reference_pose':'Source anatomical shoulder/pelvis axes and evaluated joint directions drive the unchanged rig. One shared cast frame44 defines the wrist-to-staff shaft basis; no per-clip end calibration.',
              'timing':'Original action spans preserved, no time compression, no forced first/last neutral pose or authored endpoint envelope. Runtime owns recovery-to-idle blending.',
              'translation':'Horizontal root held in place to avoid duplicate gameplay lunge. Positive source toe lift preserved as visual Y above existing skin-floor correction; no entity movement.',
              'grip':'Arm pole continuity only resolves near-extension IK ambiguity; source wrist rotations retain their rapid twirls. Right item follows source wrist quaternion. Source-driven left releases retained; shaft IK only weighted where source left wrist is near the staff axis. Existing rig pivots/mesh/display contract unchanged.',
              'source_events':json.loads((src/'clips.json').read_text()),'clips':audit}
    for path,sha in hashes.items():
        if digest(path)!=sha:raise RuntimeError('Read-only source drift: '+path)
    write_json(out/'manifest.json',manifest)
    # Representative source/retarget PNGs retain the prior clearance-candidate caption; native QA evaluates this continuity revision.
    print('W330_ARC_EXPORTED',len(clips),out)

def review(out,model,preview,h15,h19,C,refGripAxis,refs,names=None):
    # Explicit source/retarget joint and untextured rig proxies, not game screenshots or original meshes.
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    def material(name,color):
        m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
    cyan=material('source evaluated joints',(.18,.85,.95));gray=material('unchanged skin rig',(.38,.48,.6));orange=material('right arm',(.95,.5,.16));blue=material('left arm',(.2,.6,.95));white=material('labels',(.9,.95,1))
    def segment(a,b,r,matl):
        d=b-a
        if d.length<1e-6:return
        bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=d.length,location=(a+b)/2)
        o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y');o.data.materials.append(matl)
    def text(value,x,z):
        data=bpy.data.curves.new('label','FONT');data.body=value;data.size=.13
        o=bpy.data.objects.new('label',data);bpy.context.collection.objects.link(o);o.location=(x,-.5,z);o.rotation_euler=(math.pi/2,0,0);data.materials.append(white)
    def xyz(p,col,row,scale=1):return Vector((p[0]*scale+col*3.2,p[2]*-scale,p[1]*scale+row*3.15))
    parent={}
    def tree(nodes,group=None):
        for n in nodes:
            if isinstance(n,str):parent[n]=group
            else:tree(n['children'],n['uuid'])
    tree(model['outliner']);groups={g['uuid']:g for g in model['groups']}
    chains=[['C7C0BA6E','A252A6A2','A352A6A2','7E92D640'],['A352A6A2','17025F50','A3781DCD','DE9D6BEA'],['A352A6A2','D1232BA2','897A1504','8C83CB67'],['C7C0BA6E','9F0FD28C','8BD44A3F','B9B9E05D','6B138432'],['C7C0BA6E','695DAF09','35B14D1B','0F8B505D','9D7EE73A']]
    for name in (names or ['h15_super_arc_start','h15_super_arc_attack']):
        for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
        data=preview[name];count=len(data['rows']);indices=[round((count-1)*f) for f in [0,.25,.5,.75,1]]
        for col,i in enumerate(indices):
            row=data['rows'][i];pose,rootY,_=data['frames'][i]
            points={n:C.to_3x3()@Vector((m[0][3],m[1][3],m[2][3])) for n,m in row['matrices'].items()}
            for chain in chains:
                for a,b in zip(chain,chain[1:]):segment(xyz(points[a],col,1),xyz(points[b],col,1),.022,cyan)
            delta=C@axis(row['matrices']['DE9D6BEA'])@axis(refs['DE9D6BEA']).inverted()@C.inverted();shaft=delta.to_3x3()@refGripAxis;w=points['DE9D6BEA']
            segment(xyz(w-shaft*.8,col,1),xyz(w+shaft*1.1,col,1),.026,cyan)
            matrices=h19.fk(model,pose,rootY)
            for element in model['elements']:
                group=groups[parent[element['uuid']]]
                if group['name'] in ['tag_name','shadow']:continue
                matrix=Matrix(matrices[group['name']]);origin=Vector(group['origin'])
                lo,hi=element['from'],element['to'];vertices=[]
                for x,y,z in [(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])]:vertices.append(xyz(matrix@Vector((x-origin.x,y-origin.y,z-origin.z,1)),col,0,1/16))
                mesh=bpy.data.meshes.new('unchanged rig cube');mesh.from_pydata(vertices,[],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(4,0,3,7)])
                obj=bpy.data.objects.new('unchanged rig cube',mesh);bpy.context.collection.objects.link(obj)
                obj.data.materials.append(orange if group['name'].startswith(('pra_','prfa_')) else blue if group['name'].startswith(('pla_','plfa_')) else gray)
            item=Matrix(matrices['pri_right_item']);w=item.translation;shaft=item.to_3x3()@Vector((0,1,0))
            segment(xyz(w-shaft*12,col,0,1/16),xyz(w+shaft*18,col,0,1/16),.026,cyan)
            text('SOURCE .blend joint proxy | '+str(row['seconds'])+'s',col*3.2-1.35,5.5)
            text('RETARGET unchanged rig | '+str(row['seconds'])+'s',col*3.2-1.35,2.35)
        camera_data=bpy.data.cameras.new('owned review camera');camera=bpy.data.objects.new('owned review camera',camera_data);bpy.context.collection.objects.link(camera)
        camera.location=(6.4,-25,2.8);camera.rotation_euler=(Vector((6.4,0,2.8))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=16.6;bpy.context.scene.camera=camera
        scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=2000;scene.render.resolution_y=760;scene.render.resolution_percentage=100
        scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD'
        if scene.world is None: scene.world=bpy.data.worlds.new('owned review world')
        scene.world.color=(.018,.024,.036)
        scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
        scene.render.filepath=str(out/(name+'-source-retarget.png'));bpy.ops.render.render(write_still=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo-root',required=True);parser.add_argument('--output',required=True);parser.add_argument('--append-dodges',action='store_true')
    main(parser.parse_args(sys.argv[sys.argv.index('--')+1:]))
