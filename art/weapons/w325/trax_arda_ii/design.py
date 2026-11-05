"""W325 Trax Arda II (uncommon scout rifle, High-Impact) authored over the frontier_justice layout (bullpup, W151 sight).

Rip -> model: uniform 23.8 px/m; rip trigger (y -0.047) -> z 6.2 (base trigger z 6.0..6.5); rip scope axis (z 0.199) ->
y 13.2, the W151 eye line (aim tip y 13.12..13.28 at z -4.24); rip centre line x +0.08 px -> x 8.  At this placement
the raked grip (z 6.9..9.0) lies on the base grip (z 6.6..9.8) and the suppressor bore is y 11.15 (base 11.43).
Magazine moved +1.5 z / +0.55 y toward the base moving magazine (rip tilt kept; a full match would push it under the
short butt).
"""
import math

S = 23.8; ZM, YR = 6.2, -0.047; YM, ZR = 13.2, 0.199
XO = 0.08
MAG = (1.5, 0.55)
X0, X1 = 7.38, 8.62       # receiver / handguard
SX0, SX1 = 7.5, 8.5       # lower body and stock
T = 18


def uniform(p):
    x, y, z = p
    return (-(x + XO - 8.0) / S, (z - ZM) / S + YR, (y - YM) / S + ZR)


def model2world(name, p):
    x, y, z = p
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


def shift(e, dz, dy):
    e = dict(e); e['from'] = [e['from'][0], e['from'][1] + dy, e['from'][2] + dz]; e['to'] = [e['to'][0], e['to'][1] + dy, e['to'][2] + dz]
    if 'rotation' in e:
        r = dict(e['rotation']); o = r['origin']; r['origin'] = [o[0], o[1] + dy, o[2] + dz]; e['rotation'] = r
    return e


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


