#!/usr/bin/env python3
"""Original Archer's Tempo glyph raster and OFFLINE NOT INGAME layout preview.

Uses the W62 system font, SHA-pinned below, without bundling it. All work is
offline. --verify compares expected bytes in memory and never creates or repairs
files. Requires Pillow; invoke with the bundled runtime Python and -B.
"""
import argparse
import hashlib
import io
import itertools
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as PILLOW_VERSION

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/hud/w73-archers-tempo"
FONT = Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf")
FONT_SHA256 = "fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57"
NAME = "perk_archers_tempo_w73"
LABEL = "Archer's Tempo"
SIZE = (94, 24)
SCALE = 4
PADDING = 4
PACK_DIRS = ("items/gui/hud", "models/gui/hud", "textures/item/hud")
REUSED = ("perk_buff_w61", "perk_colon_w61", "perk_kill_clip_w61",
          "perk_outlaw_w62", "perk_rampage_w66_x1", "perk_rampage_w66_x2",
          "perk_rampage_w66_x3", *(f"ammo_digit_{n}" for n in range(10)))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def png(image):
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def raster_label(font_bytes):
    # Select the largest whole-pixel size up to W62's 22px, never truncate or
    # horizontally squeeze glyphs. Padding also protects Lanczos edge pixels.
    for size in range(22, 0, -1):
        font = ImageFont.truetype(io.BytesIO(font_bytes), size * SCALE)
        image = Image.new("RGBA", (SIZE[0] * SCALE, SIZE[1] * SCALE))
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = draw.textbbox((0, 0), LABEL, font=font)
        if (right - left > (SIZE[0] - 2 * PADDING) * SCALE
                or bottom - top > (SIZE[1] - 2 * PADDING) * SCALE):
            continue
        draw.text(((image.width - (right - left)) / 2 - left,
                   (image.height - (bottom - top)) / 2 - top),
                  LABEL, font=font, fill="white")
        image = image.resize(SIZE, Image.Resampling.LANCZOS)
        bounds = image.getchannel("A").getbbox()
        if not bounds or bounds[0] <= 0 or bounds[1] <= 0 or bounds[2] >= SIZE[0] or bounds[3] >= SIZE[1]:
            raise ValueError(f"Raster touches canvas edge: {LABEL}")
        return image, size, bounds
    raise ValueError(f"No font size fits: {LABEL}")


def rows(kill_clip, outlaw, stacks, rampage, tempo):
    values = (("perk_kill_clip_w61", kill_clip), ("perk_outlaw_w62", outlaw),
              (f"perk_rampage_w66_x{stacks}", rampage if stacks > 0 else 0),
              (NAME, tempo))
    return [(name, ticks, 778 - 32 * index)
            for index, (name, ticks) in enumerate((n, t) for n, t in values if t > 0)]


def validate_layout():
    # All 16 active-row combinations and inconsistent/expired Rampage inputs.
    for active in itertools.product((False, True), repeat=4):
        feed = rows(100 if active[0] else 0, 120 if active[1] else 0,
                    int(active[2]), 90 if active[2] else 0, 60 if active[3] else 0)
        if len(feed) != sum(active) or [y for _, _, y in feed] != [778 - 32 * i for i in range(sum(active))]:
            raise ValueError(f"Invalid compact layout: {active}")
    for stacks, ticks in ((0, 90), (1, 0), (0, 0), (1, -1)):
        if rows(0, 0, stacks, ticks, 1) != [(NAME, 1, 778)]:
            raise ValueError("Inactive Rampage must not leave a gap above Archer's Tempo")


