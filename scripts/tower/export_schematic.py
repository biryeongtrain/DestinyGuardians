"""DGTWR001 bundle and Sponge v2 schematic output, using a small pure Python NBT writer."""
from __future__ import annotations
import gzip
import struct
from pathlib import Path
import numpy as np

MAGIC = b"DGTWR001"
RECORD = np.dtype([("x", ">i4"), ("y", ">i4"), ("z", ">i4"), ("palette", ">u2")])


def write_vox(path, coordinates, indices, palette):
    if len(palette) > 65536 or len(coordinates) > 2147483647:
        raise ValueError("bundle exceeds DGTWR001 limits")
    if len(coordinates) != len(indices) or (len(indices) and (min(indices) < 0 or max(indices) >= len(palette))):
        raise ValueError("invalid voxel palette indices")
    if any(s in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air") for s in palette):
        raise ValueError("bundle palette must not include air")
    path = Path(path)
    with path.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as f:
        f.write(MAGIC)
        f.write(struct.pack(">i", len(palette)))
        for state in palette:
            encoded = state.encode("utf-8")
            f.write(struct.pack(">H", len(encoded)))
            f.write(encoded)
        f.write(struct.pack(">i", len(coordinates)))
        for start in range(0, len(coordinates), 65536):
            xyz = coordinates[start:start+65536]
            records = np.empty(len(xyz), dtype=RECORD)
            for dim, key in enumerate(("x", "y", "z")):
                records[key] = xyz[:, dim]
            records["palette"] = indices[start:start+65536]
            f.write(records.tobytes())


def read_vox(path):
    with gzip.open(path, "rb") as f:
        if f.read(8) != MAGIC:
            raise ValueError("invalid DGTWR001 magic")
        count, = struct.unpack(">i", f.read(4))
        if not 0 <= count <= 65536:
            raise ValueError("invalid palette count")
        palette = []
        for _ in range(count):
            size, = struct.unpack(">H", f.read(2))
            palette.append(f.read(size).decode("utf-8"))
        count, = struct.unpack(">i", f.read(4))
        if count < 0:
            raise ValueError("invalid voxel count")
        payload = f.read()
        if len(payload) != count * RECORD.itemsize:
            raise ValueError("invalid record payload length")
        records = np.frombuffer(payload, dtype=RECORD)
        indices = records["palette"].astype(np.uint16)
        if len(indices) and np.max(indices) >= len(palette):
            raise ValueError("palette index outside palette")
        xyz = np.column_stack([records[k] for k in ("x", "y", "z")]).astype(np.int32)
        return xyz, indices, palette


def _string(value):
    data = value.encode("utf-8")
    return struct.pack(">H", len(data)) + data


def _tag(kind, name, payload):
    return bytes([kind]) + _string(name) + payload


def _int(name, value):
    return _tag(3, name, struct.pack(">i", int(value)))


def _compound(name, children):
    return _tag(10, name, b"".join(children) + b"\0")


def write_schematic(path, coordinates, indices, palette, data_version=3955, max_cells=128_000_000):
    """Sponge v2, x fastest then z then y, with explicit air and WorldEdit origin.

    DataVersion defaults to Java 1.21 (3955): the portable palette contains only
    blocks already available there. Override to match a specific target version.
    """
    if not len(coordinates):
        raise ValueError("cannot export an empty schematic")
    lo, hi = coordinates.min(axis=0), coordinates.max(axis=0)
    dims = hi.astype(np.int64) - lo + 1
    if np.any(dims > 32767) or np.prod(dims) > max_cells:
        raise ValueError("schematic dimensions exceed configured limits")
    width, height, length = map(int, dims)
    dense = np.zeros(width*height*length, dtype=np.uint32)
    local = coordinates.astype(np.int64) - lo
    flat = local[:, 0] + width*(local[:, 2] + length*local[:, 1])
    dense[flat] = indices.astype(np.uint32) + 1
    # Encode each unsigned palette ID as a VarInt, including IDs >=128.
    parts = []
    for start in range(0, len(dense), 262144):
        values = dense[start:start+262144].copy()
        layers = max(1, (int(values.max()).bit_length()+6)//7)
        encoded = np.zeros((len(values), layers), dtype=np.uint8)
        valid = np.zeros_like(encoded, dtype=bool)
        for level in range(layers):
            valid[:, level] = True if level == 0 else values > 0
            encoded[:, level] = (values & 127) | np.where(values >= 128, 128, 0)
            values >>= 7
        parts.append(encoded[valid].tobytes())
    data = b"".join(parts)
    states = ["minecraft:air"] + list(palette)
    children = [_int("Version", 2), _int("DataVersion", data_version),
                _tag(2, "Width", struct.pack(">h", width)),
                _tag(2, "Height", struct.pack(">h", height)),
                _tag(2, "Length", struct.pack(">h", length)),
                _tag(11, "Offset", struct.pack(">i3i", 3, *map(int, lo))),
                _int("PaletteMax", len(states)),
                _compound("Palette", [_int(state, i) for i, state in enumerate(states)]),
                _tag(7, "BlockData", struct.pack(">i", len(data)) + data),
                _tag(9, "BlockEntities", struct.pack(">bi", 10, 0)),
                _compound("Metadata", [_int("WEOffsetX", lo[0]), _int("WEOffsetY", lo[1]),
                                       _int("WEOffsetZ", lo[2])])]
    payload = _compound("Schematic", children)
    with Path(path).open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as f:
        f.write(payload)
    return {"version": 2, "dataVersion": data_version, "dimensions": dims.tolist(),
            "origin": lo.tolist(), "airCells": int(len(dense)-len(coordinates))}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="courtyard.vox.gz")
    parser.add_argument("output", type=Path, help="portable Sponge .schem")
    parser.add_argument("--data-version", type=int, default=3955)
    args = parser.parse_args()
    write_schematic(args.output, *read_vox(args.input), data_version=args.data_version)
