#!/usr/bin/env python3
"""Offline, crop-first GLB surface voxelizer (numpy + Pillow; no downloads).

Example (coordinates are GLB world Y-up, root conversion already included)::
    python3 -B scripts/tower/voxelize_courtyard.py --input tower.textured.glb \
      --output out --crop-min -85 -48 -125 --crop-max 110 70 45 \
      --scale 2 --offset 0 40 0

Optional --config JSON::
    {"texture_mode":"median", "materials": {
       "80B4E6D0":{"block":"minecraft:red_wool", "priority":20},
       "42":{"skip":true},
       "80B4E6B0":{"texture_mode":"sample", "allowed_blocks":["minecraft:stone",
                                                            "minecraft:light_gray_concrete"]}},
     "palette":[{"block":"minecraft:stone", "rgb":[126,126,126]}],
     "rules":[{"mesh":"*canopy*", "block":"minecraft:red_wool"}]}

Material keys match index, name, sourceMaterialTag, or sourceTexture (in that
order). Rules match node/mesh/material with shell wildcards; later rules win.
Default median mode chooses one coherent block per material. Sample mode uses
downsampled textures and deterministic palette matching, never random dithering. Alpha masks still use UVs
in median mode. Missing textures fail loudly; skipped materials and opaque explicit block
overrides do not need texture files. Config can also supply a manifest object (spawn etc.).
The generated spawn is a contract seed with spawnFinalized=false; master must
verify it before installation. No column filling or solid-volume inference.
"""
from __future__ import annotations
import argparse
from collections import Counter
import fnmatch
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
from tower_mesh import GLB, overlaps, transform_bounds
from export_schematic import write_vox, write_schematic