def read_frame():
    E = []
    # ---- suppressor: teal body, perforated rear band (dark holes painted), end cap with bore, adapter
    E += cblock('sup', 7.4, 8.6, 10.45, 11.85, -8.95, -5.4, c=.15)
    E += cblock('sup_band', 7.42, 8.58, 10.47, 11.83, -5.4, -3.95, c=.15)
    E.append(box('sup_cap', (7.55, 10.6, -9.05), (8.45, 11.7, -8.95)))
    E.append(box('sup_adapter', (7.72, 10.8, -3.95), (8.28, 11.5, -2.8)))
    E.append(box('sup_adapter_ring', (7.66, 10.74, -3.6), (8.34, 11.56, -3.35)))
    # ---- handguard: teal top (split), rail channel with teeth, lower teal with belly, front block, lug
    E += cblock('hg_top', X0, X1, 11.55, 12.3, -3.45, 3.0, c=.14, segs=3, bottom=False)
    E.append(box('front_block', (7.55, 11.9, -2.1), (8.45, 12.65, -1.35)))
    E.append(box('front_block_top', (7.65, 12.65, -2.0), (8.35, 12.75, -1.45)))
    E += cblock('hg_mid', X0, X1, 9.95, 11.55, -2.85, 3.8, c=.1, segs=2, top=False)
    E.append(box('hg_channel', (7.34, 10.75, -1.2), (8.66, 11.2, 2.2)))
    for i in range(8):
        E.append(box(f'hg_tooth_{i}', (7.3, 10.82, -1.0 + i * .4), (8.7, 11.13, -0.8 + i * .4)))
    E += cblock('hg_belly', X0, X1, 9.55, 9.95, -1.9, 3.8, c=.1, segs=2, top=False)
    E.append(box('hg_lug', (7.6, 9.6, -2.75), (8.4, 10.45, -1.95)))
    # ---- upper rise to the mount (kept <= 12.4 behind z 4.4), mount block
    E.append(box('upper_step', (X0 + .12, 12.3, 4.4), (X1 - .12, 12.4, 6.1)))
    E += cblock('upper_front', X0, X1, 11.55, 12.3, 3.0, 6.1, c=.12, bottom=False)
    E += cblock('mount_block', 7.45, 8.55, 11.4, 12.55, 6.1, 7.85, c=.12, bottom=False)
    E += cblock('rec_mid', X0, X1, 10.2, 11.6, 3.8, 10.1, c=.1, segs=2, top=False, bottom=False)
    E.append(box('rec_port', (7.34, 10.75, 4.6), (8.66, 11.15, 6.3)))
    # ---- trigger guard lug, trigger opening, grip
    E.append(box('guard_lug', (7.55, 8.25, 4.3), (8.45, 10.2, 5.1)))
    E.append(box('guard_lug_toe', (7.55, 8.05, 4.3), (8.45, 8.25, 6.2)))
    E.append(box('guard_floor', (7.65, 8.9, 5.1), (8.35, 9.2, 6.4)))
    E.append(box('trigger_block', (7.5, 9.2, 6.45), (8.5, 10.2, 7.7)))
    E.append(box('trigger', (7.92, 9.55, 6.08), (8.08, 10.2, 6.25)))
    E.append(beam('trigger_hook', (6.1, 9.62), (5.95, 9.3), 0.15, 7.92, 8.08))
    E.append(beam('grip', (7.4, 9.2), (8.1, 6.85), 1.3, 7.48, 8.52, ext=(.4, 0)))
    for i in range(3):
        E.append(beam(f'grip_rib_{i}', (6.9 + i * .23, 8.7 - i * .7), (7.05 + i * .23, 8.25 - i * .7), 0.14, 7.44, 8.56))
    E.append(box('grip_heel', (7.48, 6.82, 7.55), (8.52, 7.1, 8.75)))
    # ---- body around the thumb hole (z 7.7..9.5, y 8.95..10.2), stock with slots
    E.append(box('hole_floor', (SX0, 8.05, 7.9), (SX1, 8.95, 11.2)))
    E.append(box('hole_back', (SX0, 8.5, 9.5), (SX1, 10.2, 11.5)))
    E.append(box('hole_fillet_a', (SX0 + .015, 8.75, 7.95), (SX1 - .015, 9.15, 8.35), rx=45, origin=[8.0, 8.95, 8.15]))
    E.append(box('hole_fillet_b', (SX0 + .015, 8.75, 9.3), (SX1 - .015, 9.15, 9.7), rx=45, origin=[8.0, 8.95, 9.5]))
    E += cblock('stock_body', SX0, SX1, 9.2, 11.2, 10.1, 14.25, c=.1, segs=2, top=False)
    E += cblock('stock_belly', SX0, SX1, 8.6, 9.2, 11.2, 13.4, c=.1, top=False)
    E.append(box('stock_rail', (SX0, 11.2, 10.1), (SX1, 11.45, 14.25)))
    # cheek kept under the base top (11.57 at z 8.2..10.4)
    E += cblock('cheek_block', X0, X1, 10.9, 11.55, 8.0, 10.6, c=.1, bottom=False)
    E.append(beam('cheek_tail', (10.6, 11.55), (11.25, 11.3), 0.4, X0, X1, below=True, ext=(0, .05)))
    E += cblock('butt_block', 7.4, 8.6, 9.9, 12.0, 13.3, 14.85, c=.14)
    E.append(box('butt', (SX0, 7.95, 14.25), (SX1, 9.95, 14.75)))
    E.append(box('butt_pad', (7.55, 8.0, 14.75), (8.45, 11.9, 14.92)))
    E.append(box('side_tab', (7.15, 10.7, 7.0), (7.45, 11.1, 7.5)))
    # ---- hollow scope = open sight frame around the eye line (window x 7.72..8.28, y 12.95..13.45)
    E.append(box('sight_mount', (7.65, 12.4, 6.45), (8.35, 12.82, 7.4)))
    E.append(box('sight_turret', (7.75, 13.55, 6.6), (8.25, 13.8, 7.25)))
    E.append(box('sight_turret_knob', (8.52, 13.0, 6.65), (8.72, 13.35, 7.2)))
    for tag, za, zb, g in (('', 6.0, 7.8, 0.0), ('obj_', 4.9, 6.0, .05), ('eye_', 7.8, 8.15, .08)):
        E.append(box(f'sight_{tag}top', (7.48 - g, 13.45, za), (8.52 + g, 13.65 + g, zb)))
        E.append(box(f'sight_{tag}bottom', (7.48 - g, 12.75 - g, za), (8.52 + g, 12.95, zb)))
        E.append(box(f'sight_{tag}left', (7.48 - g, 12.95, za), (7.72, 13.45, zb)))
        E.append(box(f'sight_{tag}right', (8.28, 12.95, za), (8.52 + g, 13.45, zb)))
    # ---- magazine (moved by MAG): tilted body + top block, ribs
    E.append(beam('mag_body', (8.45, 7.55), (12.0, 6.28), 2.35, 7.52, 8.48, ext=(0, 0)))
    E.append(box('mag_top', (7.52, 7.6, 9.75), (8.48, 8.55, 11.55)))
    return E


def _elements():
    return [shift(e, *MAG) if e['name'].startswith('mag_') else e for e in read_frame()]


def elements():
    return declash(_elements())


def is_magazine(n):
    return n.startswith('mag_')


