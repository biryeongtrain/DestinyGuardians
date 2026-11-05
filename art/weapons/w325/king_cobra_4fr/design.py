"""W325 King Cobra-4fr (rare linear fusion rifle, Precision) authored over the line_in_the_sand layout.

Rip -> model: uniform 23.8 px/m; rip trigger (y -0.029) -> z 5.73 (base trigger 5.5..5.9), rip z 0.071 -> y 8.95.
At this placement the raked grip (z 5.5..8.1) sits on the base pistol grip (z 6.7..9.25, ~0.6 px further forward/lower),
the bottom plate (rip battery) lands on the base moving battery (z 3.7..9.9, y 4.9..6.2) and is the magazine leaf, the
barrel shroud runs to z -10.05 (base -9.9) and the butt ends at 12.6 (base 15.15; the rip stock is short).
ADS: everything stays under the base top profile (front upper flat top 10.9, bevels 11.1, ahead of z -0.65; base 10.96+0.15).
Detail pass: bevelled receiver (diamond section), shroud top rail with real vent gaps, open coil window, white bracket,
hook rear sight, leg + brace with a real gap to the plate, chamfered plate belly; smeared caps painted flat.
"""
import math

S = 23.8; ZM, YR = 5.73, -0.029; YM, ZR = 8.95, 0.071
T = 15

GREY = (76, 73, 66)          # lower frame / leg / grip polymer
DARK = (54, 54, 51)          # receiver camo base, stock
WHITE = (205, 203, 205)


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


def octo(name, x0, x1, y0, y1, z0, z1, k=0.83):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; r = (x1 - x0) / 2 * k
    return [box(name, (x0, y0, z0), (x1, y1, z1)),
            box(name + '_r45', (cx - r, cy - r, z0 + .01), (cx + r, cy + r, z1 - .01), rz=45, origin=[cx, cy, (z0 + z1) / 2])]


def bevels(name, x0, x1, y, z0, z1, r=0.17, top=True):
    """Two 45 deg corner strips on the top (or bottom) long edges of a slab."""
    out = []
    for tag, xc in (('l', x0), ('r', x1)):
        out.append(box(f'{name}_bev_{tag}', (xc - r, y - r, z0), (xc + r, y + r, z1), rz=45, origin=[xc, y, (z0 + z1) / 2]))
    return out


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


