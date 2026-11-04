#!/usr/bin/env python3
"""Read-only selected H22 authoring/install/JAR/served pack equality gate."""
import json
import sys
import zipfile

sys.dont_write_bytecode = True
from verify_h20_assets import ROOT, digest, normalized_clips, verify
import build_hunter_animation_h21 as h21
import build_shadowshot_h22 as h22


def verify_selected():
    result = verify()  # Includes actual class and source-resource byte equality in the final JAR.
    h21_source = json.loads(h21.SOURCE.read_text())
    model21 = h21.compose(h21_source)
    assert (json.dumps(model21, indent=2) + "\n").encode() == h21.ART.read_bytes()
    assert (json.dumps(h21.export(model21), indent=2) + "\n").encode() == h21.PACK.read_bytes()
    source = json.loads(h22.SOURCE.read_text())
    model = h22.compose(source)
    art, item, definition = h22.bow_assets()
    h22.validate(model, source, item)
    pack = {"model": h22.MODEL, "animations": [a for a in model["animations"] if a["name"].startswith("h15_")]}
    saved = {}
    for path, value in ((h22.ART, model), (h22.PACK, pack), (h22.ITEM_ART, art), (h22.ITEM, item), (h22.ITEM_DEF, definition)):
        assert (json.dumps(value, indent=2) + "\n").encode() == path.read_bytes(), path
        saved[str(path.relative_to(ROOT))] = digest(path)
    expected = normalized_clips(pack)
    installed = {}
    for relative in ("run/server", "build/run/gameTest"):
        path = ROOT / relative / f"config/bettermodel/players/{h22.MODEL}.bbmodel"
        if path.is_file():
            assert normalized_clips(json.loads(path.read_text())) == expected, path
            installed[str(path.relative_to(ROOT))] = {"clips": len(expected), "sha256": digest(path)}
    equal = []
    pack_path = ROOT / "run/server/polymer/resource_pack.zip"
    if pack_path.is_file():
        with zipfile.ZipFile(pack_path) as archive:
            for path in (h22.ITEM, h22.ITEM_DEF):
                name = str(path.relative_to(ROOT / "src/main/resources"))
                assert archive.read(name) == path.read_bytes(), name
                equal.append(name)
    result.update(h21_regeneration_equal=True, h22_regeneration_equal=True,
                  h22_installed_clips_equal=installed, h22_saved_sha256=saved,
                  runtime_pack_equal_h22_assets=equal)
    return result


if __name__ == "__main__":
    print(json.dumps(verify_selected(), indent=2))
