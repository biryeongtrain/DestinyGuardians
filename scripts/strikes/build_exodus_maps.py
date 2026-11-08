#!/usr/bin/env python3
"""Exodus Crash: voxelize the four bubbles into ONE continuous block world (no zone teleports).

Source: Exodus-Crash-Strike-KO-2026-11-08/maps_glb/*.textured.glb (read-only), Destiny Z-up, 1 unit = 1 block.
World mapping (shared by every region so neighbours abut exactly):  wx = floor(src.x) - XO,  wy = floor(src.z) - ZO,
wz = floor(-src.y) - YO.  Each source column is owned by exactly one bubble GLB (the overlapping terrain is identical).
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
WORK = Path('/tmp/exo')
GLBS = ['prodromus_down__80f360a6', 'exodus_black__80f3405f', 'glade_of_echoes__80f3bd0e', 'ex_077_command__80f35561']
# source extent that holds any gameplay geometry (x, y) and Z range
X0, X1, Y0, Y1, Z0, Z1 = 505, 1620, -890, 680, -125, 25
XO, YO, ZO = X0, -Y1, Z0 - 8          # wx = ix - XO, wz = (-iy) - YO ... see below
WX, WZ, WY = X1 - X0, Y1 - Y0, Z1 - Z0 + 16
TILE, MARGIN = 160, 8

def owner(sx, sy):
    """glb index owning source column (sx, sy) (arrays of cell-centre coordinates)."""
    o = np.full(sx.shape, -1, np.int8)
    o[(sx >= 511) & (sx < 1095) & (sy >= -836) & (sy < -128)] = 2
    o[(sx >= 1060) & (sx < 1295) & (sy >= -580) & (sy < -128)] = 1
    o[(sx >= 1152) & (sx < 1620) & (sy >= -128) & (sy < 676)] = 0
    o[(sx >= 769) & (sx < 879) & (sy >= -884) & (sy < -778)] = 3
    return o

def sampler():
    spec = importlib.util.spec_from_file_location('s', ROOT / 'scripts/campaign/rising_maps.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    ev = WORK / 'ev'; ev.mkdir(parents=True, exist_ok=True)
    m.SRC = SRC; m.EVIDENCE = ev; m.CACHE_DIR = ev / 'cache'; m.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    m._load_full_texture = lambda p: np.asarray(Image.open(p).convert('RGBA'), dtype=np.float32) / 255
    return m

def voxel(only=None):
    m = sampler(); pal = m.Palette()
    world = np.lib.format.open_memmap(WORK / 'world.npy', mode='r+' if (WORK / 'world.npy').exists() else 'w+', dtype=np.uint16, shape=(WY, WZ, WX))
    glbs = [m.Glb(SRC / 'maps_glb' / (g + '.textured.glb')) for g in GLBS]
    pf = WORK / 'palette.json'
    if pf.exists():
        for s in json.loads(pf.read_text()): pal.id(s)
    done = WORK / 'tiles.done'; finished = set(done.read_text().split()) if done.exists() else set()
    for ty in range(Y0, Y1, TILE):
        for tx in range(X0, X1, TILE):
            key = f'{tx},{ty}'
            if key in finished: continue
            xs = np.arange(tx, min(tx + TILE, X1)); ys = np.arange(ty, min(ty + TILE, Y1))
            own = owner(*np.meshgrid(xs + .5, ys + .5))          # [y, x]
            if (own < 0).all(): finished.add(key); continue
            t0 = time.time()
            for gi in sorted(set(own[own >= 0].tolist())):
                if only is not None and gi not in only: continue
                lo = [tx - MARGIN, ty - MARGIN, Z0]; hi = [min(tx + TILE, X1) + MARGIN, min(ty + TILE, Y1) + MARGIN, Z1]
                grid = m.Grid(lo, hi, 1.0); agg = m.voxelize(glbs[gi], grid, lo, hi, step=.3, log=lambda *a: None)
                if not len(agg.key): continue
                labels, terr, _ = m.classify(agg, pal); labels = m.majority_smooth(grid, agg.key, labels)
                st = m.shape_blocks(grid, agg, labels, terr, pal, log=lambda *a: None)   # [y, z, x]
                # grid: x idx = ix - lo.x ; z idx = (-iy) - (-hi.y) ; y idx = iz - lo.z
                sy, sz, sx = st.shape
                for yy in range(len(ys)):
                    for_cols = own[yy] == gi
                    if not for_cols.any(): continue
                    iy = ys[yy]; gz = (-iy - 1) - (-hi[1])       # cell [iy, iy+1) -> mc z in [-iy-1, -iy)
                    wz = (-iy - 1) - (-Y1)
                    cx = np.nonzero(for_cols)[0]
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

def stage2():
    m = sampler()
    world = np.array(np.load(WORK / 'world.npy', mmap_mode='r'))
    states = json.loads((WORK / 'palette.json').read_text())
    def pid(s):
        if s not in states: states.append(s)
        return states.index(s)
    W = lambda x, y, z: (int(x) - X0, int(z) - Z0 + 8, Y1 - int(y) - 1)
    S = lambda c: (int(c[0] + X0), int(Y1 - c[2] - 1), int(c[1] + Z0 - 8))
    andesite, blackstone = pid('minecraft:polished_andesite'), pid('minecraft:polished_blackstone')
    adaptations = []
    def ramp(a, b, width=5, name=''):
        x0, y0, z0 = a; x1, y1, z1 = b; n = int(max(abs(x1 - x0), abs(z1 - z0))) + 1
        dx, dz = x1 - x0, z1 - z0; L = max(1.0, math.hypot(dx, dz)); px, pz = -dz / L, dx / L
        for i in range(n + 1):
            t = i / n; x = round(x0 + dx * t); z = round(z0 + dz * t); y = round(y0 + (y1 - y0) * t)
            for k in range(-(width // 2), width // 2 + 1):
                xx = round(x + px * k); zz = round(z + pz * k)
                world[y:y + 5, zz, xx] = 0; world[y - 1, zz, xx] = andesite
        adaptations.append(dict(kind='authored_ramp', name=name, from_=S(a), to=S(b), width=width))
    def pad(c, r, h, floor, name):
        x, y, z = c
        for dz in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r:
                    world[y:y + h, z + dz, x + dx] = 0; world[y - 1, z + dz, x + dx] = floor
        adaptations.append(dict(kind='authored_pad', name=name, centre=S(c), radius=r, height=h))
    # 1. Trench -> Exodus Black: the two bubbles meet at a 15-block cliff; a service ramp makes the descent walkable.
    ramp(W(1196, -112, -19), W(1192, -129, -34), 5, 'prodromus_to_exodus_black')
    # 2. Arrival pad for three Guardians and the boss pad inside the EX-077 sphere (the bowl floor is too steep to walk).
    start_src = (1474, 491, -55); start = W(*start_src)
    pad(start, 4, 5, andesite, 'arrival')
    boss = W(828, -812, -72); pad(boss, 16, 14, blackstone, 'boss')
    ramp(W(863, -790, -71), (boss[0] + 12, boss[1], boss[2] - 6), 5, 'command_sphere_entry')
    names = np.array([s.split(':')[1].split('[')[0] for s in states]); open_ids = np.nonzero(np.isin(names, ['air', 'light', 'snow']))[0]
    pas = np.zeros(world.shape, bool)
    for z0 in range(0, world.shape[1], 128): pas[:, z0:z0 + 128, :] = np.isin(world[:, z0:z0 + 128, :], open_ids)
    st = np.zeros_like(pas); st[1:-1] = pas[1:-1] & pas[2:] & ~pas[:-2]
    seen = m.reach(st, pas, start, max_down=12)
    if not seen[boss[1], boss[2], boss[0]]: raise SystemExit('boss pad not reachable from arrival')
    path = m.shortest_path(m.route_moves(st, pas, max_down=12), start, {boss})
    print('route cells', len(path))
    # 3. Beats: trigger = route cell; spawn candidates = reachable cells ahead of it; gates = barrier cross-sections.
    barrier = pid('minecraft:red_stained_glass'); air = 0
    markers = []; beats = []
    def mk(i, c, role='ground', **tags): markers.append(dict(id=i, pos=[c[0] + .5, float(c[1]), c[2] + .5], yaw=0.0, tags=dict(role=role, **{k: str(v) for k, v in tags.items()})))
    x, y, z = path[0]
    for i, dx in enumerate((-2, 0, 2)): mk(f'WORLD.IN.{i}', (x + dx, y, z), seat=i)
    mk('WORLD.IN', path[0])
    mk('WORLD.OUT', path[-1]); bx, by, bz = boss; mk('WORLD.CHEST', (bx - 8, by, bz))
    pa = np.array(path)
    ahead_pool = np.argwhere(seen)                      # (y, z, x) of every reachable stand cell
    for beat in BEATS:
        i = beat['at']; tx, ty, tz = path[i]
        mk(f"WORLD.{beat['id']}", path[i], beat=beat['id'])
        info = dict(beat); info['trigger'] = [tx + .5, float(ty), tz + .5]; info['routeIndex'] = i
        if beat['kind'] in ('COMBAT', 'CHARGE', 'DEFEND', 'BOSS'):
            lo, hi = min(i + 14, len(path) - 2), min(i + 80, len(path) - 1)
            seg = pa[lo:hi]
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
    # 4. Persist world (compressed), markers, beats, NBT.
    sx, sy, sz = world.shape[2], world.shape[0], world.shape[1]
    (OUT / 'zones').mkdir(parents=True, exist_ok=True); NBT_OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'zones' / 'markers.json').write_text(json.dumps(dict(schema=1, zones=dict(world=dict(size=[sx, sy, sz], markers=markers))), ensure_ascii=False))
    (OUT / 'beats.json').write_text(json.dumps(dict(schema=1, origin=list(ORIGIN), route=[list(map(int, c)) for c in path[::6]], beats=beats), ensure_ascii=False))
    (OUT / 'manifest.json').write_text(json.dumps(dict(schema=1, activity='exodus_crash', source=str(SRC), size=[sx, sy, sz], origin=list(ORIGIN),
        mapping='wx = floor(src.x) - %d; wy = floor(src.z) - %d; wz = %d - floor(src.y) - 1' % (X0, Z0 - 8, Y1), adaptations=adaptations,
        routeCells=len(path), status='source-derived; native QA required'), ensure_ascii=False, indent=1))
    sys.path.insert(0, str(ROOT / 'scripts/maps'))
    import zone_nbt as Z
    export_nbt(world, states, NBT_OUT / 'world.nbt', Z)

def export_nbt(world, states, target, Z, data_version=5023):
    sy, sz, sx = world.shape; chunks = []; count = 0
    nz = world != 0
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
                       Z.tag(8, 'biome', Z.string('minecraft:the_void')), Z.tag(9, 'block_entities', Z.items(10, [])), Z.tag(9, 'regions', Z.items(10, [])),
                       Z.tag(10, 'data', Z.compound([]))])
    target.write_bytes(gzip.compress(Z.tag(10, '', root), compresslevel=9, mtime=0))
    print('nbt', target.stat().st_size, 'sections', len(chunks), 'blocks', count, 'palette', len(states))



if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('stage', choices=['voxel', 'build']); a.add_argument('--only', type=int, nargs='*')
    r = a.parse_args()
    if r.stage == 'voxel': voxel(r.only)
    elif r.stage == 'build': stage2()


