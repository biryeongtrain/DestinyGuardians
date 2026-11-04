#!/usr/bin/env python3
"""Read-only Ace.bbmodel conversion, native 26.3 assets and W70 aim samples.

Run with Python 3 (standard library only). --verify reconstructs every output in
memory and never writes. The supplied original is an external, SHA-pinned input;
no Blockbench/Blender process, project state, Gradle or game launch is involved.
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
ART = Path("art/weapons/w83/model")
GENERATOR = Path("scripts/art/build_ace_w83.py")
SOURCE_SHA256 = "f3dbb9ca36733f51c320e71b93ac90c7fa53f17543748d4a96b44beacce47b47"
MAX_CUBES = 256
ID = "ace_of_spades"
MODEL = "item/weapon/" + ID
AIM = "item/weapon_aim_w70/" + ID
FP = ("firstperson_righthand", "firstperson_lefthand")
ADS_EYE_METERS = .42
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
        result["thirdperson_" + hand] = pose([-180 + math.degrees(.1), -180 + math.degrees(.3), 0], [0, -2, 2], .7)
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


def offline_preview(elements, atlas, display):
    """Four software-rasterized views, exact atlas/UVs and a per-pixel z buffer.

    Side / three-quarter above hip / ADS. Static idle FP includes the vanilla
    (.56,-.52,-.72) carrier. This is an authored preview, not a native game bake.
    """
    width = height = 384
    tw, th, texels = png_decode(atlas)
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
    require(sha(raw) == SOURCE_SHA256, "Source SHA differs from supplied original; refusing implicit replacement")
    source = json.loads(raw)
    cubes = source["elements"]
    require(len(cubes) == 87 and len(cubes) <= MAX_CUBES, "Expected original 87 cubes, hard limit 256")
    require(source["meta"]["model_format"] == "java_block", "Expected Java block authoring source")
    require(not source.get("parent") and not source.get("unhandled_root_fields"), "Unconverted source parent/fields")
    require(all(isinstance(n, str) for n in source["outliner"]), "Source groups require explicit transform baking")
    require(set(source["outliner"]) == {e["uuid"] for e in cubes}, "Outliner coverage differs")
    require(len(source["textures"]) == 1, "Expected exactly one source atlas")
    texture = source["textures"][0]
    require(texture["source"].startswith("data:image/png;base64,"), "Atlas must be embedded")
    atlas = base64.b64decode(texture["source"].split(",", 1)[1], validate=True)
    width, height, _ = png_decode(atlas)
    require((width, height) == (512, 512), "Expected supplied 512x512 atlas")
    require(source["resolution"] == dict(width=64, height=64), "Unexpected source UV resolution")
    # Grip center is the rotated center of original element 82 (main handle).
    handle = cubes[82]
    grip = source_point(handle, [(a + b) / 2 for a, b in zip(handle["from"], handle["to"])])
    shift = sub([8, 8, 8], grip)
    elements = []
    mapping = []
    for i, cube in enumerate(cubes):
        require(cube["type"] == "cube" and not cube.get("box_uv"), f"Unsupported source geometry {i}")
        require(cube.get("export", True) and cube.get("visibility", True), f"Hidden source cube {i}")
        require(not cube.get("inflate", 0) and not cube.get("stretch"), f"Unconverted cube deformation {i}")
        require(not cube["rescale"], f"Unexpected source rescale {i}")
        require(all(math.isfinite(v) and -16 <= v <= 32 for field in ("from", "to", "origin") for v in cube[field]), f"Invalid geometry {i}")
        require(all(a < b for a, b in zip(cube["from"], cube["to"])), f"Degenerate cube {i}")
        faces = {}
        require(set(cube["faces"]) == set(DIRECTIONS), f"Unexpected source face set {i}")
        for name, face in cube["faces"].items():
            require(face["texture"] == 0 and set(face) == {"texture", "uv"}, f"Unexpected source face metadata {i}/{name}")
            require(all(math.isfinite(v) and 0 <= v <= 64 for v in face["uv"]), f"Out of atlas UV {i}/{name}")
            faces[name] = dict(uv=[v / 4 for v in face["uv"]], texture="#0")
        element = {"from": rnd(add(cube["from"], shift)), "to": rnd(add(cube["to"], shift)), "faces": faces}
        rotation = cube.get("rotation", [0, 0, 0])
        require(sum(v != 0 for v in rotation) <= 1 and all(v in (-45, -22.5, 0, 22.5, 45) for v in rotation), f"Unexpected rotation {i}")
        if any(rotation):
            # Native 26.3 CuboidModelElement.Deserializer accepts EulerXYZ
            # scalar x/y/z fields, not Blockbench's three-number rotation array.
            element["rotation"] = dict(origin=rnd(add(cube["origin"], shift)),
                                       x=rotation[0], y=rotation[1], z=rotation[2], rescale=False)
        require(all(-16 <= v <= 32 for field in ("from", "to") for v in element[field]), f"Converted bounds {i}")
        elements.append(element)
        mapping.append(dict(index=i, sourceUuid=cube["uuid"], rotated=any(rotation)))
    points = [p for e in elements for p in corners(e)]
    # Two source rail anchors. Pitch brings both onto the same center sight line.
    front = add([8, cubes[7]["to"][1], cubes[7]["from"][2]], shift)
    rear = add([8, cubes[24]["to"][1], (cubes[24]["from"][2] + cubes[24]["to"][2]) / 2], shift)
    delta = sub(front, rear)
    pitch = math.degrees(math.atan2(delta[1], delta[2])) + 180
    pitch = (pitch + 180) % 360 - 180
    sight_y = rotate(sub(front, [8] * 3), [pitch, 0, 0])[1]
    rear_z = rotate(sub(rear, [8] * 3), [pitch, 0, 0])[2]
    # Solve a four-block hip zero from the real source bore, rather than only
    # yawing a generic gun silhouette. Native carrier/translation in model units.
    bore = add([8, (cubes[19]["from"][1] + cubes[19]["to"][1]) / 2, cubes[19]["from"][2]], shift)
    hip_target = [0, 0, -4 * 16]
    target_relative = sub(hip_target, [.56 * 16, -.52 * 16, -.72 * 16 - 2])
    bore_height = (bore[1] - 8) * .85
    hip_pitch = math.atan2(target_relative[1], -target_relative[2]) - math.asin(
        bore_height / math.hypot(target_relative[1], target_relative[2]))
    unpitched = rotate(target_relative, [-math.degrees(hip_pitch), 0, 0])
    hip_yaw = math.degrees(math.atan2(-unpitched[0], -unpitched[2]))
    hip = {context: pose([math.degrees(hip_pitch), hip_yaw, 0], [0, 0, -2], .85) for context in FP}
    hip.update(thirdperson_righthand=pose([-90, 180, 0], [0, 2, 0], .7),
               thirdperson_lefthand=pose([-90, 180, 0], [0, 2, 0], .7),
               gui=centered_context(points, [10, 65, -10]),
               ground=pose([0, 0, 0], [0, 3, 0], .4),
               fixed=centered_context(points, [0, 90, 0]),
               head=pose([0, 0, 0], [0, 8, 0], .6))
    displays = dict(hip=hip)
    ads = copy.deepcopy(hip)
    inspect = copy.deepcopy(hip)
    for context in FP:
        # Native ItemTransform reflects X translation / YZ rotations for left.
        # Both JSON hands must therefore store the SAME pose, including -8.96.
        # W154: measure eye relief from the actual rear rail, not the grip.
        # The previous fixed Z=-4 placed the small rear sight 1.194m away.
        # Move only the ADS assembly closer; preserve its original 87 cubes/UVs,
        # both on-axis anchors, HIP zero and every non-first-person transform.
        ads[context] = pose([pitch, 0, 0], [-.56 * 16, .52 * 16 - sight_y * .95,
                              .72 * 16 - ADS_EYE_METERS * 16 - rear_z * .95], .95)
        inspect[context] = pose([5, 45, -15], [-2, 1, -3], .85)
    displays.update(ads=ads, inspect=inspect, scope=copy.deepcopy(ads))
    output = {}
    def put(path, value):
        output[path] = encode(value)
    put(ASSETS / f"models/{MODEL}.json", dict(
        credit="W83 direct conversion of user-supplied Ace.bbmodel; design belongs to Bungie; source rights not provided",
        ambientocclusion=source.get("ambientocclusion", False),
        gui_light="front" if source.get("front_gui_light") else "side",
        textures={"0": f"destiny:item/weapon/{ID}", "particle": f"destiny:item/weapon/{ID}"},
        elements=elements, display=hip))
    output[ASSETS / f"textures/item/weapon/{ID}.png"] = atlas
    for state, display in displays.items():
        key = MODEL if state == "hip" else MODEL + "_" + state
        if state != "hip":
            put(ASSETS / f"models/{key}.json", dict(parent="destiny:" + MODEL, display=display))
        put(ASSETS / f"models/{key}_twohand.json", dict(parent="destiny:" + key, display=two_hand_display(display)))
    graph = dict(type="minecraft:select", property="minecraft:custom_model_data", index=0,
                 cases=[dict(when=s, model=grip_node(MODEL if s == "hip" else MODEL + "_" + s)) for s in displays],
                 fallback=grip_node(MODEL))
    put(NATIVE_ITEM, dict(model=graph, hand_animation_on_swap=False))
    frames = []
    for frame in range(21):
        display = interpolate(hip, ads, frame)
        key = f"{AIM}_{frame:02d}_native"
        put(ASSETS / f"models/{key}.json", dict(parent="destiny:" + MODEL, display=display))
        two_key = f"{AIM}_{frame:02d}_twohand"
        put(ASSETS / f"models/{two_key}.json", dict(parent="destiny:" + MODEL, display=two_hand_display(display)))
        frames.append(dict(threshold=round(frame / 20, 2), model=dict(
            type="minecraft:condition", property="minecraft:custom_model_data", index=0,
            on_false=model_node(key), on_true=model_node(two_key))))
    aim_range = dict(type="minecraft:range_dispatch", property="minecraft:custom_model_data", index=3,
                     entries=frames, fallback=copy.deepcopy(graph))
    # Same W70 wrapper/float3 architecture, with explicit inspect taking priority
    # so an old positive aim float cannot hide the original static inspect pose.
    aimed = dict(type="minecraft:select", property="minecraft:custom_model_data", index=0,
                 cases=[dict(when="inspect", model=grip_node(MODEL + "_inspect"))], fallback=aim_range)
    wrapper = dict(type="minecraft:select", property="minecraft:display_context",
                   cases=[dict(when=list(FP), model=aimed)], fallback=copy.deepcopy(graph))
    put(AIM_ITEM, dict(model=wrapper, hand_animation_on_swap=False))
    checks = validate(output, source, shift, displays, front, rear, frames, bore)
    put(ART / "pose-checks.json", checks)
    output[ART / "offline-preview.png"] = offline_preview(elements, atlas, displays)
    output[ART / "README.md"] = NOTES.encode()
    inputs = {str(GENERATOR): sha((ROOT / GENERATOR).read_bytes())}
    for path in (Path("scripts/build_weapons_w30.py"), Path("scripts/generate_aim_models_w70.py")):
        inputs[str(path)] = sha((ROOT / path).read_bytes())
    manifest = dict(schema=1, stage="W83", generator=str(GENERATOR), itemModel="destiny:weapon/" + ID,
        aimItemModel="destiny:weapon_aim_w70/" + ID, target="Minecraft Java 26.3",
        source=dict(filename="Ace.bbmodel", sha256=SOURCE_SHA256, bytes=len(raw), externalReadOnly=True,
                    originalCopied=False, authorAndLicense="Not supplied; Destiny/Ace design belongs to Bungie",
                    format=source["meta"], display=source["display"], textureSha256=sha(atlas), texturePixels=[width, height],
                    uvResolution=[64, 64], uvScaleToNative=.25, embeddedPngCopiedByteForByte=True),
        conversion=dict(method="One source cube to one native element; uniform grip translation only; no remesh/repaint",
                        sourceCubes=len(cubes), outputCubes=len(elements), cubeLimit=MAX_CUBES,
                        sourceFaces=522, outputFaces=522, rotatedCubes=sum(any(c.get("rotation", [])) for c in cubes),
                        unsupportedRotations=0, rotationSchema="26.3 origin + scalar x/y/z + rescale; native EulerXYZ",
                        sourceGrip=rnd(grip), geometryTranslation=rnd(shift), geometryScale=1,
                        mapping=mapping),
        aim=dict(progressFloatIndex=3, gripBooleanIndex=0, poseStringIndex=0, samples=21,
                 thresholds=[e["threshold"] for e in frames], offsetTolerance=0.002,
                 floatRoundingTolerance=1e-6, interpolation="Linear Euler/translation/scale; sampled, not render-frame interpolation",
                 inspectPriority=True, hipBoreZeroDistanceBlocks=4,
                 scope="Same iron-sight ADS pose; no magnifying optic/overlay",
                 rearSightEyeMeters=ADS_EYE_METERS, poseRevision="W154 closer readable rear sight"),
        sourceIssues=["Source RH first-person scale4/translation[25.5,-4.75,-37.75] and LH pose are asymmetric; replaced with authored grip-centered poses",
                      "Source third-person rotations absent; invert the complete vanilla held-item Rx-90 Ry180 base, preserving both up and muzzle axes",
                      "512px texture uses 64-unit authoring UVs: every face coordinate divided by4 for native 16-unit UVs",
                      "No unsupported geometry/rotations, no source mesh, no group transforms, no external texture dependency"],
        verification=dict(generatorReconstruction=True, nativeGameplayVerified=False, nativeCodecExecuted=False,
                          rotationParserInspected="Local 26.3 CuboidModelElement.Deserializer via javap, read only",
                          limitations=["Static idle aim mathematics and software preview only; native bake/camera/FOV/hand animation pending parent",
                                       "Twohand inverse matches W30 crossbow idle; active item-use/swing/sprint/animation/IK not modeled",
                                       "Source handle/rail anchors are authored from source parts, not measured gameplay motion",
                                       "Original external Ace.bbmodel with pinned SHA required for regenerate/verify"]),
        inputSha256=inputs, outputSha256={str(p): sha(b) for p, b in sorted(output.items())})
    put(ART / "manifest.json", manifest)
    return output


def validate(output, source, shift, displays, front, rear, frames, bore):
    """Independent invariants for geometry/UV fidelity, pose math and graph refs."""
    documents = {p: json.loads(b) for p, b in output.items() if p.suffix == ".json"}
    elements = documents[ASSETS / f"models/{MODEL}.json"]["elements"]
    max_error = 0
    for cube, element in zip(source["elements"], elements):
        expected = [add(source_point(cube, p), shift) for p in itertools.product(*zip(cube["from"], cube["to"]))]
        for a, b in zip(expected, corners(element)):
            max_error = max(max_error, max(abs(x - y) for x, y in zip(a, b)))
        for name, face in cube["faces"].items():
            require(element["faces"][name]["uv"] == [x / 4 for x in face["uv"]], "UV changed")
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
    for frame in range(21):
        for offset in (0, .000001, .001, .002):
            require(bisect.bisect_right(thresholds, frame / 20 + offset) - 1 == frame, "CMD offset selects wrong frame")
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
    return dict(geometryMaxVertexError=max_error, nativeElementCount=len(elements), faceCount=522,
                atlasPixels=[512, 512], exactFaceUvScale=.25, adsIdleSightAlignment=alignment,
                hipIdleBoreAlignment=hip_alignment,
                aimSamples=21, aimThresholdOffsetsChecked=[0, .000001, .001, .002],
                bothHandsAndBothGripBranches=True, crossbowInverseMaxErrorModelUnits=max_inverse_error,
                thirdPersonBothHandsAndGrips=thirdperson_checks, nativeGameplayVerified=False)


NOTES = """# W83 Ace of Spades model sidecar

