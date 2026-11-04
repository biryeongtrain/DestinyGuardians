#!/usr/bin/env python3
"""W91 isolated Izanagi presentation. Stdlib only; --verify writes nothing.

W198 dense bank of W197 source-derived rigid poses; existing runtime timing, no hand IK. Original
79 cubes/474 face UVs/three atlases are retained. No runtime files are edited.
"""
import argparse
import base64
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct
import sys
import uuid

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w91-izanagi'
GENERATOR = ROOT / 'scripts/generate_izanagi_presentation_w91.py'
SOURCE = ROOT / 'art/weapons/w84/model/source/izanagi.bbmodel'
SOURCE_SHA = '9ae28369f80ff0f81bb7e1344ee50b618b9a2de62dcafc631287084dbe3c8f31'
MODEL_DIR = ASSETS / 'models/item/weapon_izanagi_w91'
ITEM = ASSETS / 'items/weapon_izanagi_w91/izanagis_burden.json'
TEXTURE = ASSETS / 'textures/item/weapon_izanagi_w91/charge.png'
KEY = 'item/weapon_izanagi_w91/izanagis_burden'
FP = ('firstperson_righthand', 'firstperson_lefthand')
MAGAZINE = (26,)
BOLT = (25, 77)
PARTS = ('body', 'magazine', 'bolt')
RELOAD_INTERVALS = 60
RELOAD_SAMPLES = RELOAD_INTERVALS + 1
GENERATION_OFFSETS = (0, .00025, .0005)
MOTION = ROOT / 'art/weapons/w197/izanagi-source-motion.json'
DATASET_SHA = '16d333d78c42336e58116519b4fa951c5242326541ae7f5d8c33530fd3796e38'
TAGS = {'ordinary': '80A8A140', 'honed': '80A8A14D'}
BONES = {'body': '4A0810C4', 'magazine': '52EDE88C', 'bolt': '69768858'}
# Root-local forward X -> model -Z, height Z -> +Y, side Y -> +X.
# Reflection is explicit; conjugation still yields proper rigid rotations.
BASIS = [[0,1,0,0], [0,0,1,0], [-1,0,0,0], [0,0,0,1]]
HELPER_PATH = ROOT / 'scripts/art/build_izanagi_w84.py'
H = runpy.run_path(str(HELPER_PATH))
rotate, two_hand_display = H['rotate'], H['two_hand_display']


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def node(key):
    return {'type': 'minecraft:model', 'model': 'destiny:' + key}


def grip(native, twohand):
    return dict(type='minecraft:condition', property='minecraft:custom_model_data',
                index=0, on_false=native, on_true=twohand)


def f32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def selector(frame, start=0, offset=0):
    # Match Java float division, base addition, then generation-offset addition.
    # Rounding start + frame/60 just once can cross a Honed bucket boundary.
    return f32(f32(start + f32(frame / RELOAD_INTERVALS)) + f32(offset))


def identity():
    return [[float(i == j) for j in range(4)] for i in range(4)]


def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def inv(m):
    out = identity()
    for i in range(3):
        for j in range(3): out[i][j] = m[j][i]
        out[i][3] = -sum(m[j][i]*m[j][3] for j in range(3))
    return out


def point(m, p):
    return [sum(m[i][j]*p[j] for j in range(3))+m[i][3] for i in range(3)]


def rigid(m):
    """Remove FBX evaluation's tiny scale/shear by orthonormalizing columns."""
    require(len(m) == 4 and all(len(r) == 4 for r in m), 'Expected 4x4 matrix')
    require(all(math.isfinite(v) for r in m for v in r), 'Nonfinite source matrix')
    require(max(abs(m[3][i]-[0,0,0,1][i]) for i in range(4)) < 1e-6, 'Nonaffine matrix')
    cols = [[m[i][j] for i in range(3)] for j in range(3)]
    dot = lambda a,b: sum(x*y for x,y in zip(a,b))
    def norm(v):
        length=math.sqrt(dot(v,v));require(length>1e-9,'Degenerate source rotation')
        return [x/length for x in v]
    x = norm(cols[0]); y = norm([v-dot(x,cols[1])*u for v,u in zip(cols[1],x)])
    z = [x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0]]
    require(max(abs(cols[j][i]-[x,y,z][j][i]) for i in range(3) for j in range(3)) < .002,
            'Source scale/shear exceeds evaluated numerical tolerance')
    out = identity()
    for i in range(3):
        for j in range(3): out[i][j] = [x,y,z][j][i]
        out[i][3] = m[i][3]
    return out


def quat(m):
    # Stable largest-component extraction, quaternion order wxyz.
    values = [1+m[0][0]+m[1][1]+m[2][2], 1+m[0][0]-m[1][1]-m[2][2],
              1-m[0][0]+m[1][1]-m[2][2], 1-m[0][0]-m[1][1]+m[2][2]]
    i = max(range(4), key=values.__getitem__); v = math.sqrt(max(0,values[i]))/2; d=4*v
    if i == 0: q=[v,(m[2][1]-m[1][2])/d,(m[0][2]-m[2][0])/d,(m[1][0]-m[0][1])/d]
    elif i == 1: q=[(m[2][1]-m[1][2])/d,v,(m[0][1]+m[1][0])/d,(m[0][2]+m[2][0])/d]
    elif i == 2: q=[(m[0][2]-m[2][0])/d,(m[0][1]+m[1][0])/d,v,(m[1][2]+m[2][1])/d]
    else: q=[(m[1][0]-m[0][1])/d,(m[0][2]+m[2][0])/d,(m[1][2]+m[2][1])/d,v]
    n=math.sqrt(sum(v*v for v in q));return [v/n for v in q]


