#!/usr/bin/env python3
"""Deterministic dedicated HUD suppression. No image dependencies, network or shared GUI shaders.

--verify is strictly read-only. --inspect-source additionally compares the exact
cached official26.3 JAR/asset index. Original images/translations are not copied.
"""
import argparse, hashlib, json, re, struct, zlib, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
INPUT = "art/hud/w76-vanilla/references/source.json"
DATA = "src/main/resources/destiny/hud/w76-vanilla.json"
MANIFEST = "art/hud/w76-vanilla/manifest.json"
NAMES = {"food_empty", "food_half", "food_full", "food_empty_hunger", "food_half_hunger", "food_full_hunger",
         "hotbar", "hotbar_selection", "hotbar_offhand_left", "hotbar_offhand_right",
         "hotbar_attack_indicator_background", "hotbar_attack_indicator_progress",
         "experience_bar_background", "experience_bar_progress"}

def encode(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()

def png(width, height):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes((width * 4 + 1) * height), 9)) + chunk(b"IEND", b""))

def outputs():
    source = json.loads((ROOT / INPUT).read_text())
    assert source["minecraft"] == "26.3" and source["resourceFormat"] == [97, 1] and source["protocol"] == 777
    assert source["clientJarSha1"] == "e877b6a07acd633fb3bb475002175cec036e7b87"
    assert source["assetIndexSha1"] == "0c8f43b28f837869c1e54a6aeb22c396a1548946"
    assert len(source["sprites"]) == 14 and {Path(p["path"]).stem for p in source["sprites"]} == NAMES
    locales = source["locales"]
    assert len(locales) == 143 and locales == sorted(set(locales)) and {"en_us", "ko_kr"} <= set(locales)
    assert all(re.fullmatch(r"[a-z0-9_]+", name) for name in locales)
    assert source["hiddenTranslationKeys"] == ["gui.experience.level"]
    out = {}
    for item in source["sprites"]:
        assert item["path"] == "assets/minecraft/textures/gui/sprites/hud/" + Path(item["path"]).name
        assert not item["metadata"] and 0 < item["width"] <= 256 and 0 < item["height"] <= 256
        out["src/main/resources/" + item["path"]] = png(item["width"], item["height"])
    for locale in locales:
        out[f"src/main/resources/assets/minecraft/lang/{locale}.json"] = encode({"gui.experience.level": ""})
    data = dict(schema=1, stage="W76", minecraft="26.3", sprites=source["sprites"], locales=locales,
                hiddenTranslationKeys=source["hiddenTranslationKeys"], residuals=source["residuals"], scope=source["scope"])
    out[DATA] = encode(data)
    out[MANIFEST] = encode(dict(stage="W76", input=INPUT, inputSha256=hashlib.sha256((ROOT/INPUT).read_bytes()).hexdigest(),
                               newClientAssets=157, sprites=14, locales=143, originalArtworkCopied=False,
                               sharedGuiShadersChanged=False, fullHotbarSuppression=False,
                               sha256={p: hashlib.sha256(raw).hexdigest() for p, raw in sorted(out.items())}))
    return source, out

def inspect_source(source, jar, index):
    assert hashlib.sha1(jar.read_bytes()).hexdigest() == source["clientJarSha1"], "Wrong Minecraft client JAR"
    assert hashlib.sha1(index.read_bytes()).hexdigest() == source["assetIndexSha1"], "Wrong asset index"
    assets = json.loads(index.read_text())["objects"]
    locales = sorted({"en_us"} | {Path(p).stem for p in assets if p.startswith("minecraft/lang/") and p.endswith(".json")})
    assert locales == source["locales"], "Locale scope drift"
    with zipfile.ZipFile(jar) as z:
        assert json.loads(z.read("assets/minecraft/lang/en_us.json"))["gui.experience.level"] == "%s"
        for item in source["sprites"]:
            raw = z.read(item["path"])
            assert hashlib.sha1(raw).hexdigest() == item["vanillaSha1"]
            assert struct.unpack(">II", raw[16:24]) == (item["width"], item["height"])
            assert item["path"] + ".mcmeta" not in z.namelist()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--verify", action="store_true")
    p.add_argument("--inspect-source", action="store_true")
    p.add_argument("--client-jar", type=Path, default=Path.home()/".gradle/caches/fabric-loom/26.3/minecraft-client.jar")
    p.add_argument("--asset-index", type=Path, default=Path.home()/".gradle/caches/fabric-loom/assets/indexes/26.3-34.json")
    args = p.parse_args()
    source, out = outputs()
    if args.inspect_source:
        inspect_source(source, args.client_jar, args.asset_index)
    if args.verify:
        errors = [path for path, raw in out.items() if not (ROOT/path).is_file() or (ROOT/path).read_bytes() != raw]
        if errors:
            raise SystemExit("W76 mismatch: " + ", ".join(errors))
    else:
        for path, raw in out.items():
            target = ROOT/path
            if target.exists() and target.read_bytes() == raw:
                continue
            # Refuse replacing unrelated existing resources with a one-key language overlay.
            if "/lang/" in path and target.exists():
                assert set(json.loads(target.read_text())) == {"gui.experience.level"}, "Refuse unrelated language overwrite"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    print("W76 verified" if args.verify else "W76 generated", "14 dedicated sprites; 143 locale XP overlays; no icon/count suppression")

if __name__ == "__main__":
    main()
