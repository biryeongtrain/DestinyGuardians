#!/usr/bin/env python3
"""Losslessly export authored DGZONE grids to Nucleoid MapTemplate compressed NBT.

No external packages. World origins match DevilsWorldBuild.origin; section palette
packing follows Minecraft PalettedContainer (non-spanning longs, min four bits).
DGZONE is an offline authoring intermediate only; the strike loads the NBT files.
"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "maps"))
from zone_nbt import ROOT, export
NAMES = ("rocketyard", "refinery", "blast", "lair")

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--data-version",type=int,default=5023)
    args=parser.parse_args(); results={}
    for i,name in enumerate(NAMES):
        results[name]=export(ROOT/f"src/main/resources/data/destiny/devils_lair/zones/{name}.zone",
            ROOT/f"src/main/resources/data/destiny/map_template/devils_lair/{name}.nbt",[256+i*512,64,256],args.data_version)
    out=ROOT/"src/main/resources/data/destiny/map_template/devils_lair/manifest.json"
    out.write_text(json.dumps(dict(schema=1,format="Nucleoid MapTemplate",dataVersion=args.data_version,zones=results),indent=2)+"\n")
    print(json.dumps(results,indent=2))
if __name__ == "__main__": main()
