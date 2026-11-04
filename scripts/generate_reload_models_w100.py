#!/usr/bin/env python3
"""W100 Recluse assets: data-only FBX partition audit and reference-gated reload.

No Blender/Blockbench imports, scene execution, downloads or original-file writes.
"""
import argparse
import collections
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import runpy
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w100'
CACHE = Path('/tmp/destiny-weapons-w30/raw/the_recluse/extracted')
ARCHIVE_SHA256 = 'e0d378d31f58e758e3bcedc612fc5d2f81a469882d38668636479f6d6416efd4'
KEY = 'weapon_reload_w100/the_recluse'
SOURCE = ASSETS / 'models/weapon/submachine_gun/the_recluse.json'
BBMODEL = ROOT / 'art/blockbench/weapons/w30/the_recluse.bbmodel'
MAGAZINE_COMPONENT = ('Mesh_0007.rip', 1)
MAGAZINE_COMPONENTS = {MAGAZINE_COMPONENT}
PARTITION_IDENTIFICATION = 'geometric lower-cartridge proxy; exact physical magazine boundary remains occluded and semantically unlabelled'
MAGAZINE = [2, 3, 4, 44, 56, 62, 63, 65, 72, 77, 78, 81, 83, 84,
            141, 144, 156, 161, 162, 163, 167, 173, 178, 183]
