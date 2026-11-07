#!/usr/bin/env python3
"""W337 serialized-payload physical grip audit and actual-volume headless review.
Run with Blender --background --factory-startup --python this-file.
Review uses original skin/prop cuboids with diagnostic materials, not native shading.
"""
import json, math, importlib.util, hashlib, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[4]
MAIN=Path('/Users/qf/IdeaProjects/DestinyGuardians')
OUT=Path(__file__).resolve().parent
TEMP=Path('/tmp/w337-maul-grip');TEMP.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('w336_export',ROOT/'scripts/art/w336_class_locomotion.py')
export=importlib.util.module_from_spec(spec);spec.loader.exec_module(export)
m=export.helpers();h=m.h19;w=m.w197
model=export.read(MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel')
mesh_path=MAIN/'src/main/resources/assets/destiny/models/class_ability/titan/burning_maul.json'
mesh=export.read(mesh_path)
resource='art/animation/w336/classes/super_locomotion_classes_w336.animation.json'
before=export.read(MAIN/resource);after=export.read(ROOT/resource)
byname=lambda d:{c['name']:c for c in d['animations']}
b,a=byname(before),byname(after)
names=[n for n in a if n.startswith('w230_titan_burning_maul_')]
assert len(names)==5 and len(a)==31
shaft=next(e for e in mesh['elements']if e.get('name')=='continuous_heavy_shaft')
assert mesh['display']['thirdperson_righthand']=={'rotation':[0,0,0],'translation':[0,2,0],'scale':[1,1,1]}
palms=export.palm_geometry(model)

def frame(clip,t):
    pose={bone:[0,0,0]for bone in m.h15.BONES};positions={};root=0
    for animator in clip['animators'].values():
        for channel,output in [('rotation',pose),('position',positions)]:
            ks=[k for k in animator['keyframes']if k['channel']==channel]
            if not ks:continue
            key=min(ks,key=lambda k:abs(k['time']-t));assert abs(key['time']-t)<1e-7
            output[animator['name']]=[float(key['data_points'][0][axis])for axis in ['x','y','z']]
    root=positions.pop('player_root',[0,0,0])[1]
    return pose,positions,root,m.motion.fk_positions(model,pose,positions,root)

def contact(fk):
    item=fk['pri_right_item'];start=h.point(item,[0,shaft['from'][1]-6,0]);end=h.point(item,[0,shaft['to'][1]-6,0]);segment=h.sub(end,start);length=h.norm(segment);direction=h.unit(segment)
    result=[]
    for name,box in palms.items():
        palm=h.point(fk[name],box['center']);axial=h.dot(h.sub(palm,start),direction)
        radial=h.norm(h.sub(palm,h.add(start,h.mul(direction,axial))))
        inv=h.inverse_rotation(w.rotation(fk[name]));origin=h.point(fk[name],[0,0,0]);p0=h.vector(inv,h.sub(start,origin));p1=h.vector(inv,h.sub(end,origin));lo,hi=0.,1.
        for dim in range(3):
            delta=p1[dim]-p0[dim]
            if abs(delta)<1e-10:
                if not box['min'][dim]<=p0[dim]<=box['max'][dim]:lo,hi=1.,0.
            else:
                t0=(box['min'][dim]-p0[dim])/delta;t1=(box['max'][dim]-p0[dim])/delta
                lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
        result.append({'hand':name,'radialUnits':radial,'gripRawY':shaft['from'][1]+axial,'centerWithinShaft':0<axial<length,'shaftThroughPalmUnits':max(0,hi-lo)*length})
    return result

report={'task':'W337 actual Maul mesh shaft contact','resourceBeforeSha256':export.sha(MAIN/resource),'resourceAfterSha256':export.sha(ROOT/resource),'modelSha256':export.sha(mesh_path),'targetRigSha256':export.sha(MAIN/'art/blockbench/animations/guardian_hunter_w199_r1.bbmodel'),'sourceRevision':'R2','units':'Blockbench model units;16=1 Minecraft block','contactDefinition':'Physical continuous_heavy_shaft centerline intersects actual lower1.5u slab of each forearm skin cuboid. No separate hand/finger bones exist. Includes actual thirdperson+2Y display offset; item-node origin is not a palm.','clips':[],'render':'Actual original nonzero-volume skin and prop cuboids, diagnostic material colors. Not native shading or a live-client acceptance.'}
for name in a:
    if name not in names:assert a[name]==b[name],name
for name in names:
    ac,bc=a[name],b[name]
    assert {k:v for k,v in ac.items()if k!='animators'}=={k:v for k,v in bc.items()if k!='animators'}
    for animatorid,animator in ac['animators'].items():
        if animator['name']not in ['pla_left_arm','plfa_left_forearm','pli_left_item','pra_right_arm','prfa_right_forearm','pri_right_item']:
            assert animator==bc['animators'][animatorid],(name,animator['name'])
    times=sorted({k['time']for an in ac['animators'].values()for k in an['keyframes']})
    old=[];new=[]
    for t in times:
        old.extend(contact(frame(bc,t)[3]));new.extend(contact(frame(ac,t)[3]))
    assert all(x['centerWithinShaft']and x['radialUnits']<1e-6 and x['shaftThroughPalmUnits']>0 for x in new)
    report['clips'].append({'name':name,'periodSeconds':ac['length'],'sampleCount':len(times),'beforeMaxPalmRadialUnits':max(x['radialUnits']for x in old),'afterMaxPalmRadialUnits':max(x['radialUnits']for x in new),'afterMinimumShaftThroughPalmUnits':min(x['shaftThroughPalmUnits']for x in new),'afterGripRawYRange':[min(x['gripRawY']for x in new),max(x['gripRawY']for x in new)],'nonArmChannelsIdentical':True})
# Independently retain exact source-object JSON bytes for all26 other clips.
def rawclips(path):
    text=path.read_text();dec=json.JSONDecoder();offset=text.index('[',text.index('"animations"'))+1;out={}
    while True:
        while text[offset].isspace()or text[offset]==',':offset+=1
        if text[offset]==']':return out
        value,end=dec.raw_decode(text,offset);out[value['name']]=text[offset:end].encode();offset=end
rawb,rawa=rawclips(MAIN/resource),rawclips(ROOT/resource)
assert all(rawa[n]==rawb[n]for n in a if n not in names)
report['other26RawClipObjectsByteIdentical']=True
report['nativeAcceptance']='pending master idle6.87s/4directions/attack/recovery review'
export.write(OUT/'validation.json',report)
print('serialized contact and26rawclip checks PASS',flush=True)

import bpy
from mathutils import Vector
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world.color=(.06,.06,.06)
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.display.shading.show_specular_highlight=True
colors={'body':(.35,.4,.46,1),'right':(.95,.4,.08,1),'left':(.1,.7,.9,1),'shaft':(.24,.15,.08,1),'head':(.95,.65,.1,1)}
materials={}
for n,col in colors.items():
    mat=bpy.data.materials.new(n);mat.diffuse_color=col;materials[n]=mat

def cv(v):return(v[0],-v[2],v[1])
def cuboid(name,lo,hi,transform,material):
    if min(hi[i]-lo[i]for i in range(3))<1e-5:return
    vertices=[cv(transform([x,y,z]))for x,y,z in [(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])]]
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]);data.update();obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.data.materials.append(materials[material]);return obj

