"""Round-trip every exported block, then validate all route and marker cells."""
import json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/maps'));sys.path.insert(0,str(ROOT/'scripts/strikes'))
import section_nbt
import build_exodus_maps as e

def main():
    world=np.load(e.WORK/'final.npy',mmap_mode='r');states=json.loads((e.WORK/'final-palette.json').read_text());ids={s:i for i,s in enumerate(states)}
    path=e.NBT_OUT/'world.nbt';root=section_nbt.load(path);count=0;section_count=0
    assert list(root['bounds']['min'])==list(e.ORIGIN)
    assert list(root['bounds']['max'])==[e.ORIGIN[0]+world.shape[2]-1,e.ORIGIN[1]+world.shape[0]-1,e.ORIGIN[2]+world.shape[1]-1]
    for (cx,cy,cz),palette,index in section_nbt.sections(root):
        x,y,z=cx*16-e.ORIGIN[0],cy*16-e.ORIGIN[1],cz*16-e.ORIGIN[2]
        assert min(x,y,z)>=0 and x<world.shape[2] and y<world.shape[0] and z<world.shape[1]
        actual=np.array([ids[s]for s in palette],np.uint16)[index];expected=np.zeros((16,16,16),np.uint16)
        crop=world[y:y+16,z:z+16,x:x+16];expected[:crop.shape[0],:crop.shape[1],:crop.shape[2]]=crop
        assert np.array_equal(actual,expected),(cx,cy,cz)
        count+=int(np.count_nonzero(actual));section_count+=1
    assert count==int(np.count_nonzero(world))
    route=np.load(e.WORK/'route.npy');plan=json.loads((e.OUT/'beats.json').read_text())
    barrier=states.index('minecraft:red_stained_glass');light=states.index('minecraft:light[level=14,waterlogged=false]')
    def clear(v):return np.isin(v,[0,light,barrier]).all()
    m=e.sampler()
    for i,(x,y,z)in enumerate(route):
        assert world[y-1,z,x]not in (0,light,barrier),('floor',i)
        floor_state=states[int(world[y-1,z,x])].split('[')[0]
        assert not floor_state.endswith('_wall') and floor_state not in ('minecraft:iron_bars','minecraft:iron_chain'),('decorative support',i)
        assert clear(world[y:y+2,z,x]),('headroom',i)
        if i:
            delta=route[i]-route[i-1]
            assert abs(delta[0])+abs(delta[2])==1 and -3<=delta[1]<=1,('move',i,delta)
            a=route[i-1];rise=m.floor_height(world,states,y,z,x)-m.floor_height(world,states,a[1],a[2],a[0])
            assert -3<=rise<=1.25,('physical floor transition',i,rise)
    marker_doc=json.loads((e.OUT/'zones/markers.json').read_text())['zones']['world']['markers']
    for marker in marker_doc:
        if marker['id'].endswith('GEN'):continue
        x,y,z=map(int,marker['pos']);assert world[y-1,z,x]not in (0,light,barrier),('marker floor',marker['id'])
        assert clear(world[y:y+2,z,x]),('marker clearance',marker['id'])
    for beat in plan['beats']:
        if isinstance(beat.get('gate'),dict):
            assert all(beat['gate']['closed']),beat['id']
            for x,y,z in beat['gate']['cells']:assert world[y,z,x]==barrier
    result=dict(nbtBytes=path.stat().st_size,sections=section_count,blocks=count,roundTrip='all blocks exact',routeCells=len(route),routeMaxRise=1.25,routeMaxDrop=3,markers=len(marker_doc),gates=4,nativePlay='not run')
    print(json.dumps(result,indent=1));(e.WORK/'verification.json').write_text(json.dumps(result,indent=1))

if __name__=='__main__':main()
