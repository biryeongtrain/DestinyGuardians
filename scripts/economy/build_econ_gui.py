#!/usr/bin/env python3
"""Destiny-style economy GUI art for the 9x6 chest menus (vault, postmaster, auction ...).

The chest background is drawn by a font glyph placed in the menu title (font destiny:econ_gui): a 4x-resolution
canvas cut into 256 px tiles (the font atlas page limit), one bitmap provider per tile row so each row has its own
ascent. Only the header row differs between screens; the three lower rows are shared. Also writes:
  * destiny:econ_text  - Noto Sans KR (the shipped rg_objective atlases) at 8 GUI px for titles and tooltips;
  * item models destiny:gui/econ/<icon> for button icons;
  * tooltip style destiny:econ (gui sprites tooltip/econ_background, tooltip/econ_frame).
Layout constants must match kim.biryeong.destiny.economy.EconomyGui.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "src/main/resources/assets/destiny"
S = 4                                  # texture pixels per GUI pixel
X0, Y0, W, H = -8, -8, 192, 256        # canvas in GUI px, relative to the chest's top-left
TILE = 64                              # GUI px per tile (256 texture px)
TITLE_X, TITLE_Y = 8, 6

SCREENS = {  # id: (accent rgb, header icon texture under textures/item/hud/bungie or econ)
    "vault": ((88, 148, 214), "bungie/vendor_vault"),
    "mail": ((78, 184, 168), "bungie/vendor_postmaster"),
    "auction": ((214, 168, 84), "econ/auction"),
    "sell": ((214, 168, 84), "econ/sell"),
    "send": ((78, 184, 168), "econ/send"),
    "confirm": ((214, 168, 84), "econ/confirm"),
    "listings": ((214, 168, 84), "econ/listings"),
}
BG = (13, 17, 23, 246)
PANEL_EDGE = (74, 88, 104, 255)
CELL = (27, 34, 43, 255)
CELL_EDGE = (52, 63, 76, 255)
CELL_HI = (64, 77, 92, 255)
BUTTON = (33, 41, 51, 255)
TEXT = (226, 230, 234, 255)


def g(x, y):
    """GUI coordinate -> canvas texture pixel."""
    return (int(round((x - X0) * S)), int(round((y - Y0) * S)))


def rect(d, x1, y1, x2, y2, fill):
    a, b = g(x1, y1); c, e = g(x2, y2)
    d.rectangle([a, b, c - 1, e - 1], fill=fill)


def frame(d, x1, y1, x2, y2, edge, w=1):
    for i in range(w):
        a, b = g(x1, y1); c, e = g(x2, y2)
        d.rectangle([a + i, b + i, c - 1 - i, e - 1 - i], outline=edge)


def slot(d, x, y, kind="cell", accent=None):
    """An 18x18 slot frame whose item area is (x, y)..(x+16, y+16)."""
    fill = BUTTON if kind == "button" else CELL
    rect(d, x - 1, y - 1, x + 17, y + 17, fill)
    frame(d, x - 1, y - 1, x + 17, y + 17, CELL_EDGE)
    a, b = g(x - 1, y - 1); c, _ = g(x + 17, y - 1)
    d.line([a + 1, b + 1, c - 2, b + 1], fill=CELL_HI)              # top highlight
    if accent:
        a, _ = g(x - 1, y + 17); c, e = g(x + 17, y + 17)
        d.rectangle([a + 1, e - 3, c - 2, e - 2], fill=accent + (255,))


# ------------------------------------------------------------------ Noto glyphs for baked labels

def noto_glyphs():
    f = json.load(open(A / "font/rg_objective_medium.json"))
    out = {}
    for p in f["providers"]:
        if p["type"] != "bitmap": continue
        img = Image.open(A / "textures" / (p["file"].split(":")[1])).convert("RGBA")
        rows = p["chars"]; ch = img.height // len(rows); cw = img.width // len(rows[0])
        for r, row in enumerate(rows):
            for c, cp in enumerate(row):
                if cp != "\x00": out[cp] = (img, c * cw, r * ch, cw, ch)
    return out


GLYPHS = noto_glyphs()


def label(canvas, text, x, y, size=8, color=TEXT):
    """Bake Noto text with its cell top at GUI (x, y), cell height `size` GUI px."""
    px = g(x, y)[0]; py = g(x, y)[1]
    scale = size * S / 32
    for cp in text:
        if cp == " ": px += int(5 * scale * 32 / 32 * 1); continue
        img, sx, sy, cw, chh = GLYPHS[cp]
        cell = img.crop((sx, sy, sx + cw, sy + chh))
        box = cell.getbbox()
        if box is None: px += int(cw * scale); continue
        glyph = cell.crop((box[0], 0, box[2], chh)).resize((max(1, round((box[2] - box[0]) * scale)), round(chh * scale)), Image.LANCZOS)
        tint = Image.new("RGBA", glyph.size, color); tint.putalpha(glyph.getchannel("A"))
        canvas.alpha_composite(tint, (px, py))
        px += glyph.width + round(2 * scale)


# ------------------------------------------------------------------ backgrounds

def background(accent, icon):
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # panel
    rect(d, -4, -4, 180, 226, BG)
    frame(d, -4, -4, 180, 226, PANEL_EDGE)
    # header band with accent line
    rect(d, -3, -3, 179, 16, (20, 26, 34, 255))
    a, b = g(-3, 16); c, _ = g(179, 16)
    d.rectangle([a, b - 2, c - 1, b - 1], fill=accent + (255,))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    a, b = g(-3, -3); c, e = g(179, 16)
    for xx in range(a, c):   # soft accent glow fading from the left
        t = (xx - a) / (c - a)
        gd.line([xx, b, xx, e - 3], fill=accent + (int(70 * max(0, 1 - t * 1.6)),))
    im.alpha_composite(glow); d = ImageDraw.Draw(im)
    if icon:
        ic = Image.open(A / "textures/item/hud" / f"{icon}.png").convert("RGBA").resize((12 * S, 12 * S), Image.LANCZOS)
        im.alpha_composite(ic, g(2, 1))
    # content grid (5 rows) and control row
    for r in range(5):
        for c in range(9): slot(d, 8 + c * 18, 18 + r * 18)
    for c in range(9): slot(d, 8 + c * 18, 108, "button", accent)
    a, b = g(8, 107); c, _ = g(168, 107)
    # inventory section header (the vanilla "Inventory" label is blanked in minecraft/lang)
    a, b = g(8, 137); c, _ = g(168, 137)
    d.rectangle([a, b, c - 1, b + 1], fill=(58, 70, 84, 255))
    label(im, "인벤토리", 8, 127, color=(168, 178, 190, 255))
    # player inventory and hotbar
    for r in range(3):
        for c in range(9): slot(d, 8 + c * 18, 140 + r * 18)
    rect(d, 3, 195, 173, 196, (40, 48, 58, 255))
    for c in range(9): slot(d, 8 + c * 18, 198)
    return im


def tiles(im):
    out = {}
    for ty in range(H // TILE):
        for tx in range(W // TILE):
            t = im.crop((tx * TILE * S, ty * TILE * S, (tx + 1) * TILE * S, (ty + 1) * TILE * S))
            # Minecraft trims bitmap glyph width to the last non-transparent column; a near-invisible pixel in the
            # right column keeps every tile's advance at exactly TILE + 1 GUI px.
            for xx in (0, t.width - 1):
                if t.getpixel((xx, 0))[3] == 0: t.putpixel((xx, 0), (0, 0, 0, 1))
            out[(tx, ty)] = t
    return out


# ------------------------------------------------------------------ icons

def icon_images():
    def blank(): return Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    W_, G, R, Y, B = (232, 236, 240, 255), (110, 210, 120, 255), (226, 92, 86, 255), (232, 190, 96, 255), (120, 176, 232, 255)
    icons = {}
    def tri(pts, col):
        im = blank(); ImageDraw.Draw(im).polygon(pts, fill=col); return im
    icons["prev"] = tri([(42, 12), (18, 32), (42, 52)], W_)
    icons["next"] = tri([(22, 12), (46, 32), (22, 52)], W_)
    im = blank(); d = ImageDraw.Draw(im); d.rectangle([10, 29, 54, 35], fill=R); icons["minus"] = im
    im = blank(); d = ImageDraw.Draw(im); d.rectangle([10, 29, 54, 35], fill=G); d.rectangle([29, 10, 35, 54], fill=G); icons["plus"] = im
    im = blank(); d = ImageDraw.Draw(im); d.line([(12, 33), (26, 47), (52, 17)], fill=G, width=7); icons["confirm"] = im
    im = blank(); d = ImageDraw.Draw(im); d.line([(16, 16), (48, 48)], fill=R, width=7); d.line([(48, 16), (16, 48)], fill=R, width=7); icons["cancel"] = im
    im = blank(); d = ImageDraw.Draw(im); d.polygon([(8, 12), (56, 12), (38, 34), (38, 52), (26, 46), (26, 34)], fill=W_); icons["filter"] = im
    im = blank(); d = ImageDraw.Draw(im)
    for i, w in enumerate((40, 30, 20)): d.rectangle([10, 14 + i * 14, 10 + w, 20 + i * 14], fill=W_)
    d.polygon([(50, 12), (58, 24), (42, 24)], fill=Y); d.polygon([(50, 52), (58, 40), (42, 40)], fill=Y); icons["sort"] = im
    im = blank(); d = ImageDraw.Draw(im); d.ellipse([10, 10, 54, 54], outline=W_, width=5); d.line([(32, 32), (32, 18)], fill=W_, width=5); d.line([(32, 32), (43, 38)], fill=Y, width=5); icons["clock"] = im
    im = blank(); d = ImageDraw.Draw(im)
    for i in range(3): d.rectangle([12, 12 + i * 15, 52, 21 + i * 15], fill=(W_ if i else Y))
    icons["listings"] = im
    im = blank(); d = ImageDraw.Draw(im); d.polygon([(32, 6), (56, 30), (32, 58), (8, 30)], outline=Y, width=5); d.line([(20, 30), (44, 30)], fill=Y, width=5); icons["auction"] = im
    im = blank(); d = ImageDraw.Draw(im); d.rectangle([10, 22, 54, 50], outline=Y, width=5); d.line([(32, 8), (32, 36)], fill=G, width=6); d.polygon([(22, 18), (42, 18), (32, 6)], fill=G); icons["sell"] = im
    im = blank(); d = ImageDraw.Draw(im); d.rectangle([8, 16, 56, 48], outline=W_, width=5); d.line([(8, 16), (32, 34), (56, 16)], fill=W_, width=5); icons["send"] = im
    im = blank(); d = ImageDraw.Draw(im); d.rectangle([8, 20, 56, 52], outline=G, width=5); d.line([(32, 6), (32, 38)], fill=G, width=6); d.polygon([(22, 30), (42, 30), (32, 42)], fill=G); icons["claim_all"] = im
    im = blank(); d = ImageDraw.Draw(im); d.rectangle([6, 6, 58, 58], outline=(150, 160, 172, 255), width=3)
    for k in range(12, 56, 10): d.point((k, 6), fill=(0, 0, 0, 0))
    d.line([(32, 20), (32, 44)], fill=(150, 160, 172, 255), width=4); d.line([(20, 32), (44, 32)], fill=(150, 160, 172, 255), width=4); icons["attach"] = im
    im = blank(); d = ImageDraw.Draw(im); d.ellipse([16, 16, 48, 48], outline=(120, 132, 146, 255), width=4); d.line([(24, 40), (40, 24)], fill=(120, 132, 146, 255), width=4); icons["empty"] = im
    icons["blank"] = blank()
    return icons


# ------------------------------------------------------------------ output

def otf_to_ttf(font, max_err=1.0):
    """CFF (cubic) -> glyf (quadratic) outlines, the fontTools otf2ttf recipe."""
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import newTable
    order = font.getGlyphOrder(); gs = font.getGlyphSet(); glyphs = {}
    for name in order:
        pen = TTGlyphPen(gs)
        gs[name].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
        glyphs[name] = pen.glyph()
    font["loca"] = newTable("loca")
    glyf = font["glyf"] = newTable("glyf"); glyf.glyphOrder = order; glyf.glyphs = glyphs
    del font["CFF "]
    if "VORG" in font: del font["VORG"]
    for g_ in glyphs.values(): g_.recalcBounds(glyf)
    font["maxp"] = maxp = newTable("maxp"); maxp.tableVersion = 0x00010000
    for k in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
              "maxStackElements", "maxSizeOfInstructions", "maxComponentElements"): setattr(maxp, k, 0)
    maxp.maxZones = 1; maxp.recalc(font)
    post = font["post"]; post.formatType = 2.0; post.extraNames = []; post.mapping = {}; post.glyphOrder = order
    font["head"].indexToLocFormat = 0
    font.sfntVersion = "\x00\x01\x00\x00"


def main():
    # button icons as flat GUI item models
    tpl = json.load(open(A / "models/gui/hud/gear_cursor.json"))
    for d in (A / "textures/item/hud/econ", A / "models/gui/econ", A / "items/gui/econ"): d.mkdir(parents=True, exist_ok=True)
    for name, img in icon_images().items():
        img.save(A / f"textures/item/hud/econ/{name}.png", optimize=True)
        m = json.loads(json.dumps(tpl)); m["textures"] = {"layer0": f"destiny:item/hud/econ/{name}"}
        json.dump(m, open(A / f"models/gui/econ/{name}.json", "w"), indent=1)
        json.dump({"model": {"type": "minecraft:model", "model": f"destiny:gui/econ/{name}"}}, open(A / f"items/gui/econ/{name}.json", "w"), indent=1)

    tex = A / "textures/font/econ"; tex.mkdir(parents=True, exist_ok=True)
    for f in tex.glob("*.png"): f.unlink()
    providers = []
    # Negative/positive spaces: U+E100 + k = -(2^k), U+E120 + k = +(2^k), k = 0..8
    adv = {}
    for k in range(9):
        adv[chr(0xE100 + k)] = -(2 ** k); adv[chr(0xE120 + k)] = 2 ** k
    providers.append({"type": "space", "advances": adv})

    shared = None
    chars = {}
    code = 0xE000
    rows = H // TILE
    for sid, (accent, icon) in SCREENS.items():
        t = tiles(background(accent, icon))
        if shared is None:   # rows 1..3 identical for every screen
            shared = {}
            for ty in range(1, rows):
                for tx in range(W // TILE):
                    name = f"shared_r{ty}c{tx}"; t[(tx, ty)].save(tex / f"{name}.png", optimize=True)
                    shared[(tx, ty)] = (name, chr(code)); code += 1
        chars[sid] = []
        for ty in range(rows):
            row = []
            for tx in range(W // TILE):
                if ty == 0:
                    name = f"{sid}_r0c{tx}"; t[(tx, 0)].save(tex / f"{name}.png", optimize=True)
                    row.append((name, chr(code))); code += 1
                else: row.append(shared[(tx, ty)])
            chars[sid].append(row)
    seen = set()
    for sid in SCREENS:
        for ty, row in enumerate(chars[sid]):
            top = Y0 + ty * TILE                      # GUI y of this tile row's top edge
            for name, cp in row:
                if cp in seen: continue
                seen.add(cp)
                providers.append({"type": "bitmap", "file": f"destiny:font/econ/{name}.png",
                                  "height": TILE, "ascent": TITLE_Y + 7 - top, "chars": [cp]})
    json.dump({"providers": providers}, open(A / "font/econ_gui.json", "w"), ensure_ascii=False, indent=1)
    layout = {sid: [[cp for _, cp in row] for row in chars[sid]] for sid in SCREENS}
    (ROOT / "src/main/resources/destiny/economy").mkdir(parents=True, exist_ok=True)
    json.dump({"originX": X0, "originY": Y0, "tile": TILE, "titleX": TITLE_X, "screens": layout},
              open(ROOT / "src/main/resources/destiny/economy/gui.json", "w"), ensure_ascii=False, indent=1)

    # Noto Sans KR Medium as a TrueType provider: real kerning/advances (a bitmap provider adds +1 GUI px per glyph,
    # which spreads 8 px text). Oversample 4 = crisp at GUI scale 4. Font file: SIL OFL (art/hud/objective-ko).
    import shutil
    fdir = A / "font"
    # Subset to what menus show (Latin, punctuation/symbols, Hangul): drops the Hanja/CJK bulk of the 4.7 MB file.
    from fontTools import subset
    opts = subset.Options(); opts.layout_features = ["*"]; opts.name_IDs = ["*"]; opts.notdef_outline = True
    font = subset.load_font(str(ROOT / "art/hud/objective-ko/source/fonts/notosanskr-medium.otf"), opts)
    ranges = [(0x20, 0x7E), (0xA0, 0xFF), (0x2010, 0x2027), (0x2030, 0x203A), (0x2190, 0x21FF), (0x2200, 0x22FF),
              (0x25A0, 0x25FF), (0x2600, 0x26FF), (0x3000, 0x303F), (0x3130, 0x318F), (0x1100, 0x11FF), (0xAC00, 0xD7A3),
              (0xFF01, 0xFF5E)]
    sub = subset.Subsetter(opts); sub.populate(unicodes=[c for a, b in ranges for c in range(a, b + 1)]); sub.subset(font)
    otf_to_ttf(font)   # Minecraft's ttf provider rejects CFF outlines
    font.save(str(fdir / "notosanskr-medium.ttf"))
    old = fdir / "notosanskr-medium.otf"
    if old.exists(): old.unlink()
    lic = fdir / "notosanskr-OFL.txt"
    if lic.exists(): lic.unlink()   # licence stays with the source font in art/hud/objective-ko (pack paths reject .txt here)
    json.dump({"providers": [{"type": "ttf", "file": "destiny:notosanskr-medium.ttf", "size": 8.0, "oversample": 4.0, "shift": [0, 0.5]}]},
              open(A / "font/econ_text.json", "w"), indent=1)

    # tooltip style destiny:econ
    sp = A / "textures/gui/sprites/tooltip"; sp.mkdir(parents=True, exist_ok=True)
    bgim = Image.new("RGBA", (100, 100), (12, 16, 22, 242)); bgim.save(sp / "econ_background.png")
    json.dump({"gui": {"scaling": {"type": "nine_slice", "width": 100, "height": 100, "border": 9}}}, open(sp / "econ_background.png.mcmeta", "w"))
    fr = Image.new("RGBA", (100, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
    d.rectangle([9, 9, 90, 90], outline=(86, 102, 120, 255)); d.rectangle([9, 9, 90, 10], fill=(214, 168, 84, 255))
    fr.save(sp / "econ_frame.png")
    json.dump({"gui": {"scaling": {"type": "nine_slice", "width": 100, "height": 100, "border": 10, "stretch_inner": True}}}, open(sp / "econ_frame.png.mcmeta", "w"))

    # preview: the vault canvas composited over a vanilla-sized dark scene, 1x scale reference
    background(*SCREENS["vault"]).save("/tmp/econ_vault_canvas.png")
    print("screens", len(SCREENS), "tiles", len(list(tex.glob("*.png"))), "chars", code - 0xE000)


if __name__ == "__main__":
    main()