def build(fk):
    groups={g['uuid']:g for g in model['groups']};elements={e['uuid']:e for e in model['elements']}
    def walk(nodes,parent=None):
        for node in nodes:
            if isinstance(node,str):
                e=elements[node]
                if e.get('name')!='skin':continue
                bone=parent['name'];origin=parent['origin'];transform=lambda p,bone=bone,origin=origin:h.point(fk[bone],h.sub(p,origin))
                col='left'if bone in ['pla_left_arm','plfa_left_forearm']else'right'if bone in ['pra_right_arm','prfa_right_forearm']else'body'
                cuboid(bone,e['from'],e['to'],transform,col)
            else:walk(node['children'],groups[node['uuid']])
    walk(model['outliner'])
    item=fk['pri_right_item']
    for i,e in enumerate(mesh['elements']):
        rotation=e.get('rotation');origin=rotation.get('origin',[8,8,8])if rotation else[8,8,8]
        angles=[rotation.get(axis,0)for axis in ['x','y','z']]if rotation else[0,0,0]
        if rotation and'axis'in rotation:angles['xyz'.index(rotation['axis'])]=rotation['angle']
        matrix=m.h15.rot(angles)
        def transform(p,matrix=matrix,origin=origin):
            rotated=h.add(h.vector(matrix,h.sub(p,origin)),origin)
            return h.point(item,h.add(h.sub(rotated,[8,8,8]),[0,2,0]))
        cuboid(e.get('name',str(i)),e['from'],e['to'],transform,'shaft'if e['to'][1]<26 else'head')

camdata=bpy.data.cameras.new('review');camera=bpy.data.objects.new('review',camdata);scene.collection.objects.link(camera);scene.camera=camera;camdata.type='ORTHO';camdata.ortho_scale=58
clipname='w230_titan_burning_maul_idle';t=min({k['time']for an in a[clipname]['animators'].values()for k in an['keyframes']},key=lambda t:abs(t-a[clipname]['length']/2))
for label,clip in [('before',b[clipname]),('after',a[clipname])]:
    for obj in list(bpy.data.objects):
        if obj.type=='MESH':bpy.data.objects.remove(obj,do_unlink=True)
    fk=frame(clip,t)[3];build(fk)
    for view,location in [('front',(0,100,24)),('side',(100,0,24))]:
        camera.location=location;target=Vector((0,0,19));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/f'{label}-{view}.png');bpy.ops.render.render(write_still=True)
print('4 physical-volume review renders complete at',t,flush=True)