Direct conversion of the supplied `Ace.bbmodel`: all 87 cubes, all 522 face UVs,
all 41 rotated cubes and the embedded 512x512 RGBA PNG survive. No silhouette
substitute, voxel reconstruction, palette repaint or resampling. Geometry only
receives one uniform translation: the rotated center of source element82 (main
grip) becomes [8,8,8]. Per-face 64-unit authoring UVs become native 16-unit UVs by
division by4, including reversed rectangles. PNG bytes remain identical.

The original stays external/read-only; its SHA256 and source display settings are
in manifest.json. No full bbmodel copy, author filesystem paths or embedded project
metadata are distributed. Attribution/license beyond the Bungie design was not
supplied. This is local review material, not a license grant.

From the repository root:

    rtk proxy python3 scripts/art/build_ace_w83.py
    rtk proxy python3 scripts/art/build_ace_w83.py --verify
    rtk proxy python3 scripts/art/build_ace_w83.py --source /path/to/Ace.bbmodel --verify

Python standard library only. The source SHA is pinned and mismatches fail before
writes. --verify rebuilds every output in memory, checks exact bytes and unexpected
Ace output files, and never repairs/writes. Manifest hashes cover all generated
outputs except itself; the generator is an input hash. No timestamps or absolute
machine paths enter output. The source itself is needed to reproduce the outputs.

