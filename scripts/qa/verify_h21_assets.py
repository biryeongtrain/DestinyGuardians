#!/usr/bin/env python3
"""Read-only H21 regeneration/install/JAR checks, including preservation of H20 assets."""
import json
import sys
sys.dont_write_bytecode = True
from verify_h20_assets import ROOT, digest, normalized_clips, verify
import build_hunter_animation_h21 as author


if __name__ == "__main__":
    result = verify()
    source = json.loads(author.SOURCE.read_text())
    model = author.compose(source)
    pack = author.export(model)
    assert (json.dumps(model, indent=2) + "\n").encode() == author.ART.read_bytes()
    assert (json.dumps(pack, indent=2) + "\n").encode() == author.PACK.read_bytes()
    expected = normalized_clips(pack)
    installed = {}
    for relative in ("run/server", "build/run/gameTest"):
        path = ROOT / relative / "config/bettermodel/players/guardian_hunter_h21.bbmodel"
        if path.is_file():
            assert normalized_clips(json.loads(path.read_text())) == expected, path
            installed[str(path.relative_to(ROOT))] = {"clips": len(expected), "sha256": digest(path)}
    result["h21_regeneration_equal"] = True
    result["h21_installed_clips_equal"] = installed
    result["h21_model_sha256"] = digest(author.ART)
    result["h21_resource_sha256"] = digest(author.PACK)
    print(json.dumps(result, indent=2))
