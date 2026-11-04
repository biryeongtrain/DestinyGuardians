#!/usr/bin/env python3
"""W201 authored first-person gloves. Stdlib only; no DCC, build, or skin access.

Run from this worktree: rtk proxy python3 scripts/art/build_first_person_gloves_w201.py
--verify regenerates in memory and compares bytes, without writing any files.
The preview rasterizes the exported JSON face layout, rotations and atlas UVs.
"""
import argparse
import hashlib
import json
import math
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = "scripts/art/build_first_person_gloves_w201.py"
ART = "art/weapons/w201/gloves.json"
PREVIEW = "art/weapons/w201/gloves-preview.png"
RIGHT = "src/main/resources/assets/destiny/models/weapon_hands_w201/glove_right.json"
LEFT = "src/main/resources/assets/destiny/models/weapon_hands_w201/glove_left.json"
TEXTURE = "src/main/resources/assets/destiny/textures/item/weapon_hands_w201/gloves.png"
REPORT = "docs/qa/2026-10-27/w201/art-report.md"
SLOT = "destiny:item/weapon_hands_w201/gloves"
FACES = ("down", "up", "north", "south", "west", "east")
MATERIALS = ("palm_textile", "dorsal_plate", "knuckle_plate", "finger_textile",
             "thumb_textile", "wrist_cuff", "forearm_textile", "forearm_plate")
ANCHOR = [8, 8, 8]
SIZE = 256


def encode_json(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def png(width, height, pixels):
    """Stable RGB PNG: explicit filter 0, zlib stored blocks, no metadata/time.

    Uncompressed DEFLATE makes bytes independent of local zlib compressor tuning.
    """
    raw = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3]
                   for y in range(height))
    stream = bytearray(b"\x78\x01")
    for start in range(0, len(raw), 65535):
        block = raw[start:start + 65535]
        stream.append(int(start + len(block) == len(raw)))
        stream.extend(struct.pack("<HH", len(block), len(block) ^ 65535))
        stream.extend(block)
    stream.extend(struct.pack(">I", zlib.adler32(raw)))

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", bytes(stream)) + chunk(b"IEND", b""))


def pixel(buf, width, x, y, color):
    height = len(buf) // (width * 3)
    if 0 <= x < width and 0 <= y < height:
        offset = (y * width + x) * 3
        buf[offset:offset + 3] = bytes(color)


def rectangle(buf, width, x0, y0, x1, y1, color):
    height = len(buf) // (width * 3)
    x0, x1 = max(0, x0), min(width, x1)
    if x1 <= x0:
        return
    stripe = bytes(color) * (x1 - x0)
    for y in range(max(0, y0), min(height, y1)):
        offset = (y * width + x0) * 3
        buf[offset:offset + len(stripe)] = stripe


def atlas():
    pixels = bytearray(bytes((23, 27, 31)) * SIZE * SIZE)
    for material_index, material in enumerate(MATERIALS):
        for face_index, face in enumerate(FACES):
            tile = material_index * 6 + face_index
            tx, ty = tile % 8 * 32, tile // 8 * 32
            plate = material.endswith("plate")
            for y in range(32):
                for x in range(32):
                    edge = min(x, y, 31 - x, 31 - y)
                    if plate:
                        base = (190, 194, 183)
                        if edge < 3:
                            base = (50, 57, 59)
                        elif edge == 3:
                            base = (121, 104, 75)  # restrained bronze perimeter
                        elif edge == 4:
                            base = (216, 218, 206)
                        elif (x == 8 and 10 <= y <= 23) or (y == 24 and 8 <= x <= 23):
                            base = (151, 157, 150)  # quiet recessed plate seam
                        elif material == "forearm_plate" and 13 <= x <= 18 and 11 <= y <= 18:
                            base = (165, 174, 169)  # unbranded inset, no official insignia
                    else:
                        base = (42, 48, 53) if material != "forearm_textile" else (35, 42, 47)
                        if (x + y) % 8 == 0:
                            base = tuple(c + 4 for c in base)  # low contrast woven ribs
                        if edge < 3:
                            base = (29, 34, 39)
                        if edge == 4 and material in ("wrist_cuff", "forearm_textile", "palm_textile"):
                            base = (105, 90, 66)
                        if material == "wrist_cuff" and 13 <= y <= 17:
                            base = (71, 78, 80)
                        if material in ("finger_textile", "thumb_textile") and y in (11, 20) and 6 <= x <= 25:
                            base = (64, 71, 73)  # flexure bands, not extra geometry
                    # Direction-specific tiles, shallow baked edge contrast only.
                    factor = {"up": 1.04, "down": .94}.get(face, 1.0)
                    pixel(pixels, SIZE, tx + x, ty + y, tuple(min(255, round(c * factor)) for c in base))
    return pixels