def qmatrix(q, t):
    w,x,y,z=q; out=identity()
    out[:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),t[0]],
             [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),t[1]],
             [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y),t[2]]]
    return out


def interpolate(a,b,t):
    qa,qb=quat(a),quat(b);dot=sum(x*y for x,y in zip(qa,qb))
    if dot < 0: qb=[-x for x in qb];dot=-dot
    if dot > .9995: q=[x+(y-x)*t for x,y in zip(qa,qb)]
    else:
        angle=math.acos(min(1,dot));q=[(x*math.sin((1-t)*angle)+y*math.sin(t*angle))/math.sin(angle) for x,y in zip(qa,qb)]
    n=math.sqrt(sum(v*v for v in q));q=[v/n for v in q]
    return qmatrix(q,[a[i][3]+(b[i][3]-a[i][3])*t for i in range(3)])


def euler(m):
    # Only serialize XYZ after finite matrix composition; never add Euler channels.
    require(abs(m[0][2]) < .9999999, 'Unexpected display gimbal singularity')
    return [math.degrees(v) for v in (math.atan2(-m[1][2],m[2][2]),
             math.asin(max(-1,min(1,m[0][2]))), math.atan2(-m[0][1],m[0][0]))]


def rotation(angles):
    out=identity()
    for j,v in enumerate(([1,0,0],[0,1,0],[0,0,1])):
        for i,x in enumerate(rotate(v,angles)): out[i][j]=x
    return out


def translation(v):
    out=identity()
    for i in range(3): out[i][3]=v[i]
    return out


def dataset():
    raw=MOTION.read_bytes();require(sha(raw)==DATASET_SHA,'Compact evaluated source dataset pin changed')
    d=json.loads(raw)
    require(d['sampleSpace']=='armature_object' and d['matrixConvention']=='row_major; column_vectors', 'Source space changed')
    require(d['conversion']['basis']==BASIS, 'Source/model basis changed')
    require(d['sourceFbxSHA256']=='30f83e8948ac97294d9fde96d6fc53c12e9b3f242b04d1206c3a8e5c138aecb6', 'Source FBX pin changed')
    require(d['boneIds']==BONES, 'Hash bone mapping changed')
    for kind,tag in TAGS.items():
        c=d['clips'][kind]
        require(c['tag']==tag and len(c['samples'])==102, 'Clip/sample contract changed')
        require(c['samples'][0]['seconds']==0 and abs(c['samples'][-1]['seconds']-101/30)<1e-12, 'Source timing changed')
        for f in c['samples']:
            for m in f['matrices'].values(): rigid(m)
    return d


_MOTION = None


def motion_data():
    global _MOTION
    if _MOTION is None: _MOTION=dataset()
    return _MOTION


def source_pose(kind, progress):
    require(0 <= progress <= 1, 'Progress outside normalized range')
    frames=motion_data()['clips'][kind]['samples']; f=progress*(len(frames)-1)
    lo=int(f);hi=min(lo+1,len(frames)-1)
    return {p:interpolate(rigid(frames[lo]['matrices'][p]),rigid(frames[hi]['matrices'][p]),f-lo) for p in PARTS}


def part_indices(part):
    return MAGAZINE if part=='magazine' else BOLT if part=='bolt' else tuple(i for i in range(79) if i not in MAGAZINE+BOLT)


def motion(kind, progress, close_end=True):
    """Root in neutral root basis; independent root-relative mechanical bones."""
    if progress==0 or progress==1 and close_end: return {p:identity() for p in PARTS}
    d=motion_data()['conversion']; neutral=source_pose(kind,0); pose=source_pose(kind,progress)
    scale=d['modelUnitsPerSourceUnit']; c=BASIS; ci=inv(c)
    def convert(m):
        m=mul(mul(c,m),ci)
        for i in range(3): m[i][3]*=scale
        return m
    rest=rigid(motion_data()['bones']['body']['restMatrix'])
    neutral_rest=mul(inv(rest),neutral['body']); pose_rest=mul(inv(rest),pose['body'])
    root=convert(mul(inv(neutral_rest),pose_rest))
    anchor=d['anchors']['body']; root=mul(mul(translation(anchor),root),translation([-v for v in anchor]))
    out={'body':root}
    for part in ('magazine','bolt'):
        a=mul(inv(neutral['body']),neutral[part]); b=mul(inv(pose['body']),pose[part])
        delta=mul(b,inv(a))
        # Retarget bone rotation around the target mechanical anchor, retaining
        # source bone-head displacement rather than rotating around source origin.
        for i in range(3): delta[i][3]=b[i][3]-a[i][3]
        delta=convert(delta); pivot=d['anchors'][part]
        local=mul(mul(translation([pivot[i]+delta[i][3] for i in range(3)]),
                      qmatrix(quat(delta),[0,0,0])),translation([-v for v in pivot]))
        out[part]=mul(root,local)
    # Source motion ends close to its own neutral; runtime must restore accepted
    # target neutral exactly. Blend only final 10%, with no interior embellishment.
    if close_end and progress>.9:
        t=(progress-.9)/.1;t=t*t*(3-2*t)
        out={p:interpolate(m,identity(),t) for p,m in out.items()}
    return out


def display_for(base, kind, progress, part):
    if progress in (0,1): return copy.deepcopy(base)
    result=copy.deepcopy(base); m=motion(kind,progress)[part]
    for context in FP:
        d=result[context]; r=rotation(d['rotation']); scale=d['scale']
        require(max(scale)-min(scale)<1e-9, 'Nonuniform accepted display scale')
        # Both stored hand transforms use the same matrix. Native left hand is
        # M R M with translation X reflected, preserving W84 mirror convention.
        composed=mul(r,m)
        offset=[point(m,[8,8,8])[i]-8 for i in range(3)]
        d['rotation']=[round(v,9) for v in euler(composed)]
        delta=point(r,[v*scale[0] for v in offset])
        d['translation']=[round(v+delta[i],9) for i,v in enumerate(d['translation'])]
    return result


