#!/usr/bin/env python3
"""H20 intermediate nock geometry; preserves H19B UVs and native display hand direction.
Run after H20 animation authoring. No installed BetterModel configs are written.
"""
import copy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/blockbench/supers"
# These are the H20 IK stages .10/.15/.20/.25; Y remains +2 in equipment space.
STAGES = [(0, 3.27), (1, 5.0), (2, 6.75), (3, 8.24)]


def geometry(elements, nock_z, blockbench=False):
    nock_x = 8 + nock_z
    extension = nock_x - 11.27
    angle = math.degrees(math.atan2(extension, 12))
    length = math.hypot(12, extension)
    for e in elements:
        label = e.get("name", "")
        # Vanilla exports have no names: new H19B geometry is the final five elements.
        if label.endswith("string_lower"):
            e["from"], e["to"] = [11.23, -4, 7.95], [11.31, -4 + length, 8.05]
            origin, rotation = [11.27, -4, 8], -angle
        elif label.endswith("string_upper"):
            e["from"], e["to"] = [11.23, 20 - length, 7.95], [11.31, 20, 8.05]
            origin, rotation = [11.27, 20, 8], angle
        elif label.endswith("nocked_shaft"):
            e["from"][0], e["to"][0] = nock_x - 20.74, nock_x
            continue
        elif label.endswith("arrow_head"):
            e["from"][0], e["to"][0] = nock_x - 22.24, nock_x - 20.44
            continue
        elif label.endswith("arrow_vane"):
            e["from"][0], e["to"][0] = nock_x - 4.04, nock_x - .44
            continue
        else:
            continue
        if blockbench:
            e["origin"], e["rotation"] = origin, [0, 0, rotation]
        else:
            e["rotation"] = {"origin": origin, "axis": "z", "angle": rotation}


def main():
    rest_item = json.loads((ASSETS / "models/item/shadow_bow_h19.json").read_text())
    rest_bb = json.loads((ART / "shadow_bow_h19.bbmodel").read_text())
    rest_item["display"]["thirdperson_lefthand"]["rotation"] = [0, 90, 0]
    rest_item["display"]["thirdperson_righthand"]["rotation"] = [0, -90, 0]
    rest_bb["display"] = copy.deepcopy(rest_item["display"])
    rest_bb["name"] = rest_bb["model_identifier"] = "shadow_bow_h20"
    (ART / "shadow_bow_h20.bbmodel").write_text(json.dumps(rest_bb, indent=2)+"\n")
    (ASSETS / "models/item/shadow_bow_h20.json").write_text(json.dumps(rest_item, indent=2)+"\n")
    (ASSETS / "items/shadow_bow_h20.json").write_text(json.dumps({"model": {"type": "minecraft:model", "model": "destiny:item/shadow_bow_h20"}}, indent=2)+"\n")
    source_item = json.loads((ASSETS / "models/item/shadow_bow_h19_drawn.json").read_text())
    source_bb = json.loads((ART / "shadow_bow_h19_drawn.bbmodel").read_text())
    names = [e["name"] for e in source_bb["elements"][-5:]]
    for index, nock in STAGES:
        name = f"shadow_bow_h20_{index}"
        item, bb = copy.deepcopy(source_item), copy.deepcopy(source_bb)
        for e, label in zip(item["elements"][-5:], names): e["name"] = label
        # Full native recipe: entity * display * Ry(180) * handed ItemTransform.
        # Left JSON +90 becomes -90 in ItemTransform.apply, then the display's
        # inner Ry(180) maps the raw +X nock to -Z in BM body coordinates.
        item["display"]["thirdperson_lefthand"]["rotation"] = [0, 90, 0]
        item["display"]["thirdperson_righthand"]["rotation"] = [0, -90, 0]
        bb["display"] = copy.deepcopy(item["display"])
        geometry(item["elements"], nock)
        geometry(bb["elements"], nock, True)
        for e in item["elements"][-5:]: e.pop("name", None)
        bb["name"] = bb["model_identifier"] = name
        (ART / f"{name}.bbmodel").write_text(json.dumps(bb, indent=2)+"\n")
        (ASSETS / f"models/item/{name}.json").write_text(json.dumps(item, indent=2)+"\n")
        (ASSETS / f"items/{name}.json").write_text(json.dumps({"model": {
            "type": "minecraft:model", "model": f"destiny:item/{name}"}}, indent=2)+"\n")
        print(name, "nock", nock, "elements", len(item["elements"]))


if __name__ == "__main__": main()