def uv_for(material, face):
    tile = MATERIALS.index(material) * 6 + FACES.index(face)
    # One-pixel replicated-material gutter; UV units are 0..16, not atlas pixels.
    x, y = tile % 8 * 32, tile // 8 * 32
    return [round(v / 16, 4) for v in (x + 1, y + 1, x + 31, y + 31)]


def cuboid(name, lo, hi, material, rotation=None):
    item = {"name": "right_" + name,
            "from": [round(v + 8, 4) for v in lo],
            "to": [round(v + 8, 4) for v in hi],
            "faces": {face: {"uv": uv_for(material, face), "texture": "#0"} for face in FACES}}
    if rotation:
        origin, axis, angle = rotation
        item["rotation"] = {"origin": [v + 8 for v in origin], "axis": axis,
                            "angle": angle, "rescale": False}
    return item


def models():
    elements = []

    def add(name, lo, hi, material, rotation=None):
        elements.append(cuboid(name, lo, hi, material, rotation))

    add("palm_outer_textile", (.61, -1.03, -.58), (1.35, 1.20, .78), "palm_textile")
    add("dorsal_upper_plate", (1.35, .13, -.46), (1.50, 1.05, .63), "dorsal_plate")
    add("dorsal_lower_plate", (1.35, -.94, -.39), (1.48, .04, .65), "dorsal_plate")
    for finger, bottom, top in (("index", .67, 1.16), ("middle", .10, .61),
                                ("ring", -.44, .04), ("little", -.98, -.50)):
        front = -1.14 if finger == "index" else -1.06
        add(finger + "_proximal", (.60, bottom, front + .05), (1.36, top, -.51), "finger_textile")
        add(finger + "_curl_bridge", (-.66, bottom, front), (.64, top, -.70), "finger_textile")
        add(finger + "_return_tip", (-.88, bottom + .025, front + .05),
            (-.58, top - .025, -.14 if finger == "index" else -.10), "finger_textile")
        add(finger + "_knuckle_cap", (1.30, bottom + .035, -.98),
            (1.49, top - .035, -.54), "knuckle_plate")
    add("thumb_root", (.61, .62, .60), (1.24, 1.16, 1.12), "thumb_textile")
    add("thumb_opposition", (-.27, .76, .70), (.76, 1.22, 1.12), "thumb_textile")
    add("thumb_folded_tip", (-.73, .68, .70), (-.20, 1.16, 1.06), "thumb_textile")
    add("wrist_flex_cuff", (.50, -1.92, -.06), (1.60, -1.00, 1.55), "wrist_cuff")
    add("wrist_outer_guard", (1.60, -1.91, .10), (1.77, -1.23, 1.42), "dorsal_plate")
    forearm_rotation = ((1.15, -1.72, 1.05), "x", -22.5)
    add("short_forearm_fabric", (.45, -6.46, .20), (2.05, -1.70, 2.10),
        "forearm_textile", forearm_rotation)
    add("short_forearm_dorsal_plate", (2.05, -6.22, .33), (2.23, -1.88, 1.95),
        "forearm_plate", forearm_rotation)
    right = {"credit": "Original W201 Hunter-inspired cosmetic glove; not extracted or official.",
             "texture_size": [SIZE, SIZE], "textures": {"0": SLOT, "particle": SLOT},
             "elements": elements}
    left = json.loads(json.dumps(right))
    for item in left["elements"]:
        item["name"] = item["name"].replace("right_", "left_", 1)
        item["from"][0], item["to"][0] = round(16 - item["to"][0], 4), round(16 - item["from"][0], 4)
        if "rotation" in item:
            item["rotation"]["origin"][0] = round(16 - item["rotation"]["origin"][0], 4)
        # Mirror atlas U for each mirrored surface, swapping the X-normal faces.
        old = item["faces"]
        item["faces"] = {}
        for face in FACES:
            other = {"east": "west", "west": "east"}.get(face, face)
            item["faces"][face] = dict(old[other])
            u0, v0, u1, v1 = old[other]["uv"]
            item["faces"][face]["uv"] = [u1, v0, u0, v1]
    return right, left


