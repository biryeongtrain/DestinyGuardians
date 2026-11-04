#!/usr/bin/env python3
"""W199 Duke 80A8A53D source body in the existing W169 reload bank.

147 exact W123 solids/UV; authored cylinder/yoke, calibrated evaluated Duke body.
No hands, IK, runtime edits or DCC control. --verify checks deterministic bytes read-only.
"""
import argparse
import copy
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import struct
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
A = Path('src/main/resources/assets/destiny')
ART = Path('art/weapons/w169/duke_mk_44')
KEY = 'weapon_reload_w169_duke_mk_44/duke_mk_44'
SOURCE = A/'models/weapon_surface_w123/duke_mk_44.json'
TWOHAND = A/'models/weapon/hand_cannon/duke_mk_44_twohand.json'
ITEM = A/'items/weapon/duke_mk_44.json'
TEXTURE = A/'textures/item/weapon/w123/duke_mk_44.png'
FP = ('firstperson_righthand', 'firstperson_lefthand')
# Duke is W127 semantic-r3-blue-photo in the W123 namespace (not W129).
# Existing semantic split: fixed shroud/strap/frame versus cylinder/chambers/yoke.
MOVING = tuple(range(78,147))
NAMES = tuple([f'Cylinder_shell_{i}' for i in range(12)] +
              [n for i in range(6) for n in ([f'Chamber_{i}_{j}' for j in range(8)]+[f'Cylinder_web_{i}'])] +
              ['Cylinder_spindle','Yoke_vertical','Yoke_arm'])
FIXED_FRAME = tuple(range(8,19))
FIXED_NAMES = ('Top_strap','Top_crown','Top_chamfer_-1','Slot_shadow_-1',
               'Top_chamfer_1','Slot_shadow_1','Breech_rear','Breech_crown',
               'Cylinder_bottom_rail','Breech_to_grip','Cylinder_front_mount')
GRIP = (8,9.525,7.875)  # Current Grip_palm_wood rotation origin.
HINGE = (8,10.2,5.17)  # Current semantic source's yoke base, never recentered.
SOURCE_SHA256 = '8ce48917d727b8bc444481e8e38b1477db4d4725e8e3621d122708cce0a4fb79'
# W197 calibration math is reused, never its Ace motion dataset.
MOTION = Path('art/weapons/w199/duke-source.json')
BODY_BONE = '4A0810C4'
BASIS = [[0,-1,0],[0,0,1],[-1,0,0]]
SAMPLE_SHA = '4f2651b90fa6ebe1fcf1bd7055d8c2b3589246e3344fee95c2e3b2698e5accc5'
TRACK_SHA = 'e599e57124519e67534f7d80ae66935a6ff12cb6311cf5b76394aa79b5762198'
DATASET_SHA = '7bd6d9e7cd7f6c75bfd576276de8ba864c7e3622eb461d2205db3b3787276c0c'
INTERVALS = 60
SAMPLES = INTERVALS + 1
# Original W169 mechanical swing only; no authored body curve survives.
MECHANICAL_KEYS = ((0.,0),(.10,0),(.24,80),(.34,80),(.49,80),
                   (.60,80),(.70,80),(.82,80),(.92,0),(1.,0))


