#!/usr/bin/env python3
"""Ace ADS-only iron sight, preserving all 87 source cubes and canonical poses.

The source rail is not an aperture. Add a narrow forward blade and a real open
rear notch above it; no scope, opaque glass or generic HUD ring. Original W83
HIP/third/reload remain independent. New item graph uses the same 21-step input.
"""
import argparse, copy, hashlib, json, runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "src/main/resources/assets/destiny"
KEY = "weapon_sight_w156"
ID = "ace_of_spades"
FP = ("firstperson_righthand", "firstperson_lefthand")
CENTER = [8, 12.45, 4.075186918]
FRONT_Z = -4.380813082
EYE = .42
SCALE = .95

def enc(v): return (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def generate():
    helper = runpy.run_path(str(ROOT/"scripts/art/build_ace_w83.py"))
    source_path = A/f"models/item/weapon/{ID}.json"
    source = json.loads(source_path.read_bytes())
    assert len(source["elements"]) == 87
    body = copy.deepcopy(source)
    # Clean authored notch/blade; source metal face UVs remain the colour basis.
    # Eye +Z, muzzle -Z; all sight additions sit above the retained receiver.
    added=[]
    def box(name, low, high, donor):
        e=dict(name="w156_"+name, **{"from":low,"to":high},
               faces=copy.deepcopy(source["elements"][donor]["faces"]))
        added.append(e)
    box("rear_saddle", [7.454,12.075,3.77], [8.546,12.22,4.56],24)
    box("rear_notch_left",[7.454,12.20,3.95],[7.80,12.54,4.56],24)
    box("rear_notch_right",[8.20,12.20,3.95],[8.546,12.54,4.56],24)
    box("front_ramp",[7.78,11.769410476,-4.42],[8.22,12.16,-3.96],7)
    box("front_blade",[7.935,12.15,-4.42],[8.065,12.39,-4.14],24)
    body["elements"].extend(added)
    body["credit"]="W156 Ace ADS notch/blade above unchanged W83 87-cube assembly; Bungie weapon design"
    out={A/f"models/{KEY}/{ID}_body.json":enc(body)}
    hip=source["display"]
    ads=copy.deepcopy(hip)
    for ctx in FP:
        ads[ctx]=dict(rotation=[0,0,0],translation=[-8.96,8.32-SCALE*(CENTER[1]-8),
                    16*(.72-EYE)-SCALE*(CENTER[2]-8)],scale=[SCALE]*3)
    mapping={}
    for frame in range(21):
        display=helper["interpolate"](hip,ads,frame)
        for style in ("native","twohand"):
            path=f"{KEY}/{ID}_{frame:02}_{style}"
            parent=f"item/weapon/{ID}" if frame==0 else f"{KEY}/{ID}_body"
            out[A/f"models/{path}.json"]=enc(dict(parent="destiny:"+parent,
                display=display if style=="native" else helper["two_hand_display"](display)))
            mapping[f"destiny:item/weapon_aim_w70/{ID}_{frame:02}_{style}"]="destiny:"+path
    def remap(v):
        if isinstance(v,dict):
            return {k:mapping.get(x,x) if k=="model" and isinstance(x,str) else remap(x) for k,x in v.items()}
        if isinstance(v,list):return [remap(x) for x in v]
        return v
    graph_path=A/f"items/weapon_aim_w70/{ID}.json"
    out[A/f"items/{KEY}/{ID}.json"]=enc(remap(json.loads(graph_path.read_bytes())))
    manifest=dict(stage="W156",id=ID,source=str(source_path.relative_to(ROOT)),sourceSha256=sha(source_path.read_bytes()),
        reference="https://www.youtube.com/watch?v=YXSMO6Dk-r8",sourceCubes=87,addedCubes=len(added),totalCubes=len(body["elements"]),
        sightCenter=CENTER,frontZ=FRONT_Z,eyeToRearMeters=EYE,scale=SCALE,frames=21,
        policy="ADS-only low open rear notch and narrow front blade. No magnifying scope. Original canonical 87 cubes/UV/hip/third/inspect/reload preserved. Reference-inspired approximation, not exact ripped optic.",
        outputSha256={str(p.relative_to(ROOT)):sha(b) for p,b in out.items()})
    out[ROOT/"art/weapons/w156/ace-sight.json"]=enc(manifest)
    return out

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--verify",action="store_true");args=parser.parse_args()
    out=generate()
    for p,b in out.items():
        if args.verify:assert p.read_bytes()==b,p
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    print("Ace W156",len(out),"verified" if args.verify else "generated","92 cubes, no scope")
