"""Read delivered unlit color-bake GLBs in their pre-root, Z-up source space.

The existing source sampler consumes Z-up; it deliberately ignores the single
glTF display-root axis conversion. Nonindexed triangles and bake coverage are
handled here rather than treating bake-mask RGB as an ordinary tiled texture.
"""
from functools import lru_cache
import json, struct
from pathlib import Path
import numpy as np


def load(path, sampler):
    class BakedGlb(sampler.Glb):
        def __init__(self, path):
            self.path = Path(path)
            with self.path.open('rb') as f:
                magic, version, length = struct.unpack('<III', f.read(12))
                if magic != 0x46546c67 or version != 2:
                    raise ValueError('Expected a glTF 2 GLB')
                size, kind = struct.unpack('<II', f.read(8)); self.j = json.loads(f.read(size))
                size, kind = struct.unpack('<II', f.read(8)); self.bin = f.read(size)
            root = self.j['scenes'][0]['nodes'][0]
            self.nodes = [self.j['nodes'][i] for i in self.j['nodes'][root]['children']]
            self.layout = {}; self._mesh_cache = {}; boxes = []; self.inst_mat = []
            for n in self.nodes:
                lo, hi = self.mesh_bounds(n['mesh']); matrix = self.node_matrix(n)
                corners = np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
                w = corners @ matrix[:3,:3].T + matrix[:3,3]
                boxes.append((w.min(0),w.max(0))); self.inst_mat.append(matrix)
            self.inst_min = np.array([b[0] for b in boxes]); self.inst_max = np.array([b[1] for b in boxes])

        def primitives(self, mi):
            if mi not in self._mesh_cache:
                out = []
                for p in self.j['meshes'][mi]['primitives']:
                    mat = p.get('material', -1)
                    extra = self.j['materials'][mat].get('extras', {}) if mat >= 0 else {}
                    # Scene-default albedo is retained with explicit uncertainty;
                    # forward/decal and clipped-out layers are never collision.
                    if extra.get('colorBakeQuality') not in ('native_full_inputs', 'native_shader_scene_defaults'):
                        continue
                    pos = self.accessor(p['attributes']['POSITION']).astype(np.float64)
                    uv = self.accessor(p['attributes']['TEXCOORD_0']).astype(np.float32)
                    idx = self.accessor(p['indices']) if 'indices' in p else np.arange(len(pos))
                    out.append((pos, uv, idx.reshape(-1, 3), mat))
                self._mesh_cache[mi] = out
            return self._mesh_cache[mi]
    return BakedGlb(path)


def srgb_to_linear(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    return np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055)


@lru_cache(maxsize=24)
def image_rgba(path):
    from PIL import Image
    return np.asarray(Image.open(path).convert('RGBA'))


def sample_instance(glb, inst, lo, hi, step, sampler, max_samples=1_000_000):
    """Return linear-RGB surface samples, rejecting bake coverage below 0.5."""
    n = glb.nodes[inst]; m = glb.inst_mat[inst]
    points, colors, normals = [], [], []
    for pos, uv, idx, mat in glb.primitives(n['mesh']):
        w = pos @ m[:3, :3].T + m[:3, 3]
        tri = w[idx]
        keep = np.all(tri.max(1) >= lo, 1) & np.all(tri.min(1) <= hi, 1)
        if not keep.any():
            continue
        tri = tri[keep]; tuv = uv[idx[keep]]
        edge = np.maximum.reduce([np.linalg.norm(tri[:, a] - tri[:, b], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))])
        steps = np.clip(np.ceil(edge / step).astype(int), 1, 600)
        cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nz = cross[:, 2] / np.maximum(np.linalg.norm(cross, axis=1), 1e-12)
        tex = image_rgba(str((glb.path.parent / glb.material_texture(mat)).resolve()))
        for st in np.unique(steps):
            sel = np.flatnonzero(steps == st); bary = sampler.bary_grid(int(st))
            for off in range(0, len(sel), max(1, max_samples // len(bary))):
                ids = sel[off:off + max(1, max_samples // len(bary))]
                u, v = bary[:, 0][None, :, None], bary[:, 1][None, :, None]
                t, tu = tri[ids], tuv[ids]
                p = (t[:, :1] * (1-u-v) + t[:, 1:2]*u + t[:, 2:3]*v).reshape(-1, 3)
                q = (tu[:, :1] * (1-u-v) + tu[:, 1:2]*u + tu[:, 2:3]*v).reshape(-1, 2)
                inside = np.all((p >= lo) & (p <= hi), axis=1)
                if not inside.any():
                    continue
                p, q = p[inside], q[inside]
                # Delivered UVs already use top-left PNG origin. Clamp baked
                # islands at the image edge rather than wrapping them.
                tx = np.clip((q[:, 0]*tex.shape[1]).astype(int), 0, tex.shape[1]-1)
                ty = np.clip((q[:, 1]*tex.shape[0]).astype(int), 0, tex.shape[0]-1)
                col = tex[ty, tx].astype(np.float32)/255
                visible = col[:, 3] >= .5
                if not visible.any():
                    continue
                col = col[visible]; col[:, :3] = srgb_to_linear(col[:, :3])
                points.append(p[visible]); colors.append(col)
                normals.append(np.repeat(nz[ids], len(bary))[inside][visible].astype(np.float32))
    if not points:
        return None
    return np.concatenate(points), np.concatenate(colors), np.concatenate(normals)