Item identifiers:

- destiny:weapon/ace_of_spades: CMD string0 hip/ads/inspect/scope; missing/unknown
  uses hip. Scope intentionally aliases iron-sight ADS, without an optic overlay.
- destiny:weapon_aim_w70/ace_of_spades: W70 display-context wrapper and float3
  range dispatch; 21 samples at0,.05,...,1. Boolean0 selects native/twohand in
  every frame. Inspect takes priority over stale positive aim progress. Other
  display contexts use the original static pose select. Runtime/catalog belong
  to the parent task. Every model reference resolves inside these new Ace assets.

The source RH first-person scale4 and translation[25.5,-4.75,-37.75] differ from
its LH pose; source third-person rotation is absent. These displays are replaced
with authored transforms. Native first-person left-hand X translation and Y/Z
rotation reflection happens in ItemTransform, so both JSON hands store the same
pose. ADS aligns two selected source rail anchors to the idle camera center ray;
hip solves pitch/yaw for the actual barrel bore to meet that ray four blocks
ahead, retaining a lower-right resting position. Third-person [-90,180,0] inverts
the complete vanilla ItemInHandLayer Rx(-90) Ry(180), retaining both upright +Y
and forward -Z geometry, with the handle at the held-item pivot. The W30 Rx90
alone would retain muzzle direction but turn the source upside down here.
Twohand follows W30's first-person carrier inverse; its third-person rotation also
inverts the level-head primary crossbow arm Ry(-.3*sign) Rx(-pi/2+.1) from native
AnimationUtils.animateCrossbowHold. Both hands and all three basis axes are
checked. These are static mathematical poses, not runtime IK.

