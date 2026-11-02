"""Import the user's HUD layers and rasterize its original Korean fonts. Requires Pillow.

Usage: python scripts/art/import_objective_hud_ko.py /path/to/Rising-Guardian-Objective-HUD-KO-2026-11-02
Source files stay read-only. Output bitmap advances match Minecraft's bitmap provider.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/hud/objective-ko"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main(source):
    hashes = json.loads((source / "SHA256.json").read_text())
    for name, expected in hashes.items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == expected, name
    # Keep the source evidence and licensed font bytes reproducible, outside the runtime pack.
    for name in ["README.md", "SHA256.json", "VALIDATION.json", "hud/layout.json",
                 "evidence/bindings.json", "evidence/fonts.json", "evidence/source-tags.json",
                 "fonts/notosanskr-bold.otf", "fonts/notosanskr-medium.otf", "fonts/OFL.txt", "fonts/NOTICES.txt"]:
        dst = ART / "source" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, dst)
    layers = {}
    for name, file in {"header": "title-bar", "guide": "objective-guide", "box": "checkbox-empty",
                       "shield": "blue-tricorn-original"}.items():
        dst = ASSETS / f"textures/item/hud/rg_objective_{name}.png"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / f"layers/{file}.png", dst)
        layers[name] = list(Image.open(dst).size)
        model = f"gui/hud/rg_objective_{name}"
        write_json(ASSETS / f"models/{model}.json", {
            "gui_light": "front", "textures": {"layer0": f"destiny:item/hud/rg_objective_{name}"},
            "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "faces": {
                face: {"texture": "#layer0", "uv": [0, 0, 16, 16], "tintindex": 0}
                for face in ("north", "south")}}]})
        write_json(ASSETS / f"items/{model}.json", {"model": {"type": "minecraft:model", "model": f"destiny:{model}",
            "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}})
    # Minecraft-specific controls and completion state; these are not supplied Destiny extracts.
    key = Image.new("RGBA", (256, 64))
    draw = ImageDraw.Draw(key)
    draw.rounded_rectangle((1, 1, 254, 62), radius=7, fill=(5, 8, 12, 210), outline=(240, 244, 248, 255), width=2)
    done = Image.open(source / "layers/checkbox-empty.png").convert("RGBA")
    ImageDraw.Draw(done).line([(2, 6), (5, 9), (10, 3)], fill="white", width=2)
    for name, img in {"key": key, "box_done": done}.items():
        img.save(ASSETS / f"textures/item/hud/rg_objective_{name}.png")
        for kind in ("models", "items"):
            template = (ASSETS / f"{kind}/gui/hud/rg_objective_box.json").read_text()
            (ASSETS / f"{kind}/gui/hud/rg_objective_{name}.json").write_text(template.replace("rg_objective_box", "rg_objective_" + name))
    # All modern Hangul syllables plus Latin, Korean jamo and the punctuation used by controls.
    chars = [chr(c) for c in sorted(set(range(33, 127)) | set(range(0xAC00, 0xD7A4)) |
             set(range(0x3131, 0x318F)) | {0xB7, 0x2014, 0x2026})]
    metrics = {}
    for weight in ("bold", "medium"):
        font = ImageFont.truetype(str(source / f"fonts/notosanskr-{weight}.otf"), 20)
        providers = [{"type": "space", "advances": {" ": 5}}]
        advances = {" ": 5}
        for page in range((len(chars) + 255) // 256):
            batch = chars[page * 256:(page + 1) * 256]
            atlas = Image.new("RGBA", (512, 512))
            for i, char in enumerate(batch):
                glyph = Image.new("RGBA", (32, 32))
                draw = ImageDraw.Draw(glyph)
                draw.text((0, 25), char, font=font, anchor="ls", fill="white")
                bounds = glyph.getbbox()
                advances[char] = (bounds[2] if bounds else 0) + 1
                atlas.paste(glyph, ((i % 16) * 32, (i // 16) * 32))
            texture = f"font/rg_objective/{weight}_{page:02}.png"
            dst = ASSETS / "textures" / texture
            dst.parent.mkdir(parents=True, exist_ok=True)
            atlas.save(dst, optimize=True)
            grid = batch + ["\0"] * (256 - len(batch))
            providers.append({"type": "bitmap", "file": f"destiny:{texture}", "height": 32, "ascent": 25,
                              "chars": ["".join(grid[i:i + 16]) for i in range(0, 256, 16)]})
        write_json(ASSETS / f"font/rg_objective_{weight}.json", {"providers": providers})
        metrics[weight] = advances
    write_json(ASSETS / "hud/rg_objective_metrics.json", metrics)
    for name in ("OFL.txt", "NOTICES.txt"):
        shutil.copy2(source / "fonts" / name, ASSETS / "textures/font/rg_objective" / name)
    write_json(ART / "manifest.json", {"source": source.name, "sourceHashesVerified": len(hashes), "layers": layers,
        "font": "Noto Sans KR original OTF rasterized at 20px; bitmap advances use rightmost alpha column + 1",
        "derived": "Original badge and supplied layers copied byte-for-byte. Source labels bar/guide/checkbox/color/placement as reconstructed. Minecraft rasterization and live wrapping are adaptations.",
        "glyphsPerWeight": len(chars) + 1})
    print(json.dumps({"layers": layers, "glyphsPerWeight": len(chars) + 1, "verifiedSourceFiles": len(hashes)}))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
