"""W300 r5: port D2 Fallen VFX texture surfaces into Polymer item-model sprites (read-only source).

Each sprite is the first-surface PNG preview of a D2 particle texture (Rising-Guardian-Fallen-AV extract),
converted to a WHITE sprite whose alpha is the source luminance (times source alpha), with a soft radial/edge
fade so quads never show a hard square. Colour is applied in-game through the item model's custom_model_data
tint, so one sprite serves every weapon colour. D2 shader stages (scrolling, erosion, HDR blend) are NOT
reproduced; this is a texture-surface port. Pure Python (zlib PNG codec), deterministic output.

Run: python3 scripts/campaign/fallen_vfx.py
"""
import csv, hashlib, json, struct, sys, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = Path("/Users/qf/Downloads/Rising-Guardian-Fallen-AV-2026-11-01/Rising-Guardian-Fallen-AV-2026-11-01")
A = ROOT / "src/main/resources/assets/destiny"
TABLE = ROOT / "src/main/resources/destiny/guardian_rises/fallen_vfx.json"

# name: (texture tag, size, shape, gain, gamma, source particles/sequences, role)
# shape: "quad" camera-facing plane, "beam" two crossed planes along +Z.
SPRITES = {
    "glow":         ("80D8A448", 64, "quad", 1.15, 1.0, ["80CEA1D8@80CEA1DB", "80A6DB04@80A6DB1C", "80A5ABFB@80A5AC46", "80A5AFC8@80A5AFDB"],
                     "soft light: shock-pistol light flash, shrapnel glow, Walker EMP flash, weakpoint bright_flash"),
    "energy_ring":  ("80D8D777", 128, "quad", 1.35, .9, ["80CEA1BE@80CEA1DB", "80A5A2B8@80A5A2D7 (ring)"],
                     "shock-pistol muzzle burst; Walker cannon muzzle ring; shield pop"),
    "flash_star":   ("80D8A430", 64, "quad", 1.2, 1.0, ["80CEA676@80CEA54B (flash_round)"], "wire-rifle round flash"),
    "flash_jet":    ("80D899BF", 64, "quad", 1.2, 1.0, ["80CEA693@80CEA54B (flash_long)"], "wire-rifle long flash"),
    "burst_star":   ("80D8A2AB", 64, "quad", 1.2, 1.0, ["80CEA681@80CEA54B"],
                     "wire-rifle secondary burst; reused for bolt impacts (the impact sequences 80A6DB53/80CEA00A carry sounds only)"),
    "shrap_round":  ("80D89B5C", 64, "quad", 1.3, 1.0, ["80A6DAED@80A6DB1C (flash_round)"], "shrapnel launcher round flash"),
    "shrap_long":   ("80D89DF5", 64, "quad", 1.3, 1.0, ["80A6DAF1@80A6DB1C (flash_long)"], "shrapnel launcher long flash"),
    "cannon_jet":   ("80D8A0AD", 64, "quad", 1.25, 1.0, ["80A5A2C4@80A5A2D7 (flash_long)"], "Walker cannon long flash"),
    "fire_puffs":   ("80D8A3E4", 64, "quad", 1.25, 1.1, ["80A6DAFF@80A6DB1C (fireball)", "80A5A261@80A5A26D (fireball)"],
                     "explosion fireball body (one of the fireball material's textures)"),
    "smoke":        ("80D8A3E7", 64, "quad", .9, 1.2, ["80A5A268@80A5A26D (smoke)", "80D92741@80D9274A (smoke_plume)"], "explosion smoke"),
    "emp_arcs":     ("80D8A3AB", 128, "quad", 1.6, 1.0, ["80A5AC02/80A5AC22/80A5AC2D/80A5AC45@80A5AC46"], "Walker EMP lightning"),
    "contrail":     ("80D8A384", 64, "beam", 1.2, 1.0, ["80CEA182@80CEA22C (contrail)"], "bolt contrail"),
    "bolt_core":    ("80D8D7D0", 32, "beam", 1.2, 1.0, ["80CEA193@80CEA22C"], "bolt body"),
}

# ---------------------------------------------------------------- minimal PNG codec (8-bit, non-interlaced)
def read_png(path):
    data = Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    pos, idat, w = 8, b"", None
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + n]; pos += 12 + n
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and inter == 0, (path, depth, inter)
        elif kind == b"IDAT": idat += body
        elif kind == b"IEND": break
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat); stride = w * ch; out = bytearray(); prev = bytearray(stride); i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
        for x in range(stride):
            a = line[x - ch] if x >= ch else 0; b = prev[x]; c = prev[x - ch] if x >= ch else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out += line; prev = line
    px = []
    for k in range(w * h):
        s = out[k * ch:(k + 1) * ch]
        if ch == 1: px.append((s[0], s[0], s[0], 255))
        elif ch == 2: px.append((s[0], s[0], s[0], s[1]))
        elif ch == 3: px.append((s[0], s[1], s[2], 255))
        else: px.append(tuple(s))
    return w, h, px