# Authored only after reading the Master notes and actual 37.30/40/50/60 frames.
# Observed: raise/roll, lower-right small ejection, underside hand, ready return.
# Values/normalized timings/local path are authored, not recovered animation.
# progress, body rotation delta, body translation delta, local cartridge offset.
KEYS = [
    (0, [0, 0, 0], [0, 0, 0], [0, 0, 0]),
    (.12, [18, -8, 12], [-.4, -.1, -.25], [0, 0, 0]),
    (.24, [30, -12, 22], [-.8, .1, -.5], [.8, -2.8, .2]),
    (.40, [33, -14, 23], [-.9, .25, -.65], [1.3, -6, .5]),
    (.52, [31, -12, 21], [-.9, .25, -.65], [1.3, -6, .5]),
    (.68, [30, -10, 20], [-.75, .2, -.5], [.4, -2.4, .2]),
    (.78, [34, -9, 18], [-.65, .35, -.4], [0, 0, 0]),
    (.86, [25, -6, 13], [-.4, .2, -.3], [0, 0, 0]),
    (1, [0, 0, 0], [0, 0, 0], [0, 0, 0]),
]
REFERENCE_SHA256 = 'd053f015e48e83e96d880e0ccc1a32108b004475edb8145f351ea75555079da0'
PROVENANCE_SHA256 = '8386d29206ea7a1831a03c45dc6cecc5d731cfcac4dc37841c6f5dabafcaede4'
# These pre-W100 pins are literal inputs, not regenerated from current disk.
ORIGINALS = {
    'src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse.json':
        'b338c341d40234e39356ca70f47594e5d625c6521f102ea417a06956d33f73ae',
    'src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_ads.json':
        '7704b4118c8d119bd5f6143a3ba1b81307567e5580d8db719fa9dbab9dce95ba',
    'src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_ads_twohand.json':
        '164d204387f178bf6080a804a3931312c640493b8fdb60df9f9191c9fcc5da4b',
    'src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_inspect.json':
        'ad838bf2766050006c06d6327703cb653044c3bc8ec49842844c5fc7776ead51',
    'src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_inspect_twohand.json':
        'a316abfddee965dc1842ba7930b75dc8420f0f1754fe2b64874e70a590e8808e',
    'src/main/resources/assets/destiny/models/weapon/submachine_gun/the_recluse_twohand.json':
        'cfcb4ffe8ab00cdff8d43e89421513033018294c8b25021c82def1fd5bc0ba32',
    'src/main/resources/assets/destiny/items/weapon/the_recluse.json':
        '74132a108fd993aff0a5e2904889372ac3e9e0f584420ddf4e06e852e79c7d00',
    'src/main/resources/assets/destiny/textures/item/weapon/w30/the_recluse.png':
        'f3aad8fd07a4af6d7a368f02baf5ea695f15f7a6bedb4b41ed4af6c12ae357a3',
    'art/blockbench/weapons/w30/the_recluse.bbmodel':
        '9d922885fd0055eba9ae83974df9938cceade443ae2a349e8afc7c610331f3a0',
    'scripts/build_weapons_w30.py':
        'e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83',
    'scripts/generate_reload_models_w69.py':
        'ac4b51364886b790a9a60fd01b53a9247249a9f592584f9865f4136de286cb4c',
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def parse_fbx(path):
    """Read pinned binary FBX 7400 arrays/nodes as inert data, never execute it."""
    data = path.read_bytes()
    assert data[:23] == b'Kaydara FBX Binary  \x00\x1a\x00'
    assert struct.unpack_from('<I', data, 23)[0] == 7400

    def node(pos):
        end, count, size, length = struct.unpack_from('<IIIB', data, pos)
        pos += 13
        if end == 0:
            return None, pos
        name = data[pos:pos + length].decode()
        pos += length
        properties = []
        for _ in range(count):
            kind = chr(data[pos])
            pos += 1
            if kind in 'YCFDIL':
                fmt = {'Y': 'h', 'C': '?', 'I': 'i', 'F': 'f', 'D': 'd', 'L': 'q'}[kind]
                value = struct.unpack_from('<' + fmt, data, pos)[0]
                pos += struct.calcsize(fmt)
            elif kind in 'SR':
                length = struct.unpack_from('<I', data, pos)[0]
                pos += 4
                value = data[pos:pos + length]
                pos += length
                if kind == 'S':
                    value = value.decode(errors='replace')
            elif kind in 'fdlibc':
                length, compression, byte_count = struct.unpack_from('<III', data, pos)
                pos += 12
                raw = data[pos:pos + byte_count]
                pos += byte_count
                assert compression in (0, 1)
                if compression:
                    raw = zlib.decompress(raw)
                fmt = {'f': 'f', 'd': 'd', 'l': 'q', 'i': 'i', 'b': '?', 'c': 'b'}[kind]
                value = struct.unpack('<' + str(length) + fmt, raw)
            else:
                raise ValueError('Unsupported FBX property: ' + kind)
            properties.append(value)
        children = []
        while pos < end - 13:
            child, pos = node(pos)
            assert child is not None
            children.append(child)
        return (name, properties, children), end

    roots, pos = [], 27
    while pos < len(data):
        value, pos = node(pos)
        if value is None:
            break
        roots.append(value)
    return roots


def bounds(points):
    return [[min(p[a] for p in points) for a in range(3)],
            [max(p[a] for p in points) for a in range(3)]]


def source_meshes(cache=CACHE):
    """FBX vertex arrays already use Blender's Z-up source basis, metres.

    The export's shared -90deg X / 100 scale is its Y-up centimetre carrier.
    Pin/validate it, then apply the exact W30 source-axis/scale/anchor mapping.
    """
    bb = json.loads(BBMODEL.read_bytes())['destiny_w30']
    assert sha((cache.parent / 'source.archive').read_bytes()) == ARCHIVE_SHA256, 'Original archive drift'
    for name, pin in bb['source_files'].items():
        assert sha((cache / name).read_bytes()) == pin, 'Source drift: ' + name
    roots = parse_fbx(cache / 'Recluse.fbx')
    objects = next(n[2] for n in roots if n[0] == 'Objects')
    links = [n[1][1:] for root in roots if root[0] == 'Connections'
             for n in root[2] if n[1][0] == 'OO']
    models = {n[1][0]: n for n in objects if n[0] == 'Model'}
    meshes = []
    for node in objects:
        if node[0] != 'Geometry':
            continue
        geometry_id, label, kind = node[1]
        assert kind == 'Mesh'
        model_id = next(parent for child, parent in links if child == geometry_id)
        model = models[model_id]
        assert [parent for child, parent in links if child == model_id] == [0]
        properties = {p[1][0]: p[1][4:] for c in model[2] if c[0] == 'Properties70' for p in c[2]}
        assert all(abs(a - b) < 1e-4 for a, b in zip(properties['Lcl Rotation'], [-90, 0, 0]))
        assert properties['Lcl Scaling'] == [100, 100, 100]
        assert properties.get('Lcl Translation', [0, 0, 0]) == [0, 0, 0]
        children = {c[0]: c for c in node[2]}
        values = children['Vertices'][1][0]
        vertices = list(zip(values[::3], values[1::3], values[2::3]))
        mapped = [[-p[1] * bb['scale'] + 8, p[2] * bb['scale'] + 8,
                   -p[0] * bb['scale'] + 8] for p in vertices]
        faces, face = [], []
        for index in children['PolygonVertexIndex'][1][0]:
            face.append(index if index >= 0 else -index - 1)
            if index < 0:
                assert len(face) == 3
                faces.append(tuple(face))
                face = []
        assert not face
        # Weld coincident UV seam vertices only for topology classification.
        parent = list(range(len(vertices)))

        def root(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(a, b):
            parent[root(a)] = root(b)

        seen = {}
        for i, point in enumerate(vertices):
            key = tuple(round(v, 6) for v in point)
            if key in seen:
                union(i, seen[key])
            seen[key] = i
        for a, b, c in faces:
            union(a, b)
            union(a, c)
        groups = collections.defaultdict(list)
        for face in faces:
            groups[root(face[0])].append(face)
        components = sorted(groups.values(), key=lambda fs: (-len(fs), min(min(f) for f in fs)))
        meshes.append(dict(name=model[1][1].split('\x00')[0], geometryId=geometry_id,
                           vertices=mapped, faces=faces, components=components))
    assert sum(len(m['faces']) for m in meshes) == bb['source_triangles'] == 20369
    source_bounds = bounds([v for m in meshes for v in m['vertices']])
    assert all(abs(source_bounds[i][a] - bb['model_bounds'][i][a]) < 1e-5
               for i in range(2) for a in range(3)), source_bounds
    return meshes


def describe_source():
    for mesh in source_meshes():
        print(mesh['name'], len(mesh['faces']), 'triangles', len(mesh['components']), 'components')
        for i, faces in enumerate(mesh['components']):
            if len(faces) >= 6:
                points = [mesh['vertices'][v] for f in faces for v in f]
                print(' ', i, len(faces), [[round(v, 4) for v in row] for row in bounds(points)])


def clip_polygon(polygon, axis, edge, sign):
    """Sutherland-Hodgman clipping against an actual cuboid half-space."""
    result = []
    for i, point in enumerate(polygon):
        previous = polygon[i - 1]
        a = (point[axis] - edge) * sign
        b = (previous[axis] - edge) * sign
        if (a >= 0) != (b >= 0):
            result.append([previous[k] + (point[k] - previous[k]) * b / (b - a)
                           for k in range(3)])
        if a >= 0:
            result.append(point)
    return result


def polygon_area(polygon):
    total = 0
    for i in range(1, len(polygon) - 1):
        u = [polygon[i][a] - polygon[0][a] for a in range(3)]
        v = [polygon[i + 1][a] - polygon[0][a] for a in range(3)]
        total += math.sqrt(sum((u[(a + 1) % 3] * v[(a + 2) % 3]
                                - u[(a + 2) % 3] * v[(a + 1) % 3]) ** 2
                               for a in range(3))) * .5
    return total


def partition_audit(meshes, original):
    triangles, components = [], []
    for mesh in meshes:
        face_indices = {face: i for i, face in enumerate(mesh['faces'])}
        for ci, faces in enumerate(mesh['components']):
            points = [mesh['vertices'][v] for face in faces for v in face]
            components.append(dict(mesh=mesh['name'], component=ci, triangleCount=len(faces),
                                   modelBounds=bounds(points),
                                   sourcePolygonIndices=[face_indices[face] for face in faces]))
            for face in faces:
                points = [mesh['vertices'][v] for v in face]
                triangles.append(((mesh['name'], ci), points, bounds(points)))
    rows = []
    for index, cube in enumerate(original['elements']):
        votes = collections.defaultdict(float)
        for component, polygon, (low, high) in triangles:
            # Bounds reject impossible candidates only; all positive evidence is
            # exact clipped 3D triangle area, never a bounds/centroid vote.
            if any(high[a] < cube['from'][a] or low[a] > cube['to'][a] for a in range(3)):
                continue
            for axis in range(3):
                polygon = clip_polygon(polygon, axis, cube['from'][axis], 1)
                polygon = clip_polygon(polygon, axis, cube['to'][axis], -1)
                if not polygon:
                    break
            area = polygon_area(polygon)
            if area > 1e-10:
                votes[component] += area
        total = sum(votes.values())
        magazine = sum(v for k, v in votes.items() if k in MAGAZINE_COMPONENTS)
        share = magazine / total if total else 0
        selected = share > .5
        assert selected == (index in MAGAZINE), (index, share)
        rows.append(dict(index=index, part='magazine' if selected else 'body',
                         from_=cube['from'], to=cube['to'],
                         originalElementSha256=sha(encode(cube)),
                         totalClippedSourceArea=total, magazineClippedSourceArea=magazine,
                         magazineAreaShare=share,
                         mixed=magazine > 1e-8 and total - magazine > 1e-8,
                         sourceComponents=[dict(mesh=k[0], component=k[1], clippedArea=v)
                                           for k, v in sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))]))
    total_magazine = sum(r['magazineClippedSourceArea'] for r in rows)
    carried_magazine = sum(r['magazineClippedSourceArea'] for r in rows if r['part'] == 'magazine')
    carried_other = sum(r['totalClippedSourceArea'] - r['magazineClippedSourceArea']
                        for r in rows if r['part'] == 'magazine')
    raw_magazine_area = sum(polygon_area(points) for component, points, _ in triangles
                            if component in MAGAZINE_COMPONENTS)
    hypotheses = []
    for name, selected_components in [
        ('central pistol-grip shape', {('Mesh_0007.rip', 1)}),
        ('forward curved main component', {('Mesh_0007.rip', 0)}),
        ('forward curved component plus coincident baseplate and details',
         {('Mesh_0007.rip', 0), ('Mesh_0004.rip', 2), ('Mesh_0001.rip', 2),
          *[('Mesh_0003.rip', i) for i in (9, 10, 11, 12)]})]:
        selected_indices = []
        mixed_indices = []
        for row in rows:
            area = sum(c['clippedArea'] for c in row['sourceComponents']
                       if (c['mesh'], c['component']) in selected_components)
            if area > row['totalClippedSourceArea'] * .5:
                selected_indices.append(row['index'])
                if row['totalClippedSourceArea'] - area > 1e-8:
                    mixed_indices.append(row['index'])
        hypotheses.append(dict(name=name, sourceComponents=[dict(mesh=m, component=i)
                                for m, i in sorted(selected_components)],
                               majorityAreaCubeIndices=selected_indices,
                               cubeCount=len(selected_indices), mixedSelectedIndices=mixed_indices))
    return dict(stage='W100', partitionStatus=PARTITION_IDENTIFICATION,
                sourceCubes=217, bodyCubes=217 - len(MAGAZINE), magazineSourceCubes=len(MAGAZINE),
                compositeCubes=217, magazineIndices=MAGAZINE,
                bodyIndices=[i for i in range(217) if i not in MAGAZINE],
                classification='strict majority of actual source triangle area clipped inside each original cube',
                boundsUsedOnlyForBroadPhase=True, clippingEpsilon=1e-10,
                sourceIdentification=dict(archiveDriveId='1LRTAvTc70Sq8QLSLHqdYf7uX6MD_l72j',
                    archiveName='The Recluse.rar', localCache=str(CACHE),
                    sourceArchiveSha256=ARCHIVE_SHA256,
                    sourceSha256=json.loads(BBMODEL.read_bytes())['destiny_w30']['source_files'],
                    sourceTriangles=20369, sourceMeshes=13,
                    parser='binary FBX 7400 inert data; no Blender/Blockbench execution',
                    sourceToModel='(-Y, Z, -X) * 32.58849594479781 + (8, 8, 8)',
                    weldedCoordinateDecimalPlaces=6,
                    magazineMesh=MAGAZINE_COMPONENT[0], magazineComponent=MAGAZINE_COMPONENT[1],
                    selectedComponents=[dict(mesh=m, component=i) for m, i in sorted(MAGAZINE_COMPONENTS)],
                    magazineTriangles=sum(c['triangleCount'] for c in components
                                          if (c['mesh'], c['component']) in MAGAZINE_COMPONENTS)),
                componentIdentificationHypotheses=hypotheses,
                conservation=dict(all217IndicesExactlyOnce=True, wholeElementsOnly=True,
                    allFacesAndUVAndTexturesUnchanged=True, newFaces=0, newTextures=0,
                    sourceElementSequenceRestorable=True),
                approximation=dict(wholeCubePartition=True,
                    capturedMagazineSourceAreaFraction=carried_magazine / total_magazine,
                    capturedMagazineSourceAreaFractionBasis='selected-part source area / source area clipped inside all original cubes',
                    capturedRawComponentAreaFraction=carried_magazine / raw_magazine_area,
                    rawComponentArea=raw_magazine_area, allCubeClippedComponentArea=total_magazine,
                    selectedCubeClippedComponentArea=carried_magazine,
                    carriedFixedSourceArea=carried_other,
                    mixedSelectedIndices=[r['index'] for r in rows if r['mixed'] and r['part'] == 'magazine'],
                    mixedRetainedIndices=[r['index'] for r in rows if r['mixed'] and r['part'] == 'body'],
                    explanation='Original cubes merge surfaces from separate ripped components. Strict area majority keeps every original element intact; mixed seam cubes necessarily approximate the source part boundary. No cube splitting, new closure faces, or UV rebake.'),
                sourceComponents=components, cubes=rows)


