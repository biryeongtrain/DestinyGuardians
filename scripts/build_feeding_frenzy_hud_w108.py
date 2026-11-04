#!/usr/bin/env python3
"""Build only W108's label triplet, generated source art and OFFLINE preview.

Offline dependencies: Pillow 12.3.0 / FreeType 2.14.3 and the SHA-pinned W62
Arial Narrow Bold system font (not distributed). Run with Python -B.
--output-root mirrors repository-relative paths into an isolated directory.
--verify compares bytes without creating, repairing or deleting any files.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import zlib

from PIL import Image, ImageDraw, ImageFont, __version__ as PILLOW_VERSION, features

ROOT = Path(__file__).resolve().parents[1]
NAME = "perk_feeding_frenzy_w108"
LABEL = "FEEDING FRENZY"
SIZE = (118, 24)
SCALE = 4
PADDING = 4
FONT = Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf")
FONT_SHA256 = "fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57"
ASSETS = Path("src/main/resources/assets/destiny")
ART = Path("art/weapons/w108/hud")
SCRIPT = Path("scripts/build_feeding_frenzy_hud_w108.py")
TEST = Path("src/test/java/kim/biryeong/destiny/hud/FeedingFrenzyHudW108AssetTest.java")
TEXTURE = ASSETS / f"textures/item/hud/{NAME}.png"
MODEL = ASSETS / f"models/gui/hud/{NAME}.json"
ITEM = ASSETS / f"items/gui/hud/{NAME}.json"
SOURCE = ART / "label-source.svg"
PREVIEW = ART / "offline-preview.png"
MANIFEST = ART / "manifest.json"
PACK_PATHS = (ITEM, MODEL, TEXTURE)
OWNED = (SCRIPT, SOURCE, PREVIEW, MANIFEST, *PACK_PATHS, TEST)
PACK_BYTE_BUDGET = 16_384


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def png(image):
    """Canonical RGBA8 PNG: filter 0, stored DEFLATE, no variable metadata.

    Stored blocks avoid encoder/zlib compression-version differences. The label
    still fits the 16KiB total three-file pack budget without compression.
    """
    image = image.convert("RGBA")
    pixels = image.tobytes()
    stride = image.width * 4
    scanlines = b"".join(b"\x00" + pixels[y * stride:(y + 1) * stride]
                         for y in range(image.height))
    blocks = [scanlines[i:i + 65535] for i in range(0, len(scanlines), 65535)]
    payload = b"\x78\x01" + b"".join(
        bytes([int(i == len(blocks) - 1)])
        + struct.pack("<HH", len(block), len(block) ^ 65535) + block
        for i, block in enumerate(blocks))
    payload += struct.pack(">I", zlib.adler32(scanlines) & 0xFFFFFFFF)

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", payload) + chunk(b"IEND", b""))


def raster_label(font_bytes):
    for size in range(22, 0, -1):
        font = ImageFont.truetype(io.BytesIO(font_bytes), size * SCALE,
                                  layout_engine=ImageFont.Layout.BASIC)
        mask = Image.new("L", (SIZE[0] * SCALE, SIZE[1] * SCALE))
        draw = ImageDraw.Draw(mask)
        left, top, right, bottom = draw.textbbox((0, 0), LABEL, font=font)
        if (right - left > (SIZE[0] - 2 * PADDING) * SCALE
                or bottom - top > (SIZE[1] - 2 * PADDING) * SCALE):
            continue
        draw.text(((mask.width - right + left) / 2 - left,
                   (mask.height - bottom + top) / 2 - top), LABEL, font=font, fill=255)
        mask = mask.resize(SIZE, Image.Resampling.LANCZOS)
        bounds = mask.getbbox()
        if (not bounds or bounds[0] <= 0 or bounds[1] <= 0
                or bounds[2] >= SIZE[0] or bounds[3] >= SIZE[1] or size < 15):
            raise ValueError("Full readable label must fit without clipping")
        image = Image.new("RGBA", SIZE, (255, 255, 255, 0))
        image.putalpha(mask)
        return image, size, bounds
    raise ValueError("No readable font size fits")


def source_svg(image):
    # Self-contained generated coverage vectors: no embedded/linked font or sprite.
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="118" height="24" viewBox="0 0 118 24">',
             f"  <title>{LABEL} - original W108 generated label</title>",
             "  <desc>Generated system-font coverage; no official game sprite. Transparent background.</desc>"]
    alpha = image.getchannel("A")
    for y in range(SIZE[1]):
        x = 0
        while x < SIZE[0]:
            value, end = alpha.getpixel((x, y)), x + 1
            while end < SIZE[0] and alpha.getpixel((end, y)) == value:
                end += 1
            if value:
                lines.append(f'  <rect x="{x}" y="{y}" width="{end - x}" height="1" '
                             f'fill="white" fill-opacity="{value / 255:.8f}"/>')
            x = end
    return ("\n".join([*lines, "</svg>"]) + "\n").encode("utf-8")


def preview(image):
    # Label-only review at native size and 3x; no invented runtime stacks/timer.
    sheet = Image.new("RGBA", (472, 144), (24, 29, 36, 255))
    sheet.alpha_composite(image, (16, 8))
    sheet.alpha_composite(image.resize((354, 72), Image.Resampling.NEAREST), (16, 40))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 124), "W108 OFFLINE LABEL PREVIEW - NOT IN GAME", fill="white",
              font=ImageFont.load_default(size=10))
    return sheet


def generate(font_path):
    if PILLOW_VERSION != "12.3.0" or features.version("freetype2") != "2.14.3":
        raise ValueError("Reproducibility requires Pillow 12.3.0 / FreeType 2.14.3")
    font_bytes = font_path.read_bytes()
    if sha256(font_bytes) != FONT_SHA256:
        raise ValueError("W62 Arial Narrow Bold font SHA-256 mismatch")
    image, font_size, bounds = raster_label(font_bytes)
    outputs = {
        TEXTURE: png(image),
        MODEL: encode({
            "ambientocclusion": False, "gui_light": "front",
            "textures": {"0": f"destiny:item/hud/{NAME}", "particle": "#0"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "shade": False,
                          "faces": {face: {"texture": "#0", "uv": [0, 0, 16, 16], "tintindex": 0}
                                    for face in ("north", "south")}}]}),
        ITEM: encode({"model": {
            "type": "minecraft:model", "model": f"destiny:gui/hud/{NAME}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}),
        SOURCE: source_svg(image),
        PREVIEW: png(preview(image)),
    }
    pack_bytes = sum(len(outputs[path]) for path in PACK_PATHS)
    if pack_bytes > PACK_BYTE_BUDGET:
        raise ValueError("Three-file label pack exceeds 16KiB budget")
    outputs[MANIFEST] = encode({
        "stage": "W108", "label": LABEL, "label_size_px": list(SIZE),
        "font_family": "Arial Narrow Bold", "font_source": str(FONT),
        "font_sha256": FONT_SHA256, "font_size_px": font_size,
        "layout_engine": "BASIC", "supersampling": SCALE,
        "pillow_version": PILLOW_VERSION, "freetype_version": features.version("freetype2"),
        "alpha_bounds_px": list(bounds),
        "provenance": "Original generated system-font label and coverage vectors matching W62/W66/W73; "
                      "no official Destiny sprite, ripped asset or bundled font.",
        "preview_status": "OFFLINE LABEL PREVIEW - NOT IN GAME",
        "runtime_contract": {
            "icon_id": f"destiny:gui/hud/{NAME}", "label_size_px": list(SIZE),
            "reused_icons": ["perk_buff_w61", "perk_stack_x_w83", "perk_colon_w61",
                             *[f"ammo_digit_{n}" for n in range(10)]],
            "integration": "Master owns WeaponPerkHud, marker, stacks and timer; this slice adds only a label."},
        "pack_delta": {"new_labels": 1, "new_files": 3, "bytes": pack_bytes,
                       "byte_budget": PACK_BYTE_BUDGET,
                       "paths": [str(path) for path in PACK_PATHS]},
        "generated_paths": [str(path) for path in (*outputs, MANIFEST)],
        "freeze_paths": [str(path) for path in OWNED],
        "sha256": {str(path): sha256(data) for path, data in outputs.items()},
        "source_sha256": {str(path): sha256((ROOT / path).read_bytes()) for path in (SCRIPT, TEST)},
    })
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="read-only exact byte comparison")
    parser.add_argument("--output-root", type=Path, default=ROOT,
                        help="repository-shaped destination; defaults to this script's repository")
    parser.add_argument("--font", type=Path, default=FONT, help="identical SHA-pinned font at another path")
    args = parser.parse_args()
    try:
        outputs = generate(args.font)
        if args.verify:
            errors = [str(path) for path, data in outputs.items()
                      if not (args.output_root / path).is_file()
                      or (args.output_root / path).read_bytes() != data]
            actual = set((args.output_root / ART).rglob("*")) if (args.output_root / ART).is_dir() else set()
            expected = {args.output_root / path for path in (SOURCE, PREVIEW, MANIFEST)}
            errors.extend(str(path.relative_to(args.output_root)) for path in actual - expected if path.is_file())
            for directory in ("items/gui/hud", "models/gui/hud", "textures/gui/hud", "textures/item/hud"):
                for path in (args.output_root / ASSETS / directory).glob(f"{NAME}*"):
                    if path.relative_to(args.output_root) not in PACK_PATHS:
                        errors.append(str(path.relative_to(args.output_root)))
            if errors:
                parser.exit(1, "W108 verification failed (no writes):\n" + "\n".join(sorted(errors)) + "\n")
        else:
            for path, data in outputs.items():
                target = args.output_root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except (OSError, ValueError) as error:
        parser.exit(1, f"W108: {error}\n")
    print(f"{'verified (read-only)' if args.verify else 'generated'} 6 W108 files; "
          "1 label / 3 pack assets; 118x24 RGBA; preview OFFLINE NOT IN GAME")


if __name__ == "__main__":
    main()