def write_png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(v for p in px[y * w:(y + 1) * w] for v in p) for y in range(h))
    def chunk(k, d): return struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d) & 0xFFFFFFFF)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                          + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def sprite(tag, size, shape, gain, gamma, grid=None):
    W, H, full = read_png(SRC / f"vfx/png/{tag}.png")
    if grid:  # crop one flipbook cell
        c, r, cx, cy = grid; w, h = W // c, H // r
        px = [full[(cy * h + y) * W + cx * w + x] for y in range(h) for x in range(w)]
    else:
        w, h, px = W, H, full
    out = []
    for y in range(size):
        for x in range(size):
            # box-filter downsample
            x0, x1 = x * w // size, max(x * w // size + 1, (x + 1) * w // size)
            y0, y1 = y * h // size, max(y * h // size + 1, (y + 1) * h // size)
            acc = 0.0; n = 0
            for yy in range(y0, y1, max(1, (y1 - y0) // 4)):
                for xx in range(x0, x1, max(1, (x1 - x0) // 4)):
                    r, g, b, a = px[yy * w + xx]
                    acc += max(r, g, b) / 255 * a / 255; n += 1
            v = min(1.0, (acc / n * gain)) ** gamma
            # soft edges: a quad never shows its square; a beam fades only across its width
            u, t = (x + .5) / size * 2 - 1, (y + .5) / size * 2 - 1
            if shape == "quad": edge = max(0.0, min(1.0, (1 - (u * u + t * t) ** .5) / .18))
            else: edge = max(0.0, 1 - abs(t)) ** 1.6 * max(0.0, min(1.0, (1 - abs(u)) / .1))  # full-width falloff: no hard core
            out.append((255, 255, 255, int(round(v * edge * 255))))
    return out

def model(name, shape):
    def face(uv=(0, 0, 16, 16)): return {"texture": "#t", "uv": list(uv), "tintindex": 0}
    if shape == "quad":
        # south uv mirrored: the image's left edge lies at +X from BOTH sides, so a directional jet sprite
        # (wide end on the image's left) points along model +X however the plane is viewed.
        elements = [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False, "light_emission": 15,
                     "faces": {"north": face(), "south": face((16, 0, 0, 16))}}]
    else:  # two crossed planes running along +Z (length = display z scale)
        elements = [{"from": [8, 0, 0], "to": [8, 16, 16], "shade": False, "light_emission": 15,
                     "faces": {"east": face(), "west": face()}},
                    {"from": [0, 8, 0], "to": [16, 8, 16], "shade": False, "light_emission": 15,
                     "faces": {"up": face(), "down": face()}}]
    return {"textures": {"t": f"destiny:item/guardian_rises/vfx/{name}", "particle": f"destiny:item/guardian_rises/vfx/{name}"},
            "elements": elements}

# Flipbook sheets: (cols, rows, col, row) of the single cell we use (D2 animates these; we take one frame).
GRID = {"shrap_round": (2, 2, 0, 0), "shrap_long": (1, 3, 0, 1), "cannon_jet": (1, 3, 0, 1),
        "fire_puffs": (2, 2, 0, 0), "smoke": (2, 2, 0, 0)}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(preview_dir=None):
    pa = {r["tag"]: r for r in csv.DictReader((SRC / "particle-assets.csv").open(encoding="utf-8-sig"))}
    table = {"version": 1, "source": "Rising-Guardian-Fallen-AV-2026-11-01 (Charm 3.5.0, Steam build 25932352)",
             "note": "Texture first-surface port; colour via custom_model_data tint; D2 shader/HDR not reproduced.",
             "sprites": {}}
    for name, (tag, size, shape, gain, gamma, particles, role) in SPRITES.items():
        used = [p.split("@")[0].split("/")[0] for p in particles]
        for p in used:  # provenance: every cited particle really maps to this texture
            assert tag in json.loads(pa[p]["textures"]), (name, p, tag)
        px = sprite(tag, size, shape, gain, gamma, GRID.get(name))
        tex = A / f"textures/item/guardian_rises/vfx/{name}.png"
        write_png(tex, size, size, px)
        (A / f"models/guardian_rises/vfx/{name}.json").parent.mkdir(parents=True, exist_ok=True)
        (A / f"models/guardian_rises/vfx/{name}.json").write_text(json.dumps(model(name, shape), indent=2) + "\n")
        (A / f"items/guardian_rises/vfx/{name}.json").parent.mkdir(parents=True, exist_ok=True)
        (A / f"items/guardian_rises/vfx/{name}.json").write_text(json.dumps({"model": {
            "type": "minecraft:model", "model": f"destiny:guardian_rises/vfx/{name}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}, indent=2) + "\n")
        table["sprites"][name] = {"texture": tag, "shape": shape, "size": size, "particles": particles, "role": role,
                                  "cell": list(GRID[name]) if name in GRID else None,
                                  "source_sha256": sha(SRC / f"vfx/png/{tag}.png"), "output_sha256": sha(tex)}
        if preview_dir:  # dark-background preview, tinted by role colour for review only
            tint = {"shrap_round": (255, 150, 60), "shrap_long": (255, 150, 60), "cannon_jet": (255, 154, 60),
                    "fire_puffs": (255, 140, 50), "smoke": (120, 120, 130)}.get(name, (127, 216, 255))
            pv = [(int(tint[0] * a / 255 + 12 * (1 - a / 255)), int(tint[1] * a / 255 + 14 * (1 - a / 255)),
                   int(tint[2] * a / 255 + 18 * (1 - a / 255)), 255) for (_, _, _, a) in px]
            write_png(Path(preview_dir) / f"{name}.png", size, size, pv)
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    TABLE.write_text(json.dumps(table, indent=2, ensure_ascii=False) + "\n")
    print("sprites", len(SPRITES))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
