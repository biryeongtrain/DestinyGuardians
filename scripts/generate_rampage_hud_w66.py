#!/usr/bin/env python3
"""Original W66 Rampage labels and offline layout fixture; never runtime buff evidence.

Requires Pillow and the SHA-pinned system font below. --verify builds expected
bytes in memory and reads existing files only; it never repairs or creates files.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/hud/w66-rampage"
FONT = Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf")
FONT_SHA256 = "fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57"
SCALE = 4
SIZE = (94, 24)
FONT_SIZE = 18  # 22px overflows the existing 94px row label slot.
NAMES = tuple(f"perk_rampage_w66_x{stack}" for stack in range(1, 4))
PACK_DIRS = ("textures/item/hud", "models/gui/hud", "items/gui/hud")
REUSED = ("perk_buff_w61", "perk_kill_clip_w61", "perk_outlaw_w62",
          "perk_colon_w61", *(f"ammo_digit_{n}" for n in range(10)))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def png(image):
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def generate():
    if sha256(FONT.read_bytes()) != FONT_SHA256:
        raise ValueError(f"Font SHA-256 mismatch: {FONT}")
    out = {}
    font = ImageFont.truetype(str(FONT), FONT_SIZE * SCALE)
    for stack, name in enumerate(NAMES, 1):
        label = f"Rampage x{stack}"
        image = Image.new("RGBA", (SIZE[0] * SCALE, SIZE[1] * SCALE))
        draw = ImageDraw.Draw(image)
        left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
        if right - left > (SIZE[0] - 4) * SCALE or bottom - top > (SIZE[1] - 4) * SCALE:
            raise ValueError(f"Label would clip: {label}")
        draw.text(((image.width - (right - left)) / 2 - left,
                   (image.height - (bottom - top)) / 2 - top), label, font=font, fill="white")
        image = image.resize(SIZE, Image.Resampling.LANCZOS)
        bounds = image.getchannel("A").getbbox()
        if not bounds or bounds[0] <= 0 or bounds[1] <= 0 or bounds[2] >= SIZE[0] or bounds[3] >= SIZE[1]:
            raise ValueError(f"Raster touches canvas edge: {label}")
        out[ASSETS / f"textures/item/hud/{name}.png"] = png(image)
        out[ASSETS / f"models/gui/hud/{name}.json"] = encode({
            "gui_light": "front", "textures": {"layer0": f"destiny:item/hud/{name}"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "faces": {
                face: {"texture": "#layer0", "uv": [0, 0, 16, 16], "tintindex": 0}
                for face in ("north", "south")}}]})
        out[ASSETS / f"items/gui/hud/{name}.json"] = encode({"model": {
            "type": "minecraft:model", "model": f"destiny:gui/hud/{name}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}})

    # Reuse sprites without rewriting any previous texture, item definition or model.
    dependencies = {ASSETS / f"textures/item/hud/{name}.png":
                    (ASSETS / f"textures/item/hud/{name}.png").read_bytes() for name in REUSED}
    source = {**dependencies, **out}
    sheet = Image.new("RGBA", (1200, 850), (24, 29, 36, 255))
    draw = ImageDraw.Draw(sheet)
    heading = ImageFont.truetype(str(FONT), 26)
    caption = ImageFont.truetype(str(FONT), 18)
    draw.text((24, 16), "W66 OFFLINE LAYOUT FIXTURES - NOT IN GAME", font=heading, fill="white")
    draw.text((24, 50), "Synthetic inputs only. No live buffs, framebuffer capture or gameplay proof.",
              font=caption, fill="#C3CBD5")
    draw.text((24, 77), "Timer = ceil(next stack decay ticks / 20). Layout uses existing HUD coordinates.",
              font=caption, fill="#C3CBD5")

    def sprite(canvas, name, x, y, width, height, color):
        image = Image.open(io.BytesIO(source[ASSETS / f"textures/item/hud/{name}.png"]))
        image = image.convert("RGBA").resize((width, height), Image.Resampling.LANCZOS)
        tint = Image.new("RGBA", image.size, (*color, 255))
        tint.putalpha(image.getchannel("A"))
        canvas.alpha_composite(tint, (round(x - width / 2), round(y - height / 2)))

    # These are illustrative rows, not claims that traits can coexist on a real loadout.
    fixtures = (
        ("Rampage only: x1, 90 ticks -> 0:05", 0, 0, 1, 90),
        ("Rampage only: x2, 40 ticks -> 0:02", 0, 0, 2, 40),
        ("Both legacy rows + x3 (layout stress fixture)", 100, 120, 3, 1),
        ("Rampage absent: legacy IDs and y unchanged", 100, 120, 0, 0),
        ("Outlaw + Rampage: compact rows", 0, 120, 2, 60),
        ("All absent: no perk nodes", 0, 0, 0, 0),
    )
    for index, (title, kill_clip, outlaw, stacks, ticks) in enumerate(fixtures):
        x, y = 24 + (index % 2) * 588, 120 + (index // 2) * 232
        draw.rounded_rectangle((x, y, x + 564, y + 220), radius=8, fill="#202833", outline="#465361")
        draw.text((x + 12, y + 10), title, font=caption, fill="#E4E9EF")
        rows = [("perk_kill_clip_w61", kill_clip, 778),
                ("perk_outlaw_w62", outlaw, 746 if kill_clip > 0 else 778),
                (f"perk_rampage_w66_x{stacks}", ticks if stacks > 0 else 0,
                 778 - 32 * ((kill_clip > 0) + (outlaw > 0)))]
        # 2x detail uses the exact centres/sizes; annotations are outside the feed.
        canvas = Image.new("RGBA", (368, 184))
        for label, remaining, row_y in rows:
            if remaining <= 0:
                continue
            seconds = (remaining + 19) // 20
            parts = (("perk_buff_w61", 104, 18, 18, (141, 226, 175)),
                     (label, 168, 94, 24, (241, 243, 245)),
                     ("ammo_digit_0", 232, 10, 20, (241, 243, 245)),
                     ("perk_colon_w61", 241, 4, 20, (241, 243, 245)),
                     (f"ammo_digit_{seconds // 10}", 250, 10, 20, (241, 243, 245)),
                     (f"ammo_digit_{seconds % 10}", 262, 10, 20, (241, 243, 245)))
            for name, centre_x, width, height, color in parts:
                sprite(canvas, name, (centre_x - 88) * 2, (row_y - 700) * 2,
                       width * 2, height * 2, color)
        sheet.alpha_composite(canvas, (x + 12, y + 32))
        for row_y in (714, 746, 778):
            draw.text((x + 400, y + 32 + (row_y - 700) * 2 - 9), f"y = {row_y}",
                      font=caption, fill="#9EADB9")
    draw.text((24, 824), "Feed bottom: y=790. Super top: y=816. Ammo panel: y=920..976 (untouched).",
              font=caption, fill="#C3CBD5")
    out[ART / "offline-preview.png"] = png(sheet)
    manifest_path = ART / "manifest.json"
    freeze = ["scripts/generate_rampage_hud_w66.py",
              "src/main/java/kim/biryeong/destiny/hud/WeaponPerkHud.java",
              *map(relative, out), relative(manifest_path)]
    manifest = {
        "stage": "W66", "font_source": str(FONT), "font_sha256": FONT_SHA256,
        "font_size_px": FONT_SIZE, "label_size_px": list(SIZE),
        "provenance": "Original system-font raster labels; no official Destiny glyphs, rip or bundled font.",
        "preview": {"path": "art/hud/w66-rampage/offline-preview.png", "status": "NOT IN GAME",
                    "inputs": "Synthetic layout fixtures, never active-buff evidence."},
        "runtime": {"stacks": "WeaponRampage.stacks(ServerPlayer): 0..3",
                    "remaining": "WeaponRampage.remaining(ServerPlayer): 0..90 next-stack-decay ticks",
                    "timer": "ceil(remaining / 20) using existing W39 digits and W61 colon",
                    "prefix": "destiny:hud_perk_", "rampage_key": "rampage_",
                    "row_order": ["Kill Clip", "Outlaw", "Rampage"], "active_row_y": [778, 746, 714],
                    "nodes_per_active_row": 6, "max_perk_nodes": 18,
                    "zero_stacks": "Remove all six Rampage nodes; never display x0 or retain 0:00."},
        "pack_delta": {"new_labels": 3, "new_files": 9,
                       "prefix_counts_at_handoff": {prefix: {"before": 100, "after": 103} for prefix in PACK_DIRS}},
        "layout_review": "94x24 label slot preserved; feed ends at y=790, super begins at y=816; ammo area unchanged.",
        "sha256": {relative(path): sha256(data) for path, data in out.items()},
        "reused_texture_sha256": {relative(path): sha256(data) for path, data in dependencies.items()},
        "freeze_list": freeze,
    }
    out[manifest_path] = encode(manifest)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="compare deterministic bytes; never write")
    args = parser.parse_args()
    outputs = generate()
    if args.verify:
        errors = [relative(path) for path, expected in outputs.items()
                  if not path.is_file() or path.read_bytes() != expected]
        expected_pack = {path for path in outputs if path.is_relative_to(ASSETS)}
        actual_pack = {path for prefix in PACK_DIRS for path in (ASSETS / prefix).glob("perk_rampage_w66*")}
        errors.extend(relative(path) for path in actual_pack - expected_pack)
        if errors:
            parser.exit(1, "W66 verification failed (no writes):\n" + "\n".join(sorted(errors)) + "\n")
    else:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"{'verified (read-only)' if args.verify else 'generated'} {len(outputs)} W66 HUD files; "
          "9 pack assets, 3 labels; preview NOT IN GAME")


if __name__ == "__main__":
    main()