# Tiny raster font keeps the audit PNG deterministic and dependency-free.
FONT = dict(zip('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ:-./ ', [
    '111101101101111','010110010010111','111001111100111','111001111001111','101101111001001',
    '111100111001111','111100111101111','111001001001001','111101111101111','111101111001111',
    '010101111101101','110101110101110','111100100100111','110101101101110','111100110100111',
    '111100110100100','111100101101111','101101111101101','111010010010111','001001001101111',
    '101101110101101','100100100100111','101111111101101','101111111111101','111101101101111',
    '111101111100100','111101101111001','110101110101101','111100111001111','111010010010010',
    '101101101101111','101101101101010','101101111111101','101101010101101','101101010010010',
    '111001010100111','000010000010000','000000111000000','000000000000010','001001010100100',
    '000000000000000']))


def audit_png(meshes, audit, original):
    """Side projections of actual triangles versus unchanged source cube edges."""
    width, height = 1500, 950
    pixels = bytearray([17, 23, 34] * width * height)

    def pixel(x, y, color):
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 3
            pixels[offset:offset + 3] = bytes(color)

    def line(a, b, color):
        x, y = a
        dx, dy = b[0] - x, b[1] - y
        steps = max(abs(dx), abs(dy), 1)
        for i in range(steps + 1):
            pixel(round(x + dx * i / steps), round(y + dy * i / steps), color)

    def text(x, y, value, color=(223, 232, 245), scale=3):
        for char in value:
            glyph = FONT.get(char, FONT[' '])
            for i, bit in enumerate(glyph):
                if bit == '1':
                    for dy in range(scale):
                        for dx in range(scale):
                            pixel(x + i % 3 * scale + dx, y + i // 3 * scale + dy, color)
            x += 4 * scale

    body, magazine, mixed = (93, 121, 154), (64, 230, 184), (255, 174, 74)
    text(30, 25, 'W100 RECLUSE / SOURCE TRIANGLE PARTITION AUDIT', scale=5)
    text(30, 65, 'LOWER CARTRIDGE PROXY / PHYSICAL PART ID APPROXIMATE / STATIC AUDIT')
    text(30, 105, 'SOURCE FBX / 20369 TRIANGLES / GREEN CANDIDATE COMPONENT')
    text(770, 105, f'217 ORIGINAL CUBES / {len(MAGAZINE)} SELECTED / {217-len(MAGAZINE)} RETAINED')
    for panel in range(2):
        offset = 35 + panel * 740

        def project(v):
            return (round(offset + (v[2] + 3) * 34), round(470 - (v[1] - 5) * 34))

        if panel == 0:
            # Draw the selected component last so its real silhouette is visible.
            layers = []
            for mesh in meshes:
                for ci, faces in enumerate(mesh['components']):
                    selected = (mesh['name'], ci) in MAGAZINE_COMPONENTS
                    layers.append((selected, mesh, faces))
            for selected, mesh, faces in sorted(layers, key=lambda row: row[0]):
                for face in faces:
                    p = [project(mesh['vertices'][v]) for v in face]
                    for i in range(3):
                        line(p[i - 1], p[i], magazine if selected else body)
        else:
            for row in sorted(audit['cubes'], key=lambda r: r['part'] == 'magazine'):
                cube = original['elements'][row['index']]
                points = [project(v) for v in itertools.product(*zip(cube['from'], cube['to']))]
                x0, x1 = min(p[0] for p in points), max(p[0] for p in points)
                y0, y1 = min(p[1] for p in points), max(p[1] for p in points)
                color = magazine if row['part'] == 'magazine' else body
                if row['mixed']:
                    color = mixed
                for a, b in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                             ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
                    line(a, b, color)
    text(35, 510, 'CANDIDATE COMPONENT / ENLARGED ACTUAL TRIANGLES')
    text(775, 510, 'SELECTED CUBES / MIXED SEAMS AMBER / ORIGINAL INDICES')
    for panel in range(2):
        offset = 65 + panel * 740

        def project(v):
            return (round(offset + (v[2] - 7) * 170), round(880 - (v[1] - 6) * 85))

        if panel == 0:
            for name, ci in sorted(MAGAZINE_COMPONENTS):
                mesh = next(m for m in meshes if m['name'] == name)
                for face in mesh['components'][ci]:
                    p = [project(mesh['vertices'][v]) for v in face]
                    for i in range(3):
                        line(p[i - 1], p[i], magazine)
        else:
            for index in MAGAZINE:
                cube = original['elements'][index]
                x0, y1 = project(cube['from'])
                x1, y0 = project(cube['to'])
                color = mixed if audit['cubes'][index]['mixed'] else magazine
                for a, b in [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                             ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]:
                    line(a, b, color)
                text((x0 + x1) // 2 - 8, (y0 + y1) // 2 - 4, str(index), color, 2)
    text(35, 915, 'WHOLE CUBES PRESERVE ALL FACES AND UV / SEAM MEMBERSHIP IS AN APPROXIMATION', scale=3)

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)

    raw = b''.join(b'\0' + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def audit_outputs():
    for path, pin in ORIGINALS.items():
        assert sha((ROOT / path).read_bytes()) == pin, 'Original drift: ' + path
    original = json.loads(SOURCE.read_bytes())
    assert len(original['elements']) == 217
    meshes = source_meshes()
    audit = partition_audit(meshes, original)
    return {ART / 'model-partition-audit.json': encode(audit),
            ART / 'model-partition-audit.png': audit_png(meshes, audit, original)}


def sample(progress):
    if KEYS is None:
        raise ValueError('Master reference motion contract not yet read')
    if not 0 <= progress <= 1:
        raise ValueError(progress)
    for a, b in zip(KEYS, KEYS[1:]):
        if progress <= b[0]:
            t = max(0, min(1, (progress - a[0]) / (b[0] - a[0])))
            t = t * t * (3 - 2 * t)
            return tuple([a[column][axis] + (b[column][axis] - a[column][axis]) * t
                          for axis in range(3)] for column in (1, 2, 3))
    raise ValueError(progress)


def rotate(vector, rotation):
    # Native ItemTransform quaternion rotationXYZ: local Z, then Y, then X.
    x, y, z = vector
    a, b, c = map(math.radians, rotation)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return [x, y, z]


def generate():
    reference = ART / 'reference-notes.md'
    if KEYS is None or REFERENCE_SHA256 is None or not reference.is_file():
        raise SystemExit('Motion generation pending Master reference-notes.md and motion contract')
    assert sha(reference.read_bytes()) == REFERENCE_SHA256, 'Master reference notes changed; review before regeneration'
    provenance_path = ART / 'references/gameplay-provenance.json'
    assert sha(provenance_path.read_bytes()) == PROVENANCE_SHA256, 'Reference provenance changed'
    provenance = json.loads(provenance_path.read_bytes())
    for frame in provenance['frames']:
        assert sha((ROOT / frame['path']).read_bytes()) == frame['sha256'], 'Reference frame changed: ' + frame['path']
    outputs = audit_outputs()
    original = json.loads(SOURCE.read_bytes())
    item_source = ASSETS / 'items/weapon/the_recluse.json'
    original_item = json.loads(item_source.read_bytes())
    original_twohand = json.loads((ASSETS / 'models/weapon/submachine_gun/the_recluse_twohand.json').read_bytes())['display']
    indices = dict(body=[i for i in range(217) if i not in MAGAZINE], magazine=MAGAZINE)
    for part, selected in indices.items():
        geometry = {k: copy.deepcopy(v) for k, v in original.items() if k not in ('elements', 'display')}
        geometry['elements'] = [copy.deepcopy(original['elements'][i]) for i in selected]
        outputs[ASSETS / f'models/{KEY}_{part}.json'] = encode(geometry)
    two_hand = runpy.run_path(str(ROOT / 'scripts/build_weapons_w30.py'))['two_hand_display']
    entries = []
    for frame in range(21):
        progress = frame / 20
        rotation, translation, magazine_offset = sample(progress)
        parts = {}
        for part in ('body', 'magazine'):
            display = copy.deepcopy(original['display'])
            if frame not in (0, 20):
                for context in ('firstperson_righthand', 'firstperson_lefthand'):
                    pose = display[context]
                    pose['rotation'] = [round(v + rotation[i], 6) for i, v in enumerate(pose['rotation'])]
                    offset = rotate(magazine_offset, pose['rotation']) if part == 'magazine' else [0, 0, 0]
                    pose['translation'] = [round(v + translation[i] + offset[i] * pose['scale'][i], 6)
                                           for i, v in enumerate(pose['translation'])]
            for grip in ('native', 'twohand'):
                key = f'{KEY}_{frame:02}_{part}_{grip}'
                if grip == 'native':
                    compensated = display
                elif frame in (0, 20):
                    # Exact original accepted display objects, including their
                    # numeric precision, at both endpoints for both parts/hands.
                    compensated = original_twohand
                else:
                    compensated = two_hand(display, 'submachine_gun')
                outputs[ASSETS / f'models/{key}.json'] = encode({
                    'parent': f'destiny:{KEY}_{part}', 'display': compensated})
                parts[part, grip] = {'type': 'minecraft:model', 'model': 'destiny:' + key}

        def composite(grip):
            return {'type': 'minecraft:composite', 'models': [parts['body', grip], parts['magazine', grip]]}

        entries.append({'threshold': progress, 'model': {
            'type': 'minecraft:condition', 'property': 'minecraft:custom_model_data', 'index': 0,
            'on_true': composite('twohand'), 'on_false': composite('native')}})
    wrapper = copy.deepcopy(original_item)
    wrapper['model'] = {'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': ['firstperson_righthand', 'firstperson_lefthand'], 'model': {
            'type': 'minecraft:range_dispatch', 'property': 'minecraft:custom_model_data', 'index': 1,
            'entries': entries, 'fallback': original_item['model']}}],
        'fallback': original_item['model']}
    outputs[ASSETS / f'items/{KEY}.json'] = encode(wrapper)
    asset_paths = [p for p in outputs if p.is_relative_to(ASSETS)]
    assert len(asset_paths) == 87
    audit = json.loads(outputs[ART / 'model-partition-audit.json'])
    outputs[ART / 'manifest.json'] = encode(dict(
        stage='W100', generator='scripts/generate_reload_models_w100.py', ids=['the_recluse'],
        generatorSha256=sha(Path(__file__).read_bytes()),
        frames=21, sourceCubes=217, bodyCubes=len(indices['body']), magazineSourceCubes=len(MAGAZINE),
        magazineIndices=MAGAZINE, compositeCubes=217, maxCompositeCubes=256, assets=87,
        firstPersonContexts=['firstperson_righthand', 'firstperson_lefthand'], progressFloatIndex=1,
        gripBooleanIndex=0, sourceSha256=ORIGINALS,
        rawSourceSha256={'source.archive': ARCHIVE_SHA256,
                        **json.loads(BBMODEL.read_bytes())['destiny_w30']['source_files']},
        referenceSha256={str(reference.relative_to(ROOT)): REFERENCE_SHA256,
                        str(provenance_path.relative_to(ROOT)): PROVENANCE_SHA256,
                        **{frame['path']: frame['sha256'] for frame in provenance['frames']}},
        referenceObservations=dict(url=provenance['url'], inspectedSeeksSeconds=[37.3, 37.4, 37.5, 37.6],
            observed=['muzzle raised and body rolled after ADS', 'small lower-right ejected part',
                      'left hand approaches underside', 'insertion/return and ready pose'],
            authored=['all transform values', 'normalized keyframe placement', 'local cartridge path',
                      'whole-cube lower-cartridge proxy'],
            historicalFeedingFrenzySpeedCopied=False, gameplayDurationChanged=False,
            sourceAnimationRecovered=False),
        originalsUnchanged=True, keyframes=KEYS,
        originalGraphFallbackExact=True, endpointsExactBaseDisplay=True,
        nativeGameplayVerified=False, exactAnimationRip=False, handIK=False,
        partitionAudit='art/weapons/w100/model-partition-audit.json',
        partitionApproximation=audit['approximation'],
        nativeCheck=dict(version='26.3', status='pending Master/L2 execution',
            test='src/test/java/kim/biryeong/destiny/fx/RecluseReloadW100Test.java',
            parsers=['ItemModels.CODEC with JsonOps', 'CuboidModel.fromStream'],
            expectedAssets=87, executedByGenerator=False,
            requiredContracts=['independent literal original pins', 'native parser accepts all 87 assets',
                'exact whole-element partition and UV conservation',
                'signed left/right ItemTransform semantics', 'crossbow carrier inverse for both hands',
                'exact native/twohand endpoint display identity', 'all other-context and inactive full-graph fallback']),
        requirements=dict(sourcePins='checked', exactElementsFacesUVTexture='checked',
            partitionConservation='checked', physicalMagazineIdentification=PARTITION_IDENTIFICATION,
            compositeCubeBudget='217 <= 256',
            samples='21 thresholds 0..1 inclusive', grips='native/twohand flag 0',
            contexts='right/left first person only', inactiveFallback='original full item graph',
            otherContextFallback='original full item graph',
            endpoints='exact original native/twohand display objects',
            native26_3Parser='pending Master/L2', gameplay='pending Master'),
        limitations='Reference-informed authored sampled transforms, not an animation rip. No hands/IK, independent bolt, third-person animation, or gameplay verification. Lower central component is a cartridge proxy, not proven semantic magazine identification: the rip has generic mesh names and footage occludes the exact boundary. Whole-cube seams approximate that component boundary; exact original surfaces and UV are conserved.',
        sha256={str(p.relative_to(ROOT)): sha(outputs[p]) for p in asset_paths},
        auditSha256={str(p.relative_to(ROOT)): sha(v) for p, v in outputs.items() if not p.is_relative_to(ASSETS)},
        assetSha256={str(p.relative_to(ROOT)): sha(outputs[p]) for p in asset_paths}))
    return outputs


