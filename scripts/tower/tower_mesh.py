"""Minimal read-only glTF 2 GLB scene reader; numpy/Pillow only, no Blender axis conversion.

Accessors remain local to each shared mesh. world_instances composes each node's
matrix/TRS with its ancestors exactly once. Distant AABBs can be culled without
loading positions, indices, or external textures.
"""
from __future__ import annotations
import base64
import io
import json
import struct
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote
import numpy as np
from PIL import Image

DTYPES = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def node_matrix(node):
    if "matrix" in node:
        return np.asarray(node["matrix"], dtype=np.float64).reshape(4, 4, order="F")
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    norm = np.linalg.norm([x, y, z, w])
    if norm == 0:
        raise ValueError("zero glTF quaternion")
    x, y, z, w = np.asarray([x, y, z, w]) / norm
    rot = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                    [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                    [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    out = np.eye(4)
    out[:3, :3] = rot @ np.diag(node.get("scale", [1, 1, 1]))
    out[:3, 3] = node.get("translation", [0, 0, 0])
    return out


def transform_bounds(lo, hi, matrix):
    corners = np.array([[x, y, z] for x in (lo[0], hi[0])
                        for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    points = corners @ matrix[:3, :3].T + matrix[:3, 3]
    return points.min(axis=0), points.max(axis=0)


def overlaps(lo, hi, crop_min, crop_max):
    return bool(np.all(hi >= crop_min) and np.all(lo < crop_max))


class GLB:
    def __init__(self, path):
        self.path = Path(path)
        self.binary = b""
        with self.path.open("rb") as f:
            magic, version, length = struct.unpack("<4sII", f.read(12))
            if magic != b"glTF" or version != 2 or length != self.path.stat().st_size:
                raise ValueError("invalid GLB 2 header")
            while f.tell() < length:
                size, kind = struct.unpack("<II", f.read(8))
                chunk = f.read(size)
                if len(chunk) != size:
                    raise ValueError("truncated GLB chunk")
                if kind == 0x4E4F534A:
                    self.doc = json.loads(chunk)
                elif kind == 0x004E4942:
                    self.binary = chunk
        required = self.doc.get("extensionsRequired", [])
        unsupported = set(required) - {"KHR_texture_transform"}
        if unsupported:
            raise ValueError(f"unsupported required extensions: {unsupported}")
        if any(n.get("skin") is not None for n in self.doc.get("nodes", [])):
            raise ValueError("skinned scenes are not supported")

    def uri_bytes(self, uri):
        if uri.startswith("data:"):
            header, data = uri.split(",", 1)
            if ";base64" not in header:
                raise ValueError("non-base64 data URI unsupported")
            return base64.b64decode(data)
        if "://" in uri:
            raise ValueError("network asset URIs are unsupported")
        return (self.path.parent / unquote(uri)).read_bytes()

    @lru_cache(maxsize=4)
    def buffer(self, index):
        desc = self.doc["buffers"][index]
        return self.uri_bytes(desc["uri"]) if "uri" in desc else self.binary

    @lru_cache(maxsize=128)
    def accessor(self, index):
        acc = self.doc["accessors"][index]
        if "sparse" in acc:
            raise ValueError("sparse accessors unsupported")
        width = WIDTHS[acc["type"]]
        dtype = np.dtype(DTYPES[acc["componentType"]])
        if "bufferView" not in acc:
            result = np.zeros((acc["count"], width), dtype=dtype)
        else:
            view = self.doc["bufferViews"][acc["bufferView"]]
            result = np.ndarray((acc["count"], width), dtype=dtype,
                                buffer=self.buffer(view.get("buffer", 0)),
                                offset=view.get("byteOffset", 0) + acc.get("byteOffset", 0),
                                strides=(view.get("byteStride", width*dtype.itemsize), dtype.itemsize))
        if acc.get("normalized") and dtype.kind in "iu":
            result = result.astype(np.float64) / np.iinfo(dtype).max
            if dtype.kind == "i":
                result = np.maximum(result, -1)
        return result[:, 0] if width == 1 else result

    def primitive_bounds(self, primitive):
        index = primitive["attributes"]["POSITION"]
        acc = self.doc["accessors"][index]
        if "min" in acc and "max" in acc:
            return np.array(acc["min"]), np.array(acc["max"])
        points = self.accessor(index)
        return points.min(axis=0), points.max(axis=0)

    @lru_cache(maxsize=2048)
    def mesh_bounds(self, index):
        bounds = [self.primitive_bounds(p) for p in self.doc["meshes"][index]["primitives"]]
        return np.min([b[0] for b in bounds], axis=0), np.max([b[1] for b in bounds], axis=0)

    def world_instances(self):
        scene = self.doc.get("scene", 0)
        roots = self.doc["scenes"][scene]["nodes"]
        stack = [(idx, np.eye(4), frozenset()) for idx in reversed(roots)]
        while stack:
            index, parent, ancestors = stack.pop()
            if index in ancestors:
                raise ValueError("cycle in scene graph")
            node = self.doc["nodes"][index]
            world = parent @ node_matrix(node)
            if "mesh" in node:
                yield index, node["mesh"], world
            for child in reversed(node.get("children", [])):
                stack.append((child, world, ancestors | {index}))

    @lru_cache(maxsize=16)
    def image(self, index, max_size=256):
        desc = self.doc["images"][index]
        if "uri" in desc:
            raw = self.uri_bytes(desc["uri"])
        else:
            view = self.doc["bufferViews"][desc["bufferView"]]
            start = view.get("byteOffset", 0)
            raw = self.buffer(view.get("buffer", 0))[start:start+view["byteLength"]]
        with Image.open(io.BytesIO(raw)) as im:
            im = im.convert("RGBA")
            im.thumbnail((max_size, max_size), Image.Resampling.BOX)
            return np.asarray(im).copy()

    def texture(self, texture_index):
        desc = self.doc["textures"][texture_index]
        sampler = self.doc.get("samplers", [])[desc["sampler"]] if "sampler" in desc else {}
        return self.image(desc["source"]), sampler