def encode(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def png(im):
    out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
def add(a,b): return [x+y for x,y in zip(a,b)]
def sub(a,b): return [x-y for x,y in zip(a,b)]
def mul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(m,v): return [sum(m[i][k]*v[k] for k in range(3)) for i in range(3)]
def transpose(m): return list(map(list,zip(*m)))
def xyz(angles):
    x,y,z=map(math.radians,angles);a,b,c,d,e,f=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return [[c*e,-c*f,d],[b*d*e+a*f,-b*d*f+a*e,-b*c],[-a*d*e+b*f,a*d*f+b*e,a*c]]
def euler(m):
    b=math.asin(max(-1.,min(1.,m[0][2])))
    a,c=(math.atan2(-m[1][2],m[2][2]),math.atan2(-m[0][1],m[0][0])) if abs(math.cos(b))>1e-8 else (math.atan2(m[2][1],m[1][1]),0)
    return [round(math.degrees(v),9) for v in (a,b,c)]
def rigid(matrix):
    """Remove only evaluated FBX float drift; reject scale/shear/nonfinite input."""
    if len(matrix) != 4 or any(len(row) != 4 for row in matrix):
        raise ValueError("Expected cumulative 4x4 pose")
    if not all(math.isfinite(v) for row in matrix for v in row):
        raise ValueError("Nonfinite source pose")
    if any(abs(a-b) > 1e-7 for a,b in zip(matrix[3], (0,0,0,1))):
        raise ValueError("Invalid homogeneous source pose")
    r = [row[:3] for row in matrix[:3]]
    gram = mul(transpose(r), r)
    if max(abs(gram[i][j] - (i == j)) for i in range(3) for j in range(3)) > 1e-4:
        raise ValueError("Source pose is not rigid")
    def norm(v):
        n = math.sqrt(sum(x*x for x in v))
        return [x/n for x in v]
    x, y = [row[0] for row in r], [row[1] for row in r]
    x = norm(x)
    dot = sum(a*b for a,b in zip(x,y))
    y = norm(sub(y, [dot*v for v in x]))
    z = [x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0]]
    if sum(z[i]*r[i][2] for i in range(3)) < .999:
        raise ValueError("Reflected source pose")
    return transpose([x,y,z]), [row[3] for row in matrix[:3]]


def quaternion(r):
    """Stable matrix -> unit wxyz, including the source's rotations past 180."""
    tr = sum(r[i][i] for i in range(3))
    if tr > 0:
        t = math.sqrt(tr+1)*2
        q = [t/4, (r[2][1]-r[1][2])/t, (r[0][2]-r[2][0])/t, (r[1][0]-r[0][1])/t]
    else:
        i = max(range(3), key=lambda k:r[k][k]); j=(i+1)%3; k=(i+2)%3
        t = math.sqrt(1+r[i][i]-r[j][j]-r[k][k])*2
        q = [(r[k][j]-r[j][k])/t, 0, 0, 0]
        q[i+1]=t/4; q[j+1]=(r[j][i]+r[i][j])/t; q[k+1]=(r[k][i]+r[i][k])/t
    n = math.sqrt(sum(v*v for v in q))
    return [v/n for v in q]


def slerp(a, b, t):
    dot = sum(x*y for x,y in zip(a,b))
    if dot < 0:
        b = [-v for v in b]; dot = -dot
    dot = max(-1, min(1, dot))
    if dot > .9995:
        q = [x+(y-x)*t for x,y in zip(a,b)]
    else:
        angle = math.acos(dot)
        q = [(math.sin((1-t)*angle)*x+math.sin(t*angle)*y)/math.sin(angle) for x,y in zip(a,b)]
    n = math.sqrt(sum(v*v for v in q))
    w,x,y,z = [v/n for v in q]
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]