def _elements():
    E = []
    # ---- shroud: white octagon tube, muzzle cap, top rail with two real vent gaps, rear collar, neck
    for i, (za, zb) in enumerate(((-9.75, -6.75), (-6.65, -3.65), (-3.55, -0.55))):
        E += octo(f'tube_{i}', 7.58, 8.42, 9.62, 10.46, za, zb)
    for i, z in enumerate((-6.75, -3.65)):
        E.append(box(f'tube_band_{i}', (7.62, 9.66, z), (8.38, 10.42, z + .1)))
    E.append(box('muzzle_cap', (7.7, 9.74, -10.05), (8.3, 10.34, -9.75)))
    E.append(box('muzzle_ring', (7.55, 9.58, -9.85), (8.45, 10.5, -9.62)))
    for i, (za, zb) in enumerate(((-9.7, -8.4), (-7.7, -5.1), (-4.4, -2.45))):
        E.append(box(f'tube_rail_{i}', (7.72, 10.5, za), (8.28, 10.86, zb)))
    E.append(box('tube_collar', (7.62, 9.66, -0.6), (8.38, 10.42, -0.18)))
    E.append(box('tube_neck', (7.84, 9.88, -0.2), (8.16, 10.2, 0.45)))
    # ---- coil (open window z 0.45..2.6 between frame and upper), rear collar
    E += octo('coil', 7.6, 8.4, 9.62, 10.42, 0.45, 2.6)
    E.append(box('coil_collar', (7.55, 9.58, 2.55), (8.45, 10.46, 2.95)))
    # ---- grey lower frame (tube cradle), front fin, side rails
    E += cblock('frame', 7.52, 8.48, 8.72, 9.62, -9.45, 5.6, c=.13, segs=4, top=False)
    E.append(box('frame_lip_l', (7.44, 9.5, -9.4), (7.6, 9.75, -0.6)))
    E.append(box('frame_lip_r', (8.4, 9.5, -9.4), (8.56, 9.75, -0.6)))
    E.append(beam('fin_front', (-9.45, 9.0), (-9.3, 7.72), 0.24, 7.58, 8.42, ext=(0, .05)))
    E.append(beam('fin_back', (-9.22, 7.85), (-8.4, 8.75), 0.24, 7.58, 8.42, ext=(.05, .05)))
    E.append(box('frame_tab', (7.4, 8.85, 2.6), (8.6, 9.35, 3.6)))
    # ---- receiver front housing (around the shroud end), upper line, bevelled diamond rear receiver
    E += cblock('rec_front', 7.42, 8.58, 9.6, 10.62, -2.45, 0.45, c=.12, top=False)
    E += cham('upper_flat', 7.48, 8.52, 10.6, 10.9, -2.45, -0.6, c=.12)
    E.append(beam('upper_rise', (-0.65, 10.9), (2.6, 11.85), 0.62, 7.48, 8.52, below=True, ext=(0, .05)))
    E.append(box('rec_mid', (7.4, 9.62, 2.6), (8.6, 11.4, 4.55)))
    E += octo('rec_body', 7.25, 8.75, 9.45, 10.95, 3.6, 7.25, k=0.78)
    E += cham('rec_top', 7.45, 8.55, 10.9, 11.85, 4.5, 6.0, c=.14)
    E.append(box('logo_plate', (7.18, 10.15, 3.75), (8.82, 10.7, 5.4)))
    # ---- white bracket (slanted striped plate), white cap, hook rear sight
    E.append(beam('white_fin', (0.35, 10.95), (2.65, 11.95), 0.3, 7.6, 8.4))
    E.append(box('white_cap', (7.62, 11.75, 2.45), (8.38, 12.22, 3.4)))
    E.append(box('white_cap_lip', (7.55, 11.9, 2.35), (8.45, 12.05, 2.6)))
    E.append(box('hook_post', (7.82, 11.75, 4.55), (8.18, 12.42, 5.02)))
    E.append(beam('hook_tip', (4.62, 12.32), (4.8, 12.68), 0.26, 7.82, 8.18, ext=(.04, 0)))
    E.append(box('side_lever', (7.08, 9.95, 6.0), (7.3, 10.3, 6.9)))
    E.append(box('side_lever_tip', (7.02, 9.88, 6.6), (7.25, 10.15, 7.05)))
    # ---- leg (support hand), spike, brace with a real gap to the plate, trigger
    # support leg as a frame (front + rear struts, panel) with a recessed centre plate
    E.append(beam('leg_front', (0.55, 8.6), (1.62, 5.95), 0.6, 7.55, 8.45, ext=(.1, 0)))
    E.append(beam('leg_rear', (2.85, 8.6), (3.85, 6.2), 0.6, 7.55, 8.45, ext=(.05, 0)))
    E.append(beam('leg_panel', (1.7, 8.5), (2.75, 6.05), 1.7, 7.65, 8.35))
    E.append(box('leg_top', (7.55, 8.3, 0.6), (8.45, 8.75, 3.7)))
    E.append(beam('leg_spike', (1.35, 6.1), (1.12, 4.45), 0.42, 7.6, 8.4))
    E.append(box('leg_bolt_l', (7.44, 7.25, 2.45), (7.56, 7.47, 2.67)))
    E.append(box('leg_bolt_r', (8.44, 7.25, 2.45), (8.56, 7.47, 2.67)))
    E.append(beam('trigger', (5.55, 8.72), (5.9, 7.75), 0.22, 7.92, 8.08))
    E.append(beam('trigger_curl', (5.85, 7.85), (5.6, 7.55), 0.16, 7.92, 8.08, ext=(.03, 0)))
    # ---- raked grip with front finger bump, grip back strap into the stock
    E.append(beam('grip', (6.28, 8.65), (7.12, 5.95), 1.45, 7.48, 8.52, ext=(.25, .25)))
    E.append(beam('grip_strap', (7.05, 8.7), (7.95, 6.0), 0.3, 7.52, 8.48))
    # ---- stock: body, sloped top with bevels, cheek slot, short butt with curved back
    E.append(beam('stock_top', (6.0, 11.65), (12.55, 10.45), 0.55, 7.52, 8.48, below=True, ext=(0, 0)))
    E.append(beam('stock_top_cap', (6.0, 11.85), (12.55, 10.65), 0.2, 7.38, 8.62, below=True, ext=(-.1, -.15)))
    E += cblock('stock_body', 7.58, 8.42, 8.75, 10.6, 7.2, 11.4, c=.1, segs=2, top=False)
    E.append(box('stock_belly', (7.6, 8.45, 7.3), (8.4, 8.85, 11.4)))
    E.append(box('stock_rib', (7.5, 9.9, 9.2), (8.5, 10.15, 11.1)))
    E.append(box('butt', (7.48, 7.25, 11.4), (8.52, 10.62, 12.3)))
    E.append(box('butt_back', (7.48, 7.2, 12.3), (8.52, 10.62, 12.42)))
    E.append(box('butt_toe', (7.48, 6.88, 11.4), (8.52, 7.25, 12.2)))
    E.append(box('butt_pad', (7.55, 7.1, 12.42), (8.45, 10.4, 12.62)))
    # ---- bottom plate (rip battery) = moving magazine: plate, chamfered belly, dark window, rear lip
    E += cblock('mag_plate', 7.4, 8.6, 5.25, 6.18, 3.78, 8.2, c=.12, segs=2)
    E += cblock('mag_belly', 7.5, 8.5, 4.95, 5.25, 4.4, 7.7, c=.1, top=False)
    E.append(beam('mag_nose', (3.72, 5.85), (4.6, 4.98), 0.3, 7.45, 8.55, ext=(0, .05)))
    E.append(box('mag_lip', (7.36, 5.95, 3.7), (8.64, 6.2, 4.4)))
    E.append(box('mag_window', (7.36, 5.62, 6.85), (8.64, 5.92, 8.05)))
    E.append(box('mag_stud', (7.34, 5.38, 5.25), (8.66, 5.62, 5.55)))
    return E


