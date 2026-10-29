#!/usr/bin/env python3
"""W252: source-informed cuboid props; no source mesh or texture redistribution.

Core generation/check uses Python's standard library. Optional --preview needs Pillow.
The JSON uses the project's 26.3 scalar x/y/z cuboid rotation schema (EulerXYZ).
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "ability_w252/grenade/"
ASSETS = Path("src/main/resources/assets/destiny")
MANIFEST = Path("art/abilities/w252/grenade-manifest.json")
NAMES = ("flashbang", "incendiary", "vortex", "pulse", "fusion", "suppressor", "storm", "solar")
FACES = ("north", "south", "east", "west", "up", "down")
MATS = ("body", "plate", "dark", "band", "energy", "hot", "vent", "mark")
COLORS = {
    "flashbang": ((61, 69, 77), (213, 216, 211), (23, 29, 35), (122, 138, 148), (109, 210, 255), (226, 249, 255)),
    "incendiary": ((76, 69, 55), (152, 147, 124), (30, 30, 26), (116, 97, 68), (255, 130, 34), (255, 227, 157)),
    "suppressor": ((60, 61, 69), (162, 165, 172), (25, 26, 34), (106, 110, 127), (163, 101, 244), (226, 205, 255)),
    "pulse": ((56, 59, 63), (143, 135, 115), (20, 25, 29), (105, 110, 113), (74, 192, 255), (196, 245, 255)),
    "vortex": ((44, 20, 79), (94, 47, 153), (17, 9, 35), (116, 69, 180), (162, 102, 255), (228, 199, 255)),
    "fusion": ((146, 53, 9), (248, 137, 26), (83, 27, 6), (221, 98, 12), (255, 179, 49), (255, 246, 186)),
    "storm": ((24, 65, 96), (87, 155, 189), (10, 27, 46), (62, 123, 157), (102, 213, 255), (216, 253, 255)),
    "solar": ((184, 54, 6), (255, 126, 13), (104, 24, 4), (240, 81, 6), (255, 167, 24), (255, 240, 177)),
}
IDENTITY = {
    "flashbang": "Dark rounded lower shell, pale tapered fuse and offset lever; reviewed Explosion FBX plus Flashbang gameplay screenshot.",
    "incendiary": "Compact explosive casing, recessed hot equator and narrow fuse; Explosion-family adaptation, species-specific shell unverified.",
    "suppressor": "Squat explosive casing with broad recessed void belt and low fuse; Explosion-family adaptation, species-specific shell unverified.",
    "pulse": "Tall capsule, central drum, paired polar caps and external electrodes; reviewed original Pulse FBX, not a recolored orb.",
    "vortex": "Dark hollow core with separated tilted violet arcs; gameplay vortex-energy interpretation, projectile topology unverified.",
    "fusion": "Tiny bright seed with asymmetric six-point star corona; gameplay flying spark reference, not a metal grenade.",
    "storm": "Broken arc nucleus with separated forked lightning branches; gameplay arc-energy interpretation, projectile topology unverified.",
    "solar": "Full warm luminous sphere, ragged radial flame tongues and open flare arcs; gameplay solar-energy interpretation.",
}
REFS = {
    "flashbang": ("0/0a/Flashbang", "5936c0c11c9e4280c98e0305411df4d2fdff6af93d5e67e5b22b3235a731cd68"),
    "incendiary": ("1/1f/Incendiary", "bd3756a95a951815568ca95511dc9609d9230d711109641ff539a4e8eb0bf874"),
    "vortex": ("f/ff/Vortex", "430aa560f64cae85a927ae4d50f905743f62dacbba879549d89959b50841bec9"),
    "pulse": ("f/f6/Pulse", "ce568b425f9de1d148903a835840d5d00aa9f64577a782ae7fea902f2a590024"),
    "fusion": ("6/6b/Fusion", "91361fc8e4c77f2fac51614c1e0b115c050e69c8edf503ff8f7ed7db0d6d6ffd"),
    "suppressor": ("6/6a/Suppressor", "87989dab7005a9bf7b9fb64fddc46388f0e93828a8e5f02f317978ac01be9e80"),
    "storm": ("8/81/Storm", "e02d1b24410886daa2cf3cca718f43ff5e34a5442a79395b40603d7a21ce3131"),
    "solar": ("1/14/Solar", "76709d83b626f03e9908ccc4dd086a5bce5090048e5af548d16083590c752771"),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode()


def rotate(point, angles):
    # Native EulerXYZ = Rx * Ry * Rz: local Z applied first.
    x, y, z = point
    a, b, c = map(math.radians, angles)
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return (x, y, z)


def corners(e):
    points = list(itertools.product(*zip(e["from"], e["to"])))
    r = e.get("rotation")
    if r:
        o = r["origin"]
        points = [tuple(o[a] + v for a, v in enumerate(rotate([p[a] - o[a] for a in range(3)], [r[k] for k in "xyz"]))) for p in points]
    return points


class Form:
    def __init__(self):
        self.parts = []

    def box(self, name, center, size, mat, angles=(0, 0, 0), origin=None):
        # Store material metadata only in memory, not invented fields in item JSON.
        o = origin or center
        e = {"name": name, "from": [center[a] - size[a] / 2 for a in range(3)],
             "to": [center[a] + size[a] / 2 for a in range(3)]}
        if any(angles):
            e["rotation"] = dict(origin=list(o), **dict(zip("xyz", angles)), rescale=False)
        self.parts.append((e, mat))

    def shell(self, name, low, high, r0, r1, mat, sides=12, cap=False):
        """Faceted tapered shell, with meaningful broad panels instead of a voxel skin."""
        r = (r0 + r1) / 2
        y = (low + high) / 2
        length = math.hypot(high - low, r1 - r0)
        slope = math.degrees(math.atan2(r0 - r1, high - low))
        width = 2 * max(r0, r1) * math.tan(math.pi / sides) + .018
        for i in range(sides):
            a = i * 360 / sides
            theta = math.radians(a)
            self.box(f"{name}_panel_{i}", (r * math.cos(theta), y, -r * math.sin(theta)),
                     (.13, length + .03, width), mat, (0, a, slope))
        if cap:
            # Four broad slabs fill a faceted disk, within the shell's outer radius.
            for label, cy, cr in (("bottom", low, r0), ("top", high, r1)):
                for a in (0, 45, 90, 135):
                    self.box(f"{name}_{label}_cap_{a}", (0, cy, 0), (cr * 1.84, .12, cr * .76), mat, (0, a, 0))

    def ring(self, name, radius, thickness, mat, tilt=(0, 0, 0), start=0, count=12, center=(0, 0, 0)):
        """A real open ring, with gaps when count < 12; no opaque sphere-shaped box."""
        for i in range(count):
            a = math.radians(start + i * 30)
            p = rotate((radius * math.cos(a), radius * math.sin(a), 0), tilt)
            # Ring in XY; tilt uses X only in our callers, so Rx * Rz remains exact.
            self.box(f"{name}_{i}", tuple(p[j] + center[j] for j in range(3)),
                     (thickness, radius * .55, thickness), mat, (tilt[0], 0, math.degrees(a)), origin=tuple(p[j] + center[j] for j in range(3)))

    def orb(self, name, radius, mat):
        # Three tapered belts keep a rounded volume and avoid the six-face cube silhouette.
        self.shell(name + "_south", -radius * .86, -radius * .35, radius * .48, radius * .91, mat, 10, True)
        self.shell(name + "_equator", -radius * .35, radius * .35, radius * .91, radius * .91, mat, 10, False)
        self.shell(name + "_north", radius * .35, radius * .86, radius * .91, radius * .48, mat, 10, True)


def geometry(name):
    f = Form()
    if name in ("flashbang", "incendiary", "suppressor"):
        # Source Explosion f3eab080_0: rounded lower, equator, shoulder, fuse, offset lever.
        squat = name == "suppressor"
        r = 2.4 if squat else 2.05
        f.shell("lower_bevel", -2.8, -2.25, r * .36, r * .8, "body", cap=True)
        f.shell("lower_curve", -2.25, -1.4, r * .8, r, "body")
        f.shell("main_shell", -1.4, -.25, r, r, "body")
        f.shell("equator", -.25, .1 if name == "flashbang" else .45, r + .08, r + .08,
                "band" if name == "flashbang" else "energy")
        f.shell("shoulder", .2 if name == "flashbang" else .5, 1.1, r, 1.28, "plate")
        f.shell("fuse", 1.1, 3 if name == "flashbang" else 2.25 if squat else 2.7,
                .95, .38, "plate", 8, True)
        f.box("lever_hinge", (-.9, 2, -.1), (.55, .65, .7), "dark")
        f.box("lever_upper", (-1.35, 1.1, -.1), (.35, 2.4, .7), "band", (0, 0, -19))
        f.box("lever_lower", (-1.9, -.9, -.1), (.32, 2, .7), "dark", (0, 0, -7))
        if name == "incendiary":
            # Recessed seams are UV; just the protruding fuse band gets volume.
            f.box("fuse_heat_slot", (0, 1.1, -.92), (.8, .22, .13), "hot")
        elif squat:
            f.box("recessed_void_aperture", (0, .65, -1.9), (1.1, .4, .14), "dark")
    elif name == "pulse":
        f.shell("lower_pole", -3.2, -2.6, .65, 1.3, "plate", 10, True)
        f.shell("lower_capsule", -2.6, -.55, 1.3, 1.3, "body", 10)
        f.shell("central_drum", -.55, .55, 1.62, 1.62, "band", 12)
        f.shell("upper_capsule", .55, 2.6, 1.3, 1.3, "body", 10)
        f.shell("upper_dome", 2.6, 3.2, 1.3, .65, "plate", 10, True)
        for i, a in enumerate((0, 90, 180, 270)):
            t = math.radians(a)
            p = (1.68 * math.cos(t), 0, -1.68 * math.sin(t))
            f.box(f"equator_contact_{i}", p, (.3, 1.5, .5), "plate", (0, a, 0))
            for s in (-1, 1):
                c = (1.68 * math.cos(t), s * 2.0, -1.68 * math.sin(t))
                f.box(f"polar_electrode_{i}_{s}", c, (.14, 1.65, .28), "energy", (0, a, 0))
    elif name == "vortex":
        f.orb("void_nucleus", 1.25, "dark")
        f.ring("outer_vortex", 3.1, .22, "energy", (57, 0, 0), 0, 10)
        f.ring("inner_vortex", 2.35, .28, "plate", (-38, 0, 0), 40, 8)
        f.box("white_void_seed", (0, 0, -.2), (.7, .7, .7), "hot", (12, 23, 27))
    elif name == "fusion":
        f.orb("fusion_seed", .95, "hot")
        # Flying Fusion in the gameplay image is a small hot knot, with a sharp star corona.
        for i, (a, length) in enumerate(((12, 2.3), (71, 1.65), (128, 2), (195, 2.6), (247, 1.5), (306, 2.15))):
            t = math.radians(a)
            f.box(f"fusion_ray_{i}", ((.9 + length / 2) * math.cos(t), (.9 + length / 2) * math.sin(t), (i % 2 - .5) * .35),
                  (length, .16 if i % 2 else .22, .15), "energy", (0, 0, a))
        f.ring("fusion_corona", 1.4, .15, "band", (33, 0, 0), 10, 7)
    elif name == "storm":
        f.orb("arc_nucleus", 1.05, "hot")
        f.box("arc_envelope_a", (-.15, -.1, 0), (2.35, .22, .24), "energy", (-16, 13, -25))
        for i, (a, length) in enumerate(((18, 2.35), (83, 2.6), (149, 1.8), (217, 2.1), (282, 1.8))):
            t = math.radians(a)
            p = ((1 + length / 2) * math.cos(t), (1 + length / 2) * math.sin(t), .25 * (i % 2))
            f.box(f"lightning_stem_{i}", p, (length, .2, .22), "energy", (0, 0, a))
            p = ((1 + length) * math.cos(t), (1 + length) * math.sin(t), .25 * (i % 2))
            f.box(f"lightning_fork_{i}", p, (.9, .13, .16), "hot", (0, 0, a + 48))
    elif name == "solar":
        f.orb("solar_photosphere", 2.1, "energy")
        f.ring("solar_flare", 2.65, .19, "hot", (-24, 0, 0), 15, 9)
        for i, (a, length) in enumerate(((8, 1.2), (60, .9), (112, 1.35), (172, .8), (230, 1.45), (292, 1.05))):
            t = math.radians(a)
            c = ((2 + length / 2) * math.cos(t), (2 + length / 2) * math.sin(t), .18 if i % 2 else -.3)
            f.box(f"flame_tongue_{i}", c, (length, .3, .26), "plate", (0, 0, a + 12))
    points = [p for e, _ in f.parts for p in corners(e)]
    low = [min(p[a] for p in points) for a in range(3)]
    high = [max(p[a] for p in points) for a in range(3)]
    center = [(low[a] + high[a]) / 2 for a in range(3)]
    factor = 8 / max(high[a] - low[a] for a in range(3))
    for e, _ in f.parts:
        for k in ("from", "to"):
            e[k] = [round(8 + (e[k][a] - center[a]) * factor, 6) for a in range(3)]
        if "rotation" in e:
            e["rotation"]["origin"] = [round(8 + (e["rotation"]["origin"][a] - center[a]) * factor, 6) for a in range(3)]
    return f.parts


def texture(name, enemy):
    palette = list(COLORS[name])
    if enemy:
        # Separate hostile warning palette; keep dark/metal material identities legible.
        palette[4:6] = [(255, 76, 73), (255, 221, 190)]
        if name == "flashbang":
            palette[3] = (235, 79, 71)  # Existing equator band carries the warning, no red fuse speckle.
    palette += [palette[2], palette[1]]
    pixels = bytearray(128 * 64 * 4)
    for j, base in enumerate(palette):
        ox, oy = (j % 4) * 32, (j // 4) * 32
        for y in range(32):
            for x in range(32):
                shade = 1.0
                if j in (0, 1, 3, 6, 7):
                    shade = 1.05 - y * .004
                    if j != 1 and (x in (2, 29) or y in (2, 29)):
                        shade *= .84
                    if j == 0 and ((x - 16) ** 2 + (y - 16) ** 2 < 13):
                        shade = .67  # Source's shell fasteners live in UV, not extra bolt cubes.
                    if j == 1 and y in (5, 26):
                        shade *= .97  # Fuse metal stays broad and quiet at this small scale.
                    if j == 6 and y % 7 in (2, 3):
                        shade = .4
                else:
                    # Large curved energy strands with quiet midtones, no random speckle noise.
                    curve = 15 + 7 * math.sin(y * .18 + (NAMES.index(name) + 1) * .4)
                    shade = 1.12 if abs(x - curve) < 1.6 else .74 + .14 * math.sin((x + y) * .13)
                    if j == 5:
                        shade = .9 + .1 * math.cos((x - 16) * .12)
                rgb = [max(0, min(255, round(c * shade))) for c in base]
                if enemy and j == 7 and 24 <= y <= 27 and 6 <= x <= 25:
                    rgb = list(palette[4])  # UV warning band, not a silhouette-changing add-on.
                i = ((oy + y) * 128 + ox + x) * 4
                pixels[i:i + 4] = bytes(rgb + [255])
    return pixels


def png(pixels):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    raw = b"".join(b"\0" + pixels[y * 512:(y + 1) * 512] for y in range(64))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 128, 64, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def item_model(parts, name):
    elements = []
    for src, mat in parts:
        e = json.loads(json.dumps(src))
        e["faces"] = {}
        for face in FACES:
            index = MATS.index(mat)
            if face == "down" and mat in ("body", "plate"):
                index = MATS.index("dark")
            # Pixels converted to item UV's 0..16 coordinate space, with 1px bleed margin.
            x, y = (index % 4) * 32, (index // 4) * 32
            e["faces"][face] = {"uv": [(x + 1) / 8, (y + 1) / 4, (x + 31) / 8, (y + 31) / 4], "texture": "#0"}
        elements.append(e)
    # NONE context is exactly the native centered model; callers own all hand/projectile scaling.
    return {"ambientocclusion": False, "textures": {"0": "destiny:item/" + PREFIX + name,
             "particle": "destiny:item/" + PREFIX + name}, "elements": elements,
            "display": {"gui": {"rotation": [18, -32, 0], "scale": [1.55, 1.55, 1.55]}}}


def build():
    files = {}
    rows = []
    forms = {}
    for name in NAMES:
        parts = geometry(name)
        forms[name] = parts
        points = [p for e, _ in parts for p in corners(e)]
        lo = [min(p[a] for p in points) for a in range(3)]
        hi = [max(p[a] for p in points) for a in range(3)]
        assert 1 < len(parts) <= 100, (name, len(parts))
        assert max(hi[a] - lo[a] for a in range(3)) <= 8.00001
        assert all(abs((hi[a] + lo[a]) / 2 - 8) < .00001 for a in range(3))
        for enemy in (False, True):
            key = name + ("_enemy" if enemy else "")
            model = item_model(parts, key)
            for e in model["elements"]:
                assert all(e["to"][a] > e["from"][a] for a in range(3))
                assert set(e["faces"]) == set(FACES)
                for face in e["faces"].values():
                    assert all(0 <= v <= 16 for v in face["uv"])
                assert all(math.isfinite(v) for p in corners(e) for v in p)
            files[ASSETS / "models/item" / (PREFIX + key + ".json")] = encoded(model)
            files[ASSETS / "items" / (PREFIX + key + ".json")] = encoded({"model": {"type": "minecraft:model", "model": "destiny:item/" + PREFIX + key}})
            files[ASSETS / "textures/item" / (PREFIX + key + ".png")] = png(texture(name, enemy))
        shape = [{k: v for k, v in e.items() if k in ("from", "to", "rotation")} for e, _ in parts]
        rows.append({"name": name, "elements": len(parts), "geometry_sha256": digest(encoded(shape)),
                     "identity": IDENTITY[name], "bounds_units": [[round(v, 5) for v in lo], [round(v, 5) for v in hi]],
                     "dimensions_blocks_none_scale1": [round((hi[a] - lo[a]) / 16, 5) for a in range(3)],
                     "source_status": "reviewed_original_mesh_reconstruction" if name in ("flashbang", "pulse") else "provisional_family_adaptation" if name in ("incendiary", "suppressor") else "gameplay_energy_interpretation_not_verified_projectile_mesh"})
    assert len({r["geometry_sha256"] for r in rows}) == 8, "Species must not be geometry recolors"
    manifest = {"revision": "W252", "generator": "scripts/art/build_grenades_w252.py", "format": "Minecraft 26.3 cuboids, scalar x/y/z EulerXYZ",
        "provenance": {"method": "New cuboid geometry and hand-designed material atlas after source review; no FBX triangles or ripped PNG pixels copied into product.",
        "drive_archive": {"url": "https://drive.google.com/file/d/1yEfOLn_FJGT2tY5Q5oRNtA0OCnjkt2fQ/view", "name": "Misc/Four Grenade Types.7z", "bytes": 2370535,
        "sha256": "b3183e471b5ce992a463e4b779a2ce9f0530aab538f770fd21c908ea772bb75f",
        "reviewed_meshes": [
            {"path": "Explosion Grenade/Explosion Grenade.fbx", "sha256": "d4833b00b30efea11d0a8e9fccdea75d7d2874a66c1d394a32b79136c6c7a9cc", "vertices": 570, "polygon_indices": 2538, "tag_in_mesh_name": "f3eab080", "ability_mapping": "Flashbang screenshot shape correspondence; archive calls it Explosion, not Flashbang/Incendiary/Suppressor"},
            {"path": "Pulse Grenade/Pulse Grenade.fbx", "sha256": "1ed683efe866ec5e4611390fd3872e1b1663e4e7cdef71558dfd1179c4f08df0", "vertices": [614, 198], "polygon_indices": [2610, 486], "tag_in_mesh_name": "20f2b080", "ability_mapping": "Pulse Grenade named in archive"}],
        "also_present_not_used": ["Grenades.blend", "Magnetic Grenade", "Spike Grenade"],
        "review": "Binary FBX vertices/polygon indices parsed in memory, untextured front/oblique/side software projections and original Diffuse PNG visually inspected. Projections normalize each Geometry independently and do not evaluate FBX scene transforms/materials. Blender scene not evaluated for grenade props.",
        "source_credit": "Destiny design Bungie; community archive ripper, game build and asset-extraction date unspecified. Downloaded 2026-10-29."},
        "ssd": {"path": "/Volumes/qf-ssd/Destiny-Light-Abilities-2026-10-28", "read_only": True, "review": "Inventory has animation FBX/Blends, no separately named grenade prop mesh identified; not a prop-mesh source."},
        "reference_images": [{"name": n, "page": "https://www.destinypedia.com/" + n.title() + "_Grenade", "local": "/private/tmp/destiny-w252/assets/" + n + ".jpg",
            "url": "https://destiny.wiki.gallery/images/thumb/" + REFS[n][0] + "_Grenade.jpg/350px-" + n.title() + "_Grenade.jpg", "sha256": REFS[n][1],
            "role": "Visible mechanical shell in flight" if n == "flashbang" else "In-flight bright spark" if n == "fusion" else "Detonation/energy reference only, not projectile-shell topology proof"} for n in NAMES]},
        "coordinates": {"center_units": [8, 8, 8], "units_per_block": 16, "max_extent_units": 8, "max_extent_blocks_none_scale1": .5,
            "fp_scale_suggested": [.5, .6], "fp_max_extent_blocks": [.25, .3], "hand_grip": "Center; tall mechanical props point +Y. No embedded NONE/hand scale or hand translation.",
            "gui_only": "18/-32/0 degrees, scale 1.55; does not affect NONE ItemDisplays"},
        "enemy": "Identical per-species geometry/UV, separate warm warning atlas selected by existing AbilityVisualVariants.item; no new team resolver.",
        "models": rows,
        "checks": {"species_unique_geometry": True, "finite_coordinates": True, "centered_aabb": True, "explicit_face_uv": True, "max_elements": 100, "generated_files_excluding_manifest": len(files)},
        "unverified": ["Native resource-pack load / shader / transparency rendering", "Actual first/third-person hand fit and 6-tick release", "Projectile shells for the six species without individually mapped source FBX", "Particle animation, additive bloom, native emissive behavior, 10-20 simultaneous props", "Java compilation (master only)"],
        "outputs": {str(p): digest(b) for p, b in sorted(files.items())}}
    files[MANIFEST] = encoded(manifest)
    return files, forms, manifest


def preview(path, files):
    """Optional software view of actual emitted JSON geometry/UV. No live application access."""
    from PIL import Image, ImageDraw
    import io
    canvas = Image.new("RGB", (1440, 1100), (18, 23, 31))
    draw = ImageDraw.Draw(canvas)
    # Render orthographic, textured, with Z-buffer and opaque materials, from exported data.
    face_indices = {"north": (0, 4, 6, 2), "south": (5, 1, 3, 7), "west": (1, 0, 2, 3),
                    "east": (4, 5, 7, 6), "down": (1, 5, 4, 0), "up": (2, 6, 7, 3)}
    for row in range(4):
        for col in range(4):
            enemy = row >= 2
            name = NAMES[(row % 2) * 4 + col]
            key = name + ("_enemy" if enemy else "")
            ox, oy = col * 360, row * 275
            draw.rounded_rectangle((ox + 5, oy + 5, ox + 354, oy + 269), radius=8, fill=(27, 34, 44))
            draw.text((ox + 14, oy + 12), key, fill=(244, 231, 212))
            model = json.loads(files[ASSETS / "models/item" / (PREFIX + key + ".json")])
            atlas = Image.open(io.BytesIO(files[ASSETS / "textures/item" / (PREFIX + key + ".png")])).convert("RGB")
            for view, yaw in enumerate((-28, 90)):
                w, h = 168, 226
                tile = Image.new("RGB", (w, h), (27, 34, 44))
                depth = [-1e9] * (w * h)
                pix = tile.load()
                for e in model["elements"]:
                    pts = [rotate([v - 8 for v in p], (13, yaw, 0)) for p in corners(e)]
                    for face, ids in face_indices.items():
                        v = [pts[k] for k in ids]
                        ab = [v[1][i] - v[0][i] for i in range(3)]
                        ac = [v[2][i] - v[0][i] for i in range(3)]
                        normal = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
                        norm = math.sqrt(sum(a * a for a in normal)) or 1
                        light = .63 + .37 * abs(sum(a * b for a, b in zip(normal, (-.3, .6, .74))) / norm)
                        uv = e["faces"][face]["uv"]
                        tex = ((uv[0] * 8, uv[1] * 4), (uv[2] * 8, uv[1] * 4), (uv[2] * 8, uv[3] * 4), (uv[0] * 8, uv[3] * 4))
                        v = [(p[0] * 20 + w / 2, h / 2 - p[1] * 20, p[2]) for p in v]
                        for tri in ((0, 1, 2), (0, 2, 3)):
                            a, b, c = [v[i] for i in tri]
                            ta, tb, tc = [tex[i] for i in tri]
                            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                            if abs(den) < 1e-8:
                                continue
                            for y in range(max(0, int(min(a[1], b[1], c[1]))), min(h, int(max(a[1], b[1], c[1])) + 1)):
                                for x in range(max(0, int(min(a[0], b[0], c[0]))), min(w, int(max(a[0], b[0], c[0])) + 1)):
                                    u = ((b[1] - c[1]) * (x + .5 - c[0]) + (c[0] - b[0]) * (y + .5 - c[1])) / den
                                    t = ((c[1] - a[1]) * (x + .5 - c[0]) + (a[0] - c[0]) * (y + .5 - c[1])) / den
                                    q = 1 - u - t
                                    if min(u, t, q) < 0:
                                        continue
                                    z = u * a[2] + t * b[2] + q * c[2]
                                    index = y * w + x
                                    if z <= depth[index]:
                                        continue
                                    tx = min(127, max(0, int(u * ta[0] + t * tb[0] + q * tc[0])))
                                    ty = min(63, max(0, int(u * ta[1] + t * tb[1] + q * tc[1])))
                                    pix[x, y] = tuple(round(k * light) for k in atlas.getpixel((tx, ty)))
                                    depth[index] = z
                canvas.paste(tile, (ox + 10 + view * 174, oy + 35))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Compare generated bytes to existing assets, no product writes")
    ap.add_argument("--preview", type=Path, help="Write offline contact sheet, e.g. /private/tmp/destiny-w252/assets/grenade-preview.png")
    args = ap.parse_args()
    files, forms, manifest = build()
    errors = []
    for rel, data in files.items():
        path = ROOT / rel
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                errors.append(str(rel))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if errors:
        raise SystemExit("Generated output drift: " + ", ".join(errors))
    if args.preview:
        preview(args.preview, files)
    print(json.dumps({"check": args.check, "files": len(files), "center": [8, 8, 8], "max_extent_blocks": .5,
                      "elements": {name: len(parts) for name, parts in forms.items()}, "preview": str(args.preview) if args.preview else None}))


if __name__ == "__main__":
    main()
