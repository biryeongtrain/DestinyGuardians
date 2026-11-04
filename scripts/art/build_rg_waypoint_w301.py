"""W301: Destiny-style objective waypoint glyph (font destiny:rg_waypoint, char U+E300).

A hollow diamond with a solid inner diamond and a short drop line, white (tinted by the text colour).
Run: python scripts/art/build_rg_waypoint_w301.py
"""
import os
from PIL import Image, ImageChops, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "main", "resources",
                   "assets", "destiny", "textures", "font", "rg_waypoint.png")
SS, N = 8, 64


def diamond(draw, cx, cy, r, fill):
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def main():
    big = N * SS
    m = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(m)
    c = big / 2
    diamond(d, c, c - 4 * SS, 26 * SS, 255)
    hole = Image.new("L", (big, big), 0)
    diamond(ImageDraw.Draw(hole), c, c - 4 * SS, 20 * SS, 255)
    m = ImageChops.subtract(m, hole)
    d = ImageDraw.Draw(m)
    diamond(d, c, c - 4 * SS, 9 * SS, 255)
    d.rectangle([c - 1.5 * SS, c + 24 * SS, c + 1.5 * SS, c + 31 * SS], fill=255)
    a = m.resize((N, N), Image.LANCZOS)
    out = Image.new("RGBA", (N, N), (255, 255, 255, 0))
    out.putalpha(a)
    out.save(OUT, optimize=True)


if __name__ == "__main__":
    main()
