#!/usr/bin/env python3
"""Exodus Crash: voxelize the four bubbles into ONE continuous block world (no zone teleports).

Source: Exodus-Crash-Strike-KO-2026-11-08/maps_baked/Exodus_Crash_Continuous.baked.glb (read-only).
World mapping (shared by every region so neighbours abut exactly):  wx = floor(src.x) - XO,  wy = floor(src.z) - ZO,
wz = floor(-src.y) - YO. The assembled bake retains overlapping, vertically stacked geometry.
Stage 1 `voxel` writes a uint16 memmap + palette; later stages cut templates, markers and routes from it.
Run with numpy + Pillow (/tmp/venv/bin/python).
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = Path('/Users/qf/Downloads/Exodus-Crash-Strike-KO-2026-11-08/Exodus-Crash-Strike-KO-2026-11-08')
WORK = Path('/tmp/exodus-r3')
WORK.mkdir(parents=True, exist_ok=True)
# source extent that holds any gameplay geometry (x, y) and Z range
X0, X1, Y0, Y1, Z0, Z1 = 505, 1620, -1000, 680, -125, 90
XO, YO, ZO = X0, -Y1, Z0 - 8          # wx = ix - XO, wz = (-iy) - YO ... see below
WX, WZ, WY = X1 - X0, Y1 - Y0, Z1 - Z0 + 16
TILE, MARGIN = 160, 8

sys.path.insert(0, str(ROOT / 'scripts/maps'))
import baked_source
from walk_route import astar, reachable
from exodus_palette import EXTRA_PALETTE

def sample_identity():
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sourceSha256=sha(SRC/'maps_baked/Exodus_Crash_Continuous.baked.glb'),
                sourceBounds=[X0,X1,Y0,Y1,Z0,Z1],step=.3,tile=TILE,margin=MARGIN,
                bakeReaderSha256=sha(ROOT/'scripts/maps/baked_source.py'),
                samplerSha256=sha(ROOT/'scripts/campaign/rising_maps.py'))

def sampler():
    spec = importlib.util.spec_from_file_location('s', ROOT / 'scripts/campaign/rising_maps.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    ev = WORK / 'ev'; ev.mkdir(parents=True, exist_ok=True)
    m.SRC = SRC; m.EVIDENCE = ev; m.CACHE_DIR = ev / 'cache'; m.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    m._load_full_texture = lambda p: np.asarray(Image.open(p).convert('RGBA'), dtype=np.float32) / 255
    m.PALETTE_DEF.extend(EXTRA_PALETTE)
    return m

def voxel(recolor=False):
    m = sampler(); pal = m.Palette()
    identity = sample_identity(); identity_file=WORK/'sample-identity.json'
    if identity_file.exists() and json.loads(identity_file.read_text()) != identity:
        raise SystemExit('Source/sampler changed: use a fresh WORK directory before reusing the sample cache')
    if not identity_file.exists() and (WORK/'samples').exists():
        raise SystemExit('Unidentified sample cache: use a fresh WORK directory')
    identity_file.write_text(json.dumps(identity,indent=1))
    world = np.lib.format.open_memmap(WORK / 'world.npy', mode='r+' if (WORK / 'world.npy').exists() else 'w+', dtype=np.uint16, shape=(WY, WZ, WX))
    glb = baked_source.load(SRC / 'maps_baked/Exodus_Crash_Continuous.baked.glb', m)
    m.sample_instance = lambda g, i, lo, hi, step: baked_source.sample_instance(g, i, lo, hi, step, m)
    pf = WORK / 'palette.json'
    if pf.exists():
        for s in json.loads(pf.read_text()): pal.id(s)
    done = WORK / 'tiles.done'; finished = set(done.read_text().split()) if done.exists() and not recolor else set()
    for ty in range(Y0, Y1, TILE):
        for tx in range(X0, X1, TILE):
            key = f'{tx},{ty}'
            if key in finished: continue
            xs = np.arange(tx, min(tx + TILE, X1)); ys = np.arange(ty, min(ty + TILE, Y1))
            t0 = time.time()
            lo = [tx - MARGIN, ty - MARGIN, Z0]; hi = [min(tx + TILE, X1) + MARGIN, min(ty + TILE, Y1) + MARGIN, Z1]
            grid = m.Grid(lo, hi, 1.0)
            cache = WORK/'samples';cache.mkdir(exist_ok=True);sample_file=cache/(key+'.npz')
            if sample_file.exists():
                saved=np.load(sample_file);agg=m.Agg();agg.key=saved['key'];agg.occ=saved['occ'];agg.f={field:saved[field]for field in agg.FIELDS}
            else:
                agg = m.voxelize(glb, grid, lo, hi, step=.3, log=lambda *a: None)
            if len(agg.key):
                if not sample_file.exists():np.savez_compressed(sample_file, key=agg.key, occ=agg.occ, **agg.f)
                # Average baked albedo in linear RGB, then enter the existing
                # perceptual Minecraft palette classifier in sRGB exactly once.
                for channel in ('r', 'g', 'b'):
                    agg.f[channel] = baked_source.linear_to_srgb(agg.f[channel] / agg.f['cnt']) * agg.f['cnt']
                labels, terr, _ = m.classify(agg, pal); labels = m.majority_smooth(grid, agg.key, labels)
                st = m.shape_blocks(grid, agg, labels, terr, pal, log=lambda *a: None)   # [y, z, x]
                # grid: x idx = ix - lo.x ; z idx = (-iy) - (-hi.y) ; y idx = iz - lo.z
                sy, sz, sx = st.shape
                for yy in range(len(ys)):
                    iy = ys[yy]; gz = (-iy - 1) - (-hi[1])       # cell [iy, iy+1) -> mc z in [-iy-1, -iy)
                    wz = (-iy - 1) - (-Y1)
                    cx = np.arange(len(xs))
                    gx = xs[cx] - lo[0]
                    if gz < 0 or gz >= sz: continue
                    col = st[:, gz, :][:, gx]                     # [y, n]
                    h = min(sy, WY - 8)
                    world[8:8 + h, wz, xs[cx] - X0] = col[:h].astype(np.uint16)
            finished.add(key); done.write_text('\n'.join(sorted(finished)))
            pf.write_text(json.dumps(pal.states)); world.flush()
            print(key, round(time.time() - t0, 1), 'palette', len(pal.states), flush=True)
    print('voxel done')

# ---------------------------------------------------------------------------------------------------------------
# Stage 2: authored adaptations, route, beats, markers and NBT
# ---------------------------------------------------------------------------------------------------------------
import gzip, hashlib, math, struct
OUT = ROOT / 'src/main/resources/data/destiny/exodus_crash'
NBT_OUT = ROOT / 'src/main/resources/data/destiny/map_template/exodus_crash'
ORIGIN = (256, 32, 256)         # template min corner in the run world

# Beat table. `at` is a route-cell index (route = shortest walk from the arrival pad to the boss pad).
# kinds: ADVANCE (talk only) | COMBAT | CHARGE (carry Arc charges to a generator) | DEFEND (hold a Ghost hack) | BOSS
BEATS = [
 dict(id='B00', kind='ADVANCE', at=30, title='엑소더스 블랙에 있는 벡스와 구원의 가문 세력을 찾으세요.', short='앞으로 나아가기'),
 dict(id='B01', kind='COMBAT', at=140, title='구역 내 몰락자를 처치하세요.', short='몰락자 처치',
      waves=[['DREG', 4], ['VANDAL', 2], ['SHANK', 2]]),
 dict(id='B02', kind='COMBAT', at=340, title='구역 내 과충전된 섕크나 시공 섕크를 제거하세요.', short='섕크 파괴',
      waves=[['SHANK', 5], ['DREG', 3], ['VANDAL', 2]]),
 dict(id='B03', kind='CHARGE', at=560, title='벡스로부터 전기 구체를 획득하여, 몰락자 방벽을 과부하시키세요.', short='전기 충전', need=3, gate=True,
      waves=[['GOBLIN', 6], ['HOBGOBLIN', 3], ['DREG', 3]]),
 dict(id='B04', kind='COMBAT', at=800, title='강력한 몰락자를 처치하세요.', short='강력한 몰락자 처치',
      waves=[['CAPTAIN', 1], ['VANDAL', 3], ['MARAUDER', 2], ['DREG', 4]]),
 dict(id='B05', kind='COMBAT', at=955, title='엑소더스 블랙의 추락 지점을 계속해서 수색하세요.', short='벡스 전투',
      waves=[['GOBLIN', 6], ['HOBGOBLIN', 4], ['MINOTAUR', 1], ['DREG', 3]]),
 dict(id='B06', kind='COMBAT', at=1100, title='고스트가 해킹을 계속할 수 있도록 몰락자 부관을 처치하세요.', short='부관 처치',
      waves=[['CAPTAIN', 2], ['MARAUDER', 2], ['VANDAL', 3]]),
 dict(id='B07', kind='COMBAT', at=1290, title='남은 강력한 몰락자를 처치해 2차 방벽을 무너뜨리세요.', short='강력한 몰락자 처치', gate=True,
      waves=[['CAPTAIN', 1], ['VANDAL', 4], ['MARAUDER', 2], ['SHANK', 4], ['DREG', 6]]),
 dict(id='B08', kind='COMBAT', at=1470, title='엑소더스 블랙에 있는 벡스와 구원의 가문 세력을 찾으세요.', short='벡스 전투',
      waves=[['GOBLIN', 8], ['HARPY', 3], ['HOBGOBLIN', 3], ['MINOTAUR', 1]]),
 dict(id='B09', kind='CHARGE', at=1710, title='전기 구체를 모아 몰락자 발전기를 과부하시키세요.', short='전기 충전', need=4, gate=True,
      waves=[['GOBLIN', 8], ['HOBGOBLIN', 4], ['HARPY', 2], ['DREG', 4]]),
 dict(id='B10', kind='DEFEND', at=1900, title='방벽을 해제하는 고스트를 보호하세요.', short='해킹 진행 상황', seconds=60, gate=True,
      waves=[['GOBLIN', 6], ['VANDAL', 4], ['HOBGOBLIN', 3], ['MARAUDER', 2], ['HARPY', 2]]),
 dict(id='B11', kind='BOSS', at=2098, title='구원의 가문 파이키스를 처치하고 엑소더스 블랙에서 몰락자를 몰아내세요.', short='구원의 가문 파이키스 처치',
      waves=[['PYKIS', 1], ['DREG', 4], ['VANDAL', 3], ['SHANK', 3], ['CYCLOPS', 1]]),
]

# Reviewed three-dimensional landmarks, in source Z-up. Parent placement
# coordinates are hints only: snap to start-connected floor, never a roof or
# an isolated cavity merely because it is nearest in the horizontal plane.
LANDMARKS = [
    ('B01', (1440, 441, -64)), ('B02', (1378, 365, -73)),
    ('trench_bend', (1337, 220, -84)), ('B03', (1244, 65, -58)),
    ('B04', (1267, -43, -34)), ('B05', (1198, -195, -44)),
    ('B06', (1197, -240, -45)), ('B07', (1115, -328, -48)),
    ('B08', (1040, -655, -46)), ('B09', (935, -718, -71)),
    ('B10', (852, -790, -71)), ('B11', (828, -812, -74)),
]

def stage2():
    m = sampler()
    world = np.array(np.load(WORK / 'world.npy', mmap_mode='r'))
    states = json.loads((WORK / 'palette.json').read_text())
    def pid(s):
        if s not in states: states.append(s)
        return states.index(s)
    W = lambda x, y, z: (int(x) - X0, int(z) - Z0 + 8, Y1 - int(y) - 1)
    S = lambda c: (int(c[0] + X0), int(Y1 - c[2] - 1), int(c[1] + Z0 - 8))
    andesite = pid('minecraft:polished_andesite')
    adaptations = []
    def pad(c, r, h, floor, name):
        x, y, z = c
        for dz in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r:
                    world[y:y + h, z + dz, x + dx] = 0; world[y - 1, z + dz, x + dx] = floor
        adaptations.append(dict(kind='authored_pad', name=name, centre=S(c), radius=r, height=h))
    # Only the arrival pad is authored. Full assembled geometry already joins
    # the regions; do not cut a seam ramp or flatten the whole boss chamber.
    start_src = (1474, 491, -55); start = W(*start_src)
    pad(start, 4, 5, andesite, 'arrival')
    names = np.array([s.split(':')[1].split('[')[0] for s in states]); open_ids = np.nonzero(np.isin(names, ['air', 'light', 'snow']))[0]
    pas = np.zeros(world.shape, bool)
    for z0 in range(0, world.shape[1], 128): pas[:, z0:z0 + 128, :] = np.isin(world[:, z0:z0 + 128, :], open_ids)
    # First trace the reviewed corridor on the surface grid. At one-block
    # resolution a few original sloping parts become 1.5-block slab jumps, and
    # thin rails can masquerade as floor. Repair only those supporting cells,
    # then recompute reachability with the stricter physical floor model.
    provisional_st = np.zeros_like(pas); provisional_st[1:-1] = pas[1:-1] & pas[2:] & ~pas[:-2]
    provisional_seen = m.reach(provisional_st, pas, start, max_down=3)
    provisional_connected = provisional_st & provisional_seen
    provisional_moves = m.route_moves(provisional_st, pas, max_down=3)
    provisional_path = [start]
    for name, source in LANDMARKS:
        target = m.nearest_standable(provisional_connected, W(*source), 12)
        if target is None: raise SystemExit(f'No source floor near {name}')
        provisional_path.extend(astar(provisional_moves, provisional_path[-1], {target})[1:])
    repaired = set()
    def repair_floor(c, target_state, reason):
        x,y,z=c; old=states[int(world[y-1,z,x])]
        world[y-1,z,x]=pid(target_state)
        if (x,y,z) not in repaired:
            adaptations.append(dict(kind='single_support_repair', centre=S(c), before=old, after=target_state, reason=reason))
            repaired.add((x,y,z))
    for c in provisional_path:
        x,y,z=c; state=states[int(world[y-1,z,x])];base=state.split('[')[0]
        if base.endswith('_wall') or base in ('minecraft:iron_bars','minecraft:iron_chain'):
            full={'minecraft:mud_brick_wall':'minecraft:mud_bricks'}.get(base,base.removesuffix('_wall')) if base.endswith('_wall') else 'minecraft:polished_andesite'
            repair_floor(c,full,'stable one-block support instead of a decorative rod/wall')
    for a,b in zip(provisional_path,provisional_path[1:]):
        ha=m.floor_height(world,states,a[1],a[2],a[0]);hb=m.floor_height(world,states,b[1],b[2],b[0])
        low=a if hb-ha>1.25 else b if hb-ha < -3 else None
        if low is not None:
            state=states[int(world[low[1]-1,low[2],low[0]])]
            if '_slab[' not in state or 'type=bottom' not in state:raise SystemExit(f'Unresolved physical step {a}->{b}')
            repair_floor(low,state.replace('type=bottom','type=double'),'half-block correction for rise<=1.25/drop<=3')
    del provisional_st, provisional_seen, provisional_connected, provisional_moves, provisional_path
    support = np.array([not (s.split(':')[1].split('[')[0] in ('air','light','snow','iron_bars','iron_chain') or s.split('[')[0].endswith('_wall')) for s in states])
    st = np.zeros_like(pas); st[1:-1] = pas[1:-1] & pas[2:] & support[world[:-2]]
    offsets = np.array([-.5 if '_slab[' in s and 'type=bottom' in s else 0 for s in states])
    def floor_height(c): return c[1] + offsets[world[c[1]-1,c[2],c[0]]]
    raw_moves = m.route_moves(st, pas, max_down=3)
    def moves(c):
        h = floor_height(c)
        return [n for n in raw_moves(c) if -3 <= floor_height(n)-h <= 1.25]
    seen = reachable(moves, start, st.shape)
    connected = st & seen
    path = [start]; landmark_indices = {'B00': 30}; landmark_info = []
    for name, source in LANDMARKS:
        target = m.nearest_standable(connected, W(*source), 12)
        if target is None: raise SystemExit(f'No start-connected floor near {name}: {source}')
        leg = astar(moves, path[-1], {target})
        path.extend(leg[1:]); landmark_indices[name] = len(path) - 1
        landmark_info.append(dict(id=name, source=list(source), floorSource=S(target), routeIndex=len(path)-1, cells=len(leg)))
        print('landmark', name, S(target), 'leg', len(leg), flush=True)
    boss = path[-1]
    print('route cells', len(path))
    # 3. Beats: trigger = route cell; spawn candidates = reachable cells ahead of it; gates = barrier cross-sections.
    barrier = pid('minecraft:red_stained_glass')
    markers = []; beats = []
    def mk(i, c, role='ground', **tags): markers.append(dict(id=i, pos=[c[0] + .5, float(c[1]), c[2] + .5], yaw=0.0, tags=dict(role=role, **{k: str(v) for k, v in tags.items()})))
    x, y, z = path[0]
    for i, dx in enumerate((-2, 0, 2)): mk(f'WORLD.IN.{i}', (x + dx, y, z), seat=i)
    mk('WORLD.IN', path[0])
    mk('WORLD.OUT', path[-1]); bx, by, bz = boss; mk('WORLD.CHEST', (bx - 8, by, bz))
    pa = np.array(path)
    for beat in BEATS:
        i = landmark_indices[beat['id']]; tx, ty, tz = path[i]
        mk(f"WORLD.{beat['id']}", path[i], beat=beat['id'])
        info = dict(beat); info['at'] = i; info['trigger'] = [tx + .5, float(ty), tz + .5]; info['routeIndex'] = i
        if beat['kind'] in ('COMBAT', 'CHARGE', 'DEFEND', 'BOSS'):
            lo, hi = min(i + 14, len(path) - 2), min(i + 80, len(path) - 1)
            seg = pa[lo:hi] if beat['kind'] != 'BOSS' else pa[max(0, i-70):i+1]
            chosen = []
            cand = []
            for cx, cy, cz in seg[::2]:
                for ox in range(-7, 8, 3):
                    for oz in range(-7, 8, 3):
                        yy = cy
                        for dy in (0, 1, -1, 2, -2):
                            q = (cx + ox, cy + dy, cz + oz)
                            if 0 < q[1] < seen.shape[0] - 5 and seen[q[1], q[2], q[0]] and pas[q[1]:q[1] + 4, q[2], q[0]].all():
                                cand.append(q); break
            rng = np.random.default_rng(int(beat['id'][1:]) * 7919 + 13)
            rng.shuffle(cand)
            for q in cand:
                if all((q[0] - c[0]) ** 2 + (q[2] - c[2]) ** 2 + (q[1] - c[1]) ** 2 >= 25 for c in chosen):
                    chosen.append(q)
                if len(chosen) >= 36: break
            if len(chosen) < 12: raise SystemExit(f"{beat['id']} has only {len(chosen)} spawn cells")
            for k, c in enumerate(chosen): mk(f"WORLD.spawn.{beat['id']}.{k}", c, lane=f"WORLD.{beat['id']}")
            if beat['kind'] in ('CHARGE', 'DEFEND'):
                gi = min(i + 22, len(path) - 1); info['generator'] = [path[gi][0] + .5, float(path[gi][1]), path[gi][2] + .5]
                mk(f"WORLD.{beat['id']}.GEN", path[gi], role='source_prop')
        if beat.get('gate'):
            gi = min(i + 95, len(path) - 6)
            gx, gy, gz = path[gi]; nx, ny, nz = path[gi + 4]; dx, dz = nx - gx, nz - gz; L = max(1.0, math.hypot(dx, dz)); px, pz = -dz / L, dx / L
            cells = []; closed = [False, False]
            for side in (1, -1):
                for k in range(0, 90):
                    xx, zz = round(gx + px * k * side), round(gz + pz * k * side)
                    col = [(xx, yy, zz) for yy in range(gy, min(gy + 6, world.shape[0])) if pas[yy, zz, xx]]
                    if not col or not pas[gy, zz, xx] and not pas[gy + 1, zz, xx]:
                        closed[(0 if side == 1 else 1)] = True; break
                    cells.extend(col)
            cells = sorted(set(cells))
            if not all(closed): print('WARNING gate', beat['id'], 'is open on a side; players could walk around it')
            for cx, cy, cz in cells: world[cy, cz, cx] = barrier
            info['gate'] = dict(cells=[list(c) for c in cells], block='minecraft:red_stained_glass', closed=closed)
            print(beat['id'], 'gate cells', len(cells), 'closed', closed)
        beats.append(info)
    # 3b. Interior lighting: roofed stretches of the route (trench, hull, caves) get invisible light blocks; open sky keeps daylight.
    light = pid('minecraft:light[level=14,waterlogged=false]'); lit = 0
    for k in range(0, len(path), 6):
        x, y, z = path[k]
        if not world[y + 3:min(y + 46, world.shape[0]), z, x].any(): continue
        for ox, oz in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)):
            xx, zz = x + ox, z + oz
            if not (0 <= xx < world.shape[2] and 0 <= zz < world.shape[1]): continue
            if ox or oz:
                if not seen[y, zz, xx]: continue
            for dy in (2, 3, 1):
                if world[y + dy, zz, xx] == 0: world[y + dy, zz, xx] = light; lit += 1; break
    print('light blocks', lit)
    from nessus_finish import apply as finish_nessus
    art = finish_nessus(world, states, WORK, path, markers)
    # 4. Persist world (compressed), markers, beats, NBT.
    sx, sy, sz = world.shape[2], world.shape[0], world.shape[1]
    (OUT / 'zones').mkdir(parents=True, exist_ok=True); NBT_OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'zones' / 'markers.json').write_text(json.dumps(dict(schema=1, zones=dict(world=dict(size=[sx, sy, sz], markers=markers))), ensure_ascii=False))
    # Keep the final point and each beat in the guidance route even when their
    # index is not divisible by six.
    route_indices = sorted(set(range(0, len(path), 6)) | set(landmark_indices.values()) | {len(path)-1})
    (OUT / 'beats.json').write_text(json.dumps(dict(schema=1, origin=list(ORIGIN), route=[list(map(int, path[i])) for i in route_indices], beats=beats), ensure_ascii=False))
    (OUT / 'manifest.json').write_text(json.dumps(dict(schema=1, activity='exodus_crash', source=str(SRC), size=[sx, sy, sz], origin=list(ORIGIN),
        mapping='wx = floor(src.x) - %d; wy = floor(src.z) - %d; wz = %d - floor(src.y) - 1' % (X0, Z0 - 8, Y1), adaptations=adaptations,
        sourceGlb='maps_baked/Exodus_Crash_Continuous.baked.glb', sourceGlbSha256=hashlib.sha256((SRC/'maps_baked/Exodus_Crash_Continuous.baked.glb').read_bytes()).hexdigest(),
        colorPolicy='native baked PNG + BakedColorUV; linear RGB average; scene-default albedo retained with uncertainty; forward/decal and clipped-out layers excluded',
        geometryPolicy='one assembled source; no per-bubble rectangular column ownership; no seam ramp or large boss pad',
        routeModel='ordered 3D landmarks; true slab floor rise <=1.25, drop <=3; rods/walls not support; start-connected floor', landmarks=landmark_info,
        routeCells=len(path), art=art, status='authored Nessus finish generated; verification recorded separately in docs/qa'), ensure_ascii=False, indent=1))
    np.save(WORK/'final.npy',world); np.save(WORK/'route.npy',np.array(path))
    (WORK/'final-palette.json').write_text(json.dumps(states))
    sys.path.insert(0, str(ROOT / 'scripts/maps'))
    import zone_nbt as Z
    export_nbt(world, states, NBT_OUT / 'world.nbt', Z)

def export_nbt(world, states, target, Z, data_version=5023):
    sy, sz, sx = world.shape; chunks = []; count = 0
    for cy in range((sy + 15) // 16):
        for cz in range((sz + 15) // 16):
            for cx in range((sx + 15) // 16):
                blk = world[cy * 16:cy * 16 + 16, cz * 16:cz * 16 + 16, cx * 16:cx * 16 + 16]
                if not blk.any(): continue
                section = np.zeros((16, 16, 16), np.uint16); section[:blk.shape[0], :blk.shape[1], :blk.shape[2]] = blk
                used = np.unique(section).tolist(); count += int(np.count_nonzero(section))
                remap = {v: i for i, v in enumerate(used)}
                entries = [Z.tag(9, 'palette', Z.items(10, [Z.block_state(states[v]) for v in used]))]
                if len(used) > 1:
                    bits = max(4, (len(used) - 1).bit_length()); per = 64 // bits
                    flat = np.vectorize(remap.get)(section.reshape(-1)).astype(np.uint64) if len(used) > 1 else None
                    words = []
                    for off in range(0, 4096, per):
                        grp = flat[off:off + per]; word = 0
                        for j, v in enumerate(grp.tolist()): word |= int(v) << (j * bits)
                        words.append(struct.pack('>Q', word))
                    entries.append(Z.tag(12, 'data', Z.i32(len(words)) + b''.join(words)))
                chunks.append(Z.compound([Z.tag(11, 'pos', Z.ints([cx + ORIGIN[0] // 16, cy + ORIGIN[1] // 16, cz + ORIGIN[2] // 16])),
                                          Z.tag(10, 'block_states', Z.compound(entries))]))
    bounds = Z.compound([Z.tag(11, 'min', Z.ints(list(ORIGIN))), Z.tag(11, 'max', Z.ints([ORIGIN[0] + sx - 1, ORIGIN[1] + sy - 1, ORIGIN[2] + sz - 1]))])
    root = Z.compound([Z.tag(3, 'data_version', Z.i32(data_version)), Z.tag(9, 'chunks', Z.items(10, chunks)), Z.tag(10, 'bounds', bounds),
                       Z.tag(8, 'biome', Z.string('destiny:nessus')), Z.tag(9, 'block_entities', Z.items(10, [])), Z.tag(9, 'regions', Z.items(10, [])),
                       Z.tag(10, 'data', Z.compound([]))])
    target.write_bytes(gzip.compress(Z.tag(10, '', root), compresslevel=9, mtime=0))
    print('nbt', target.stat().st_size, 'sections', len(chunks), 'blocks', count, 'palette', len(states))



if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('stage', choices=['voxel', 'build']); a.add_argument('--recolor',action='store_true')
    r = a.parse_args()
    if r.stage == 'voxel': voxel(r.recolor)
    elif r.stage == 'build': stage2()


