#!/usr/bin/env python3
"""W300 "A Guardian Rises" map pipeline.

Turns the extracted Destiny 2 map GLBs (maps_glb/*.textured.glb, read-only source) into compact
Minecraft block zones (.zone) plus zone-local gameplay markers (markers.json).

Run with a Python that has numpy, e.g. Blender's bundled interpreter:
  PY=/Applications/Blender.app/Contents/Resources/5.4/python/bin/python3.13
  $PY scripts/campaign/rising_maps.py survey   --zone breach      # top-down review rasters
  $PY scripts/campaign/rising_maps.py build    --zone all         # voxelize + write .zone/markers
  $PY scripts/campaign/rising_maps.py preview  --zone all         # review renders of the voxel result

Coordinates: source JSON/CSV are Destiny Z-up (x, y, z).  Minecraft/glTF is (x, z, -y) with the
same metre unit (the README's conversion; GLBs already carry it on their root node, so we read the
child node TRS in source space and convert once ourselves).  Zone-local block coordinates are
floor((mc - zone_min) * SCALE).
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import math
import os
import struct
import sys
import time
import zlib
from pathlib import Path

import numpy as np

SRC = Path(os.environ.get("RISING_SRC", "/Users/qf/Downloads/Rising-Guardian-2026-11-01"))
REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "src/main/resources/data/destiny/guardian_rises/zones"
EVIDENCE = Path(os.environ.get("RISING_EVIDENCE",
                               "/Users/qf/IdeaProjects/DestinyGuardians-wortrees/w300-evidence/map"))


# --------------------------------------------------------------------------------------------
# PNG I/O (no PIL in Blender's python)
# --------------------------------------------------------------------------------------------

def png_read(path: Path) -> np.ndarray:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    pos, idat, w = 8, [], 0
    while pos < len(data):
        ln, = struct.unpack(">I", data[pos:pos + 4]); typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR":
            w, h, bd, ct, _, _, il = struct.unpack(">IIBBBBB", body)
            if bd != 8 or il != 0 or ct not in (2, 6):
                raise ValueError(f"unsupported png {path} {bd} {ct} {il}")
            ch = 4 if ct == 6 else 3
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    raw = np.frombuffer(zlib.decompress(b"".join(idat)), dtype=np.uint8)
    stride = w * ch
    raw = raw.reshape(h, stride + 1)
    out = np.zeros((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.int32)
    for y in range(h):
        f = raw[y, 0]; line = raw[y, 1:].astype(np.int32)
        if f == 0:
            cur = line
        elif f == 2:
            cur = (line + prev) & 255
        elif f in (1, 3, 4):
            cur = np.zeros(stride, dtype=np.int32)
            for x in range(stride):  # rare path; acceptable for the few textures using it
                a = cur[x - ch] if x >= ch else 0
                b = prev[x]
                c = prev[x - ch] if x >= ch else 0
                if f == 1:
                    p = a
                elif f == 3:
                    p = (a + b) >> 1
                else:
                    pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                    p = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                cur[x] = (line[x] + p) & 255
        else:
            raise ValueError(f)
        out[y] = cur; prev = cur
    img = out.reshape(h, w, ch)
    if ch == 3:
        img = np.concatenate([img, np.full((h, w, 1), 255, np.uint8)], axis=2)
    return img


def png_write(path: Path, rgb: np.ndarray) -> None:
    rgb = np.ascontiguousarray(rgb.astype(np.uint8))
    h, w, ch = rgb.shape
    ct = 6 if ch == 4 else 2
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ct, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


# --------------------------------------------------------------------------------------------
# Textures: downsampled colour cache (Blender's image loader when available)
# --------------------------------------------------------------------------------------------

TEX_RES = 128
_TEX_CACHE: dict[str, np.ndarray] = {}
CACHE_DIR = EVIDENCE / "cache"


def _load_full_texture(path: Path) -> np.ndarray:
    try:
        import bpy  # type: ignore
        img = bpy.data.images.load(str(path), check_existing=False)
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        # Blender pixels are linear for sRGB images when colorspace is sRGB; read as stored bytes.
        arr = px.reshape(h, w, 4)[::-1]  # bottom-up -> top-down
        return arr
    except ImportError:
        return png_read(path).astype(np.float32) / 255.0


def texture(uri: str) -> np.ndarray:
    """Returns a TEX_RES x TEX_RES x 4 float32 sRGB [0,1] texture (top row = v 0)."""
    if uri in _TEX_CACHE:
        return _TEX_CACHE[uri]
    name = Path(uri).name
    cpath = CACHE_DIR / f"tex_{TEX_RES}_{name}.npy"
    if cpath.exists():
        arr = np.load(cpath)
    else:
        full = _load_full_texture((SRC / "maps_glb" / uri).resolve())
        h, w = full.shape[:2]
        ys = (np.arange(TEX_RES + 1) * h // TEX_RES); xs = (np.arange(TEX_RES + 1) * w // TEX_RES)
        # box filter via cumulative sums
        cs = np.cumsum(np.cumsum(np.pad(full, ((1, 0), (1, 0), (0, 0))), 0), 1)
        s = cs[ys[1:]][:, xs[1:]] - cs[ys[:-1]][:, xs[1:]] - cs[ys[1:]][:, xs[:-1]] + cs[ys[:-1]][:, xs[:-1]]
        area = ((ys[1:] - ys[:-1])[:, None] * (xs[1:] - xs[:-1])[None, :]).astype(np.float32)
        arr = (s / np.maximum(area, 1)[..., None]).astype(np.float32)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(cpath, arr)
    _TEX_CACHE[uri] = arr
    return arr


# --------------------------------------------------------------------------------------------
# GLB scene access (source Z-up space)
# --------------------------------------------------------------------------------------------

def quat_matrix(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]], dtype=np.float64)


class Glb:
    def __init__(self, path: Path):
        self.path = path
        with open(path, "rb") as f:
            f.read(12)
            ln, _ = struct.unpack("<II", f.read(8))
            self.j = json.loads(f.read(ln))
            ln2, _ = struct.unpack("<II", f.read(8))
            self.bin = f.read(ln2)
        j = self.j
        root = j["scenes"][0]["nodes"][0]
        self.nodes = [j["nodes"][i] for i in j["nodes"][root].get("children", [])]
        self.layout = {}
        lay = path.with_name(path.name.replace(".textured.glb", ".layout.json"))
        if lay.exists():
            self.layout = {m["id"]: m for m in json.loads(lay.read_text())["meshes"]}
        self._mesh_cache: dict[int, list] = {}
        # instance world bounds (source space)
        boxes, mats = [], []
        for n in self.nodes:
            mn, mx = self.mesh_bounds(n["mesh"])
            m = self.node_matrix(n)
            corners = np.array([[a, b, c] for a in (mn[0], mx[0]) for b in (mn[1], mx[1]) for c in (mn[2], mx[2])])
            w = corners @ m[:3, :3].T + m[:3, 3]
            boxes.append((w.min(0), w.max(0))); mats.append(m)
        self.inst_min = np.array([b[0] for b in boxes]); self.inst_max = np.array([b[1] for b in boxes])
        self.inst_mat = mats

    def node_matrix(self, n):
        m = np.eye(4)
        r = quat_matrix(n.get("rotation", [0, 0, 0, 1]))
        s = np.array(n.get("scale", [1, 1, 1]))
        m[:3, :3] = r * s[None, :]
        m[:3, 3] = n.get("translation", [0, 0, 0])
        return m

    def mesh_bounds(self, mi):
        mn, mx = np.full(3, np.inf), np.full(3, -np.inf)
        for p in self.j["meshes"][mi]["primitives"]:
            a = self.j["accessors"][p["attributes"]["POSITION"]]
            if "min" in a:
                mn = np.minimum(mn, a["min"]); mx = np.maximum(mx, a["max"])
            else:
                v = self.accessor(p["attributes"]["POSITION"])
                mn = np.minimum(mn, v.min(0)); mx = np.maximum(mx, v.max(0))
        return mn, mx

    def accessor(self, ai):
        a = self.j["accessors"][ai]; bv = self.j["bufferViews"][a["bufferView"]]
        comp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        arr = np.frombuffer(self.bin, dtype=dt, count=a["count"] * comp, offset=off)
        return arr.reshape(a["count"], comp) if comp > 1 else arr

    def mesh_name(self, mi):
        return self.j["meshes"][mi]["name"]

    def is_terrain(self, mi):
        return bool(self.j["meshes"][mi].get("extras", {}).get("terrain"))

    def primitives(self, mi):
        if mi not in self._mesh_cache:
            out = []
            for p in self.j["meshes"][mi]["primitives"]:
                pos = self.accessor(p["attributes"]["POSITION"]).astype(np.float64)
                uv = self.accessor(p["attributes"]["TEXCOORD_0"]).astype(np.float32) \
                    if "TEXCOORD_0" in p["attributes"] else np.zeros((len(pos), 2), np.float32)
                idx = self.accessor(p["indices"]).reshape(-1, 3)
                out.append((pos, uv, idx, p.get("material", -1)))
            self._mesh_cache[mi] = out
        return self._mesh_cache[mi]

    def material_texture(self, mat):
        if mat < 0:
            return None
        m = self.j["materials"][mat]
        t = m.get("pbrMetallicRoughness", {}).get("baseColorTexture")
        if not t:
            return None
        return self.j["images"][self.j["textures"][t["index"]]["source"]]["uri"]

    def material_factor(self, mat):
        if mat < 0:
            return np.array([0.6, 0.6, 0.6, 1.0])
        return np.array(self.j["materials"][mat].get("pbrMetallicRoughness", {}).get("baseColorFactor", [1, 1, 1, 1]))

    def instances_in(self, lo, hi):
        """Instance indices whose source-space AABB intersects [lo, hi]."""
        lo = np.asarray(lo); hi = np.asarray(hi)
        ok = np.all(self.inst_max >= lo, 1) & np.all(self.inst_min <= hi, 1)
        return np.nonzero(ok)[0]


def src_to_mc(p):
    p = np.asarray(p, dtype=np.float64)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], axis=-1)


# --------------------------------------------------------------------------------------------
# Triangle surface sampling
# --------------------------------------------------------------------------------------------

_BARY_CACHE: dict[int, np.ndarray] = {}


def bary_grid(n: int) -> np.ndarray:
    """Barycentric (u, v) points of a triangle subdivided into n steps per edge."""
    if n not in _BARY_CACHE:
        i, k = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
        m = (i + k) <= n
        uv = np.stack([i[m], k[m]], 1).astype(np.float64) / n
        _BARY_CACHE[n] = uv
    return _BARY_CACHE[n]


_CUTOUT: dict = {}


def is_cutout(uri) -> bool:
    """Alpha is treated as opacity only for clearly binary (foliage/decal card) textures."""
    if not uri:
        return False
    if uri not in _CUTOUT:
        a = texture(uri)[..., 3]
        f0 = float((a < 0.1).mean()); f1 = float((a > 0.9).mean())
        _CUTOUT[uri] = f0 > 0.15 and f0 + f1 > 0.8
    return _CUTOUT[uri]


def sample_instance(glb: Glb, inst: int, lo, hi, step: float, max_samples=4_000_000):
    """Surface samples of one placed instance inside source-space box [lo, hi].

    Returns (points[N,3] source space, rgba[N,4], normal_z[N]) or None."""
    n = glb.nodes[inst]; m = glb.inst_mat[inst]
    lo = np.asarray(lo); hi = np.asarray(hi)
    out_p, out_c, out_n = [], [], []
    for pos, uv, idx, mat in glb.primitives(n["mesh"]):
        w = pos @ m[:3, :3].T + m[:3, 3]
        tri = w[idx]  # T,3,3
        tmin = tri.min(1); tmax = tri.max(1)
        keep = np.all(tmax >= lo, 1) & np.all(tmin <= hi, 1)
        if not keep.any():
            continue
        tri = tri[keep]; tuv = uv[idx[keep]]
        e = np.stack([np.linalg.norm(tri[:, 1] - tri[:, 0], axis=1),
                      np.linalg.norm(tri[:, 2] - tri[:, 1], axis=1),
                      np.linalg.norm(tri[:, 0] - tri[:, 2], axis=1)], 1).max(1)
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nl = np.linalg.norm(nrm, axis=1)
        nz = np.where(nl > 1e-12, nrm[:, 2] / np.maximum(nl, 1e-12), 0.0)
        steps = np.clip(np.ceil(e / step).astype(np.int64), 1, 600)
        uri = glb.material_texture(mat)
        tex = texture(uri) if uri else None
        fac = glb.material_factor(mat)
        cut = is_cutout(uri)
        for s in np.unique(steps):
            sel = np.nonzero(steps == s)[0]
            b = bary_grid(int(s))  # P,2
            # chunk to bound memory
            per = max(1, max_samples // len(b))
            for c0 in range(0, len(sel), per):
                cs = sel[c0:c0 + per]
                t = tri[cs]; tu = tuv[cs]
                u = b[:, 0][None, :, None]; v = b[:, 1][None, :, None]
                p = t[:, 0:1] * (1 - u - v) + t[:, 1:2] * u + t[:, 2:3] * v
                q = tu[:, 0:1] * (1 - u - v) + tu[:, 1:2] * u + tu[:, 2:3] * v
                p = p.reshape(-1, 3); q = q.reshape(-1, 2)
                inside = np.all((p >= lo) & (p <= hi), 1)
                if not inside.any():
                    continue
                p = p[inside]; q = q[inside]
                if tex is not None:
                    tx = (np.mod(q[:, 0], 1.0) * TEX_RES).astype(np.int64) % TEX_RES
                    ty = (np.mod(q[:, 1], 1.0) * TEX_RES).astype(np.int64) % TEX_RES
                    col = tex[ty, tx] * fac[None, :]
                    if cut:
                        vis = col[:, 3] >= 0.5
                        p, col, inside = p[vis], col[vis], np.nonzero(inside)[0][vis]
                        if not len(p):
                            continue
                else:
                    col = np.repeat(fac[None, :], len(p), 0)
                out_p.append(p); out_c.append(col.astype(np.float32))
                out_n.append(np.repeat(nz[cs], len(b))[inside].astype(np.float32))
    if not out_p:
        return None
    return np.concatenate(out_p), np.concatenate(out_c), np.concatenate(out_n)


# --------------------------------------------------------------------------------------------
# Survey: top-down review rasters of a source region
# --------------------------------------------------------------------------------------------

def survey(glb_name: str, lo, hi, res: float, out: Path, marks=()):
    glb = Glb(SRC / "maps_glb" / f"{glb_name}.textured.glb")
    lo = np.array(lo, float); hi = np.array(hi, float)
    nx = int(math.ceil((hi[0] - lo[0]) / res)); ny = int(math.ceil((hi[1] - lo[1]) / res))
    zbuf = np.full((ny, nx), -1e9); cbuf = np.zeros((ny, nx, 3), np.float32)
    insts = glb.instances_in(lo, hi)
    # skip giant sky/background shells larger than the region in every axis
    t0 = time.time()
    for i in insts:
        s = sample_instance(glb, i, lo, hi, res * 0.7)
        if s is None:
            continue
        p, c, _ = s
        ix = ((p[:, 0] - lo[0]) / res).astype(np.int64).clip(0, nx - 1)
        iy = ((hi[1] - p[:, 1]) / res).astype(np.int64).clip(0, ny - 1)  # north up
        order = np.argsort(p[:, 2])
        ix, iy, z, c = ix[order], iy[order], p[order, 2], c[order]
        # last write wins = highest z
        upd = z > zbuf[iy, ix]
        zbuf[iy[upd], ix[upd]] = z[upd]; cbuf[iy[upd], ix[upd]] = c[upd, :3]
    print(f"survey {glb_name}: {len(insts)} instances {time.time() - t0:.1f}s", file=sys.stderr)
    valid = zbuf > -1e8
    zr = zbuf[valid]
    zlo, zhi = (np.percentile(zr, 2), np.percentile(zr, 98)) if len(zr) else (0, 1)
    shade = np.clip((zbuf - zlo) / max(zhi - zlo, 1e-3), 0, 1)
    img = np.clip(cbuf * (0.45 + 0.55 * shade[..., None]), 0, 1)
    img[~valid] = (0.05, 0.0, 0.08)
    img = (img * 255).astype(np.uint8)
    for (mx, my, colr) in marks:
        cx = int((mx - lo[0]) / res); cy = int((hi[1] - my) / res)
        if 0 <= cx < nx and 0 <= cy < ny:
            img[max(cy - 1, 0):cy + 2, max(cx - 1, 0):cx + 2] = colr
    # grid every 50 m
    for gx in np.arange(math.ceil(lo[0] / 50) * 50, hi[0], 50):
        img[:, min(int((gx - lo[0]) / res), nx - 1)] //= 2
    for gy in np.arange(math.ceil(lo[1] / 50) * 50, hi[1], 50):
        img[min(int((hi[1] - gy) / res), ny - 1)] //= 2
    png_write(out, img)
    np.save(out.with_suffix(".z.npy"), zbuf.astype(np.float32))
    print(f"  -> {out} z[{zlo:.1f},{zhi:.1f}]", file=sys.stderr)


# --------------------------------------------------------------------------------------------
# Curated vanilla palette (mirrored in ZonePalette.java for provenance/validation)
# --------------------------------------------------------------------------------------------

MC_JAR = Path(os.environ.get("RISING_MC_JAR", str(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-client.jar")))

# name, texture, family, slab (or None), allowed for terrain
# families: snow, ground, rock, concrete, metal, rust, paint, teal, glass, dark
PALETTE_DEF = [
    ("snow_block", "snow", "snow", "snow[layers=4]", True),
    ("calcite", "calcite", "concrete", "polished_diorite_slab", True),
    ("polished_diorite", "polished_diorite", "concrete", "polished_diorite_slab", False),
    ("smooth_stone", "smooth_stone", "concrete", "smooth_stone_slab", False),
    ("andesite", "andesite", "rock", "andesite_slab", True),
    ("polished_andesite", "polished_andesite", "concrete", "polished_andesite_slab", False),
    ("stone", "stone", "rock", "stone_slab", True),
    ("stone_bricks", "stone_bricks", "concrete", "stone_brick_slab", False),
    ("tuff", "tuff", "rock", "tuff_slab", True),
    ("polished_tuff", "polished_tuff", "concrete", "polished_tuff_slab", False),
    ("cobbled_deepslate", "cobbled_deepslate", "rock", "cobbled_deepslate_slab", True),
    ("polished_deepslate", "polished_deepslate", "metal", "polished_deepslate_slab", False),
    ("deepslate_tiles", "deepslate_tiles", "metal", "deepslate_tile_slab", False),
    ("polished_blackstone", "polished_blackstone", "dark", "polished_blackstone_slab", False),
    ("netherite_block", "netherite_block", "dark", "polished_blackstone_slab", False),
    ("smooth_basalt", "smooth_basalt", "metal", "polished_deepslate_slab", False),
    ("iron_block", "iron_block", "metal", "smooth_stone_slab", False),
    ("waxed_exposed_cut_copper", "exposed_cut_copper", "rust", "waxed_exposed_cut_copper_slab", False),
    ("waxed_weathered_cut_copper", "weathered_cut_copper", "teal", "waxed_weathered_cut_copper_slab", False),
    ("waxed_oxidized_cut_copper", "oxidized_cut_copper", "teal", "waxed_oxidized_cut_copper_slab", False),
    ("waxed_cut_copper", "cut_copper", "rust", "waxed_cut_copper_slab", False),
    ("terracotta", "terracotta", "rust", "granite_slab", False),
    ("granite", "granite", "rust", "granite_slab", True),
    ("brown_terracotta", "brown_terracotta", "rust", None, True),
    ("soul_soil", "soul_soil", "ground", None, True),
    ("podzol", "podzol_top", "ground", None, True),
    ("orange_terracotta", "orange_terracotta", "rust", "cut_red_sandstone_slab", False),
    ("red_terracotta", "red_terracotta", "rust", None, False),
    ("yellow_terracotta", "yellow_terracotta", "paint", None, False),
    ("light_gray_terracotta", "light_gray_terracotta", "rust", "mud_brick_slab", False),
    ("cyan_terracotta", "cyan_terracotta", "concrete", None, False),
    ("gray_terracotta", "gray_terracotta", "rust", None, False),
    ("packed_mud", "packed_mud", "ground", "mud_brick_slab", True),
    ("mud_bricks", "mud_bricks", "rust", "mud_brick_slab", False),
    ("coarse_dirt", "coarse_dirt", "ground", None, True),
    ("rooted_dirt", "rooted_dirt", "ground", None, True),
    ("dirt", "dirt", "ground", None, True),
    ("moss_block", "moss_block", "ground", None, True),
    ("prismarine", "prismarine", "teal", "prismarine_slab", False),
    ("dark_prismarine", "dark_prismarine", "teal", "dark_prismarine_slab", False),
    ("orange_concrete", "orange_concrete", "paint", None, False),
    ("yellow_concrete", "yellow_concrete", "paint", None, False),
    ("white_concrete", "white_concrete", "concrete", "polished_diorite_slab", False),
]
GLASS = "gray_stained_glass"
LIGHT_BLOCKS = ("ochre_froglight", "lantern", "sea_lantern", "shroomlight")
_JAR_TEX: dict[str, np.ndarray] = {}


def jar_texture_rgb(tex: str) -> np.ndarray:
    """Average opaque sRGB colour of a vanilla block texture (read from the local client jar)."""
    if tex not in _JAR_TEX:
        import zipfile
        with zipfile.ZipFile(MC_JAR) as z:
            raw = z.read(f"assets/minecraft/textures/block/{tex}.png")
        tmp = CACHE_DIR / f"mc_{tex}.png"; tmp.parent.mkdir(parents=True, exist_ok=True); tmp.write_bytes(raw)
        img = _load_full_texture(tmp)
        img = img[:img.shape[1]] if img.shape[0] > img.shape[1] else img  # animated strips: first frame
        a = img[..., 3] > 0.5
        _JAR_TEX[tex] = img[..., :3][a].mean(0) if a.any() else img[..., :3].reshape(-1, 3).mean(0)
    return _JAR_TEX[tex]


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    c = np.asarray(rgb, np.float64)
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


# --------------------------------------------------------------------------------------------
# Voxelization
# --------------------------------------------------------------------------------------------

class Grid:
    """Zone block grid.  src box (Z-up) -> Minecraft-frame block indices (x, y, z)."""

    def __init__(self, src_lo, src_hi, scale=1.0):
        self.src_lo = np.array(src_lo, float); self.src_hi = np.array(src_hi, float); self.scale = scale
        self.mc_min = np.array([self.src_lo[0], self.src_lo[2], -self.src_hi[1]])
        ext = (self.src_hi - self.src_lo)[[0, 2, 1]]
        self.size = tuple(int(math.ceil(e * scale)) for e in ext)  # sx, sy, sz

    def to_block(self, src):
        return (src_to_mc(src) - self.mc_min) * self.scale

    def src_of_block(self, b):
        mc = np.asarray(b, float) / self.scale + self.mc_min
        return np.stack([mc[..., 0], -mc[..., 2], mc[..., 1]], -1)

    def flat(self, ix, iy, iz):
        sx, sy, sz = self.size
        return (iy.astype(np.int64) * sz + iz) * sx + ix


class Agg:
    """Sparse per-voxel sample statistics with streaming merge."""
    FIELDS = ("cnt", "r", "g", "b", "terr", "up", "down", "vert")

    def __init__(self):
        self.key = np.zeros(0, np.int64); self.occ = np.zeros(0, np.uint8)
        self.f = {k: np.zeros(0, np.float64) for k in self.FIELDS}
        self.pend: list = []; self.pend_n = 0

    def add(self, key, sub, rgb, terr, nz):
        self.pend.append((key, sub, rgb, terr, nz)); self.pend_n += len(key)
        if self.pend_n > 8_000_000:
            self.flush()

    def flush(self):
        if not self.pend:
            return
        key = np.concatenate([p[0] for p in self.pend]); sub = np.concatenate([p[1] for p in self.pend])
        rgb = np.concatenate([p[2] for p in self.pend]); terr = np.concatenate([p[3] for p in self.pend])
        nz = np.concatenate([p[4] for p in self.pend])
        self.pend = []; self.pend_n = 0
        vals = {"cnt": np.ones(len(key)), "r": rgb[:, 0], "g": rgb[:, 1], "b": rgb[:, 2],
                "terr": terr.astype(np.float64), "up": (nz > 0.6).astype(np.float64),
                "down": (nz < -0.6).astype(np.float64), "vert": (np.abs(nz) < 0.35).astype(np.float64)}
        occ = (np.uint8(1) << sub.astype(np.uint8)).astype(np.uint8)
        allk = np.concatenate([self.key, key]); allo = np.concatenate([self.occ, occ])
        order = np.argsort(allk, kind="stable"); allk = allk[order]
        start = np.concatenate([[0], np.nonzero(np.diff(allk))[0] + 1]) if len(allk) else np.zeros(0, np.int64)
        newf = {}
        for k in self.FIELDS:
            v = np.concatenate([self.f[k], vals[k]])[order]
            newf[k] = np.add.reduceat(v, start) if len(v) else v
        self.occ = np.bitwise_or.reduceat(allo[order], start) if len(allo) else allo
        self.key = allk[start]; self.f = newf


def texture_alpha_mean(uri):
    return float(texture(uri)[..., 3].mean()) if uri else 1.0


# Cloud / fog layer textures (soft alpha-less cards seen in the Gateway review); never solid.
NON_SOLID_TEXTURES = {"8108F04A"}


def is_utility_mesh(glb: Glb, mi: int, ext) -> bool:
    """Untextured quads (blockers / water / fog planes) and cloud cards are not geometry."""
    prims = glb.primitives(mi)
    texs = [glb.material_texture(p[3]) for p in prims]
    if any(t and Path(t).stem in NON_SOLID_TEXTURES for t in texs):
        return True
    ntri = sum(len(p[2]) for p in prims)
    return all(t is None for t in texs) and ntri <= 4 and max(ext[0], ext[1]) > 20


def voxelize(glb: Glb, grid: Grid, core_lo, core_hi, vista_lo=None, vista_hi=None,
             vista_min=12.0, step=0.25, exclude=(), log=print):
    """Samples instance surfaces into grid voxels.  Core: every instance; vista: big instances only."""
    agg = Agg()
    sx, sy, sz = grid.size
    passes = [(np.array(core_lo), np.array(core_hi), step, None)]
    if vista_lo is not None:
        passes.append((np.array(vista_lo), np.array(vista_hi), step * 2, vista_min))
    for pi, (lo, hi, st, min_size) in enumerate(passes):
        insts = glb.instances_in(lo, hi)
        t0 = time.time(); total = 0
        for i in insts:
            ext = glb.inst_max[i] - glb.inst_min[i]
            if ext.max() > 3000:   # sky domes / horizon cards
                continue
            mi = glb.nodes[i]["mesh"]; name = glb.mesh_name(mi)
            if any(name.startswith(e) for e in exclude) or is_utility_mesh(glb, mi, ext):
                continue
            if min_size is not None and ext.max() < min_size:
                continue
            s = sample_instance(glb, i, lo, hi, st)
            if s is None:
                continue
            p, c, nz = s
            if min_size is not None:  # vista pass: keep only outside the core box
                inside = np.all((p >= core_lo) & (p <= core_hi), 1)
                p, c, nz = p[~inside], c[~inside], nz[~inside]
            if not len(p):
                continue
            f = grid.to_block(p)
            b = np.floor(f).astype(np.int64)
            ok = (b[:, 0] >= 0) & (b[:, 0] < sx) & (b[:, 1] >= 0) & (b[:, 1] < sy) & (b[:, 2] >= 0) & (b[:, 2] < sz)
            if not ok.any():
                continue
            b, f, c, nz = b[ok], f[ok], c[ok], nz[ok]
            sb = np.clip(np.floor((f - b) * 2).astype(np.int64), 0, 1)
            sub = sb[:, 0] | (sb[:, 1] << 1) | (sb[:, 2] << 2)
            terr = np.full(len(b), glb.is_terrain(mi))
            agg.add(grid.flat(b[:, 0], b[:, 1], b[:, 2]), sub, c[:, :3], terr, nz)
            total += len(b)
        agg.flush()
        log(f"  pass {pi}: {len(insts)} instances, {total} samples, {len(agg.key)} voxels, {time.time() - t0:.1f}s")
    return agg


# --------------------------------------------------------------------------------------------
# Classification and block shaping
# --------------------------------------------------------------------------------------------

class Palette:
    def __init__(self):
        self.states = ["minecraft:air"]
        self.index = {"minecraft:air": 0}
        self.entries = []
        for name, tex, fam, slab, terr in PALETTE_DEF:
            rgb = jar_texture_rgb(tex)
            self.entries.append(dict(name=name, rgb=rgb, lab=srgb_to_lab(rgb), family=fam, slab=slab, terrain=terr,
                                     pid=self.id("minecraft:" + name)))
        self.lab = np.stack([e["lab"] for e in self.entries])
        self.fam = np.array([e["family"] for e in self.entries])
        self.terr_ok = np.array([e["terrain"] for e in self.entries])
        self.ground = np.array([e["family"] in ("ground",) for e in self.entries])

    def id(self, state: str) -> int:
        if state not in self.index:
            self.index[state] = len(self.states); self.states.append(state)
        return self.index[state]

    def entry_of(self, pid):
        for e in self.entries:
            if e["pid"] == pid:
                return e
        return None


def classify(agg: Agg, pal: Palette, chunk=400_000):
    """Nearest curated block per voxel (Lab), with terrain / structure gating."""
    cnt = agg.f["cnt"]
    rgb = np.stack([agg.f["r"], agg.f["g"], agg.f["b"]], 1) / cnt[:, None]
    # Source base colours are albedo under no lighting; gently lift contrast/saturation for blocks.
    terr = agg.f["terr"] / cnt > 0.5
    # Gentle saturation lift only for clearly coloured surfaces (rust, paint); greys stay neutral.
    lum = rgb.mean(1, keepdims=True)
    lab0 = srgb_to_lab(rgb); chroma = np.hypot(lab0[:, 1], lab0[:, 2])
    boost = 1.0 + np.where(terr, 0.0, 0.25) * np.clip((chroma - 10) / 20, 0, 1)
    rgb = np.clip(lum + (rgb - lum) * boost[:, None], 0, 1)
    out = np.empty(len(cnt), np.int64)
    w = np.array([1.0, 1.25, 1.25])
    for c0 in range(0, len(cnt), chunk):
        lab = srgb_to_lab(rgb[c0:c0 + chunk])
        d = (((lab[:, None, :] - pal.lab[None, :, :]) * w) ** 2).sum(-1)
        t = terr[c0:c0 + chunk]
        d[t[:, None] & ~pal.terr_ok[None, :]] += 1e6          # terrain: natural blocks only
        d[(~t)[:, None] & pal.ground[None, :]] += 400.0       # structures: avoid dirt/moss unless very close
        d[(~t)[:, None] & (pal.fam == "snow")[None, :]] += 80.0  # painted metal is not snow
        out[c0:c0 + chunk] = np.argmin(d, 1)
    return out, terr, rgb


def neighbours26():
    return [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dy, dz) != (0, 0, 0)]


def majority_smooth(grid: Grid, keys, labels, iterations=1, min_votes=10):
    """Removes speckle: a voxel adopts the dominant neighbour label when clearly outvoted."""
    sx, sy, sz = grid.size
    order = np.argsort(keys); keys_s = keys[order]
    labels = labels.copy()
    x = keys % sx; z = (keys // sx) % sz; y = keys // (sx * sz)
    for _ in range(iterations):
        lab_s = labels[order]
        votes = np.full((len(keys), 26), -1, np.int64)
        for k, (dx, dy, dz) in enumerate(neighbours26()):
            nx, ny, nz = x + dx, y + dy, z + dz
            ok = (nx >= 0) & (nx < sx) & (ny >= 0) & (ny < sy) & (nz >= 0) & (nz < sz)
            nk = grid.flat(nx.clip(0, sx - 1), ny.clip(0, sy - 1), nz.clip(0, sz - 1))
            pos = np.searchsorted(keys_s, nk).clip(0, len(keys_s) - 1)
            hit = ok & (keys_s[pos] == nk)
            votes[hit, k] = lab_s[pos[hit]]
        vs = np.sort(votes, 1)
        # mode per row
        best = labels.copy(); bestc = np.zeros(len(keys), np.int64)
        run = np.ones(len(keys), np.int64)
        for k in range(1, 26):
            same = (vs[:, k] == vs[:, k - 1]) & (vs[:, k] >= 0)
            run = np.where(same, run + 1, 1)
            upd = (vs[:, k] >= 0) & (run > bestc)
            bestc = np.where(upd, run, bestc); best = np.where(upd, vs[:, k], best)
        own = (votes == labels[:, None]).sum(1)
        change = (bestc >= min_votes) & (own <= 3) & (best != labels)
        labels = np.where(change, best, labels)
    return labels


TERRAIN_DEPTH = 3   # solid ground below every terrain surface voxel (collision + no see-through)
TOP_SUBS = 0xCC   # sub-cells with local y >= 0.5
BOT_SUBS = 0x33
X1_SUBS, X0_SUBS = 0xAA, 0x55
Z1_SUBS, Z0_SUBS = 0xF0, 0x0F


def shape_blocks(grid: Grid, agg: Agg, labels, terr, pal: Palette, log=print):
    """Dense block-state array (y, z, x) from classified voxels: terrain fill, slabs, rails, chains."""
    sx, sy, sz = grid.size
    key = agg.key
    state = np.zeros((sy, sz, sx), np.int32)
    occ = np.zeros((sy, sz, sx), np.uint8)
    cnt = agg.f["cnt"]
    upf = agg.f["up"] / cnt; downf = agg.f["down"] / cnt; vertf = agg.f["vert"] / cnt
    pid = np.array([pal.entries[l]["pid"] for l in range(len(pal.entries))])[labels]
    y = key // (sx * sz); z = (key // sx) % sz; x = key % sx
    state[y, z, x] = pid; occ[y, z, x] = agg.occ
    tdense = np.zeros((sy, sz, sx), bool); tdense[y, z, x] = terr
    up = np.zeros((sy, sz, sx), np.float32); up[y, z, x] = upf
    hor = np.zeros((sy, sz, sx), np.float32); hor[y, z, x] = upf + downf
    vert = np.zeros((sy, sz, sx), np.float32); vert[y, z, x] = vertf
    solid0 = state > 0

    # 1. Terrain is a closed ground: fill down from each terrain surface until other geometry.
    filling = np.zeros((sz, sx), bool); depth = np.zeros((sz, sx), np.int32); carry = np.zeros((sz, sx), np.int32)
    filled = 0
    for yy in range(sy - 1, -1, -1):
        cur = state[yy]; t = tdense[yy]
        start = t & (cur > 0)
        stop = (cur > 0) & ~t
        empty = cur == 0
        f = filling & empty
        if f.any():
            cur[f] = carry[f]; filled += int(f.sum())
            depth[f] += 1
        carry = np.where(start, cur, carry); depth = np.where(start, 0, depth)
        filling = ((filling & ~stop) | start) & (depth < TERRAIN_DEPTH)
    log(f"  terrain fill: {filled} blocks")

    solid = state > 0
    above = np.zeros_like(solid); above[:-1] = solid[1:]
    below = np.zeros_like(solid); below[1:] = solid[:-1]
    slab_of = {e["pid"]: e["slab"] for e in pal.entries}
    # 2. Half-height surfaces -> slabs (gives walkable half steps on ramps and stairs).
    bottom_only = solid0 & ((occ & TOP_SUBS) == 0) & ~above & (up > 0.4) & ~tdense
    top_only = solid0 & ((occ & BOT_SUBS) == 0) & ~below & (hor > 0.5)
    nb = nt = 0
    for spid, slab in slab_of.items():
        if not slab:
            continue
        m = bottom_only & (state == spid)
        if m.any():
            st = "minecraft:" + slab if "[" in slab else f"minecraft:{slab}[type=bottom]"
            state[m] = pal.id(st); nb += int(m.sum())
        if slab.startswith("snow"):
            continue
        m = top_only & (state == spid)
        if m.any():
            state[m] = pal.id(f"minecraft:{slab}[type=top]"); nt += int(m.sum())
    # 3a. Poles (thin in both horizontal axes, e.g. street lights / stanchions): one wall post column.
    thinx1 = (occ & X0_SUBS) == 0; thinx0 = (occ & X1_SUBS) == 0
    thinz1 = (occ & Z0_SUBS) == 0; thinz0 = (occ & Z1_SUBS) == 0
    pole = solid0 & ~tdense & (vert > 0.5) & (thinx1 | thinx0) & (thinz1 | thinz0)
    def nshift(a, dx=0, dz=0):
        o = np.zeros_like(a)
        o[:, max(-dz, 0):sz - max(dz, 0), max(-dx, 0):sx - max(dx, 0)] = a[:, max(dz, 0):sz + min(dz, 0) or None, max(dx, 0):sx + min(dx, 0) or None]
        return o
    drop = pole & ((thinx1 & nshift(pole & thinx0, dx=1)) | (thinz1 & nshift(pole & thinz0, dz=1)))
    state[drop] = 0; solid0 = solid0 & ~drop
    pole &= ~drop
    vstack = np.zeros_like(pole); vstack[1:] |= pole[:-1]; vstack[:-1] |= pole[1:]
    pole &= vstack
    other = solid0 & ~pole
    pole &= ~(nshift(other, dx=1) | nshift(other, dx=-1) | nshift(other, dz=1) | nshift(other, dz=-1))
    fam0 = {e["pid"]: e["family"] for e in pal.entries}
    wall_for = {"rust": "mud_brick_wall", "teal": "prismarine_wall", "concrete": "andesite_wall", "rock": "andesite_wall",
                "paint": "mud_brick_wall", "snow": "diorite_wall", "ground": "mud_brick_wall"}
    npole = 0
    for spid, famname in fam0.items():
        m = pole & (state == spid)
        if m.any():
            w = wall_for.get(famname, "polished_deepslate_wall")
            state[m] = pal.id(f"minecraft:{w}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
            npole += int(m.sum())
    log(f"  poles: {npole} (deduplicated {int(drop.sum())})")
    # 3b. Thin uprights standing on a floor: railings -> iron bars; isolated vertical lines -> chains.
    thin = solid0 & ~tdense & ~pole & (vert > 0.6) & ((((occ & X1_SUBS) == 0) | ((occ & X0_SUBS) == 0))
                                            | (((occ & Z1_SUBS) == 0) | ((occ & Z0_SUBS) == 0)))
    solid = state > 0
    def sh(a, dy=0, dz=0, dx=0):
        o = np.zeros_like(a)
        ys = slice(max(dy, 0), sy + min(dy, 0)); yd = slice(max(-dy, 0), sy + min(-dy, 0))
        zs = slice(max(dz, 0), sz + min(dz, 0)); zd = slice(max(-dz, 0), sz + min(-dz, 0))
        xs = slice(max(dx, 0), sx + min(dx, 0)); xd = slice(max(-dx, 0), sx + min(-dx, 0))
        o[yd, zd, xd] = a[ys, zs, xs]
        return o
    floor1 = sh(solid & ~thin, dy=-1); floor2 = sh(solid & ~thin, dy=-2)
    rail = (thin & (floor1 | (sh(thin, dy=-1) & floor2)) & ~sh(solid & ~thin, dy=1)
            & ~(sh(thin, dy=1) & sh(thin, dy=2)))
    horiz_n = sum(sh(solid, dz=a, dx=b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    chain = solid0 & ~pole & ~tdense & (horiz_n == 0) & (sh(solid, dy=1) | sh(solid, dy=-1)) & (vert > 0.5) & ~rail
    fam = {e["pid"]: e["family"] for e in pal.entries}
    railable = np.isin(state, [p for p, f in fam.items() if f in ("metal", "dark", "rust", "teal", "concrete", "paint")])
    rail &= railable
    thin_both = (thinx1 | thinx0) & (thinz1 | thinz0)
    post = chain & ~thin_both
    chain &= thin_both
    state[chain] = pal.id("minecraft:iron_chain[axis=y]")
    for spid, famname in fam0.items():
        m = post & (state == spid)
        if m.any():
            w = wall_for.get(famname, "polished_deepslate_wall")
            state[m] = pal.id(f"minecraft:{w}[east=none,north=none,south=none,up=true,waterlogged=false,west=none]")
    bars = rail.copy()
    full = (state > 0) & ~bars
    n = 0
    east = sh(bars | full, dx=1); west = sh(bars | full, dx=-1)
    south = sh(bars | full, dz=1); north = sh(bars | full, dz=-1)
    code = (east.astype(np.int32) << 3) | (west.astype(np.int32) << 2) | (south.astype(np.int32) << 1) | north.astype(np.int32)
    for c in range(16):
        m = bars & (code == c)
        if not m.any():
            continue
        e, w, s_, nn = bool(c & 8), bool(c & 4), bool(c & 2), bool(c & 1)
        st = f"minecraft:iron_bars[east={str(e).lower()},north={str(nn).lower()},south={str(s_).lower()},west={str(w).lower()}]"
        state[m] = pal.id(st); n += int(m.sum())
    log(f"  slabs bottom={nb} top={nt} bars={n} chains={int(chain.sum())} posts={int(post.sum())}")
    return state


# --------------------------------------------------------------------------------------------
# .zone format v1 (gzip):  "DGZONE01" | int sx, sy, sz | u16 palette n | n x (u16 len, utf8 state)
#                           | int runs | runs x (varint palette index, varint length)
# Linear order: index = (y * sz + z) * sx + x.  Palette index 0 is always minecraft:air.
# --------------------------------------------------------------------------------------------

def _varint(v: int, out: bytearray):
    while True:
        b = v & 0x7F; v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b); return


def write_zone(path: Path, state: np.ndarray, states: list[str]) -> dict:
    sy, sz, sx = state.shape
    used = np.unique(state)
    if used[0] != 0:
        used = np.concatenate([[0], used])
    remap = np.zeros(max(len(states), int(state.max()) + 1), np.int32); remap[used] = np.arange(len(used))
    flat = remap[state.reshape(-1)]
    pal = [states[u] for u in used]
    change = np.nonzero(np.diff(flat))[0] + 1
    starts = np.concatenate([[0], change]); lengths = np.diff(np.concatenate([starts, [len(flat)]]))
    vals = flat[starts]
    body = bytearray()
    body += b"DGZONE01" + struct.pack(">iii", sx, sy, sz) + struct.pack(">H", len(pal))
    for st in pal:
        b = st.encode(); body += struct.pack(">H", len(b)) + b
    body += struct.pack(">i", len(vals))
    for v, l in zip(vals.tolist(), lengths.tolist()):
        _varint(v, body); _varint(l, body)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = gzip.compress(bytes(body), 9, mtime=0)
    path.write_bytes(raw)
    return dict(size=[sx, sy, sz], palette=len(pal), runs=int(len(vals)), blocks=int((flat != 0).sum()), bytes=len(raw))


def read_zone(path: Path):
    data = gzip.decompress(path.read_bytes())
    assert data[:8] == b"DGZONE01"
    sx, sy, sz = struct.unpack(">iii", data[8:20]); n, = struct.unpack(">H", data[20:22]); pos = 22
    pal = []
    for _ in range(n):
        l, = struct.unpack(">H", data[pos:pos + 2]); pal.append(data[pos + 2:pos + 2 + l].decode()); pos += 2 + l
    runs, = struct.unpack(">i", data[pos:pos + 4]); pos += 4
    out = np.zeros(sx * sy * sz, np.int32); i = 0
    for _ in range(runs):
        vals = []
        for _k in range(2):
            v = shift = 0
            while True:
                b = data[pos]; pos += 1; v |= (b & 0x7F) << shift; shift += 7
                if not b & 0x80:
                    break
            vals.append(v)
        out[i:i + vals[1]] = vals[0]; i += vals[1]
    assert i == len(out)
    return out.reshape(sy, sz, sx), pal


# --------------------------------------------------------------------------------------------
# Review renders of the voxel result
# --------------------------------------------------------------------------------------------

_STATE_RGB: dict[str, np.ndarray] = {}
_TEX_ALIASES = {"podzol": "podzol_top", "snow": "snow", "iron_chain": "iron_chain", "ochre_froglight": "ochre_froglight_side",
                "lantern": "lantern", "sea_lantern": "sea_lantern", "shroomlight": "shroomlight",
                "light": None, "barrier": None}


def state_rgb(st: str) -> np.ndarray:
    if st in _STATE_RGB:
        return _STATE_RGB[st]
    name = st.split(":")[1].split("[")[0]
    rgb = np.array([0.0, 0.0, 0.0])
    if name != "air" and _TEX_ALIASES.get(name, 1) is not None:
        cands = [_TEX_ALIASES.get(name, name)]
        base = name[6:] if name.startswith("waxed_") else name
        cands.append(base)
        for suf in ("_slab", "_stairs", "_wall"):
            if base.endswith(suf):
                b = base[:-len(suf)]; cands += [b, b + "s", b.replace("brick", "bricks"), b.replace("tile", "tiles")]
        if name.endswith("_bulb"):
            cands.append(base + ("_lit" if "lit=true" in st else ""))
        for c in cands:
            try:
                rgb = jar_texture_rgb(c); break
            except KeyError:
                continue
    _STATE_RGB[st] = rgb
    return rgb


def _visible_ids(states):
    return np.array([not (s.startswith("minecraft:barrier") or s.startswith("minecraft:light[") or s == "minecraft:air")
                     for s in states])


def render_top(state: np.ndarray, states: list[str], out: Path, ycut: int | None = None, marks=()):
    sy, sz, sx = state.shape
    vis = _visible_ids(states)
    state = np.where(vis[state], state, 0)
    st = state if ycut is None else state[:ycut]
    solid = st > 0
    top = np.where(solid.any(0), sy - 1 - np.argmax(solid[::-1], 0) if ycut is None
                   else st.shape[0] - 1 - np.argmax(solid[::-1], 0), -1)
    lut = np.stack([state_rgb(s) for s in states])
    idx = np.take_along_axis(st, np.clip(top, 0, None)[None], 0)[0]
    img = lut[idx]
    hmin, hmax = np.percentile(top[top >= 0], [2, 98]) if (top >= 0).any() else (0, 1)
    shade = np.clip((top - hmin) / max(hmax - hmin, 1), 0, 1)
    # simple hillshade from height differences
    gx = np.zeros_like(top, float); gx[:, 1:] = top[:, 1:] - top[:, :-1]
    img = img * (0.55 + 0.45 * shade[..., None]) * np.clip(1 + 0.08 * gx[..., None], 0.7, 1.2)
    img[top < 0] = (0.04, 0.0, 0.07)
    img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    for (mx, mz, colr) in marks:
        if 0 <= mx < sx and 0 <= mz < sz:
            img[max(mz - 1, 0):mz + 2, max(mx - 1, 0):mx + 2] = colr
    png_write(out, np.repeat(np.repeat(img, 2, 0), 2, 1))


def render_view(state: np.ndarray, states: list[str], out: Path, eye, yaw_deg, pitch_deg=0.0,
                w=480, h=270, fov=75.0, max_dist=400.0, light=None):
    """Software ray-march of the block grid from an eye (block coords, y up). yaw 0 = +z (south)."""
    sy, sz, sx = state.shape
    lut = np.stack([state_rgb(s) for s in states])
    vis = _visible_ids(states)
    state = np.where(vis[state], state, 0)
    yaw = math.radians(yaw_deg); pitch = math.radians(pitch_deg)
    fwd = np.array([-math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch)])
    right = np.array([math.cos(yaw), 0, math.sin(yaw)]) * -1
    up = np.cross(right, fwd)
    t = math.tan(math.radians(fov) / 2)
    u = (np.arange(w) + 0.5) / w * 2 - 1; v = 1 - (np.arange(h) + 0.5) / h * 2
    uu, vv = np.meshgrid(u * t * w / h, v * t)
    d = fwd[None, None] + uu[..., None] * right[None, None] + vv[..., None] * up[None, None]
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    d = d.reshape(-1, 3)
    n = len(d)
    o = np.array(eye, float)
    cell = np.repeat(np.floor(o).astype(np.int64)[None], n, 0)
    stp = np.where(d >= 0, 1, -1).astype(np.int64)
    inv = 1.0 / np.where(np.abs(d) < 1e-9, 1e-9, d)
    nxt = cell + (stp > 0)
    tmax = (nxt - o[None]) * inv
    tdel = np.abs(inv)
    col = np.zeros((n, 3)); hit = np.zeros(n, bool); axis = np.zeros(n, np.int64); tcur = np.zeros(n)
    alive = np.arange(n)
    dims = np.array([sx, sy, sz])
    for _ in range(int(max_dist * 1.8)):
        if not len(alive):
            break
        c = cell[alive]
        inb = np.all((c >= 0) & (c < dims), 1)
        sv = np.zeros(len(alive), np.int64)
        sv[inb] = state[c[inb, 1], c[inb, 2], c[inb, 0]]
        hm = sv > 0
        if hm.any():
            j = alive[hm]
            shade = np.where(axis[j] == 1, np.where(d[j, 1] < 0, 1.0, 0.55), np.where(axis[j] == 0, 0.8, 0.68))
            fog = np.exp(-tcur[j] / 220.0)[:, None]
            hp = o[None] + d[j] * tcur[j][:, None]
            fr = hp - np.floor(hp)
            fr = np.where(np.arange(3)[None] == axis[j][:, None], 0.5, fr)
            edge = np.min(np.minimum(fr, 1 - fr), 1)
            shade = shade * np.where(edge < 0.04, 0.78, 1.0)
            c0 = lut[sv[hm]] * shade[:, None]
            if light is not None:   # vanilla lightmap curve on the cell in front of the hit face
                pc = cell[j].copy(); pc[np.arange(len(j)), axis[j]] -= stp[j, axis[j]]
                pc = np.clip(pc, 0, dims - 1)
                lv = light[pc[:, 1], pc[:, 2], pc[:, 0]].astype(np.float64) / 15.0
                c0 = c0 * np.maximum(lv / (4.0 - 3.0 * lv), 0.02)[:, None]
                fog = np.ones_like(fog)
            col[j] = c0 * fog + np.array([0.55, 0.6, 0.66]) * (1 - fog)
            hit[j] = True
        far = tcur[alive] > max_dist
        alive = alive[~hm & ~far]
        if not len(alive):
            break
        tm = tmax[alive]
        ax = np.argmin(tm, 1)
        r = np.arange(len(alive))
        tcur[alive] = tm[r, ax]
        cell[alive, ax] += stp[alive, ax]
        tmax[alive, ax] += tdel[alive, ax]
        axis[alive] = ax
    sky = np.array([0.55, 0.6, 0.66])
    col[~hit] = sky
    img = (np.clip(col.reshape(h, w, 3), 0, 1) * 255).astype(np.uint8)
    png_write(out, img)


def source_anchors(bubble: str | None = None):
    """(name, kind, phase, source xyz, yaw_deg) from actors.csv and activity_data props."""
    import csv
    out = []
    with open(SRC / "actors.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if bubble and r["bubble"] != bubble:
                continue
            out.append((r["entityName"].strip(), "actor", r["phase"],
                        (float(r["x"]), float(r["y"]), float(r["z"])), None))
    act = json.loads((SRC / "activity_data/80C87171.json").read_text())
    for e in act["entries"]:
        if bubble and e["bubble"] != bubble:
            continue
        t = e["transform"]["Translation"]; q = e["transform"]["Rotation"]
        yaw = math.degrees(math.atan2(2 * (q["W"] * q["Z"] + q["X"] * q["Y"]), 1 - 2 * (q["Y"] ** 2 + q["Z"] ** 2)))
        out.append((e["name"], "prop", e["phase"], (t["X"], t["Y"], t["Z"]), yaw))
    return out


ANCHOR_COLOURS = {"fallen_dreg": (255, 60, 60), "fallen_vandal": (255, 140, 0), "fallen_captain": (255, 0, 255),
                  "fallen_slag": (200, 0, 0), "Shank": (255, 255, 0), "Ghost": (0, 255, 255),
                  "Walker": (255, 255, 255), "Skiff": (180, 180, 255)}


# --------------------------------------------------------------------------------------------
# Zone definitions (crop choices documented in docs/design/guardian-rises/map-pipeline.md)
# --------------------------------------------------------------------------------------------

SCALE = 1.0

ZONES = {
    "gateway": dict(glb="gateway", bubble="Gateway", start=(345, -990, 6),
                    core=((285, -1065, -40), (425, -770, 92)),
                    vista=((150, -1150, -60), (600, -700, 130)),
                    views=[("wake", (342, -1000, 6), 180, -5), ("cars", (340, -930, 5), 180, 0),
                           ("gate", (340, -850, 3), 180, -10), ("tunnel", (338, -800, -3), 180, 0),
                           ("overview", (345, -1120, 60), 180, 20, "free")]),
    "breach": dict(glb="the_breach", bubble="The Breach", start=(390.5, -786.6, 17.4),
                   core=((335, -845, -6), (565, -645, 40)),
                   views=[("start", (390.5, -786.6, 17.4), -90, 5), ("weapon", (412, -793.7, 17.7), -90, 5),
                          ("arena", (465, -800, 17.3), -90, 0), ("chest", (520, -737.7, 16.5), -90, 5),
                          ("corridor", (508, -722, 14.0), 90, 0), ("garage", (440, -705, 9.0), 90, 5),
                          ("overview", (465, -560, 70), 0, 35, "free")]),
    "divide": dict(glb="the_divide", bubble="The Divide", start=(398, -676, 10),
                   core=((95, -705, -20), (450, -470, 70)),
                   vista=((-50, -850, -40), (600, -350, 160)),
                   views=[("enter", (400, -640, 10), 90, 0), ("courtyard", (240, -590, 6), 90, 0),
                          ("hangar_gate", (150, -545, 6), 90, 0),
                          ("overview", (270, -760, 80), 180, 30, "free")]),
    "dock13": dict(glb="dock_13", bubble="Dock 13", start=(118, -538, 6),
                   core=((20, -680, -15), (190, -480, 60)),
                   vista=((-100, -800, -40), (350, -350, 150)),
                   views=[("gate", (115, -540, 6), 135, 0), ("hangar", (85, -570, 6), 135, 0),
                          ("overview", (105, -700, 70), 180, 35, "free")]),
}


# --------------------------------------------------------------------------------------------
# Walkability analysis (Minecraft player: 0.6 wide, 1.8 tall, step 0.6, jump ~1.25)
# --------------------------------------------------------------------------------------------

def passable_mask(state, states):
    """True where a player can occupy the cell (air, light, chains are NOT passable)."""
    names = np.array([s.split(":")[1].split("[")[0] for s in states])
    open_ids = np.nonzero(np.isin(names, ["air", "light", "snow"]) )[0]
    pas = np.isin(state, open_ids)
    # snow[layers=4] is half height: treat as solid ground for support, passable above.
    return pas


def standable(state, states):
    """Feet cells: passable cell + passable head cell + supporting block below (y,z,x bool)."""
    pas = passable_mask(state, states)
    names = [s for s in states]
    sup = ~pas | np.isin(state, [i for i, s in enumerate(names) if s.startswith("minecraft:snow[")])
    st = np.zeros_like(pas)
    st[1:-1] = pas[1:-1] & pas[2:] & sup[:-2] & ~np.isin(state[1:-1], [i for i, s in enumerate(names) if s.startswith("minecraft:snow[")])
    return st


def nearest_standable(stand, p, radius=6):
    """Nearest standable cell to block-space point p (x, y, z) within radius, preferring the same height."""
    sy, sz, sx = stand.shape
    x0, y0, z0 = (int(math.floor(v)) for v in p)
    best, bd = None, 1e9
    for y in range(max(1, y0 - radius), min(sy - 1, y0 + radius + 1)):
        for z in range(max(0, z0 - radius), min(sz, z0 + radius + 1)):
            row = stand[y, z, max(0, x0 - radius):min(sx, x0 + radius + 1)]
            for xi in np.nonzero(row)[0]:
                x = xi + max(0, x0 - radius)
                d = (x + 0.5 - p[0]) ** 2 + (z + 0.5 - p[2]) ** 2 + 2.0 * (y - p[1]) ** 2
                if d < bd:
                    bd, best = d, (x, y, z)
    return best


def reach(stand, pas, start, max_down=12, region=None):
    """Breadth-first walk over feet cells: 4-neighbour steps, step/jump up 1 block, falls <= max_down."""
    from collections import deque
    sy, sz, sx = stand.shape
    seen = np.zeros_like(stand); q = deque()
    if start is None:
        return seen
    seen[start[1], start[2], start[0]] = True; q.append(start)
    while q:
        x, y, z = q.popleft()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            if not (0 <= nx < sx and 0 <= nz < sz):
                continue
            if region is not None and not (region[0] <= nx < region[1] and region[2] <= nz < region[3]):
                continue
            land = None
            if y + 2 < sy and stand[y + 1, nz, nx] and pas[y + 2, z, x]:
                land = (nx, y + 1, nz)
            elif pas[y, nz, nx] and pas[y + 1, nz, nx]:
                ny = y
                while ny > 1 and pas[ny - 1, nz, nx] and y - ny < max_down:
                    ny -= 1
                if stand[ny, nz, nx]:
                    land = (nx, ny, nz)
            if land and not seen[land[1], land[2], land[0]]:
                seen[land[1], land[2], land[0]] = True; q.append(land)
    return seen


def analyze_zone(name: str, start_src=None, log=print):
    spec = ZONES[name]
    lo, hi = spec.get("vista", spec["core"]); grid = Grid(lo, hi, SCALE)
    state = np.load(CACHE_DIR / f"state_{name}.npy"); states = json.loads((CACHE_DIR / f"states_{name}.json").read_text())
    pas = passable_mask(state, states); stand = standable(state, states)
    anchors = [a for a in source_anchors(spec["bubble"])]
    start_src = start_src or spec.get("start")
    start = nearest_standable(stand, grid.to_block(np.array(start_src)), 8) if start_src else None
    seen = reach(stand, pas, start, region=core_region(name, grid))
    log(f"[{name}] standable={int(stand.sum())} reachable={int(seen.sum())} start={start}")
    rows = []
    for n, k, ph, p, yaw in anchors:
        b = grid.to_block(np.array(p))
        c = nearest_standable(stand, b, 6)
        ok = c is not None and seen[c[1], c[2], c[0]]
        rows.append((n, k, p, b.round(1).tolist(), c, ok))
        log(f"   {n:24s} {k:5s} src={tuple(round(v, 1) for v in p)} blk={b.round(1).tolist()} stand={c} reach={ok}")
    # review image: top-down, reachable floor = green tint, other floor = blue tint
    sy, sz, sx = state.shape
    lut = np.stack([state_rgb(s_) for s_ in states])
    any_st = stand.any(0)
    top_st = np.where(any_st, sy - 1 - np.argmax(stand[::-1], 0), 0)
    reach2d = np.take_along_axis(seen, top_st[None], 0)[0] & any_st
    floor_col = lut[np.take_along_axis(state, np.clip(top_st - 1, 0, None)[None], 0)[0]]
    hmin, hmax = (top_st[any_st].min(), top_st[any_st].max()) if any_st.any() else (0, 1)
    shade = 0.45 + 0.55 * (top_st - hmin) / max(hmax - hmin, 1)
    img = floor_col * shade[..., None]
    img = np.where(reach2d[..., None], img * 0.6 + np.array([0.1, 0.9, 0.2]) * 0.4,
                   np.where(any_st[..., None], img * 0.6 + np.array([0.2, 0.3, 1.0]) * 0.4, np.array([0.03, 0, 0.06])))
    img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    for n, k, p, b, c, ok in rows:
        x, z = int(b[0]), int(b[2])
        if 0 <= x < sx and 0 <= z < sz:
            img[max(z - 1, 0):z + 2, max(x - 1, 0):x + 2] = (255, 255, 255) if ok else (255, 0, 0)
    if start:
        img[max(start[2] - 2, 0):start[2] + 3, max(start[0] - 2, 0):start[0] + 3] = (255, 255, 0)
    png_write(EVIDENCE / "renders" / f"{name}_walk.png", np.repeat(np.repeat(img, 3, 0), 3, 1))
    return grid, state, states, stand, seen, rows


def view_cam(spec, view, name=None):
    """(src eye xyz, yaw, pitch) of a review camera.  Ground views snap to the nearest standable
    voxel cell (eye 1.62 above feet) so source and voxel renders share a valid player eye."""
    eye = np.array(view[1], float); yaw = float(view[2]); pitch = float(view[3]) if len(view) > 3 else 0.0
    if len(view) > 4 and view[4] == "free":
        return eye, yaw, pitch
    lo, hi = spec.get("vista", spec["core"]); grid = Grid(lo, hi, SCALE)
    sp = CACHE_DIR / f"state_{name}.npy"
    if name and sp.exists():
        state = np.load(sp); states = json.loads((CACHE_DIR / f"states_{name}.json").read_text())
        c = nearest_standable(standable(state, states), grid.to_block(eye), 6)
        if c is not None:
            eye = grid.src_of_block(np.array([c[0] + 0.5, c[1] + 1.62, c[2] + 0.5]))
    return eye, yaw, pitch


def render_source_views(name: str):
    """Blender (bpy) render of the source GLB crop from the zone review cameras."""
    import bpy  # type: ignore
    spec = ZONES[name]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SRC / "maps_glb" / f"{spec['glb']}.textured.glb"))
    lo, hi = spec.get("vista", spec["core"])
    lo = np.array(lo) - 2; hi = np.array(hi) + 2
    for ob in list(bpy.data.objects):
        if ob.type != "MESH":
            continue
        bb = np.array([ob.matrix_world @ __import__("mathutils").Vector(c) for c in ob.bound_box])
        if np.any(bb.max(0) < lo) or np.any(bb.min(0) > hi) or np.ptp(bb, 0).max() > 3000:
            bpy.data.objects.remove(ob, do_unlink=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_shadows = False
    sc.render.resolution_x, sc.render.resolution_y = 480, 270
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.3, 0.33, 0.38)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.sensor_fit = "VERTICAL"; cam.data.angle = math.radians(70); cam.data.clip_end = 4000
    for view in spec.get("views", []):
        eye, yaw, pitch = view_cam(spec, view, name)
        cam.location = tuple(eye)
        cam.rotation_euler = (math.radians(90 - pitch), 0, math.radians(180 - yaw))
        sc.render.filepath = str(EVIDENCE / "renders" / f"{name}_{view[0]}_src.png")
        bpy.ops.render.render(write_still=True)


def render_voxel_views(name: str, grid: Grid, state, states):
    for view in ZONES[name].get("views", []):
        eye, yaw, pitch = view_cam(ZONES[name], view, name)
        b = grid.to_block(eye)
        render_view(state, states, EVIDENCE / "renders" / f"{name}_{view[0]}_vox.png", b, yaw, pitch, fov=70)


def write_markers(name, grid: Grid, markers, prov):
    path = OUT_DIR / "markers.json"
    doc = json.loads(path.read_text()) if path.exists() else {}
    doc.setdefault("schema", 1)
    doc["coordinates"] = ("zone-local block coordinates (feet position; x/z cell centre). World = origin + pos. "
                          "Yaw: Minecraft degrees (0 = +Z/south, -90 = +X/east).")
    doc.setdefault("zones", {})
    sx, sy, sz = grid.size
    doc["zones"][name] = dict(
        size=[sx, sy, sz], scale=SCALE,
        source=dict(glb=f"maps_glb/{ZONES[name]['glb']}.textured.glb",
                    box_zup=[list(map(float, ZONES[name].get("vista", ZONES[name]["core"])[0])),
                             list(map(float, ZONES[name].get("vista", ZONES[name]["core"])[1]))],
                    core_zup=[list(map(float, ZONES[name]["core"][0])), list(map(float, ZONES[name]["core"][1]))]),
        markers=sorted(markers, key=lambda m: m["id"]),
        provenance=[dict(id=i, note=w, source_zup=None if p is None else [round(float(v), 3) for v in p]) for i, w, p in prov])
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------------------------
# Gameplay markers.  Positions are authored in source coordinates (Z-up) and snapped to the voxel
# result.  "src" = extracted placement (actor-placements / activity_data); "authored" = W300 design
# choice derived from geometry review (no source data exists for it).
# --------------------------------------------------------------------------------------------

def actors(bubble, names=None, near=None, radius=1e9):
    out = []
    for n, k, ph, p, yaw in source_anchors(bubble):
        if k != "actor" or (names and n not in names):
            continue
        if near is not None and math.dist(p[:2], near[:2]) > radius:
            continue
        out.append(p)
    return out


def prop(bubble, name):
    for n, k, ph, p, yaw in source_anchors(bubble):
        if n == name:
            return p, yaw
    raise KeyError(name)


MARKER_SPECS = {
    "gateway": dict(
        points=[
            # id, src xyz, facing (src xy direction or yaw), tags, provenance
            ("spawn.player", (342, -1000, 6), (0, 1), {}, "authored: car-wreck field south end, facing the Wall"),
            ("checkpoint.wake", (342, -1000, 6), (0, 1), {}, "authored: fall-recovery point"),
            ("trigger.wall_entrance", (340, -838, 2), (0, 1), {"radius": "6", "height": "5"},
             "authored: gate opening in the Wall at the head of the car jam"),
            ("exit.breach", (338, -806, -3), (0, 1), {"radius": "3", "height": "4"},
             "authored: end of the walkable gate tunnel under the Wall -> Breach spawn"),
        ],
        ghost=dict(distance=1.9, height=1.45),
        lights=[("light.gate_warm", (340, -826, 2), True, "always", "authored: warm practical light marking the way in")],
    ),
    "breach": dict(
        points=[
            ("spawn.player", (390.5, -786.6, 17.4), (1, 0), {}, "src: Ghost placement (enc_launchpad_breach_catwalks) start of the Breach"),
            ("ghost.scan", None, None, {}, "authored: Ghost 'nux' light-up hover point in front of the player"),
            ("trigger.breach_dark", (392, -788, 17.4), (1, 0), {"radius": "4", "height": "4"}, "authored: dark entry (pflg_breach_lightup / ho_ghostlight)"),
            ("trigger.rifle", "prop:o_weapon_interact", None, {"radius": "2.5", "height": "3"}, "src: o_weapon_interact"),
            ("prop.rifle", "prop:o_weapon", None, {"free": "true"}, "src: o_weapon transform"),
            ("checkpoint.arm_yourself", (408, -793.7, 17.7), (1, 0), {}, "authored: beside the rifle crate"),
            ("trigger.cache", "prop:o_chest_weapon", None, {"radius": "2.5", "height": "3"}, "src: o_chest_weapon"),
            ("prop.shotgun_cache", "prop:o_chest_weapon", None, {"free": "true"}, "src: o_chest_weapon transform"),
            ("trigger.breach_exit", (398, -676, 11), (-1, 0), {"radius": "4", "height": "4"},
             "authored: trench north of the garage (Breach->Divide hand-off)"),
            ("exit.divide", (398, -676, 11), (-1, 0), {"radius": "4", "height": "4"}, "authored: same hand-off point"),
        ],
        encounters=[
            # name, order, source names/area, composition, provenance
            ("breach_first", 1, dict(near=(462, -801), radius=14), [("dreg", 3), ("vandal", 1)],
             "src area: dregs/slag/vandal at (452..490,-797..-806) z17"),
            ("breach_far", 2, dict(near=(532, -818), radius=8), [("dreg", 3)], "src area: dregs (532..533,-816..-820)"),
            ("breach_chest", 3, dict(near=(533, -744), radius=6), [("dreg", 2)], "src area: dreg (532.9,-744.0) by the cache"),
            ("breach_corridor", 4, dict(near=(487, -721), radius=24), [("dreg", 5), ("vandal", 1)],
             "src area: dropdown dregs (465..508,-715..-728) z14"),
            ("breach_garage", 5, dict(near=(410, -700), radius=26), [("captain", 1), ("vandal", 3), ("dreg", 4)],
             "src area: garage captain/vandals/dregs (395..428,-679..-718) z8-10"),
        ],
        lights=[
            # id, src xyz (floor point under the fixture), lit at build, phase
            ("light.start_emergency", (393, -789, 17.4), True, "always", "authored: faint emergency light at the wake point"),
            ("light.rifle", (410.6, -793.7, 17.7), False, "breach_lightup", "authored: lit when the Ghost lights the Breach"),
            ("light.arena_one", (465, -801, 17.3), False, "breach_lightup", "authored"),
            ("light.cache", (532, -740, 16.5), False, "breach_lightup", "authored"),
            ("light.corridor_west", (470, -721, 14.0), False, "breach_lightup", "authored"),
            ("light.corridor_east", (500, -723, 14.0), False, "breach_lightup", "authored"),
            ("light.garage", (415, -700, 9.0), False, "breach_lightup", "authored"),
            ("light.garage_exit", (400, -680, 9.5), False, "breach_lightup", "authored"),
        ],
    ),
    "divide": dict(
        points=[
            ("spawn.player", (398, -676, 11), (-1, 0), {}, "authored: trench (Breach hand-off)"),
            ("trigger.divide_enter", (345, -660, 10), (-1, 1), {"radius": "6", "height": "5"}, "authored: trench exit onto the open ground"),
            ("checkpoint.divide_walker", (320, -625, 8), (-1, 1), {}, "authored: edge of the Walker courtyard"),
            ("trigger.walker_arena", (240, -590, 6), (-1, 0), {"radius": "20", "height": "8"}, "authored: graveyard courtyard centre"),
            ("prop.heavy_cache", "prop:o_graveyard_chest", None, {"free": "true"}, "src: o_graveyard_chest (heavy ammo nux)"),
            ("prop.skiff_drop", (85.0, -577.0, 83.5), (1, 0), {"free": "true"}, "src: Skiff placement (Walker dropship)"),
            ("exit.dock13", (112, -537, 5.0), (-1, -1), {"radius": "3", "height": "4"}, "src: o_hangar_gating (hangar gate)"),
        ],
        encounters=[
            ("divide_lure", 1, dict(near=(240, -582), radius=40), [("dreg", 2), ("vandal", 3), ("shank", 3)],
             "src area: enc_launchpad_graveyard_public lure squads (205..275,-572..-597)"),
            ("divide_walker", 2, dict(near=(235, -590), radius=10), [("walker", 1)],
             "authored ground spot; src Walker placement (82,-577.5,84) is the skiff drop in the air"),
            ("divide_reinforce", 3, dict(near=(250, -600), radius=30), [("dreg", 3), ("vandal", 1)],
             "authored reinforcement wave (plan: Walker + 증원)"),
        ],
        lights=[],
    ),
    "dock13": dict(
        points=[
            ("spawn.player", (116, -537, 5.0), (-1, -1), {}, "authored: just inside the hangar gate (o_hangar_gating)"),
            ("trigger.dock_enter", (110, -543, 5.0), (-1, -1), {"radius": "4", "height": "4"}, "authored"),
            ("checkpoint.dock_13", (112, -540, 5.0), (-1, -1), {}, "authored"),
            ("prop.ship", (78.5, -567.0, 5.0), (1, 1), {"free": "true"}, "authored: ship under hangar_roof_broken_b (takeoff gap)"),
            ("trigger.ship", (88, -558, 5.0), (-1, -1), {"radius": "7", "height": "5"},
             "authored: ship approach (r5: radius 7 so the guidance route ends well inside it)"),
            ("exit.tower", (78.5, -567.0, 5.0), (1, 1), {"radius": "6", "height": "6"}, "authored: departure"),
        ],
        encounters=[
            ("dock_defense", 1, dict(near=(112, -540), radius=18), [("dreg", 2), ("vandal", 1), ("shank", 2)],
             "src area: enc_launchpad_hangar_ship mixed/shank squads (104..127,-533..-543); r6: wave 1 of 3"),
            # r6 (authored): two Skiff-dropped waves under the ship-bay roof hole, either side of prop.ship and
            # outside its hull footprint (rg_ship ~7 x 9 blocks), open sky straight above for a direct drop.
            ("dock_ship_west", 2, dict(near=(72, -561), radius=7, avoid=(78.5, -567.0, 6.0), sky=True),
             [("dreg", 2), ("vandal", 2)], "authored (r6): wave 2, Skiff drop NW of the ship under the roof hole"),
            ("dock_ship_east", 3, dict(near=(85, -573), radius=7, avoid=(78.5, -567.0, 6.0), sky=True),
             [("captain", 1), ("vandal", 2), ("dreg", 2)], "authored (r6): wave 3, Skiff drop SE of the ship, captain finale"),
        ],
        lights=[
            ("light.hangar_gate", (110, -540, 5.0), True, "always", "authored"),
            ("light.ship_bay", (82, -563, 5.0), False, "ship_scan", "authored: lit by the Ghost ship scan"),
        ],
    ),
}


def clear_area(pas, stand, x, y, z, radius=3, height=9):
    """Open footprint for large enemies: standable floor within radius and free air `height` up."""
    sy, sz, sx = pas.shape
    if y + height >= sy or x - radius < 0 or z - radius < 0 or x + radius >= sx or z + radius >= sz:
        return False
    box = pas[y:y + height, z - radius:z + radius + 1, x - radius:x + radius + 1]
    return bool(box.all()) and int(stand[y, z - radius:z + radius + 1, x - radius:x + radius + 1].sum()) >= (2 * radius + 1) ** 2 * 0.8


def open_column(pas, cells):
    """True for (y, z, x) cells with nothing solid anywhere above them (open sky)."""
    solid = ~pas
    top = np.where(solid.any(0), solid.shape[0] - 1 - np.argmax(solid[::-1], 0), -1)
    return top[cells[:, 1], cells[:, 2]] < cells[:, 0]


def _yaw_from_src_dir(d):
    """Minecraft yaw for a source-space XY facing direction."""
    mx, mz = d[0], -d[1]
    return round(math.degrees(math.atan2(-mx, mz)), 1)


def place_markers(name, grid: Grid, state, states, pal: Palette, log=print):
    """Resolves MARKER_SPECS into zone-local markers; may edit state (barriers, light fixtures)."""
    spec = MARKER_SPECS[name]; bubble = ZONES[name]["bubble"]
    stand = standable(state, states); pas = passable_mask(state, states)
    markers = []; prov = []

    def local(c, y_off=0.0):
        return [round(c[0] + 0.5, 3), round(c[1] + y_off, 3), round(c[2] + 0.5, 3)]

    spawn = None
    for mid, where, facing, tags, why in spec["points"]:
        tags = dict(tags)
        if mid == "ghost.scan":
            continue
        free = tags.pop("free", None) == "true"
        if isinstance(where, str) and where.startswith("prop:"):
            p, yaw = prop(bubble, where[5:])
            yaw_mc = round(-yaw + 0.0, 1) if yaw is not None else 0.0
            # source yaw is about +Z (Destiny); convert heading to Minecraft yaw via a direction vector
            if yaw is not None:
                yaw_mc = _yaw_from_src_dir((math.cos(math.radians(yaw)), math.sin(math.radians(yaw))))
        else:
            p = where; yaw_mc = _yaw_from_src_dir(facing)
        b = grid.to_block(np.array(p, float))
        if free:
            pos = [round(float(v), 3) for v in b]
        else:
            c = nearest_standable(stand, b, 6)
            if c is None:
                raise SystemExit(f"[{name}] marker {mid}: no standable cell near {p}")
            pos = local(c)
        markers.append(dict(id=mid, pos=pos, yaw=yaw_mc, tags=tags)); prov.append((mid, why, p))
        if mid == "spawn.player":
            spawn = (pos, yaw_mc)
    if spawn and ("ghost" in spec or any(m[0] == "ghost.scan" for m in spec["points"])):
        g = spec.get("ghost", dict(distance=1.9, height=1.45))
        (px, py, pz), yaw = spawn
        fx, fz = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        gp = [round(px + fx * g["distance"], 3), round(py + g["height"], 3), round(pz + fz * g["distance"], 3)]
        markers.append(dict(id="ghost.scan", pos=gp, yaw=round((yaw + 180) % 360 - 180, 1),
                            tags={"look_at": "spawn.player"}))
        prov.append(("ghost.scan", "authored: hover point in front of the player's eye, facing the player", None))
    # Encounters: distinct, reachable, standable spawn cells around the source squads.
    start = nearest_standable(stand, grid.to_block(np.array(ZONES[name]["start"], float)), 8)
    seen = reach(stand, pas, start, region=core_region(name, grid))
    taken = set()
    for enc, order, area, comp, why in spec.get("encounters", []):
        cx, cy = area["near"]; r = area["radius"]
        pts = [p for p in actors(bubble, near=(cx, cy), radius=r)] or [(cx, cy, 0.0)]
        cands = np.argwhere(stand & seen)  # (y, z, x)
        src_xy = grid.src_of_block(np.stack([cands[:, 2] + 0.5, cands[:, 0], cands[:, 1] + 0.5], 1))
        d = np.hypot(src_xy[:, 0] - cx, src_xy[:, 1] - cy)
        keep = d <= r
        if "avoid" in area:
            ax, ay, ar = area["avoid"]
            keep &= np.hypot(src_xy[:, 0] - ax, src_xy[:, 1] - ay) >= ar
        if area.get("sky"):
            keep &= open_column(pas, cands)
        inside = np.nonzero(keep)[0]
        if not len(inside):
            raise SystemExit(f"[{name}] encounter {enc}: no reachable floor within {r} m of {area['near']}")
        # prefer cells near any source actor point and at the source height
        sp = np.array(pts, float)
        dd = np.min(np.hypot(src_xy[inside, None, 0] - sp[None, :, 0], src_xy[inside, None, 1] - sp[None, :, 1])
                    + 0.5 * np.abs(src_xy[inside, None, 2] - sp[None, :, 2]), 1)
        order_idx = inside[np.argsort(dd)]
        kinds = [k for k, n in comp for _ in range(n)]
        chosen = []
        for k in kinds:
            best = None
            for ci in order_idx:
                y_, z_, x_ = cands[ci]
                if (x_, y_, z_) in taken:
                    continue
                if k == "walker" and not clear_area(pas, stand, x_, y_, z_, radius=3, height=9):
                    continue
                if all(abs(x_ - q[0]) + abs(z_ - q[2]) >= (5 if k == "walker" else 3) for q in chosen):
                    best = (x_, y_, z_); break
            if best is None:
                raise SystemExit(f"[{name}] encounter {enc}: not enough distinct cells")
            chosen.append(best); taken.add(best)
        # face the player's approach: toward the encounter centroid from the spawn side -> face spawn
        for i, (k, c) in enumerate(zip(kinds, chosen)):
            to = np.array(spawn[0]) - np.array(local(c)) if spawn else np.array([0, 0, 1.0])
            yaw = round(math.degrees(math.atan2(-to[0], to[2])), 1)
            markers.append(dict(id=f"enemy.{enc}.{i}", pos=local(c), yaw=yaw,
                                tags={"kind": k, "order": str(order)}))
        prov.append((f"enemy.{enc}.*", why + f"; {len(kinds)} spawns (actor counts are not spawn counts)", (cx, cy)))
    # Lights: switchable copper-bulb fixtures embedded in the ceiling above the floor point.
    for lid, p, lit, phase, why in spec.get("lights", []):
        b = grid.to_block(np.array(p, float))
        c = nearest_standable(stand, b, 4)
        if c is None:
            raise SystemExit(f"[{name}] light {lid}: no floor")
        x, y, z = c
        fy = None
        for yy in range(y + 2, min(y + 10, state.shape[0])):
            if not pas[yy, z, x]:
                fy = yy; break
        bulb = "waxed_weathered_copper_bulb" if phase == "always" else "waxed_exposed_copper_bulb"
        lit_state = f"minecraft:{bulb}[lit=true,powered=false]"
        off_state = f"minecraft:{bulb}[lit=false,powered=false]"
        if fy is None:   # open sky above: free-standing lantern post beside the route
            fy = y; st = "minecraft:lantern[hanging=false,waterlogged=false]" if lit else "minecraft:air"
            tags = {"block": "minecraft:lantern[hanging=false,waterlogged=false]", "mount": "floor"}
        else:
            st = lit_state if lit else off_state
            tags = {"block": lit_state, "unlit": off_state, "mount": "ceiling"}
        if st != "minecraft:air":
            state[fy, z, x] = pal.id(st)
        level = {"waxed_weathered_copper_bulb": "8", "waxed_exposed_copper_bulb": "12"}.get(bulb, "15")
        if tags["mount"] == "floor":
            level = "15"
        tags.update({"level": level, "phase": phase})
        markers.append(dict(id=lid, pos=[x + 0.5, fy + 0.5, z + 0.5], yaw=0.0, tags=tags))
        prov.append((lid, why, p))
    # Every walk-to marker must be reachable from the zone start under the Minecraft movement model.
    for m in markers:
        if m["id"].startswith(("light.", "prop.", "ghost.")):
            continue
        x, y, z = (int(math.floor(v)) for v in m["pos"])
        if not seen[y, z, x]:
            raise SystemExit(f"[{name}] marker {m['id']} at {m['pos']} is not reachable from the zone start")
    log(f"  markers: {len(markers)} (all walk-to markers reachable)")
    return markers, prov, seen


# Authored geometry fixes (documented): connect walk routes the voxel conversion leaves broken.
# Each entry: (kind, src xyz a, src xyz b, block) -- kinds: "ramp" (slab/full-block stair line from a
# to b over the existing floor), "fill" (solid box a..b), "clear" (air box a..b).
FIXUPS: dict[str, list] = {}


def apply_fixups(name, grid: Grid, state, pal: Palette, log=print):
    for kind, a, b, block in FIXUPS.get(name, []):
        pa = np.floor(grid.to_block(np.array(a, float))).astype(int)
        pb = np.floor(grid.to_block(np.array(b, float))).astype(int)
        lo = np.minimum(pa, pb); hi = np.maximum(pa, pb)
        sl = (slice(lo[1], hi[1] + 1), slice(lo[2], hi[2] + 1), slice(lo[0], hi[0] + 1))
        if kind == "fill":
            state[sl] = pal.id(block)
        elif kind == "clear":
            state[sl] = 0
        elif kind == "ramp":
            # staircase of half steps from a (low) to b (high) along the dominant horizontal axis
            n = int(max(abs(pb[0] - pa[0]), abs(pb[2] - pa[2]), 1))
            for i in range(n + 1):
                t = i / n
                x = int(round(pa[0] + (pb[0] - pa[0]) * t)); z = int(round(pa[2] + (pb[2] - pa[2]) * t))
                h = pa[1] + (pb[1] - pa[1]) * t
                for w in (-1, 0, 1):
                    xx, zz = (x + w, z) if abs(pb[2] - pa[2]) >= abs(pb[0] - pa[0]) else (x, z + w)
                    for yy in range(int(pa[1]) - 1, int(math.floor(h))):
                        state[yy, zz, xx] = pal.id(block.split("|")[0])
                    if h - math.floor(h) >= 0.5:
                        state[int(math.floor(h)), zz, xx] = pal.id(block.split("|")[1])
                    for yy in range(int(math.floor(h)) + (1 if h - math.floor(h) >= 0.5 else 0), int(math.floor(h)) + 3):
                        if 0 <= yy < state.shape[0]:
                            state[yy, zz, xx] = 0
        log(f"  fixup {kind} {a}->{b}")
    return state


def core_region(name, grid: Grid):
    """(x0, x1, z0, z1) block range of the playable core inside the zone grid."""
    lo, hi = ZONES[name]["core"]
    a = np.floor(grid.to_block(np.array([lo[0], hi[1], lo[2]], float))).astype(int)
    b = np.ceil(grid.to_block(np.array([hi[0], lo[1], hi[2]], float))).astype(int)
    return (max(a[0], 0), min(b[0], grid.size[0]), max(a[2], 0), min(b[2], grid.size[2]))


def add_boundary_barriers(name, grid: Grid, state, states, pal: Palette, seen, log=print):
    """Invisible barrier walls where reachable floor meets the playable core boundary (no walking into
    the vista shell or off cut geometry)."""
    x0, x1, z0, z1 = core_region(name, grid)
    sy, sz, sx = state.shape
    bar = pal.id("minecraft:barrier")
    pas = passable_mask(state, states)
    n = 0
    ys, zs, xs = np.nonzero(seen)
    edge = (xs == x0) | (xs == x1 - 1) | (zs == z0) | (zs == z1 - 1)
    for x, y, z in zip(xs[edge], ys[edge], zs[edge]):
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            outside = nx < x0 or nx >= x1 or nz < z0 or nz >= z1
            if not outside:
                continue
            if not (0 <= nx < sx and 0 <= nz < sz):
                nx, nz = x, z   # grid ends at the core: fence the edge cell itself
            for yy in range(max(0, y - 1), min(sy, y + 4)):
                if pas[yy, nz, nx] and state[yy, nz, nx] != bar:
                    state[yy, nz, nx] = bar; n += 1
    log(f"  boundary barriers: {n}")
    return n


# --------------------------------------------------------------------------------------------
# Light simulation + lighting pass (W300 r2)
#
# Block light follows the vanilla rule: a source of level L lights neighbours with L-1, and so on
# through transparent cells.  Opaque = every full block plus slabs/snow layers (conservative: real
# slabs leak light sideways, so the simulation can only under-estimate).  Transparent = air, light,
# barrier, iron bars, chains, walls, lanterns.  Sky light: 15 down open columns, then spreads -1 per
# step (daytime; the instance clock is pinned to morning).
# --------------------------------------------------------------------------------------------

_TRANSPARENT_IDS = ("air", "light", "barrier", "iron_bars", "iron_chain", "lantern")


def _base_name(st):
    return st.split(":")[1].split("[")[0]


def light_tables(states):
    names = [_base_name(s) for s in states]
    trans = np.array([n in _TRANSPARENT_IDS or n.endswith("_wall") for n in names])
    emit = np.zeros(len(states), np.int8)
    for i, s in enumerate(states):
        n = names[i]
        if n.endswith("copper_bulb") and "lit=true" in s:
            emit[i] = {"waxed_copper_bulb": 15, "waxed_exposed_copper_bulb": 12,
                       "waxed_weathered_copper_bulb": 8, "waxed_oxidized_copper_bulb": 4}[n]
        elif n == "lantern":
            emit[i] = 15
        elif n == "light":
            emit[i] = int(s.split("level=")[1].split(",")[0].split("]")[0]) if "level=" in s else 15
    return trans, emit


def _spread(field, trans, fixed=None, iterations=15):
    """In-place max-minus-one dilation of int8 light through transparent cells."""
    f = field
    for _ in range(iterations):
        nb = np.zeros_like(f)
        np.maximum(nb[1:], f[:-1], out=nb[1:]); np.maximum(nb[:-1], f[1:], out=nb[:-1])
        np.maximum(nb[:, 1:], f[:, :-1], out=nb[:, 1:]); np.maximum(nb[:, :-1], f[:, 1:], out=nb[:, :-1])
        np.maximum(nb[:, :, 1:], f[:, :, :-1], out=nb[:, :, 1:]); np.maximum(nb[:, :, :-1], f[:, :, 1:], out=nb[:, :, :-1])
        nb = np.where(trans, np.maximum(nb - 1, 0), 0).astype(np.int8)
        new = np.maximum(f, nb)
        if fixed is not None:
            new = np.maximum(new, fixed)
        if np.array_equal(new, f):
            break
        f[...] = new
    return f


def block_light(state, states):
    trans, emit = light_tables(states)
    t = trans[state]; e = emit[state]
    f = e.copy()
    return _spread(f, t, fixed=e)


def sky_light(state, states):
    trans, _ = light_tables(states)
    t = trans[state]
    blocked = np.cumsum(~t[::-1], 0)[::-1] > 0   # any opaque at or above
    f = np.where(~blocked, 15, 0).astype(np.int8)
    return _spread(f, t, fixed=np.where(~blocked, 15, 0).astype(np.int8))


def _local_field(trans, src, level, r=15):
    """Light from a single source (y, z, x) in a cube window; returns (slices, field)."""
    sy, sz, sx = trans.shape
    y, z, x = src
    sl = (slice(max(y - r, 0), min(y + r + 1, sy)), slice(max(z - r, 0), min(z + r + 1, sz)),
          slice(max(x - r, 0), min(x + r + 1, sx)))
    t = trans[sl]
    fixed = np.zeros(t.shape, np.int8)
    fixed[y - sl[0].start, z - sl[1].start, x - sl[2].start] = level
    return sl, _spread(fixed.copy(), t, fixed=fixed, iterations=level)


LIGHT_TARGETS = {
    # zone: (min effective light on the route, route scope, target mean block-or-sky light on roofed route)
    "dock13": dict(minimum=4, scope="all", mean=(7.0, 10.0), aim=8.5),
    "divide": dict(minimum=4, scope="roofed", mean=None, aim=None),
}
SHIP_SCAN_MEAN = 11.5      # ship bay (route cells within SHIP_BAY_RADIUS of prop.ship) once ship_scan lights are on
SHIP_BAY_RADIUS = 9


def _route_stats(eff, route):
    v = eff[route].astype(np.float64)
    return dict(cells=int(route.sum()), min=int(v.min()) if len(v) else 0, mean=round(float(v.mean()), 2) if len(v) else 0,
                p10=float(np.percentile(v, 10)) if len(v) else 0,
                below4=int((v < 4).sum()), hist=np.bincount(v.astype(int), minlength=16).tolist())


def _candidates(state, trans, is_full, route_cell, max_up=6, radius=3):
    """Visible fixture sites near a route feet cell: full opaque blocks on a wall (feet+2..+4) or the
    ceiling (feet+2..+max_up) with an exposed transparent face."""
    sy, sz, sx = state.shape
    y0, z0, x0 = route_cell
    out = []
    for dy in range(2, max_up + 1):
        y = y0 + dy
        if y >= sy - 1:
            break
        for dz in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                z, x = z0 + dz, x0 + dx
                if not (0 <= z < sz and 0 <= x < sx) or not is_full[y, z, x]:
                    continue
                ceiling = trans[y - 1, z, x]
                wall = dy <= 4 and any(0 <= z + a < sz and 0 <= x + b < sx and trans[y, z + a, x + b]
                                       for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if ceiling or wall:
                    out.append((y, z, x))
    return out


def lighting_pass(name, grid: Grid, state, pal: Palette, seen, markers, prov, log=print):
    """Adds 'always' fixtures until the route meets LIGHT_TARGETS; adds ship_scan fixtures for the bay.
    Fails the build (SystemExit) when a target cannot be met.  Returns stats."""
    states = pal.states
    trans_tab, emit_tab = light_tables(states)
    trans = trans_tab[state]
    names = [_base_name(s) for s in states]
    full_ids = np.array([not trans_tab[i] and not n.endswith(("_slab", "_wall", "_stairs", "copper_bulb"))
                         and n not in ("snow", "barrier", "light") for i, n in enumerate(names)])
    is_full = full_ids[state]
    sky = sky_light(state, states)
    blk = block_light(state, states)
    target = LIGHT_TARGETS.get(name)
    roofed = seen & (sky < 4)
    stats = {"zone": name}
    stats["before"] = dict(route=_route_stats(np.maximum(blk, sky), seen), roofed=_route_stats(np.maximum(blk, sky), roofed))
    added = []
    if target:
        route = seen if target["scope"] == "all" else roofed
        bulb = {12: "minecraft:waxed_exposed_copper_bulb[lit=true,powered=false]",
                15: "minecraft:waxed_copper_bulb[lit=true,powered=false]"}
        fill = "minecraft:light[level={},waterlogged=false]"
        rcells = np.argwhere(route)

        def eff_at():
            return np.maximum(blk, sky)

        for it in range(2000):
            eff = eff_at()
            v = eff[route]
            need_min = v.min() < target["minimum"]
            need_mean = target["aim"] is not None and roofed.any() and eff[roofed].mean() < target["aim"]
            if not need_min and not need_mean:
                break
            goal = target["minimum"] if need_min else int(math.ceil(target["aim"]))
            dark = rcells[eff[route] < goal]
            # darkest first, then deterministic order
            dv = eff[dark[:, 0], dark[:, 1], dark[:, 2]]
            worst = tuple(dark[np.lexsort((dark[:, 2], dark[:, 1], dark[:, 0], dv))[0]])
            best = None
            for c in _candidates(state, trans, is_full, worst):
                for lvl in (12, 15):
                    sl, f = _local_field(trans, c, lvl)
                    rsub = route[sl]; cur = eff[sl]
                    gain = int((np.minimum(np.maximum(f, cur), goal) - np.minimum(cur, goal))[rsub].sum())
                    covered = np.maximum(f, cur)[worst[0] - sl[0].start, worst[1] - sl[1].start, worst[2] - sl[2].start] >= goal
                    score = gain * (1.0 if lvl == 12 else 0.75) + (1000 if covered else 0)
                    if best is None or score > best[0]:
                        best = (score, c, lvl, sl, f, "bulb")
            if best is None or best[0] < 1000:
                # open hall with nothing to mount on: invisible fill light above head height
                y, z, x = worst
                fy = y + 2 if y + 2 < state.shape[0] and state[y + 2, z, x] == 0 else y + 1
                if state[fy, z, x] == 0:
                    lvl = 11
                    sl, f = _local_field(trans, (fy, z, x), lvl)
                    best = (0, (fy, z, x), lvl, sl, f, "fill")
            if best is None:
                raise SystemExit(f"[{name}] lighting: no fixture site for dark route cell {worst}")
            _, c, lvl, sl, f, kind = best
            st = bulb[lvl] if kind == "bulb" else fill.format(lvl)
            state[c] = pal.id(st)
            if kind == "fill":
                trans[c] = True
            np.maximum(blk[sl], f, out=blk[sl])
            added.append((kind, lvl, c))
        else:
            raise SystemExit(f"[{name}] lighting: target not met after 2000 fixtures")
        eff = np.maximum(blk, sky)
        if eff[route].min() < target["minimum"]:
            raise SystemExit(f"[{name}] lighting: route minimum {eff[route].min()} < {target['minimum']}")
        if target["mean"] is not None and roofed.any() and not (target["mean"][0] <= eff[roofed].mean() <= target["mean"][1]):
            raise SystemExit(f"[{name}] lighting: roofed route mean {eff[roofed].mean():.2f} outside {target['mean']}")
    stats["fixtures"] = dict(bulb12=sum(1 for k, l, _ in added if k == "bulb" and l == 12),
                             bulb15=sum(1 for k, l, _ in added if k == "bulb" and l == 15),
                             fill=sum(1 for k, *_ in added if k == "fill"))
    eff = np.maximum(blk, sky)
    stats["after"] = dict(route=_route_stats(eff, seen), roofed=_route_stats(eff, roofed))
    # Ship bay: switchable bulbs (built unlit), verified with the phase lit.
    ship = next((m for m in markers if m["id"] == "prop.ship"), None)
    if ship is not None:
        sx_, sy_, sz_ = ship["pos"]
        ys, zs, xs = np.nonzero(seen)
        near = (np.hypot(xs + 0.5 - sx_, zs + 0.5 - sz_) <= SHIP_BAY_RADIUS) & (np.abs(ys - sy_) <= 4)
        bay = np.zeros_like(seen); bay[ys[near], zs[near], xs[near]] = True
        phase_blk = blk.copy()
        for m in markers:   # existing ship_scan lights, lit
            if m["id"].startswith("light.") and m["tags"].get("phase") == "ship_scan":
                x, y, z = (int(math.floor(v)) for v in m["pos"])
                sl, f = _local_field(trans, (y, z, x), 15)
                np.maximum(phase_blk[sl], f, out=phase_blk[sl])
        # Judged on block light only, so the bay reads at any instance time of day.
        n = 0
        bcells = np.argwhere(bay)
        while phase_blk[bay].mean() < SHIP_SCAN_MEAN and n < 40:
            e = phase_blk
            dv = e[bay]
            worst = tuple(bcells[np.lexsort((bcells[:, 2], bcells[:, 1], bcells[:, 0], dv))[0]])
            best = None
            for c in _candidates(state, trans, is_full, worst, max_up=8, radius=4):
                sl, f = _local_field(trans, c, 15)
                gain = int((np.maximum(f, e[sl]) - e[sl])[bay[sl]].sum())
                if best is None or gain > best[0]:
                    best = (gain, c, sl, f, "bulb")
            if best is None or best[0] == 0:
                y, z, x = worst      # open bay: switchable fill light above head height
                fy = y + 2 if state[y + 2, z, x] == 0 else y + 1
                sl, f = _local_field(trans, (fy, z, x), 15)
                best = (1, (fy, z, x), sl, f, "fill")
            _, c, sl, f, kind = best
            y, z, x = c
            n += 1
            mid = f"light.ship_bay_{n}"
            if kind == "bulb":
                state[c] = pal.id("minecraft:waxed_copper_bulb[lit=false,powered=false]")
                tags = {"block": "minecraft:waxed_copper_bulb[lit=true,powered=false]",
                        "unlit": "minecraft:waxed_copper_bulb[lit=false,powered=false]", "mount": "ceiling"}
            else:   # not built; the director places the invisible light block when ship_scan starts
                tags = {"block": "minecraft:light[level=15,waterlogged=false]", "mount": "fill"}
                trans[c] = True
            tags.update({"level": "15", "phase": "ship_scan"})
            np.maximum(phase_blk[sl], f, out=phase_blk[sl])
            markers.append(dict(id=mid, pos=[x + 0.5, y + 0.5, z + 0.5], yaw=0.0, tags=tags))
            prov.append((mid, "authored (r2): ship bay flood light, lit by the Ghost ship scan", None))
        if phase_blk[bay].mean() < SHIP_SCAN_MEAN:
            raise SystemExit(f"[{name}] lighting: ship bay block-light mean below {SHIP_SCAN_MEAN}")
        stats["ship_bay"] = dict(fixtures=n, build_block=_route_stats(blk, bay), build_eff=_route_stats(eff, bay),
                                 ship_scan_block=_route_stats(phase_blk, bay))
    np.save(CACHE_DIR / f"light_{name}.npy", np.stack([blk, sky]))
    log(f"  lighting: {json.dumps({k: v for k, v in stats.items() if k != 'zone'}, default=str)[:600]}")
    return stats


# --------------------------------------------------------------------------------------------
# QA reference routes (W300 r3): shortest walkable path through the zone objectives.  Evidence only.
# --------------------------------------------------------------------------------------------

ROUTES = {
    "gateway": ["spawn.player", "trigger.wall_entrance", "exit.breach"],
    "breach": ["spawn.player", "trigger.rifle", "light.arena_one", "trigger.cache", "exit.divide"],
    "divide": ["spawn.player", "trigger.walker_arena", "exit.dock13"],
    "dock13": ["spawn.player", "trigger.dock_enter", "trigger.ship"],
}


def floor_height(state, states, y, z, x):
    """Top surface height (blocks) under feet cell y: full block = y, bottom slab / snow[4] = y - 0.5."""
    st = states[state[y - 1, z, x]]
    if "type=bottom" in st or st.startswith("minecraft:snow["):
        return y - 0.5
    return float(y)


def route_moves(stand, pas, max_down=12, region=None):
    """Neighbour generator matching reach(): returns list of (landing cell) per cell."""
    sy, sz, sx = stand.shape

    def moves(c):
        x, y, z = c
        out = []
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            if not (0 <= nx < sx and 0 <= nz < sz):
                continue
            if region is not None and not (region[0] <= nx < region[1] and region[2] <= nz < region[3]):
                continue
            if y + 2 < sy and stand[y + 1, nz, nx] and pas[y + 2, z, x]:
                out.append((nx, y + 1, nz))
            elif pas[y, nz, nx] and pas[y + 1, nz, nx]:
                ny = y
                while ny > 1 and pas[ny - 1, nz, nx] and y - ny < max_down:
                    ny -= 1
                if stand[ny, nz, nx]:
                    out.append((nx, ny, nz))
        return out
    return moves


def shortest_path(moves, start, goals):
    from collections import deque
    prev = {start: None}; q = deque([start])
    while q:
        c = q.popleft()
        if c in goals:
            path = []
            while c is not None:
                path.append(c); c = prev[c]
            return path[::-1]
        for n in moves(c):
            if n not in prev:
                prev[n] = c; q.append(n)
    return None


def select_waypoints(cells, keep=(), lo=3.0, hi=6.0, every=4.0):
    """Path indices ~`every` blocks apart (horizontal); objectives/ends always kept, and a plain waypoint
    closer than `lo` to a kept one is dropped when the gap it leaves stays <= `hi`."""
    keep = set(keep) | {0, len(cells) - 1}
    hd = lambda i, j: math.hypot(cells[i][0] - cells[j][0], cells[i][2] - cells[j][2])
    out = [0]
    for i in range(1, len(cells)):
        if i in keep:
            if len(out) >= 2 and out[-1] not in keep and hd(out[-1], i) < lo:
                a = out[-2]
                if hd(a, i) <= hi:
                    out.pop()
                else:   # re-pick the previous point so both gaps are within [lo, hi]
                    mid = next((k for k in range(a + 1, i) if lo <= hd(a, k) <= hi and lo <= hd(k, i) <= hi), None)
                    if mid is not None:
                        out[-1] = mid
            out.append(i)
        elif hd(out[-1], i) >= every:
            out.append(i)
    return out


def export_routes(names, log=print):
    out = {"schema": 1, "coordinates": "zone-local block coords (feet; x/z cell centre, y = floor surface height)",
           "model": "4-neighbour walk, step/jump up 1 block, drop <= 12, core region only (rising_maps.reach)",
           "jump_rule": "jump=true on a waypoint when the floor rises > 0.6 blocks before the next waypoint",
           "zones": {}}
    doc = json.loads((OUT_DIR / "markers.json").read_text())
    for name in names:
        spec = ZONES[name]; lo, hi = spec.get("vista", spec["core"]); grid = Grid(lo, hi, SCALE)
        state = np.load(CACHE_DIR / f"state_{name}.npy"); states = json.loads((CACHE_DIR / f"states_{name}.json").read_text())
        stand = standable(state, states); pas = passable_mask(state, states)
        region = core_region(name, grid)
        ms = {m["id"]: m for m in doc["zones"][name]["markers"]}
        sp = ms["spawn.player"]["pos"]
        seen = reach(stand, pas, (int(sp[0]), int(sp[1]), int(sp[2])), region=region)
        moves = route_moves(stand, pas, region=region)

        def goal_cells(mid):
            m = ms[mid]; x, y, z = m["pos"]
            r = float(m["tags"].get("radius", 1.5)) if mid.startswith(("trigger.", "exit.")) else 1.0
            if mid.startswith("light."):
                r = 4.0   # "area" under the ceiling fixture
            ys, zs, xs = np.nonzero(seen)
            d = np.hypot(xs + 0.5 - x, zs + 0.5 - z)
            dy = ys - y if not mid.startswith("light.") else ys - (y - 8)
            ok = (d <= r) & (np.abs(dy) <= (3 if not mid.startswith("light.") else 9))
            if mid.startswith("light."):
                ok &= ys < y
            if not ok.any():
                i = int(np.argmin(d + np.abs(dy)))
                ok = np.zeros(len(xs), bool); ok[i] = True
            return set(zip(xs[ok].tolist(), ys[ok].tolist(), zs[ok].tolist()))

        cur = (int(sp[0]), int(sp[1]), int(sp[2]))
        full = [cur]; legs = []
        for mid in ROUTES[name][1:]:
            p = shortest_path(moves, cur, goal_cells(mid))
            if p is None:
                raise SystemExit(f"[{name}] no path to {mid}")
            legs.append(dict(to=mid, steps=len(p) - 1, start_index=len(full) - 1))
            full += p[1:]; cur = p[-1]
        h = [floor_height(state, states, y, z, x) for x, y, z in full]
        jumps = [i for i in range(1, len(full)) if h[i] - h[i - 1] > 0.6]
        # waypoints: every 4 steps, plus each objective, never closer than 3 unless it is an objective
        obj_idx = {l["start_index"] + l["steps"]: l["to"] for l in legs}
        wp_idx = select_waypoints(full, obj_idx)
        wps = []
        for k, i in enumerate(wp_idx):
            nxt = wp_idx[k + 1] if k + 1 < len(wp_idx) else i
            x, y, z = full[i]
            w = dict(pos=[x + 0.5, round(h[i], 1), z + 0.5], jump=any(i < j <= nxt for j in jumps))
            if i in obj_idx:
                w["objective"] = obj_idx[i]
            if i == 0:
                w["objective"] = "spawn.player"
            wps.append(w)
        out["zones"][name] = dict(steps=len(full) - 1, jumps=len(jumps), legs=legs, waypoints=wps)
        np.save(CACHE_DIR / f"route_{name}.npy", np.array(full))
        log(f"[{name}] route {len(full) - 1} steps, {len(jumps)} jumps, {len(wps)} waypoints, legs={[(l['to'], l['steps']) for l in legs]}")
    d = EVIDENCE / "r3"; d.mkdir(parents=True, exist_ok=True)
    (d / "routes.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    return out


# --------------------------------------------------------------------------------------------
# W300 r4: guidance route (bundled routes.json) + route-cue lights
# --------------------------------------------------------------------------------------------

ROUTE_JUMP_COST = 8
ROUTE_GOAL_INSET = 1.5      # route ends this far inside an objective radius (director uses <= radius)


def objective_radius(m):
    """Horizontal trigger radius of an objective marker (light.* objective = 4 m area under the fixture)."""
    return 4.0 if m["id"].startswith("light.") else float(m["tags"].get("radius", 1.5))


def check_route_objectives(name, wps, objective_idx, markers):
    """Final waypoint and the waypoint nearest each objective must lie inside it by ROUTE_GOAL_INSET
    (horizontal) and within its height tag; fails the build otherwise.  Returns per-objective rows."""
    ms = {m["id"]: m for m in markers}
    rows = []
    for mid, k in objective_idx.items():
        if mid == "spawn.player":
            continue
        m = ms[mid]; mx, my, mz = m["pos"]
        r = objective_radius(m)
        hgt = float(m["tags"].get("height", max(3.0, r)))
        dist = [math.hypot(w[0] - mx, w[2] - mz) for w in wps]
        near = int(np.argmin(dist))
        for label, i in (("objective waypoint", k), ("nearest waypoint", near)):
            w = wps[i]
            dy = abs(w[1] - my) if not mid.startswith("light.") else 0.0
            ok = dist[i] <= r - ROUTE_GOAL_INSET + 1e-6 and dy <= hgt
            rows.append(dict(objective=mid, which=label, index=i, dist=round(dist[i], 2), radius=r, dy=round(dy, 2),
                             height=hgt, ok=ok))
            if not ok:
                raise SystemExit(f"[{name}] route {label} {i} {w[:3]} is {dist[i]:.2f} m / dy {dy:.1f} from {mid} "
                                 f"(radius {r}, inset {ROUTE_GOAL_INSET}, height {hgt})")
    last = len(wps) - 1
    if last not in objective_idx.values():
        raise SystemExit(f"[{name}] route does not end on its final objective")
    return rows          # a 1-block jump costs like 8 extra steps: prefer walkable lanes over parkour
CUE_TUNNEL = {"gateway": dict(after="trigger.wall_entrance", minimum=6, mean=8.0)}
CUE_LANE = {"gateway": dict(spacing=32, before="trigger.wall_entrance")}
CUE_TURNS = {"divide": dict(max=6)}
_ROUTE_CACHE: dict = {}


def guidance_route(name, state, states, markers, region):
    """Jump-penalised shortest walk spawn.player -> objectives (ROUTES order). Returns cells and leg ends."""
    import heapq
    stand = standable(state, states); pas = passable_mask(state, states)
    ms = {m["id"]: m for m in markers}
    sp = ms["spawn.player"]["pos"]; start = (int(sp[0]), int(sp[1]), int(sp[2]))
    seen = reach(stand, pas, start, region=region)
    moves = route_moves(stand, pas, region=region)
    ys, zs, xs = np.nonzero(seen)

    def goal_cells(mid):
        x, y, z = ms[mid]["pos"]
        light_area = mid.startswith("light.")
        r = objective_radius(ms[mid]) - ROUTE_GOAL_INSET
        d = np.hypot(xs + 0.5 - x, zs + 0.5 - z)
        ok = (d <= r) & ((ys < y) & (ys >= y - 9) if light_area else (np.abs(ys - y) <= 3))
        if not ok.any():
            ok = np.zeros(len(xs), bool); ok[int(np.argmin(d + np.abs(ys - y)))] = True
        return set(zip(xs[ok].tolist(), ys[ok].tolist(), zs[ok].tolist()))

    def dij(a, goals):
        dist = {a: 0}; prev = {a: None}; pq = [(0, a)]
        while pq:
            dc, c = heapq.heappop(pq)
            if c in goals:
                out = []
                while c is not None:
                    out.append(c); c = prev[c]
                return out[::-1]
            if dc > dist[c]:
                continue
            hc = floor_height(state, states, c[1], c[2], c[0])
            for n in moves(c):
                w = 1 + (ROUTE_JUMP_COST if floor_height(state, states, n[1], n[2], n[0]) - hc > 0.6 else 0)
                if dc + w < dist.get(n, 1 << 60):
                    dist[n] = dc + w; prev[n] = c; heapq.heappush(pq, (dc + w, n))
        return None

    cur = start; full = [start]; ends = {0: "spawn.player"}
    for mid in ROUTES[name][1:]:
        p = dij(cur, goal_cells(mid))
        if p is None:
            raise SystemExit(f"[{name}] guidance route: no path to {mid}")
        full += p[1:]; cur = p[-1]; ends[len(full) - 1] = mid
    h = [floor_height(state, states, y, z, x) for x, y, z in full]
    return full, h, ends, stand, pas, seen


def _lantern_site(state, stand, pas, route_set, near_markers, cell, prefer_side=None):
    """Floor-lantern cell beside a route cell that keeps a >= 2-wide walk: the lantern stands against an
    obstacle (no walkable cell beyond it) or two cells out, never on the route, and never on/next to a marker."""
    x, y, z = cell
    sy, sz, sx = state.shape
    best = None
    for dist in (1, 2):
        for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dy in (0, 1, -1):
                c = (x + ox * dist, y + dy, z + oz * dist)
                if not (0 < c[1] < sy - 1 and 0 <= c[0] < sx and 0 <= c[2] < sz):
                    continue
                if not stand[c[1], c[2], c[0]] or state[c[1], c[2], c[0]] != 0 or c in route_set:
                    continue
                if any(abs(c[0] - m[0]) <= 1 and abs(c[2] - m[2]) <= 1 and abs(c[1] - m[1]) <= 2 for m in near_markers):
                    continue
                # walk width: the route cell keeps a walkable neighbour on the far side, or the lantern is 2 out
                far = (x - ox, y, z - oz)
                far_ok = 0 <= far[0] < sx and 0 <= far[2] < sz and (stand[far[1], far[2], far[0]]
                                                                    or stand[far[1] + 1, far[2], far[0]])
                beyond = (c[0] + ox, c[1], c[2] + oz)
                against = not (0 <= beyond[0] < sx and 0 <= beyond[2] < sz) or not pas[beyond[1], beyond[2], beyond[0]]
                if dist == 1 and not (far_ok and against):
                    continue
                # no walkable neighbour of the lantern may be left as a 1-wide cell
                pinch = False
                for ax_, az_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    for ay in (c[1] - 1, c[1], c[1] + 1):
                        n_ = (c[0] + ax_, ay, c[2] + az_)
                        if not (0 < ay < sy - 2 and 0 <= n_[0] < sx and 0 <= n_[2] < sz) or not stand[ay, n_[2], n_[0]]:
                            continue
                        more = False
                        for k in (1, 2):
                            q = (n_[0] + ax_ * k, n_[2] + az_ * k)
                            if 0 <= q[0] < sx and 0 <= q[1] < sz and any(stand[yy, q[1], q[0]] for yy in (ay - 1, ay, ay + 1)):
                                more = True
                        pinch |= not more
                if pinch:
                    continue
                score = (0 if against else 1) + dist
                if best is None or score < best[0]:
                    best = (score, c)
        if best:
            break
    return None if best is None else best[1]


def route_cues(name, grid: Grid, state, pal: Palette, markers, prov, log=print):
    """Places always-on route-cue fixtures (markers light.gate_trail_N / gate_lane_N / route_turn_N) and returns
    the guidance route for routes.json.  Fails the build when the tunnel light target is missed or when a cue
    breaks reachability."""
    states = pal.states
    region = core_region(name, grid)
    full, h, ends, stand, pas, seen = guidance_route(name, state, states, markers, region)
    route_set = set(full)
    marker_cells = [tuple(int(math.floor(v)) for v in m["pos"]) for m in markers]
    trans_tab, _ = light_tables(states)
    trans = trans_tab[state]
    names = [_base_name(s_) for s_ in states]
    full_ids = np.array([not trans_tab[i] and not n.endswith(("_slab", "_wall", "_stairs", "copper_bulb"))
                         and n not in ("snow", "barrier", "light") for i, n in enumerate(names)])
    is_full = full_ids[state]
    lantern = "minecraft:lantern[hanging=false,waterlogged=false]"
    bulb = "minecraft:waxed_exposed_copper_bulb[lit=true,powered=false]"
    added = []

    def add(kind, prefix, c, why, mount):
        y, z, x = c if kind == "bulb" else (c[1], c[2], c[0])
        state[y, z, x] = pal.id(bulb if kind == "bulb" else lantern)
        trans[y, z, x] = kind != "bulb"
        if kind == "bulb":
            is_full[y, z, x] = False
        n = sum(1 for m in markers if m["id"].startswith(prefix)) + 1
        tags = {"block": bulb if kind == "bulb" else lantern, "mount": mount, "level": "12" if kind == "bulb" else "15",
                "phase": "always"}
        if kind == "bulb":
            tags["unlit"] = bulb.replace("lit=true", "lit=false")
        markers.append(dict(id=f"{prefix}{n}", pos=[x + 0.5, y + 0.5, z + 0.5], yaw=0.0, tags=tags))
        prov.append((f"{prefix}{n}", "authored (r4): route cue — " + why, None))
        added.append((prefix, kind, (x, y, z)))

    # 1. Tunnel / dark leg: light the route after an objective to minimum/mean targets.
    t = CUE_TUNNEL.get(name)
    if t:
        i0 = next(i for i, m in ends.items() if m == t["after"])
        rmask = np.zeros(state.shape, bool)
        for x, y, z in full[i0:]:
            rmask[y, z, x] = True
        sky = sky_light(state, states); blk = block_light(state, states)
        before = np.maximum(blk, sky)[rmask]
        for _ in range(40):
            eff = np.maximum(blk, sky)
            if eff[rmask].min() >= t["minimum"] and eff[rmask].mean() >= t["mean"]:
                break
            rc = np.argwhere(rmask); dv = eff[rmask]
            worst = tuple(rc[np.lexsort((rc[:, 2], rc[:, 1], rc[:, 0], dv))[0]])
            best = None
            for c in _candidates(state, trans, is_full, worst, max_up=6, radius=3):
                sl, f = _local_field(trans, c, 12)
                gain = int((np.minimum(np.maximum(f, eff[sl]), 8) - np.minimum(eff[sl], 8))[rmask[sl]].sum())
                if best is None or gain > best[0]:
                    best = (gain, c)
            if best is not None and best[0] >= 20:
                c = best[1]; mount = "ceiling" if trans[c[0] - 1, c[1], c[2]] else "wall"
                add("bulb", "light.gate_trail_", c, "dark gate tunnel", mount)
                sl, f = _local_field(trans, c, 12)
            else:
                site = _lantern_site(state, stand, pas, route_set, marker_cells, (worst[2], worst[0], worst[1]))
                if site is None:
                    raise SystemExit(f"[{name}] cue: no fixture site near tunnel cell {worst}")
                add("lantern", "light.gate_trail_", site, "dark gate tunnel", "floor")
                stand[site[1], site[2], site[0]] = False
                sl, f = _local_field(trans, (site[1], site[2], site[0]), 15)
            np.maximum(blk[sl], f, out=blk[sl])
        eff = np.maximum(blk, sky)
        if eff[rmask].min() < t["minimum"] or eff[rmask].mean() < t["mean"]:
            raise SystemExit(f"[{name}] cue: tunnel light {eff[rmask].min()}/{eff[rmask].mean():.1f} below target")
        log(f"  tunnel cues: route light min/mean {int(before.min())}/{before.mean():.1f} -> "
            f"{int(eff[rmask].min())}/{eff[rmask].mean():.1f}")
    # 2. Lane breadcrumbs: floor lanterns along the jump-free lane before an objective.
    lc = CUE_LANE.get(name)
    if lc:
        i1 = next(i for i, m in ends.items() if m == lc["before"])
        for i in range(lc["spacing"] // 4, i1 - 6, lc["spacing"]):
            site = None
            for off in (0, -2, 2, -4, 4, -6, 6, -8, 8):
                if 0 <= i + off < i1:
                    site = _lantern_site(state, stand, pas, route_set, marker_cells, full[i + off])
                    if site is not None:
                        i += off; break
            if site is None:
                raise SystemExit(f"[{name}] lane cue: no clear site near step {i}")
            add("lantern", "light.gate_lane_", site, f"breadcrumb beside the jump-free lane (step {i})", "floor")
            stand[site[1], site[2], site[0]] = False
    # 3. Turn cues: where the straight Ghost trail toward the objective is hidden and the route turns away.
    tc = CUE_TURNS.get(name)
    if tc:
        ms = {m["id"]: m for m in markers}
        objective_at = []
        nxt = None
        for i in range(len(full) - 1, -1, -1):
            if i in ends and i != 0:
                nxt = ends[i]
            objective_at.append(nxt)
        objective_at = objective_at[::-1]
        scored = []
        for i in range(0, len(full) - 8):
            x, y, z = full[i]; tgt = ms[objective_at[i]]["pos"]
            e = np.array([x + 0.5, h[i] + 1.22, z + 0.5]); d = np.array(tgt, float) - e
            L = min(14.0, float(np.linalg.norm(d))); d = d / max(np.linalg.norm(d), 1e-6)
            ts = np.arange(1.5, L, 0.8)
            if not len(ts):
                continue
            b = np.floor(e[None] + ts[:, None] * d[None]).astype(int)
            b[:, 1] = b[:, 1].clip(0, state.shape[0] - 1)
            hidden = float((~pas[b[:, 1], b[:, 2], b[:, 0]]).mean())
            jx, _, jz = full[i + 8]
            bp = math.atan2(jz - z, jx - x); bt = math.atan2(d[2], d[0])
            dev = abs((math.degrees(bp - bt) + 180) % 360 - 180)
            if hidden >= 0.3 and dev >= 45:
                scored.append((i, dev, hidden))
        clusters = []
        for i, dev, hid in scored:
            if clusters and i - clusters[-1][-1][0] <= 6:
                clusters[-1].append((i, dev, hid))
            else:
                clusters.append([(i, dev, hid)])
        clusters.sort(key=lambda c: -(len(c) * max(v[1] for v in c)))
        for c in sorted(clusters[:tc["max"]], key=lambda c: c[0][0]):
            i = c[0][0]
            site = _lantern_site(state, stand, pas, route_set, marker_cells, full[i])
            if site is None:
                log(f"  turn cue: no site at step {i}"); continue
            add("lantern", "light.route_turn_", site,
                f"turn where the straight trail is hidden (step {i}, dev {max(v[1] for v in c):.0f} deg)", "floor")
            stand[site[1], site[2], site[0]] = False
        log(f"  turn candidates: {len(clusters)} clusters, placed {sum(1 for a in added if a[0] == 'light.route_turn_')}")
    # Re-validate: every walk-to marker reachable and the guidance route intact.
    stand2 = standable(state, states); pas2 = passable_mask(state, states)
    sp = full[0]; seen2 = reach(stand2, pas2, sp, region=region)
    for m in markers:
        if m["id"].startswith(("light.", "prop.", "ghost.")):
            continue
        x, y, z = (int(math.floor(v)) for v in m["pos"])
        if not seen2[y, z, x]:
            raise SystemExit(f"[{name}] cue broke reachability of {m['id']}")
    if any(not stand2[y, z, x] for x, y, z in full):
        raise SystemExit(f"[{name}] cue blocked the guidance route")
    idx = select_waypoints(full, ends.keys())
    jumps = {i for i in range(1, len(full)) if h[i] - h[i - 1] > 0.6}
    wps = []
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else i
        x, y, z = full[i]
        wps.append([x + 0.5, round(h[i], 1), z + 0.5, 1 if any(i < q <= j for q in jumps) else 0])
    obj_idx = {ends[i]: k for k, i in enumerate(idx) if i in ends}
    checks = check_route_objectives(name, wps, obj_idx, markers)
    _ROUTE_CACHE[name] = wps
    log(f"  guidance route: {len(full) - 1} steps, {len(jumps)} jumps, {len(wps)} waypoints; cues {len(added)}")
    return dict(steps=len(full) - 1, jumps=len(jumps), waypoints=len(wps), objective_checks=checks, cues=[(a, b, list(map(int, c))) for a, b, c in added])


def write_routes():
    path = OUT_DIR / "routes.json"
    doc = json.loads(path.read_text()) if path.exists() else {}
    doc["schema"] = 1
    doc["format"] = "zone-local [x, y, z, jump]; y = floor surface; jump=1 when a jump is needed before the next point"
    doc.setdefault("zones", {}).update(_ROUTE_CACHE)
    doc["zones"] = {k: doc["zones"][k] for k in sorted(doc["zones"])}
    body = ",\n".join(f' "{k}": [' + ",".join(json.dumps(w, separators=(",", ":")) for w in v) + "]"
                      for k, v in doc["zones"].items())
    path.write_text('{"schema":1,"format":' + json.dumps(doc["format"]) + ',"zones":{\n' + body + "\n}}\n")


# --------------------------------------------------------------------------------------------
# W300 r6: Skiff hover hints  (prop.skiff_<encounter>, read by SkiffDrop as the preferred hover point)
# Mirrors SkiffDrop.Sky: hull 7 x 5 x 7 (x/z +-3, y -2..+2) clear, open sky above y+3, and at least one
# ground unit's eye (feet + 1.6) sees the belly (hover - 2) along a quarter-block ray.  Collision follows
# SkiffZoneScanTest: everything except air / light / snow layers is solid.
# --------------------------------------------------------------------------------------------

SKIFF_HINTS = {"dock13": {"dock_defense": False, "dock_ship_west": True, "dock_ship_east": True},
               "breach": {"breach_corridor": False}}
SKIFF_HEIGHTS = (9, 7, 11, 5, 13, 15, 18, 22, 26, 30)
SKIFF_RADIUS, SKIFF_DROP_RADIUS, SKIFF_MAX_EYES = 24, 10.0, 8


def _skiff_riders(units):
    """SkiffDrop.Choice.dropped/ground: riders = ground units within 10 m of the densest unit, riders first."""
    ground = [u for u in units if u[1] not in ("shank", "walker")]
    if not ground:
        return [], []
    best, anchor = -1, ground[0]
    for a in ground:
        n = sum(1 for b in ground if math.hypot(a[0][0] - b[0][0], a[0][2] - b[0][2]) <= SKIFF_DROP_RADIUS)
        if n > best:
            best, anchor = n, a
    riders = [u for u in ground if math.hypot(u[0][0] - anchor[0][0], u[0][2] - anchor[0][2]) <= SKIFF_DROP_RADIUS]
    return riders, riders + [u for u in ground if u not in riders]


def skiff_hints(name, state, states, markers, prov, log=print):
    want = SKIFF_HINTS.get(name)
    if not want:
        return []
    names = [s_.split("[")[0] for s_ in states]
    solid_pal = np.array([n not in ("minecraft:air", "minecraft:light", "minecraft:snow") for n in names])
    solid = solid_pal[state]
    sy, sz, sx = state.shape
    top = np.where(solid.any(0), sy - 1 - np.argmax(solid[::-1], 0), -1)

    def is_solid(x, y, z):
        if not (0 <= x < sx and 0 <= z < sz) or y < 0 or y >= sy:
            return False   # outside the template the instance is empty
        return bool(solid[y, z, x])

    def sky(x, y, z):
        return not (0 <= x < sx and 0 <= z < sz) or y > top[z, x]

    def hull_clear(x, y, z):
        if not sky(x, y + 3, z):
            return False
        x0, x1, z0, z1 = max(x - 3, 0), min(x + 4, sx), max(z - 3, 0), min(z + 4, sz)
        y0, y1 = max(y - 2, 0), min(y + 3, sy)
        return y0 >= y1 or not solid[y0:y1, z0:z1, x0:x1].any()

    def visible(a, b):
        a = np.array(a); b = np.array(b); n = max(1, int(math.ceil(np.linalg.norm(b - a) * 4)))
        last = None
        for i in range(1, n):
            q = a + (b - a) * (i / n); c = (int(math.floor(q[0])), int(math.floor(q[1])), int(math.floor(q[2])))
            if c == last:
                continue
            last = c
            if is_solid(*c):
                return False
        return True

    out = []
    for enc, required in want.items():
        units = [(m["pos"], m["tags"]["kind"]) for m in markers if m["id"].startswith(f"enemy.{enc}.")]
        riders, ground = _skiff_riders(units)
        if len(riders) < 2:
            if required:
                raise SystemExit(f"[{name}] skiff hint {enc}: fewer than 2 riders")
            continue
        eyes = [(u[0][0], u[0][1] + 1.6, u[0][2]) for u in ground[:SKIFF_MAX_EYES]]
        ax = sum(u[0][0] for u in riders) / len(riders); az = sum(u[0][2] for u in riders) / len(riders)
        ay = min(u[0][1] for u in riders)
        best = None
        for dx in range(-SKIFF_RADIUS, SKIFF_RADIUS + 1):
            for dz in range(-SKIFF_RADIUS, SKIFF_RADIUS + 1):
                x, z = int(math.floor(ax)) + dx, int(math.floor(az)) + dz
                near = min(math.hypot(x + 0.5 - g[0][0], z + 0.5 - g[0][2]) for g in ground)
                if near > SKIFF_RADIUS:
                    continue
                for hi, h in enumerate(SKIFF_HEIGHTS):
                    y = int(math.floor(ay)) + h
                    if not hull_clear(x, y, z):
                        continue
                    belly = (x + 0.5, y - 2, z + 0.5)
                    seen = sum(1 for e in eyes if visible(e, belly))
                    if not seen:
                        continue
                    # most riders see it; then closest to the drop; then the preferred height order
                    key = (-seen, round(math.hypot(x + 0.5 - ax, z + 0.5 - az), 1), hi)
                    if best is None or key < best[0]:
                        best = (key, (x, y, z), seen)
                    break
        if best is None:
            if required:
                raise SystemExit(f"[{name}] skiff hint {enc}: no open-sky hover with a clear hull the riders can see")
            log(f"  skiff hint {enc}: none (runtime search decides)")
            continue
        (x, y, z), seen = best[1], best[2]
        mid = f"prop.skiff_{enc}"
        markers.append(dict(id=mid, pos=[x + 0.5, float(y), z + 0.5], yaw=0.0, tags={}))
        prov.append((mid, f"authored (r6): Skiff hover hint, open sky, 7x5x7 hull clear, seen by {seen}/{len(eyes)} "
                          f"ground units, {best[0][1]} m from the drop centroid", None))
        out.append(dict(encounter=enc, hover=[x + 0.5, y, z + 0.5], seen_by=seen, eyes=len(eyes),
                        offset=best[0][1], riders=len(riders)))
        log(f"  skiff hint {enc}: hover {x + 0.5},{y},{z + 0.5} seen {seen}/{len(eyes)} offset {best[0][1]} m")
    return out


def build_zone(name: str, log=print):
    spec = ZONES[name]
    t0 = time.time()
    glb = Glb(SRC / "maps_glb" / f"{spec['glb']}.textured.glb")
    lo, hi = spec.get("vista", spec["core"])
    grid = Grid(lo, hi, SCALE)
    log(f"[{name}] grid {grid.size} ({np.prod(grid.size) / 1e6:.1f}M cells), {len(glb.nodes)} instances")
    agg = voxelize(glb, grid, *spec["core"], *(spec["vista"] if "vista" in spec else (None, None)),
                   exclude=spec.get("exclude", ()), log=log)
    pal = Palette()
    labels, terr, rgb = classify(agg, pal)
    labels = majority_smooth(grid, agg.key, labels, iterations=1)
    state = shape_blocks(grid, agg, labels, terr, pal, log=log)
    state = apply_fixups(name, grid, state, pal, log=log)
    try:
        markers, prov, seen = place_markers(name, grid, state, pal.states, pal, log=log)
        add_boundary_barriers(name, grid, state, pal.states, pal, seen, log=log)
        rstats = route_cues(name, grid, state, pal, markers, prov, log=log)
        (EVIDENCE / "r6").mkdir(parents=True, exist_ok=True)
        (EVIDENCE / "r6" / f"route_{name}.json").write_text(json.dumps(rstats, indent=1))
        lstats = lighting_pass(name, grid, state, pal, seen, markers, prov, log=log)
        (EVIDENCE / "r2").mkdir(parents=True, exist_ok=True)
        (EVIDENCE / "r2" / f"light_{name}.json").write_text(json.dumps(lstats, indent=1, default=str))
        hints = skiff_hints(name, state, pal.states, markers, prov, log=log)
        (EVIDENCE / "r6").mkdir(parents=True, exist_ok=True)
        (EVIDENCE / "r6" / f"skiff_{name}.json").write_text(json.dumps(hints, indent=1))
    except SystemExit as e:
        if not os.environ.get("RISING_LENIENT"):
            raise
        log(f"  !! markers skipped (lenient): {e}"); markers, prov = [], []
    np.save(CACHE_DIR / f"state_{name}.npy", state)
    (CACHE_DIR / f"states_{name}.json").write_text(json.dumps(pal.states))
    write_markers(name, grid, markers, prov)
    info = write_zone(OUT_DIR / f"{name}.zone", state, pal.states)
    log(f"[{name}] wrote {info} in {time.time() - t0:.1f}s")
    ev = EVIDENCE / "renders"
    render_top(state, pal.states, ev / f"{name}_top.png")
    return grid, state, pal


def _argv():
    a = sys.argv
    return a[a.index("--") + 1:] if "--" in a else a[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--zone", default="all")
    ap.add_argument("--glb")
    ap.add_argument("--box", type=float, nargs=6)
    ap.add_argument("--res", type=float, default=1.0)
    ap.add_argument("--out")
    args = ap.parse_args(_argv())
    if args.cmd == "survey":
        b = args.box
        bubble = {"the_breach": "The Breach", "the_divide": "The Divide", "dock_13": "Dock 13",
                  "gateway": "Gateway"}.get(args.glb)
        marks = [(p[0], p[1], ANCHOR_COLOURS.get(n, (0, 255, 0))) for n, k, ph, p, y in source_anchors()]
        survey(args.glb, b[0:3], b[3:6], args.res, Path(args.out), marks)
    elif args.cmd == "srcview":
        for n in (list(ZONES) if args.zone == "all" else args.zone.split(",")):
            render_source_views(n)
    elif args.cmd == "voxview":
        for n in (list(ZONES) if args.zone == "all" else args.zone.split(",")):
            lo, hi = ZONES[n].get("vista", ZONES[n]["core"])
            st = np.load(CACHE_DIR / f"state_{n}.npy"); sts = json.loads((CACHE_DIR / f"states_{n}.json").read_text())
            render_voxel_views(n, Grid(lo, hi, SCALE), st, sts)
    elif args.cmd == "montage":
        for n in (list(ZONES) if args.zone == "all" else args.zone.split(",")):
            rows = []
            for view in ZONES[n].get("views", []):
                pair = []
                for kind in ("src", "vox"):
                    f = EVIDENCE / "renders" / f"{n}_{view[0]}_{kind}.png"
                    pair.append((_load_full_texture(f)[..., :3] * 255).astype(np.uint8) if f.exists()
                                else np.zeros((270, 480, 3), np.uint8))
                rows.append(np.concatenate([pair[0], np.full((270, 6, 3), 255, np.uint8), pair[1]], 1))
                rows.append(np.full((6, rows[-1].shape[1], 3), 255, np.uint8))
            png_write(EVIDENCE / "renders" / f"{n}_compare.png", np.concatenate(rows, 0))
    elif args.cmd == "analyze":
        for n in (list(ZONES) if args.zone == "all" else args.zone.split(",")):
            analyze_zone(n)
    elif args.cmd == "routes":
        export_routes(list(ZONES) if args.zone == "all" else args.zone.split(","))
    elif args.cmd == "build":
        names = list(ZONES) if args.zone == "all" else args.zone.split(",")
        for n in names:
            build_zone(n)
        write_routes()
    else:
        raise SystemExit(f"unknown command {args.cmd}")


if __name__ == "__main__":
    main()
