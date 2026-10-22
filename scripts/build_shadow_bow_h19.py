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
    # MC26.3 ItemTransform.apply negates Y/Z rotation for LEFT_HAND contexts.
    # Both effective rotations must be Ry(-90): local arrow -X -> shot -Z,
    # local string/nock +X -> draw hand +Z. Do not mirror the geometry or the rig.
    item["display"]["thirdperson_lefthand"] = {"rotation": [0, 90, 0], "translation": [0, 2, 0]}
    item["display"]["thirdperson_righthand"] = {"rotation": [0, -90, 0], "translation": [0, 2, 0]}
    model["display"] = copy.deepcopy(item["display"])
    if drawn:
        old = next(e for e in model["elements"] if e["name"] == "spectral_bowstring")
        model["elements"].remove(old)
        # Blockbench element order is NOT vanilla export order. Match the unique string's bounds.
        matches = [i for i, e in enumerate(item["elements"])
                   if e["from"] == old["from"] and e["to"] == old["to"]]
        if len(matches) != 1:
            raise ValueError("Expected exactly one runtime straight bowstring")
        index = matches[0]
        runtime_string = item["elements"].pop(index)
        def remove(nodes):
            for node in list(nodes):
                if node == old["uuid"]:
                    nodes.remove(node)
                    return nodes
                if isinstance(node, dict):
                    found = remove(node.get("children", []))
                    if found is not None: return found
            return None
        bb_strings = remove(model["outliner"])
        if bb_strings is None: raise ValueError("Missing BB string group")
        # Keep editor-only vanilla export groups in sync as well (the game ignores them).
        def remap(nodes):
            target = None
            kept = []
            for node in nodes:
                if isinstance(node, int):
                    if node == index:
                        target = nodes
                    else: kept.append(node - 1 if node > index else node)
                elif isinstance(node, dict):
                    found = remap(node.get("children", []))
                    if found is not None: target = found
                    kept.append(node)
            nodes[:] = kept
            return target
        runtime_strings = remap(item.get("groups", []))
        added = []
        runtime_added = []
        def cube(label, a, b, rotation=None):
            src = copy.deepcopy(old)
            src.update(name=label, uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, "destiny:h19:" + label)),
                       origin=[8, 8, 8], **{"from": a, "to": b})
            # Runtime faces already use 0..16 UVs; BB faces use pixels (256x128 here).
            runtime = {"from": a, "to": b, "faces": copy.deepcopy(runtime_string["faces"])}
            if rotation:
                runtime["rotation"] = rotation
                src["origin"] = rotation["origin"]
                src["rotation"] = [0, 0, rotation["angle"]]
            model["elements"].append(src)
            runtime_added.append(len(item["elements"]))
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
        bb_strings.extend(added)
        if runtime_strings is not None: runtime_strings.extend(runtime_added)
    (ART / (name + ".bbmodel")).write_text(json.dumps(model, indent=2) + "\n")
    (ASSETS / "models/item" / (name + ".json")).write_text(json.dumps(item, indent=2) + "\n")
    (ASSETS / "items" / (name + ".json")).write_text(json.dumps({"model": {
        "type": "minecraft:model", "model": "destiny:item/" + name}}, indent=2) + "\n")


if __name__ == "__main__":
    build(False)
    build(True)