Native26.3 CuboidModelElement.Deserializer was inspected from the existing local
Minecraft jar via read-only javap. It accepts rotation origin + scalar x/y/z +
rescale (EulerXYZ); all source rotations are supported. Item display rotations
remain ordinary [x,y,z] EulerXYZ arrays. Source rotations are single-axis, so no
Blockbench/native multi-axis order ambiguity arises.

offline-preview.png is a deterministic software z-buffer preview with the exact
atlas: top-left side; top-right three-quarter; bottom-left hip; bottom-right ADS.
Bottom views use a70-degree square camera and idle vanilla carrier, with red
center marks. Lighting is illustrative. It does not reproduce Minecraft atlas
stitching, native bake, hands, FOV changes, bob/swing, reload, active item use,
third-person arm animation or clipping under every runtime condition.

pose-checks.json records independent geometry-vertex, UV, reference-resolution,
both-hand ADS center, twohand carrier inverse, threshold-offset and third-person
axis checks. Native codec execution, native visual testing, runtime/catalog and
gameplay verification remain the parent task's responsibility. No Gradle/game
launch, production Java/data edit or Blockbench/Blender interaction was used.
"""


def owned_paths():
    paths = {NATIVE_ITEM, AIM_ITEM}
    for directory, pattern in (
        (ASSETS / "models/item/weapon", ID + "*.json"),
        (ASSETS / "models/item/weapon_aim_w70", ID + "*.json"),
        (ASSETS / "textures/item/weapon", ID + "*.png"),
    ):
        paths.update(p.relative_to(ROOT) for p in (ROOT / directory).glob(pattern))
    paths.update(p.relative_to(ROOT) for p in (ROOT / ART).rglob("*") if p.is_file())
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home() / "Downloads/Ace.bbmodel")
    parser.add_argument("--verify", action="store_true", help="Read-only byte reconstruction and invariant checks")
    args = parser.parse_args()
    output = build(args.source)
    extra = owned_paths() - output.keys()
    require(not extra, "Unexpected Ace outputs (not deleted): " + ", ".join(map(str, sorted(extra))))
    if args.verify:
        stale = [str(p) for p, raw in output.items() if not (ROOT / p).is_file() or (ROOT / p).read_bytes() != raw]
        require(not stale, "Missing/stale W83 outputs: " + ", ".join(stale))
    else:
        for path, raw in output.items():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(raw)
    print(f"W83 {'verified' if args.verify else 'generated'} {len(output)} files; 87/256 cubes, 522 exact UV faces, 21 aim samples; source {SOURCE_SHA256}")


if __name__ == "__main__":
    main()