def posed_elements(elements, kind, progress):
    """Bake only local part motion for honest offline previews; body uses display."""
    out=copy.deepcopy(elements); transforms=motion(kind,progress)
    for part in ('magazine','bolt'):
        m=mul(inv(transforms['body']),transforms[part])
        for i in part_indices(part):
            e=out[i]; old=e.get('rotation',{}); center=[(a+b)/2 for a,b in zip(e['from'],e['to'])]
            angles=[old.get(a,0) for a in 'xyz']; pivot=old.get('origin',[8,8,8])
            center=[a+b for a,b in zip(pivot,rotate([v-pivot[j] for j,v in enumerate(center)],angles))]
            center=point(m,center); dimensions=[b-a for a,b in zip(e['from'],e['to'])]
            e['from']=[center[j]-dimensions[j]/2 for j in range(3)]
            e['to']=[center[j]+dimensions[j]/2 for j in range(3)]
            rot=euler(mul(m,rotation(angles)))
            e['rotation']=dict(origin=center,x=rot[0],y=rot[1],z=rot[2],rescale=False)
    return out


def extract_source(path):
    """Read W196 evaluated evidence; never touch FBX, SSD or a live application."""
    import gzip
    raw=gzip.decompress(path.read_bytes()); source=json.loads(raw)
    require(sha(raw)=='b8d3223bb5a2471e4f067197c7cbf07233ef3bde32817f800e50d2510ade3320', 'W196 evaluated sample pin changed')
    indices={b['name']:i for i,b in enumerate(source['bones'])}
    selected={p:source['bones'][indices[b]] for p,b in BONES.items()}
    base=json.loads((ASSETS/'models/item/weapon/izanagis_burden.json').read_bytes())
    # Source bolt-mag forward separation calibrated to accepted receiver centers.
    rest={p:rigid(b['restMatrix']) for p,b in selected.items()}
    a=point(inv(rest['body']),[rest['magazine'][i][3] for i in range(3)])
    b=point(inv(rest['body']),[rest['bolt'][i][3] for i in range(3)])
    anchors={'body':[8,8,8]}
    for p,i in [('magazine',26),('bolt',25)]: anchors[p]=[(x+y)/2 for x,y in zip(base['elements'][i]['from'],base['elements'][i]['to'])]
    scale=(anchors['bolt'][2]-anchors['magazine'][2])/(a[0]-b[0])
    d={k:source[k] for k in ('schemaVersion','group','sourceFbx','sourceFbxSHA256','sourceManifestSHA256','sourceBoneMapSHA256','sampleSpace','matrixConvention','fps','importObjectMatrix','blenderVersion','blenderBuild')}
    d.update(evaluatedSample='docs/qa/2026-10-27/w196/samples/'+path.name,evaluatedUncompressedSHA256=sha(raw),evaluatedGzipSHA256=sha(path.read_bytes()),
             boneIds=BONES,bones=selected,unmappedBone='72997168',honedExclusivityConfirmed=False, boltRelativeMotion='Stationary within FBX numerical tolerance (<0.00012 degrees, <4.3e-7 source units); do not invent bolt action',
             conversion=dict(basis=BASIS,modelUnitsPerSourceUnit=scale,anchors=anchors,outerFbxMatrixApplied=False,
                neutral='Each clip first evaluated frame -> accepted W84 display at grip [8,8,8]',
                formula='root=C*inverse(P_root0)*P_root(t)*inverse(C); part=inverse(P_root(t))*P_part(t); relative rotation and head displacement from frame0; target anchor compensation; root*part',
                restBasis='N_rest=inverse(Rest_root)*P_root0; P_rest(t)=inverse(Rest_root)*P_root(t); inverse(N_rest)*P_rest(t) calibrates to accepted neutral. Independent bone rest orientation cancels in root-relative R(t)*inverse(R0). Bone hash mapping, never bone-map index.',
                timing='linear progress*101/30 seconds; 21 runtime samples; only final progress .9..1 smoothstep/slerp to accepted neutral',
                geometryMapping=dict(body=list(part_indices('body')),magazine=list(MAGAZINE),bolt=list(BOLT)),
                boltEvidence='Original cubes25/77 form rear longitudinal receiver/bolt sleeve, adjoining body36 at raw Z16.45625; end Z25.45625. Magazine26 ahead at Z13.45625..16.45625. Generic groups do not encode skin weights; mechanical assignment inferred from coordinates.',
                axisEvidence='root-local bolt-minus-mag=(-.08778,+.02489,+.03508): bolt rearward and above magazine; model -Z is muzzle, +Y height. Y-side sign is a recorded calibration, pending native/contact review.'),clips={})
    for kind,tag in TAGS.items():
        c=next(c for c in source['clips'] if c['tag']==tag)
        d['clips'][kind]={k:v for k,v in c.items() if k!='frames'}
        d['clips'][kind]['samples']=[dict(frame=f['frame'],seconds=f['seconds'],matrices={p:f['matrices'][indices[b]] for p,b in BONES.items()}) for f in c['frames']]
    return (json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()


def read_json(path, inputs):
    raw = path.read_bytes()
    inputs[path] = sha(raw)
    return json.loads(raw)


def resolve_model(identifier, inputs):
    require(identifier.startswith('destiny:'), 'Unexpected external model')
    model = read_json(ASSETS / ('models/' + identifier.split(':', 1)[1] + '.json'), inputs)
    if 'parent' not in model:
        return model
    parent = resolve_model(model['parent'], inputs)
    # Native display contexts inherit independently, not field by field.
    display = copy.deepcopy(parent.get('display', {}))
    display.update(model.get('display', {}))
    parent.update(model)
    parent['display'] = display
    parent.pop('parent', None)
    return parent


def charge_geometry(convert):
    """Thin blue-white border accents; no opaque shell covering original artwork.

    Raw source coordinates follow the barrel top/bottom edges and muzzle collar.
    Deliberately below optic line; never cross the source lens center ray.
    """
    boxes = []
    for z0, z1 in [(-12, -7), (-6.7, -1.7), (-1.4, 3.6), (3.9, 9.8)]:
        for x0, x1 in [(7.12, 7.24), (8.76, 8.88)]:
            boxes.append(([x0, 12.46, z0], [x1, 12.62, z1]))
    # Small segments on lower edges keep the cue visible on a rolled inspect.
    for z0, z1 in [(-10.5, -4), (-3.5, 3), (3.5, 10)]:
        for x0, x1 in [(7.16, 7.26), (8.74, 8.84)]:
            boxes.append(([x0, 8.75, z0], [x1, 8.88, z1]))
    for x0, x1 in [(7.10, 7.24), (8.76, 8.90)]:
        boxes.append(([x0, 8.72, -14.53], [x1, 12.67, -14.35]))
    faces = {name: {'uv': [0, 0, 16, 16], 'texture': '#3'}
             for name in ('north', 'east', 'south', 'west', 'up', 'down')}
    return [{'from': [round(v, 9) for v in convert(a)],
             'to': [round(v, 9) for v in convert(b)],
             'faces': copy.deepcopy(faces), 'shade': False} for a, b in boxes]


def preview_model(source, native, extras, offset, display, texture_raw):
    """Self-contained java_block preview in the same coordinates as native JSON."""
    preview = copy.deepcopy(source)
    preview['name'] = ('W91 Izanagi authored presentation preview' if extras
                       else 'W197 Izanagi source-derived presentation preview')
    preview.pop('animations', None)
    preview['display'] = copy.deepcopy(display)
    for index, (cube, element) in enumerate(zip(preview['elements'], native)):
        delta = offset if index in MAGAZINE else [0, 0, 0]
        for field in ('from', 'to'):
            cube[field] = [round(v + delta[i], 9) for i, v in enumerate(element[field])]
        cube['origin'] = copy.deepcopy(element.get('rotation', {}).get('origin', [8, 8, 8]))
        if 'rotation' in element:
            cube['rotation'] = [element['rotation'][a] for a in 'xyz']
        else:
            cube.pop('rotation', None)
        for face, data in element['faces'].items():
            cube['faces'][face] = {'uv': [v * 4 for v in data['uv']],
                                   'texture': int(data['texture'][1:])}
    if extras:
        preview['textures'].append(dict(name='w91_charge.png', id='3',
            uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, KEY + '/charge_texture')),
            source='data:image/png;base64,' + base64.b64encode(texture_raw).decode(),
            mode='bitmap', saved=True, uv_width=64, uv_height=64))
        children = []
        for index, e in enumerate(extras):
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, KEY + '/charge/' + str(index)))
            preview['elements'].append(dict(name=f'authored_charge_border_{index:02}',
                uuid=uid, type='cube', **{
                    'from': e['from'], 'to': e['to'], 'origin': [8, 8, 8],
                    'box_uv': False, 'autouv': 0, 'shade': False,
                    'faces': {f: {'uv': [v * 4 for v in d['uv']], 'texture': 3}
                              for f, d in e['faces'].items()}}))
            children.append(uid)
        preview['outliner'].append(dict(name='W91 authored charged border',
            origin=[8, 8, 8], uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, KEY + '/charge_group')),
            children=children))
    return preview