def elements():
    return declash(_elements())


def is_magazine(n):
    return n.startswith('mag_')


MAT = {
    'grey': (78, 76, 68), 'grey_dk': (60, 59, 53), 'camo': (66, 62, 70), 'camo_lt': (112, 104, 116), 'camo_dk': (44, 42, 48),
    'white': (214, 212, 214), 'white_dk': (168, 166, 170), 'black': (26, 26, 28), 'coil': (40, 44, 40),
    'green': (150, 200, 60), 'steel': (150, 150, 146),
}
RULES = [
    ('tube_rail', 'white_dk'), ('tube_collar', 'white_dk'), ('tube_band', 'black'), ('tube_neck', 'steel'), ('tube', 'white'),
    ('muzzle', 'white_dk'), ('coil_collar', 'white_dk'), ('coil', 'coil'),
    ('frame_lip', 'grey_dk'), ('frame_tab', 'grey_dk'), ('frame', 'grey'), ('fin_', 'grey'),
    ('rec_front', 'camo'), ('upper_', 'camo'), ('rec_mid', 'camo'), ('rec_body', 'camo'), ('rec_top', 'camo'),
    ('logo_plate', 'camo_dk'), ('white_', 'white'), ('hook', 'black'), ('side_lever', 'white_dk'),
    ('leg_bolt', 'steel'), ('leg_panel', 'grey_dk'), ('leg', 'grey'), ('brace', 'grey'), ('trigger', 'white_dk'), ('grip', 'grey'),
    ('stock_rib', 'camo_dk'), ('stock', 'camo'), ('butt_pad', 'black'), ('butt', 'grey_dk'),
    ('mag_window', 'black'), ('mag_stud', 'steel'), ('mag', 'grey'),
]
DEFAULT_MAT = 'grey'
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




def camo(e, fn, s, t):
    """Large purple camo blobs, fixed in model space so they run across neighbouring parts."""
    p = __import__('sys').modules['__main__'].face_point(e, fn, s, t)
    v = math.sin(p[2] * 1.3 + p[1] * 0.7) + math.sin(p[2] * 0.55 - p[1] * 1.7 + 1.3) + 0.6 * math.sin(p[0] * 3 + p[2])
    return 'camo_lt' if v > 1.0 else ('camo_dk' if v < -1.1 else 'camo')


