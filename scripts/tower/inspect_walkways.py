#!/usr/bin/env python3
"""Find supported, unobstructed spawn positions in the converted courtyard."""
import argparse
import json
from pathlib import Path

import numpy as np

from preview_map import read_map


def inspect(path, wanted, open_sky=True):
    palette, records = read_map(path)
    xyz = np.column_stack([records[k] for k in ("x", "y", "z")]).astype(np.int32)
    lo, hi = xyz.min(0), xyz.max(0)
    grid = np.zeros(tuple(hi - lo + 1), dtype=np.bool_)
    q = xyz - lo
    grid[q[:, 0], q[:, 1], q[:, 2]] = True
    candidates = grid[:, :-2, :] & ~grid[:, 1:-1, :] & ~grid[:, 2:, :]
    # A safe spawn needs a supported 3x3 floor and two clear blocks above it.
    wide = np.zeros_like(candidates)
    wide[1:-1, :, 1:-1] = np.logical_and.reduce([
        candidates[1 + dx:candidates.shape[0] - 1 + dx, :, 1 + dz:candidates.shape[2] - 1 + dz]
        for dx in (-1, 0, 1) for dz in (-1, 0, 1)
    ])
    locations = np.argwhere(wide) + lo
    locations[:, 1] += 1
    if open_sky:
        # Two clear blocks can still be an enclosed gap below a rendered floor.
        # A hub spawn should see the plaza, so select the highest surface column.
        heights = np.where(grid, np.arange(grid.shape[1])[None, :, None], -10000).max(1) + lo[1] + 1
        lx, lz = locations[:, 0] - lo[0], locations[:, 2] - lo[2]
        locations = locations[heights[lx, lz] == locations[:, 1]]
    # Ground-level courtyard excludes rooftop and substructure spawn candidates.
    locations = locations[(locations[:, 1] >= 69) & (locations[:, 1] <= 80)]
    score = ((locations - np.array(wanted)) ** 2 * np.array([1, 5, 1])).sum(1)
    closest = locations[np.argsort(score)[:12]]
    floor = []
    for pos in closest:
        x, y, z = (int(v) for v in pos)
        exact = records[(records["x"] == x) & (records["y"] == y - 1) & (records["z"] == z)]
        floor.append({"x": x + .5, "y": y, "z": z + .5,
                      "floor": palette[int(exact[0]["p"])], "supported3x3": True,
                      "clearHeadroom": 2})
    return {"requested": wanted, "requiresOpenSky": open_sky,
            "groundSpawnCandidateCount": len(locations), "closest": floor}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--wanted", nargs=3, type=int, default=[44, 75, -51])
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-covered", action="store_true", help="Permit covered positions; review their actual view separately")
    args = parser.parse_args()
    result = inspect(args.input, args.wanted, not args.allow_covered)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
