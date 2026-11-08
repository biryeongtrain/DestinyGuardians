#!/usr/bin/env python3
"""Generates the launch loading screen's bitmap font sheets (no third-party imports).

assets/destiny/textures/font/loading_spinner.png : 12 frames of a 16x16 orbiting-dot ring (U+E500..E50B)
assets/destiny/textures/font/loading_bar.png     : 8x8 bar cells, empty / 1..4 of 5 columns / full / head (U+E510..E516)
Re-run after editing; the font definition is assets/destiny/font/loading_ui.json.
"""
import math, struct, zlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2] / "src/main/resources/assets/destiny/textures/font"


def png(path, width, height, pixels):
    raw = b"".join(b"\x00" + bytes(v for px in pixels[y * width:(y + 1) * width] for v in px) for y in range(height))
    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def spinner():
    frames, size, dots, radius = 12, 16, 12, 6.0
    img = [(0, 0, 0, 0)] * (size * frames * size)
    for f in range(frames):
        for i in range(dots):
            age = (f - i) % dots              # 0 = head, larger = older
            alpha = 255 if age == 0 else max(34, int(235 - age * 24)) if age < 8 else 34
            a = math.radians(i * 30 - 90)
            cx, cy = 8 + radius * math.cos(a), 8 + radius * math.sin(a)
            x0, y0 = int(round(cx - 1)), int(round(cy - 1))
            for dx in range(2):
                for dy in range(2):
                    x, y = f * size + x0 + dx, y0 + dy
                    img[y * size * frames + x] = (236, 239, 243, alpha)
    png(ROOT / "loading_spinner.png", size * frames, size, img)


def bar():
    cells, w = 7, 8
    img = [(0, 0, 0, 0)] * (w * cells * w)
    track, fill, head = (62, 67, 75, 255), (236, 239, 243, 255), (227, 196, 107, 255)
    for c in range(cells):
        for col in range(5):                # column 5..7 stay transparent: the gap between segments
            for row in range(3, 5 + 1):     # a 3px tall line
                if c == 0: colour = track
                elif c <= 4: colour = fill if col < c else track
                elif c == 5: colour = fill
                else: colour = head
                img[row * w * cells + c * w + col] = colour
    png(ROOT / "loading_bar.png", w * cells, w, img)


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    spinner(); bar()
    print("wrote", ROOT)
