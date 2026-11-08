"""Nessus art direction over the assembled Exodus bake; source assets stay read-only.

Artist references (visual review 2026-11-08):
https://sklipowicz.artstation.com/projects/O433e — red growth, dark bark, pale rock
https://pittskrieg.artstation.com/projects/9bNKN — Exodus Black metal interiors
https://mjcr24.artstation.com/projects/ELOn5N — local light / shadow hierarchy

This is an authored Minecraft adaptation, not recovered Destiny shader output.
"""
import json
import numpy as np
from surface_finish import palette_id, replace_shape, patch_field, protected_columns


def source_roles(work, shape):
    """Recover terrain and surface orientation from the retained baked samples."""
    roles = np.zeros(shape, np.uint8)
    paths=sorted((work / 'samples').glob('*.npz'))
    expected={f'{x},{z}.npz'for x in range(505,1620,160)for z in range(-1000,680,160)}
    if {p.name for p in paths} != expected:
        raise ValueError('Nessus finish needs all 77 baked sample tiles; run the voxel stage first')
    for path in paths:
        tx, tz = map(int, path.stem.split(','))
        lo_x, lo_z = tx-8, tz-8
        hi_x, hi_z = min(tx+160, 1620)+8, min(tz+160, 680)+8
        sx, sz = hi_x-lo_x, hi_z-lo_z
        with np.load(path) as s:
            key, cnt = s['key'], s['cnt']
            x = lo_x + key % sx
            z = hi_z - (key // sx) % sz - 1
            y = key // (sx*sz) + 8
            core = (x >= tx) & (x < min(tx+160,1620)) & (z >= tz) & (z < min(tz+160,680))
            flag = ((s['terr']/cnt > .5).astype(np.uint8)
                    | ((s['up']/cnt > .55).astype(np.uint8) << 1)
                    | ((s['down']/cnt > .55).astype(np.uint8) << 2))
            roles[y[core], 679-z[core], x[core]-505] = flag[core]
    return roles


def apply(world, states, work, route, markers):
    pid = lambda s: palette_id(states, s)
    before = list(states)
    protected = protected_columns(world.shape, route, markers)
    roles = source_roles(work, world.shape)
    # Carry the terrain role into the three support layers added by voxelization.
    terrain=roles&1
    for depth in range(1,4):
        roles[:-depth] |= (terrain[depth:] & (world[:-depth] != 0))
    del terrain
    neutral = {'snow_block','calcite','polished_diorite','smooth_stone','andesite',
               'polished_andesite','stone','stone_bricks','tuff','polished_tuff',
               'white_concrete','light_gray_concrete','light_gray_terracotta'}
    ground = {'podzol','coarse_dirt','rooted_dirt','dirt','moss_block','packed_mud','soul_soil'}
    # Each replacement has an actual slab counterpart, so ramps retain their height.
    warm_rock = [('calcite','smooth_quartz_slab'),('smooth_quartz','smooth_quartz_slab'),
                 ('tuff','tuff_slab')]
    steel = [('polished_andesite','polished_andesite_slab'),('cyan_terracotta','smooth_stone_slab'),
             ('polished_deepslate','polished_deepslate_slab')]
    vex = [('smooth_quartz','smooth_quartz_slab'),('cyan_terracotta','polished_andesite_slab'),
           ('polished_diorite','polished_diorite_slab')]
    changed, leaf_litter = 0, 0
    # Process vertical strips to bound working memory even for large templates.
    for z0 in range(0,world.shape[1],64):
        block = world[:,z0:z0+64,:]; role = roles[:,z0:z0+64,:]
        yy,zz,xx = np.nonzero(block)
        old = block[yy,zz,xx].copy(); original = old.copy()
        rr = role[yy,zz,xx]; zz = zz+z0
        field = patch_field(xx+505,679-zz)
        natural = (rr & 1) != 0
        exterior = (xx+505 < 1180) & (679-zz > -805) & (679-zz < -145)
        for i,state in enumerate(before):
            name = state.split(':')[1].split('[')[0]
            # Match base material of slab variants without touching decorative shapes.
            base = name.removesuffix('_slab')
            base = {'stone_brick':'stone_bricks'}.get(base,base)
            if base not in neutral | ground:
                continue
            match = original == i
            if not match.any(): continue
            n = match & natural
            choices = np.where(field < -.63,2,np.where(field > .4,1,0))
            for j,(full,slab) in enumerate(warm_rock[:3]):
                mask = n & (choices==j)
                old[mask] = pid(replace_shape(state, full, slab))
            # Inside the crash site the floor is dark soil/debris. Pale stone
            # is reserved for exposed rock, never a yellow carpet in the hull.
            inside_floor=n & ~exterior & ((rr&2)!=0)
            old[inside_floor]=pid(replace_shape(state,'gray_terracotta','polished_deepslate_slab'))
            if base in ground:
                old[n & ~exterior]=pid(replace_shape(state,'soul_soil',None))
            # Original bright painted panels remain bright enough to read, but
            # undersides/floors gain steel texture instead of emitting flat white.
            s = match & ~natural
            for region,kit in ((exterior,vex),(~exterior,steel)):
                choice = np.where(field > .48,1,0)
                if kit is steel:
                    choice = np.where((rr & 4)!=0,2,choice)
                for j,(full,slab) in enumerate(kit):
                    mask = s & region & (choice==j)
                    old[mask] = pid(replace_shape(state,full,slab))
        changed += int(np.count_nonzero(old != original))
        block[yy,zz-z0,xx] = old
    # Only the highest natural full-block surface receives living ground cover.
    # Roofs, caves, route ramps and all spawn/generator columns stay clear.
    solid = world != 0
    for i,s in enumerate(states):
        if s.startswith('minecraft:light['): solid[world==i]=False
    highest = world.shape[0]-1-np.argmax(solid[::-1],axis=0)
    zz,xx = np.indices(highest.shape); yy = highest
    rr = roles[yy,zz,xx]; field = patch_field(xx+505,679-zz)
    exterior = (xx+505<1180)&(679-zz>-805)&(679-zz<-145)
    full = np.array(['[' not in s and s!='minecraft:air' for s in states])
    bed = exterior & ((rr&3)==3) & full[world[yy,zz,xx]] & (yy<world.shape[0]-20)
    red = bed & (field > -.04)
    # Biome-tinted grass gives the red ground a living surface and supports
    # real grass clumps. Terracotta beneath short grass would fail survival.
    world[yy[red],zz[red],xx[red]] = pid('grass_block[snowy=false]')
    leaf_litter = int(red.sum())
    root = pid('short_grass'); leaves = pid('oak_leaves[distance=1,persistent=true,waterlogged=false]')
    log = pid('dark_oak_log[axis=y]')
    rng = np.random.default_rng(661193)
    red[:10]=False;red[-10:]=False;red[:,:10]=False;red[:,-10:]=False
    candidates = np.argwhere(red & ~protected)
    rng.shuffle(candidates)
    plants = bushes = trees = 0
    for z,x in candidates:
        y = int(highest[z,x])+1
        # Deterministic clusters with open breaks rather than carpeted collision.
        if rng.random() < .28 and world[y,z,x]==0:
            world[y,z,x]=root;plants+=1
    occupied = np.zeros_like(protected)
    def grow(cells,material):
        nonlocal occupied
        for x,y,z in cells:
            if (0<=x<world.shape[2] and 0<=z<world.shape[1] and 0<=y<world.shape[0]
                and not protected[z,x] and world[y,z,x] in (0,root)):
                world[y,z,x]=material
    for z,x in candidates:
        y = int(highest[z,x])+1
        if occupied[z,x] or rng.random()>.018:continue
        # Bush volumes follow an ellipsoid, with lobed silhouettes.
        r=int(rng.integers(2,4))
        if protected[max(0,z-r):z+r+1,max(0,x-r):x+r+1].any():continue
        grow([(x+dx,y+dy,z+dz) for dy in range(3) for dz in range(-r,r+1) for dx in range(-r,r+1)
              if dx*dx+dz*dz+(dy*1.7)**2<r*r+1],leaves)
        occupied[max(0,z-7):z+8,max(0,x-7):x+8]=True;bushes+=1
        if bushes>=650:break
    for z,x in candidates:
        if trees>=45:break
        if rng.random()>.003:continue
        if protected[max(0,z-10):z+11,max(0,x-10):x+11].any():continue
        y=int(highest[z,x])+1;h=int(rng.integers(10,18))
        # Require a genuinely open volume; do not thread a trunk through the ship.
        if world[y:y+h+4,z-4:z+5,x-4:x+5].shape!=(h+4,9,9):continue
        volume=world[y:y+h+4,z-4:z+5,x-4:x+5]
        if np.isin(volume,[0,root,leaves]).mean()<.98:continue
        bend=int(rng.choice([-1,1]));trunk=[]
        for dy in range(h):
            bx=x+bend*(dy//6)
            trunk += [(bx,y+dy,z),(bx+1,y+dy,z)]
        grow(trunk,log)
        for bx,by,bz,r in [(x+bend*2,y+h-1,z,5),(x-3,y+h-3,z+3,4),(x+4,y+h-4,z-3,4)]:
            grow([(bx+dx,by+dy,bz+dz)for dy in range(-2,3)for dz in range(-r,r+1)for dx in range(-r,r+1)
                  if dx*dx+dz*dz+dy*dy*3<r*r],leaves)
        trees+=1
    # Turn the uniform level-14 fill into localized readable light pools.
    lighting = boss_lighting = 0
    for i,s in enumerate(before):
        if s.startswith('minecraft:light['):
            mask=world==i;lighting+=int(mask.sum());world[mask]=pid('light[level=11,waterlogged=false]')
            yy,zz,xx=np.nonzero(mask)
            boss=(xx+505<900)&(679-zz<-760)
            world[yy[boss],zz[boss],xx[boss]]=pid('light[level=13,waterlogged=false]')
            boss_lighting+=int(boss.sum())
    fixtures=0
    for k in range(0,len(route),22):
        x,y,z=map(int,route[k])
        for dx,dz in ((3,0),(-3,0),(0,3),(0,-3)):
            col=world[y+4:min(y+20,world.shape[0]),z+dz,x+dx]
            for dy in np.flatnonzero(col):
                py=y+4+int(dy);s=states[int(world[py,z+dz,x+dx])]
                if '[' not in s and not s.endswith('air'):
                    world[py,z+dz,x+dx]=pid('ochre_froglight[axis=y]' if (k//22)%3 else 'sea_lantern')
                    fixtures+=1
                break
            if fixtures and fixtures%2==0:break
    report=dict(version=3,materialCells=changed,redGroundCells=leaf_litter,grassClumps=plants,
                bushes=bushes,trees=trees,fillLights=lighting,fillLevel=11,ceilingFixtures=fixtures,
                bossFillLights=boss_lighting,bossFillLevel=13,
                protectedColumns=int(protected.sum()),biome='destiny:nessus',
                policy='baked geometry + authored surface finishes and outdoor vegetation; original slab properties retained')
    (work/'nessus-art.json').write_text(json.dumps(report,indent=1))
    print('Nessus finish',json.dumps(report),flush=True)
    return report
