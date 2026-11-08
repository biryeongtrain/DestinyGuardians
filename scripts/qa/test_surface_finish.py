"""Regression for high Exodus ceilings mistaken for open sky."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'maps'))
from surface_finish import has_roof,roof_opacity


class RoofTests(unittest.TestCase):
    def test_ceiling_above_old_46_block_cutoff_is_indoors(self):
        states=['minecraft:air','minecraft:stone'];world=np.zeros((100,1,1),np.uint16)
        world[80,0,0]=1
        self.assertTrue(has_roof(world,roof_opacity(states),0,10,0))
        self.assertFalse(has_roof(world,roof_opacity(states),0,81,0))

    def test_thin_decor_and_invisible_fill_do_not_create_a_roof(self):
        states=['minecraft:air','minecraft:iron_bars','minecraft:iron_chain[axis=y]',
                'minecraft:red_stained_glass','minecraft:light[level=13,waterlogged=false]',
                'minecraft:oak_leaves[persistent=true]','minecraft:andesite_wall','minecraft:stone_slab[type=top]']
        world=np.zeros((100,1,1),np.uint16);world[30:36,0,0]=np.arange(1,7)
        opaque=roof_opacity(states)
        self.assertFalse(has_roof(world,opaque,0,10,0))
        world[80,0,0]=7
        self.assertTrue(has_roof(world,opaque,0,10,0))


if __name__=='__main__':unittest.main()