def evaluate(graph, context, pose, flag, aim, state):
    kind = graph['type'].split(':')[-1]
    if kind == 'model':
        return [graph['model']]
    if kind == 'composite':
        return [x for child in graph['models'] for x in evaluate(child, context, pose, flag, aim, state)]
    if kind == 'condition':
        return evaluate(graph['on_true' if flag else 'on_false'], context, pose, flag, aim, state)
    if kind == 'select':
        value = context if graph['property'] == 'minecraft:display_context' else pose
        child = graph['fallback']
        for case in graph['cases']:
            when = case['when'] if isinstance(case['when'], list) else [case['when']]
            if value in when:
                child = case['model']
                break
        return evaluate(child, context, pose, flag, aim, state)
    require(kind == 'range_dispatch', 'Unknown graph node ' + kind)
    value = aim if graph['index'] == 3 else state
    value = f32(value)
    child = graph['fallback']
    for entry in graph['entries']:
        threshold = f32(entry['threshold'])
        if value >= threshold:
            child = entry['model']
    return evaluate(child, context, pose, flag, aim, state)


def build():
    inputs = {}
    source = read_json(SOURCE, inputs)
    require(inputs[SOURCE] == SOURCE_SHA, 'Read-time original SHA mismatch')
    base = read_json(ASSETS / 'models/item/weapon/izanagis_burden.json', inputs)
    original_item = read_json(ASSETS / 'items/weapon/izanagis_burden.json', inputs)
    aim_item = read_json(ASSETS / 'items/weapon_aim_w70/izanagis_burden.json', inputs)
    require(len(base['elements']) == 79, 'Expected all 79 original cubes')
    require(len(source['textures']) == 3, 'Expected three original atlases')
    require(not source.get('animations'), 'Source gained animation; re-audit authoring')
    for path in [HELPER_PATH, ROOT / 'scripts/generate_reload_models_w47.py',
                 ROOT / 'scripts/generate_reload_models_w64.py',
                 ROOT / 'scripts/generate_reload_models_w69.py',
                 ROOT / 'art/weapons/w84/model/README.md',
                 ROOT / 'art/weapons/w84/model/manifest.json',
                 ROOT / 'art/weapons/w84/reference-notes.md',
                 ROOT / 'art/weapons/w84/references/gameplay-evidence.json',
                 ROOT / 'docs/design/99_이자나기의_짐_연마된_칼날.md']:
        inputs[path] = sha(path.read_bytes())
    atlases = []
    for texture, suffix in zip(source['textures'], ('_lens', '', '_accent')):
        path = ASSETS / f'textures/item/weapon/izanagis_burden{suffix}.png'
        raw = path.read_bytes()
        inputs[path] = sha(raw)
        require(raw == base64.b64decode(texture['source'].split(',', 1)[1]), 'Original atlas changed')
        atlases.append(raw)
    for name in ['youtube-KgJR3zohsEs-storyboard-L3-M2-raw.jpg',
                 'youtube-ov6C5oF7KSc-storyboard-L2-M0-raw.jpg']:
        path = ROOT / 'art/weapons/w84/references' / name
        inputs[path] = sha(path.read_bytes())
    # Same uniform W84 source-to-native coordinate conversion; no UV edits.
    cube = source['elements'][53]
    center = H['source_point'](cube, [(a+b)/2 for a, b in zip(cube['from'], cube['to'])])
    shift = [8 - v * .625 for v in center]
    def convert(point):
        return [v * .625 + shift[i] for i, v in enumerate(point)]
    for index, (s, e) in enumerate(zip(source['elements'], base['elements'])):
        for field in ('from', 'to'):
            require(max(abs(a-b) for a, b in zip(convert(s[field]), e[field])) < 1e-8,
                    f'Source geometry mismatch {index}')
        for face in s['faces']:
            require(e['faces'][face] == dict(uv=[v/4 for v in s['faces'][face]['uv']],
                    texture='#' + str(s['faces'][face]['texture'])), f'Original UV mismatch {index}')
        source_rotation = s.get('rotation', [0,0,0])
        require(('rotation' in e) == any(source_rotation), 'Original cube rotation lost')
        if any(source_rotation):
            require([e['rotation'][a] for a in 'xyz'] == source_rotation and
                    not e['rotation']['rescale'], 'Original cube rotation changed')
            require(max(abs(a-b) for a,b in zip(convert(s['origin']),e['rotation']['origin'])) < 1e-8,
                    'Original cube pivot changed')
    output = {}
    def put_model(key, value):
        path = ASSETS / ('models/' + key + '.json')
        output[path] = encode(value)
    for part in PARTS:
        geometry = {k: copy.deepcopy(v) for k, v in base.items() if k != 'display'}
        geometry['elements'] = [copy.deepcopy(e) for i, e in enumerate(base['elements'])
                                if i in part_indices(part)]
        put_model(KEY + '_' + part, geometry)
    reloads = {}
    poses = []
    for kind in TAGS:
        entries = []
        for frame in range(RELOAD_SAMPLES):
            branches = {}
            for part in PARTS:
                display = display_for(base['display'], kind, frame/RELOAD_INTERVALS, part)
                for branch in ('native', 'twohand'):
                    key = f'{KEY}_{kind}_{frame:02}_{part}_{branch}'
                    put_model(key, dict(parent='destiny:' + KEY + '_' + part,
                        display=display if branch == 'native' else two_hand_display(display)))
                    branches[part, branch] = node(key)
            models = {branch: dict(type='minecraft:composite', models=[branches[p, branch]
                        for p in PARTS]) for branch in ('native', 'twohand')}
            entries.append(dict(threshold=selector(frame, 0 if kind == 'ordinary' else 2), model=grip(models['native'], models['twohand'])))
            poses.append(dict(kind=kind, frame=frame, progress=frame/RELOAD_INTERVALS,
                slot6=selector(frame, 0 if kind == 'ordinary' else 2),
                sourceTag=TAGS[kind], sourceSeconds=frame/RELOAD_INTERVALS*101/30, partMatrices=motion(kind, frame/RELOAD_INTERVALS)))
        reloads[kind] = dict(type='minecraft:range_dispatch',
            property='minecraft:custom_model_data', index=6,
            entries=entries, fallback=aim_item['model'])
    extras = charge_geometry(convert)
    require(79 + len(extras) <= 256, 'Charged cube budget')
    # Opaque blue-white color, no mcmeta, emission, bloom, shader or invented codec fields.
    texture_raw = H['png_encode'](16, 16, bytes([199, 218, 255, 255] * 256))
    output[TEXTURE] = texture_raw
    charged = copy.deepcopy(base)
    charged['textures']['3'] = 'destiny:item/weapon_izanagi_w91/charge'
    charged['elements'] += extras
    put_model(KEY + '_charged', charged)
    remaps = {}
    def charged_graph(graph):
        result = copy.deepcopy(graph)
        def walk(n):
            if isinstance(n, dict):
                if n.get('type') == 'minecraft:model':
                    old = n['model']
                    if old not in remaps:
                        original = resolve_model(old, inputs)
                        tail = old.split('/')[-1]
                        key = 'item/weapon_izanagi_w91/charged_' + tail
                        put_model(key, dict(parent='destiny:' + KEY + '_charged',
                                            display=original['display']))
                        remaps[old] = 'destiny:' + key
                    n['model'] = remaps[old]
                for value in list(n.values()):
                    walk(value)
            elif isinstance(n, list):
                for child in n:
                    walk(child)
        walk(result)
        return result
    charged_aim = charged_graph(aim_item['model'])
    def state_dispatch(first_person):
        return dict(type='minecraft:range_dispatch', property='minecraft:custom_model_data', index=6,
            entries=[dict(threshold=0, model=reloads['ordinary'] if first_person else aim_item['model']),
                     dict(threshold=1.01, model=aim_item['model']),
                     dict(threshold=2, model=reloads['honed'] if first_person else aim_item['model']),
                     dict(threshold=3.01, model=aim_item['model']),
                     dict(threshold=4, model=charged_aim),
                     dict(threshold=4.01, model=aim_item['model'])], fallback=aim_item['model'])
    # Preserve inspection priority during stale reload data as W84 does during aim.
    first = dict(type='minecraft:select', property='minecraft:custom_model_data', index=0,
        cases=[dict(when='inspect', model=state_dispatch(False))], fallback=state_dispatch(True))
    wrapper = {k: copy.deepcopy(v) for k, v in original_item.items() if k != 'model'}
    wrapper['model'] = dict(type='minecraft:select', property='minecraft:display_context',
        cases=[dict(when=list(FP), model=first)], fallback=state_dispatch(False))
    output[ITEM] = encode(wrapper)
    checks = validate(output, base, wrapper, aim_item, remaps, extras, inputs)
    previews = []
    # Historical preview suffixes are W197 /20 snapshot indices, not dense-bank indices.
    for kind, frame in [('ordinary', 7), ('ordinary', 14), ('honed', 10), ('honed', 17)]:
        display = display_for(base['display'], kind, frame/20, 'body')
        offset = [0,0,0]
        path = ART / f'asset-preview-{kind}-{frame:02}.bbmodel'
        output[path] = encode(preview_model(source, posed_elements(base['elements'],kind,frame/20), [], offset, display, texture_raw))
        previews.append(dict(path=relative(path), slot6=(0 if kind == 'ordinary' else 2)+frame/20,
            string0='hip', flag0=False, float3=0, description='Source-derived display; independent magazine/bolt rigid poses baked into geometry'))
    for pose in ('hip', 'scope', 'inspect'):
        name = 'izanagis_burden' + ('' if pose == 'hip' else '_' + pose)
        resolved = resolve_model('destiny:item/weapon/' + name, inputs)
        path = ART / f'asset-preview-charged-{pose}.bbmodel'
        output[path] = encode(preview_model(source, base['elements'], extras, [0,0,0],
                                           resolved['display'], texture_raw))
        previews.append(dict(path=relative(path), slot6=4, string0=pose, flag0=False,
            float3=-1, description='Completed charged, all original detail plus thin colored border'))
    output[ART / 'asset-poses.json'] = encode(dict(sourceDataset=relative(MOTION), sourceTags=TAGS, samples=poses,
                                                  previews=previews, chargedModelRemaps=remaps))
    # Offline atlas-exact software views for review, not native renderer evidence.
    ads_display = resolve_model('destiny:item/weapon/izanagis_burden_ads', inputs)['display']
    for kind, frame in [('ordinary', 4), ('honed', 4), ('charged', None)]:
        elements = copy.deepcopy(base['elements'])
        display = base['display']
        if frame is None:
            elements += extras
        else:
            display = display_for(display, kind, frame/20, 'body')
            elements = posed_elements(elements,kind,frame/20)
        output[ART / f'asset-preview-{kind}.png'] = H['offline_preview'](
            elements, atlases + [texture_raw], {'hip': display, 'ads': ads_display})
    output[ART / 'asset-validation.json'] = encode(checks)
    output[ART / 'asset-handoff.md'] = HANDOFF.encode()
    originalhash = dict(readTimeOriginalSha256=SOURCE_SHA,
        sha256={relative(p): value for p, value in sorted(inputs.items())})
    output[ART / 'asset-originalhash.json'] = encode(originalhash)
    output[ART / 'asset-outputmanifest.json'] = encode(dict(stage='W198-dense-source-motion',
        itemIdentifier='destiny:weapon_izanagi_w91/izanagis_burden',
        generator=relative(GENERATOR), generatorSha256=sha(GENERATOR.read_bytes()),
        originalCubes=79, originalFaceUvs=474, originalAtlases=3,
        magazineSourceIndices=list(MAGAZINE), boltSourceIndices=list(BOLT), bodyCubes=76, magazineCubes=1, boltCubes=2,
        sourceDataset=relative(MOTION), sourceDatasetSHA256=sha(MOTION.read_bytes()), sourceTags=TAGS, honedExclusivityConfirmed=False,
        magazineSourceUuids=[source['elements'][i]['uuid'] for i in MAGAZINE],
        chargedAddedCubes=len(extras), chargedTotalCubes=79+len(extras), samplesPerReload=RELOAD_SAMPLES, intervalsPerReload=RELOAD_INTERVALS,
        nativeGameplayVerified=False, nativeFullCodecExecuted=False,
        sourceEvaluatedAnimation=True, handIK=False, displayLightEmissionUsed=False,
        sha256={relative(p): sha(raw) for p, raw in sorted(output.items())}))
    return output, inputs


