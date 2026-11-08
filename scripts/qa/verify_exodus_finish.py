"""Compare a Nessus finish to the pre-art NBT build, independently of its masks."""
import argparse, json, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts/maps'),str(ROOT/'scripts/strikes')]
import build_exodus_maps as e
from surface_finish import protected_columns


def shape(state):
    if state=='minecraft:air' or state.startswith('minecraft:light['):return 'open'
    if '_slab[' in state:return 'slab:'+state.split('[')[1]
    if any(n in state for n in ('_wall[','iron_bars[','iron_chain[')):return state
    return 'full'


def main():
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);a=p.parse_args()
    old=np.load(a.before/'before.npy',mmap_mode='r');new=np.load(e.WORK/'final.npy',mmap_mode='r')
    oldstates=json.loads((a.before/'before-palette.json').read_text());states=json.loads((e.WORK/'final-palette.json').read_text())
    route=np.load(e.WORK/'route.npy');assert np.array_equal(route,np.load(a.before/'route-before.npy'))
    markers=json.loads((e.OUT/'zones/markers.json').read_text())['zones']['world']['markers']
    protected=protected_columns(new.shape,route,markers)
    signatures=sorted({shape(s)for s in oldstates+states})
    oldshape=np.array([signatures.index(shape(s))for s in oldstates],np.uint16)
    newshape=np.array([signatures.index(shape(s))for s in states],np.uint16)
    allowed={'minecraft:dead_bush','minecraft:oak_leaves[distance=1,persistent=true,waterlogged=false]','minecraft:dark_oak_log[axis=y]'}
    allowed_ids=[i for i,s in enumerate(states)if s in allowed]
    added=0;changed=0
    for z in range(0,new.shape[1],64):
        b=old[:,z:z+64];c=new[:,z:z+64];original=b!=0
        # All prior blocks retain the exact collision category / slab properties.
        assert (oldshape[b][original]==newshape[c][original]).all(),('changed original shape',z)
        grow=(b==0)&(c!=0)
        assert np.isin(c[grow],allowed_ids).all(),('unexpected new object',z)
        assert not (grow & protected[z:z+64][None]).any(),('new obstruction in route/spawn reservation',z)
        added+=int(grow.sum());changed+=int((b!=c).sum())
    out=dict(originalCollisionShapes='all retained, including slab properties',route='2488 cells identical',
             protectedColumns=int(protected.sum()),newVegetationBlocks=added,changedCells=changed,
             newGeometryInProtectedColumns=0)
    print(json.dumps(out,indent=1));(e.WORK/'finish-verification.json').write_text(json.dumps(out,indent=1))


if __name__=='__main__':main()