DEFAULT_PALETTE = [
    ("minecraft:white_concrete", (207,213,214)),
    ("minecraft:light_gray_concrete", (125,125,115)),
    ("minecraft:gray_concrete", (54,57,61)),
    ("minecraft:black_concrete", (8,10,15)),
    ("minecraft:stone", (126,126,126)),
    ("minecraft:smooth_stone", (158,158,158)),
    ("minecraft:polished_andesite", (132,135,133)),
    ("minecraft:stone_bricks", (122,121,122)),
    ("minecraft:smooth_quartz", (235,229,222)),
    ("minecraft:quartz_bricks", (235,230,222)),
    ("minecraft:iron_block", (220,220,220)),
    ("minecraft:polished_deepslate", (72,72,73)),
    ("minecraft:light_gray_terracotta", (135,107,98)),
    ("minecraft:brown_terracotta", (77,51,36)),
    ("minecraft:smooth_sandstone", (216,203,155)),
    ("minecraft:red_wool", (161,39,34)),
    ("minecraft:red_concrete", (142,32,32)),
    ("minecraft:orange_terracotta", (161,83,37)),
    ("minecraft:yellow_terracotta", (186,133,35)),
    ("minecraft:moss_block", (89,109,45)),
    ("minecraft:green_concrete", (73,91,36)),
    ("minecraft:green_terracotta", (76,83,42)),
    ("minecraft:dark_prismarine", (51,91,75)),
    ("minecraft:cyan_terracotta", (86,91,91)),
    ("minecraft:blue_concrete", (44,46,143)),
]
SEED_MANIFEST = {
    "schema": 1, "id": "destiny:tower", "voxelResource": "data/destiny/tower/courtyard.vox.gz",
    "spawn": {"x": 44.5, "y": 75.0, "z": -50.5, "yaw": 180.0, "pitch": 0.0},
    "returnBelowY": -60, "worldBorder": 448,
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ragged_grid(lo, hi):
    """Enumerate bounded variable-size integer boxes without a Python per-triangle loop."""
    sizes = np.maximum(hi-lo+1, 0).astype(np.int64)
    counts = np.prod(sizes, axis=1)
    ids = np.repeat(np.arange(len(lo)), counts)
    if not len(ids):
        return ids, np.empty((0, lo.shape[1]), dtype=np.int64)
    starts = np.cumsum(counts)-counts
    rem = np.arange(len(ids), dtype=np.int64)-np.repeat(starts, counts)
    xyz = np.empty((len(ids), lo.shape[1]), dtype=np.int64)
    for dim in reversed(range(lo.shape[1])):
        size = sizes[ids, dim]
        xyz[:, dim] = rem % size + lo[ids, dim]
        rem //= size
    return ids, xyz


def triangle_box_mask(triangles, cells):
    """Exact conservative triangle/unit-box SAT; touching surfaces are retained."""
    centered = triangles - (cells[:, None, :] + 0.5)
    edges = np.roll(triangles, -1, axis=1)-triangles
    keep = np.all((centered.max(axis=1) >= -0.50000001) &
                  (centered.min(axis=1) <= 0.50000001), axis=1)
    normal = np.cross(edges[:, 0], edges[:, 1])
    axes = [normal]
    eye = np.eye(3)
    for e in range(3):
        for dim in range(3):
            axes.append(np.cross(edges[:, e], eye[dim]))
    for axis in axes:
        projection = np.einsum("nij,nj->ni", centered, axis)
        radius = np.abs(axis).sum(axis=1)*0.5 + 1e-8
        keep &= (projection.min(axis=1) <= radius) & (projection.max(axis=1) >= -radius)
    return keep


def surface_cells(triangles, grid_min, grid_max, candidate_budget=200000):
    """Yield (integer cells, original triangle IDs) via dominant-axis projection.

    Projected square coverage uses 2D SAT, then the triangle plane restricts the
    third coordinate to at most a few cells, followed by exact 3D SAT. Work is
    proportional to projected surface area rather than triangle bounding volume.
    Recursion splits oversized batches, never undersamples large triangles.
    """
    triangles = np.asarray(triangles, dtype=np.float64)
    if not len(triangles):
        return
    normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    valid = np.max(np.abs(normals), axis=1) > 1e-14
    # Exact tiny-triangle shortcut: every vertex lies in the same half-open cell.
    # A centroid-only shortcut for boundary-crossing triangles would leave holes.
    bbox_min = np.floor(triangles.min(axis=1)).astype(np.int64)
    bbox_max = np.floor(triangles.max(axis=1)).astype(np.int64)
    contained = valid & np.all(bbox_min == bbox_max, axis=1)
    contained &= np.all(bbox_min >= grid_min, axis=1) & np.all(bbox_max <= grid_max, axis=1)
    if contained.any():
        yield bbox_min[contained], np.flatnonzero(contained)
    valid &= ~contained
    dominant = np.argmax(np.abs(normals), axis=1)
    for axis in range(3):
        original = np.flatnonzero(valid & (dominant == axis))
        if not len(original):
            continue
        other = [i for i in range(3) if i != axis]
        tri = triangles[original]
        projected = tri[:, :, other]
        lower = np.maximum(np.floor(projected.min(axis=1)).astype(np.int64), grid_min[other])
        upper = np.minimum(np.floor(projected.max(axis=1)).astype(np.int64), grid_max[other])
        counts = np.prod(np.maximum(upper-lower+1, 0), axis=1)
        if counts.sum() > candidate_budget and len(original) > 1:
            cut = len(original)//2
            for subset in (original[:cut], original[cut:]):
                for cells, ids in surface_cells(triangles[subset], grid_min, grid_max, candidate_budget):
                    yield cells, subset[ids]
            continue
        # A single triangle's projection can span the crop; tile rows to bound RAM.
        if len(original) == 1 and counts[0] > candidate_budget:
            columns = min(int(upper[0, 1]-lower[0, 1]+1), candidate_budget)
            rows = max(1, candidate_budget//columns)
            for start in range(int(lower[0, 0]), int(upper[0, 0])+1, rows):
                for column in range(int(lower[0, 1]), int(upper[0, 1])+1, columns):
                    sub_min, sub_max = grid_min.copy(), grid_max.copy()
                    sub_min[other] = [start, column]
                    sub_max[other] = [min(start+rows-1, upper[0, 0]), min(column+columns-1, upper[0, 1])]
                    for cells, ids in surface_cells(tri, sub_min, sub_max, candidate_budget):
                        yield cells, original[ids]
            continue
        ids, pixels = ragged_grid(lower, upper)
        if not len(ids):
            continue
        p = projected[ids] - (pixels[:, None, :]+0.5)
        e = np.roll(p, -1, axis=1)-p
        keep = np.ones(len(ids), dtype=bool)
        for edge in range(3):
            a = np.column_stack((-e[:, edge, 1], e[:, edge, 0]))
            dots = np.einsum("nij,nj->ni", p, a)
            r = np.abs(a).sum(axis=1)*0.5 + 1e-8
            keep &= (dots.min(axis=1) <= r) & (dots.max(axis=1) >= -r)
        ids, pixels = ids[keep], pixels[keep]
        if not len(ids):
            continue
        n = normals[original[ids]]
        slopes = -n[:, other]/n[:, axis, None]
        height = tri[ids, 0, axis] + np.sum(slopes*(pixels+0.5-tri[ids, 0][:, other]), axis=1)
        radius = np.abs(slopes).sum(axis=1)*0.5
        bottom = np.maximum(np.floor(height-radius-1e-10).astype(np.int64), grid_min[axis])
        top = np.minimum(np.floor(height+radius+1e-10).astype(np.int64), grid_max[axis])
        # A perfectly flat face belongs to floor(height), not the layer below.
        flat = radius < 1e-12
        bottom[flat] = np.maximum(np.floor(height[flat]+1e-10).astype(np.int64), grid_min[axis])
        depth_ids, levels = ragged_grid(bottom[:, None], top[:, None])
        if not len(depth_ids):
            continue
        cells = np.empty((len(depth_ids), 3), dtype=np.int64)
        cells[:, other] = pixels[depth_ids]
        cells[:, axis] = levels[:, 0]
        tri_ids = original[ids[depth_ids]]
        exact = triangle_box_mask(triangles[tri_ids], cells)
        if exact.any():
            yield cells[exact], tri_ids[exact]


def linear_to_srgb(value):
    value = np.clip(value, 0, 1)
    return np.where(value <= .0031308, 12.92*value, 1.055*value**(1/2.4)-.055)


def srgb_to_linear(value):
    return np.where(value <= .04045, value/12.92, ((value+.055)/1.055)**2.4)


def sample_uv(uv, image, sampler):
    uv = np.array(uv, dtype=np.float64, copy=True)
    for dim, key in enumerate(("wrapS", "wrapT")):
        mode = sampler.get(key, 10497)
        if mode == 33071:
            uv[:, dim] = np.clip(uv[:, dim], 0, np.nextafter(1., 0.))
        elif mode == 33648:
            uv[:, dim] = 1-np.abs(uv[:, dim] % 2-1)
        elif mode == 10497:
            uv[:, dim] %= 1
        else:
            raise ValueError(f"unsupported texture wrap {mode}")
    # glTF UV (0,0) is image top left; do not apply an extra V flip.
    x = np.minimum((uv[:, 0]*image.shape[1]).astype(int), image.shape[1]-1)
    y = np.minimum((uv[:, 1]*image.shape[0]).astype(int), image.shape[0]-1)
    return image[y, x]/255.


def barycentric_at_cells(triangles, cells):
    v0, v1 = triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]
    point = cells+.5-triangles[:, 0]
    a = np.einsum("ij,ij->i", v0, v0)
    b = np.einsum("ij,ij->i", v0, v1)
    c = np.einsum("ij,ij->i", v1, v1)
    d = np.einsum("ij,ij->i", point, v0)
    e = np.einsum("ij,ij->i", point, v1)
    denom = np.maximum(a*c-b*b, 1e-30)
    u, v = (c*d-b*e)/denom, (a*e-b*d)/denom
    weights = np.maximum(np.column_stack((1-u-v, u, v)), 0)
    return weights/weights.sum(axis=1, keepdims=True)


class Materials:
    def __init__(self, glb, config):
        self.glb, self.config = glb, config
        entries = config.get("palette")
        self.palette = [e["block"] for e in entries] if entries is not None else [x[0] for x in DEFAULT_PALETTE]
        self.rgb = np.array([e["rgb"] for e in entries] if entries is not None else [x[1] for x in DEFAULT_PALETTE], dtype=float)
        if not len(self.palette) or self.rgb.shape != (len(self.palette), 3) or not np.isfinite(self.rgb).all():
            raise ValueError("palette must contain block/rgb entries")
        if len(set(self.palette)) != len(self.palette) or len(self.palette) > 65535:
            raise ValueError("palette must contain unique states, at most 65535")
        for state in self.palette:
            self.validate_state(state)
        self.report = {}
        self.cache = {}

    @staticmethod
    def validate_state(state):
        if not isinstance(state, str) or not state.startswith("minecraft:") or state.split("[", 1)[0] in {
                "minecraft:air", "minecraft:cave_air", "minecraft:void_air"}:
            raise ValueError(f"expected non-air vanilla block state: {state!r}")

    def options(self, index, node_name, mesh_name):
        material = self.glb.doc.get("materials", [])[index] if index >= 0 else {}
        extras = material.get("extras", {})
        choices = self.config.get("materials", {})
        keys = (str(index), material.get("name"), extras.get("sourceMaterialTag"), extras.get("sourceTexture"))
        options = {}
        for key in keys:
            if key is not None and key in choices:
                value = choices[key]
                options.update({"block": value} if isinstance(value, str) else value)
                break
        for rule in self.config.get("rules", []):
            names = {"node": node_name, "mesh": mesh_name, "material": material.get("name", str(index))}
            if all(fnmatch.fnmatchcase(names[k], rule[k]) for k in names if k in rule):
                options.update({k:v for k,v in rule.items() if k not in names})
        return options

    def nearest(self, colors, allowed=None):
        candidates = np.arange(len(self.rgb)) if allowed is None else np.array([self.palette.index(s) for s in allowed])
        if not len(candidates):
            raise ValueError("allowed_blocks must not be empty")
        # Redmean distance separates neutral concrete from saturated cloth/greenery.
        diff = colors[:, None, :]-self.rgb[candidates][None, :, :]
        mean_red = (colors[:, None, 0]+self.rgb[candidates][None, :, 0])/2
        distance = (2+mean_red/256)*diff[:, :, 0]**2 + 4*diff[:, :, 1]**2 + (2+(255-mean_red)/256)*diff[:, :, 2]**2
        return candidates[np.argmin(distance, axis=1)]

    def get(self, index, options):
        key = (index, json.dumps(options, sort_keys=True))
        if key in self.cache:
            return self.cache[key]
        mat = self.glb.doc.get("materials", [])[index] if index >= 0 else {}
        pbr = mat.get("pbrMetallicRoughness", {})
        factor = np.asarray(pbr.get("baseColorFactor", [1,1,1,1]), dtype=float)
        factor[:3] *= np.asarray(options.get("tint", [1,1,1]))
        info = pbr.get("baseColorTexture")
        image, sampler = (None, {})
        masked = mat.get("alphaMode") in ("MASK", "BLEND") and not options.get("ignore_alpha", False)
        if info and not options.get("skip") and ("block" not in options or masked):
            image, sampler = self.glb.texture(info["index"])
        pixels = np.ones((1,4)) if image is None else image.reshape(-1,4)/255.
        visible = pixels[:, 3]*factor[3] >= mat.get("alphaCutoff", .5)
        chosen = pixels[visible, :3] if visible.any() else pixels[:, :3]
        rgb = np.median(linear_to_srgb(srgb_to_linear(chosen)*factor[:3]), axis=0)*255
        mode = options.get("texture_mode", self.config.get("texture_mode", "median"))
        if mode not in ("median", "sample"):
            raise ValueError("texture_mode must be median or sample")
        block = options.get("block")
        if block is not None:
            self.validate_state(block)
            if block not in self.palette:
                if len(self.palette) == 65535:
                    raise ValueError("voxel grid supports at most 65535 non-air block states")
                self.palette.append(block)
                self.rgb = np.vstack((self.rgb, rgb))
            choice = self.palette.index(block)
        else:
            choice = int(self.nearest(rgb[None, :], options.get("allowed_blocks"))[0])
        priority = int(options.get("priority", 0))
        if not -32767 <= priority <= 32767:
            raise ValueError("priority outside int16 range")
        result = dict(index=index, material=mat, options=options, factor=factor,
                      texture_info=info, image=image, sampler=sampler, mode=mode,
                      choice=choice, priority=priority, explicit_block=block is not None)
        self.cache[key] = result
        self.report[str(index)+":"+str(len(self.report))] = {
            "index": index, "name": mat.get("name", "<default>"), "extras": mat.get("extras", {}),
            "medianRGB": np.round(rgb, 2).tolist(), "block": self.palette[choice],
            "textureMode": mode, "overrides": options,
        }
        return result

    def color_cells(self, material, triangles, cells, uv_triangles):
        n = len(cells)
        selected = np.full(n, material["choice"], dtype=np.uint16)
        visible = np.ones(n, dtype=bool)
        image = material["image"]
        masked = (material["material"].get("alphaMode") in ("MASK", "BLEND") and
                  not material["options"].get("ignore_alpha", False))
        if image is not None and (material["mode"] == "sample" or masked):
            if uv_triangles is None:
                raise ValueError("textured primitive has no required TEXCOORD accessor")
            weights = barycentric_at_cells(triangles, cells)
            uv = np.einsum("ni,nij->nj", weights, uv_triangles)
            ext = material["texture_info"].get("extensions", {}).get("KHR_texture_transform", {})
            uv *= np.asarray(ext.get("scale", [1,1]))
            angle = ext.get("rotation", 0)
            if angle:
                c, s = math.cos(angle), math.sin(angle)
                uv = uv @ np.array([[c,s],[-s,c]])
            uv += np.asarray(ext.get("offset", [0,0]))
            rgba = sample_uv(uv, image, material["sampler"])
            if masked:
                visible = rgba[:, 3]*material["factor"][3] >= material["material"].get("alphaCutoff", .5)
            if material["mode"] == "sample" and not material["explicit_block"]:
                colors = linear_to_srgb(srgb_to_linear(rgba[:, :3])*material["factor"][:3])*255
                selected = self.nearest(colors, material["options"].get("allowed_blocks")).astype(np.uint16)
        elif masked:
            visible[:] = material["factor"][3] >= material["material"].get("alphaCutoff", .5)
        return selected, visible


def voxelize(glb, crop_min, crop_max, scale, offset, config=None, max_grid_cells=128_000_000,
             batch_triangles=4096, progress=True):
    config = config or {}
    crop_min, crop_max, offset = [np.asarray(v, dtype=float) for v in (crop_min, crop_max, offset)]
    if any(v.shape != (3,) or not np.isfinite(v).all() for v in (crop_min, crop_max, offset)):
        raise ValueError("crop and offset must be finite three-vectors")
    if not np.isfinite(scale) or scale <= 0 or np.any(crop_max <= crop_min):
        raise ValueError("scale must be positive and crop bounds strictly increasing")
    grid_min = np.floor(crop_min*scale+offset).astype(np.int64)
    grid_max = np.ceil(crop_max*scale+offset).astype(np.int64)-1
    if np.any(grid_min < -2147483648) or np.any(grid_max > 2147483647):
        raise ValueError("coordinates exceed signed int32")
    dims = grid_max-grid_min+1
    volume = math.prod(map(int, dims))
    if volume > max_grid_cells:
        raise ValueError(f"crop grid {volume:,} cells exceeds --max-grid-cells {max_grid_cells:,}")
    blocks = np.zeros(tuple(dims), dtype=np.uint16)
    priorities = np.full(tuple(dims), -32768, dtype=np.int16)
    materials = Materials(glb, config)
    stats = Counter()
    started = time.monotonic()
    last_progress = started
    for node_index, mesh_index, world in glb.world_instances():
        stats["instancesSeen"] += 1
        lo, hi = transform_bounds(*glb.mesh_bounds(mesh_index), world)
        if not overlaps(lo, hi, crop_min, crop_max):
            stats["instancesCulled"] += 1
            continue
        stats["instancesIntersectingCrop"] += 1
        mesh = glb.doc["meshes"][mesh_index]
        node = glb.doc["nodes"][node_index]
        for primitive in mesh["primitives"]:
            lo, hi = transform_bounds(*glb.primitive_bounds(primitive), world)
            if not overlaps(lo, hi, crop_min, crop_max):
                stats["primitivesCulled"] += 1
                continue
            if primitive.get("mode", 4) != 4 or primitive.get("targets"):
                raise ValueError("only static triangle-list primitives supported")
            index = primitive.get("material", -1)
            options = materials.options(index, node.get("name", ""), mesh.get("name", ""))
            if options.get("skip"):
                stats["primitivesSkippedByConfig"] += 1
                continue
            material = materials.get(index, options)
            positions = glb.accessor(primitive["attributes"]["POSITION"])
            points = (positions @ world[:3, :3].T + world[:3, 3])*scale+offset
            indices = glb.accessor(primitive["indices"]) if "indices" in primitive else np.arange(len(points))
            if len(indices)%3 or (len(indices) and (indices.min()<0 or indices.max()>=len(points))):
                raise ValueError("invalid triangle index buffer")
            indices = indices.reshape(-1, 3)
            uv = None
            info = material["texture_info"]
            if material["image"] is not None:
                ext = info.get("extensions", {}).get("KHR_texture_transform", {})
                uv_key = "TEXCOORD_"+str(ext.get("texCoord", info.get("texCoord", 0)))
                if uv_key in primitive["attributes"]:
                    uv = glb.accessor(primitive["attributes"][uv_key])
            for start in range(0, len(indices), batch_triangles):
                batch_indices = indices[start:start+batch_triangles]
                triangles = points[batch_indices]
                stats["trianglesDecoded"] += len(triangles)
                # Reject whole triangles in source Y-up before rasterization.
                tri_min, tri_max = triangles.min(axis=1), triangles.max(axis=1)
                valid = np.all(tri_max >= crop_min*scale+offset, axis=1) & np.all(tri_min < crop_max*scale+offset, axis=1)
                stats["trianglesCulled"] += int((~valid).sum())
                triangles, batch_indices = triangles[valid], batch_indices[valid]
                stats["trianglesRasterized"] += len(triangles)
                for cells, ids in surface_cells(triangles, grid_min, grid_max):
                    selected, visible = materials.color_cells(material, triangles[ids], cells,
                                                              uv[batch_indices[ids]] if uv is not None else None)
                    cells, selected = cells[visible], selected[visible]
                    stats["surfaceCandidates"] += len(cells)
                    if not len(cells):
                        continue
                    local = cells-grid_min
                    flat = np.ravel_multi_index(local.T, dims)
                    # Last source triangle wins a same-priority collision, deterministically.
                    _, reverse = np.unique(flat[::-1], return_index=True)
                    choose = len(flat)-1-reverse
                    flat, selected = flat[choose], selected[choose]
                    accepted = material["priority"] >= priorities.ravel()[flat]
                    flat, selected = flat[accepted], selected[accepted]
                    blocks.ravel()[flat] = selected+1
                    priorities.ravel()[flat] = material["priority"]
            stats["primitivesDecoded"] += 1
        now = time.monotonic()
        if progress and now-last_progress >= 10:
            print(json.dumps({"progress": dict(stats), "elapsedSeconds": round(now-started, 1)}), flush=True)
            last_progress = now
    del priorities
    flat = np.flatnonzero(blocks)
    if not len(flat):
        raise ValueError("crop produced no surface voxels")
    xyz = np.column_stack(np.unravel_index(flat, dims))+grid_min
    ids = blocks.ravel()[flat]-1
    # Drop unused palette entries so binary/schematic palettes describe actual records.
    used, compact = np.unique(ids, return_inverse=True)
    palette = [materials.palette[int(i)] for i in used]
    stats["blockCount"] = len(xyz)
    stats["gridCells"] = volume
    stats["elapsedSeconds"] = round(time.monotonic()-started, 3)
    stats["blockHistogram"] = {palette[i]:int(n) for i,n in enumerate(np.bincount(compact))}
    return xyz.astype(np.int32), compact.astype(np.uint16), palette, dict(stats), materials.report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--crop-min", nargs=3, type=float, required=True, metavar=("X","Y","Z"))
    parser.add_argument("--crop-max", nargs=3, type=float, required=True, metavar=("X","Y","Z"))
    parser.add_argument("--scale", type=float, default=2)
    parser.add_argument("--offset", nargs=3, type=float, default=[0,40,0])
    parser.add_argument("--config", "--material-overrides", type=Path)
    parser.add_argument("--contract", type=Path, help="optional map-contract.json seed; binary schema is fixed")
    parser.add_argument("--no-schematic", action="store_true")
    parser.add_argument("--data-version", type=int, default=3955, help="Sponge Minecraft DataVersion (default Java 1.21)")
    parser.add_argument("--max-grid-cells", type=int, default=128_000_000)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text()) if args.config else {}
    contract = json.loads(args.contract.read_text()) if args.contract else {}
    if contract.get("magic", "DGTWR001") != "DGTWR001":
        parser.error("contract magic must be DGTWR001")
    scene = GLB(args.input)
    xyz, ids, palette, stats, material_report = voxelize(scene, args.crop_min, args.crop_max, args.scale,
        args.offset, config, args.max_grid_cells, progress=not args.quiet)
    args.output.mkdir(parents=True, exist_ok=True)
    binary = args.output/"courtyard.vox.gz"
    write_vox(binary, xyz, ids, palette)
    schematic = None
    if not args.no_schematic:
        schematic = write_schematic(args.output/"courtyard.schem", xyz, ids, palette,
                                    data_version=args.data_version, max_cells=args.max_grid_cells)
    # Hash only textures actually read, including external image contents.
    texture_ids = set()
    for item in material_report.values():
        index = item["index"]
        if index < 0:
            continue
        mat = scene.doc["materials"][index]
        info = mat.get("pbrMetallicRoughness", {}).get("baseColorTexture")
        options = item["overrides"]
        masked = mat.get("alphaMode") in ("MASK", "BLEND") and not options.get("ignore_alpha", False)
        if info and ("block" not in options or masked):
            texture_ids.add(scene.doc["textures"][info["index"]]["source"])
    textures = []
    for image_index in sorted(texture_ids):
        desc = scene.doc["images"][image_index]
        if "uri" in desc:
            data = scene.uri_bytes(desc["uri"])
        else:
            view = scene.doc["bufferViews"][desc["bufferView"]]
            start = view.get("byteOffset", 0)
            data = scene.buffer(view.get("buffer", 0))[start:start+view["byteLength"]]
        textures.append({"image": image_index, "uri": desc.get("uri", "<embedded>"),
                         "sha256": hashlib.sha256(data).hexdigest()})
    manifest = dict(SEED_MANIFEST)
    manifest.update({k:v for k,v in contract.get("manifest", {}).items() if k not in ("bounds", "blockCount")})
    manifest.update(config.get("manifest", {}))
    manifest.update(bounds={"min": xyz.min(axis=0).tolist(), "max": xyz.max(axis=0).tolist()},
                    blockCount=len(xyz), spawnFinalized=False, stats=stats,
                    provenance={"source": str(args.input.resolve()), "sourceSHA256": sha256(args.input),
                        "sourceCoordinateSystem": "glTF world Y-up (node hierarchy applied once)",
                        "sourceCropYup": {"min": args.crop_min, "max": args.crop_max},
                        "cropConvention": "min inclusive, max exclusive; output block cells intersect the crop",
                        "transform": {"scale": args.scale, "offset": args.offset},
                        "algorithm": "dominant-axis conservative surface projection + triangle-box SAT; no volume fill",
                        "config": config, "sourceTextures": textures, "binarySHA256": sha256(binary),
                        "scriptsSHA256": {n:sha256(Path(__file__).parent/n) for n in
                            ("voxelize_courtyard.py", "tower_mesh.py", "export_schematic.py")}},
                    schematic=schematic)
    (args.output/"courtyard.json").write_text(json.dumps(manifest, indent=2)+"\n")
    (args.output/"materials.json").write_text(json.dumps(material_report, indent=2)+"\n")
    print(json.dumps({"output": str(args.output), "bounds": manifest["bounds"], "stats": stats}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