MAT = {
    'teal': (64, 86, 84), 'teal_dk': (48, 66, 64), 'gun': (76, 76, 78), 'gun_dk': (56, 56, 58),
    'black': (28, 28, 30), 'steel': (140, 142, 142), 'grip': (60, 60, 62),
}
RULES = [
    ('sup_band', 'gun'), ('sup_cap', 'black'), ('sup_adapter_ring', 'steel'), ('sup_adapter', 'gun_dk'), ('sup', 'teal'),
    ('hg_tooth', 'gun'), ('hg_channel', 'black'), ('hg_lug', 'gun'), ('hg_top', 'teal'), ('hg_', 'teal_dk'),
    ('front_block', 'gun_dk'), ('upper_', 'teal'), ('mount_block', 'gun'), ('rec_port', 'black'), ('rec_mid', 'gun'),
    ('guard', 'gun'), ('trigger_block', 'gun'), ('trigger', 'black'), ('grip_rib', 'gun_dk'), ('grip', 'grip'),
    ('hole', 'gun'), ('stock_rail', 'gun_dk'), ('stock', 'gun'), ('cheek', 'teal'), ('butt_block', 'teal'),
    ('butt_pad', 'black'), ('butt', 'gun'), ('side_tab', 'black'),
    ('sight_mount', 'gun'), ('sight_turret', 'gun'), ('sight_eye', 'gun_dk'), ('sight_obj', 'teal_dk'), ('sight_', 'teal'),
    ('mag_rib', 'gun'), ('mag', 'gun_dk'),
]
DEFAULT_MAT = 'gun'
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
        return (12, 12, 14, 255) if d < .2 else MAT['gun'] + (255,)
    if n == 'mag_body' and fn in ('east', 'west') and (line(e, fn, s, t, .3, 's') or line(e, fn, s, t, .55, 's') or line(e, fn, s, t, .8, 's')) and .15 < t < .85:
        return MAT['gun'] + (255,)
    if n.startswith('sup_band') and fn in ('east', 'west', 'up', 'down'):
        # perforated band: staggered dark holes
        lu, lv = face_px(e, fn); i, j = int(s * lu * 3), int(t * lv * 3)
        if (i + (j % 2)) % 2 == 0 and j % 2 == 0: return MAT['black'] + (255,)
    if n.startswith('sight_') and ((n.endswith('left') and fn == 'east') or (n.endswith('right') and fn == 'west')
                                   or (n.endswith('top') and fn == 'down') or (n.endswith('bottom') and fn == 'up')):
        return (22, 23, 25, 255)
    if n == 'butt_block' and fn in ('east', 'west') and 0.35 < s < 0.65 and 0.15 < t < 0.4:
        return MAT['black'] + (255,)
    if n.startswith('stock_body_s') and fn in ('east', 'west') and 0.6 < t < 0.75 and 0.15 < s < 0.85:
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

PANEL_PARTS=('hg_','upper_','rec_mid','stock_','cheek_','mount_','mag_','sup','butt_block','hole_')
def identity_paint(e,fn,s,t,u,c):
    n=e['name'];side=fn in ('east','west');x,y,w,h=face_grid(e,fn,s,t)
    if side and n.startswith(('hg_mid_s','hg_top_s','hg_belly_s','upper_front_s')):
        if inset(s,t,.09,.16,.91,.85,.025):return (118,139,134,255)
        if n.startswith('hg_top_s') and .25<t<.65 and .4<s<.75 and abs(t-.45)<.035:return (35,52,50,255)
    if side and n.startswith(('stock_body_s','hole_back','rec_mid_s')):
        if inset(s,t,.12,.16,.88,.85,.025):return (107,110,108,255)
        for a in (.2,.8):
            q=ring(e,fn,s,t,c,a,.5,.11)
            if q:return q
    if side and n=='mag_body':
        for a in (.09,.36,.63):
            if inset(s,t,a,.17,a+.2,.8,.025):return (130,132,128,255)
        if y==h-4:return (124,126,124,255)
    if side and n.startswith('butt_block') and .18<s<.5 and .25<t<.53:return (14,22,23,255)
    if n.startswith('sup_band') and side:return panel(e,fn,s,t,MAT['steel']+(255,),False)
    if side and n.startswith('sight_turret'):
        q=ring(e,fn,s,t,c,r=.3)
        if q:return q
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

