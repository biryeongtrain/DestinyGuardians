#!/usr/bin/env python3
"""External-view software z-buffer comparison, NOT native screenshots or FPS.

Reads JUnit's build-only exports and the unchanged authored W118 assets. Refuses
stale exports and existing evidence destinations. Does not launch Minecraft/DCC.
"""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/assets/destiny"
EXPORT = ROOT / "build/qa/w119-culling"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location("bf_renderer", ROOT / "scripts/generate_surface_w115_blast_furnace.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    audit = json.loads((EXPORT / "audit.json").read_text())
    pins = json.loads((ROOT / "docs/qa/2026-10-25/w118/final-product-pins.json").read_text())
    for row in pins:
        assert hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() == row["sha256"], row["path"]
    rows = []
    contact = Image.new("RGB", (1400, 12 * 300), "#171c23")
    pen = ImageDraw.Draw(contact)
    for weapon in ("blast_furnace", "hammerhead"):
        parts = ("body", "magazine", "cover") if weapon == "hammerhead" else ("body", "magazine")
        before = {}
        after = {}
        for part in parts:
            filename = f"{weapon}_{part}.json"
            raw = (RES / "models/weapon_surface_w115" / filename).read_bytes()
            culled = (EXPORT / filename).read_bytes()
            key = f"assets/destiny/models/weapon_reload_w114_{weapon}/{filename}"
            assert hashlib.sha256(raw).hexdigest() == audit[key]["inputSha256"]
            assert hashlib.sha256(culled).hexdigest() == audit[key]["outputSha256"]
            before[part] = json.loads(raw)["elements"]
            after[part] = json.loads(culled)["elements"]
            named = {e["name"]: e for e in before[part]}
            assert all(named[e["name"]] == e for e in after[part]), "Retained element changed"
        texture = Image.open(io.BytesIO((RES / f"textures/item/weapon/w115/{weapon}.png").read_bytes()))
        views = ((0, 0), (-28, 18), (152, 16), (-10, 72), (90, 15), (-18, 8))
        for case, (yaw, elevation) in enumerate(views):
            outputs = []; framed_geometry=[]
            for group in (before, after):
                geometry = []
                for part in parts:
                    elements = copy.deepcopy(group[part])
                    if case == 5 and part != "body":
                        # Rigid separation diagnostic, NOT an actual reload frame.
                        delta = np.array([0, 3 if part == "cover" else -3.4, 0])
                        for e in elements:
                            for key in ("from", "to"):
                                e[key] = (np.array(e[key]) + delta).tolist()
                            if "rotation" in e:
                                e["rotation"]["origin"] = (np.array(e["rotation"]["origin"]) + delta).tolist()
                    geometry.extend(elements)
                framed_geometry.append(geometry)
            view=renderer.camera(yaw,elevation)
            # Fit the entire authored geometry (including separated parts), not
            # the BF-specific legacy fixed-center crop; the long HH muzzle matters.
            vertices=np.concatenate([renderer.vertices(e) for e in framed_geometry[0]])
            delta_from_legacy_center=vertices-np.array([8.006,10.70,5.69445])
            projected=np.stack((delta_from_legacy_center@view[0],delta_from_legacy_center@view[1]),axis=1)
            lower,upper=projected.min(0),projected.max(0);extent=upper-lower
            scale=min(24,640/max(extent[0],1e-9),230/max(extent[1],1e-9))
            center=(lower+upper)/2
            offset=(350-center[0]*scale,140+center[1]*scale)
            for geometry in framed_geometry:
                outputs.append(renderer.render(geometry, texture, view, 700, 280, scale,offset=offset))
            a, b = map(np.array, outputs)
            delta = np.abs(a.astype(int) - b.astype(int))
            changed = int(np.any(delta != 0, axis=2).sum())
            label = f"{weapon}-{case:02d}"
            for side, im in zip(("authored", "culled"), outputs):
                im.save(args.output / f"{label}-{side}.png")
            Image.fromarray(np.clip(delta * 8, 0, 255).astype(np.uint8)).save(args.output / f"{label}-diff-x8.png")
            y = len(rows) * 300
            contact.paste(outputs[0], (0, y + 20));contact.paste(outputs[1], (700, y + 20))
            pen.text((8, y + 4), f"OFFLINE {label}: W118 authored | W119 culled; changed pixels {changed}", fill="white")
            rows.append(dict(weapon=weapon, view=[yaw, elevation], rigidSeparatedDiagnostic=case == 5,
                             changedPixels=changed, maxChannelDifference=int(delta.max()),
                             projectedExtentPixels=(extent*scale).tolist(),scale=scale,offset=list(offset)))
    contact.save(args.output / "contact.png")
    report = dict(kind="software_zbuffer_external_view_not_native", cases=rows,
                  authoredPinsUnchanged=len(pins), allIdentical=all(r["changedPixels"] == 0 for r in rows),
                  limitations=["Not actual framebuffer/native performance evidence", "No mipmap/filtering or inside-hull camera proof"])
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    assert report["allIdentical"], "External-view differences require review; evidence retained"


if __name__ == "__main__":
    main()
