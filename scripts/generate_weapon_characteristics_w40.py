#!/usr/bin/env python3
"""Validate pinned Bungie definitions and reproduce the runtime metadata; no network required."""
from pathlib import Path
import argparse,json
ROOT=Path(__file__).resolve().parents[1]
def generate():
    rows=json.loads((ROOT/"art/weapons/w40/definitions.json").read_text())
    catalog=json.loads((ROOT/"src/main/resources/destiny/weapons/w30.json").read_text())
    assert {r["id"] for r in rows}=={r["id"] for r in catalog} and len(rows)==len(catalog)==63
    for row in rows:
        assert row["slot"] in ("KINETIC","ENERGY","POWER")
        assert row["ammo"] in ("PRIMARY","SPECIAL","HEAVY")
        assert row["damage"] in ("KINETIC","ARC","SOLAR","VOID","STASIS","STRAND")
        assert (row["slot"]=="POWER")==(row["ammo"]=="HEAVY")
        if row["slot"]=="KINETIC":assert row["damage"] in ("KINETIC","STASIS","STRAND")
        if row["slot"]=="ENERGY":assert row["damage"] in ("ARC","SOLAR","VOID")
    return (json.dumps(rows,ensure_ascii=False,indent=2)+"\n").encode()
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--verify",action="store_true");args=p.parse_args()
    target=ROOT/"src/main/resources/destiny/weapons/w40-characteristics.json";data=generate()
    if args.verify:assert target.read_bytes()==data
    else:target.write_bytes(data)
    print("verified" if args.verify else "generated","63 official weapon characteristics")