MUZZLE_NAME='sup_cap';BORE=(8,11.15,.23)
def identity_geometry(E):
    E=[e for e in E if not e['name'].startswith('sup_band')]
    E.extend([box('sup_band_top',(7.42,11.63,-5.4),(8.58,11.83,-3.95)),
              box('sup_band_bottom',(7.42,10.47,-5.4),(8.58,10.67,-3.95)),
              box('sup_band_mid',(7.42,11.1,-5.4),(8.58,11.2,-3.95)),
              box('sup_band_core',(7.7,10.7,-5.4),(8.3,11.6,-3.95))])
    for i in range(5):
        z=-5.4+i*.33
        E.append(box('sup_band_post_'+str(i),(7.42,10.67,z),(8.58,11.63,min(z+.13,-3.95))))
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
MATERIALS = {'bore_dark': {'kind': 'dark', 'color': (12, 15, 17), 'detail': 0, 'amp': 0, 'rim': 0}, 'optic_inner': {'kind': 'dark', 'color': (20, 24, 27), 'detail': 0, 'amp': 1, 'rim': 0.05}, 'rubber_pad': {'kind': 'rubber', 'color': (25, 28, 29), 'detail': 0.15, 'amp': 6, 'field': 0.025, 'rim': 0.04}, 'silver_steel': {'kind': 'steel', 'color': (135, 140, 140), 'detail': 0.6, 'amp': 10, 'field': 0.1, 'rim': 0.19}, 'black_recess': {'kind': 'dark', 'color': (23, 26, 29), 'detail': 0.3, 'amp': 2, 'rim': 0.06}, 'teal_paint': {'kind': 'paint', 'color': (57, 79, 75), 'detail': 1.05, 'amp': 2, 'field': 0.07, 'rim': 0.11}, 'teal_shadow': {'kind': 'paint', 'color': (44, 64, 60), 'detail': 0.9, 'amp': 2, 'rim': 0.1}, 'receiver_metal': {'kind': 'metal', 'color': (70, 74, 73), 'detail': 0.85, 'amp': 8, 'field': 0.09, 'rim': 0.14}, 'dark_metal': {'kind': 'metal', 'color': (47, 53, 52), 'detail': 0.65, 'amp': 7, 'field': 0.1, 'rim': 0.13}, 'grip_polymer': {'kind': 'polymer', 'color': (48, 52, 51), 'detail': 0.5, 'amp': 5, 'rim': 0.07}, 'vent_steel': {'kind': 'steel', 'color': (127, 134, 132), 'detail': 0, 'amp': 11, 'field': 0.11, 'rim': 0.18}}
MATERIAL_ROLES = {'teal': 'teal_paint', 'teal_dk': 'teal_shadow', 'gun': 'receiver_metal', 'gun_dk': 'dark_metal', 'black': 'black_recess', 'steel': 'silver_steel', 'grip': 'grip_polymer'}

def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith('sight') and ((name.endswith('left') and face=='east') or (name.endswith('right') and face=='west') or (name.endswith('top') and face=='down') or (name.endswith('bottom') and face=='up')):return 'optic_inner'
    if name.startswith('sup_band'):return 'dark_metal' if name.endswith('core') else 'vent_steel'
    if name.startswith('butt_pad'):return 'rubber_pad'
    if name.startswith('sight_turret'):return 'silver_steel'
    if name.startswith('mag_'):return 'dark_metal'
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

    if side and n.startswith('butt_block') and .18<s<.5 and .25<t<.53:
        return (14,22,23,255)  # Original black rectangular stock insert.
    return None


# MATERIAL R2: bare metal interfaces, explicit rubber/polymer contrast, sparse motifs.
MATERIALS['receiver_metal'].update(color=(87,94,94),amp=6)
MATERIALS['grip_polymer'].update(color=(54,59,58),plate=False)
MATERIALS['rubber_pad'].update(color=(23,27,26),plate=False)
MATERIALS['teal_paint'].update(wear=(132,145,139))
MATERIALS['teal_shadow'].update(wear=(112,127,120))
MATERIALS['rail_steel']={'kind':'steel','color':(111,119,118),'detail':.45,'amp':7,'field':.065}
MATERIALS['magazine_metal']={'kind':'metal','color':(80,87,85),'detail':.5,'amp':6}

_r1_material_key=material_key
def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith(('hg_tooth','front_block','mount_block','guard','trigger','side_tab')):return 'rail_steel'
    if name.startswith('mag_'):return 'magazine_metal'
    if name.startswith('hg_mid') and '_sl' not in name and '_sr' not in name:return 'receiver_metal'
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
    if side and n=='mag_body':
        # Original three pressed magazine panels, one-texel inset outlines.
        for a,b in ((.09,.29),(.36,.56),(.63,.83)):
            xa,xb=round(a*(w-1)),round(b*(w-1));ya,yb=round(.17*(h-1)),round(.81*(h-1))
            if (x in (xa,xb) and ya<=y<=yb) or (y in (ya,yb) and xa<=x<=xb):return (29,35,34,255)
    return _r1_special(e,fn,s,t)