def vertices(item, face):
    x0, y0, z0 = item["from"]
    x1, y1, z1 = item["to"]
    # Vanilla FaceInfo order: TL, BL, BR, TR as seen from outside.
    result = {
        "down": [(x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)],
        "up": [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)],
        "north": [(x1, y1, z0), (x1, y0, z0), (x0, y0, z0), (x0, y1, z0)],
        "south": [(x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1)],
        "west": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
        "east": [(x1, y1, z1), (x1, y0, z1), (x1, y0, z0), (x1, y1, z0)],
    }[face]
    if "rotation" in item:
        rot = item["rotation"]
        assert rot["axis"] == "x"
        ox, oy, oz = rot["origin"]
        angle = math.radians(rot["angle"])
        c, s = math.cos(angle), math.sin(angle)
        result = [(x, oy + c * (y - oy) - s * (z - oz), oz + s * (y - oy) + c * (z - oz))
                  for x, y, z in result]
    return result


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    length = math.sqrt(dot(a, a))
    return tuple(x / length for x in a)


# Embedded 5x7 font keeps PNG rendering deterministic and independent of OS fonts.
GLYPHS = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-+.:=()",
    ("01110100011000111111100011000110001", "11110100011000111110100011000111110",
     "01111100001000010000100001000001111", "11110100011000110001100011000111110",
     "11111100001000011110100001000011111", "11111100001000011110100001000010000",
     "01111100001000010111100011000101111", "10001100011000111111100011000110001",
     "11111001000010000100001000010011111", "00111000100001000010100101001001100",
     "10001100101010011000101001001010001", "10000100001000010000100001000011111",
     "10001110111010110101100011000110001", "10001110011010110011100011000110001",
     "01110100011000110001100011000101110", "11110100011000111110100001000010000",
     "01110100011000110001101011001001101", "11110100011000111110101001001010001",
     "01111100001000001110000010000111110", "11111001000010000100001000010000100",
     "10001100011000110001100011000101110", "10001100011000110001100010101000100",
     "10001100011000110101101011101110001", "10001100010101000100010101000110001",
     "10001100010101000100001000010000100", "11111000010001000100010001000011111",
     "01110100011001110101110011000101110", "00100011000010000100001000010001110",
     "01110100010000100010001000100011111", "11110000010000101110000010000111110",
     "00010001100101010010111110001000010", "11111100001000011110000010000111110",
     "01110100001000011110100011000101110", "11111000010001000100010000100001000",
     "01110100011000101110100011000101110", "01110100011000101111000010000101110",
     "00001000100001000100010000100010000", "00000000000000011111000000000000000",
     "00000001000010011111001000010000000", "00000000000000000000000000011000110",
     "00000001100011000000001100011000000", "00000000001111100000111110000000000",
     "00010001000100001000010000010000010", "01000001000001000010000100010001000")))


def text(buf, width, x, y, value, color=(218, 225, 227), scale=2):
    for letter in value.upper():
        pattern = GLYPHS.get(letter, "0" * 35)
        for row in range(7):
            for col in range(5):
                if pattern[row * 5 + col] == "1":
                    rectangle(buf, width, x + col * scale, y + row * scale,
                              x + (col + 1) * scale, y + (row + 1) * scale, color)
        x += 6 * scale


