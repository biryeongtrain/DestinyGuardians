#!/usr/bin/env python3
"""H19 bow states, derived from the authored H15 prop; no installed model writes.

Keeps the original geometry/atlas. Adds a visibly pulled V string and a nocked
arrow in the drawn state. Both JSON items and editable Blockbench files are saved.
"""
import copy
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src/main/resources/assets/destiny"
ART = ROOT / "art/blockbench/supers"


def build(drawn):
    name = "shadow_bow_h19" + ("_drawn" if drawn else "")
    item = json.loads((ASSETS / "models/item/shadow_bow.json").read_text())
    model = json.loads((ART / "shadow_bow.bbmodel").read_text())
    model["name"] = model["model_identifier"] = name
    # Bow is supported in the left hand. Its limb plane must contain the shot axis.
    item["display"]["thirdperson_lefthand"] = {"rotation": [0, -90, 0], "translation": [0, 2, 0]}
    model["display"] = copy.deepcopy(item["display"])
    if drawn:
        old = next(e for e in model["elements"] if e["name"] == "spectral_bowstring")
        index = model["elements"].index(old)
        del model["elements"][index]
        del item["elements"][index]
        def remove(nodes):
            for node in list(nodes):
                if node == old["uuid"]: nodes.remove(node)
                elif isinstance(node, dict): remove(node.get("children", []))
        remove(model["outliner"])
        added = []
        def cube(label, a, b, rotation=None):
            src = copy.deepcopy(old)
            src.update(name=label, uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, "destiny:h19:" + label)),
                       origin=[8, 8, 8], **{"from": a, "to": b})
            runtime = {"from": a, "to": b, "faces": copy.deepcopy(item["elements"][0]["faces"])}
            for face in runtime["faces"].values():
                face["uv"] = copy.deepcopy(old["faces"]["north"]["uv"])
            if rotation:
                runtime["rotation"] = rotation
                src["origin"] = rotation["origin"]
                src["rotation"] = [0, 0, rotation["angle"]]
            model["elements"].append(src)
            item["elements"].append(runtime)
            added.append(src["uuid"])
        # 12 vertical units at22.5 degrees puts the pulled nock atX16.24/Y8.
        cube("h19_string_lower", [11.23, -4, 7.95], [11.31, 8.989, 8.05],
             {"origin": [11.27, -4, 8], "axis": "z", "angle": -22.5})
        cube("h19_string_upper", [11.23, 7.011, 7.95], [11.31, 20, 8.05],
             {"origin": [11.27, 20, 8], "axis": "z", "angle": 22.5})
        cube("h19_nocked_shaft", [-4.5, 7.94, 7.94], [16.24, 8.06, 8.06])
        cube("h19_arrow_head", [-6, 7.8, 7.82], [-4.2, 8.2, 8.18])
        cube("h19_arrow_vane", [12.2, 7.5, 7.97], [15.8, 8.5, 8.03])
        model["outliner"][0]["children"].extend(added)
    (ART / (name + ".bbmodel")).write_text(json.dumps(model, indent=2) + "\n")
    (ASSETS / "models/item" / (name + ".json")).write_text(json.dumps(item, indent=2) + "\n")
    (ASSETS / "items" / (name + ".json")).write_text(json.dumps({"model": {
        "type": "minecraft:model", "model": "destiny:item/" + name}}, indent=2) + "\n")


if __name__ == "__main__":
    build(False)
    build(True)
