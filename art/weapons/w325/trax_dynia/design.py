"""W325 Trax Dynia (rare scout rifle, Lightweight) authored over the patron_of_lost_causes layout (bullpup scout).

Rip -> model: uniform 23.8 px/m, rip muzzle (y -0.71) -> z -8.93, rip bore height (z 0.119) -> y 10.52.
At this placement the rip grip, trigger, magazine and holo window already sit on the base contract
(base grip z 8.3..9.4, trigger z 6.6, magazine z 10.6..13.4, W153 aim tip y 12.68 z 6.1; holo window centre y 12.7).
"""
import math

S = 23.8; ZM, YR = -8.93, -0.71; YM, ZR = 10.52, 0.119
WIN = (7.63, 8.37, 12.3, 13.1)      # holo window (x0, x1, y0, y1), open front and back for the W153 aim tip


def uniform(p):
    x, y, z = p
    return (-(x - 8.0) / S, (z - ZM) / S + YR, (y - YM) / S + ZR)


def model2world(name, p):
    return uniform(p)


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
    """Square + 45 deg twin: a cheap round section along z."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; r = (x1 - x0) / 2 * 0.83
    return [box(name, (x0, y0, z0), (x1, y1, z1)),
            box(name + '_r45', (cx - r, cy - r, z0 + .01), (cx + r, cy + r, z1 - .01), rz=45, origin=[cx, cy, (z0 + z1) / 2])]


X0, X1 = 7.42, 8.65          # upper receiver width (top view)
T = 15


def _elements():
    E = []
    # ---- barrel, ported brake (separate cap / port blocks / collar), gas ring
    E += octo('barrel', 7.76, 8.24, 10.11, 10.59, -6.85, -4.7)
    E += octo('barrel_rear', 7.76, 8.24, 10.11, 10.59, -4.6, -2.45)
    E.append(box('barrel_joint', (7.72, 10.07, -4.7), (8.28, 10.63, -4.6)))
    E.append(box('brake_cap', (7.62, 10.0, -8.9), (8.38, 10.72, -8.6)))
    for i, (za, zb) in enumerate(((-8.6, -8.15), (-8.05, -7.6))):
        E += cblock(f'brake_seg{i}', 7.58, 8.42, 9.95, 10.77, za, zb, c=.1)
    E.append(box('brake_core', (7.7, 10.1, -8.15), (8.3, 10.62, -8.05)))
    E.append(box('brake_collar', (7.64, 10.0, -7.6), (8.36, 10.72, -6.85)))
    E.append(box('brake_ring', (7.6, 9.97, -7.2), (8.4, 10.75, -7.05)))
    E.append(box('barrel_ring', (7.7, 10.05, -3.2), (8.3, 10.65, -2.95)))
    # ---- receiver front plate, sling loop, lug
    E += cblock('front_plate', 7.48, 8.58, 9.25, 11.78, -2.45, -2.1, c=.1)
    E.append(box('sling_loop', (7.9, 11.0, -2.78), (8.1, 11.36, -2.45)))
    E.append(box('front_lug', (7.85, 9.25, -2.68), (8.15, 9.55, -2.45)))
    # ---- tan upper: two machined blocks (front with through window z -1.9..-1.0), chamfered top
    E += cblock('upper_main', X0, X1, 11.15, 11.9, -1.0, 8.0, c=.13, segs=3, bottom=False)
    E += cblock('upper_nose', X0, X1, 11.15, 11.9, -2.1, -1.9, c=.13, bottom=False)
    E.append(box('upper_crown', (7.68, 11.9, -2.0), (8.39, 12.0, 7.9)))
    E.append(box('upper_low_front', (X0, 10.6, -2.1), (X1, 11.15, -1.9)))
    E += cblock('upper_low', X0, X1, 10.6, 11.15, -1.0, 8.0, c=.08, top=False, bottom=False, segs=2)
    E.append(box('upper_win_top', (X0, 11.1, -1.9), (X1, 11.15, -1.0)))
    E.append(box('upper_window_bar', (7.85, 10.6, -1.9), (8.22, 11.1, -1.0)))
    E.append(box('upper_panel', (7.36, 11.2, 2.4), (7.42, 11.55, 6.2)))
    E.append(box('upper_panel_r', (8.65, 11.2, 2.4), (8.71, 11.55, 6.2)))
    # ---- dark rear upper (kept under the base profile: <= 12.0 to z 12, <= 11.85 behind) with a through slot
    E += cblock('rear_strip', 7.45, 8.62, 10.6, 11.1, 8.0, 14.9, c=.1, segs=2)
    E.append(box('rear_mid', (7.45, 11.1, 8.0), (8.62, 11.3, 14.6)))
    E.append(box('rear_rail', (7.5, 11.8, 8.0), (8.57, 11.98, 11.9)))
    E.append(box('rear_post_front', (7.45, 11.3, 8.0), (8.62, 11.8, 8.6)))
    E.append(box('rear_post_back', (7.45, 11.3, 11.4), (8.62, 11.82, 12.9)))
    E.append(beam('rear_tail', (12.9, 11.82), (14.9, 11.0), 0.5, 7.45, 8.62, below=True))
    E.append(box('rear_slot_floor', (7.6, 11.3, 8.6), (8.47, 11.36, 11.4)))
    # ---- lower chassis (olive grey), segmented with chamfered belly
    E += cblock('lower_front', 7.46, 8.61, 9.12, 10.6, -2.1, 4.9, c=.12, segs=3, top=False)
    E.append(beam('lower_nose_chamfer', (-2.3, 9.55), (-1.4, 9.05), 0.3, 7.46, 8.61))
    E += cblock('lower_mid', 7.46, 8.61, 9.42, 10.6, 4.9, 8.45, c=.1, top=False)
    E.append(box('lower_hole_bar', (7.46, 9.92, 8.45), (8.61, 10.6, 9.75)))
    E += cblock('lower_rear', 7.46, 8.61, 9.22, 10.6, 9.75, 14.9, c=.12, segs=2, top=False)
    E.append(box('insert_ejector', (7.4, 10.28, -0.55), (8.67, 10.86, 1.2)))
    E.append(box('bolt_slide', (7.4, 10.08, 9.6), (8.67, 10.5, 13.0)))
    for i in range(4):
        E.append(box(f'bolt_rib_{i}', (7.36, 10.15, 11.4 + i * .4), (8.71, 10.43, 11.55 + i * .4)))
    E.append(box('charging_bar', (6.86, 10.3, 7.6), (9.14, 10.62, 7.95)))
    for i, z in enumerate((-1.5, 0.8, 3.1, 10.3, 13.6)):
        E.append(box(f'screw_{i}', (7.4, 9.7, z), (8.67, 9.86, z + .16)))
    # ---- trigger guard loop, trigger
    E.append(beam('guard_front', (5.0, 9.45), (6.1, 6.25), 0.26, 7.78, 8.22))
    E.append(beam('guard_toe', (5.85, 6.55), (6.6, 6.02), 0.28, 7.78, 8.22, below=True, ext=(0, .05)))
    E.append(box('guard_bottom', (7.78, 6.02, 6.6), (8.22, 6.3, 9.9)))
    E.append(box('trigger_blade', (7.9, 9.0, 6.68), (8.1, 9.45, 6.9)))
    E.append(beam('trigger_hook', (6.9, 9.05), (6.72, 8.68), 0.17, 7.9, 8.1))
    # ---- grip (raked), finger grooves, web, thumb hole above web (z 8.45..9.75, y 9.0..9.92)
    E.append(beam('grip', (7.95, 9.45), (8.95, 6.55), 1.15, 7.5, 8.5, ext=(0, .12)))
    for i in range(3):
        y = 8.7 - i * .65; z = 7.95 + (9.45 - y) * (1.0 / 2.9) - .62
        E.append(box(f'grip_groove_{i}', (7.56, y - .14, z - .12), (8.44, y + .14, z + .12)))
    E.append(box('grip_web', (7.5, 6.5, 8.6), (8.5, 9.0, 10.4)))
    E.append(box('grip_hole_post', (7.5, 8.95, 9.75), (8.5, 9.95, 10.35)))
    E.append(box('grip_floor', (7.5, 6.32, 8.45), (8.5, 6.6, 10.0)))
    E.append(box('hole_fillet_a', (7.53, 9.72, 8.42), (8.47, 10.12, 8.82), rx=45, origin=[8.0, 9.92, 8.62]))
    E.append(box('hole_fillet_b', (7.53, 9.72, 9.42), (8.47, 10.12, 9.82), rx=45, origin=[8.0, 9.92, 9.62]))
    # ---- tan triangular mag-well cover
    # tan triangular cover (A 10.0/6.45, B 11.0/8.45, C 13.65/8.45): two edge slabs + fills kept inside the triangle
    E.append(beam('cover_hyp', (10.0, 6.45), (13.65, 8.45), 0.7, 7.42, 8.65, above=True))
    E.append(beam('cover_left', (10.0, 6.45), (11.0, 8.45), 0.55, 7.42, 8.65, below=True))
    E.append(box('cover_top', (7.42, 7.95, 11.0), (8.65, 8.45, 12.8)))
    E.append(box('cover_fill', (7.43, 7.3, 10.75), (8.64, 7.95, 11.6)))
    E.append(box('well_block', (7.46, 8.45, 10.3), (8.61, 9.3, 13.85)))
    # ---- stock rod, screw, slab butt with chamfered pad
    E.append(box('stock_link', (7.7, 10.55, 14.85), (8.3, 11.2, 15.1)))
    E.append(box('stock_rod', (7.85, 8.45, 13.55), (8.15, 8.8, 15.1)))
    E.append(box('stock_screw', (7.7, 8.38, 14.05), (8.3, 8.86, 14.38)))
    E += cblock('butt_pad', 7.42, 8.58, 7.42, 11.7, 15.05, 15.72, c=.12, segs=1)
    E.append(box('butt_toe', (7.42, 7.3, 15.3), (8.58, 7.42, 15.72)))
    E.append(box('butt_back', (7.5, 7.7, 15.7), (8.5, 11.4, 15.86)))
    for i in range(4):
        E.append(box(f'butt_rib_{i}', (7.55, 8.1 + i * .8, 15.84), (8.45, 8.35 + i * .8, 15.92)))
    # ---- holo sight (hooded window, open both ends; ends by z 8.0, roof <= 13.42)
    E.append(box('sight_base', (7.45, 12.0, 4.78), (8.55, 12.3, 8.0)))
    E.append(box('sight_nose', (7.45, 12.3, 4.8), (8.55, 12.5, 5.5)))
    for t, xa, xb in (('l', 7.4, WIN[0]), ('r', WIN[1], 8.6)):
        E.append(box(f'sight_wall_{t}', (xa, 12.3, 5.4), (xb, 13.25, 7.6)))
        E.append(beam(f'sight_wall_front_{t}', (4.95, 12.42), (5.55, 13.25), 0.3, xa, xb))
        E.append(beam(f'sight_wall_back_{t}', (7.55, 13.25), (7.98, 12.4), 0.28, xa, xb))
        E.append(box(f'sight_rib_{t}', (xa - .06, 12.55, 5.9), (xa + .02 if t == 'l' else xb + .06, 12.9, 6.9)))
    E.append(box('sight_roof', (7.5, WIN[3], 5.45), (8.5, 13.25, 7.6)))
    E.append(box('sight_roof_cap', (7.62, 13.25, 5.6), (8.38, 13.38, 7.45)))
    E.append(box('sight_tan_band', (7.38, 13.12, 6.95), (8.62, 13.36, 7.55)))
    E.append(box('sight_knob', (8.6, 12.45, 6.3), (8.82, 12.75, 6.9)))
    E.append(box('sight_lens', (WIN[0], 12.3, 5.5), (WIN[1], 12.38, 5.6)))
    # ---- magazine (moving leaf)
    E += cblock('mag_body', 7.5, 8.5, 5.32, 9.0, 10.45, 13.05, c=.1, top=False)
    E.append(box('mag_floor', (7.45, 5.15, 10.4), (8.55, 5.35, 13.1)))
    E.append(box('mag_rib_front', (7.46, 5.4, 11.25), (8.54, 8.4, 11.45)))
    E.append(box('mag_rib_back', (7.46, 5.4, 12.15), (8.54, 8.4, 12.35)))
    E.append(box('mag_window', (7.46, 5.6, 12.6), (8.54, 6.2, 12.85)))
    return E


def elements():
    return declash(_elements())


def is_magazine(n):
    return n.startswith('mag_')


MAT = {
    'tan': (158, 116, 78), 'tan_dk': (120, 86, 58), 'olive': (74, 80, 72), 'olive_dk': (58, 63, 57),
    'dark': (44, 45, 47), 'black': (30, 30, 32), 'steel': (132, 134, 134), 'grip': (52, 54, 52), 'silver': (176, 178, 176),
}
RULES = [
    ('brake_core', 'black'), ('brake', 'dark'), ('barrel_ring', 'steel'), ('barrel_joint', 'steel'), ('barrel', 'dark'),
    ('front_plate', 'olive_dk'), ('sling', 'dark'), ('front_lug', 'dark'),
    ('upper_window_bar', 'dark'), ('upper_panel', 'tan_dk'), ('upper_crown', 'tan_dk'), ('upper_', 'tan'),
    ('rear_slot', 'black'), ('rear_', 'olive_dk'),
    ('insert_ejector', 'dark'), ('bolt_rib', 'steel'), ('bolt_slide', 'silver'), ('charging', 'dark'), ('screw', 'steel'),
    ('lower_', 'olive'), ('guard', 'olive'), ('trigger', 'black'),
    ('grip_groove', 'black'), ('grip_web', 'olive'), ('grip_hole', 'olive'), ('grip_floor', 'olive'), ('hole_fillet', 'olive'),
    ('grip', 'grip'), ('cover_', 'tan'), ('well', 'olive_dk'),
    ('stock_', 'dark'), ('butt_rib', 'black'), ('butt', 'dark'),
    ('sight_tan', 'tan'), ('sight_lens', 'black'), ('sight_rib', 'olive_dk'), ('sight_', 'dark'),
    ('mag_window', 'black'), ('mag_rib', 'olive_dk'), ('mag', 'dark'),
]
DEFAULT_MAT = 'olive'
DECAL = {('upper_main', 'east'), ('upper_main', 'west')}
PALETTE_KEEP = list(MAT.values()) + [(60, 150, 170), (190, 60, 60), (70, 80, 180)]


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


def special(e, fn, s, t):
    n = e['name']
    if n == 'brake_cap' and fn == 'north':
        d = math.hypot(s - .5, t - .5)
        return (12, 12, 14, 255) if d < .22 else MAT['steel'] + (255,)
    if n.startswith('brake_seg') and fn in ('east', 'west', 'up') and n.count('_') == 1:
        return MAT['black'] + (255,) if 0.3 < s < 0.7 and 0.3 < t < 0.7 else None or flat(e, fn, s, t)
    if n.startswith('upper_main_s') and n.endswith('_1') and fn in ('east', 'west') and 0.35 < t < 0.65:
        u = s if fn == 'west' else 1 - s
        if 0.05 < u < 0.95:
            if line(e, fn, s, t, .35) or line(e, fn, s, t, .65): return MAT['silver'] + (255,)
            k = int(u * 12)
            return ((60, 150, 170, 255) if k == 2 else (190, 60, 60, 255) if k == 9 else (70, 80, 180, 255) if k == 8
                    else MAT['black'] + (255,))
    if n == 'upper_main' and fn in ('east', 'west'):
        # projected rip art kept only for the readout strip (blue/red dots); rest is flat tan with a groove line
        if line(e, fn, s, t, .78): return MAT['tan_dk'] + (255,)
        return None if 0.25 < t < 0.7 and 0.28 < s < 0.62 else MAT['tan'] + (255,)
    if n.startswith('lower_front') and fn in ('east', 'west') and line(e, fn, s, t, .35):
        return MAT['olive_dk'] + (255,)
    if n.startswith(('sight_wall', 'sight_roof')) and fn in ('north', 'south') or n == 'sight_roof' and fn == 'down':
        return MAT['black'] + (255,)
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

PANEL_PARTS=('upper_','lower_','rear_','cover_','grip_web','mag_','sight_wall','sight_roof','bolt_')
def identity_paint(e,fn,s,t,u,c):
    n=e['name'];side=fn in ('east','west');x,y,w,h=face_grid(e,fn,s,t)
    if n.startswith('cover_step'):
        c=MAT['tan']+(255,)
        if side:
            za=e['from'][2]+(e['to'][2]-e['from'][2])*(1-s if fn=='west' else s)
            ya=e['to'][1]-(e['to'][1]-e['from'][1])*t
            left=10+(ya-6.45)*.5;right=10+(ya-6.45)*1.825
            if abs(za-left)<.065 or abs(za-right)<.065:return (211,190,157,255)
            return c
        return edge_paint(e,fn,s,t,c)
    if n.startswith('upper_panel') and side:
        if y in (0,h-1) or x in (0,w-1):return (198,192,174,255)
        c=(76,77,69,255)
        if .15<t<.85:
            if .1<u<.17:return (170,51,43,255)
            if .2<u<.27:return (54,82,165,255)
            if .33<u<.44:return (32,34,35,255) if abs(t-.5)<.18 else (166,168,155,255)
            if .5<u<.66 and int(u*60)%5<2 and int(t*10)%4<2:return (187,187,167,255)
            if .73<u<.9:return (53,126,134,255) if .3<t<.7 else (148,163,153,255)
        return c
    if side and n.startswith(('upper_main_s','upper_low_s','cover_')):
        if inset(s,t,.07,.12,.93,.88,.023):return (211,190,157,255)
    if side and n.startswith('lower_front_s') and y==h//3:return (40,47,42,255)
    if n=='sight_lens' and fn in ('north','south','up'):return (216,112,48,255) if s>.2 else (250,210,138,255)
    if side and n.startswith('sight_wall'):
        q=ring(e,fn,s,t,c,.75,.75,.12)
        if q:return q
    if side and n=='bolt_slide' and 3<y<h-3 and x%6 in (0,1):return (73,80,75,255)
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

MUZZLE_NAME='brake_cap';BORE=(8,10.36,.18)
def identity_geometry(E):
    # One connected stepped triangular well cover. The old intersecting rotated
    # edge slabs produced a hooked corner in quarter view.
    E=[e for e in E if not e['name'].startswith('cover_')]
    for i in range(12):
        ya=6.45+i/6;yb=ya+1/6
        left=10+(ya-6.45)*.5
        right=10+(yb-6.45)*1.825
        E.append(box('cover_step_'+str(i),(7.42,ya,left),(8.65,yb,right)))
    for e in E:
        if e['name'] in ('upper_panel','upper_panel_r'):
            e['from'][1]=11.16;e['to'][1]=11.65
    return E

# T20 close-view pixel detail exceeds the shared shelf packer 512 atlas.
ATLAS = 1024


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
MATERIALS = {'bore_dark': {'kind': 'dark', 'color': (12, 15, 17), 'detail': 0, 'amp': 0, 'rim': 0}, 'optic_inner': {'kind': 'dark', 'color': (20, 24, 27), 'detail': 0, 'amp': 1, 'rim': 0.05}, 'rubber_pad': {'kind': 'rubber', 'color': (25, 28, 29), 'detail': 0.15, 'amp': 6, 'field': 0.025, 'rim': 0.04}, 'silver_steel': {'kind': 'steel', 'color': (135, 140, 140), 'detail': 0.6, 'amp': 10, 'field': 0.1, 'rim': 0.19}, 'black_recess': {'kind': 'dark', 'color': (23, 26, 29), 'detail': 0.3, 'amp': 2, 'rim': 0.06}, 'tan_paint': {'kind': 'paint', 'color': (129, 103, 79), 'detail': 1.0, 'amp': 2, 'field': 0.075, 'rim': 0.12}, 'tan_shadow': {'kind': 'paint', 'color': (102, 80, 60), 'detail': 0.7, 'amp': 2, 'rim': 0.1}, 'olive_paint': {'kind': 'paint', 'color': (59, 68, 60), 'detail': 0.85, 'amp': 2, 'rim': 0.11}, 'olive_shadow': {'kind': 'paint', 'color': (44, 52, 45), 'detail': 0.7, 'amp': 2}, 'dark_metal': {'kind': 'metal', 'color': (42, 47, 48), 'detail': 0.65, 'amp': 8, 'field': 0.1, 'rim': 0.16}, 'grip_rubber': {'kind': 'rubber', 'color': (37, 41, 39), 'detail': 0.4, 'amp': 6, 'rim': 0.05}, 'readout_steel': {'kind': 'steel', 'color': (74, 81, 77), 'detail': 0, 'amp': 6, 'field': 0.07, 'rim': 0.14}, 'amber_emitter': {'kind': 'glow', 'color': (216, 116, 46), 'detail': 0}}
MATERIAL_ROLES = {'tan': 'tan_paint', 'tan_dk': 'tan_shadow', 'olive': 'olive_paint', 'olive_dk': 'olive_shadow', 'dark': 'dark_metal', 'black': 'black_recess', 'steel': 'silver_steel', 'grip': 'grip_rubber', 'silver': 'silver_steel'}

def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith('sight') and ((name.endswith('left') and face=='east') or (name.endswith('right') and face=='west') or (name.endswith('top') and face=='down') or (name.endswith('bottom') and face=='up')):return 'optic_inner'
    if name.startswith('upper_panel'):return 'readout_steel'
    if name=='sight_lens':return 'amber_emitter'
    if name.startswith('butt'):return 'rubber_pad'
    if name.startswith('mag_'):return 'dark_metal'
    return MATERIAL_ROLES[mat_of(name)]

def material(name,face):
    key=material_key(name,face)
    if name.startswith('upper_main'):
        # The new diagnostic bezel covers a different-sized source region;
        # do not repeat its projected lights under the independently painted one.
        m=dict(MATERIALS[key]);m['detail']=0
        return m
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

    if side and n.startswith('upper_panel'):
        # Diagnostic lights and bezel only; substrate is brushed steel.
        if y in (0,h-1) or x in (0,w-1):return (168,171,158,255)
        if .18<t<.82:
            if .10<u<.17:return (156,42,35,255)
            if .20<u<.27:return (45,67,147,255)
            if .33<u<.44 and abs(t-.5)<.18:return (25,28,29,255)
            if .5<u<.66 and int(u*60)%5<2 and int(t*10)%4<2:return (171,179,160,255)
            if .73<u<.9 and .3<t<.7:return (49,112,119,255)
    if n=='sight_lens' and fn in ('north','south') and s<.18:return (249,208,130,255)
    return None


# MATERIAL R2: bare metal interfaces, explicit rubber/polymer contrast, sparse motifs.
MATERIALS['tan_paint'].update(color=(139,111,82),wear=(181,172,152))
MATERIALS['tan_shadow'].update(wear=(148,140,123))
MATERIALS['grip_rubber'].update(color=(23,27,26),plate=False,field=.02)
MATERIALS['rubber_pad'].update(color=(23,27,26),plate=False)
MATERIALS['dark_metal'].update(color=(49,54,53))
MATERIALS['olive_frame_metal']={'kind':'metal','color':(78,87,80),'detail':.6,'amp':6,'field':.06}
MATERIALS['guard_steel']={'kind':'steel','color':(100,109,104),'detail':.4,'amp':6,'field':.06}

_r1_material_key=material_key
def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith(('lower_','rear_','well_','grip_web','grip_hole','grip_floor','hole_fillet','upper_window')):return 'olive_frame_metal'
    if name.startswith(('guard','trigger','charging','front_plate')):return 'guard_steel'
    if name.startswith(('screw','bolt','stock_screw')):return 'silver_steel'
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
    if side and n=='bolt_slide' and 2<y<h-3 and 3<x<w-4:
        if x%6==0:return (55,64,60,255)
        if x%6==1:return (166,175,170,255)
    if side and n.startswith('mag_rib') and y==2:return (114,124,120,255)
    return _r1_special(e,fn,s,t)