def generate():
    font_bytes = FONT.read_bytes()
    if sha256(font_bytes) != FONT_SHA256:
        raise ValueError(f"Font SHA-256 mismatch: {FONT}")
    validate_layout()
    label, font_size, bounds = raster_label(font_bytes)
    out = {ASSETS / f"textures/item/hud/{NAME}.png": png(label)}
    out[ASSETS / f"models/gui/hud/{NAME}.json"] = encode({
        "gui_light": "front", "textures": {"layer0": f"destiny:item/hud/{NAME}"},
        "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "faces": {
            face: {"texture": "#layer0", "uv": [0, 0, 16, 16], "tintindex": 0}
            for face in ("north", "south")}}]})
    out[ASSETS / f"items/gui/hud/{NAME}.json"] = encode({"model": {
        "type": "minecraft:model", "model": f"destiny:gui/hud/{NAME}",
        "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}})
    dependencies = {ASSETS / f"textures/item/hud/{name}.png":
                    (ASSETS / f"textures/item/hud/{name}.png").read_bytes() for name in REUSED}
    source = {**dependencies, **out}
    sheet = Image.new("RGBA", (1200, 1040), (24, 29, 36, 255))
    draw = ImageDraw.Draw(sheet)
    heading = ImageFont.truetype(io.BytesIO(font_bytes), 26)
    caption = ImageFont.truetype(io.BytesIO(font_bytes), 18)
    draw.text((24, 16), "W73 OFFLINE NOT INGAME - Archer's Tempo HUD", font=heading, fill="white")
    draw.text((24, 50), "Synthetic layout fixtures only; no live buffs or framebuffer capture.",
              font=caption, fill="#C3CBD5")
    draw.text((24, 77), f"Full label, dynamically fitted at {font_size}px in the existing 94x24 slot; six cached nodes per row.",
              font=caption, fill="#C3CBD5")

    def sprite(canvas, name, x, y, width, height, color):
        with Image.open(io.BytesIO(source[ASSETS / f"textures/item/hud/{name}.png"])) as raw:
            image = raw.convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
        tint = Image.new("RGBA", image.size, (*color, 255))
        tint.putalpha(image.getchannel("A"))
        canvas.alpha_composite(tint, (round(x - width / 2), round(y - height / 2)))

    fixtures = (
        ("Tempo only: 60 ticks -> 0:03", 0, 0, 0, 0, 60),
        ("All four rows: synthetic layout stress fixture", 100, 120, 3, 90, 60),
        ("Outlaw + Tempo: compact rows", 0, 120, 0, 0, 40),
        ("Rampage + Tempo: last tick -> 0:01", 0, 0, 2, 40, 1),
        ("Tempo expired: previous rows retain their layout", 100, 120, 1, 90, 0),
        ("All absent: zero perk nodes", 0, 0, 0, 0, 0),
    )
    for index, (title, kill_clip, outlaw, stacks, rampage, tempo) in enumerate(fixtures):
        x, y = 24 + index % 2 * 588, 120 + index // 2 * 296
        draw.rounded_rectangle((x, y, x + 564, y + 284), radius=8, fill="#202833", outline="#465361")
        draw.text((x + 12, y + 10), title, font=caption, fill="#E4E9EF")
        canvas = Image.new("RGBA", (368, 248))
        for name, ticks, row_y in rows(kill_clip, outlaw, stacks, rampage, tempo):
            seconds = (ticks + 19) // 20
            parts = (("perk_buff_w61", 104, 18, 18, (141, 226, 175)),
                     (name, 168, 94, 24, (241, 243, 245)),
                     ("ammo_digit_0", 232, 10, 20, (241, 243, 245)),
                     ("perk_colon_w61", 241, 4, 20, (241, 243, 245)),
                     (f"ammo_digit_{seconds // 10}", 250, 10, 20, (241, 243, 245)),
                     (f"ammo_digit_{seconds % 10}", 262, 10, 20, (241, 243, 245)))
            for part, centre_x, width, height, color in parts:
                sprite(canvas, part, (centre_x - 88) * 2, (row_y - 666) * 2,
                       width * 2, height * 2, color)
        sheet.alpha_composite(canvas, (x + 12, y + 32))
        for row_y in (682, 714, 746, 778):
            draw.text((x + 400, y + 32 + (row_y - 666) * 2 - 9), f"y = {row_y}",
                      font=caption, fill="#9EADB9")
    draw.text((24, 1010), "2x detail. Fourth row y=682; feed bottom y=790. OFFLINE NOT INGAME.",
              font=caption, fill="#C3CBD5")
    out[ART / "offline-preview.png"] = png(sheet)
    out[ART / "manifest.json"] = encode({
        "stage": "W73", "label": LABEL, "font_source": str(FONT), "font_sha256": FONT_SHA256,
        "font_size_px": font_size, "font_fit": "Largest integer size <=22 fitting full text with 4px padding",
        "label_size_px": list(SIZE), "alpha_bounds_px": list(bounds), "supersampling": SCALE,
        "pillow_version": PILLOW_VERSION,
        "provenance": "Original rasterized system-font glyphs matching W62; no ripped assets or bundled font.",
        "preview": {"path": relative(ART / "offline-preview.png"), "status": "OFFLINE NOT INGAME",
                    "inputs": "Synthetic layout fixtures only; not runtime or gameplay evidence."},
        "runtime": {"remaining": "WeaponArcherTempo.remaining(ServerPlayer), ticks",
                    "key": "destiny:hud_perk_archers_tempo_", "timer": "ceil(remaining / 20)",
                    "row_order": ["Kill Clip", "Outlaw", "Rampage", LABEL],
                    "active_row_y": [778, 746, 714, 682], "nodes_per_active_row": 6,
                    "max_perk_nodes": 24, "inactive": "Remove all six nodes when ticks <= 0",
                    "cache": "Existing CombatHud.sprite state cache and stable per-player IDs"},
        "pack_delta": {"new_labels": 1, "new_files": 3,
                       "reused": "W61 marker and colon, W39 digits; previous row labels in preview only"},
        "sha256": {relative(path): sha256(data) for path, data in out.items()},
        "reused_texture_sha256": {relative(path): sha256(data) for path, data in dependencies.items()},
    })
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="compare bytes read-only; never write")
    args = parser.parse_args()
    outputs = generate()
    if args.verify:
        errors = [relative(path) for path, expected in outputs.items()
                  if not path.is_file() or path.read_bytes() != expected]
        expected_pack = {path for path in outputs if path.is_relative_to(ASSETS)}
        actual_pack = {path for prefix in PACK_DIRS for path in (ASSETS / prefix).glob(f"{NAME}*")}
        errors.extend(relative(path) for path in actual_pack - expected_pack)
        if errors:
            parser.exit(1, "W73 verification failed (no writes):\n" + "\n".join(sorted(errors)) + "\n")
    else:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"{'verified (read-only)' if args.verify else 'generated'} {len(outputs)} W73 HUD files; "
          "3 pack assets, 1 label; preview OFFLINE NOT INGAME")


if __name__ == "__main__":
    main()
