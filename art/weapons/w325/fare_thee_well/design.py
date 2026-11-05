"""W325 Fare-Thee-Well (uncommon scout rifle, Lightweight) authored over the patron_of_lost_causes layout (bullpup).

Rip -> model: uniform 23.8 px/m; rip trigger (y -0.057) -> z 7.3 (DZ 0.5 behind the read frame so the grip lands on the
base pistol grip z 8.3..9.4), rip bore (z 0.115) -> y 10.52.  Magazine moved +0.8 z / +0.3 y toward the base moving
magazine (z 10.6..13.4), rake kept.  Rear sight fin gets two ears so the W153 aim tip (y 12.68, z 6.1) sits in a notch.
"""
import math

S = 23.8; ZM, YR = 6.8, -0.057; YM, ZR = 10.52, 0.115
DZ = 0.5                 # read frame (coordinates below) -> model
MAG = (0.8, 0.3)         # extra magazine move (z, y)
T = 16


def uniform(p):
    x, y, z = p
    return (-(x - 8.0) / S, (z - ZM) / S + YR, (y - YM) / S + ZR)


def model2world(name, p):
    x, y, z = p; z -= DZ
    if name.startswith('mag_'):
        z -= MAG[0]; y -= MAG[1]
    return uniform((x, y, z))


def box(name, lo, hi, rx=0.0, origin=None, rz=0.0):
    e = {'name': name, 'from': list(lo), 'to': list(hi)}
    if rx or rz:
        o = origin or [(lo[i] + hi[i]) / 2 for i in range(3)]
        e['rotation'] = {'origin': list(o), 'x': rx, 'y': 0, 'z': rz}
    return e


