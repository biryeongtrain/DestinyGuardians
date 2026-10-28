#!/usr/bin/env python3
"""Render a bundled tower voxel map without loading Minecraft or the source GLB."""
import argparse
import gzip
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def read_map(path):
    data = memoryview(gzip.decompress(Path(path).read_bytes()))
    if data[:8] != b"DGTWR001":
        raise ValueError("Unsupported tower map")
    offset = 8
    count, = struct.unpack_from(">i", data, offset)
    offset += 4
    palette = []
    for _ in range(count):
        length, = struct.unpack_from(">H", data, offset)
        offset += 2
        palette.append(bytes(data[offset:offset + length]).decode())
        offset += length
    count, = struct.unpack_from(">i", data, offset)
    offset += 4
    dtype = np.dtype([("x", ">i4"), ("y", ">i4"), ("z", ">i4"), ("p", ">u2")])
    if len(data) - offset != count * dtype.itemsize:
        raise ValueError("Invalid voxel payload size")
    records = np.frombuffer(data[offset:], dtype=dtype)
    return palette, records


COLORS = {
    "white": (207, 211, 213), "light_gray": (151, 151, 143),
    "gray": (75, 79, 81), "black": (28, 31, 34),
    "brown": (110, 80, 55), "red": (151, 46, 42),
    "orange": (208, 114, 45), "yellow": (225, 184, 64),
    "lime": (107, 143, 45), "green": (69, 96, 43),
    "cyan": (53, 113, 122), "light_blue": (93, 161, 202),
    "blue": (52, 65, 137), "purple": (115, 66, 151),
    "magenta": (162, 74, 151), "pink": (207, 133, 151),
}


def block_color(name):
    short = name.split(":")[-1].split("[")[0]
    for color in sorted(COLORS, key=len, reverse=True):
        if short.startswith(color + "_"):
            return COLORS[color]
    if "leaves" in short or "moss" in short:
        return (75, 112, 48)
    if "quartz" in short or "calcite" in short:
        return (221, 216, 200)
    if "iron" in short:
        return (190, 193, 190)
    if "deepslate" in short:
        return (65, 66, 68)
    if "stone" in short or "andesite" in short:
        return (128, 130, 126)
    if "sand" in short:
        return (208, 195, 148)
    if "wood" in short or "log" in short or "planks" in short:
        return (112, 88, 60)
    if "glass" in short:
        return (142, 175, 181)
    return (130, 128, 117)


def render(path, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    palette, rec = read_map(path)
    xyz = np.column_stack([rec[k] for k in ("x", "y", "z")]).astype(np.int32)
    lo, hi = xyz.min(0), xyz.max(0)
    colors = np.array([block_color(p) for p in palette], dtype=np.uint8)
    # Slice away overhead structures to expose the navigable courtyard underneath.
    for name, ceiling in (("top", int(hi[1])), ("walkways", 82)):
        take = xyz[:, 1] <= ceiling
        points, indices = xyz[take], rec["p"][take]
        order = np.argsort(points[:, 1], kind="stable")
        points, indices = points[order], indices[order]
        w, h = int(hi[0] - lo[0] + 1), int(hi[2] - lo[2] + 1)
        pixels = np.full((h, w, 3), [26, 35, 48], dtype=np.uint8)
        # Last write in ascending Y selects the highest block in each column.
        flat = (points[:, 2] - lo[2]) * w + points[:, 0] - lo[0]
        _, reverse_indices = np.unique(flat[::-1], return_index=True)
        selected = len(flat) - 1 - reverse_indices
        pixels.reshape(-1, 3)[flat[selected]] = colors[indices[selected]]
        im = Image.fromarray(pixels).resize((w * 3, h * 3), Image.Resampling.NEAREST)
        draw = ImageDraw.Draw(im)
        draw.rectangle((0, 0, min(w * 3, 620), 28), fill=(15, 21, 30))
        draw.text((8, 8), f"Tower W232 | {name} | x+ right, z+ down | ceiling Y={ceiling}", fill="white")
        im.save(output / (name + ".png"))
    report = {"blocks": len(rec), "palette": palette, "bounds": [lo.tolist(), hi.tolist()]}
    (output / "preview.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    print(json.dumps(render(args.input, args.output), indent=2))