def validate(output, base, wrapper, aim_item, remaps, extras, inputs):
    def geometry(key):
        return json.loads(output[ASSETS / ('models/' + key + '.json')])
    parts={p:geometry(KEY+'_'+p) for p in PARTS}
    require([len(parts[p]['elements']) for p in PARTS]==[76,1,2], 'Part counts')
    for p in PARTS:
        require(parts[p]['elements']==[base['elements'][i] for i in part_indices(p)], 'Original geometry/UV partition changed')
    require(geometry(KEY + '_charged')['elements'][:79] == base['elements'], 'Charged original geometry changed')
    require(all(e['to'][1] < base['elements'][78]['from'][1] for e in extras), 'Cue reaches optic ray height')
    for kind in TAGS:
        for part in PARTS:
            for frame in (0,RELOAD_INTERVALS):
                for branch in ('native','twohand'):
                    actual=geometry(f'{KEY}_{kind}_{frame:02}_{part}_{branch}')['display']
                    expected=base['display'] if branch=='native' else two_hand_display(base['display'])
                    require(actual==expected,'Reload endpoint failed to restore accepted display')
        for frame in range(RELOAD_SAMPLES):
            matrices=motion(kind,frame/RELOAD_INTERVALS)
            for context in FP:
                left=context==FP[1];mirror=identity();mirror[0][0]=-1;mirror[0][3]=16
                for part in PARTS:
                    native=geometry(f'{KEY}_{kind}_{frame:02}_{part}_native')['display'][context]
                    twohand=geometry(f'{KEY}_{kind}_{frame:02}_{part}_twohand')['display'][context]
                    local=mul(mul(mirror,matrices[part]),mirror) if left else matrices[part]
                    for p in ([8,8,8],[8,9,10],[9,10,7]):
                        actual=H['item_point'](p,native,left)
                        expected=H['item_point'](point(local,p),base['display'][context],left)
                        require(max(abs(a-b) for a,b in zip(actual,expected))<3e-8,'Composed source transform differs between hands')
                        compensated=H['item_point'](p,twohand,left);sign=-1 if left else 1
                        carried=rotate(compensated,[0,10*sign,0]);carried[0]-=.641864*16*sign
                        require(max(abs(a-b) for a,b in zip(actual,carried))<3e-8,'Two-hand inverse changes source part pose')
    graph_checks = 0
    for context in (*FP, 'gui', 'ground', 'thirdperson_righthand', 'thirdperson_lefthand', 'fixed', 'head'):
        for pose in ('hip', 'ads', 'scope', 'inspect', 'unknown', ''):
            for flag in (False, True):
                for aim in (-1, 0, .35, 1):
                    old = evaluate(aim_item['model'], context, pose, flag, aim, -1)
                    require(evaluate(wrapper['model'],context,pose,flag,aim,-1) == old, 'Idle fallback changed')
                    require(evaluate(wrapper['model'],context,pose,flag,aim,4) == [remaps[x] for x in old],
                            'Charged pose/grip/aim/scope routing changed')
                    for kind, start in [('ordinary',0),('honed',2)]:
                        for frame in range(RELOAD_SAMPLES):
                            for offset in GENERATION_OFFSETS:
                                value = selector(frame, start, offset)
                                actual = evaluate(wrapper['model'],context,pose,flag,aim,value)
                                if context in FP and pose != 'inspect':
                                    branch = 'twohand' if flag else 'native'
                                    expected = ['destiny:' + f'{KEY}_{kind}_{frame:02}_{p}_{branch}'
                                                for p in PARTS]
                                else:
                                    expected = old
                                require(actual == expected, f'Slot6 routing mismatch {kind} {frame} {value}')
                                graph_checks += 1
                    for invalid in (1.5, 3.5, 4.5, 5):
                        require(evaluate(wrapper['model'],context,pose,flag,aim,invalid)==old, 'Gap fallback changed')
    # Resolve every parent/model/texture reference and enforce owned geometry bounds.
    ref_checks = 0
    def walk(value):
        nonlocal ref_checks
        if isinstance(value,dict):
            for field in ('parent','model'):
                identifier = value.get(field)
                if isinstance(identifier,str) and identifier.startswith('destiny:'):
                    path = ASSETS / ('models/'+identifier.split(':',1)[1]+'.json')
                    require(path in output or path.is_file(), 'Missing model ' + identifier)
                    ref_checks += 1
            for v in value.values():
                walk(v)
        elif isinstance(value,list):
            for child in value:
                walk(child)
    for path, raw in list(output.items()):
        if path.suffix != '.json':
            continue
        data = json.loads(raw)
        walk(data)
        for element in data.get('elements',[]):
            require(all(math.isfinite(v) and -16 <= v <= 32 for field in ('from','to')
                        for v in element[field]), 'Native coordinate outside bounds')
            require('light_emission' not in element, 'Unverified emission field')
        for identifier in data.get('textures',{}).values():
            if identifier.startswith('destiny:'):
                path = ASSETS / ('textures/'+identifier.split(':',1)[1]+'.png')
                require(path in output or path.is_file(), 'Missing texture')
    return dict(originalCubesPreserved=79, originalFaceUvsPreserved=474, originalAtlasesByteExact=3,
        zeroThicknessLensPlanesPreserved=2, chargedTotalCubes=79+len(extras),
        graphSampleCases=graph_checks, float32ThresholdsAndOffsetsChecked=list(GENERATION_OFFSETS),
        reloadSamples=RELOAD_SAMPLES, reloadIntervals=RELOAD_INTERVALS,
        reloadThresholdsExact=True, bothHandsBothGripsChecked=True,
        scopeInspectAdsRoutingPreserved=True, originalEndpointsRestored=True,
        softwareReloadPreviewProgress=.2,
        sourceDerivedMotion=True, independentRootMagazineBoltSamples=True, honedExclusivityConfirmed=False, modelReferenceChecks=ref_checks,
        partRigidTransformsBothHandsChecked=True, twoHandCarrierInverseChecked=True,
        nativeFullCodecExecuted=False, nativeGameplayVerified=False,
        opticHeightClearanceChecked=True, exactGlowShaderClaim=False)


