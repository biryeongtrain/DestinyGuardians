#!/usr/bin/env python3
"""Ace cosmetic first-person reload; stdlib only, no runtime/audio/mechanics edits.

W198: dense bank of evaluated Ace 80A8A567 + disclosed W157 mechanical hybrid.
Canonical cubes/UVs stay intact. 61 native/twohand poses use rigid source
matrices; cylinder/yoke, extractor and six cartridges remain authored.
XYZ matrices are composed before decomposition, never added as Euler angles.
"""
import argparse
import copy
import gzip
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = Path("src/main/resources/assets/destiny")
KEY = "weapon_reload_w157/ace_of_spades"
SOURCE = ASSET / "models/item/weapon/ace_of_spades.json"
TWOHAND = ASSET / "models/item/weapon/ace_of_spades_twohand.json"
ITEM = ASSET / "items/weapon/ace_of_spades.json"
AUDIT = Path("art/weapons/w83/model/manifest.json")
MANIFEST = Path("art/weapons/w157/ace-reload.json")
MOTION = Path("art/weapons/w197/ace-source-motion.json")
ACE_SAMPLE_SHA = "fdc1867d29b4a87e918ed57859a07d6ebae07cd7f9a78cdd0b73e1c88edd31e2"
BODY_BONE = "4A0810C4"
TRACK_SHA = "b05ec084ae820ef0f4ff07845f9ebe298698361d3fcab48e02eb429be7e79696"
# Source root local X forward / Z up -> accepted model -Z forward / Y up.
BASIS = [[0, -1, 0], [0, 0, 1], [-1, 0, 0]]
INTERVALS = 60
SAMPLES = INTERVALS + 1
FP = ("firstperson_righthand", "firstperson_lefthand")
# Audited source element indices, not bounds-based selection. The supplied bbmodel
# has a flat UUID outliner, NOT named mechanical groups. W83 preserves its order.
DRUM = (25, 26, 27, 28, 29, 30, 31, 32, 37, 38, 39, 40, 41, 42, 43, 44)
AXLE = (48,)
YOKE = (49, 50, 51, 52)
CYLINDER = DRUM + AXLE + YOKE
CYLINDER_UUIDS = (
    "c4a1592c-b378-d02a-d226-434e33dd4e97", "72d63609-f5a8-160a-f333-2b1035e06760",
    "7473771e-795f-2bfa-2cd4-13e864a9bf0a", "5fb3bbcf-f55a-ecd9-24aa-8b5dc711da2b",
    "efbc44a0-8833-d6bc-2f05-193453d2033f", "1f60970f-af98-2fde-fa6f-d2689e434e2f",
    "4e424fbb-41a6-a42e-25c2-7222ef31eb50", "f8504c81-cf33-488c-79b8-ec8e5e5c5e50",
    "28172f66-f44e-9ccb-9d40-f0d249de4ec3", "ae0d0518-1813-b7db-3d26-63b6a8988d56",
    "41d0fe19-c913-44c5-8731-bfc468a47a7a", "0fdf87ee-b83a-e121-cf05-4805e4ebf8b5",
    "731db041-7d2a-4150-0d43-e20bbfeab50a", "0f29849a-9e89-ff24-5590-d57571d791ef",
    "65e7d228-c98a-b1c6-68d9-f63b27cde9fc", "82440a70-8314-76e9-2c01-977bddb5f417",
    "2e7af525-0262-3508-6e7a-cf927b94d092", "0b0dbeda-e3e8-5b11-09cc-c11738950d39",
    "7ac99df0-c35d-9899-3f4c-00145d929a9a", "1fcc1d1e-de17-c61b-1aae-6e1a7bf8fd63",
    "416ea4f7-61e2-443f-75cb-927c5d0661c8",
)
# Original yoke stem (52) midpoint; the hinge runs along the barrel's Z axis.
HINGE = (8.0, 9.144410476, 3.284186918)
# Grip web / trigger-finger region, not the model origin or the cylinder centre.
GRIP = (8.0, 8.234410476, 6.728186918)
DRUM_CENTER = (8.0, 10.404410476, 4.719186918)
# W157 authored mechanical articulation ONLY. No authored body curve survives.
# progress, cylinder hinge angle, extractor travel. This is not extracted motion.
MECHANICAL_KEYS = (
    (0.00, 0, 0), (0.10, 0, 0), (0.20, 76, 0),
    (0.30, 86, 0), (0.35, 86, .65), (0.45, 86, 0),
    (0.50, 86, 0), (0.60, 86, 0), (0.65, 86, 0),
    (0.70, 0, 0), (1.00, 0, 0),
)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def float32(value):
    """Match Java progress division and the client range-dispatch float codec."""
    return struct.unpack("!f", struct.pack("!f", value))[0]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def vec(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def transpose(m):
    return [list(v) for v in zip(*m)]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def xyz(angles):
    """Minecraft/JOML rotationXYZ = Rx Ry Rz; rightmost Z acts first."""
    a, b, c = map(math.radians, angles)
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    return [[cb*cc, -cb*sc, sb],
            [sa*sb*cc+ca*sc, -sa*sb*sc+ca*cc, -sa*cb],
            [-ca*sb*cc+sa*sc, ca*sb*sc+sa*cc, ca*cb]]


def euler(m):
    b = math.asin(max(-1.0, min(1.0, m[0][2])))
    if abs(math.cos(b)) > 1e-8:
        a, c = math.atan2(-m[1][2], m[2][2]), math.atan2(-m[0][1], m[0][0])
    else:
        a, c = math.atan2(m[2][1], m[1][1]), 0.0
    return [round(math.degrees(v), 9) for v in (a, b, c)]


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


def load_motion(root=ROOT):
    data = json.loads((Path(root)/MOTION).read_bytes())
    if (data['group'] != 'hand_cannon_f163a4c8' or data['clip']['tag'] != '80A8A567'
            or data['provenance']['uncompressedSHA256'] != ACE_SAMPLE_SHA
            or data['sampleSpace'] != 'armature_object' or data['bodyBone'] != BODY_BONE
            or data['conversion']['sourceRootToModelBasis'] != BASIS):
        raise ValueError("Wrong Ace source identity/basis")
    if (data['conversion']['modelUnitsPerSourceUnit'] != 32
            or data['conversion']['neutralSourceFrame'] != 1
            or data['conversion']['targetAnchor'] != list(GRIP)):
        raise ValueError("Unexpected Ace neutral/translation calibration")
    if track_sha(data) != TRACK_SHA or data['provenance']['evaluatedTracksSHA256'] != TRACK_SHA:
        raise ValueError("Evaluated Ace tracks differ from pinned extraction")
    frames = data['samples']
    if len(frames) != 127 or set(frames[0]['poses']) != set(data['bones']):
        raise ValueError("Incomplete Ace sample tracks")
    for i,f in enumerate(frames):
        if f['frame'] != i+1 or abs(f['seconds']-i/30) > 1e-8 or set(f['poses']) != set(data['bones']):
            raise ValueError("Invalid Ace source timeline/bone identities")
        for m in f['poses'].values():
            rigid(m)
    return data


def extract_source(sample_path, source_map_path):
    """Read-only W196 import; default generation never needs SSD or Blender."""
    compressed = Path(sample_path).read_bytes(); raw = gzip.decompress(compressed)
    if sha(raw) != ACE_SAMPLE_SHA:
        raise ValueError("Expected pinned evaluated Ace sample, not Duke or authored curves")
    src = json.loads(raw); clip = src['clips'][0]
    smap_raw = Path(source_map_path).read_bytes(); smap = json.loads(smap_raw)
    if (smap['groupId'] != src['group'] or smap['selector'] != '5267F9DF'
            or not any(c['tag'] == clip['tag'] for c in smap['clips'])):
        raise ValueError("Source selector/clip mismatch")
    bones = {b['name']: b for b in src['bones'] if b['weaponBone']}
    index = {b['name']:i for i,b in enumerate(src['bones'])}
    result = {
        'schemaVersion': 1, 'group': src['group'], 'bodyBone': BODY_BONE,
        'sampleSpace': src['sampleSpace'], 'matrixConvention': src['matrixConvention'],
        'provenance': {k:src[k] for k in ('sourceFbx','sourceFbxSHA256','sourceManifestSHA256',
            'sourceBoneMapSHA256','blenderVersion','blenderBuild')} | {
            'sampleFile': 'docs/qa/2026-10-27/w196/samples/hand_cannon_f163a4c8.json.gz',
            'sampleGzipSHA256': sha(compressed), 'uncompressedSHA256': sha(raw),
            'sourceMapSHA256': sha(smap_raw), 'sourceMap': smap,
            'importObjectMatrixMetadataOnly': src['importObjectMatrix']},
        'clip': {k:v for k,v in clip.items() if k != 'frames'}, 'bones': bones,
        'conversion': {
            'neutralSourceFrame': 1, 'sourceRootToModelBasis': BASIS,
            'modelUnitsPerSourceUnit': 32, 'targetAnchor': list(GRIP),
            'basisEvidence': 'Root-rest child positions lie in X/Z plane; X runs along weapon, Z above grip. Map root-local +X to model -Z, +Y to -X, +Z to +Y. Axis signs are calibration, not independently verified source camera axes.',
            'restAttachment': 'Target offset v-GRIP attaches in source rest via R_rest * C^T / 32. Pose * inverse(rest) cancels rest; neutral calibration gives C * inverse(P_0) * P_t * C^T. No outer FBX matrix is baked.',
            'translationCalibration': '32 model units/source unit is an explicit uniform presentation calibration; no per-frame authored body offsets, no mesh scaling.',
            'retiming': 'Linear source seconds = 4.2 * normalized runtime progress. 21 samples; shortest-arc quaternion SLERP between adjacent evaluated 30fps poses, linear position.',
            'endpointBlend': 'Only final 0.95..1 progress: SLERP to identity and translation to zero, smoothstep. Frame 0 and 20 use accepted displays byte-exactly. No interior motion warping.',
            'mechanicalBinding': 'Unresolved. Hash chain 3F37833F > 3C37833F > BE811ABD > 82C5B60A moves relative to root; no mesh skin weights/semantic proof maps it to W157 DRUM/AXLE/YOKE. Keep authored W157 swing/extractor/cartridges; do not label them extracted.',
        },
        'samples': [{'frame':f['frame'], 'seconds':f['seconds'],
                     'poses':{name:f['matrices'][index[name]] for name in bones}} for f in clip['frames']],
    }
    result['provenance']['evaluatedTracksSHA256'] = track_sha(result)
    if track_sha(result) != TRACK_SHA:
        raise ValueError("Extracted tracks differ from pinned Ace data")
    return result


def sample(progress, motion=None):
    if not math.isfinite(progress) or not 0 <= progress <= 1:
        raise ValueError(f"Invalid reload progress: {progress}")
    motion = load_motion() if motion is None else motion
    frames = motion['samples']; n = progress*(len(frames)-1)
    i = min(int(n), len(frames)-2); t = n-i
    ra,pa = rigid(frames[i]['poses'][BODY_BONE]); rb,pb = rigid(frames[i+1]['poses'][BODY_BONE])
    r0,p0 = rigid(frames[0]['poses'][BODY_BONE])
    r = slerp(quaternion(ra), quaternion(rb), t)
    p = add(pa, [(b-a)*t for a,b in zip(pa,pb)])
    body = mul(BASIS, mul(mul(transpose(r0),r), transpose(BASIS)))
    translation = [32*v for v in vec(BASIS, vec(transpose(r0), sub(p,p0)))]
    if progress > .95:
        t = (progress-.95)/.05; t=t*t*(3-2*t)
        body = slerp(quaternion(body), [1,0,0,0], t)
        translation = [v*(1-t) for v in translation]
    if progress in (0,1):
        body,translation = xyz((0,0,0)), [0,0,0]
    for a,b in zip(MECHANICAL_KEYS,MECHANICAL_KEYS[1:]):
        if progress <= b[0]:
            t = (progress-a[0])/(b[0]-a[0]); t=t*t*(3-2*t)
            return body, translation, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t
    raise ValueError(progress)


def pose_display(original, twohand, progress, part, grip, motion=None):
    """T + R S (v-8), preserving the hinge under the complete composed XYZ."""
    accepted = original if grip == "native" else twohand
    if progress in (0, 1):
        return copy.deepcopy(accepted)
    body, translation, swing, _ = sample(progress, motion)
    local = xyz((0, 0, swing if part == "cylinder" else 0))
    # v -> B (L v + P-LP - H) + H. Work in centred model units.
    h, p = sub(GRIP, (8, 8, 8)), sub(HINGE, (8, 8, 8))
    offset = add(sub(h, vec(body, h)), vec(body, sub(p, vec(local, p))))
    display = copy.deepcopy(accepted)
    for context in FP:
        idle = original[context]
        if len(set(idle['scale'])) != 1:
            raise ValueError("Rigid reload requires uniform canonical first-person scale")
        base = xyz(idle['rotation'])
        rotation = mul(base, mul(body, local))
        position = add(idle['translation'],
                       vec(base, [v*idle['scale'][0] for v in add(offset, translation)]))
        if grip == "twohand":
            # Derive the existing charged-crossbow compensation from accepted idle
            # transforms. No hand IK, third-person edits or dependency on W64 math.
            comp = mul(xyz(twohand[context]['rotation']), transpose(base))
            shift = sub(twohand[context]['translation'], vec(comp, idle['translation']))
            position, rotation = add(vec(comp, position), shift), mul(comp, rotation)
        display[context]['rotation'] = euler(rotation)
        display[context]['translation'] = [round(v, 9) for v in position]
    return display


def cylinder_elements(source, progress, motion=None):
    elements = [copy.deepcopy(source[i]) for i in CYLINDER]
    # Authored W157 extractor travel, not an extracted hash-bone binding.
    travel = sample(progress, motion)[3]
    if travel:
        rod = elements[len(DRUM)]
        for key in ('from', 'to'):
            rod[key][2] += travel
    # Six cartridge silhouettes, only during ejection or loading. Reuse the
    # source axle's silver metal UV (no invented brass texture or hand geometry).
    spent = .30 <= progress <= .45
    loading = .50 <= progress <= .65
    if not (spent or loading):
        return elements
    t = (progress-.30)/.15 if spent else (progress-.50)/.15
    for chamber in range(6):
        angle = math.tau*chamber/6
        radius = .57 + (.25*t if spent else 0)
        x = DRUM_CENTER[0] + radius*math.cos(angle)
        y = DRUM_CENTER[1] + radius*math.sin(angle) - (2.7*t*t if spent else 0)
        z = 5.30 + (3.8*t if spent else 2.2*(1-t))
        cartridge = copy.deepcopy(source[48])
        cartridge['name'] = f"W157_{'spent' if spent else 'load'}_chamber_{chamber+1}"
        cartridge['from'], cartridge['to'] = [round(x-.09,9), round(y-.09,9), round(z,9)], [round(x+.09,9), round(y+.09,9), round(z+.82,9)]
        if spent:
            cartridge['rotation'] = {'origin': [round(x,9), round(y,9), round(z+.41,9)],
                                     'x': round(34*t,9), 'y': round((chamber-2.5)*8*t,9),
                                     'z': 0, 'rescale': False}
        elements.append(cartridge)
    return elements


def generate(root=ROOT):
    root = Path(root)
    motion = load_motion(root)
    source = json.loads((root/SOURCE).read_bytes())
    twohand = json.loads((root/TWOHAND).read_bytes())['display']
    item = json.loads((root/ITEM).read_bytes())
    audit = json.loads((root/AUDIT).read_bytes())
    mapping = audit['conversion']['mapping']
    if len(source['elements']) != 87 or tuple(mapping[i]['sourceUuid'] for i in CYLINDER) != CYLINDER_UUIDS:
        raise ValueError("Ace source partition changed; re-audit explicit UUID/index mapping")
    output = {}
    def emit(path, value):
        output[root/path] = encode(value)
    for part in ('body', 'cylinder'):
        geo = {k: copy.deepcopy(v) for k, v in source.items() if k != 'elements'}
        geo['elements'] = [copy.deepcopy(e) for i,e in enumerate(source['elements'])
                           if (i in CYLINDER) == (part == 'cylinder')]
        emit(ASSET/f'models/{KEY}_{part}.json', geo)
    entries = []
    counts = []
    for frame in range(SAMPLES):
        progress = frame/INTERVALS
        extra = cylinder_elements(source['elements'], progress, motion)
        counts.append(66+len(extra))
        for part in ('body', 'cylinder'):
            for grip in ('native', 'twohand'):
                model = {'parent': f'destiny:{KEY}_{part}',
                         'display': pose_display(source['display'], twohand, progress, part, grip, motion)}
                if part == 'cylinder' and extra != [source['elements'][i] for i in CYLINDER]:
                    model['elements'] = extra
                emit(ASSET/f'models/{KEY}_{frame:02}_{part}_{grip}.json', model)
        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [
                {'type': 'minecraft:model', 'model': f'destiny:{KEY}_{frame:02}_{part}_{grip}'}
                for part in ('body', 'cylinder')]}
        model = copy.deepcopy(item['model']) if frame in (0,INTERVALS) else {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}
        entries.append({'threshold': float32(progress), 'model': model})
    wrapper = copy.deepcopy(item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': list(FP), 'model': {'type': 'minecraft:range_dispatch',
            'property': 'minecraft:custom_model_data', 'index': 1, 'entries': entries,
            'fallback': copy.deepcopy(item['model'])}}], 'fallback': copy.deepcopy(item['model'])}
    emit(ASSET/f'items/{KEY}.json', wrapper)
    inputs = [MOTION, SOURCE, TWOHAND, ITEM, AUDIT, ASSET/'textures/item/weapon/ace_of_spades.png',
              Path('scripts/generate_ace_reload_w157.py'),
              Path('art/weapons/w83/references/gameplay-evidence.json'),
              Path('art/weapons/w83/references/youtube-YXSMO6Dk-r8-storyboard-L2-M0-raw.jpg')]
    emit(MANIFEST, {
        'stage': 'W198', 'generator': 'scripts/generate_ace_reload_w157.py',
        'itemModel': f'destiny:{KEY}', 'frames': SAMPLES, 'intervals': INTERVALS,
        'thresholdEncoding': 'float32(frame / 60), matching Java float division; +.001 activation offset remains in the same bucket', 'progressFloatIndex': 1, 'gripFlagIndex': 0,
        'firstPersonContexts': list(FP), 'sourceCubes': 87, 'bodyCubes': 66,
        'cylinderSourceCubes': 21, 'maxTransientCartridges': 6, 'maxAssembledElements': max(counts),
        'assembledElementsByFrame': counts, 'elementLimit': 1000,
        'cylinderIndices': list(CYLINDER), 'drumIndices': list(DRUM), 'axleIndices': list(AXLE),
        'yokeIndices': list(YOKE), 'cylinderSourceUuids': dict(zip(map(str,CYLINDER), CYLINDER_UUIDS)),
        'sourceStructure': 'Original flat 87 UUID outliner; no named groups. Explicit W83 index/UUID mapping audited against supplied Ace.bbmodel.',
        'externalSource': {'path': '/Users/qf/Downloads/Ace.bbmodel', 'sha256': audit['source']['sha256'], 'readOnly': True},
        'pivot': list(HINGE), 'gripPivot': list(GRIP), 'drumCenter': list(DRUM_CENTER),
        'rotationConvention': 'Rx Ry Rz; R_idle * C * R_neutral^-1 * R_source(t) * C^T * R_cylinder; model-space source translation and centred pivot offsets transformed by R_idle, then uniform accepted scale',
        'sourceMotionDataset': str(MOTION), 'bodyMotionTag': motion['clip']['tag'],
        'bodyMotionBone': BODY_BONE, 'motionBasis': {**motion['conversion'],
            'retiming': 'Linear source seconds = 4.2 * normalized runtime progress. 61 samples / 60 intervals; unchanged shortest-arc quaternion SLERP between adjacent evaluated 30fps poses, linear position.',
            'endpointBlend': 'Unchanged final 0.95..1 progress: SLERP to identity and translation to zero, smoothstep. Frame 0 and 60 use accepted displays byte-exactly. No interior motion warping.'},
        'authoredMechanicalKeyframes': MECHANICAL_KEYS, 'hybridAnimation': True, 'originalsUnchanged': True, 'handIK': False,
        'nativeGameplayVerified': False, 'mechanicsOrAudioChanged': False,
        'reference': {'url': 'https://www.youtube.com/watch?v=YXSMO6Dk-r8',
            'localStoryboard': 'art/weapons/w83/references/youtube-YXSMO6Dk-r8-storyboard-L2-M0-raw.jpg',
            'observations': 'Raised muzzle/handling at approximate 15s and 120s. Sparse 5s storyboard samples do not resolve exact reload phase timing.',
            'phaseBasis': 'Body uses evaluated Ace 80A8A567 source matrices. W157 cylinder/extractor/cartridges retain authored timings; their source hash-bone binding is unresolved.',
            'highResolutionActualFrameInspected': False},
        'offlinePreview': {'generatedForW197': False,
            'method': 'Source matrix/point checks and approximate FOV70 crop guard only; no W197 rendered or native screenshot.',
            'framing': 'Existing approximate drum crop guard passes; master native framing and contact review pending.'},
        'nativeCaptureMoments': [
            {'progress': 0, 'frame': 0, 'moment': 'original ready; both grip modes'},
            {'progress': .20, 'frame': 12, 'moment': 'tilted barrel and opening cylinder/yoke'},
            {'progress': .35, 'frame': 21, 'moment': 'fully open; extractor stroke and six ejected cases'},
            {'progress': .55, 'frame': 33, 'moment': 'six aligned loading cartridges approaching rear face'},
            {'progress': .70, 'frame': 42, 'moment': 'authored cylinder seated during source recovery; phase/contact unverified'},
            {'progress': .85, 'frame': 51, 'moment': 'source late recovery, check framing'},
            {'progress': 1, 'frame': 60, 'moment': 'exact original ready restoration; cancel/swap; non-FP fallback'}],
        'limitations': [
            'Hybrid: evaluated source body; authored W157 cylinder swing/extractor/cartridges. Unknown hash bones are not asserted to be cylinders.',
            'Six cartridge cuboids use original silver-metal UV; no brass repaint or per-round ammo mechanics.',
            'Neutral frame/basis and uniform source translation scale calibrated to accepted grip; no hands, IK or verified native hand contact. Source/mechanical phase alignment requires master capture.',
            'Native pack load, left/right hand reflection, 10-20 displays, deadline/audio sync and runtime routing remain master QA.',
            'Vanilla held-item component updates remain limited to 20 TPS; the dense bank does not add per-render blending.'],
        'sourceSha256': {str(p): sha((root/p).read_bytes()) for p in inputs},
        'sha256': {str(p.relative_to(root)): sha(v) for p,v in output.items()},
    })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='read-only deterministic byte comparison')
    parser.add_argument('--extract-source', type=Path, help='read pinned W196 gzip and write compact owned dataset')
    parser.add_argument('--source-map', type=Path, help='read-only Ace source-map.json for extraction')
    args = parser.parse_args()
    if args.extract_source:
        if args.verify or not args.source_map:
            parser.error('--extract-source requires --source-map and cannot use --verify')
        dataset = extract_source(args.extract_source, args.source_map)
        target = ROOT/MOTION
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((json.dumps(dataset, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n').encode())
    outputs = generate()
    for path, data in outputs.items():
        if args.verify:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f'W157 asset differs: {path.relative_to(ROOT)}')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'{"Verified" if args.verify else "Generated"} {len(outputs)} W198 Ace product files (W157 namespace)')


if __name__ == '__main__':
    main()