def render_panel(canvas, width, ox, oy, model, texture, camera, grip=False):
    panel_width, panel_height = 448, 322
    cam = unit(camera)
    right = unit(cross((0, 1, 0), cam))
    up = unit(cross(cam, right))
    light = unit(tuple(cam[i] * .65 + up[i] * .7 - right[i] * .35 for i in range(3)))
    center = (8, 6.15, 9)
    scale = 45
    depth = [-1e10] * (panel_width * panel_height)

    def projection(p):
        p = sub(p, center)
        return (panel_width / 2 + dot(p, right) * scale,
                panel_height / 2 - dot(p, up) * scale, dot(p, cam))

    elements = list(model["elements"])
    if grip:
        guide = cuboid("preview_only_grip", (-.55, -1.65, -.65), (.55, 1.75, .65), "palm_textile")
        guide["guide"] = True
        elements.append(guide)
    for item in elements:
        for face in FACES:
            world = vertices(item, face)
            normal = unit(cross(sub(world[1], world[0]), sub(world[3], world[0])))
            if dot(normal, cam) <= 0:
                continue
            shade = .53 + .47 * max(0, dot(normal, light))
            points = [projection(p) for p in world]
            u0, v0, u1, v1 = item["faces"][face]["uv"]
            uv = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
            for triangle in ((0, 1, 2), (0, 2, 3)):
                a, b, c = [points[i] for i in triangle]
                ua, ub, uc = [uv[i] for i in triangle]
                denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(denominator) < 1e-10:
                    continue
                for y in range(max(0, math.floor(min(a[1], b[1], c[1]))),
                               min(panel_height, math.ceil(max(a[1], b[1], c[1])))):
                    for x in range(max(0, math.floor(min(a[0], b[0], c[0]))),
                                   min(panel_width, math.ceil(max(a[0], b[0], c[0])))):
                        px, py = x + .5, y + .5
                        w0 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / denominator
                        w1 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / denominator
                        w2 = 1 - w0 - w1
                        if min(w0, w1, w2) < -1e-8:
                            continue
                        z = w0 * a[2] + w1 * b[2] + w2 * c[2]
                        index = y * panel_width + x
                        if z <= depth[index]:
                            continue
                        depth[index] = z
                        if item.get("guide"):
                            color = (45, 128, 146)
                        else:
                            u = sum(w * p[0] for w, p in zip((w0, w1, w2), (ua, ub, uc)))
                            v = sum(w * p[1] for w, p in zip((w0, w1, w2), (ua, ub, uc)))
                            ix, iy = min(255, max(0, int(u * 16))), min(255, max(0, int(v * 16)))
                            offset = (iy * SIZE + ix) * 3
                            color = texture[offset:offset + 3]
                        pixel(canvas, width, ox + x, oy + y, tuple(round(q * shade) for q in color))


def preview(right, left, texture):
    width, height = 1440, 992
    canvas = bytearray(bytes((16, 22, 29)) * width * height)
    text(canvas, width, 28, 26, "W201 / HUNTER GLOVE STUDY", scale=3)
    text(canvas, width, 28, 63, "ORIGINAL COSMETICS / 26 CUBOIDS PER HAND / 256 ATLAS", (157, 173, 184))
    views = (("RIGHT / FRONT THREE QUARTER", right, (1.4, .7, -1.8), True),
             ("RIGHT / INNER PALM + THUMB", right, (-1.8, 1.2, 1.8), False),
             ("RIGHT / DORSAL + SHORT ARM", right, (2.8, .4, 1.4), False),
             ("LEFT / MIRRORED THREE QUARTER", left, (-1.4, .7, -1.8), True),
             ("RIGHT / MUZZLE SIDE -Z", right, (0, .12, -1), True))
    for index, (label, model, camera, grip) in enumerate(views):
        x, y = 24 + index % 3 * 472, 106 + index // 3 * 418
        rectangle(canvas, width, x, y, x + 448, y + 398, (24, 32, 41))
        text(canvas, width, x + 12, y + 16, label, (190, 203, 211), scale=1)
        rectangle(canvas, width, x + 12, y + 36, x + 436, y + 37, (70, 81, 87))
        render_panel(canvas, width, x, y + 45, model, texture, camera, grip)
        text(canvas, width, x + 12, y + 373,
             "CYAN = 1.1 X 1.3 TEST GRIP" if grip else
             ("OPEN GRIP CHANNEL / OPPOSED THUMB" if index == 1 else "OUTER PALE PLATES / CHARCOAL FABRIC"),
             (102, 175, 186) if grip else (160, 167, 164), scale=1)
    x, y = 968, 524
    rectangle(canvas, width, x, y, x + 448, y + 398, (24, 32, 41))
    text(canvas, width, x + 12, y + 16, "AUTHORED ATLAS / FACE-SPECIFIC UVS", scale=1)
    for ty in range(SIZE):
        start = ty * SIZE * 3
        target = ((y + 47 + ty) * width + x + 16) * 3
        canvas[target:target + SIZE * 3] = texture[start:start + SIZE * 3]
    for yy, line in enumerate(("8 MATERIALS", "6 FACES EACH", "NO ALPHA", "NO SKIN", "NO RIP", "BRONZE SEAMS")):
        text(canvas, width, x + 292, y + 74 + yy * 29, line, (168, 180, 186), scale=1)
    text(canvas, width, x + 16, y + 324, "ANCHOR (8,8,8) / Y UP / MUZZLE -Z", scale=1)
    text(canvas, width, x + 16, y + 347, "RIGHT PALM +X / LEFT PALM -X", scale=1)
    text(canvas, width, x + 16, y + 373, "BASE MODELS HAVE NO DISPLAY TRANSFORMS", scale=1)
    text(canvas, width, 28, 951, "OFFLINE JSON + UV CPU RENDER / CYAN GRIP IS A PREVIEW GUIDE / NATIVE COMBAT + RELOAD CHECKS PENDING",
         (154, 171, 184), scale=1)
    return png(width, height, canvas)