HANDOFF = """# W198 Izanagi dense source animation bank

The W91 namespace and item wrapper now provide 61 samples / 60 intervals
(previously 21 / 20), resampling the identical W197 curves. Slot6 ordinary0..1 /
Honed2..3 / charged4 / idle-1 lifecycle, grip and ADS/scope/inspect routing remain.
This worker leaves runtime Java to master (60-interval quantization and collision
checks). Gameplay deadlines, charged accents and three original atlases remain.
Float32 thresholds match Java division/base addition, with generation offsets
0, .00025 and .0005 staying inside the intended bucket for both reload modes.

Ordinary samples come from evaluated80A8A140. Honed cosmetic samples use the
80A8A14D reload_special candidate; exclusivity and actual Honed trigger are NOT
confirmed. Both clips are very similar; no exaggerated authored curve is added.
The bolt stays stationary relative to the root within FBX numerical tolerance
(<0.00012deg, <4.3e-7 source units); no authored bolt cycle is added.
The compact W197 dataset contains all102 source frames for root4A0810C4,
magazine52EDE88C and bolt69768858, with rest matrices, hashes and conversion.
72997168 remains unmapped. No hands/IK/contact or source events are invented.

Source armature-object cumulative matrices are orthonormalized only for tiny
FBX numerical scale/shear, then quaternion interpolated. The outer .01/axis
matrix is recorded and never baked. Each clip frame1 calibrates to accepted W84
neutral. Root motion uses its neutral basis, parts use independently sampled
root-relative motion, with target-anchor compensation. XYZ is extracted only
after matrix composition; Euler channels are never added. Basis/scale/anchors
and retiming are explicit in the dataset. Progress maps linearly to3.366667s;
existing gameplay timing wins. Only final progress .9..1 blends to exact accepted
neutral. Native left-hand reflection and crossbow twohand inverse are preserved.

Original79 cubes/474 face UVs are partitioned body76+magazine1+bolt2. Cube26 is
magazine. Cubes25/77 form the longitudinal rear bolt sleeve behind the magazine,
adjoining receiver36 at Z16.45625 and ending near25.45625;77 is its diagonal
companion surface. This coordinate-based mechanical mapping is inferred, not
extracted skin weights (the source model groups are generic). No mesh, UV,
grip/ADS, charged95-cube geometry or scope plane redesign occurred.

Reproduce: rtk proxy python3 -B scripts/generate_izanagi_presentation_w91.py
Check: rtk proxy python3 -B scripts/generate_izanagi_presentation_w91.py --verify
Optional provenance rebuild: same generator --extract-source /absolute/path/to/
sniper_rifle_ececad46.json.gz (W196 evaluated evidence read-only). Normal generator
and verify require neither SSD nor Blender. Originalhash baseline is unchanged;
source dataset SHA and source tags are recorded separately in outputmanifest.
The W197 dataset stays byte-identical, including its historical 21-sample note;
W198 density is recorded in this handoff and outputmanifest instead.

Offline PNGs use progress .2 (source time .673333s) to show withdrawal.
Existing bbmodel frame07/14 and10/17 names keep W197 snapshot progress
.35/.70 and .50/.85 (dense indices21/42 and30/51); their bytes stay unchanged.
Offline PNGs/bbmodels bake mechanical rigid motion and use the body display.
They are software previews, not native/contact evidence. Master must check
actual1P/3P transitions, mechanical assignment/axis sign, hand contact, endpoint
settling, cancel/swap cleanup and slot6 timing in centralized native QA. This
worker ran no Blender/Blockbench/server/client/CU/Vision or Gradle.
Vanilla held-item updates remain limited to 20TPS with no per-render pose
blending; a denser bank reduces quantization and does not promise 60FPS motion.
"""


