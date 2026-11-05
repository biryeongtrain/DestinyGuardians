"""W325 Trax Lysis II (rare scout rifle, High-Impact) authored over the frontier_justice layout (bullpup, W151 sight).

Rip -> model: uniform 23.8 px/m (same scale as the other W325 Trax rifles, so the compact gun is ~16.5 px long against the
base 25 px); rip trigger (y -0.055) -> z 6.2 (base trigger z 6.0..6.5), rip z 0.10 -> y 10.93 (gun 0.5 px lower than a
bore match so the raked grip sits on the base grip, z 6.6..9.8 y 7.0..9.8).  Scope moved 0.3 px down (SCOPE_DY) so its
hollow tube centre is y 13.18 on the W151 eye line (aim tip y 13.12..13.28 at z -4.24).  Drum magazine moved to the base
moving magazine (centre z 12.45 y 7.45) and squared to the base axis (rip drum is tilted 12.4 deg).
"""
import math

S = 23.8; ZM, YR = 6.2, -0.055; YM, ZR = 10.93, 0.10
SCOPE_DY = -0.3
T = 18
MAG_C = (12.45, 7.45)          # model centre of the drum
MAG_SRC = (9.7, 7.0)          # rip-placed centre of the drum (uniform map)
MAG_TILT = -12.4               # rip drum tilt about x (deg)
X0, X1 = 7.42, 8.58


def uniform(p):
    x, y, z = p
    return (-(x - 8.0) / S, (z - ZM) / S + YR, (y - YM) / S + ZR)


def model2world(name, p):
    x, y, z = p
    if name.startswith('scope_'):
        y -= SCOPE_DY
    elif name.startswith('mag_'):
        dz, dy = z - MAG_C[0], y - MAG_C[1]; t = math.radians(MAG_TILT)
        z = MAG_SRC[0] + dz * math.cos(t) - dy * math.sin(t); y = MAG_SRC[1] + dz * math.sin(t) + dy * math.cos(t)
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


