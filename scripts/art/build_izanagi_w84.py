#!/usr/bin/env python3
"""Read-only izanagi.bbmodel conversion, native 26.3 assets and W70 aim samples.

Run with Python 3 (standard library only). --verify reconstructs every output in
memory and never writes. The supplied original and complete raw copy are SHA
pinned; no Blockbench/Blender state, Gradle or game launch is involved.
"""
import argparse
import base64
import bisect
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w84/model")
GENERATOR = Path("scripts/art/build_izanagi_w84.py")
SOURCE_SHA256 = "9ae28369f80ff0f81bb7e1344ee50b618b9a2de62dcafc631287084dbe3c8f31"
MAX_CUBES = 256
GEOMETRY_SCALE = .625
RAW_SOURCE = ART / "source/izanagi.bbmodel"
TEXTURE_SUFFIXES = ("_lens", "", "_accent")
ID = "izanagis_burden"
MODEL = "item/weapon/" + ID
AIM = "item/weapon_aim_w70/" + ID
FP = ("firstperson_righthand", "firstperson_lefthand")
NATIVE_ITEM = ASSETS / f"items/weapon/{ID}.json"
AIM_ITEM = ASSETS / f"items/weapon_aim_w70/{ID}.json"
DIRECTIONS = ("north", "east", "south", "west", "up", "down")


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rnd(vector):
    return [round(x, 9) + 0 for x in vector]


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def rotate(v, angles):
    """Native ItemTransform/EulerXYZ: Rx * Ry * Rz (local Z applied first)."""
    x, y, z = v
    a, b, c = map(math.radians, angles)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return [x, y, z]


def source_point(cube, point):
    origin = cube["origin"]
    return add(origin, rotate(sub(point, origin), cube.get("rotation", [0, 0, 0])))


def corners(element):
    points = list(itertools.product(*zip(element["from"], element["to"])))
    rotation = element.get("rotation")
    if rotation:
        angles = [rotation[axis] for axis in "xyz"]
        points = [add(rotation["origin"], rotate(sub(p, rotation["origin"]), angles)) for p in points]
    return points


def pose(rotation, translation, scale):
    return dict(rotation=rnd(rotation), translation=rnd(translation), scale=[scale] * 3)


def centered_context(points, rotation):
    points = [rotate(sub(p, [8] * 3), rotation) for p in points]
    lo = [min(p[a] for p in points) for a in range(3)]
    hi = [max(p[a] for p in points) for a in range(3)]
    scale = round(min(.9, 14.8 / max(hi[a] - lo[a] for a in (0, 1))), 9)
    return pose(rotation, [-(lo[a] + hi[a]) * scale / 2 for a in range(3)], scale)


def item_point(point, transform, left=False):
    sign = -1 if left else 1
    angles = list(transform["rotation"])
    angles[1] *= sign
    angles[2] *= sign
    v = rotate([(point[a] - 8) * transform["scale"][a] for a in range(3)], angles)
    t = list(transform["translation"])
    t[0] *= sign
    return add(v, t)