def track_sha(data):
    return sha(json.dumps({k:data[k] for k in ("bones","samples")},
                          sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def float32(value):
    """Match Java progress division and Minecraft's float range threshold codec."""
    return struct.unpack('!f',struct.pack('!f',value))[0]


def load_motion(root=ROOT):
    raw=(Path(root)/MOTION).read_bytes()
    if sha(raw)!=DATASET_SHA: raise ValueError('Pinned Duke dataset/provenance drift')
    data=json.loads(raw)
    if (data['group']!='hand_cannon_cedb29ae' or data['bodyBone']!=BODY_BONE
        or data['clip']['tag']!='80A8A53D'
        or data['clip']['action']!='Armature|fp_80A8A53D_reload_full|Base'
        or data['sampleSpace']!='armature_object'
        or data['matrixConvention']!='row_major; column_vectors'
        or data['provenance']['uncompressedSHA256']!=SAMPLE_SHA
        or data['provenance']['sourceMap']['selector']!='64A7DE8C'):
        raise ValueError('Wrong Duke source identity')
    conversion=data['conversion']
    if (conversion['sourceRootToModelBasis']!=BASIS
        or conversion['neutralSourceFrame']!=1
        or conversion['modelUnitsPerSourceUnit']!=32
        or conversion['targetAnchor']!=list(GRIP)):
        raise ValueError('Duke calibration drift')
    if track_sha(data)!=TRACK_SHA or data['provenance']['evaluatedTracksSHA256']!=TRACK_SHA:
        raise ValueError('Duke evaluated tracks drift')
    if len(data['samples'])!=127: raise ValueError('Incomplete Duke timeline')
    for i,f in enumerate(data['samples']):
        if (f['frame']!=i+1 or abs(f['seconds']-i/30)>1e-8
            or set(f['poses'])!=set(data['bones'])):
            raise ValueError('Duke timeline/bone identity mismatch')
        for matrix in f['poses'].values(): rigid(matrix)
    return data


def sample(p,motion=None):
    if not math.isfinite(p) or not 0<=p<=1: raise ValueError(p)
    motion=load_motion() if motion is None else motion
    frames=motion['samples']; n=p*(len(frames)-1)
    i=min(int(n),len(frames)-2); t=n-i
    ra,pa=rigid(frames[i]['poses'][BODY_BONE]); rb,pb=rigid(frames[i+1]['poses'][BODY_BONE])
    r0,p0=rigid(frames[0]['poses'][BODY_BONE])
    r=slerp(quaternion(ra),quaternion(rb),t)
    position=add(pa,[(b-a)*t for a,b in zip(pa,pb)])
    body=mul(BASIS,mul(mul(transpose(r0),r),transpose(BASIS)))
    shift=[32*v for v in vec(BASIS,vec(transpose(r0),sub(position,p0)))]
    if p>.95:
        blend=(p-.95)/.05; blend=blend*blend*(3-2*blend)
        body=slerp(quaternion(body),[1,0,0,0],blend)
        shift=[v*(1-blend) for v in shift]
    if p in (0,1): body,shift=xyz((0,0,0)),[0,0,0]
    for a,b in zip(MECHANICAL_KEYS,MECHANICAL_KEYS[1:]):
        if p<=b[0]:
            t=(p-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return body,shift,[0,0,a[1]+(b[1]-a[1])*t]
    raise ValueError(p)

def pose_display(original,twohand,p,part,grip,motion=None):
    accepted=original if grip=='native' else twohand
    if p in (0,1): return copy.deepcopy(accepted)
    body,shift,cylinder=sample(p,motion)
    component=xyz(cylinder if part=='moving' else (0,0,0))
    h=sub(GRIP,(8,8,8));c=sub(HINGE,(8,8,8))
    # Independent cylinder rotation around its crane, then whole gun around grip.
    local=add(sub(h,vec(body,h)),vec(body,sub(c,vec(component,c))))
    display=copy.deepcopy(accepted)
    for context in FP:
        idle=original[context];base=xyz(idle['rotation']);scale=idle['scale']
        if len(set(scale))!=1: raise ValueError('Rigid motion requires uniform FP scale')
        if twohand[context]['scale']!=scale: raise ValueError('Grip scale mismatch')
        rotation=mul(mul(base,body),component)
        position=add(idle['translation'],vec(base,[scale[0]*v for v in add(local,shift)]))
        if grip=='twohand':
            comp=mul(xyz(twohand[context]['rotation']),transpose(base))
            carrier=sub(twohand[context]['translation'],vec(comp,idle['translation']))
            position=add(vec(comp,position),carrier);rotation=mul(comp,rotation)
        display[context]['rotation']=euler(rotation)
        display[context]['translation']=[round(v,9) for v in position]
    return display

def expected_output_paths():
    paths={A/f'models/{KEY}_{part}.json' for part in ('body','moving')}
    paths.update(A/f'models/{KEY}_{i:02}_{part}_{grip}.json' for i in range(SAMPLES) for part in ('body','moving') for grip in ('native','twohand'))
    return paths|{A/f'items/{KEY}.json',ART/'manifest.json',ART/'comparison.png',ART/'storyboard.png'}

def previews(source,reference,motion):
    """Textured offline diagnostics, never native captures or hand-contact proof."""
    helper=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))
    texture=Image.open(ROOT/TEXTURE).convert('RGBA')
    triangles=[helper['model_triangles']({'part':{'elements':[e]}},texture) for e in source['elements']]
    def posed(p):
        body,shift,cylinder=sample(p,motion);b=np.array(body);c=np.array(xyz(cylinder))
        g=np.array(GRIP);hinge=np.array(HINGE);result=[]
        for i,tris in enumerate(triangles):
            for points,uv,tex,normal in tris:
                points=np.asarray(points);normal=np.asarray(normal)
                if i in MOVING:
                    points=(points-hinge)@c.T+hinge;normal=c@normal
                points=(points-g)@b.T+g+np.array(shift)
                result.append((points,uv,tex,b@normal))
        return result
    poses={p:posed(p) for p in (0,.35,.70,.85,1)}
    allpoints=np.concatenate([t[0] for ts in poses.values() for t in ts])
    def render_pose(p,cam,w,hgt):
        ts=poses[p] if p in poses else posed(p)
        return helper['render'](ts,cam,helper['frame'](allpoints,cam,w,hgt),(w,hgt))[0]
    sheet=Image.new('RGB',(1440,1050),'#111925');d=ImageDraw.Draw(sheet)
    d.text((14,10),'W199 DUKE 80A8A53D body + authored cylinder | 61 samples | OFFLINE, not native',fill='white')
    for row,cam in enumerate(([1,.1,-.15],[-1,.30,.55],[.35,.30,1])):
        for col,p in enumerate((0,.35,1)):
            sheet.paste(render_pose(p,cam,480,300),(col*480,50+row*330))
            d.text((col*480+12,35+row*330),f'p={p:.2f} / '+('side','rear oblique','grip-facing oblique')[row],fill='white')
    d.text((14,1030),'78 fixed body + 69 moving cylinder/chambers/yoke = 147; fixed frame stays. No hands/IK.',fill='white')
    story=Image.new('RGB',(1600,1440),'#111925');draw=ImageDraw.Draw(story)
    draw.text((12,10),'ACTUAL DUKE MK.44 GAMEPLAY | Rin -oS68Bu_sDs | source seconds | dark/silver footage: motion only',fill='white')
    for i,f in enumerate(reference['frames']):
        im=Image.open(ROOT/f['path']).convert('RGB');im.thumbnail((400,225));x=(i%4)*400;y=40+(i//4)*260
        story.paste(im,(x,y));draw.text((x+8,y+228),f"{f['timestampSeconds']:.3f}s",fill='white')
    draw.text((12,830),'DUKE SOURCE BODY + W169 AUTHORED CYLINDER | W123 paint | source seconds=4.2p; footage above is mechanical reference only',fill='white')
    for i,p in enumerate((0,.15,.35,.70,.85,1)):
        x=(i%3)*533;y=865+(i//3)*280
        story.paste(render_pose(p,[-1,.25,.45],533,250),(x,y));draw.text((x+8,y+250),f'p={p:.2f} / source {4.2*p:.2f}s',fill='white')
    return png(sheet),png(story)

def generate():
    source=json.loads((ROOT/SOURCE).read_bytes());twohand=json.loads((ROOT/TWOHAND).read_bytes())['display'];item=json.loads((ROOT/ITEM).read_bytes())
    if sha((ROOT/SOURCE).read_bytes())!=SOURCE_SHA256: raise ValueError('Current cleaned source drift')
    if len(source['elements'])!=147 or [source['elements'][i]['name'] for i in MOVING]!=list(NAMES) or [source['elements'][i]['name'] for i in FIXED_FRAME]!=list(FIXED_NAMES): raise ValueError('W127 cylinder/yoke partition drift')
    design=json.loads((ROOT/'art/weapons/w123/duke_mk_44/design.json').read_bytes())
    if [p['geometry'] for p in design['parts']['body']+design['parts']['cylinder']]!=source['elements']: raise ValueError('Semantic source parts drift')
    ref=json.loads((ROOT/ART/'motion-reference.json').read_bytes())
    if not ref['inspectedActualFrames'] or len(ref['frames'])!=12: raise ValueError('Missing reviewed actual reference')
    for f in ref['frames']:
        if sha((ROOT/f['path']).read_bytes())!=f['sha256']: raise ValueError('Reference drift: '+f['path'])
    motion=load_motion()
    output={}
    def emit(path,v): output[path]=encode(v)
    for part in ('body','moving'):
        geo={k:copy.deepcopy(v) for k,v in source.items() if k!='elements'}
        geo['elements']=[copy.deepcopy(e) for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='moving')]
        emit(A/f'models/{KEY}_{part}.json',geo)
    entries=[]
    for i in range(SAMPLES):
        p=i/INTERVALS
        for part in ('body','moving'):
            for grip in ('native','twohand'):
                emit(A/f'models/{KEY}_{i:02}_{part}_{grip}.json',dict(parent=f'destiny:{KEY}_{part}',display=pose_display(source['display'],twohand,p,part,grip,motion)))
        def composite(grip): return dict(type='minecraft:composite',models=[dict(type='minecraft:model',model=f'destiny:{KEY}_{i:02}_{part}_{grip}') for part in ('body','moving')])
        entries.append(dict(threshold=float32(p),model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,on_true=composite('twohand'),on_false=composite('native'))))
    wrapper=copy.deepcopy(item)
    wrapper['model']=dict(type='minecraft:select',property='minecraft:display_context',cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,entries=entries,fallback=copy.deepcopy(item['model'])))],fallback=copy.deepcopy(item['model']))
    emit(A/f'items/{KEY}.json',wrapper)
    comparison,story=previews(source,ref,motion);output[ART/'comparison.png']=comparison;output[ART/'storyboard.png']=story
    inputs=[Path('art/weapons/w123/duke_mk_44/design.json'),Path('art/weapons/w123/duke_mk_44/manifest.json'),SOURCE,TWOHAND,ITEM,TEXTURE,ART/'motion-reference.json',Path('scripts/generate_reload_w169_duke_mk_44.py'),Path('scripts/generate_surface_w123_hammerhead.py'),MOTION]
    emit(ART/'manifest.json',dict(
        stage='W199',weapon='duke_mk_44',itemModel='destiny:'+KEY,
        ownedFiles=253,generatedFiles=250,packFiles=247,staticParts=2,
        parentDisplayChildren=244,frames=SAMPLES,intervals=INTERVALS,progressFloatIndex=1,gripFlagIndex=0,
        firstPersonContexts=list(FP),sourceElements=147,bodyElements=78,
        movingElements=69,maxAssembledElements=147,elementLimit=1000,
        movingIndices=list(MOVING),movingNames=list(NAMES),
        fixedFrameIndices=list(FIXED_FRAME),
        partitionRationale='Exact existing W127 semantic split: body 0..77 fixed; cylinder shell, six chamber bores/webs, spindle and two yoke links 78..146 move as one attached assembly. Top strap, breech, bottom rail and front mount never join cylinder motion. No geometry/UV/paint edits.',
        sourceGeometryPath=str(SOURCE),sourceGeometryFileSha256=sha((ROOT/SOURCE).read_bytes()),
        sourceElementsAndUVSha256=sha(encode(source['elements'])),
        partElementsAndUVSha256={part:sha(encode([e for i,e in enumerate(source['elements']) if (i in MOVING)==(part=='moving')])) for part in ('body','moving')},
        sourceRevision='W127 semantic-r3-blue-photo clean authored solids in weapon_surface_w123',geometryAndUVPreserved=True,
        hipEndpoints=[0,60],
        fallback='Exact canonical items/weapon/duke_mk_44 graph for non-FP and inactive negative progress; ADS and inspect graph preserved',
        mechanicalKeyframes=MECHANICAL_KEYS,sourceMotionDataset=str(MOTION),bodyMotionTag=motion['clip']['tag'],
        sourceBodyCalibration=motion['conversion'],gripPivot=GRIP,cylinderHinge=HINGE,
        authoredMechanicalPhases={'raiseRoll':[0,.10],'openBesideFrame':[.10,.24],'raiseUpright':[.24,.34],'openHold':[.34,.49],'lowerLoaderContact':[.49,.70],'loaderContactHold':[.70,.82],'closeReseat':[.82,.92],'recover':[.92,1]},
        sourceObservedSeconds=ref['selectedSeconds'],
        timingPolicy='Source seconds = 4.2 * normalized runtime progress. Authored cylinder uses existing W169 phases. Neither source 4.2s nor footage 2.4s overrides gameplay duration/credit/audio.',
        rotationConvention='JOML Rx Ry Rz; R_idle * C * R_neutral^T * R_source * C^T * R_cylinder; cylinder hinge before body grip affine; model-space source translation scaled once in idle basis, then twohand carrier compensation',
        referenceConfidence=ref['referenceConfidence'],reference=ref['url'],
        nativeGameplayVerified=False,handIK=False,extractedAnimation=True,extractedBones=True,
        integration={'replaces':'weapon_reload_w64/duke_mk_44','replacementOnly':True,'expectedExistingRouteCount':14,'addsRoute':False,'masterOwnsRegistryRuntime':True,'masterSelectorIntervals':60,'thresholdEncoding':'IEEE754 float32(i/60); master selector must use 60 intervals and float progress, not the old 20','masterTests':'Update ReloadW169DukeTest endpoints 00/60, 61 entries, 247 pack files; reference hash changes are expected for generated images/manifest only','preserve':'W159 Ace and every other route; no shared runtime changes'},
        nativeQueue=['Both hands/native and twohand: source body framing through 61 poses, muzzle-up visibility, open gap, cylinder/body phase alignment and reseat seams','Inactive/third-person/GUI/ground/fixed/ADS/inspect use canonical graph','Reload cancellation, completion and equip restore with master runtime route swap','Short 10-20 display observation; no performance certification from offline renders'],
        mechanicsOrAudioChanged=False,
        limitations=[
            'Hybrid: evaluated Duke 80A8A53D body with W197 presentation calibration; W169 cylinder/yoke remains authored, source binding unresolved.',
            'Calibration basis/signs, grip attachment, 32 units/source unit and final 5 percent neutral recovery are explicit choices; no camera/contact proof.',
            'Existing dark/silver partial-reload footage is mechanical reference only; not a time-aligned match to the extracted full-reload clip.',
            'No cartridge, loader, hand/IK, base-duration or perk-speed certification. Mechanical/source phase alignment requires master QA.',
        ]+['Cylinder and two existing yoke links travel as one rigid assembly; no additional linkage articulation, cases, rounds or speedloader geometry.','Native framing, closed seams and open clearance require master QA.'],
        sourceSha256={str(p):sha((ROOT/p).read_bytes()) for p in inputs},
        sha256={str(p):sha(b) for p,b in output.items()}))
    if set(output)!=expected_output_paths(): raise ValueError('Output ownership mismatch')
    return output

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    output=generate()
    for p,b in output.items():
        dst=ROOT/p
        if args.verify:
            if not dst.is_file() or dst.read_bytes()!=b: raise SystemExit('Asset differs: '+str(p))
        else: dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
    print(('Verified' if args.verify else 'Generated')+f' {len(output)} deterministic outputs; 247 pack files; 61 samples; 78+69=147 elements')
if __name__=='__main__': main()