def special(e, fn, s, t):
    n = e['name']
    if n == 'muzzle_cap' and fn == 'north':
        d = math.hypot(s - .5, t - .5)
        return (14, 14, 16, 255) if d < .22 else MAT['white_dk'] + (255,)
    if n == 'logo_plate' and fn in ('east', 'west'):
        # "VEIST" flash: green chevron + bar as flat texels
        u = s if fn == 'west' else 1 - s
        if .3 < t < .7 and (.1 < u < .2 or (.25 < u < .8 and abs(t - .5) < .12)):
            return MAT['green'] + (255,)
    if n.startswith('tube') and not n.startswith('tube_rail') and fn in ('east', 'west', 'up') and line(e, fn, s, t, .35):
        return MAT['white_dk'] + (255,)
    if n == 'white_fin' and fn in ('east', 'west', 'up') and (line(e, fn, s, t, .3, 's') or line(e, fn, s, t, .55, 's') or line(e, fn, s, t, .8, 's')):
        return MAT['black'] + (255,)
    if mat_of(n) == 'camo' and '_sl' not in n and '_sr' not in n:
        return MAT[camo(e, fn, s, t)] + (255,)
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
    painted=None if mat_of(n)=='camo' else _previous_special(e,fn,s,t)
    if painted is not None:c=painted
    c=panel(e,fn,s,t,c,bolts=side) if n.startswith(PANEL_PARTS) else edge_paint(e,fn,s,t,c)
    x,y,w,h=face_grid(e,fn,s,t)
    if n.startswith(('grip','butt_pad')) and w>8 and h>8 and 2<x<w-3 and 2<y<h-3:
        if (x+2*(y//3))%5==0 and y%3==0:c=ink(c,-24)
    if n.endswith('_bore_back'):return (12,13,15,255)
    if n.startswith('sight') and fn in ('north','south'):
        if x in (1,w-2) or y in (1,h-2):c=(72,106,116,255)
    return identity_paint(e,fn,s,t,u,c)

PANEL_PARTS=('rec_','stock_','frame','leg_panel','mag_plate','white_','tube')
def identity_paint(e,fn,s,t,u,c):
    n=e['name'];side=fn in ('east','west');x,y,w,h=face_grid(e,fn,s,t)
    if side and n=='logo_plate':
        u=s  # Both independently painted side UVs must read VEIST, never mirrored.
        if .05<u<.95 and .2<t<.8 and lettering('VEIST',(u-.05)/.9,(t-.2)/.6):return (172,211,72,255)
        return (39,40,43,255)
    if mat_of(n)=='camo' and material_key(n,fn)=='camo_paint':
        za=e['from'][2]+(e['to'][2]-e['from'][2])*(1-s if fn=='west' else s)
        ya=e['to'][1]-(e['to'][1]-e['from'][1])*t
        a,b=int(za*3),int(ya*4);v=(a//3+2*(b//2)+(a//7))%7
        base=MAT['camo_lt'] if v in (0,1) else MAT['camo_dk'] if v in (4,5) else MAT['camo']
        c=panel(e,fn,s,t,base+(255,),side)
    if n=='white_fin' and side:
        c=(220,220,213,255)
        if .15<t<.93 and any(abs(u-(a+t*.18))<.055 for a in (.15,.4,.65)):return (48,52,49,255)
        return edge_paint(e,fn,s,t,c)
    if n.startswith('white_cap') and side:
        q=ring(e,fn,s,t,c,.3,.6,.16)
        if q:return q
    if n.startswith('tube_') and not n.startswith(('tube_rail','tube_band','tube_collar','tube_neck')) and side:
        if .25<t<.36 and x%12 in (3,4,5):return (112,116,113,255)
        if y==h-4:return (143,145,141,255)
    if n.startswith('coil') and not n.startswith('coil_collar') and x%4==0:return (78,89,77,255)
    if side and n=='leg_panel' and inset(s,t,.12,.1,.88,.9,.025):return (36,40,34,255)
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

MUZZLE_NAME='muzzle_cap';BORE=(8,10.04,.17)
def identity_geometry(E):
    for e in E:
        if e['name']=='white_fin':
            e.update(beam('white_fin',(.35,11.1923),(2.6,11.85),.5,7.32,8.68,below=True))
        if e['name'].startswith('white_cap'):e['from'][0]-=.21;e['to'][0]+=.21
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
MATERIALS = {'bore_dark': {'kind': 'dark', 'color': (12, 15, 17), 'detail': 0, 'amp': 0, 'rim': 0}, 'optic_inner': {'kind': 'dark', 'color': (20, 24, 27), 'detail': 0, 'amp': 1, 'rim': 0.05}, 'rubber_pad': {'kind': 'rubber', 'color': (25, 28, 29), 'detail': 0.15, 'amp': 6, 'field': 0.025, 'rim': 0.04}, 'silver_steel': {'kind': 'steel', 'color': (135, 140, 140), 'detail': 0.6, 'amp': 10, 'field': 0.1, 'rim': 0.19}, 'black_recess': {'kind': 'dark', 'color': (23, 26, 29), 'detail': 0.3, 'amp': 2, 'rim': 0.06}, 'camo_paint': {'kind': 'paint', 'color': (65, 60, 68), 'detail': 0.45, 'amp': 2, 'field': 0.055, 'rim': 0.11}, 'barrel_steel': {'kind': 'steel', 'color': (181, 182, 184), 'detail': 0.45, 'amp': 11, 'field': 0.11, 'rim': 0.17}, 'white_paint': {'kind': 'paint', 'color': (206, 205, 199), 'detail': 0.35, 'amp': 2, 'field': 0.045, 'rim': 0.1}, 'collar_steel': {'kind': 'steel', 'color': (143, 148, 147), 'detail': 0.45, 'amp': 10, 'field': 0.1, 'rim': 0.18}, 'frame_polymer': {'kind': 'polymer', 'color': (66, 63, 54), 'detail': 0.75, 'amp': 5, 'rim': 0.08}, 'grip_rubber': {'kind': 'rubber', 'color': (52, 49, 42), 'detail': 0.4, 'amp': 6, 'rim': 0.05}, 'coil_metal': {'kind': 'metal', 'color': (33, 42, 34), 'detail': 0.4, 'amp': 7, 'field': 0.08, 'rim': 0.11}, 'logo_metal': {'kind': 'metal', 'color': (34, 35, 40), 'detail': 0, 'amp': 4, 'rim': 0.08}}
MATERIAL_ROLES = {'grey': 'frame_polymer', 'grey_dk': 'frame_polymer', 'camo': 'camo_paint', 'camo_lt': 'camo_paint', 'camo_dk': 'camo_paint', 'white': 'barrel_steel', 'white_dk': 'collar_steel', 'black': 'black_recess', 'coil': 'coil_metal', 'green': 'logo_metal', 'steel': 'silver_steel'}

def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith('sight') and ((name.endswith('left') and face=='east') or (name.endswith('right') and face=='west') or (name.endswith('top') and face=='down') or (name.endswith('bottom') and face=='up')):return 'optic_inner'
    if name.startswith('white_'):return 'white_paint'
    if name=='logo_plate':return 'logo_metal'
    if name.startswith('grip'):return 'grip_rubber'
    if name.startswith('butt_pad'):return 'rubber_pad'
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

    if side and n=='logo_plate':
        if .05<s<.95 and .2<t<.8 and lettering('VEIST',(s-.05)/.9,(t-.2)/.6):return (160,197,65,255)
    if mat_of(n)=='camo' and material_key(n,fn)=='camo_paint':
        # Limited hard-edged paint islands, not a flat fill over the entire receiver.
        # A continuous model-space mask follows the original purple/charcoal patches.
        a,b=FACE_UV[fn];p=[(e['from'][i]+e['to'][i])/2 for i in range(3)]
        p[a]=e['from'][a]+(e['to'][a]-e['from'][a])*(1-s if fn=='west' else s)
        p[b]=e['to'][b]-(e['to'][b]-e['from'][b])*t
        z,y0=round(p[2]*7)/7,round(p[1]*7)/7
        v=math.sin(z*1.7+y0*.4)+math.sin(z*.6-y0*2.4+.7)
        if v>1.18:return (99,91,104,255)
        if v<-1.25:return (39,37,44,255)
    if n=='white_fin' and side and .15<t<.93 and any(abs(u-(a+t*.18))<.055 for a in (.15,.4,.65)):
        return (48,52,49,255)
    return None


# MATERIAL R2: bare metal interfaces, explicit rubber/polymer contrast, sparse motifs.
MATERIALS['frame_polymer'].update(color=(77,75,65),plate=False)
MATERIALS['grip_rubber'].update(color=(27,29,24),plate=False,field=.02)
MATERIALS['rubber_pad'].update(color=(25,27,24),plate=False)
MATERIALS['camo_paint'].update(wear=False)
MATERIALS['white_paint'].update(wear=(157,164,160))
MATERIALS['receiver_metal']={'kind':'metal','color':(88,91,98),'detail':.5,'amp':6,'field':.07}
MATERIALS['frame_steel']={'kind':'steel','color':(107,115,109),'detail':.4,'amp':7,'field':.065}

_r1_material_key=material_key
def material_key(name,face):
    if name.endswith('_bore_back'):return 'bore_dark'
    if name.startswith(('rec_body','rec_mid','rec_top')):return 'receiver_metal'
    if name.startswith(('frame_lip','frame_tab','fin_','trigger','side_lever','leg_bolt','white_cap_lip')):return 'frame_steel'
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
    if side and n.startswith('tube_') and not n.startswith(('tube_rail','tube_band','tube_collar','tube_neck')):
        if y in (round(.28*(h-1)),round(.62*(h-1))) and x%13 in (4,5,6):return (73,84,81,255)
    return _r1_special(e,fn,s,t)
