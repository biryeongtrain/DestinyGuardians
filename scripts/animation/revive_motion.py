#!/usr/bin/env python3
"""Evaluate read-only Guardian revive .blend, then retarget to the existing skin limb.
Blender: --background --factory-startup --disable-autoexec --python THIS -- --evaluate --source-root MOTIONS --samples OUT
Python: THIS --root REPO --samples OUT --output-root DELTA [--verify]
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
TAG = '80A8AD85'
NAME = 'h15_revive_combat'
PACK = 'src/main/resources/destiny/animation/revive_combat.animation.json'
REPORT = 'docs/qa/2026-11-03/fireteam-revive/motion/manifest.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, value, verify=False):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if verify: assert p.read_bytes()==raw, ('Reproduction mismatch',str(p))
    else: p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(raw)

def evaluate(args):
    import bpy
    source=args.source_root.resolve(); out=args.samples.resolve()
    assert not out.is_relative_to(source)
    assert bpy.app.background and not bpy.context.preferences.filepaths.use_scripts_auto_execute
    paths=['Guardian_Revive_72bone.blend','Guardian_Revive_72bone.fbx','README.md','samples_20tps/80A8AD85.json','provenance/source-bones.json','provenance/query-clip-links.json']
    hashes={p:sha(source/p) for p in paths}
    bpy.ops.wm.open_mainfile(filepath=str(source/paths[0]),use_scripts=False)
    rigs=[o for o in bpy.data.objects if o.type=='ARMATURE']; assert len(rigs)==1
    rig=rigs[0]; assert len(rig.data.bones)==72
    rig.animation_data_create()
    for track in rig.animation_data.nla_tracks: track.mute=True
    action=next(a for a in bpy.data.actions if TAG in a.name)
    rig.animation_data.action=action
    slots=[s for s in action.slots if s.target_id_type=='OBJECT']; assert len(slots)<=1
    if slots: rig.animation_data.action_slot=slots[0]
    first,last=map(float,action.frame_range); assert last-first==48
    scene=bpy.context.scene; fps=scene.render.fps/scene.render.fps_base; assert fps==30
    bones=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local]} for b in rig.data.bones]
    frames=[]
    for i in range(49):
        scene.frame_set(int(first)+i); bpy.context.view_layer.update()
        ev=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        joints={b.name:[list(r) for r in b.matrix] for b in ev.pose.bones}
        assert all(math.isfinite(v) for m in joints.values() for row in m for v in row)
        frames.append({'frame':int(first)+i,'joints':joints})
    assert hashes=={p:sha(source/p) for p in paths}
    write(out,{'sourceRoot':str(source),'sourceHashes':hashes,'blenderVersion':bpy.app.version_string,'autoexecDisabled':True,'sampleSpace':'armature_object','sourceBlendOpenedDirectly':True,'savedSourceBlend':False,'sourceUnchanged':True,'bones':bones,'actions':[{'name':a.name,'range':list(a.frame_range)} for a in bpy.data.actions],'clip':{'tag':TAG,'action':action.name,'slot':slots[0].identifier if slots else None,'firstFrame':first,'lastFrame':last,'fps':fps,'frames':frames}})
    print('EVALUATED',len(bones),'bones',len(frames),'frames',first,last)

def convert(args):
    root=args.root.resolve(); output=args.output_root.resolve(); data=json.loads(args.samples.read_text()); source=Path(data['sourceRoot'])
    assert not output.is_relative_to(source)
    assert data['sourceUnchanged'] and data['sourceBlendOpenedDirectly'] and data['autoexecDisabled']
    assert data['sourceHashes']=={p:sha(source/p) for p in data['sourceHashes']}
    sys.path[:0]=[str(root/'scripts'),str(root/'scripts/animation')]
    import build_hunter_animation_h15 as h15
    import build_hunter_animation_h19 as h19
    import build_hunter_source_w197 as w197
    import build_crucible_intro_w260 as base
    model_path=root/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'
    model=json.loads(model_path.read_text()); groups={g['name']:g for g in model['groups']}
    base.h15=h15; base.h19=h19; base.w197=w197; base.C=w197.C; base.model=model; base.GROUPS=groups
    old=json.loads((root/'art/weapons/w197/hunter-source-motion.json').read_text())['bones']
    bones={b['name']:b for b in data['bones']}; assert old.keys()==bones.keys()
    difference=max(abs(old[n]['restMatrix'][i][j]-bones[n]['matrix'][i][j]) for n in old for i in range(4) for j in range(4))
    assert difference<1e-5, ('Unexpected source rest rig',difference)
    c=data['clip']; g={'bones':data['bones']}; normals={}; repairs={}
    for chain in [['9F0FD28C','8BD44A3F','B9B9E05D'],['695DAF09','35B14D1B','0F8B505D'],['D1232BA2','897A1504','8C83CB67'],['17025F50','A3781DCD','DE9D6BEA']]:
        normals[chain[0]],repairs[chain[0]]=base.stable_normals(c,chain)
    frames=[(round((f['frame']-c['firstFrame'])/30,9),base.pose(g,f,{n:vs[i] for n,vs in normals.items()})) for i,f in enumerate(c['frames'])]
    base.unwrap(frames)
    # Pin actor X/Z. Preserve source airborne foot clearance separately from the
    # proportion-adapted target knee/hip crouch; source pelvis displacement alone
    # drives short Minecraft limbs below the floor. Feet have no independent rig.
    feet=['0F8B505D','9D7EE73A','B9B9E05D','6B138432']
    source_floor=min(c['frames'][-1]['joints'][n][2][3] for n in feet)
    units=groups['phip_hip']['origin'][1]/bones['C7C0BA6E']['head'][2]
    clearance=[max(0,min(f['joints'][n][2][3] for n in feet)-source_floor)*units for f in c['frames']]
    positions={t:h15.floor_y(model,p)+height for (t,p),height in zip(frames,clearance)}
    clip=h15.clip(model,NAME,frames,root_positions=positions,linear_root=True); clip['snapping']=30
    for animator in clip['animators'].values():
        for key in animator['keyframes']:
            key['interpolation']='linear'
            key['data_points'][0]={n:round(float(v),7) for n,v in key['data_points'][0].items()}
    assert clip['length']==1.6
    assert all(math.isfinite(v) for a in clip['animators'].values() for k in a['keyframes'] for v in k['data_points'][0].values())
    max_step=max(abs(p[n][a]-prev[n][a]) for (_,prev),(_,p) in zip(frames,frames[1:]) for n in p for a in range(3))
    assert max_step<90, ('Euler discontinuity',max_step)
    helpers=['scripts/build_hunter_animation_h15.py','scripts/build_hunter_animation_h19.py','scripts/build_hunter_source_w197.py','scripts/animation/build_crucible_intro_w260.py','art/blockbench/animations/guardian_hunter_w199_r1.bbmodel','art/weapons/w197/hunter-source-motion.json']
    report={'sourceRoot':str(source),'sourceHashes':data['sourceHashes'],'generatorSha256':sha(Path(__file__)),'baselineHashes':{p:sha(root/p) for p in helpers},'evaluation':{k:data[k] for k in ['blenderVersion','sourceBlendOpenedDirectly','savedSourceBlend','autoexecDisabled','sourceUnchanged','actions']},'clip':{'name':NAME,'sourceTag':TAG,'sourceFrames':49,'durationSeconds':1.6,'runtimeTicks':32,'sourceBones':72,'targetAnimatedBones':len(h15.BONES),'targetGroups':len(groups),'maxRestMatrixDifference':difference,'maxAdjacentEulerStepDegrees':max_step,'airborneClearanceModelUnits':[min(clearance),max(clearance)],'collinearRepairs':repairs},'retarget':{'basis':w197.C,'rotation':'Reuse W260 evaluated source/rest torso, limb directions and transported bend-plane IK; same rest rig verified numerically. Keep source timing.','translation':'X/Z fixed at actor anchor. Target lowest skin touches ground plus proportional source minimum ankle/toe clearance above final source floor; maintains airborne descent then proportion-adapted crouch. Runtime owns fixed actor yaw and no view pitch.','limitations':['16 animated rigid skin groups cannot reproduce 72 source bones','No independent clavicle, wrist skin, ankle, toes or finger deformation','No original-game A/B comparison','Generated static FK review is not Minecraft visual acceptance']},'verification':{'reproducible':True,'nativeClient':False,'audioListening':False}}
    write(output/PACK,{'animations':[clip]},args.verify); write(output/REPORT,report,args.verify)
    print('RETARGET',NAME,'49 poses, 1.6s, max Euler step',max_step,'airborne height',max(clearance))
    if not args.verify: review(output,model,clip,c,base,h15,h19,units,source_floor)

def review(output,model,clip,c,base,h15,h19,units,source_floor):
    from PIL import Image,ImageDraw
    groups={g['uuid']:g for g in model['groups']}; elements={e['uuid']:e for e in model['elements']}
    def skin(p,y):
        matrices=h19.fk(model,p,y); faces=[]
        def walk(nodes,parent):
            for node in nodes:
                if isinstance(node,str):
                    e=elements.get(node,{})
                    if e.get('name')!='skin':continue
                    o=parent['origin']; vertices=[h19.point(matrices[parent['name']],[x-o[0],y-o[1],z-o[2]]) for x in (e['from'][0],e['to'][0]) for y in (e['from'][1],e['to'][1]) for z in (e['from'][2],e['to'][2])]
                    for indices in ([0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]):faces.append(([vertices[i] for i in indices],parent['name']))
                else:walk(node['children'],groups[node['uuid']])
        walk(model['outliner'],None); return faces
    times=[0,.2,.4,.6,.8,1.2,1.6]
    for view in ['front','side']:
        im=Image.new('RGB',(1540,700),'#101b28'); draw=ImageDraw.Draw(im)
        draw.text((12,8),'Revive 80A8AD85 | evaluated .blend source / target rigid skin FK | '+view,fill='white')
        for index,t in enumerate(times):
            cx=index*220+110
            def project(v,base_y):return (cx+(v[0]+v[2]*.15 if view=='front' else -v[2]+v[0]*.15)*6,base_y-v[1]*6)
            f=c['frames'][round(t*30)]; points={n:base.convert(base.xyz(m)) for n,m in f['joints'].items()}
            hip=points['C7C0BA6E']; points={n:[(v[0]-hip[0])*units,(v[1]-source_floor)*units,(v[2]-hip[2])*units] for n,v in points.items()}
            draw.text((index*220+12,35),str(t)+'s',fill='white')
            for b in base_source_bones:
                if b['parent'] is not None:draw.line([project(points[b['name']],325),project(points[b['parent']],325)],fill='#f5aa62',width=2)
            p,y=h19.sample(clip,t)
            for verts,n in sorted(skin(p,y),key=lambda f:sum(v[2] if view=='front' else v[0] for v in f[0]),reverse=True):
                draw.polygon([project(v,655) for v in verts],fill='#68bbcf' if 'leg' in n else '#b7d0df',outline='#243d54')
            for ground in (325,655):draw.line([(index*220,ground),((index+1)*220,ground)],fill='#536579')
        draw.text((12,678),'Offline FK comparison only. Actual client camera, equipment and landing still require master QA.',fill='white')
        im.save(output/Path(REPORT).parent/('contact-'+view+'.png'))

def main():
    global base_source_bones
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--evaluate',action='store_true');p.add_argument('--source-root',type=Path);p.add_argument('--samples',required=True,type=Path);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--output-root',type=Path);p.add_argument('--verify',action='store_true')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    if args.evaluate:evaluate(args)
    else:
        if args.output_root is None:args.output_root=args.root
        base_source_bones=json.loads(args.samples.read_text())['bones'];convert(args)
if __name__=='__main__':main()
