#!/usr/bin/env python3
"""W253 delivered .blend geometry/UV/material -> W255 native grenade props.

Use Python with numpy/Pillow. --check verifies byte-identical owned assets.
--refresh-blender evaluates source files in a separate --disable-autoexec process;
all raw geometry and previews stay outside the checkout. Never saves a .blend.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/Volumes/qf-ssd/Destiny-Grenade-Models-W253-2026-10-30")
CACHE = Path("/private/tmp/destiny-w255/grenade-worker")
ASSETS = Path("src/main/resources/assets/destiny")
MANIFEST = Path("art/abilities/w255/grenade-manifest.json")
PREFIX = "ability_w255/grenade/"
GEOMETRIES = ("80C308CB_80C30922", "80C3339B_80C3339C", "80C3659F_80C365A4", "80C38A9A_80C38A9B")
PALETTES = {"fusion": (0xFF7A1A, 0xFFD38A), "solar": (0xFF7A1A, 0xFFD38A),
            "vortex": (0xA86BFF, 0xE2C8FF), "storm": (0x5FC8FF, 0xC8F4FF)}
ATLAS = 512
TILE = 16


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def helpers():
    path = ROOT / "scripts/art/build_ripped_grenades_w252.py"
    ns = {"__file__": str(path), "__name__": "w252_helpers"}
    exec(compile(path.read_text(), str(path), "exec"), ns)
    return ns


def blender_stage(source, cache):
    import bpy
    result = {"blender": bpy.app.version_string, "models": {}}
    for geometry in GEOMETRIES:
        path = source / "geometry" / geometry / "source-preview.blend"
        bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False, use_scripts=False)
        meshes = sorted((o for o in bpy.context.scene.objects if o.type == "MESH"),
                        key=lambda o: o.get("source_part_index", -1))

        def snapshot(obj, mesh):
            mesh.calc_loop_triangles()
            uv = mesh.uv_layers.get("uv0")
            assert uv is not None
            triangles = []
            for triangle in mesh.loop_triangles:
                points = []
                for index in triangle.vertices:
                    p = obj.matrix_world @ mesh.vertices[index].co
                    points.append([float(p.x), float(p.z), float(-p.y)])
                triangles.append({"p": points, "uv": [list(uv.data[i].uv) for i in triangle.loops]})
            return triangles

        audits = []
        for obj in meshes:
            triangles = snapshot(obj, obj.data)
            signature = sorted(tuple(sorted(tuple(round(x, 8) for x in p) for p in t["p"])) for t in triangles)
            audits.append({"object": obj.name, "part": obj["source_part_index"],
                           "stage": obj["source_render_stage"], "triangles": len(triangles),
                           "geometry_sha256": sha(encode(signature)), "material": obj.material_slots[0].material.name})
        selected = [o for o in meshes if o["source_render_stage"] in ("Transparents", "GenerateGbuffer")]
        original = [t for obj in selected for t in snapshot(obj, obj.data)]
        bpy.ops.object.select_all(action="DESELECT")
        for obj in selected:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = selected[0]
        if len(selected) > 1:
            bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        points = [p for t in original for p in t["p"]]
        lo = [min(p[i] for p in points) for i in range(3)]
        hi = [max(p[i] for p in points) for i in range(3)]
        center = [(a + b) / 2 for a, b in zip(lo, hi)]
        scale = 8 / max(b - a for a, b in zip(lo, hi))
        # Never join shadow, depth, compute-skinning or light-shaft shells.
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=1e-7)
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.data.calc_loop_triangles()
        welded = len(obj.data.loop_triangles)
        reduced = snapshot(obj, obj.data)
        ratio = 1.0
        if len(reduced) > 470:
            modifier = obj.modifiers.new("W255_owned_reduction", "DECIMATE")
            modifier.decimate_type = "COLLAPSE"
            modifier.use_collapse_triangulate = True
            ratio = 460 / welded
            for attempt in range(12):
                modifier.ratio = ratio
                bpy.context.view_layer.update()
                graph = bpy.context.evaluated_depsgraph_get()
                evaluated = obj.evaluated_get(graph)
                mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=graph)
                reduced = snapshot(obj, mesh)
                evaluated.to_mesh_clear()
                if len(reduced) <= 470:
                    break
                ratio *= .95
        assert 1 < len(reduced) <= 470
        for triangle in original + reduced:
            triangle["p"] = [[8 + (v - center[i]) * scale for i, v in enumerate(p)] for p in triangle["p"]]
        result["models"][geometry] = {"source_blend_sha256": sha(path.read_bytes()), "parts": audits,
            "selected_parts": [0, 2] if geometry == GEOMETRIES[0] else [0], "source_objects": audits,
            "original_triangles": len(original), "reduced_triangles": len(reduced), "ratio": ratio,
            "source_bounds": [lo, hi], "normalization": {"source_center": center, "scale": scale,
                "target_center": [8, 8, 8], "max_extent": 8}, "original": original, "reduced": reduced}
        print(geometry, len(original), "->", len(reduced), flush=True)
    cache.mkdir(parents=True, exist_ok=True)
    (cache / "evaluated.json").write_bytes(encode(result))


def rgb(integer):
    return [(integer >> shift) & 255 for shift in (16, 8, 0)]


def paint(ability, geometry, uv, diffuse, sample):
    import numpy as np
    color, glow = (np.asarray(rgb(v), dtype=float) for v in PALETTES[ability])
    if geometry in GEOMETRIES[:2]:
        # Authored continuous energy, not the source inspection UV checker.
        # Periodic sine warps keep the UV seam continuous without extra geometry.
        tau = 2 * np.pi
        u, v = uv[..., 0], uv[..., 1]
        warp = .18 * np.sin(tau * v * 2) + .08 * np.cos(tau * (u + v))
        noise = (np.sin(tau * (u * 2 + warp))
                 + .45 * np.sin(tau * (u * 5 + v * 3 + warp))
                 + .2 * np.cos(tau * (u * 11 - v * 7))) / 1.65
        broad = np.clip(.5 + noise * .5, 0, 1)
        broad = broad * broad * (3 - 2 * broad)
        ripple = np.exp(-8 * np.sin(tau * (u * 3 + v * 2 + warp)) ** 2)
        intensity = np.clip(.12 + broad * .68 + ripple * .2, 0, 1)[..., None]
        # R1 native capture: .65 Solar base plus item directional lighting read brown.
        # Raise the radiance floor without per-camera compensation or extra shells.
        low = np.array([150, 100, 225] if ability == "vortex" else [255, 186, 78], dtype=float)
        glow = np.array([235, 210, 255] if ability == "vortex" else [255, 250, 215], dtype=float)
        pixels = np.empty((*uv.shape[:-1], 4), dtype="uint8")
        pixels[..., :3] = low + intensity * (glow - low)
        pixels[..., 3] = 255
        return pixels, 15
    pixels = sample(diffuse, uv)
    # Source t0 RGB is actual diffuse, not a guessed grey material. Its tiny hot-red
    # patch is recolored as a PRODUCT energy accent; shader emission was not decoded.
    values = pixels[..., :3].astype(float)
    accent = (values[..., 0] > 220) & (values[..., 1] < 80) & (values[..., 2] < 60)
    luminance = values[..., 0] * .2126 + values[..., 1] * .7152 + values[..., 2] * .0722
    # Preserve diffuse luminance/detail, with an explicit product element tint.
    values = values * .35 + luminance[..., None] * (color / 255) * .65
    values[accent] = glow
    pixels[..., :3] = values.astype("uint8")
    pixels[..., 3] = 255  # t0 alpha is packed data, not opacity.
    return pixels, 15 if accent.mean() > .7 else (6 if accent.any() else 0)


def source_inputs(source):
    paths = ["PROVENANCE.json", "MATERIAL_MAPPING.md", "material-details.json"]
    for ability in PALETTES:
        paths.append(f"abilities/{ability}/manifest.json")
    for geometry in GEOMETRIES:
        paths.extend(f"geometry/{geometry}/{name}" for name in ("source-preview.blend", "mesh-data.json"))
    for material in ("80C308C5", "80C308CA", "80C33394", "80C3659E", "80C38A97"):
        paths.append(f"Materials/{material}.json")
    for shader in ("80C3D35F", "80C37280", "80C3A1A2", "80C3A904"):
        paths.append(f"Shaders/HLSL/PS_{shader}.hlsl")
    paths.extend(("TexturesPNG/80C3C18E.png", "TexturesPNG/80C3C190.png"))
    return {path: sha((source / path).read_bytes()) for path in paths}


def generate(stage, source):
    import numpy as np
    from PIL import Image
    helper = helpers()
    adapter = helper["adapter"]()
    diffuse = np.asarray(Image.open(source / "TexturesPNG/80C3C18E.png").convert("RGBA"), dtype=float)
    diffuse[..., 3] = 255
    files, baked, records, bindings = {}, {}, {}, {}
    inputs = source_inputs(source)
    yy, xx = np.mgrid[0:TILE, 0:TILE]
    u, v = (xx - .5) / (TILE - 2), (yy - .5) / (TILE - 2)
    mask = (u <= v + 1 / (2 * (TILE - 2))) & (u >= -1 / (TILE - 2)) & (v <= 1 + 1 / (TILE - 2))
    for ability in PALETTES:
        delivered = json.loads((source / f"abilities/{ability}/manifest.json").read_text())
        bindings[ability] = {"product_ids": delivered["productIds"], "source_pattern": delivered["sourcePattern"],
                             "source_paths": delivered["sourcePaths"], "confidence": delivered["identityConfidence"]}
        for phase in ("held", "projectile"):
            candidate = next(t for t in delivered["stages"] if t["stage"] == phase)
            geometry = candidate["geometry"]
            info = stage["models"][geometry]
            assert info["source_blend_sha256"] == inputs[f"geometry/{geometry}/source-preview.blend"], "Stale source cache"
            atlas = np.zeros((ATLAS, ATLAS, 4), dtype="uint8")
            elements, provenance = [], []
            error = 0.0
            for face, triangle in enumerate(info["reduced"]):
                for fragment in adapter["split_triangle"](triangle["p"]):
                    index = len(elements)
                    assert index < 1000
                    x, y = index % (ATLAS // TILE) * TILE, index // (ATLAS // TILE) * TILE
                    uv = [(x + 1) * 16 / ATLAS, (y + 1) * 16 / ATLAS,
                          (x + TILE - 1) * 16 / ATLAS, (y + TILE - 1) * 16 / ATLAS]
                    element = adapter["to_element"](fragment, f"source_face_{face}_fragment_{index}", uv)
                    t0, t1, t2 = [helper["bary_uv"](p, triangle) for p in fragment["vertices"]]
                    coords = t0 + u[..., None] * (t1 - t0) + (1 - v[..., None]) * (t2 - t0)
                    pixels, emission = paint(ability, geometry, coords, diffuse, helper["sample"])
                    pixels[..., 3] = np.where(mask, pixels[..., 3], 0)
                    atlas[y:y + TILE, x:x + TILE] = pixels
                    element.update(shade=emission == 0, light_emission=emission)
                    elements.append(element)
                    rotation, lo, hi = element["rotation"], element["from"], element["to"]
                    pivot = rotation["origin"]
                    for p, expected in zip((lo, (hi[0], lo[1], lo[2]), (lo[0], hi[1], lo[2])), fragment["vertices"]):
                        actual = adapter["add"](pivot, adapter["rotate"](adapter["sub"](p, pivot), [rotation[a] for a in "xyz"]))
                        error = max(error, max(abs(a - b) for a, b in zip(actual, expected)))
                    provenance.append({"face": face, "source_uv": triangle["uv"],
                                       "fragment_uv": [t0.tolist(), t1.tolist(), t2.tolist()]})
            assert 0 < len(elements) <= 1000 and error < 1e-7
            key = ability + "_" + phase
            for enemy in (False, True):
                name = key + ("_enemy" if enemy else "")
                pixels = atlas.copy()
                if enemy:
                    # Red presentation variant: identical coverage, UV, geometry and lighting.
                    values = pixels[..., :3].astype(float)
                    luminance = values[..., 0] * .2126 + values[..., 1] * .7152 + values[..., 2] * .0722
                    if geometry in GEOMETRIES[:2]:
                        # Raised ally radiance must not clip the enemy atlas to flat red.
                        level = np.clip((luminance - (110 if ability == "vortex" else 180))
                                        / (110 if ability == "vortex" else 75), 0, 1)
                        pixels[..., :3] = np.stack((160 + level * 95, 15 + level * 55,
                                                   10 + level * 35), axis=-1).astype("uint8")
                    else:
                        pixels[..., :3] = np.stack((np.minimum(255, luminance * 1.2 + 45),
                                                   luminance * .22, luminance * .16), axis=-1).astype("uint8")
                output = io.BytesIO()
                Image.fromarray(pixels).save(output, format="PNG", optimize=False)
                model = {"ambientocclusion": False,
                    "textures": {"0": "destiny:item/" + PREFIX + name, "particle": "destiny:item/" + PREFIX + name},
                    "elements": elements, "display": {"gui": {"rotation": [15, -30, 0], "scale": [1.55] * 3}}}
                if geometry in GEOMETRIES[:2]:
                    # This selects flat/front GUI light directions; it is not an unlit shader.
                    model["gui_light"] = "front"
                files[ASSETS / "models/item" / (PREFIX + name + ".json")] = encode(model)
                files[ASSETS / "items" / (PREFIX + name + ".json")] = encode({"model": {
                    "type": "minecraft:model", "model": "destiny:item/" + PREFIX + name}})
                files[ASSETS / "textures/item" / (PREFIX + name + ".png")] = output.getvalue()
                baked[name] = (model, pixels)
            records[key] = {"candidate": candidate, "geometry": geometry, "selected_parts": info["selected_parts"],
                "passes": info["parts"], "source_blend_sha256": info["source_blend_sha256"],
                "source_triangles": info["original_triangles"], "triangles": info["reduced_triangles"],
                "decimate_ratio": info["ratio"], "elements": len(elements), "normalization": info["normalization"],
                "atlas_size": [ATLAS, ATLAS], "fragment_size": TILE, "geometry_mapping_max_error_units": error,
                "geometry_uv_sha256": sha(encode(info["reduced"])), "fragment_uv_sha256": sha(encode(provenance)),
                "material_policy": "source UV + authored smooth energy ripples in project element palette" if geometry in GEOMETRIES[:2]
                    else "actual t0 diffuse with product element tint + hot-red energy accent"}
    manifest = {"revision": "W255 delivered grenade held/projectile models", "generator": "scripts/art/build_grenades_w255.py",
        "generator_sha256": sha(Path(__file__).read_bytes()), "source_root": str(source),
        "source_provenance": json.loads((source / "PROVENANCE.json").read_text()), "source_inputs_sha256": inputs,
        "blender": stage["blender"], "bindings": bindings, "models": records,
        "method": "Source .blend evaluated in own headless --disable-autoexec process; visible parts only, weld positional seams and collapse <=470 triangles; retain/interpolate uv0; W252 barycentric bake + W115 native triangle adapter. Both thermal transparent parts retained.",
        "basis": "Blender world -> native (x,z,-y); selected original AABB centered at(8,8,8), max extent8 native units. Includes thermal secondary silhouette; no copied preview geometry.",
        "native_rotation": "Rz*Ry*Rx; reconstructed each emitted fragment vertex with error <1e-7 native units",
        "shader_evidence": {"thermal": "Materials/80C308C5.json: no diffuse; PushGlobalChannelVector25. PS_80C3D35F.hlsl: frac(10*v3.xy), abs difference of UV ramps, cb0[5]/[6] colors; selected Transparents0/2, omitted LightShaftOcclusion4/6.",
            "shared_held": "80C33394 / PS_80C37280: same periodic UV-ramp motif, cb0[0]/[1] grey inspection values; Frame26 dissolve. GenerateGbuffer0 retained; ShadowGenerate2/ComputeSkinning4 omitted.",
            "field": "80C3659E / PS_80C3A1A2 and 80C38A97 / PS_80C3A904 bind t0=80C3C18E(sRGB diffuse), t1=80C3C190(packed normal XY). t0 luminance/detail retained with authored element tint and hot-red energy accent. Source alpha not opacity. Gbuffer0 only; no shadow/depth/compute shells."},
        "energy_adaptation": {"palette_source": "guardian/Element.java project Solar FF7A1A/FFD38A, Void A86BFF/E2C8FF, Arc 5FC8FF/C8F4FF; these are product colors, not decoded Destiny runtime globals",
            "grid": "Authored continuous sine-warp noise and soft ripple bands sampled through source UV, R1-lifted radiance floor Solar[255,186,78] to[255,250,215], Void[150,100,225] to[235,210,255]; emission15 with shade=false and front GUI lighting. Source checker deliberately replaced after visual review; no hard checker cells or neutral inspection shell.",
            "field": "Diffuse RGB blended35 percent original plus65 percent luminance times element color for readable blue/purple shells; source detail retained. t0 hot-red texels R>220,G<80,B<60 recolored to glow. Authored tint/energy accent, not decoded shader emission. Bright/mixed fragments emission15/6; shell fragments0.",
            "enemy": "Separate red luminance presentation atlas; energy luminance compressed to a red ramp to preserve ripples after R1 brightness lift. Identical geometry, UV, alpha and emission. Existing AbilityVisualVariants suffix lookup remains compatible."},
        "r1_review": {"evidence": "/private/tmp/destiny-w255/r1/frames/{fusion,solar,vortex,storm}-held-phase3.png and -flight-phase8.png, grenade-contact-sheet.png",
            "finding": "Native four throws succeeded per master. Correct energy geometry appeared dark/faceted in held fixture: initial Solar atlas median luma153/255 versus approximate warm prop pixels89/255. Vanilla item.vsh applies minecraft_mix_light independently of sample_lightmap; light.glsl has0.4 ambient plus0.6 directional light. shade=false/light_emission15 are not an unlit material.",
            "correction": "Energy-only texture radiance floor raised and contrast reduced; energy-only gui_light front selects GuiItemAtlas ITEMS_FLAT rather than ITEMS_3D via ModelRenderProperties. Geometry, UV, alpha, shade and emission unchanged. Physical field diffuse/tint unchanged.",
            "limits": "No shader or runtime changes. Front GUI light selection still uses directional normal lighting; native faceting cannot be fully removed by asset brightness. Held/flight R2 Vision required, including enemy readability."},
        "fallbacks": {"hunter/arc_flashbang": "W252 explosion", "hunter/solar_incendiary": "W252 explosion",
                      "titan/void_grenade": "W252 explosion (Suppressor)", "titan/arc_grenade": "W252 pulse"},
        "limitations": ["Delivery stage/entity assignments are candidates, not runtime-verified phase identity; inventory plug activation is unresolved.",
            "Source thermal globals, derivative filtering, Frame26 dissolve and stochastic discard are unsupported; smooth energy ripples and shell element tints are explicit authored product adaptations; source inspection checker is not shipped.",
            "Original additive/premultiplied transparency, atmospheric/depth/volumetric inputs, normal/PBR and animated particle simulation are not reconstructed.",
            "Native item planes use geometric alpha masks, not source translucent volumetric shells. No extra VFX mesh or depth/shadow/compute shell added.",
            "460-triangle derivatives and 16px atlas islands trade smoothness/detail for <=1000 native elements and 512px atlases.",
            "Master owns native codecs/tests, resource load, Vision first/third-person and flight validation; offline preview does not certify those."],
        "outputs": {str(path): sha(data) for path, data in files.items()}}
    files[MANIFEST] = encode(manifest)
    return files, baked, manifest


def preview(path, baked):
    """Offline rasterization of the EMITTED JSON/atlas, never game evidence."""
    import numpy as np
    from PIL import Image, ImageDraw
    helper = helpers()
    adapter = helper["adapter"]()
    size = 280
    canvas = Image.new("RGB", (size * 4, (size + 45) * 4), (22, 28, 35))
    draw = ImageDraw.Draw(canvas)
    for row, ability in enumerate(PALETTES):
        for col, suffix in enumerate(("held", "held_enemy", "projectile", "projectile_enemy")):
            name = ability + "_" + suffix
            model, texture = baked[name]
            output = np.zeros((size, size, 3), dtype="uint8")
            output[:] = (30, 37, 44)
            depth = np.full((size, size), -1e30)
            for element in model["elements"]:
                lo, hi, rotation = element["from"], element["to"], element["rotation"]
                pivot = rotation["origin"]
                points = [adapter["add"](pivot, adapter["rotate"](adapter["sub"](p, pivot), [rotation[a] for a in "xyz"]))
                    for p in (lo, (hi[0], lo[1], lo[2]), hi, (lo[0], hi[1], lo[2]))]
                uv = [v / 16 for v in element["faces"]["south"]["uv"]]
                texcoords = ((uv[0], 1-uv[3]), (uv[2], 1-uv[3]), (uv[2], 1-uv[1]), (uv[0], 1-uv[1]))
                for ids in ((0, 1, 2), (0, 2, 3)):
                    ps = np.array([adapter["rotate"]([v-8 for v in points[i]], (12, -28, 0)) for i in ids])
                    xy = np.stack((ps[:, 0] * 26 + size / 2, size / 2 - ps[:, 1] * 26), axis=1)
                    x0, x1 = max(0, int(xy[:, 0].min())), min(size, int(xy[:, 0].max()) + 1)
                    y0, y1 = max(0, int(xy[:, 1].min())), min(size, int(xy[:, 1].max()) + 1)
                    if x1 <= x0 or y1 <= y0:
                        continue
                    a, b, c = xy
                    den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                    if abs(den) < 1e-10:
                        continue
                    yy, xx = np.mgrid[y0:y1, x0:x1]
                    xx, yy = xx + .5, yy + .5
                    u = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
                    v = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
                    w = 1-u-v
                    z = u*ps[0, 2]+v*ps[1, 2]+w*ps[2, 2]
                    tc = np.array([texcoords[i] for i in ids])
                    pixels = helper["sample"](texture, u[..., None]*tc[0]+v[..., None]*tc[1]+w[..., None]*tc[2])
                    mask = (u >= 0) & (v >= 0) & (w >= 0) & (z > depth[y0:y1, x0:x1]) & (pixels[..., 3] >= 128)
                    output[y0:y1, x0:x1][mask] = pixels[..., :3][mask]
                    depth[y0:y1, x0:x1][mask] = z[mask]
            y = row * (size + 45)
            canvas.paste(Image.fromarray(output), (col * size, y + 40))
            draw.text((col * size + 8, y + 5), name, fill="white")
            draw.text((col * size + 8, y + 21), f"{len(model['elements'])} elements; offline JSON/atlas", fill=(180, 200, 220))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--blender", type=Path, default=Path("/Applications/Blender.app/Contents/MacOS/Blender"))
    parser.add_argument("--refresh-blender", action="store_true")
    parser.add_argument("--blender-stage", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--preview", type=Path)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    assert not args.cache.resolve().is_relative_to(ROOT), "Raw cache must stay outside worktree"
    assert not args.cache.resolve().is_relative_to(args.source.resolve()), "Source is read-only"
    if args.preview:
        assert not args.preview.resolve().is_relative_to(ROOT), "Preview is not an owned product output"
        assert not args.preview.resolve().is_relative_to(args.source.resolve()), "Source is read-only"
    if args.blender_stage:
        blender_stage(args.source, args.cache)
        return
    if args.refresh_blender or not (args.cache / "evaluated.json").exists():
        subprocess.run(["rtk", "proxy", str(args.blender), "--background", "--factory-startup", "--disable-autoexec",
            "--python", str(Path(__file__).resolve()), "--", "--blender-stage", "--source", str(args.source),
            "--cache", str(args.cache)], check=True)
    stage = json.loads((args.cache / "evaluated.json").read_text())
    files, baked, manifest = generate(stage, args.source)
    for relative, data in files.items():
        path = ROOT / relative
        if args.check:
            assert path.exists() and path.read_bytes() == data, str(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if args.preview:
        preview(args.preview, baked)
    print(json.dumps({"check": args.check, "files": len(files), "models": {
        key: {k: value[k] for k in ("triangles", "elements", "atlas_size")} for key, value in manifest["models"].items()}}))


if __name__ == "__main__":
    main()