def bounds(model):
    points = [p for item in model["elements"] for face in FACES for p in vertices(item, face)]
    return {"min": [round(min(p[k] for p in points), 4) for k in range(3)],
            "max": [round(max(p[k] for p in points), 4) for k in range(3)]}


def validate(right, left):
    for model in (right, left):
        assert len(model["elements"]) == 26
        assert not {"display", "parent", "vertices", "triangles"}.intersection(model)
        assert model["textures"] == {"0": SLOT, "particle": SLOT}
        assert len({item["name"] for item in model["elements"]}) == 26
        for item in model["elements"]:
            assert all(0 <= a < b <= 16 for a, b in zip(item["from"], item["to"]))
            assert set(item["faces"]) == set(FACES)
            for face in FACES:
                uv = item["faces"][face]["uv"]
                assert len(uv) == 4 and all(0 <= x <= 16 for x in uv)
                assert uv[0] != uv[2] and uv[1] != uv[3]
                assert item["faces"][face]["texture"] == "#0"
                assert "cullface" not in item["faces"][face]
            # Palm/fingers leave a grip cavity; cuff below the palm may widen.
            points = [p for face in FACES for p in vertices(item, face)]
            x0, x1 = min(p[0] for p in points), max(p[0] for p in points)
            y0, y1 = min(p[1] for p in points), max(p[1] for p in points)
            z0, z1 = min(p[2] for p in points), max(p[2] for p in points)
            assert y1 <= 7.0 or y0 >= 9.25 or x1 <= 7.45 or x0 >= 8.55 or z1 <= 7.35 or z0 >= 8.65, item["name"]
    for r, l in zip(right["elements"], left["elements"]):
        rp = sorted(tuple(round(v, 7) for v in (16 - p[0], p[1], p[2]))
                    for face in FACES for p in vertices(r, face))
        lp = sorted(tuple(round(v, 7) for v in p) for face in FACES for p in vertices(l, face))
        assert rp == lp, r["name"]
        # Verify texel orientation against physically reflected vanilla corners.
        for face in FACES:
            other = {"east": "west", "west": "east"}.get(face, face)
            ruv, luv = r["faces"][face]["uv"], l["faces"][other]["uv"]
            def pairs(item, key, uv):
                a, b, c, d = uv
                return list(zip(vertices(item, key), ((a, b), (a, d), (c, d), (c, b))))
            for p, uv in pairs(r, face, ruv):
                reflected = (16 - p[0], p[1], p[2])
                matching = [q_uv for q, q_uv in pairs(l, other, luv)
                            if max(abs(a - b) for a, b in zip(q, reflected)) < 1e-7]
                assert matching == [uv], (r["name"], face, uv, matching)