def _elements():
    E = []
    # ---- front: cap with bore, cream top band (split), ribbed grey handguard with fins, VI nose
    E += cblock('front_cap', 7.4, 8.6, 9.4, 11.42, -2.0, -1.1, c=.12)
    E.append(box('front_cap_lug', (7.7, 9.15, -1.85), (8.3, 9.4, -1.3)))
    E += cblock('top_band', X0, X1, 10.72, 11.43, -1.1, 6.8, c=.12, segs=3, bottom=False)
    E.append(box('top_band_rib', (7.6, 11.43, 1.6), (8.4, 11.52, 3.4)))
    E += cblock('hg_lower', 7.45, 8.55, 9.05, 10.72, -0.95, 4.0, c=.1, top=False)
    for i in range(7):
        z = -0.75 + i * 0.62
        E.append(box(f'hg_fin_{i}', (7.39, 9.35, z), (8.61, 10.25, z + .34)))
    E.append(box('hg_nose', (7.55, 9.25, -1.1), (8.45, 10.72, -0.95)))
    E += cblock('nose_cream', X0, X1, 9.0, 10.72, 4.0, 5.25, c=.12, top=False)
    # ---- trigger guard opening z 5.25..6.75 y 9.15..10.05, lug, trigger
    E.append(box('guard_lug', (7.55, 8.2, 4.7), (8.45, 9.05, 6.3)))
    E.append(box('guard_bar', (7.72, 8.95, 5.2), (8.28, 9.2, 6.3)))
    E.append(box('rec_lower', (X0, 10.05, 5.25), (X1, 10.72, 6.8)))
    E.append(box('trigger', (7.92, 9.62, 6.18), (8.08, 10.05, 6.36)))
    E.append(beam('trigger_hook', (6.25, 9.66), (6.12, 9.38), 0.15, 7.92, 8.08))
    # ---- tapered grip (rip: y 8.0 z 7.3..9.4, y 7.0 z 7.7..8.75)
    E.append(beam('grip', (8.4, 9.0), (8.22, 6.85), 0.95, 7.5, 8.5))
    E.append(beam('grip_front', (7.19, 9.07), (7.89, 7.07), 0.4, 7.52, 8.48))
    E.append(beam('grip_rear', (9.43, 8.55), (8.58, 7.1), 0.4, 7.52, 8.48))
    E.append(box('grip_heel', (7.48, 6.78, 7.72), (8.52, 7.0, 8.78)))
    # ---- dark body around the thumb hole (z 8.05..9.55, y 9.1..10.15), stock frame with window
    E.append(box('body_neck', (7.45, 9.0, 6.6), (8.55, 10.15, 8.05)))
    E += cblock('body_low', 7.45, 8.55, 8.2, 9.12, 7.8, 11.0, c=.1, top=False)
    E.append(box('body_post', (7.45, 8.5, 9.55), (8.55, 10.2, 11.45)))
    E.append(box('hole_fillet_a', (7.465, 9.85, 7.85), (8.535, 10.25, 8.25), rx=45, origin=[8.0, 10.05, 8.05]))
    E.append(box('hole_fillet_b', (7.465, 9.85, 9.35), (8.535, 10.25, 9.75), rx=45, origin=[8.0, 10.05, 9.55]))
    E += cblock('stock_bottom', 7.45, 8.55, 8.5, 9.1, 10.9, 14.2, c=.1, top=False)
    E += cblock('rec_upper', 7.45, 8.55, 10.15, 11.45, 6.8, 11.9, c=.1, segs=2, top=False)
    for i in range(4):
        E.append(box(f'rec_slot_{i}', (7.41, 10.75, 8.4 + i * .65), (8.59, 10.85, 8.8 + i * .65)))
    E.append(box('stock_front', (X0, 8.7, 11.4), (X1, 10.52, 12.2)))
    E.append(box('stock_floor', (X0, 9.1, 12.2), (X1, 9.45, 13.75)))
    E.append(box('stock_back', (X0, 9.2, 13.7), (X1, 10.52, 14.22)))
    E += cblock('stock_top', X0, X1, 10.5, 11.38, 11.4, 14.22, c=.12, bottom=False)
    E.append(box('stock_cheek', (7.5, 11.35, 12.4), (8.5, 11.62, 14.05)))
    E += cblock('butt', 7.45, 8.55, 8.85, 11.62, 14.2, 14.55, c=.1)
    E.append(box('butt_pad', (7.52, 8.95, 14.55), (8.48, 11.5, 14.65)))
    # ---- cream sight base (ends z 8.15, under the base profile behind it) and low dark rear hump
    E += cblock('top_cream', X0, X1, 11.43, 12.38, 4.6, 8.15, c=.14, segs=2, bottom=False)
    E.append(box('top_cream_dot', (7.38, 11.75, 7.2), (7.42, 11.95, 7.4)))
    E.append(box('hump', (7.45, 11.45, 8.15), (8.55, 11.7, 10.72)))
    E.append(box('hump_rear', (7.45, 11.45, 10.72), (8.55, 12.3, 11.2)))
    E.append(beam('hump_slope', (11.2, 12.3), (11.75, 11.62), 0.4, 7.45, 8.55, below=True, ext=(.05, 0)))
    E.append(box('side_tab', (7.05, 10.85, 7.25), (7.45, 11.15, 7.65)))
    # ---- scope mount + hollow box scope = open sight frame around the eye line (window x 7.72..8.28, y 12.92..13.45)
    E.append(box('sight_mount', (7.62, 12.36, 6.35), (8.38, 12.72, 7.65)))
    for tag, za, zb, g in (('', 5.45, 7.95, 0.0), ('front_', 5.4, 5.95, .06), ('rear_', 7.6, 8.05, .06)):
        E.append(box(f'sight_scope_{tag}top', (7.45 - g, 13.45, za), (8.55 + g, 13.65 + g, zb)))
        E.append(box(f'sight_scope_{tag}bottom', (7.45 - g, 12.7 - g, za), (8.55 + g, 12.92, zb)))
        E.append(box(f'sight_scope_{tag}left', (7.45 - g, 12.92, za), (7.72, 13.45, zb)))
        E.append(box(f'sight_scope_{tag}right', (8.28, 12.92, za), (8.55 + g, 13.45, zb)))
    E.append(box('sight_scope_turret', (8.55, 12.95, 6.5), (8.72, 13.4, 7.0)))
    E.append(box('sight_scope_cap_l', (7.38, 13.0, 6.35), (7.45, 13.35, 6.85)))
    # ---- drum magazine (moving leaf) + feed neck into the stock
    cz, cy = MAG_C
    E.append(box('mag_drum', (7.05, cy - 1.0, cz - .95), (8.95, cy + 1.0, cz + .95)))
    E.append(box('mag_drum_r45', (7.2, cy - .83, cz - .9), (8.8, cy + .83, cz + .9), rz=45, origin=[8.0, cy, cz]))
    E.append(box('mag_drum_cap_l', (6.98, cy - .55, cz - .55), (7.05, cy + .55, cz + .55)))
    E.append(box('mag_drum_cap_r', (8.95, cy - .55, cz - .55), (9.02, cy + .55, cz + .55)))
    E.append(box('mag_neck', (7.6, cy + .9, cz - .5), (8.4, 9.3, cz + .5)))
    return E


