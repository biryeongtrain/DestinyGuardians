#!/usr/bin/env python3
"""Read-only H20 provenance checks; regeneration is confined to a temporary directory.

Run from any directory after `test build`. Does not replace installed artist models.
"""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_clips(model):
    result = {}
    for clip in model["animations"]:
        if not clip["name"].startswith("h15_"):
            continue
        clip = dict(clip)
        clip["animators"] = {a["name"]: a for a in clip["animators"].values()}
        result[clip["name"]] = clip
    return result


def verify():
    animation = importlib.import_module("build_hunter_animation_h20")
    bow = importlib.import_module("build_shadow_bow_h20")
    source = json.loads(animation.SOURCE.read_text())
    model = animation.compose(source)
    pack = animation.export(model)
    assert (json.dumps(model, indent=2) + "\n").encode() == animation.ART.read_bytes()
    assert (json.dumps(pack, indent=2) + "\n").encode() == animation.PACK.read_bytes()

    with tempfile.TemporaryDirectory(prefix="h20-authoring-") as temporary:
        base = Path(temporary)
        original_art, original_assets = bow.ART, bow.ASSETS
        bow.ART, bow.ASSETS = base / "art", base / "assets"
        bow.ART.mkdir()
        for folder in ("items", "models/item"):
            (bow.ASSETS / folder).mkdir(parents=True)
        for name in ("shadow_bow_h19", "shadow_bow_h19_drawn"):
            shutil.copyfile(original_art / f"{name}.bbmodel", bow.ART / f"{name}.bbmodel")
            shutil.copyfile(original_assets / f"models/item/{name}.json",
                            bow.ASSETS / f"models/item/{name}.json")
        bow.main()
        generated = []
        for folder, original in ((bow.ART, original_art), (bow.ASSETS, original_assets)):
            for path in sorted(folder.rglob("*h20*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(folder)
                assert path.read_bytes() == (original / relative).read_bytes(), relative
                generated.append(str(relative))

    expected = normalized_clips(pack)
    installed = {}
    for relative in ("run/server", "build/run/gameTest"):
        path = ROOT / relative / "config/bettermodel/players/guardian_hunter_h20.bbmodel"
        if path.is_file():
            assert normalized_clips(json.loads(path.read_text())) == expected, path
            installed[str(path.relative_to(ROOT))] = {"clips": len(expected), "sha256": digest(path)}

    jar = ROOT / "build/libs/destiny-guardians-0.1.0+26.3.jar"
    with zipfile.ZipFile(jar) as archive:
        classes = sorted((ROOT / "build/classes/java/main").rglob("*.class"))
        for path in classes:
            name = str(path.relative_to(ROOT / "build/classes/java/main"))
            assert archive.read(name) == path.read_bytes(), name
        resources = sorted(p for p in (ROOT / "src/main/resources").rglob("*")
                           if p.is_file() and p.name != "fabric.mod.json")
        for path in resources:
            name = str(path.relative_to(ROOT / "src/main/resources"))
            assert archive.read(name) == path.read_bytes(), name
    pack_path = ROOT / "run/server/polymer/resource_pack.zip"
    pack_equal = []
    if pack_path.is_file():
        with zipfile.ZipFile(pack_path) as archive:
            for path in sorted((ROOT / "src/main/resources/assets/destiny").rglob("*h20*.json")):
                name = str(path.relative_to(ROOT / "src/main/resources"))
                assert archive.read(name) == path.read_bytes(), name
                pack_equal.append(name)

    return {"animation_regeneration_equal": True, "bow_regeneration_equal": generated,
            "installed_clips_equal": installed, "jar_sha256": digest(jar),
            "jar_equal_dev_classes": len(classes), "jar_equal_source_resources": len(resources),
            "runtime_pack_equal_assets": pack_equal}


if __name__ == "__main__":
    # The authoring helper prints stage diagnostics before this final JSON object.
    print(json.dumps(verify(), indent=2))