def metadata(right, left):
    return {
        "schemaVersion": 1, "batch": "W201", "feature": "w201-hands-art",
        "authorship": "Original authored Minecraft cuboids and pixel atlas; Hunter-inspired cosmetics.",
        "sourceLimits": ["No extracted mesh, texture, player skin, or animation data used.",
                         "No official Bungie asset, replica accuracy, or player-skin matching claim.",
                         "Skill Ace/Izanagi study used for clean volumes and explicit face UVs only.",
                         "Static curled cosmetic pose; named finger segments are not animated bones.",
                         "Offline preview is not evidence of native pack load, contact, or performance."],
        "design": {"palette": {"textile": "dark charcoal", "plates": "pale gray ivory",
                                  "seams": "muted bronze"},
                   "identity": "compact armored dorsal plates, four articulated curls, opposed thumb, short angled cuff",
                   "geometry": "26 named cuboids per hand; no meshes, alpha cutouts, or noisy stacked micro-layers",
                   "wristForearmNominalLengthUnits": 4.46,
                   "wristForearmDownwardSpanUnits": round(7.0 - bounds(right)["min"][1], 4),
                   "palmAndFingersBoundsRelativeToGrip": {"min": [-.88, -1.03, -1.14], "max": [1.50, 1.22, 1.12]}},
        "gripOrigin": ANCHOR,
        "coordinateSpace": "Minecraft item model units; 16 units per item block, no display transform",
        "directions": {"weaponGripAxis": "+Y", "muzzle": "-Z", "rightPalmOutside": "+X",
                       "rightFingerCurl": "+X around front -Z, returning toward -X",
                       "rightForearm": "-Y and +Z, with a small +X offset",
                       "left": "exact X reflection around x=8; same grip origin and muzzle sign"},
        "gripClearance": {"widthX": 1.1, "depthZ": 1.3,
                          "minXZ": [7.45, 7.35], "maxXZ": [8.55, 8.65],
                          "test": "All transformed element AABBs miss the core for all Y.",
                          "minimumAxisGapUnits": .03,
                          "limit": "Larger grips, trigger guards and weapon bodies require master contact adjustment."},
        "integration": {"pivot": ANCHOR, "baseDisplayTransforms": False,
                        "pointTransform": "p_out = anchor_target + R * S * (p_model - [8,8,8])",
                        "nativeItemCenter": "Vanilla item geometry may subtract 0.5 block; [8,8,8] then maps to local zero.",
                        "masterOwns": "Item registration, graph overlays, weapon anchors, camera transforms and reload motion.",
                        "displayScale": "Inherits each weapon's display scale in the master graph; base gloves add no scale.",
                        "skinPolicy": "Opaque authored gloves; no player skin sampling or promise."},
        "texture": {"path": TEXTURE, "resource": SLOT, "size": [SIZE, SIZE],
                    "format": "RGB PNG, opaque", "materials": list(MATERIALS),
                    "faceTiles": 48, "tilePixels": 32, "gutterPixels": 1,
                    "uvUnits": "0..16; reversed ranges intentional for mirrored hand"},
        "models": {"right": {"path": RIGHT, "resource": "destiny:weapon_hands_w201/glove_right",
                              "elements": 26, "faces": 156, "bounds": bounds(right)},
                   "left": {"path": LEFT, "resource": "destiny:weapon_hands_w201/glove_left",
                             "elements": 26, "faces": 156, "bounds": bounds(left)}},
        "elementsCounts": {"right": 26, "left": 26, "simultaneousPair": 52},
        "preview": {"path": PREVIEW, "renderer": "stdlib textured triangle rasterizer, orthographic Z buffer",
                    "views": ["right front three-quarter", "right inner palm", "right dorsal/rear",
                              "left front three-quarter", "right muzzle side -Z", "atlas"],
                    "testGrip": "Preview-only cyan 1.1 X 1.3 guide, not emitted into glove models."},
        "nativeChecksNeeded": ["Register/load both item models and resolve texture in the master's pack.",
                               "Ace, Duke, Izanagi and Ammit: check hip fire, ADS/combat, trigger and sight occlusion.",
                               "Check reload phases and support-hand movement with inherited per-weapon display scale.",
                               "Check centered-anchor scale/rotation and left mirror in the native renderer.",
                               "Briefly inspect 10-20 displayed assemblies for visible artifacts or stutter."],
    }