def elements():
    return declash(_elements())


def is_magazine(n):
    return n.startswith('mag_')


MAT = {
    'cream': (226, 218, 150), 'ivory': (226, 222, 206), 'grey': (78, 76, 82), 'grey_dk': (58, 57, 62),
    'dark': (40, 40, 44), 'green': (66, 76, 73), 'black': (24, 24, 26), 'steel': (150, 150, 146),
}
RULES = [
    ('front_cap_lug', 'grey'), ('front_cap', 'ivory'), ('top_band_rib', 'ivory'), ('top_band', 'cream'),
    ('hg_fin', 'grey_dk'), ('hg_', 'grey'), ('nose_cream', 'cream'),
    ('guard', 'green'), ('rec_lower', 'green'), ('trigger', 'black'), ('grip', 'dark'),
    ('body_', 'dark'), ('hole_fillet', 'dark'), ('rec_slot', 'black'), ('rec_upper', 'green'), ('stock_bottom', 'grey_dk'),
    ('stock_cheek', 'dark'), ('stock_top', 'green'), ('stock_', 'cream'), ('butt_pad', 'black'), ('butt', 'green'),
    ('top_cream_dot', 'black'), ('top_cream', 'cream'), ('hump', 'green'), ('side_tab', 'black'),
    ('sight_mount', 'ivory'), ('sight_scope_turret', 'ivory'), ('sight_scope_cap', 'steel'),
    ('sight_scope_front', 'dark'), ('sight_scope_rear', 'dark'), ('sight_scope', 'cream'),
    ('mag_drum_cap', 'steel'), ('mag_neck', 'dark'), ('mag', 'ivory'),
]
DEFAULT_MAT = 'dark'
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
    if n == 'front_cap' and fn == 'north':
        yy = 11.42 - t * 2.02; xx = 7.4 + s * 1.2
        d = math.hypot(xx - 8.0, yy - 10.82)
        if d < .2: return (12, 12, 14, 255)
        if d < .3: return (40, 40, 42, 255)
    if n.startswith('sight_scope') and ((n.endswith('left') and fn == 'east') or (n.endswith('right') and fn == 'west')
                                        or (n.endswith('top') and fn == 'down') or (n.endswith('bottom') and fn == 'up')):
        return (22, 23, 25, 255)
    if n == 'nose_cream' and fn in ('east', 'west'):
        # "VI" chevron mark as flat dark texels
        u = s if fn == 'west' else 1 - s
        if (abs(u - .25 - (t - .2) * .4) < .07 or abs(u - .55 + (t - .2) * .4) < .07) and .2 < t < .55:
            return MAT['grey'] + (255,)
    if n.startswith('top_cream_s') and fn in ('east', 'west') and line(e, fn, s, t, .5):
        return MAT['grey'] + (255,)
    if n.startswith('mag_drum') and fn in ('east', 'west', 'north', 'south', 'up', 'down') and line(e, fn, s, t, .3):
        return MAT['dark'] + (255,)
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