def two_hand_display(display):
    """W30/W70 crossbow idle inverse, including native left-hand reflection."""
    result = copy.deepcopy(display)
    for context in FP:
        t = result[context]
        # Carrier is T(-.641864*sign,0,0) * Ry(10*sign), in block units.
        t["translation"] = rnd(rotate(add(t["translation"], [.641864 * 16, 0, 0]), [0, -10, 0]))
        # Left-multiply the native rotation matrix by Ry(-10), then extract XYZ.
        columns = [rotate(rotate(v, t["rotation"]), [0, -10, 0]) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
        m = [[columns[j][i] for j in range(3)] for i in range(3)]
        t["rotation"] = rnd([math.degrees(v) for v in (
            math.atan2(-m[1][2], m[2][2]), math.asin(max(-1, min(1, m[0][2]))), math.atan2(-m[0][1], m[0][0]))])
    # Level-head AnimationUtils.animateCrossbowHold primary arm is
    # Ry(-.3*sign) Rx(-pi/2+.1). Invert it AND ItemInHandLayer's
    # Rx(-90) Ry(180); only preserving the muzzle axis would hide an upside-down gun.
    for hand in ("righthand", "lefthand"):
        result["thirdperson_" + hand] = pose([-180 + math.degrees(.1), -180 + math.degrees(.3), 0], [0, -2, 2], .9)
    return result


def model_node(key):
    return {"type": "minecraft:model", "model": "destiny:" + key}


def grip_node(key):
    return dict(type="minecraft:condition", property="minecraft:custom_model_data", index=0,
                on_false=model_node(key), on_true=model_node(key + "_twohand"))


def interpolate(hip, ads, frame):
    result = copy.deepcopy(hip)
    for context in FP:
        for field in ("rotation", "translation", "scale"):
            result[context][field] = rnd([a + (b - a) * frame / 20 for a, b in zip(hip[context][field], ads[context][field])])
    return result


def png_decode(raw):
    """Decode the pinned non-interlaced RGBA8 atlas without external packages."""
    require(raw.startswith(b"\x89PNG\r\n\x1a\n"), "Expected PNG")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", raw[16:29])
    require((depth, color, compression, filtering, interlace) == (8, 6, 0, 0, 0), "Expected noninterlaced RGBA8 PNG")
    chunks = []
    offset = 8
    while offset < len(raw):
        size = struct.unpack(">I", raw[offset:offset + 4])[0]
        kind = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + size]
        crc = struct.unpack(">I", raw[offset + 8 + size:offset + 12 + size])[0]
        require(zlib.crc32(kind + data) & 0xffffffff == crc, "Invalid PNG CRC")
        if kind == b"IDAT":
            chunks.append(data)
        offset += size + 12
    filtered = zlib.decompress(b"".join(chunks))
    stride = width * 4
    require(len(filtered) == height * (stride + 1), "Unexpected PNG scanline size")
    rows = []
    previous = bytearray(stride)
    for y in range(height):
        method = filtered[y * (stride + 1)]
        require(method in range(5), "Unsupported PNG filter")
        row = bytearray(filtered[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for x in range(stride):
            a = row[x - 4] if x >= 4 else 0
            b = previous[x]
            c = previous[x - 4] if x >= 4 else 0
            estimate = a + b - c
            distances = (abs(estimate - a), abs(estimate - b), abs(estimate - c))
            paeth = (a, b, c)[distances.index(min(distances))]
            predictor = (0, a, b, (a + b) // 2, paeth)[method]
            row[x] = (row[x] + predictor) & 255
        rows.append(bytes(row))
        previous = row
    return width, height, b"".join(rows)


def png_encode(width, height, pixels):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    scanlines = b"".join(b"\0" + bytes(pixels[y * width * 4:(y + 1) * width * 4]) for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b""))


def face_corners(element):
    x, y, z = element["from"]
    X, Y, Z = element["to"]
    # Face vertices in native UV order: top-left, top-right, bottom-right, bottom-left.
    return dict(north=[(X, Y, z), (x, Y, z), (x, y, z), (X, y, z)],
                south=[(x, Y, Z), (X, Y, Z), (X, y, Z), (x, y, Z)],
                east=[(X, Y, Z), (X, Y, z), (X, y, z), (X, y, Z)],
                west=[(x, Y, z), (x, Y, Z), (x, y, Z), (x, y, z)],
                up=[(x, Y, z), (X, Y, z), (X, Y, Z), (x, Y, Z)],
                down=[(x, y, Z), (X, y, Z), (X, y, z), (x, y, z)])


def offline_preview(elements, atlases, display):
    """Four software-rasterized views, exact atlas/UVs and a per-pixel z buffer.

    Side / three-quarter above hip / ADS. Static idle FP includes the vanilla
    (.56,-.52,-.72) carrier. This is an authored preview, not a native game bake.
    """
    width = height = 384
    textures = [png_decode(atlas) for atlas in atlases]
    tiles = []
    all_points = [p for e in elements for p in corners(e)]
    for view in range(4):
        pixels = bytearray([29, 34, 43, 255] * (width * height))
        depth = [float("inf")] * (width * height)
        rotation = [0, 90, 0] if view == 0 else [15, 55, 0]
        if view < 2:
            projected = [rotate(sub(p, [8] * 3), rotation) for p in all_points]
            lo = [min(p[a] for p in projected) for a in range(3)]
            hi = [max(p[a] for p in projected) for a in range(3)]
            center = [(a + b) / 2 for a, b in zip(lo, hi)]
            zoom = min((width - 48) / (hi[0] - lo[0]), (height - 48) / (hi[1] - lo[1]))

        def project(point):
            if view < 2:
                x, y, z = sub(rotate(sub(point, [8] * 3), rotation), center)
                return [width / 2 + x * zoom, height / 2 - y * zoom, -z + 40, 1]
            transform = display["hip" if view == 2 else "ads"][FP[0]]
            x, y, z = add([x / 16 for x in item_point(point, transform)], [.56, -.52, -.72])
            require(z < -.05, "Preview near-plane clipping; revise pose")
            focal = height / (2 * math.tan(math.radians(70) / 2))
            return [width / 2 + focal * x / -z, height / 2 - focal * y / -z, -z, 1 / -z]

        for element in elements:
            for name, points in face_corners(element).items():
                if "rotation" in element:
                    r = element["rotation"]
                    points = [add(r["origin"], rotate(sub(p, r["origin"]), [r[a] for a in "xyz"])) for p in points]
                # Match native front-face culling, especially opposing coplanar
                # lens faces whose artwork is intentionally different.
                normal = dict(north=[0,0,-1], south=[0,0,1], east=[1,0,0],
                              west=[-1,0,0], up=[0,1,0], down=[0,-1,0])[name]
                if "rotation" in element:
                    normal = rotate(normal, [element["rotation"][a] for a in "xyz"])
                if view < 2:
                    if rotate(normal, rotation)[2] <= 0:
                        continue
                else:
                    transform = display["hip" if view == 2 else "ads"][FP[0]]
                    normal = rotate(normal, transform["rotation"])
                    center = add([v / 16 for v in item_point(points[0], transform)], [.56,-.52,-.72])
                    if sum(a*b for a,b in zip(normal, center)) >= 0:
                        continue
                tw, th, texels = textures[int(element["faces"][name]["texture"][1:])]
                points = [project(p) for p in points]
                u0, v0, u1, v1 = element["faces"][name]["uv"]
                uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
                lighting = dict(up=1, down=.55, north=.8, south=.8, east=.7, west=.7)[name]
                for indices in ((0, 1, 2), (0, 2, 3)):
                    a, b, c = [points[i] for i in indices]
                    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                    if abs(denominator) < 1e-10:
                        continue
                    xmin = max(0, math.floor(min(a[0], b[0], c[0])))
                    xmax = min(width - 1, math.ceil(max(a[0], b[0], c[0])))
                    ymin = max(0, math.floor(min(a[1], b[1], c[1])))
                    ymax = min(height - 1, math.ceil(max(a[1], b[1], c[1])))
                    for py in range(ymin, ymax + 1):
                        for px in range(xmin, xmax + 1):
                            x, y = px + .5, py + .5
                            wa = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / denominator
                            wb = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / denominator
                            wc = 1 - wa - wb
                            if min(wa, wb, wc) < -1e-9:
                                continue
                            weights = [wa, wb, wc]
                            triangle = [a, b, c]
                            invz = sum(w * p[3] for w, p in zip(weights, triangle))
                            distance = 1 / invz if view >= 2 else sum(w * p[2] for w, p in zip(weights, triangle))
                            index = py * width + px
                            if distance >= depth[index]:
                                continue
                            uv = [sum(w * triangle[j][3] * uvs[indices[j]][axis] for j, w in enumerate(weights)) / invz for axis in range(2)]
                            tx = min(tw - 1, max(0, int(uv[0] * tw / 16)))
                            ty = min(th - 1, max(0, int(uv[1] * th / 16)))
                            offset = (ty * tw + tx) * 4
                            color = texels[offset:offset + 4]
                            if color[3] < 128:
                                continue
                            pixels[index * 4:index * 4 + 4] = bytes([int(v * lighting) for v in color[:3]] + [255])
                            depth[index] = distance
        if view >= 2:
            for delta in range(-7, 8):
                if abs(delta) >= 3:
                    for x, y in ((width // 2 + delta, height // 2), (width // 2, height // 2 + delta)):
                        pixels[(y * width + x) * 4:(y * width + x) * 4 + 4] = bytes([235, 103, 92, 255])
        tiles.append(pixels)
    contact = bytearray()
    for row in range(2):
        for y in range(height):
            for column in range(2):
                contact.extend(tiles[row * 2 + column][y * width * 4:(y + 1) * width * 4])
    return png_encode(width * 2, height * 2, contact)


def build(source_path):
    raw = source_path.read_bytes()
    require(sha(raw) == SOURCE_SHA256, "Source SHA mismatch; original replacement refused")
    source = json.loads(raw)
    cubes = source["elements"]
    require(len(cubes) == 79 and len(cubes) <= MAX_CUBES, "Expected original 79 cubes; limit 256")
    require(source["meta"]["model_format"] == "java_block", "Expected Java authoring source")
    require(not source.get("parent") and not source.get("unhandled_root_fields"), "Unconverted root fields")
    require(source["resolution"] == dict(width=64, height=64), "Unexpected project UV space")
    outliner_ids = []
    groups = []

    def walk(nodes):
        for node in nodes:
            if isinstance(node, str):
                outliner_ids.append(node)
            else:
                require(not any(node.get("rotation", [])), "Rotated group requires transform baking")
                require(node.get("export", True) and node.get("visibility", True), "Hidden group")
                groups.append(dict(name=node["name"], sourceUuid=node["uuid"], transform="identity"))
                walk(node["children"])
    walk(source["outliner"])
    require(len(outliner_ids) == len(cubes) and set(outliner_ids) == {e["uuid"] for e in cubes}, "Outliner coverage")
    require(len(source["textures"]) == 3, "Expected all three embedded atlases")
    atlases = []
    texture_metadata = []
    for index, texture in enumerate(source["textures"]):
        require(texture["source"].startswith("data:image/png;base64,"), "External texture dependency")
        atlas = base64.b64decode(texture["source"].split(",", 1)[1], validate=True)
        width, height, _ = png_decode(atlas)
        expected_size = (128, 128) if index == 0 else (512, 512)
        require((width, height) == expected_size, "Unexpected embedded PNG size")
        atlases.append(atlas)
        texture_metadata.append(dict(index=index, sourceName=texture["name"],
            bytes=len(atlas), sha256=sha(atlas), pixels=[width, height],
            sourceTextureUvMetadata=[texture["uv_width"], texture["uv_height"]],
            effectiveJavaProjectUv=[64, 64], nativeUvScale=.25,
            copiedByteForByte=True, output=f"destiny:item/weapon/{ID}{TEXTURE_SUFFIXES[index]}"))
    # Rotated center of the original pistol grip, source element53. A uniform
    # 5/8 scale permits grip centering without violating native [-16,32] bounds.
    handle = cubes[53]
    grip = source_point(handle, [(a+b)/2 for a,b in zip(handle["from"], handle["to"])])
    shift = [8 - v * GEOMETRY_SCALE for v in grip]

    def convert(point):
        return add([v * GEOMETRY_SCALE for v in point], shift)

    elements = []
    mapping = []
    for index, cube in enumerate(cubes):
        require(cube["type"] == "cube" and not cube.get("box_uv"), f"Unsupported geometry {index}")
        require(cube.get("export", True) and cube.get("visibility", True), f"Hidden cube {index}")
        require(not cube.get("inflate", 0) and not cube.get("stretch") and not cube.get("rescale"), f"Cube deformation {index}")
        require(all(math.isfinite(v) for field in ("from", "to", "origin") for v in cube[field]), "Nonfinite geometry")
        require(all(a <= b for a,b in zip(cube["from"], cube["to"])), "Inverted cube")
        plane = [axis for axis,(a,b) in enumerate(zip(cube["from"], cube["to"])) if a == b]
        require(not plane or index in (43, 78) and plane == [2], "Unexpected degenerate geometry")
        require(set(cube["faces"]) == set(DIRECTIONS), "Incomplete source face set")
        faces = {}
        for name, face in cube["faces"].items():
            require(set(face) == {"texture", "uv"} and face["texture"] in (0, 1, 2), "Unknown face metadata")
            require(all(math.isfinite(v) and 0 <= v <= 64 for v in face["uv"]), "UV outside project atlas")
            faces[name] = dict(uv=[v / 4 for v in face["uv"]], texture="#" + str(face["texture"]))
        element = dict(**{"from": rnd(convert(cube["from"])), "to": rnd(convert(cube["to"]))}, faces=faces)
        rotation = cube.get("rotation", [0, 0, 0])
        require(sum(v != 0 for v in rotation) <= 1 and all(v in (-45, -22.5, 0, 22.5, 45) for v in rotation), "Unexpected rotation")
        if any(rotation):
            element["rotation"] = dict(origin=rnd(convert(cube["origin"])), x=rotation[0], y=rotation[1], z=rotation[2], rescale=False)
        require(all(-16 <= v <= 32 for field in ("from", "to") for v in element[field]), "Native geometry bounds exceeded")
        elements.append(element)
        mapping.append(dict(index=index, sourceUuid=cube["uuid"], rotated=any(rotation), zeroThicknessLens=bool(plane)))
    points = [p for element in elements for p in corners(element)]
    # Scope-lens planes, not an invented barrel/top-rail approximation. Their
    # x/y centers coincide; local -Z is forward for both rifle and scope.
    front = convert([(a+b)/2 for a,b in zip(cubes[78]["from"], cubes[78]["to"])])
    rear = convert([(a+b)/2 for a,b in zip(cubes[43]["from"], cubes[43]["to"])])
    require(abs(front[0]-rear[0]) < 1e-9 and abs(front[1]-rear[1]) < 1e-9 and front[2] < rear[2], "Scope axis not longitudinal")
    sight_y = front[1] - 8
    # Muzzle opening: center of the source four-piece muzzle collar (5..8).
    bore = convert([8, (cubes[6]["to"][1]+cubes[5]["from"][1])/2, cubes[5]["from"][2]])
    hip_scale = .95
    hip_translation = [0, 0, -4]
    target_relative = sub([0, 0, -64], add([.56*16, -.52*16, -.72*16], hip_translation))
    bore_height = (bore[1] - 8) * hip_scale
    pitch = math.atan2(target_relative[1], -target_relative[2]) - math.asin(bore_height / math.hypot(target_relative[1], target_relative[2]))
    unpitched = rotate(target_relative, [-math.degrees(pitch), 0, 0])
    yaw = math.degrees(math.atan2(-unpitched[0], -unpitched[2]))
    hip = {context: pose([math.degrees(pitch), yaw, 0], hip_translation, hip_scale) for context in FP}
    hip.update(thirdperson_righthand=pose([-90,180,0], [0,2,0], .9),
               thirdperson_lefthand=pose([-90,180,0], [0,2,0], .9),
               gui=centered_context(points, [10,65,-10]),
               ground=centered_context(points, [0,0,0]),
               fixed=centered_context(points, [0,90,0]),
               head=pose([0,0,0], [0,8,0], .6))
    ads = copy.deepcopy(hip)
    inspect = copy.deepcopy(hip)
    for context in FP:
        ads[context] = pose([0,0,0], [-.56*16, .52*16-sight_y*.95, -4], .95)
        inspect[context] = pose([5,35,-12], [-2,0,-7], .8)
    displays = dict(hip=hip, ads=ads, inspect=inspect, scope=copy.deepcopy(ads))
    output = {}

    def put(path, value):
        output[path] = encode(value)

    texture_ids = {str(i): f"destiny:item/weapon/{ID}{suffix}" for i,suffix in enumerate(TEXTURE_SUFFIXES)}
    texture_ids["particle"] = texture_ids["1"]
    put(ASSETS / f"models/{MODEL}.json", dict(
        credit="W84 direct conversion of supplied izanagi.bbmodel; Bungie design; source license not supplied",
        ambientocclusion=source["ambientocclusion"], gui_light="front" if source["front_gui_light"] else "side",
        textures=texture_ids, elements=elements, display=hip))
    for index, atlas in enumerate(atlases):
        output[ASSETS / f"textures/item/weapon/{ID}{TEXTURE_SUFFIXES[index]}.png"] = atlas
    for state, display in displays.items():
        key = MODEL if state == "hip" else MODEL + "_" + state
        if state != "hip":
            put(ASSETS / f"models/{key}.json", dict(parent="destiny:"+MODEL, display=display))
        put(ASSETS / f"models/{key}_twohand.json", dict(parent="destiny:"+key, display=two_hand_display(display)))
    graph = dict(type="minecraft:select", property="minecraft:custom_model_data", index=0,
        cases=[dict(when=state, model=grip_node(MODEL if state == "hip" else MODEL+"_"+state)) for state in displays],
        fallback=grip_node(MODEL))
    put(NATIVE_ITEM, dict(model=graph, hand_animation_on_swap=False))
    frames = []
    for frame in range(21):
        display = interpolate(hip, ads, frame)
        key = f"{AIM}_{frame:02d}_native"
        two_key = f"{AIM}_{frame:02d}_twohand"
        put(ASSETS / f"models/{key}.json", dict(parent="destiny:"+MODEL, display=display))
        put(ASSETS / f"models/{two_key}.json", dict(parent="destiny:"+MODEL, display=two_hand_display(display)))
        frames.append(dict(threshold=round(frame/20, 2), model=dict(type="minecraft:condition",
            property="minecraft:custom_model_data", index=0, on_false=model_node(key), on_true=model_node(two_key))))
    aim_range = dict(type="minecraft:range_dispatch", property="minecraft:custom_model_data", index=3,
                     entries=frames, fallback=copy.deepcopy(graph))
    aimed = dict(type="minecraft:select", property="minecraft:custom_model_data", index=0,
        cases=[dict(when="inspect", model=grip_node(MODEL+"_inspect"))], fallback=aim_range)
    wrapper = dict(type="minecraft:select", property="minecraft:display_context",
                  cases=[dict(when=list(FP), model=aimed)], fallback=copy.deepcopy(graph))
    put(AIM_ITEM, dict(model=wrapper, hand_animation_on_swap=False))
    checks = validate(output, source, convert, displays, front, rear, frames, bore, atlases)
    put(ART / "pose-checks.json", checks)
    output[RAW_SOURCE] = raw
    output[ART / "offline-preview.png"] = offline_preview(elements, atlases, displays)
    output[ART / "README.md"] = NOTES.encode()
    inputs = {str(path): sha((ROOT/path).read_bytes()) for path in (
        GENERATOR, Path("scripts/art/build_ace_w83.py"), Path("scripts/build_weapons_w30.py"),
        Path("scripts/generate_aim_models_w70.py"))}
    manifest = dict(schema=1, stage="W84", generator=str(GENERATOR), id=ID, family="sniper_rifle",
        expectedRuntimeGrip="TWO_HAND", runtimeRegistrationByParent=True,
        itemModel="destiny:weapon/"+ID, aimItemModel="destiny:weapon_aim_w70/"+ID, target="Minecraft Java 26.3",
        source=dict(filename="izanagi.bbmodel", sha256=SOURCE_SHA256, bytes=len(raw), externalReadOnly=True,
            originalCopiedByteForByte=True, pinnedRawCopy=str(RAW_SOURCE), format=source["meta"],
            display=source["display"], authorAndLicense="Not supplied; Bungie design; not a redistribution license",
            embeddedTextures=texture_metadata, effectiveUvResolution=[64,64]),
        conversion=dict(method="One source cube to one native element; uniform 5/8 scale and grip translation only",
            sourceCubes=79, outputCubes=79, cubeLimit=MAX_CUBES, sourceFaces=474, outputFaces=474,
            rotatedCubes=30, unsupportedRotations=0, preservedZeroThicknessLenses=[43,78],
            geometryScale=GEOMETRY_SCALE, sourceGrip=rnd(grip), geometryTranslation=rnd(shift),
            rotationSchema="26.3 rotation origin + scalar x/y/z + rescale, not array/axis-angle legacy syntax",
            identityGroups=groups, mapping=mapping),
        aim=dict(progressFloatIndex=3, gripBooleanIndex=0, poseStringIndex=0, samples=21,
            thresholds=[e["threshold"] for e in frames], offsetTolerance=.002, floatRoundingTolerance=1e-6,
            interpolation="Linear Euler/translation/scale; 20TPS samples, not render-frame interpolation",
            inspectPriority=True, hipBoreZeroDistanceBlocks=4,
            scope="ADS/scope align original lens centers; original red-ring/cutout-lens fallback; no overlay/magnification",
            sourceScopeFrontIndex=78, sourceScopeRearIndex=43),
        sourceIssues=SOURCE_ISSUES,
        verification=dict(generatorReconstruction=True, nativeGameplayVerified=False, nativeCodecExecuted=False,
            nativeParserInspected="26.3 CuboidModelElement.Deserializer via read-only javap",
            limitations=["Offline static geometry/camera math only; full client codec/bake/visual validation pending parent",
                "Idle crossbow inverse for both hands; no animated support-hand IK, swing, reload or active-use compensation",
                "Original red reticle ring and transparent lens center retained; no optical magnification",
                "Right-hand software preview only; mathematical pose checks cover both hands/grips"]),
        inputSha256=inputs, outputSha256={str(p):sha(b) for p,b in sorted(output.items())})
    put(ART / "manifest.json", manifest)
    return output




def validate(output, source, convert, displays, front, rear, frames, bore, atlases):
    """Independent invariants for geometry/UV fidelity, pose math and graph refs."""
    documents = {p: json.loads(b) for p, b in output.items() if p.suffix == ".json"}
    elements = documents[ASSETS / f"models/{MODEL}.json"]["elements"]
    require(len(elements) == 79 and len(elements) <= MAX_CUBES, "Native cube count")
    max_error = 0
    for cube, element in zip(source["elements"], elements):
        expected = [convert(source_point(cube, p)) for p in itertools.product(*zip(cube["from"], cube["to"]))]
        for a, b in zip(expected, corners(element)):
            max_error = max(max_error, max(abs(x - y) for x, y in zip(a, b)))
        for name, face in cube["faces"].items():
            require(element["faces"][name]["uv"] == [x / 4 for x in face["uv"]], "UV changed")
            require(element["faces"][name]["texture"] == "#"+str(face["texture"]), "Face atlas changed")
    require(max_error < 2e-9, "Geometry fidelity failure")
    for p, doc in documents.items():
        if "display" in doc:
            for context, transform in doc["display"].items():
                for field, vector in transform.items():
                    require(len(vector) == 3 and all(math.isfinite(x) for x in vector), f"Invalid display {p}/{context}")
                    if field == "translation":
                        require(max(map(abs, vector)) <= 80, "Native translation clamp")
                    if field == "scale":
                        require(all(0 < x <= 4 for x in vector), "Native scale clamp")
        def references(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("parent", "model") and isinstance(value, str):
                        require(value.startswith("destiny:"), "Unexpected external model")
                        target = ASSETS / ("models/" + value.split(":", 1)[1] + ".json")
                        require(target in documents, f"Unresolved model {p}: {target}")
                    else:
                        references(value)
            elif isinstance(node, list):
                for value in node:
                    references(value)
        references(doc)
    base = documents[ASSETS / f"models/{MODEL}.json"]
    for element in elements:
        for field in ("from", "to"):
            require(len(element[field]) == 3 and all(-16 <= x <= 32 for x in element[field]), "Native element bound")
        if "rotation" in element:
            require(set(element["rotation"]) == {"origin", "x", "y", "z", "rescale"}, "Non-native rotation schema")
        for face in element["faces"].values():
            require(face["texture"][1:] in base["textures"], "Missing texture slot")
    for index,suffix in enumerate(TEXTURE_SUFFIXES):
        require(output[ASSETS / f"textures/item/weapon/{ID}{suffix}.png"] == atlases[index], "Atlas bytes changed")
    require(sum(e["from"][2] == e["to"][2] for e in elements) == 2, "Lost lens plane")
    alignment = []
    hip_alignment = []
    for left, context in zip((False, True), FP):
        carrier = [-.56 * 16 if left else .56 * 16, -.52 * 16, -.72 * 16]
        for name, point in (("front", front), ("rear", rear)):
            camera = add(item_point(point, displays["ads"][context], left), carrier)
            require(abs(camera[0]) < 1e-7 and abs(camera[1]) < 1e-7 and camera[2] < 0, "ADS sight not on central camera ray")
            alignment.append(dict(hand=context, anchor=name, cameraPointBlocks=rnd([x / 16 for x in camera])))
        hip = displays["hip"][context]
        camera = add(item_point(bore, hip, left), carrier)
        angles = list(hip["rotation"])
        if left:
            angles[1] *= -1
            angles[2] *= -1
        direction = rotate([0, 0, -1], angles)
        distance = (-4 * 16 - camera[2]) / direction[2]
        hit = add(camera, [x * distance for x in direction])
        require(abs(hit[0]) < 1e-7 and abs(hit[1]) < 1e-7 and distance > 0, "Hip bore misses center aim zero")
        hip_alignment.append(dict(hand=context, cameraIntersectionBlocks=rnd([x / 16 for x in hit])))
    max_inverse_error = 0
    for frame in range(21):
        native = interpolate(displays["hip"], displays["ads"], frame)
        twohand = two_hand_display(native)
        for context, left in zip(FP, (False, True)):
            sign = -1 if left else 1
            for point in ([8, 8, 8], front, rear, [9, 11, 2]):
                actual = add(rotate(item_point(point, twohand[context], left), [0, 10 * sign, 0]), [-.641864 * 16 * sign, 0, 0])
                expected = item_point(point, native[context], left)
                max_inverse_error = max(max_inverse_error, max(abs(a - b) for a, b in zip(actual, expected)))
        if frame in (0, 20):
            require(native == displays["hip" if frame == 0 else "ads"], "Aim endpoint mismatch")
    require(max_inverse_error < 1e-7, "Twohand compensation failed")
    thresholds = [entry["threshold"] for entry in frames]
    f32 = lambda x: struct.unpack("<f", struct.pack("<f", x))[0]
    native_thresholds = [f32(x) for x in thresholds]
    for frame in range(21):
        for offset in (0, .000001, .001, .002):
            require(bisect.bisect_right(thresholds, frame / 20 + offset) - 1 == frame, "CMD offset selects wrong frame")
            runtime_progress = f32(f32(frame / 20) + f32(offset))
            require(bisect.bisect_right(native_thresholds, runtime_progress)-1 == frame, "IEEE754 float selects wrong frame")
    thirdperson_checks = []
    for twohand in (False, True):
        display = two_hand_display(displays["hip"]) if twohand else displays["hip"]
        for left, hand in ((False, "righthand"), (True, "lefthand")):
            sign = -1 if left else 1
            angles = list(display["thirdperson_" + hand]["rotation"])
            angles[1] *= sign
            angles[2] *= sign
            axes = {}
            for name, vector in (("muzzle", [0, 0, -1]), ("up", [0, 1, 0]), ("right", [1, 0, 0])):
                # Actual ItemInHandLayer order, including the easily missed Y180.
                actual = rotate(rotate(rotate(vector, angles), [0, 180, 0]), [-90, 0, 0])
                if twohand:
                    actual = rotate(rotate(actual, [-90 + math.degrees(.1), 0, 0]), [0, -math.degrees(.3) * sign, 0])
                require(max(abs(a - b) for a, b in zip(actual, vector)) < 1e-9, "Third-person orientation: " + name)
                axes[name] = rnd(actual)
            thirdperson_checks.append(dict(hand=hand, grip="twohand" if twohand else "native", levelHeadIdleAxes=axes))
    # Route the actual generated graph rather than trusting a list of thresholds.
    def resolve(node, context, state, twohand, progress):
        kind = node["type"]
        if kind == "minecraft:model":
            return node["model"]
        if kind == "minecraft:condition":
            require(node["property"] == "minecraft:custom_model_data" and node["index"] == 0, "Grip selector")
            return resolve(node["on_true" if twohand else "on_false"], context,state,twohand,progress)
        if kind == "minecraft:select":
            value = context if node["property"] == "minecraft:display_context" else state
            for case in node["cases"]:
                if value in (case["when"] if isinstance(case["when"], list) else [case["when"]]):
                    return resolve(case["model"], context,state,twohand,progress)
            return resolve(node["fallback"], context,state,twohand,progress)
        require(kind == "minecraft:range_dispatch" and node["index"] == 3, "Aim range selector")
        selection = bisect.bisect_right([f32(e["threshold"]) for e in node["entries"]], f32(progress))-1
        child = node["entries"][selection]["model"] if selection >= 0 else node["fallback"]
        return resolve(child, context,state,twohand,progress)
    graph_checks = 0
    for context in FP:
        for twohand in (False,True):
            style = "twohand" if twohand else "native"
            suffix = "_twohand" if twohand else ""
            for state in ("hip","ads","scope","unknown",None):
                for frame in range(21):
                    for offset in (0,.000001,.001,.002):
                        selected = resolve(documents[AIM_ITEM]["model"],context,state,twohand,f32(f32(frame/20)+f32(offset)))
                        require(selected == f"destiny:{AIM}_{frame:02d}_{style}", "Wrapper sample route mismatch")
                        graph_checks += 1
            selected = resolve(documents[AIM_ITEM]["model"],context,"inspect",twohand,1.002)
            require(selected == "destiny:"+MODEL+"_inspect"+suffix, "Inspect lost to stale progress")
    for context in ("gui","ground","fixed","thirdperson_righthand","thirdperson_lefthand"):
        for state in ("hip","ads","scope","inspect",None):
            for twohand in (False,True):
                key = MODEL + ("_"+state if state not in ("hip",None) else "") + ("_twohand" if twohand else "")
                for item in (NATIVE_ITEM,AIM_ITEM):
                    require(resolve(documents[item]["model"],context,state,twohand,.55) == "destiny:"+key, "Static display route")
                    graph_checks += 1
    # The south lens region is a red reticle ring with transparent center;
    # north artwork is blank. A UV-space error could silently erase the reticle.
    width,height,texels = png_decode(atlases[0])
    def alpha_at(x,y):
        return texels[(y*width+x)*4+3]
    require(alpha_at(20,84) == 0 and alpha_at(10,84) == 255 and alpha_at(20,65) == 255 and alpha_at(20,20) == 0, "Unexpected original lens artwork")
    # Independent source-space ray/OBB slab test. The true optic-center ray
    # must clear all solid original parts, not merely line up two hidden planes.
    source_lens = source["elements"][43]
    ray_origin = [8, (source_lens["from"][1]+source_lens["to"][1])/2,
                  max(e["to"][2] for e in source["elements"])+1]
    for index,cube in enumerate(source["elements"]):
        if index in (43,78):
            continue  # Both opposing plane faces have transparent center UVs.
        angles = [-a for a in cube.get("rotation", [0,0,0])]
        origin = add(cube["origin"], rotate(sub(ray_origin,cube["origin"]),angles))
        direction = rotate([0,0,-1],angles)
        near,far = 0,float("inf")
        for axis in range(3):
            if abs(direction[axis]) < 1e-10:
                if not cube["from"][axis] <= origin[axis] <= cube["to"][axis]:
                    far = -1
            else:
                interval = sorted((cube[field][axis]-origin[axis])/direction[axis] for field in ("from","to"))
                near,far = max(near,interval[0]),min(far,interval[1])
        require(far < near, f"Original geometry blocks center optic ray: {index}")
    return dict(geometryMaxVertexError=max_error, nativeElementCount=len(elements), faceCount=474,
                atlasPixels=[[128,128],[512,512],[512,512]], exactFaceUvScale=.25, adsIdleSightAlignment=alignment,
                hipIdleBoreAlignment=hip_alignment,
                aimSamples=21, aimThresholdOffsetsChecked=[0, .000001, .001, .002],
                ieee754Float32DispatchChecked=True, graphCasesChecked=graph_checks,
                nativeSchemaChecks=True, nativeFullCodecExecuted=False,
                scopeLensSourceElements=[78,43], preservedZeroThicknessPlanes=2,
                rearLensCenterAlpha=0, rearReticleRingAlpha=255, oppositeLensArtworkAlpha=0,
                scopeCenterRaySolidObstructions=0, sourcePartsRayTested=77,
                bothHandsAndBothGripBranches=True, crossbowInverseMaxErrorModelUnits=max_inverse_error,
                thirdPersonBothHandsAndGrips=thirdperson_checks, nativeGameplayVerified=False)


SOURCE_ISSUES = [
    "Two intentional zero-thickness scope planes (43,78), preserved with all opposing face UVs",
    "Lens atlas metadata says uv4x4, but java_block uses project64x64: getUVWidth returns Project.texture_width when per_texture_uv_size is false; native UVs divided by4",
    "Lens north UV region is transparent; south region contains red reticle ring and transparent center, preserved rather than replaced with a synthetic scope",
    "Source first/third-person left and right displays differ; replaced with grip-centered, both-hand native/crossbow-compensated authored poses",
    "Grip centering at full source scale would violate native element bounds; uniformly scaled to5/8, no detail removed or geometry remeshed",
    "Three unrotated outliner groups have origins but no transforms; safe to flatten without baking",
    "Source atlas filenames imply reversed pixel resolutions; embedded PNG headers, not filenames, are authoritative",
    "All30 rotations are supported; no source mesh, no external texture dependency",
]

NOTES = """# W84 Izanagi's Burden model sidecar

Model-only direct conversion of the user-supplied `izanagi.bbmodel`: 79/256 cubes,
474 original face UVs, 30 original rotated cubes, and all three embedded RGBA
PNGs survive. The 128px lens and both 512px atlases are copied byte-for-byte,
without repainting, combining, resizing or sampling new art. All source parts,
including the two zero-thickness scope lens planes, survive. No silhouette proxy.

`source/izanagi.bbmodel` pins the complete original bytes, including embedded
atlases and source metadata, as explicitly requested. The original in Downloads
is read-only and unchanged. The raw copy retains the author's Windows texture
path strings. Author/asset license was not supplied; this local material does
not grant redistribution rights. The weapon design belongs to Bungie.

## Reproduce / verify (no game/editor needed)

    rtk proxy python3 -B scripts/art/build_izanagi_w84.py
    rtk proxy python3 -B scripts/art/build_izanagi_w84.py --verify
    rtk proxy python3 -B scripts/art/build_izanagi_w84.py --source /Users/qf/Downloads/izanagi.bbmodel --verify

Python standard library only. The default input is the pinned raw copy, falling
back to Downloads for first generation. --verify reconstructs everything in
memory, checks exact output bytes/hashes and unexpected owned paths, and writes
nothing. Source SHA mismatch fails before writes. No absolute machine paths or
timestamps are generated except the explicitly preserved raw source metadata.
manifest.json hashes all other outputs and the self-contained generator plus its
W30/W70/W83 convention references. Those earlier files are read, never edited.

## Native model contract

- ID `izanagis_burden`, family `sniper_rifle`, expected runtime grip `TWO_HAND`.
- `destiny:weapon/izanagis_burden`: CMD string0 selects hip/ads/inspect/scope;
  unknown/missing falls back to hip. Every state has boolean0 native/twohand
  branches. Parent registers the model and sets boolean0 for the default grip.
- `destiny:weapon_aim_w70/izanagis_burden`: first-person W70 float3 range dispatch,
  21 exact thresholds0,.05,...,1, with native/twohand branches in every sample.
  Right/left contexts are both present. Inspect wins over stale positive progress.
  Hip/ads/scope strings otherwise use the sampled HIP-to-optic-ADS path; outside
  first person the original static pose selector applies. At1, ADS/scope coincide.
- All model references are internal to these new W84 assets. There is no new
  weapon_scope_w45 dependency, HUD overlay, audio, Java/data or catalog change.
- Rotations use native26.3 `origin` + scalar `x/y/z` + `rescale`; item display
  rotations remain arrays. Native parser was inspected with read-only javap.
  All from/to coordinates stay within [-16,32]. Zero-thickness planes are allowed
  by the native position parser. Full client codec/bake execution is for parent.

## Fidelity / poses / source issues

The native Java authoring model uses the PROJECT64x64 UV space for every atlas,
not the lens's stale per-texture4x4 metadata. Blockbench installed bundle was
read offline: getUVWidth() selects Project.texture_width when the format does
not enable per_texture_uv_size; java_block does not enable that option. Thus
every face UV is divided by4, even the128px lens's [0,32,20.5,52] rear-art region.
The rear-facing south lens has an opaque red reticle ring and a transparent
central aperture; its opposing north artwork is entirely transparent. This is
original art, not a new optical overlay. Source filenames
iza_512/iza_128 disagree with actual PNG dimensions; PNG headers are authoritative.

The rotated center of source element53 (pistol grip) becomes [8,8,8]. All elements
and pivots receive one uniform5/8 scale and translation, needed to retain the
entire long rifle within native coordinate bounds. Relative shapes, rotations,
and UVs are unchanged. The three source groups have identity transforms.

ADS/scope align the centers of the ACTUAL front/rear lens planes (78/43) on the
central idle camera ray. The muzzle axis is parallel, with the physical scope
height above bore retained (not incorrectly pretending both axes coincide).
Hip solves the original muzzle collar's bore intersection with the camera center
ray four blocks ahead. Both hands use native X/YZ reflection, not guessed mirrored
JSON translation. TWO_HAND applies the inverse idle crossbow carrier; it is not
support-hand IK. Both native and twohand third-person transforms cancel the
complete held-item Rx(-90) Ry(180) base, including crossbow arm pose in TWO_HAND,
preserving upright +Y and muzzle -Z on both hands. Native/fullcodec visual tests,
camera bob, swing/reload, active-use/sprint and arm animation remain unverified.

The existing red reticle ring and transparent lens center provide the real
source-authored scope fallback at full ADS/scope. No claim of magnification,
native zoom-shader behavior, or final gameplay verification.

offline-preview.png: top-left side, top-right three-quarter, bottom-left hip,
bottom-right ADS. Exact multi-atlas software z-buffer with front-face culling,
70-degree square camera for lower panels; center marks are red. No native game
renderer, hand mesh, zoom shader, atlas stitching or animated transforms.
pose-checks.json: independent source/native vertex and UV fidelity, atlas bytes,
both-hand optic center and four-block hip zero, source-space scope-center ray
clearance through all77 solid parts, both-grip carrier inverses,
third-person basis axes, all sample routes and IEEE754 float32 offset handling.
"""


def owned_paths():
    paths = {NATIVE_ITEM, AIM_ITEM}
    for directory, pattern in (
        (ASSETS / "models/item/weapon", ID+"*.json"),
        (ASSETS / "models/item/weapon_aim_w70", ID+"*.json"),
        (ASSETS / "textures/item/weapon", ID+"*.png"),
    ):
        paths.update(p.relative_to(ROOT) for p in (ROOT/directory).glob(pattern))
    paths.update(p.relative_to(ROOT) for p in (ROOT/ART).rglob("*") if p.is_file())
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
        default=(ROOT/RAW_SOURCE if (ROOT/RAW_SOURCE).is_file() else Path.home()/"Downloads/izanagi.bbmodel"))
    parser.add_argument("--verify", action="store_true", help="Read-only reconstruction and invariants; never repairs")
    args = parser.parse_args()
    output = build(args.source)
    extra = owned_paths() - output.keys()
    require(not extra, "Unexpected W84 model outputs (not deleted): "+", ".join(map(str,sorted(extra))))
    if args.verify:
        stale = [str(p) for p,raw in output.items() if not (ROOT/p).is_file() or (ROOT/p).read_bytes() != raw]
        require(not stale, "Missing/stale W84 model outputs: "+", ".join(stale))
    else:
        for path,raw in output.items():
            # Re-generation may only update this generator's exact owned outputs.
            (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT/path).write_bytes(raw)
    print(f"W84 {'verified' if args.verify else 'generated'} {len(output)} files; 79/256 cubes, 474 exact UV faces, 30 supported rotations, 21 aim samples; source {SOURCE_SHA256}")


if __name__ == "__main__":
    main()

