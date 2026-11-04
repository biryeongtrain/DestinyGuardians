#!/usr/bin/env python3
"""Apply the W106 particle alias to exactly four hash-pinned W105 models.

Run W105 generation first, then this overlay. W105's raw-model --verify is
historical after overlay; this script's --verify checks the final models without
writing. --output-root emits only the four models under a separate root, using
the repository's original manifest and validated (raw or overlaid) source models.
Standard library only; no image generation, network, build or game process.
"""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("art/hud/w105-shotgun/manifest.json")
ASSETS = Path("src/main/resources/assets/destiny")
FRAMES = ("aggressive", "precision", "lightweight", "rapid_fire")
MODELS = tuple(ASSETS / f"models/gui/hud/reticle_w105_shotgun_{f}.json" for f in FRAMES)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def expected_models():
    """Preflight the full original 12-file inventory before any output write."""
    manifest = json.loads((ROOT / MANIFEST).read_bytes())
    inventory = {
        ASSETS / f"{directory}/reticle_w105_shotgun_{frame}.{extension}"
        for frame in FRAMES
        for directory, extension in (("models/gui/hud", "json"),
                                     ("items/gui/hud", "json"),
                                     ("textures/item/hud", "png"))
    }
    hashes = manifest["sha256"]
    if set(hashes) != {p.as_posix() for p in inventory} or manifest["assetCount"] != 12:
        raise ValueError("W105 manifest must contain exactly the original 12 asset paths")
    if set(manifest["frames"]) != set(FRAMES):
        raise ValueError("W105 frame inventory differs from the exact four-frame scope")
    for directory, extension in (("models/gui/hud", "json"),
                                 ("items/gui/hud", "json"),
                                 ("textures/item/hud", "png")):
        actual = {p.relative_to(ROOT) for p in (ROOT / ASSETS / directory)
                  .glob(f"reticle_w105_shotgun_*.{extension}")}
        expected = {p for p in inventory if p.parent == ASSETS / directory}
        if actual != expected:
            raise ValueError(f"Unexpected or missing W105 inventory in {directory}")

    output = {}
    for relative in sorted(inventory):
        data = (ROOT / relative).read_bytes()
        original_hash = hashes[relative.as_posix()]
        if relative not in MODELS:
            if sha256(data) != original_hash:
                raise ValueError(f"Unrelated W105 asset changed: {relative}")
            continue
        frame = FRAMES[MODELS.index(relative)]
        model = json.loads(data)
        textures = model["textures"]
        particle = textures.pop("particle", None)
        if particle not in (None, "#0"):
            raise ValueError(f"Unexpected particle alias: {relative}")
        texture = f"destiny:item/hud/reticle_w105_shotgun_{frame}"
        if textures != {"0": texture}:
            raise ValueError(f"Unexpected texture 0: {relative}")
        original = encode(model)
        if sha256(original) != original_hash:
            raise ValueError(f"Original W105 model hash mismatch after stripping particle: {relative}")
        textures["particle"] = "#0"
        patched = encode(model)
        if data not in (original, patched):
            raise ValueError(f"Source is neither canonical W105 nor canonical W106: {relative}")
        output[relative] = patched
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true",
                        help="Read-only comparison; require the final W106 overlay, never repair.")
    parser.add_argument("--output-root", type=Path, default=ROOT,
                        help="Destination root; only the four model paths are emitted/verified.")
    args = parser.parse_args()
    root = args.output_root.resolve()
    try:
        output = expected_models()
        directory = root / ASSETS / "models/gui/hud"
        extras = {p.relative_to(root) for p in directory.glob("reticle_w105_shotgun_*.json")} - set(MODELS)
        if extras:
            raise ValueError(f"Unexpected destination W105 models: {sorted(map(str, extras))}")
        # Validate all existing destinations before writing any of the four files.
        for relative, patched in output.items():
            path = root / relative
            if args.verify:
                if not path.is_file() or path.read_bytes() != patched:
                    raise ValueError(f"Missing or different W106 model: {relative}")
            elif path.exists():
                model = json.loads(patched)
                del model["textures"]["particle"]
                if path.read_bytes() not in (encode(model), patched):
                    raise ValueError(f"Refusing to overwrite divergent destination: {relative}")
        if not args.verify:
            for relative, patched in output.items():
                path = root / relative
                if not path.is_file() or path.read_bytes() != patched:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(patched)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"W106: {error}\n")
    print(f"{'Verified read-only' if args.verify else 'Applied'} W106 particle=#0 to exactly 4 models in {root}")


if __name__ == "__main__":
    main()