PANEL_PARTS=('nose_cream','top_cream','top_band','stock_','rec_upper','body_','mag_drum','hg_','sight_scope')
def identity_paint(e,fn,s,t,u,c):
    n=e['name'];side=fn in ('east','west');x,y,w,h=face_grid(e,fn,s,t)
    if side and n.startswith(('nose_cream','top_cream_s','stock_front')):
        if inset(s,t,.08,.12,.92,.87,.022):return (115,116,91,255)
        if n.startswith('nose_cream'):
            if .2<t<.57 and (abs(u-.22-(t-.2)*.4)<.024 or abs(u-.34-(t-.2)*.4)<.024):return (92,95,76,255)
            if .43<u<.86 and .17<t<.6:
                if abs(t-.18)<.035 or abs(u-(.43+(t-.18)*.52))<.027 or abs(u-(.86-(t-.18)*.52))<.027:return (93,95,74,255)
    if side and n.startswith('top_cream_s'):
        for a in (.17,.8):
            q=ring(e,fn,s,t,c,a,.65,.1)
            if q:return q
    if side and n.startswith('sight_scope'):
        if n in ('sight_scope_left','sight_scope_right'):
            for a in (.22,.72):
                q=ring(e,fn,s,t,c,a,.5,.22)
                if q:return q
        if n.startswith(('sight_scope_front','sight_scope_rear')) and x%4==0:return (143,145,136,255)
    if side and n=='mag_drum':
        if .22<t<.7 and .15<s<.85:return (32,38,37,255)
        if y in (2,h-3):return (104,111,104,255)
    if n.startswith('mag_drum_cap') and side:return (35,42,40,255) if .18<s<.82 and .28<t<.72 else panel(e,fn,s,t,(215,214,195,255),False)
    if side and n.startswith('hg_fin') and (y==h//2 or x==w//2):return (22,24,26,255)
    if side and n.startswith('rec_upper_s') and .3<t<.5 and .15<s<.8:return (30,34,34,255)
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

MUZZLE_NAME='front_cap';BORE=(8,10.82,.18)
def identity_geometry(E):return E

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
MATERIALS = {'bore_dark': {'kind': 'dark', 'color': (12, 15, 17), 'detail': 0, 'amp': 0, 'rim': 0}, 'optic_inner': {'kind': 'dark', 'color': (20, 24, 27), 'detail': 0, 'amp': 1, 'rim': 0.05}, 'rubber_pad': {'kind': 'rubber', 'color': (25, 28, 29), 'detail': 0.15, 'amp': 6, 'field': 0.025, 'rim': 0.04}, 'silver_steel': {'kind': 'steel', 'color': (135, 140, 140), 'detail': 0.6, 'amp': 10, 'field': 0.1, 'rim': 0.19}, 'black_recess': {'kind': 'dark', 'color': (23, 26, 29), 'detail': 0.3, 'amp': 2, 'rim': 0.06}, 'yellow_paint': {'kind': 'paint', 'color': (205, 199, 137), 'detail': 0.85, 'amp': 2, 'field': 0.055, 'rim': 0.1}, 'ivory_paint': {'kind': 'paint', 'color': (201, 198, 184), 'detail': 0.8, 'amp': 2, 'rim': 0.1}, 'green_paint': {'kind': 'paint', 'color': (46, 57, 52), 'detail': 0.85, 'amp': 2, 'rim': 0.1}, 'violet_metal': {'kind': 'metal', 'color': (68, 67, 75), 'detail': 0.55, 'amp': 7, 'field': 0.085, 'rim': 0.13}, 'dark_metal': {'kind': 'metal', 'color': (46, 48, 53), 'detail': 0.65, 'amp': 7, 'rim': 0.13}, 'body_polymer': {'kind': 'polymer', 'color': (35, 40, 43), 'detail': 0.7, 'amp': 5, 'rim': 0.07}, 'grip_rubber': {'kind': 'rubber', 'color': (32, 37, 39), 'detail': 0.3, 'amp': 6, 'rim': 0.045}}
MATERIAL_ROLES = {'cream': 'yellow_paint', 'ivory': 'ivory_paint', 'grey': 'violet_metal', 'grey_dk': 'dark_metal', 'dark': 'body_polymer', 'green': 'green_paint', 'black': 'black_recess', 'steel': 'silver_steel'}

def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith('sight') and ((name.endswith('left') and face=='east') or (name.endswith('right') and face=='west') or (name.endswith('top') and face=='down') or (name.endswith('bottom') and face=='up')):return 'optic_inner'
    if name.startswith('grip'):return 'grip_rubber'
    if name.startswith('butt_pad'):return 'rubber_pad'
    if name.startswith(('sight_scope_front','sight_scope_rear')):return 'dark_metal'
    if name.startswith('mag_drum_cap'):return 'silver_steel'
    return MATERIAL_ROLES[mat_of(name)]

def material(name,face):
    key=material_key(name,face)
    if name.startswith(('front_cap','mag_drum','top_band_rib')):
        # The reshaped front plate and relocated drum do not share the rip's
        # surface parameterization. Keep their material, discard stretched relief.
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
    if side and n in ('sight_scope_left','sight_scope_right'):
        for a in (.22,.72):
            radius=.22*min(w,h);dist=math.hypot((s-a)*w,(t-.5)*h)
            if abs(dist-radius)<.65:return (105,110,95,255)
            if abs(dist-radius-1.2)<.6:return (222,221,194,255)

    if side and n.startswith('nose_cream'):
        if .2<t<.57 and (abs(u-.22-(t-.2)*.4)<.024 or abs(u-.34-(t-.2)*.4)<.024):return (92,95,76,255)
        if .43<u<.86 and .17<t<.6 and (abs(t-.18)<.035 or abs(u-(.43+(t-.18)*.52))<.027 or abs(u-(.86-(t-.18)*.52))<.027):return (93,95,74,255)
    if n=='mag_drum' and side and .35<t<.64:return (29,34,35,255)
    if n.startswith('mag_drum_cap') and side and .18<s<.82 and .4<t<.6:return (27,33,34,255)
    return None


# MATERIAL R2: bare metal interfaces, explicit rubber/polymer contrast, sparse motifs.
MATERIALS['body_polymer'].update(color=(53,58,61),plate=False)
MATERIALS['grip_rubber'].update(color=(22,27,29),plate=False,field=.02)
MATERIALS['rubber_pad'].update(color=(22,27,29),plate=False)
MATERIALS['yellow_paint'].update(wear=(153,156,145))
MATERIALS['ivory_paint'].update(wear=(146,152,148))
MATERIALS['green_frame_metal']={'kind':'metal','color':(79,89,84),'detail':.55,'amp':6,'field':.06}
MATERIALS['rail_steel']={'kind':'steel','color':(110,119,116),'detail':.4,'amp':6}

_r1_material_key=material_key
def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith(('rec_upper','rec_lower','hump','stock_top','butt','guard')) and not name.startswith('butt_pad'):return 'green_frame_metal'
    if name.startswith(('trigger','side_tab','sight_mount','top_band_rib','mag_neck')):return 'rail_steel'
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
    if side and n.startswith('hg_fin'):
        # Vent shoe machining: sparse cross slots observed on the rip rail row.
        if (y==h//2 and 2<x<w-3) or (x==w//2 and h//3<y<2*h//3):return (26,31,33,255)
    if side and n.startswith('sight_scope_turret') and y in (2,h-3) and 2<x<w-3:return (182,188,173,255)
    return _r1_special(e,fn,s,t)
