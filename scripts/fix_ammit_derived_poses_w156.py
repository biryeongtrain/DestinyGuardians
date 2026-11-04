#!/usr/bin/env python3
"""Apply W156 native ITEM-arm correction after art/aim/reload/swap generation.
Only Ammit non-twohand third-person rotations exactly equal to the old Rx90
are touched. Independent animation first-person transforms and all geometry stay.
"""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def pending():
    out={}
    for p in (ROOT/"src/main/resources/assets/destiny/models").rglob("ammit_ar2*.json"):
        if "_twohand" in p.stem:continue
        d=json.loads(p.read_bytes());changed=False
        for ctx in ("thirdperson_righthand","thirdperson_lefthand"):
            t=d.get("display",{}).get(ctx)
            if t and t.get("rotation")==[90,0,0]:t["rotation"]=[72,0,0];changed=True
        if changed:out[p]=(json.dumps(d,indent=2,ensure_ascii=False)+"\n").encode()
    return out
if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--verify",action="store_true");args=parser.parse_args();out=pending()
    if args.verify:assert not out,"Stale Ammit native thirdperson rotation: "+str(list(out))
    else:
        for p,b in out.items():p.write_bytes(b)
    print("Ammit derived pose",len(out),"pending" if args.verify else "patched")