def owned_files():
    files = {GENERATOR}
    for directory in (MODEL_DIR, ITEM.parent, TEXTURE.parent):
        if directory.exists():
            files.update(p for p in directory.rglob('*') if p.is_file())
    if ART.exists():
        files.update(p for p in ART.glob('asset-*') if p.is_file())
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Reconstruct/check; never write')
    parser.add_argument('--extract-source', type=Path, help='Rebuild compact dataset from pinned W196 evaluated gzip')
    args = parser.parse_args()
    metadata = Path((ROOT / '.git').read_text().strip().split(': ',1)[1]) / 'worktree-batch.json' if (ROOT / '.git').is_file() else None
    allowed = None
    if metadata and metadata.exists():
        batch=json.loads(metadata.read_bytes()); require(batch['status']=='ready','Worktree not ready')
        allowed=set(batch['owned_paths'])
    if args.extract_source:
        require(allowed is None or relative(MOTION) in allowed,'Dataset is not owned')
        raw=extract_source(args.extract_source)
        if args.verify: require(MOTION.read_bytes()==raw, 'Extracted dataset differs')
        else:
            MOTION.parent.mkdir(parents=True,exist_ok=True);MOTION.write_bytes(raw)
    motion_data()
    output, inputs = build()
    baseline = ART / 'asset-originalhash.json'
    if baseline.exists():
        require(baseline.read_bytes() == output[baseline], 'Original inputs changed since first authoring; re-audit required')
    unexpected = owned_files() - set(output) - {GENERATOR}
    require(not unexpected, 'Unexpected owned output files: ' + str(sorted(map(relative,unexpected))))
    for path, raw in output.items():
        if allowed is not None and relative(path) not in allowed:
            require(path.is_file() and path.read_bytes()==raw,'Changed unowned output: '+relative(path))
        require(path == ITEM or path == TEXTURE or path.parent == MODEL_DIR or
                path.parent == ART and path.name.startswith('asset-'), 'Write outside ownership')
        if args.verify:
            require(path.is_file() and path.read_bytes() == raw, 'Output mismatch: ' + relative(path))
        else:
            if path == TEXTURE:
                require(path.read_bytes()==raw, 'Existing charged texture changed; unowned read-only input')
                continue
            if path.is_file() and path.read_bytes()==raw:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    for path, expected in inputs.items():
        require(sha(path.read_bytes()) == expected, 'Original input changed during generation')
    print(f'{"Verified read-only" if args.verify else "Generated"} {len(output)} W91 files; '
          f'original SHA {SOURCE_SHA}; ordinary/Honed{RELOAD_SAMPLES} each; charged95 cubes')


if __name__ == '__main__':
    main()