def validate_outputs(outputs):
    """Independent data invariants; native 26.3 parsing remains the L2 test."""
    original = json.loads(SOURCE.read_bytes())
    source_elements = original['elements']
    source_item = json.loads((ASSETS / 'items/weapon/the_recluse.json').read_bytes())
    elements_by_index = {}
    part_counts = []
    for part, selected in [('body', [i for i in range(217) if i not in MAGAZINE]),
                           ('magazine', MAGAZINE)]:
        geometry = json.loads(outputs[ASSETS / f'models/{KEY}_{part}.json'])
        part_counts.append(len(geometry['elements']))
        assert {k: v for k, v in geometry.items() if k != 'elements'} == {
            k: v for k, v in original.items() if k not in ('elements', 'display')}
        for index, element in zip(selected, geometry['elements'], strict=True):
            assert index not in elements_by_index
            elements_by_index[index] = element
        for grip in ('native', 'twohand'):
            endpoint = original['display'] if grip == 'native' else json.loads(
                (ASSETS / 'models/weapon/submachine_gun/the_recluse_twohand.json').read_bytes())['display']
            for frame in (0, 20):
                pose = json.loads(outputs[ASSETS / f'models/{KEY}_{frame:02}_{part}_{grip}.json'])
                assert pose['display'] == endpoint
    assert [elements_by_index[i] for i in range(217)] == source_elements
    assert sum(part_counts) == 217 <= 256
    item = json.loads(outputs[ASSETS / f'items/{KEY}.json'])
    assert {k: v for k, v in item.items() if k != 'model'} == {
        k: v for k, v in source_item.items() if k != 'model'}
    select = item['model']
    assert select['fallback'] == source_item['model']
    assert select['cases'][0]['when'] == ['firstperson_righthand', 'firstperson_lefthand']
    dispatch = select['cases'][0]['model']
    assert dispatch['fallback'] == source_item['model'] and dispatch['index'] == 1
    assert len(dispatch['entries']) == 21
    references = set()
    for frame, entry in enumerate(dispatch['entries']):
        assert entry['threshold'] == frame / 20
        condition = entry['model']
        assert condition['index'] == 0
        for grip, branch in [('native', 'on_false'), ('twohand', 'on_true')]:
            composite = condition[branch]
            assert composite['type'] == 'minecraft:composite' and len(composite['models']) == 2
            for part, model in zip(('body', 'magazine'), composite['models'], strict=True):
                key = f'{KEY}_{frame:02}_{part}_{grip}'
                assert model == {'type': 'minecraft:model', 'model': 'destiny:' + key}
                pose = json.loads(outputs[ASSETS / f'models/{key}.json'])
                assert pose['parent'] == f'destiny:{KEY}_{part}'
                references.add(key)
                for context, transform in pose['display'].items():
                    for field in ('rotation', 'translation', 'scale'):
                        assert len(transform[field]) == 3
                        assert all(math.isfinite(v) for v in transform[field])
                    assert all(abs(v) <= 80 for v in transform['translation'])
                    assert all(0 < abs(v) <= 4 for v in transform['scale'])
                    if not context.startswith('firstperson_'):
                        base = original['display'] if grip == 'native' else json.loads(
                            (ASSETS / 'models/weapon/submachine_gun/the_recluse_twohand.json').read_bytes())['display']
                        assert transform == base[context]
    assert len(references) == 84


def write_outputs(outputs, verify):
    for path, data in outputs.items():
        allowed = path in (ART / 'manifest.json', ART / 'model-partition-audit.json', ART / 'model-partition-audit.png')
        allowed |= path.is_relative_to(ASSETS / 'models/weapon_reload_w100')
        allowed |= path.is_relative_to(ASSETS / 'items/weapon_reload_w100')
        assert allowed, 'Output outside W100 ownership: ' + str(path)
        if verify:
            assert path.is_file() and path.read_bytes() == data, 'W100 output differs: ' + str(path.relative_to(ROOT))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if not verify:
        for path, pin in ORIGINALS.items():
            assert sha((ROOT / path).read_bytes()) == pin, 'Original changed: ' + path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect-source', action='store_true')
    parser.add_argument('--partition-only', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.inspect_source:
        describe_source()
    elif args.partition_only:
        write_outputs(audit_outputs(), args.verify)
        print(('Verified' if args.verify else 'Generated') + ' W100 provisional partition audit')
    else:
        outputs = generate()
        validate_outputs(outputs)
        write_outputs(outputs, args.verify)
        print(f'{"Verified" if args.verify else "Generated"} {len(outputs)} W100 files')