def beam(name, p0, p1, thick, x0, x1, ext=(0.0, 0.0), below=False, above=False):
    """Box along the (z, y) segment p0->p1; below=True: segment is the top edge, above=True: the bottom edge."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dz, dy)
    a = math.degrees(math.atan2(-dy, dz))
    cz, cy = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    if below or above:
        nz, ny = -dy / L, dz / L                 # left normal
        if ny < 0: nz, ny = -nz, -ny             # make it point up
        sg = -1 if below else 1
        cz += sg * nz * thick / 2; cy += sg * ny * thick / 2
    sh = (ext[1] - ext[0]) / 2; cz += dz / L * sh; cy += dy / L * sh; h = (L + ext[0] + ext[1]) / 2
    return box(name, (x0, cy - thick / 2, cz - h), (x1, cy + thick / 2, cz + h), rx=round(a, 4), origin=[8.0, cy, cz])


def octo(name, x0, x1, y0, y1, z0, z1):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; r = (x1 - x0) / 2 * 0.83
    return [box(name, (x0, y0, z0), (x1, y1, z1)),
            box(name + '_r45', (cx - r, cy - r, z0 + .01), (cx + r, cy + r, z1 - .01), rz=45, origin=[cx, cy, (z0 + z1) / 2])]


def shift(e, dz, dy=0.0):
    e = dict(e); e['from'] = [e['from'][0], e['from'][1] + dy, e['from'][2] + dz]; e['to'] = [e['to'][0], e['to'][1] + dy, e['to'][2] + dz]
    if 'rotation' in e:
        r = dict(e['rotation']); o = r['origin']; r['origin'] = [o[0], o[1] + dy, o[2] + dz]; e['rotation'] = r
    return e


X0, X1 = 7.53, 8.47      # receiver / stock width (rip top view 7.62..8.56, centred)
MAROON = (86, 65, 67); GREY = (88, 88, 86); DARK = (50, 50, 49); STEEL = (112, 113, 112)


def bev(name, xs, y, z0, z1, r=0.13):
    """45 deg strips along the long edges at height y (chamfer look on a slab top or bottom)."""
    return [box(f'{name}_{t}', (x - r, y - r, z0), (x + r, y + r, z1), rz=45, origin=[x, y, (z0 + z1) / 2])
            for t, x in (('l', xs[0]), ('r', xs[1]))]


def fillet(name, z, y, r=0.32, x0=X0 + .015, x1=X1 - .015):
    """45 deg wedge filling a rectangular hole corner (round-ish holes)."""
    return box(name, (x0, y - r / 2, z - r / 2), (x1, y + r / 2, z + r / 2), rx=45, origin=[8.0, y, z])


def cblock(name, x0, x1, y0, y1, z0, z1, c=0.12, segs=1, top=True, bottom=True, gap=0.06):
    """DMW-style machined block: core plus stepped side strips (unrotated corner chamfers top/bottom); the side
    strips are split into segs pieces with small notches that read as panel seams."""
    out = [box(name, (x0 + c, y0, z0), (x1 - c, y1, z1))]
    ya, yb = y0 + (c if bottom else 0), y1 - (c if top else 0)
    L = (z1 - z0) / segs
    for i in range(segs):
        za = z0 + i * L + (gap / 2 if i else 0); zb = z0 + (i + 1) * L - (gap / 2 if i < segs - 1 else 0)
        sfx = f'_{i}' if segs > 1 else ''
        out.append(box(f'{name}_sl{sfx}', (x0, ya, za), (x0 + c, yb, zb)))
        out.append(box(f'{name}_sr{sfx}', (x1 - c, ya, za), (x1, yb, zb)))
    return out


def cham(name, x0, x1, y0, y1, z0, z1, c=0.12, segs=1, top=True, bottom=False, gap=0.06):
    """cblock whose corner steps are filled flush by 45 deg strips (diamond centred on the inner step corner,
    half-diagonal = c, so the 45 deg face runs exactly from step edge to step edge: no overhang, no gap)."""
    out = cblock(name, x0, x1, y0, y1, z0, z1, c=c, segs=segs, top=top, bottom=bottom, gap=gap)
    r = c / 2 ** .5; L = (z1 - z0) / segs
    for i in range(segs):
        za = z0 + i * L + (gap / 2 if i else 0); zb = z0 + (i + 1) * L - (gap / 2 if i < segs - 1 else 0)
        sfx = f'_{i}' if segs > 1 else ''
        for ty, yc in (('t', y1 - c), ('b', y0 + c)):
            if (ty == 't' and not top) or (ty == 'b' and not bottom): continue
            for tx, xc in (('l', x0 + c), ('r', x1 - c)):
                out.append(box(f'{name}_ch{ty}{tx}{sfx}', (xc - r, yc - r, za), (xc + r, yc + r, zb), rz=45,
                               origin=[xc, yc, (za + zb) / 2]))
    return out


def read_frame():
    E = []
    # ---- suppressor: octagon body, end rings, front cap with bore, knurled rear collar
    E += octo('sup', 7.52, 8.48, 10.13, 10.96, -9.85, -6.65)
    E.append(box('sup_cap', (7.6, 10.2, -9.95), (8.4, 10.89, -9.82)))
    E.append(box('sup_ring_front', (7.49, 10.1, -9.6), (8.51, 10.99, -9.42)))
    E.append(box('sup_ring_mid', (7.49, 10.1, -7.9), (8.51, 10.99, -7.72)))
    E.append(box('sup_collar', (7.5, 10.05, -6.65), (8.5, 11.02, -5.95)))
    E.append(box('sup_collar_rim', (7.56, 10.11, -5.95), (8.44, 10.96, -5.7)))
    # ---- barrel, gas block, angled riser, gas tube with front/rear collars
    E += octo('barrel', 7.83, 8.17, 10.3, 10.64, -5.7, -1.3)
    E.append(box('gas_block', (7.74, 10.2, -5.1), (8.26, 10.78, -4.6)))
    E.append(beam('gas_riser', (-5.0, 10.6), (-4.45, 11.12), 0.34, 7.84, 8.16, ext=(0, .1)))
    E.append(box('gas_tube', (7.86, 10.92, -4.55), (8.14, 11.22, -1.9)))
    E.append(box('gas_slot_band', (7.82, 10.88, -3.9), (8.18, 11.26, -2.6)))
    E.append(box('gas_collar', (7.78, 10.8, -2.0), (8.22, 11.2, -1.4)))
    # ---- handguard: front plate, upper shell with real slots, bevelled lower with belly
    E += cham('front_plate', 7.5, 8.5, 9.75, 11.5, -1.6, -1.3, c=.1)
    E += cham('hg_upper', 7.58, 8.42, 10.95, 11.5, -1.3, 1.45, c=.1)
    for i, (za, zb) in enumerate(((-1.3, -0.95), (-0.35, -0.05), (0.55, 0.85))):
        E.append(box(f'hg_post_{i}', (7.58, 10.72, za), (8.42, 10.95, zb)))
    E += cblock('hg_lower', X0, X1, 9.75, 10.72, -1.3, 1.45, c=.1, segs=2, top=False)
    E += cblock('hg_lower_tail', X0, X1, 9.75, 10.1, 1.45, 5.0, c=.1, segs=2, top=False)
    E += cham('hg_belly', X0, X1, 9.45, 9.75, -1.3, 5.0, c=.1, segs=2, top=False, bottom=True)
    for i in range(4):
        z = -0.6 + i * 0.85
        E.append(box(f'hg_rib_{i}', (7.48, 9.95, z), (8.52, 10.45, z + .32)))
    # ---- maroon receiver: chamfered top, recessed ejection port with bolt, rail with teeth
    E += cham('rec_upper', X0, X1, 11.1, 11.55, 1.45, 8.0, c=.12)
    E += cblock('rec_lower', X0, X1, 10.1, 10.6, 1.45, 8.0, c=.08, segs=2, top=False, bottom=False)
    E.append(box('rec_mid_front', (X0, 10.6, 1.45), (X1, 11.1, 2.4)))
    E.append(box('rec_mid_back', (X0, 10.6, 4.9), (X1, 11.1, 8.0)))
    E.append(box('port_floor', (7.68, 10.6, 2.4), (8.32, 11.1, 4.9)))
    E.append(box('port_bolt', (7.6, 10.7, 2.7), (7.68, 10.98, 4.0)))
    E.append(box('port_bolt_r', (8.32, 10.7, 2.7), (8.4, 10.98, 4.0)))
    E.append(box('rail', (7.7, 11.55, 1.45), (8.3, 11.62, 7.5)))
    for i in range(12):
        z = 1.6 + i * 0.5
        E.append(box(f'rail_tooth_{i}', (7.66, 11.62, z), (8.34, 11.74, z + .26)))
    E.append(beam('rec_tail', (7.9, 11.4), (8.85, 10.75), 0.7, X0, X1, ext=(.1, .1)))
    E.append(box('lower_mid', (X0, 9.4, 5.0), (X1, 10.1, 7.7)))
    E.append(box('rec_pin', (7.46, 10.3, 7.3), (8.54, 10.5, 7.5)))
    # ---- low rear sight fin (top 12.24, under the base profile) with an open centre notch
    E.append(box('rsight_base', (7.7, 11.6, 7.4), (8.3, 11.95, 7.95)))
    E.append(box('rsight_fin_l', (7.7, 11.95, 7.45), (7.9, 12.24, 7.72)))
    E.append(box('rsight_fin_r', (8.1, 11.95, 7.45), (8.3, 12.24, 7.72)))
    E.append(beam('rsight_ramp', (7.72, 12.0), (8.3, 11.6), 0.24, 7.7, 8.3, ext=(.02, 0)))
    # ---- side controls
    E.append(box('side_tab', (7.3, 10.25, 6.95), (7.53, 10.6, 7.6)))
    E.append(box('charging_rod', (7.05, 10.3, 7.88), (7.53, 10.5, 8.08)))
    E.append(box('charging_knob', (7.0, 10.22, 7.84), (7.2, 10.58, 8.4)))
    E.append(box('selector', (8.47, 9.9, 7.75), (8.6, 10.15, 8.25)))
    # ---- trigger guard + trigger
    E.append(box('guard_bottom', (7.88, 8.8, 6.15), (8.12, 8.96, 7.3)))
    E.append(beam('guard_front', (6.0, 9.42), (6.25, 8.85), 0.16, 7.88, 8.12, ext=(0, .05)))
    E.append(box('guard_rear', (7.88, 8.8, 7.25), (8.12, 9.42, 7.42)))
    E.append(beam('trigger', (6.72, 9.4), (6.88, 8.98), 0.15, 7.92, 8.08))
    E.append(beam('trigger_curl', (6.86, 9.04), (6.7, 8.86), 0.12, 7.92, 8.08, ext=(.02, 0)))
    # ---- grip with finger ribs, palm swell, heel
    E.append(beam('grip', (8.1, 9.35), (8.68, 6.9), 1.1, 7.55, 8.45))
    for i in range(4):
        y = 8.85 - i * 0.48
        z = 7.62 + (9.35 - y) * (0.58 / 2.45) - 0.05
        E.append(box(f'grip_rib_{i}', (7.6, y - .1, z - .2), (8.4, y + .1, z + .05), rx=-13, origin=[8.0, y, z]))
    E.append(box('grip_pad', (7.55, 6.9, 8.1), (8.45, 7.25, 9.15)))
    # ---- thumbhole stock (holes z 8.85..10.35 y 9.15..10.15 and z 13.3..14.8 y 8.7..10.2, filleted corners)
    E.append(box('body_neck', (X0, 9.4, 7.6), (X1, 10.85, 8.85)))
    E += cham('stock_top', X0, X1, 10.15, 10.9, 8.85, 15.45, c=.12, segs=3)
    E.append(box('hole1_floor', (X0, 7.85, 8.5), (X1, 9.15, 10.4)))
    E += cblock('well_front', X0, X1, 7.3, 7.95, 8.9, 11.3, c=.1, top=False)
    E += cblock('body_mid', X0, X1, 7.9, 10.15, 10.35, 13.3, c=.12, segs=2, top=False)
    E.append(box('stock_plate', (7.47, 8.6, 10.75), (8.53, 9.75, 12.6)))
    E += cblock('stock_lower', X0, X1, 7.6, 8.75, 13.3, 14.65, c=.12, top=False)
    E += cblock('stock_post', X0, X1, 7.4, 10.2, 14.6, 15.45, c=.12, top=False)
    for i, (z, y) in enumerate(((8.85, 9.15), (10.35, 9.15), (8.85, 10.15), (10.35, 10.15))):
        E.append(fillet(f'hole1_fillet_{i}', z, y))
    for i, (z, y) in enumerate(((13.3, 8.75), (14.6, 8.75), (13.3, 10.15), (14.6, 10.15))):
        E.append(fillet(f'hole2_fillet_{i}', z, y, r=.4))
    # ---- cheek riser with chamfered ends and bevelled top
    E += cham('cheek_riser', 7.6, 8.4, 10.85, 11.32, 11.55, 14.05, c=.1)
    E.append(box('cheek_step_f', (7.68, 10.85, 11.25), (8.32, 11.08, 11.55)))
    E.append(box('cheek_step_b', (7.68, 10.85, 14.05), (8.32, 11.08, 14.35)))
    # ---- butt: plate, toe, rubber pad
    E += cblock('butt', X0, X1, 7.0, 10.88, 15.45, 15.82, c=.1)
    E.append(box('butt_pad', (7.5, 7.05, 15.82), (8.5, 10.8, 15.94)))
    E.append(box('butt_heel', (X0, 10.6, 15.3), (X1, 10.95, 15.85)))
    # ---- magazine (raked; moved to the base well by MAG): body, ribs, floor plate, feed lip
    E.append(beam('mag_body', (10.05, 4.95), (11.1, 7.6), 2.25, 7.6, 8.4, ext=(-.15, .6)))
    E.append(beam('mag_rib_front', (9.0, 5.28), (10.0, 7.85), 0.18, 7.56, 8.44, ext=(-.25, 0)))
    E.append(beam('mag_rib_back', (11.05, 4.85), (12.0, 7.3), 0.18, 7.56, 8.44, ext=(-.35, 0)))
    E.append(beam('mag_floor', (9.12, 5.45), (11.0, 4.66), 0.3, 7.55, 8.45))
    E.append(beam('mag_floor_tab', (10.95, 4.72), (11.35, 4.56), 0.22, 7.65, 8.35, ext=(0, .05)))
    return E


def _elements():
    out = []
    for e in read_frame():
        out.append(shift(e, DZ + MAG[0], MAG[1]) if e['name'].startswith('mag_') else shift(e, DZ))
    return out


def elements():
    return declash(_elements())


def is_magazine(n):
    return n.startswith('mag_')


MAT = {
    'maroon': (122, 46, 52), 'maroon_dk': (88, 34, 40), 'grey': (92, 93, 92), 'grey_dk': (70, 71, 71),
    'stock': (50, 51, 54), 'stock_lt': (66, 67, 70), 'grip': (60, 61, 63), 'rubber': (34, 34, 36),
    'steel': (128, 130, 132), 'steel_dk': (68, 70, 73), 'black': (36, 36, 38), 'sup': (44, 45, 48),
}
RULES = [
    ('sup_ring', 'steel'), ('sup_collar_rim', 'steel'), ('sup_cap', 'black'), ('sup', 'sup'),
    ('gas_slot', 'black'), ('gas_', 'steel_dk'), ('barrel', 'steel_dk'),
    ('hg_rib', 'grey_dk'), ('front_plate', 'grey_dk'), ('hg_', 'grey'),
    ('rail_tooth', 'black'), ('rail', 'black'), ('port_floor', 'black'), ('port_bolt', 'steel'),
    ('rec_pin', 'steel'), ('rec_tail', 'maroon_dk'), ('rec_', 'maroon'), ('lower_mid', 'grey'),
    ('rsight', 'black'), ('charging_knob', 'steel'), ('side_tab', 'black'), ('charging', 'black'), ('selector', 'black'),
    ('guard', 'black'), ('trigger', 'black'), ('grip_rib', 'stock'), ('grip_pad', 'stock'), ('grip', 'grip'),
    ('stock_plate', 'stock_lt'), ('butt_pad', 'rubber'), ('mag_rib', 'steel'), ('mag_floor', 'black'), ('mag', 'stock'),
]
DEFAULT_MAT = 'stock'
DECAL = set()
PALETTE_KEEP = list(MAT.values())


# ------------------------------------------------------------------ W30-style flat paint (pixel kit, master style brief)
FACE_UV = {'north': (0, 1), 'south': (0, 1), 'east': (2, 1), 'west': (2, 1), 'up': (0, 2), 'down': (0, 2)}


def face_px(e, fn):
    """Face size in model px (u, v) — for 1-texel lines and panel insets."""
    a, b = FACE_UV[fn]
    return abs(e['to'][a] - e['from'][a]), abs(e['to'][b] - e['from'][b])


def mat_of(n):
    for p, m in RULES:
        if n.startswith(p): return m
    return DEFAULT_MAT


def flat(e, fn, s, t):
    """Flat material colour; DECAL (name, face|'*') keeps the projected rip texture (logos, panel art)."""
    n = e['name']
    if (n, fn) in DECAL or (n, '*') in DECAL: return None
    c = MAT[mat_of(n)]
    if '_sl' in n or '_sr' in n:   # cblock chamfer strips: one step lighter, reads as a machined edge
        c = tuple(min(255, int(v * 1.18 + 6)) for v in c)
    return c + (255,)


def line(e, fn, s, t, frac, axis='t', width=1):
    """True on a 1-texel line at fraction frac of the face along axis 't' (rows) or 's' (columns)."""
    lu, lv = face_px(e, fn); L = (lv if axis == 't' else lu) * T; v = (t if axis == 't' else s) * L
    return abs(v - frac * L) < width * .5 + 1e-6 if L >= 2 else False


def special(e, fn, s, t):
    n = e['name']
    if n == 'sup_cap' and fn == 'north':
        d = math.hypot(s - .5, t - .5)
        return (14, 14, 16, 255) if d < .2 else ((40, 40, 40, 255) if d < .27 else None) or flat(e, fn, s, t)
    if n == 'stock_plate' and fn in ('east', 'west'):
        # Fare-Thee-Well stock badge: steel triangle outline inside the plate
        u = s if fn == 'west' else 1 - s
        edge = (abs(t - .12) < .09 and .1 < u < .9) or (abs(u - .1) < .06 and .1 < t < .9) or abs((1 - t) - (u - .1) * 1.0) < .09 and u > .1
        if edge: return MAT['steel'] + (255,)
    if n.startswith('rec_upper') and fn in ('east', 'west') and line(e, fn, s, t, .85):
        return MAT['maroon_dk'] + (255,)
    if n == 'hg_lower' and fn in ('east', 'west') and line(e, fn, s, t, .3):
        return MAT['grey_dk'] + (255,)
    if n == 'mag_body' and fn in ('east', 'west') and (line(e, fn, s, t, .18, 's') or line(e, fn, s, t, .82, 's')):
        return MAT['steel_dk'] + (255,)
    if n.startswith(('hole1_fillet', 'hole2_fillet')):
        return MAT['stock'] + (255,)
    return flat(e, fn, s, t)


def declash(E, eps=0.012):
    """Negative-reference rule: no coplanar overlapping faces (z-fight slivers). For every pair of unrotated elements
    whose same-facing faces lie in one plane and overlap, the smaller element is pulled back by eps on that side."""
    def rotated(e):
        r = e.get('rotation'); return bool(r) and any(r.get(k, 0) for k in 'xyz')
    def vol(e): return abs((e['to'][0] - e['from'][0]) * (e['to'][1] - e['from'][1]) * (e['to'][2] - e['from'][2]))
    ax = [e for e in E if not rotated(e)]
    for _ in range(3):
        moved = False
        for i, a in enumerate(ax):
            for b in ax[i + 1:]:
                for k in range(3):
                    for side in (0, 1):
                        ka = 'to' if side else 'from'
                        if abs(a[ka][k] - b[ka][k]) > 1e-4: continue
                        ov = 1.0
                        for j in range(3):
                            if j == k: continue
                            ov *= max(0.0, min(a['to'][j], b['to'][j]) - max(a['from'][j], b['from'][j]))
                        if ov <= 1e-4: continue
                        s = a if vol(a) < vol(b) else b
                        s[ka] = list(s[ka]); s[ka][k] += -eps if side else eps; moved = True
        if not moved: break
    return E


# W325 identity pass: authored face paint; no projected texels are needed.
DECAL = set()
T = 20

def ink(c, amount):
    return tuple(max(0, min(255, v + amount)) for v in c[:3]) + (255,)

def face_grid(e, fn, s, t):
    a,b=face_px(e,fn)
    w,h=max(1,round(a*T)),max(1,round(b*T))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

def edge_paint(e,fn,s,t,c):
    x,y,w,h=face_grid(e,fn,s,t)
    if w>=4 and h>=4:
        if y==0 or x==0:return ink(c,28)
        if y==h-1 or x==w-1:return ink(c,-24)
    return tuple(c[:3])+(255,)

def panel(e,fn,s,t,c,bolts=True):
    x,y,w,h=face_grid(e,fn,s,t)
    if w>=14 and h>=9:
        if (y==h-3 and 3<=x<w-3) or (x in (2,w-3) and 3<=y<h-3):return ink(c,-30)
        if y==2 and 3<=x<w-3:return ink(c,18)
        if bolts and w>=18 and h>=12:
            for bx in (5,w-6):
                dx,dy=abs(x-bx),abs(y-5)
                if dx<=1 and dy<=1:return ink(c,44 if dx+dy else -40)
    return edge_paint(e,fn,s,t,c)

def ring(e,fn,s,t,c,cx=.5,cy=.5,r=.27):
    x,y,w,h=face_grid(e,fn,s,t)
    d=math.hypot((s-cx)*w,(t-cy)*h);rr=r*min(w,h)
    if abs(d-rr)<.85:return ink(c,65)
    if d<rr-1:return ink(c,-35)
    return None

def inset(s,t,a,b,c,d,width=.025):
    return a<=s<=c and b<=t<=d and (s<a+width or s>c-width or t<b+width or t>d-width)

GLYPHS={
 'V':['10001','10001','10001','01010','00100'],
 'E':['11111','10000','11110','10000','11111'],
 'I':['111','010','010','010','111'],
 'S':['11111','10000','11111','00001','11111'],
 'T':['11111','00100','00100','00100','00100'],
}
def lettering(text,u,v):
    glyphs=[GLYPHS[k] for k in text];total=sum(len(g[0])+1 for g in glyphs)-1
    x,y=int(u*total),int(v*5)
    if not 0<=y<5 or not 0<=x<total:return False
    for g in glyphs:
        n=len(g[0])
        if x<n:return g[y][x]=='1'
        x-=n+1
    return False

_previous_special = special

def special(e,fn,s,t):
    n=e['name'];side=fn in ('east','west');u=s if fn=='west' else 1-s
    c=flat(e,fn,s,t) or MAT[mat_of(n)]+(255,)
    painted=_previous_special(e,fn,s,t)
    if painted is not None:c=painted
    c=panel(e,fn,s,t,c,bolts=side) if n.startswith(PANEL_PARTS) else edge_paint(e,fn,s,t,c)
    x,y,w,h=face_grid(e,fn,s,t)
    if n.startswith(('grip','butt_pad')) and w>8 and h>8 and 2<x<w-3 and 2<y<h-3:
        if (x+2*(y//3))%5==0 and y%3==0:c=ink(c,-24)
    if n.endswith('_bore_back'):return (12,13,15,255)
    if n.startswith('sight') and fn in ('north','south'):
        if x in (1,w-2) or y in (1,h-2):c=(72,106,116,255)
    return identity_paint(e,fn,s,t,u,c)

PANEL_PARTS=('rec_','stock_','body_','hg_','mag_body','sup','port_bolt','well_','hole1_floor')
def identity_paint(e,fn,s,t,u,c):
    n=e['name'];side=fn in ('east','west');x,y,w,h=face_grid(e,fn,s,t)
    if side and n=='stock_plate':
        c=panel(e,fn,s,t,MAT['stock_lt']+(255,),False)
        a,b=(u-.10)/.8,(t-.12)/.76
        if 0<a<1 and 0<b<1:
            d=min(a,b,abs(b-(1-a)))
            if d<.055 or (.15<a<.78 and .15<b<.78 and abs(b-(.85-a))<.04):return (166,169,168,255)
        if (abs(u-.15)<.04 and abs(t-.18)<.05) or (abs(u-.15)<.04 and abs(t-.8)<.05):return (38,39,42,255)
    if side and n.startswith('rec_'):
        if y==h-4 and w>12:return (54,24,30,255)
        if n=='rec_mid_back' and .18<u<.26 and .25<t<.7:return (49,32,36,255)
    if side and n=='mag_body':
        if inset(s,t,.08,.09,.92,.91,.025):return (133,137,136,255)
        if .18<t<.82 and (abs(s-.2)<.018 or abs(s-.8)<.018):return (24,26,28,255)
    if n=='sup_collar' and fn in ('east','west','up','down') and x%5==0:return (119,122,124,255)
    if side and n.startswith('port_bolt') and y in (h//3,2*h//3):return (40,42,43,255)
    return c


_identity_source_elements = elements

def hollow_muzzle(e,cx,cy,r):
    x0,y0,z0=e['from'];x1,y1,z1=e['to'];n=e['name']
    return [box(n+'_rim_top',(x0,cy+r,z0),(x1,y1,z1)),
            box(n+'_rim_bottom',(x0,y0,z0),(x1,cy-r,z1)),
            box(n+'_rim_left',(x0,cy-r,z0),(cx-r,cy+r,z1)),
            box(n+'_rim_right',(cx+r,cy-r,z0),(x1,cy+r,z1)),
            box(n+'_bore_back',(cx-r,cy-r,z1-.025),(cx+r,cy+r,z1))]

def elements():
    E=_identity_source_elements();out=[]
    for e in E:
        if e['name']==MUZZLE_NAME:
            out.extend(hollow_muzzle(e,*BORE));continue
        out.append(e)
    return declash(identity_geometry(out))

MUZZLE_NAME='sup_cap';BORE=(8,10.545,.19)
def identity_geometry(E):return E


# Rotated frame members also need distinct end planes. The old axis-only
# declash missed their coplanar side faces; these sub-texel recesses are <0.03 px.
_identity_before_plane_cleanup = elements
def elements():
    E=_identity_before_plane_cleanup()
    for i,e in enumerate(E):
        r=e.get('rotation',{})
        axis=0 if r.get('x',0) else 2 if r.get('z',0) else None
        if axis is None:continue
        eps=min(.006+(i+1)*.0001,(e['to'][axis]-e['from'][axis])/10)
        e['from'][axis]+=eps;e['to'][axis]-=eps
    return declash(E)

# MATERIAL PASS: W123/Gnawing Hunger/Beloved surface language.
# Whole-face flat paint is intentionally bypassed. Geometry above is unchanged.
STYLE = 'material'
MATERIALS = {'bore_dark': {'kind': 'dark', 'color': (12, 15, 17), 'detail': 0, 'amp': 0, 'rim': 0}, 'optic_inner': {'kind': 'dark', 'color': (20, 24, 27), 'detail': 0, 'amp': 1, 'rim': 0.05}, 'rubber_pad': {'kind': 'rubber', 'color': (25, 28, 29), 'detail': 0.15, 'amp': 6, 'field': 0.025, 'rim': 0.04}, 'silver_steel': {'kind': 'steel', 'color': (135, 140, 140), 'detail': 0.6, 'amp': 10, 'field': 0.1, 'rim': 0.19}, 'black_recess': {'kind': 'dark', 'color': (23, 26, 29), 'detail': 0.3, 'amp': 2, 'rim': 0.06}, 'maroon_paint': {'kind': 'paint', 'color': (83, 57, 59), 'detail': 1.1, 'amp': 2, 'field': 0.08, 'rim': 0.12}, 'maroon_shadow': {'kind': 'paint', 'color': (65, 44, 47), 'detail': 0.7, 'amp': 2}, 'grey_polymer': {'kind': 'polymer', 'color': (73, 74, 73), 'detail': 0.75, 'amp': 5, 'rim': 0.08}, 'stock_polymer': {'kind': 'polymer', 'color': (43, 46, 48), 'detail': 0.8, 'amp': 5, 'rim': 0.08}, 'grip_rubber': {'kind': 'rubber', 'color': (66, 67, 66), 'detail': 0.35, 'amp': 6}, 'black_anodized': {'kind': 'metal', 'color': (41, 44, 47), 'detail': 0.55, 'amp': 8, 'field': 0.1, 'rim': 0.15}, 'dark_steel': {'kind': 'metal', 'color': (65, 69, 71), 'detail': 0.65, 'amp': 9, 'field': 0.1, 'rim': 0.16}}
MATERIAL_ROLES = {'maroon': 'maroon_paint', 'maroon_dk': 'maroon_shadow', 'grey': 'grey_polymer', 'grey_dk': 'grey_polymer', 'stock': 'stock_polymer', 'stock_lt': 'stock_polymer', 'grip': 'grip_rubber', 'rubber': 'rubber_pad', 'steel': 'silver_steel', 'steel_dk': 'dark_steel', 'black': 'black_anodized', 'sup': 'black_anodized'}

def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith('sight') and ((name.endswith('left') and face=='east') or (name.endswith('right') and face=='west') or (name.endswith('top') and face=='down') or (name.endswith('bottom') and face=='up')):return 'optic_inner'
    if name.startswith(('port_floor','hole1_fillet','hole2_fillet')):return 'black_recess'
    if name.startswith(('mag_body','mag_rib','mag_floor')):return 'black_anodized'
    return MATERIAL_ROLES[mat_of(name)]

def material(name,face):
    key=material_key(name,face)
    # End faces are frequently occluded or differently shaped in the rip. A
    # clean material grain is safer there than stretched side-photo relief.
    if face in ('north','south') or name.startswith(('cover_step','sup_band','sight_')):
        m=dict(MATERIALS[key]);m['detail']=0
        if name.startswith('cover_step'):m['field']=0
        return m
    return key

def special(e,fn,s,t):
    n=e['name'];side=fn in ('east','west');u=s if fn=='west' else 1-s
    x,y,w,h=face_grid(e,fn,s,t)

    if side and n=='stock_plate':
        # Original nested triangular metal badge; the backing remains polymer.
        a,b=(u-.10)/.8,(t-.12)/.76
        if 0<a<1 and 0<b<1 and (min(a,b,abs(b-(1-a)))<.045 or (.15<a<.78 and .15<b<.78 and abs(b-(.85-a))<.035)):
            return (149,155,154,255)
    return None


# MATERIAL R2: bare metal interfaces, explicit rubber/polymer contrast, sparse motifs.
MATERIALS['stock_polymer'].update(color=(57,61,63),plate=False)
MATERIALS['grip_rubber'].update(color=(24,27,29),plate=False,field=.02)
MATERIALS['rubber_pad'].update(color=(23,26,28),plate=False)
MATERIALS['maroon_paint'].update(wear=(124,120,114))
MATERIALS['maroon_shadow'].update(wear=(105,101,97))
MATERIALS['machined_frame']={'kind':'metal','color':(91,97,99),'detail':.6,'amp':6,'field':.065}

_r1_material_key=material_key
def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith(('rail','guard','trigger','hg_rib','front_plate','rec_lower','lower_mid')):return 'machined_frame'
    if name.startswith(('port_bolt','rec_pin','charging_knob','selector')):return 'silver_steel'
    return _r1_material_key(name,face)

_r1_material=material
def material(name,face):
    m=_r1_material(name,face)
    if isinstance(m,dict) and m.get('detail')==0:
        m=dict(m);m['wear']=False
    return m

_r1_special=special
def special(e,fn,s,t):
    n=e['name'];side=fn in ('east','west');x,y,w,h=face_grid(e,fn,s,t)
    if side and n=='mag_body' and .12<t<.88:
        for a in (.18,.50,.82):
            if x==round(a*(w-1)):return (24,29,31,255)
            if x==round(a*(w-1))+1:return (87,94,96,255)
    if n=='sup_collar' and fn in ('east','west','up','down') and 1<y<h-2 and x%5==0:return (108,115,117,255)
    return _r1_special(e,fn,s,t)
