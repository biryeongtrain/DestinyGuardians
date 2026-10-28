#!/usr/bin/env python3
"""Original W223 split-X glyphs. Stdlib only; writes exactly six owned assets + manifest.
Run from any cwd. --check validates byte-for-byte reproducibility without writing files.
No downloaded, extracted, or traced Destiny pixels are inputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
SIZE, SAMPLES = 64, 4
GLYPHS = {
    "hit_confirmation_w223": [(8, 8), (9.5, 7.5), (16, 14), (14, 16), (7.5, 9.5)],
    "kill_confirmation_w223": [(9, 9), (11, 8), (20, 17), (17, 20), (8, 11)],
}


def inside(x, y, polygon):
    result = False
    previous = polygon[-1]
    for current in polygon:
        ax, ay = previous
        bx, by = current
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            result = not result
        previous = current
    return result


def pixels(polygon):
    # Reflect one authored tapered stroke into all four quadrants; never fill the aim point.
    shapes = [[(SIZE / 2 + sx * x, SIZE / 2 + sy * y) for x, y in polygon]
              for sx in (-1, 1) for sy in (-1, 1)]
    output = bytearray()
    for y in range(SIZE):
        for x in range(SIZE):
            covered = sum(any(inside(x + (dx + .5) / SAMPLES,
                                     y + (dy + .5) / SAMPLES, shape) for shape in shapes)
                          for dy in range(SAMPLES) for dx in range(SAMPLES))
            alpha = (covered * 255 + SAMPLES * SAMPLES // 2) // (SAMPLES * SAMPLES)
            output.extend((255, 255, 255, alpha))
    return bytes(output)


def png(rgba):
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))
    rows = b"".join(b"\0" + rgba[y * SIZE * 4:(y + 1) * SIZE * 4] for y in range(SIZE))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def outputs():
    generated = {}
    glyph_metadata = []
    for name, polygon in GLYPHS.items():
        rgba = pixels(polygon)
        # Fully transparent 14x14 square around the exact center in both sprites.
        assert all(rgba[(y * SIZE + x) * 4 + 3] == 0 for y in range(25, 39) for x in range(25, 39))
        assert any(rgba[i] == 255 for i in range(3, len(rgba), 4))
        item = {"model": {"type": "minecraft:model", "model": "destiny:gui/hud/" + name,
                           "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}
        face = {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
        model = {"gui_light": "front", "textures": {"0": "destiny:item/hud/" + name},
                 "elements": [{"from": [0, 0, 8], "to": [16, 16, 8],
                               "faces": {"north": dict(face), "south": dict(face)}}]}
        base = "src/main/resources/assets/destiny/"
        generated[base + "items/gui/hud/" + name + ".json"] = json_bytes(item)
        generated[base + "models/gui/hud/" + name + ".json"] = json_bytes(model)
        generated[base + "textures/item/hud/" + name + ".png"] = png(rgba)
        alpha = [rgba[i] for i in range(3, len(rgba), 4)]
        glyph_metadata.append({"name": name, "size": [SIZE, SIZE], "rgba": True,
                               "nontransparent_pixels": sum(a > 0 for a in alpha),
                               "opaque_pixels": sum(a == 255 for a in alpha),
                               "guaranteed_transparent_center_square": [25, 25, 39, 39],
                               "authored_quadrant_polygon": polygon})
    manifest = {
        "schema": 1, "generator": "scripts/generate_hit_confirmation_w223.py",
        "provenance": "Original procedural split-X approximation; no extracted or traced game pixels.",
        "source_notes": "art/hud/w223/SOURCE.md", "supersampling": SAMPLES,
        "hud": {"prefix": "destiny:hit_confirmation_w223_", "max_nodes": 1,
                "anchor": [960, 540], "plane_size": [64, 64], "layer": 8,
                "hit_tint": "#F1F3F5", "kill_tint": "#E85C50", "hit_ticks": 4, "kill_ticks": 7,
                "timing_and_dimensions": "Authored tuning, not measured Destiny constants",
                "precision_color": None},
        "glyphs": glyph_metadata,
        "assets": [{"path": path, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                   for path, data in sorted(generated.items())],
    }
    generated["art/hud/w223/manifest.json"] = json_bytes(manifest)
    return generated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    if args.check:
        drift = [path for path, data in generated.items()
                 if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != data]
        if drift:
            raise SystemExit("W223 generated drift: " + ", ".join(drift))
        print("W223: 6 assets + manifest reproducible; transparent centers validated")
    else:
        for path, data in generated.items():
            target = ROOT / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        print("W223: generated exactly 6 owned assets + manifest")


if __name__ == "__main__":
    main()
