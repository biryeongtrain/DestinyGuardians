"""A collision-safe gap under the plaza must not become the hub's spawn."""
import tempfile
import unittest
from pathlib import Path

import numpy as np

from export_schematic import write_vox
from inspect_walkways import inspect


class SpawnInspectionTests(unittest.TestCase):
    def test_open_sky_chooses_visible_floor_over_enclosed_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tower.vox.gz"
            # Both surfaces have a 3x3 floor and two clear head blocks.
            # Only the upper one belongs to the visible outdoor plaza.
            points = [[x, y, z] for x in range(-3, 4) for z in range(-3, 4) for y in (70, 74)]
            points.append([10, 84, 10])
            xyz = np.array(points, dtype=np.int32)
            write_vox(path, xyz, np.zeros(len(xyz), dtype=np.uint16), ["minecraft:smooth_stone"])
            outside = inspect(path, [0, 71, 0])
            covered = inspect(path, [0, 71, 0], open_sky=False)
            self.assertTrue(outside["requiresOpenSky"])
            self.assertEqual(75, outside["closest"][0]["y"])
            self.assertEqual(71, covered["closest"][0]["y"])


if __name__ == "__main__":
    unittest.main()