def report(outputs):
    hashes = "\n".join(f"- `{path}`: `{hashlib.sha256(value).hexdigest()}`" for path, value in outputs.items())
    return ("""# W201 hands art — offline handoff

Ready for master integration: 26 named cuboids / 156 UV faces per hand (52 per pair).
Original charcoal textile, pale dorsal/knuckle armor, bronze seams, four segmented
finger curls and an opposed thumb. No extracted mesh, skin, official texture or
animation data; no official asset or player-skin matching claim. Read AGENTS.md,
RTK, the requested weapon-art skill and its Ace/Izanagi study; the study informs
clean volumes and face UVs, not copied ornamentation.

## Contract

Item-unit grip origin `[8,8,8]`; grip +Y, muzzle -Z, right palm outside +X,
fingers curl across -Z toward -X. Left reflects X about x=8. Palm/finger bounds
are 2.38 X 2.25 X 2.26 units; short wrist/forearm reaches about 5.33 units below
the palm, down/back (+Z) and slightly outward. The 1.1 X 1.3 palm grip core stays
empty with >=0.03 axis clearance at Y7..9.25; the lower cuff can widen. No base display transform or parent; inherit
master per-weapon display scale. Master applies `target + R*S*(point-[8,8,8])`;
account for native half-block centering once. Rigid cosmetic poses, no finger rig.

## Verification and visual review

Stdlib generator and read-only `--verify` pass: deterministic output bytes,
valid model/UV bounds and texture reference, six faces per cuboid, exact mirrored
geometry/UV corners and conservative rotated-AABB grip clearance. Original
256x256 RGB atlas: 48 face/material tiles with gutters. PNGs use filter 0,
fixed stored DEFLATE and no timestamps. Inspected the textured CPU contact sheet:
front, inner palm/thumb, dorsal/rear, left mirror and muzzle side. Finger gaps,
small wrist silhouette and plate edges read clearly. Cyan grip is preview-only.

## Native checks — master

Ace / Duke / Izanagi / Ammit: pack/model/texture load, inherited display scale,
hip fire and ADS sight clearance, trigger/receiver clipping, combat and reload
phases including left support-hand motion. Briefly inspect 10–20 assemblies for
visible artifacts/stutter. Offline images do not establish native acceptance.
No build, native game or live DCC was used; unsaved DCC work was untouched.

## Exact owned paths

""" + "\n".join(f"- `{p}`" for p in (GENERATOR, ART, PREVIEW, RIGHT, LEFT, TEXTURE, REPORT)) + """

## Reproduce

Cwd: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w201-hands-art`

```sh
rtk proxy python3 scripts/art/build_first_person_gloves_w201.py
rtk proxy python3 scripts/art/build_first_person_gloves_w201.py --verify
```

## Generated SHA-256

""" + hashes + "\n").encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="compare deterministic output in memory; write nothing")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "docs/qa/2026-10-27/w201/batch.json").read_text())
    feature = next(f for f in manifest["features"] if f["name"] == "w201-hands-art")
    assert ROOT in (Path(feature["destination"]), Path('/Users/qf/IdeaProjects/DestinyGuardians')), "Run only in the authorized worktree or integrated source."
    assert set(feature["owned_paths"]) == {GENERATOR, ART, PREVIEW, RIGHT, LEFT, TEXTURE, REPORT}
    right, left = models()
    validate(right, left)
    texture = atlas()
    outputs = {RIGHT: encode_json(right), LEFT: encode_json(left), TEXTURE: png(SIZE, SIZE, texture),
               ART: encode_json(metadata(right, left)), PREVIEW: preview(right, left, texture)}
    outputs[REPORT] = report(outputs)
    mismatches = []
    for path, value in outputs.items():
        target = ROOT / path
        if args.verify:
            if not target.is_file() or target.read_bytes() != value:
                mismatches.append(path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
    if mismatches:
        raise SystemExit("VERIFY FAILED: " + ", ".join(mismatches))
    print(json.dumps({"mode": "verified_read_only" if args.verify else "generated",
                      "elementsPerHand": 26, "pairElements": 52, "facesPerHand": 156,
                      "texture": [SIZE, SIZE], "gripOrigin": ANCHOR, "outputPaths": list(outputs)}, indent=2))


if __name__ == "__main__":
    main()
