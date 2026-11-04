#!/usr/bin/env python3
"""W204/W209 shared, fingerless arm segments for BetterModel 3.5.1 colors.

API: generated() -> {absolute Path: bytes}; arm_nodes(side, display, outputs, segment='forearm')
adds two inherited pose models to outputs and returns the ready/slim graph.
Neither function writes files or executes W201's generator. Default RGB data
uses the official 26.3 client JAR textures; Pillow is needed for that step.

UV mapping adapted from toxicity188/BetterModel, commit
4128f2cea38e06690626d8b81afedad014af525f (SkinManagerImpl.kt), and
 toxicity188/DynamicUV, commit 07be63631285f5b3eb4bd7179eb769b82e6d5a04
(UVFace, UVPos, UVAxis, UVElement, UVMappedFace).
Copyright (c) 2024-2026 toxicity188 (BetterModel)
Copyright (c) 2025 toxicity188 (DynamicUV)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import copy
import hashlib
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'src/main/resources/assets/destiny'
PREFIX = 'skin_arm_w204/'
LAYOUT = ROOT / 'art/weapons/w204/skin-layout.json'
DEFAULTS = ROOT / 'src/main/resources/destiny/weapons/w204-default-skin-arms.json'
SOURCES = ROOT / 'art/weapons/w204/default-skin-sources.json'
# Read-only official client JAR. No individual skin texture/pack is emitted.
DEFAULT_INPUTS = Path.home() / '.gradle/caches/fabric-loom/26.3/minecraft-client.jar'
FACE_ORDER = ('north', 'south', 'east', 'west', 'down')
UPPER_FACE_ORDER = ('north', 'south', 'east', 'west', 'up')
SIDES = ('right', 'left')
VARIANTS = ('classic', 'slim')
SEGMENTS = ('forearm', 'upper')
OFFSETS = {'right': 64, 'left': 192}
UPPER_OFFSETS = {'right': 320, 'left': 448}
READY_FLAG, SLIM_FLAG, COLOR_STRIDE = 8, 9, 128
DEFAULT_NAMES = ('alex', 'ari', 'efe', 'kai', 'makena', 'noor', 'steve', 'sunny', 'zuri')


def enc(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _check(side, variant, segment='forearm'):
    if side not in SIDES or variant not in VARIANTS or segment not in SEGMENTS:
        raise ValueError('Expected right/left, classic/slim and forearm/upper')


def origin_uv(side, variant, segment='forearm'):
    """Exact BM UVPos origins for its base and sleeve arm elements."""
    _check(side, variant, segment)
    w = 3 if variant == 'slim' else 4
    u, v = (44, 26) if side == 'right' else (36, 58)
    if segment == 'upper':
        v -= 6
    faces = UPPER_FACE_ORDER if segment == 'upper' else FACE_ORDER
    cap = (u, v - 4) if segment == 'upper' else (u + w, v - 10)
    base = dict(zip(faces, ((u, v), (u + w + 4, v), (u - 4, v),
                           (u + w, v), cap)))
    du, dv = (0, 16) if side == 'right' else (16, 0)
    sleeve = {f: (x + du, y + dv) for f, (x, y) in base.items()}
    return base, sleeve


def _plane(face, u, v, width):
    """UVFace/UVAxis orientation in skin units before adaptation (Y -6..0)."""
    h = width / 2
    if face == 'north':
        return (h-u, -v, -2), (h-u-1, -v-1, -2)
    if face == 'south':
        return (-h+u, -v, 2), (-h+u+1, -v-1, 2)
    if face == 'east':
        return (h, -v, 2-u), (h, -v-1, 1-u)
    if face == 'west':
        return (-h, -v, -2+u), (-h, -v-1, -1+u)
    if face == 'up':
        return (h-u, 0, 2-v), (h-u-1, 0, 1-v)
    return (h-u, -6, 2-v), (h-u-1, -6, 1-v)


def _adapt(point, segment='forearm'):
    # Rotate 180 degrees about Z, then scale/translate to W201's (8,8,8)
    # contact frame. Forearm: hand Y=9, elbow Y=1.5. Upper: shoulder Y=.5,
    # elbow Y=8. Positive scales after Z180 preserve the whole arm's normals.
    x, y, z = point
    origin_y = .5 if segment == 'upper' else 1.5
    return [round(8 - .6*x, 8), round(origin_y - 1.25*y, 8), round(8 + .6*z, 8)]


def pixel_layout(side, variant, segment='forearm'):
    """Tint order: enum face order; image X outer, image Y inner (DOWN: X/Z)."""
    _check(side, variant, segment)
    width = 3 if variant == 'slim' else 4
    base, sleeve = origin_uv(side, variant, segment)
    faces = UPPER_FACE_ORDER if segment == 'upper' else FACE_ORDER
    offsets = UPPER_OFFSETS if segment == 'upper' else OFFSETS
    result = []
    face_after_z180 = dict(zip(FACE_ORDER, ('north', 'south', 'west', 'east', 'up')))
    face_after_z180['up'] = 'down'
    for face in faces:
        columns = 4 if face in ('east', 'west') else width
        rows = 4 if face in ('up', 'down') else 6
        for u in range(columns):
            for v in range(rows):
                a, b = (_adapt(p, segment) for p in _plane(face, u, v, width))
                i = len(result)
                result.append({'tintindex': i, 'cmdIndex': offsets[side] + i,
                    'sourceFace': face, 'face': face_after_z180[face],
                    'facePixel': [u, v],
                    'baseUV': [base[face][0]+u, base[face][1]+v],
                    'sleeveUV': [sleeve[face][0]+u, sleeve[face][1]+v],
                    'from': [min(a[k], b[k]) for k in range(3)],
                    'to': [max(a[k], b[k]) for k in range(3)]})
    return result


def common_model(side, variant, segment='forearm'):
    credit = ('W209 genuine upper arm' if segment == 'upper' else 'W204 fingerless forearm')
    return {'credit': credit + '; BetterModel/DynamicUV MIT; see skin-layout.json.',
            'ambientocclusion': False,
            'textures': {'0': 'destiny:item/skin_arm_w204/white',
                         'particle': 'destiny:item/skin_arm_w204/white'},
            'elements': [{'from': p['from'], 'to': p['to'], 'shade': False,
                          'faces': {p['face']: {'uv': [0, 0, 16, 16],
                                              'texture': '#0', 'tintindex': p['tintindex']}}}
                         for p in pixel_layout(side, variant, segment)]}


def arm_nodes(side, display, outputs, segment='forearm'):
    """Return ready(flag8) -> slim(flag9) -> two shared-parent model refs.

    outputs is a mutable Path->bytes map, matching W201's generator convention.
    display is copied verbatim, preserving inherited W201 contact frames.
    Upper models use the supplied display unchanged: source-driven placement and
    ordinary source length / 7.5 scaling belong to the caller.
    """
    _check(side, 'classic', segment)
    offsets = UPPER_OFFSETS if segment == 'upper' else OFFSETS
    suffix = '_upper' if segment == 'upper' else ''
    refs = {}
    for variant in VARIANTS:
        record = {'parent': f'destiny:{PREFIX}{side}{suffix}_{variant}',
                  'display': copy.deepcopy(display)}
        data = enc(record)
        key = f'{PREFIX}poses/{side}{suffix}_{variant}_{digest(data)[:24]}'
        path = A / f'models/{key}.json'
        if path in outputs and outputs[path] != data:
            raise ValueError('Pose hash collision: ' + key)
        outputs[path] = data
        count = 96 if variant == 'slim' else 112
        refs[variant] = {'type': 'minecraft:model', 'model': 'destiny:' + key,
                         'tints': [{'type': 'minecraft:custom_model_data',
                                    'index': offsets[side]+i, 'default': 0xFFFFFF}
                                   for i in range(count)]}
    return {'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data',
            'index': READY_FLAG, 'on_false': {'type': 'minecraft:empty'},
            'on_true': {'type': 'minecraft:condition',
                        'property': 'minecraft:custom_model_data', 'index': SLIM_FLAG,
                        'on_true': refs['slim'], 'on_false': refs['classic']}}


def _white_png():
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind+body))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff\xff', 9)) + chunk(b'IEND', b''))


def flatten_rgb(base, sleeve):
    """BM round(alpha/255*2): 0=base, 1=half overlay, 2=opaque sleeve.

    Integer half-up channel rounding makes the CPU contract deterministic.
    RGB ignores the base alpha, matching DynamicUV's RGB element.
    """
    level = (sleeve[3]*2 + 127) // 255
    channels = [(base[c]*(2-level) + sleeve[c]*level + 1)//2 for c in range(3)]
    return (channels[0] << 16) | (channels[1] << 8) | channels[2]


def default_skin_files(layout, input_dir=DEFAULT_INPUTS):
    from PIL import Image
    from io import BytesIO
    from zipfile import ZipFile
    input_dir = Path(input_dir)
    archive = ZipFile(input_dir) if input_dir.is_file() else None
    skins, inputs = [], []
    # Vanilla 26.3 DefaultPlayerSkin static initializer and get(UUID), javap
    # verified against ~/.gradle/caches/fabric-loom/26.3/minecraft-client.jar.
    for folder, variant in (('slim', 'slim'), ('wide', 'classic')):
        for name in DEFAULT_NAMES:
            path = Path(input_dir) / folder / (name + '.png')
            data = archive.read(f'assets/minecraft/textures/entity/player/{folder}/{name}.png') if archive else path.read_bytes()
            with Image.open(BytesIO(data)) as image:
                if image.size != (64, 64):
                    raise ValueError('Expected official 64x64 default skin: ' + str(path))
                rgba = image.convert('RGBA')
                entry = {'index': len(skins), 'name': name, 'slim': variant == 'slim'}
                for side in SIDES:
                    for segment in SEGMENTS:
                        suffix = '_upper' if segment == 'upper' else ''
                        field = side + ('Upper' if segment == 'upper' else '')
                        pixels = layout['variants'][f'{side}{suffix}_{variant}']['pixels']
                        entry[field+'Bare'] = [flatten_rgb(rgba.getpixel(tuple(p['baseUV'])), (0,0,0,0)) for p in pixels]
                        entry[field] = [flatten_rgb(rgba.getpixel(tuple(p['baseUV'])),
                                                   rgba.getpixel(tuple(p['sleeveUV']))) for p in pixels]
            skins.append(entry)
            inputs.append({'index': entry['index'], 'name': name, 'slim': entry['slim'],
                'inputArchive': input_dir.name if archive else 'official-default-PNG', 'sha256': digest(data),
                'vanillaTexture': f'minecraft:textures/entity/player/{folder}/{name}.png'})
    if archive: archive.close()
    resource = {'schemaVersion': 1, 'selection': 'Math.floorMod(uuid.hashCode(), 18)',
                'colorOffsets': OFFSETS, 'upperColorOffsets': UPPER_OFFSETS, 'colorStride': COLOR_STRIDE,
                'readyFlag': READY_FLAG, 'slimFlag': SLIM_FLAG,
                'colorEncoding': 'unsigned RGB 0xRRGGBB integers',
                'sleeveComposite': 'round(alpha/255*2) -> 0, 1/2, 1; half-up RGB rounding',
                'skins': skins}
    provenance = {'schemaVersion': 1, 'generator': 'scripts/skin_arm_models_w204.py',
                  'inputPolicy': 'Official 26.3 client JAR skin textures; common RGB data, no per-player pack.',
                  'selectionEvidence': 'MC 26.3 DefaultPlayerSkin javap: get(UUID), static initializer',
                  'uuidHash': 'Java UUID.hashCode: signed32(msb ^ (msb >>> 32) ^ lsb ^ (lsb >>> 32))',
                  'selection': resource['selection'], 'sources': inputs,
                  'upperSkinMapping': 'BetterModel rightArm/leftArm: six upper side rows and UP shoulder cap; genuine base and sleeve UVs.',
                  'resourceSha256': digest(enc(resource))}
    return {DEFAULTS: enc(resource), SOURCES: enc(provenance)}


def generated(include_defaults=False):
    """Return ten shared asset/layout files; no filesystem mutation.

    include_defaults=True additionally regenerates the two frozen RGB/provenance
    resources from the official client JAR (requires Pillow). Normal generation
    uses the frozen common RGB resource and needs neither Pillow nor that JAR.
    """
    layout = {'schemaVersion': 1, 'generator': 'scripts/skin_arm_models_w204.py',
        'betterModelVersion': '3.5.1', 'colorOffsets': OFFSETS,
        'upperColorOffsets': UPPER_OFFSETS, 'colorStride': COLOR_STRIDE,
        'readyFlag': READY_FLAG, 'slimFlag': SLIM_FLAG, 'faceOrder': list(FACE_ORDER),
        'pixelOrder': 'image X outer, image Y inner; DOWN image X outer, image Z inner',
        'geometry': {'contactOrigin': [8, 8, 8], 'skinToLocal': ['8 - 0.6*x', '1.5 - 1.25*y', '8 + 0.6*z'],
                     'skinBoundsY': [-6, 0], 'localBoundsY': [1.5, 9],
                     'classicWidth': 2.4, 'slimWidth': 1.8, 'depth': 2.4,
                     'rotationZ': 180, 'fingers': False, 'sleeveGeometry': False},
        'upperFaceOrder': list(UPPER_FACE_ORDER),
        'upperGeometry': {'elbowJoint': [8, 8, 8], 'shoulderJoint': [8, .5, 8],
                          'skinToLocal': ['8 - 0.6*x', '0.5 - 1.25*y', '8 + 0.6*z'],
                          'skinBoundsY': [-6, 0], 'localBoundsY': [.5, 8],
                          'length': 7.5, 'classicWidth': 2.4, 'slimWidth': 1.8, 'depth': 2.4,
                          'rotationZ': 180, 'shoulderCap': True, 'elbowCap': False,
                          'fingers': False, 'sleeveGeometry': False},
        'attribution': [
            {'project': 'BetterModel', 'url': 'https://github.com/toxicity188/BetterModel',
             'commit': '4128f2cea38e06690626d8b81afedad014af525f',
             'source': 'core/src/main/kotlin/kr/toxicity/model/manager/SkinManagerImpl.kt',
             'copyright': 'Copyright (c) 2024-2026 toxicity188', 'license': 'MIT'},
            {'project': 'DynamicUV', 'url': 'https://github.com/toxicity188/DynamicUV',
             'commit': '07be63631285f5b3eb4bd7179eb769b82e6d5a04',
             'sources': ['UVFace.java', 'UVPos.java', 'UVAxis.java', 'UVElement.java', 'UVMappedFace.java'],
             'copyright': 'Copyright (c) 2025 toxicity188', 'license': 'MIT'}],
        'licenseText': __doc__[__doc__.index('Permission is hereby granted'):].strip(),
        'variants': {}}
    outputs = {A / 'textures/item/skin_arm_w204/white.png': _white_png()}
    for side in SIDES:
        for variant in VARIANTS:
            for segment in SEGMENTS:
                suffix = '_upper' if segment == 'upper' else ''
                key = f'{side}{suffix}_{variant}'
                base, sleeve = origin_uv(side, variant, segment)
                pixels = pixel_layout(side, variant, segment)
                layout['variants'][key] = {'pixelCount': len(pixels),
                    'originUV': {'base': base, 'sleeve': sleeve}, 'pixels': pixels}
                outputs[A / f'models/{PREFIX}{key}.json'] = enc(common_model(side, variant, segment))
    outputs[LAYOUT] = enc(layout)
    if include_defaults:
        outputs.update(default_skin_files(layout))
    return outputs
