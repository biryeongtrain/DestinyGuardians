#!/usr/bin/env python3
"""Export Guardian Rises' unchanged authoring grids to shared NBT chunk templates."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "maps"))
from zone_nbt import ROOT, export

NAMES = ("gateway", "breach", "divide", "dock13")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-version", type=int, default=5023)
    args = parser.parse_args()
    results = {}
    for i, name in enumerate(NAMES):
        results[name] = export(ROOT / f"src/main/resources/data/destiny/guardian_rises/zones/{name}.zone",
            ROOT / f"src/main/resources/data/destiny/map_template/guardian_rises/{name}.nbt",
            [2048 + i * 4096, 64, 2048], args.data_version)
    target = ROOT / "src/main/resources/data/destiny/map_template/guardian_rises/manifest.json"
    target.write_text(json.dumps(dict(schema=1, format="Nucleoid MapTemplate", dataVersion=args.data_version,
        zones=results), indent=2) + "\n")
    print(json.dumps(results, indent=2))

if __name__ == "__main__": main()
