#!/usr/bin/env python3
"""Real community-ripped FBX -> headless Blender decimation -> native triangle atlas.

Run with bundled Python (Pillow/numpy), not Blender, unless --blender-stage.
No live scene, Gradle, Minecraft or main checkout access. External cache is disposable.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "ability_w252/ripped_grenade/"
ASSETS = Path("src/main/resources/assets/destiny")
MANIFEST = Path("art/abilities/w252/ripped-grenade-manifest.json")
CACHE = Path("/private/tmp/destiny-w252/ripped-source")
URL = "https://drive.google.com/uc?export=download&id=1yEfOLn_FJGT2tY5Q5oRNtA0OCnjkt2fQ"
ARCHIVE_SHA = "b3183e471b5ce992a463e4b779a2ce9f0530aab538f770fd21c908ea772bb75f"
DIFFUSE_SHA = {"explosion": "e4a657a0ef9960a4aa4bbd20582cd612c84f0b2ce41c37ffb61804c9f439c1ef", "pulse": "b4a9f460c91c4af1001e778c2055e6a873e6fc8ddfeb881879786e53e5825ae4"}
FBX_SHA = {"explosion": "d4833b00b30efea11d0a8e9fccdea75d7d2874a66c1d394a32b79136c6c7a9cc", "pulse": "1ed683efe866ec5e4611390fd3872e1b1663e4e7cdef71558dfd1179c4f08df0"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def encode(o):
    return (json.dumps(o, ensure_ascii=False, indent=2) + "\n").encode()


def source_inputs():
    CACHE.mkdir(parents=True, exist_ok=True)
    arc = CACHE / "Four Grenade Types.7z"
    if not arc.exists():
        b = urllib.request.urlopen(URL, timeout=45).read()
        assert sha(b) == ARCHIVE_SHA
        arc.write_bytes(b)
    assert sha(arc.read_bytes()) == ARCHIVE_SHA
    for key in ("explosion", "pulse"):
        title = key.title()
        for member, filename, expected in ((f"{title} Grenade/{title} Grenade.fbx", key + ".fbx", FBX_SHA[key]),
                                           (f"{title} Grenade/textures/{title}Grenade_Diffuse.PNG", key + "-diffuse.png", DIFFUSE_SHA[key])):
            target = CACHE / filename
            if not target.exists():
                r = subprocess.run(["rtk", "proxy", "tar", "-xOf", str(arc), member], capture_output=True, check=True)
                assert sha(r.stdout) == expected
                target.write_bytes(r.stdout)
            assert sha(target.read_bytes()) == expected


def blender_stage():
    import bpy
    result = {"blender_version": bpy.app.version_string, "models": {}}
    for key in ("explosion", "pulse"):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(CACHE / (key + ".fbx")), use_anim=False)
        objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        assert objects
        bindings = [{"object": o.name, "matrix_world": [list(r) for r in o.matrix_world],
                     "materials": [s.material.name if s.material else None for s in o.material_slots],
                     "material_alpha": [{"name": s.material.name, "diffuse_alpha": s.material.diffuse_color[3],
                         "principled_alpha": [n.inputs['Alpha'].default_value for n in s.material.node_tree.nodes if n.type=='BSDF_PRINCIPLED'] if s.material.use_nodes else []}
                         for s in o.material_slots if s.material]} for o in objects]
        bpy.ops.object.select_all(action="DESELECT")
        for o in objects:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects) > 1:
            bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        def snapshot(mesh):
            mesh.calc_loop_triangles()
            uv = mesh.uv_layers.active
            assert uv is not None
            out = []
            for t in mesh.loop_triangles:
                points = []
                for vi in t.vertices:
                    p = obj.matrix_world @ mesh.vertices[vi].co
                    points.append([p.x, p.z, -p.y])  # Blender Z-up -> native Y-up.
                out.append({"p": points, "uv": [list(uv.data[i].uv) for i in t.loops], "material": t.material_index})
            return out
        original = snapshot(obj.data)
        # Weld positional FBX seam duplicates while retaining loop UV attributes.
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=0.000001)
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.data.calc_loop_triangles()
        welded = len(obj.data.loop_triangles)
        modifier = obj.modifiers.new("W252_owned_decimation", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.use_collapse_triangulate = True
        ratio = min(1., 475 / welded)
        for attempt in range(12):
            modifier.ratio = ratio
            bpy.context.view_layer.update()
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
            reduced = snapshot(mesh)
            evaluated.to_mesh_clear()
            if len(reduced) <= 490:
                break
            ratio *= .90
        assert 1 < len(reduced) <= 490, (key, len(reduced))
        points = [p for t in original for p in t["p"]]
        lo = [min(p[a] for p in points) for a in range(3)]
        hi = [max(p[a] for p in points) for a in range(3)]
        center = [(a + b) / 2 for a, b in zip(lo, hi)]
        scale = 8 / max(b - a for a, b in zip(lo, hi))
        for triangles in (original, reduced):
            for t in triangles:
                t["p"] = [[8 + (p[a] - center[a]) * scale for a in range(3)] for p in t["p"]]
        result["models"][key] = {"original": original, "reduced": reduced,
            "source_objects": bindings, "original_triangles": len(original), "welded_triangles": welded,
            "reduced_triangles": len(reduced), "decimate_ratio": ratio, "source_bounds_native_basis": [lo, hi],
            "normalization": {"source_center": center, "scale": scale, "target_center": [8, 8, 8], "max_units": 8},
            "uv_policy": "Blender loop UVs retained/interpolated by collapse decimation; diffuse sampled through each resulting triangle's UV."}
        print("W252", key, len(original), "->", len(reduced), flush=True)
    (CACHE / "evaluated.json").write_bytes(encode(result))


def adapter():
    ns = {}
    path = ROOT / "scripts/mesh/native_triangle_elements_w115.py"
    exec(compile(path.read_text(), str(path), "exec"), ns)
    return ns


def bary_uv(point, triangle):
    import numpy as np
    p = np.asarray(triangle["p"])
    uv = np.asarray(triangle["uv"])
    basis = np.stack((p[1] - p[0], p[2] - p[0]), axis=1)
    b, c = np.linalg.lstsq(basis, np.asarray(point) - p[0], rcond=None)[0]
    return uv[0] + b * (uv[1] - uv[0]) + c * (uv[2] - uv[0])


def sample(image, uv):
    import numpy as np
    h, w = image.shape[:2]
    x = np.mod(uv[..., 0], 1.) * (w - 1)
    y = (1 - np.mod(uv[..., 1], 1.)) * (h - 1)
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    x1 = np.minimum(x0 + 1, w - 1); y1 = np.minimum(y0 + 1, h - 1)
    u = (x - x0)[..., None]; v = (y - y0)[..., None]
    return ((1-u)*(1-v)*image[y0,x0]+u*(1-v)*image[y0,x1]+(1-u)*v*image[y1,x0]+u*v*image[y1,x1]).astype('uint8')


def generate(stage):
    import numpy as np
    from PIL import Image
    tri = adapter()
    files = {}; records = {}; baked = {}; proof = {}
    for key, info in stage["models"].items():
        original = np.asarray(Image.open(CACHE / (key + "-diffuse.png")).convert("RGBA"), dtype=float)
        # These Destiny Diffuse alpha channels are packed surface data, not cutout opacity.
        # Native alpha is supplied exclusively by our triangle mask; source RGB stays original.
        original[...,3] = 255
        atlas = np.zeros((1024, 1024, 4), dtype='uint8')
        elements = []; provenance = []; max_error = 0.
        for face_index, triangle in enumerate(info["reduced"]):
            for part in tri["split_triangle"](triangle["p"]):
                i = len(elements); x = (i % 32) * 32; y = (i // 32) * 32
                uv = [(x + 1) / 64, (y + 1) / 64, (x + 31) / 64, (y + 31) / 64]
                element = tri["to_element"](part, f"source_face_{face_index}_half_{i}", uv)
                elements.append(element)
                # Atlas (0,1)=foot, (1,1)=endpoint, (0,0)=third point.
                t0, t1, t2 = [bary_uv(p, triangle) for p in part["vertices"]]
                yy, xx = np.mgrid[0:32, 0:32]
                u = (xx - .5) / 30; v = (yy - .5) / 30
                coords = t0 + u[...,None]*(t1-t0) + (1-v[...,None])*(t2-t0)
                pixels = sample(original, coords)
                # Half-texel conservative edge to prevent transparent seams at finite resolution.
                mask = (u <= v + 1/60) & (u >= -1/30) & (v <= 1+1/30)
                pixels[...,3] = np.where(mask, pixels[...,3], 0)
                atlas[y:y+32,x:x+32] = pixels
                r = element["rotation"]; pivot = r["origin"]
                lo, hi = element["from"], element["to"]
                for p, expected in zip((lo, (hi[0],lo[1],lo[2]), (lo[0],hi[1],lo[2])), part["vertices"]):
                    actual = tri["add"](pivot, tri["rotate"](tri["sub"](p,pivot), [r[a] for a in "xyz"]))
                    max_error = max(max_error, max(abs(a-b) for a,b in zip(actual,expected)))
                provenance.append({"source_decimated_face": face_index, "source_uv": triangle["uv"], "fragment_uv": [t0.tolist(),t1.tolist(),t2.tolist()]})
        assert len(elements) <= 980 and max_error < 1e-7
        for enemy in (False, True):
            name = key + ("_enemy" if enemy else "")
            pixels = atlas.copy()
            if enemy:
                # Explicit presentation tint of the baked original; alpha/UV/geometry unchanged.
                rgb = pixels[...,:3].astype(float)
                rgb[...,0] = np.minimum(255, rgb[...,0]*1.13+32)
                rgb[...,1] *= .62; rgb[...,2] *= .56
                pixels[...,:3] = rgb.astype('uint8')
            out = io.BytesIO(); Image.fromarray(pixels).save(out, format="PNG", optimize=False)
            model = {"ambientocclusion": False, "textures": {"0": "destiny:item/"+PREFIX+name, "particle": "destiny:item/"+PREFIX+name},
                     "elements": elements, "display": {"gui": {"rotation": [15,-30,0], "scale": [1.55]*3}}}
            files[ASSETS/"models/item"/(PREFIX+name+".json")] = encode(model)
            files[ASSETS/"items"/(PREFIX+name+".json")] = encode({"model": {"type": "minecraft:model", "model": "destiny:item/"+PREFIX+name}})
            files[ASSETS/"textures/item"/(PREFIX+name+".png")] = out.getvalue()
            baked[name] = (model,pixels)
        records[key] = {k:v for k,v in info.items() if k not in ("original","reduced")}
        records[key].update({"elements": len(elements), "geometry_mapping_max_error_units": max_error,
            "decimated_geometry_uv_sha256": sha(encode(info["reduced"])), "fragment_uv_provenance_sha256": sha(encode(provenance)),
            "original_fbx_sha256": FBX_SHA[key], "original_diffuse_sha256": DIFFUSE_SHA[key]})
        proof[key] = provenance
    manifest = {"revision": "W252 real ripped grenade temporary props", "generator": "scripts/art/build_ripped_grenades_w252.py",
        "archive": {"url": URL, "sha256": ARCHIVE_SHA, "ripper_game_build_date": "Not supplied in archive", "credit": "Bungie Destiny design; community rip archive"},
        "method": "Actual FBX import with evaluated object transforms; weld positional duplicates; Blender collapse <=490 triangles; preserve/interpolate loop UV; bake original Diffuse into per-fragment alpha atlas; existing native_triangle_elements_w115 adapter.",
        "native_rotation": "Rz*Ry*Rx, adapter rotationZYX, checked against fragment vertices",
        "basis": "FBX importer -> Blender world -> native (x,z,-y), center original AABB at (8,8,8), max extent8 units=.5block; FP .5-.6 gives .25-.3block",
        "blender": stage["blender_version"], "models": records,
        "mapping": {"hunter/arc_flashbang": "explosion (Flashbang screenshot-corresponding explosive family; archive not individually named Flashbang)",
            "titan/arc_grenade": "pulse (archive named Pulse Grenade)", "warlock/arc_grenade": "pulse (Storm temporary substitute)",
            "others": "explosion (Incendiary, Suppressor, Vortex, Fusion, Solar temporary substitute; not their exact individual shells)"},
        "enemy": "Red presentation tint of original Diffuse bake; same geometry/UV/alpha. Existing AbilityVisualVariants selects _enemy.",
        "source_alpha": "Diffuse alpha is packed surface data, not imported as cutout opacity. Original RGB baked opaque inside triangle mask; PNG alpha comes only from geometric triangle coverage.",
        "limitations": ["Decimated derivative, not unchanged original polygon topology/UV", "Diffuse only; original normal/PBR/emission not restored", "Finite atlas resolution and conservative half-texel triangle edges", "Native alpha rendering, resource load, first/third-person fit and performance require master", "No further missing-rip requests; temporary substitutions intentional"],
        "outputs": {str(p):sha(b) for p,b in files.items()}}
    files[MANIFEST] = encode(manifest)
    return files,baked,manifest


def preview(path, stage, baked):
    import numpy as np
    from PIL import Image, ImageDraw
    tri = adapter(); canvas = Image.new("RGB",(1440,900),(22,28,35)); draw = ImageDraw.Draw(canvas)
    def render(triangles, texture):
        size=350; output=np.zeros((size,size,3),dtype='uint8');output[:]=(30,37,44);depth=np.full((size,size),-1e30)
        # All panels share camera, center, scale and directional light.
        for points,uv in triangles:
            ps=np.array([tri['rotate']([x-8 for x in p],(12,-28,0)) for p in points])
            n=np.cross(ps[1]-ps[0],ps[2]-ps[0]); norm=np.linalg.norm(n)
            if norm<1e-12:continue
            light=.65+.35*abs(np.dot(n/norm,[.3,.6,.74]))
            xy=np.stack([ps[:,0]*35+size/2,size/2-ps[:,1]*35],axis=1)
            x0=max(0,int(xy[:,0].min()));x1=min(size,int(xy[:,0].max())+1);y0=max(0,int(xy[:,1].min()));y1=min(size,int(xy[:,1].max())+1)
            if x1<=x0 or y1<=y0:continue
            a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5;yy=yy+.5
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
            z=u*ps[0,2]+v*ps[1,2]+w*ps[2,2];uv=np.array(uv)
            coords=u[...,None]*uv[0]+v[...,None]*uv[1]+w[...,None]*uv[2]
            col=sample(texture,coords);mask=(u>=0)&(v>=0)&(w>=0)&(z>depth[y0:y1,x0:x1])&(col[...,3]>=128)
            output[y0:y1,x0:x1][mask]=(col[...,:3]*light).astype('uint8')[mask];depth[y0:y1,x0:x1][mask]=z[mask]
        return Image.fromarray(output)
    for row,key in enumerate(("explosion","pulse")):
        source=np.asarray(Image.open(CACHE/(key+'-diffuse.png')).convert('RGBA'),dtype=float)
        source[...,3]=255
        views=[('Original FBX + original UV/Diffuse',[(t['p'],t['uv']) for t in stage['models'][key]['original']],source)]
        for name in (key,key+'_enemy'):
            model,texture=baked[name];faces=[]
            for e in model['elements']:
                lo,hi=e['from'],e['to'];r=e['rotation'];pivot=r['origin'];points=[]
                for p in (lo,(hi[0],lo[1],lo[2]),hi,(lo[0],hi[1],lo[2])):
                    points.append(tri['add'](pivot,tri['rotate'](tri['sub'](p,pivot),[r[a] for a in 'xyz'])))
                uv=e['faces']['south']['uv'];uv=[v/16 for v in uv]
                tex=((uv[0],uv[3]),(uv[2],uv[3]),(uv[2],uv[1]),(uv[0],uv[1]))
                for ids in ((0,1,2),(0,2,3)):faces.append(([points[i] for i in ids],[tex[i] for i in ids]))
            # Atlas V is already top-down; sample() expects bottom-up source UV.
            faces=[(p,[(u,1-v) for u,v in uv]) for p,uv in faces]
            views.append((name+' emitted JSON + baked atlas',faces,texture.astype(float)))
        views.append(('Decimated FBX geometry / source UV',[(t['p'],t['uv']) for t in stage['models'][key]['reduced']],source))
        for col,(label,faces,texture) in enumerate(views):
            canvas.paste(render(faces,texture),(col*360+5,row*440+60));draw.text((col*360+8,row*440+20),key,fill='white');draw.text((col*360+8,row*440+38),label,fill=(200,210,220))
        draw.text((10,row*440+420),f"{key}: {stage['models'][key]['original_triangles']} -> {stage['models'][key]['reduced_triangles']} triangles; {len(baked[key][0]['elements'])} native elements. Offline only; no native renderer claim.",fill='white')
    path.parent.mkdir(parents=True,exist_ok=True);canvas.save(path)


def main():
    if '--blender-stage' in sys.argv:
        blender_stage();return
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');ap.add_argument('--refresh-blender',action='store_true');ap.add_argument('--preview',type=Path);args=ap.parse_args()
    source_inputs()
    if args.refresh_blender or not (CACHE/'evaluated.json').exists():
        subprocess.run(['rtk','proxy','/Applications/Blender.app/Contents/MacOS/Blender','--background','--factory-startup','--python',str(Path(__file__).resolve()),'--','--blender-stage'],check=True)
    stage=json.loads((CACHE/'evaluated.json').read_text());files,baked,manifest=generate(stage)
    for rel,data in files.items():
        path=ROOT/rel
        if args.check:assert path.exists() and path.read_bytes()==data, str(rel)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    if args.preview:preview(args.preview,stage,baked)
    print(json.dumps({'check':args.check,'files':len(files),'models':{k:{'triangles':v['reduced_triangles'],'elements':v['elements']} for k,v in manifest['models'].items()},'preview':str(args.preview)}))


if __name__=='__main__':
    main()
