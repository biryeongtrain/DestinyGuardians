"""W325 Traveler's Chosen (common sidearm, Adaptive) over base allied_demand (W219 reload bank + W151 sight).

Rip -> model: uniform 32 px/m, rip grip back (y 0.028) -> z 10, rip slide top (z 0.155) -> y 13.25, rip x -> -(x-8).
The rip has no suppressor, so the muzzle lands at z ~1.0 where the base slide/suppressor joint is (base slide
1.3..9.5); grip, trigger (z ~6.2) and magazine box (z 8.2..9.9, y 6.7..10.6) fall onto the base contract unmoved.
Detail pass (W325 r2): 45 deg chamfered slide/frame edges (corner bars never rise above the flat top), real bore,
octagonal chrome dial, proud wood grip panels, raised rear-sight wings at the base W151 notch (z 8.19..8.61, top
13.43), front blade on the base blade (z 1.75..2.09, top 13.43).  ADS: everything stays under the base top profile
(slide 13.25, beavertail kept under 11.4 behind z 9.6); verified with kit adscheck.
Style pass (W325 r3, W30 / Dead Man Walking look): slide split into machined segments with chamfers, flat painted
panels (lilac/black/blue/wood), proud emblem plate and chrome dial, split wood grip panels, slanted slide vents.
"""
# ---------------------------------------------------------------- shared W325-7 shape helpers (inlined per weapon)
import json as _json, math
from pathlib import Path as _Path

_FLAT_P = _Path(__file__).resolve().parent / 'flat_faces.json'
FLAT = _json.loads(_FLAT_P.read_text()) if _FLAT_P.exists() else {}   # faces the projection smears -> flat rip colour


def B(name, lo, hi, rot=None, **kw):
    e = {'name': name, 'from': list(lo), 'to': list(hi)}
    if rot: e['rotation'] = rot
    e.update(kw)
    return e


def R(origin, x=0.0, y=0.0, z=0.0):
    return {'origin': list(origin), 'x': x, 'y': y, 'z': z}


def bevel(name, x0, x1, y0, y1, z0, z1, b, top=True, bottom=False):
    """Legacy name: box with 45 deg chamfers on its top (and/or bottom) long edges (see prism)."""
    return prism(name, x0, x1, y0, y1, z0, z1, b if top else 0, b if bottom else 0)


def bar45(name, cx, cy, b, z0, z1):
    """Single 45 deg corner bar (vertices at cx+-b / cy+-b)."""
    h = b / math.sqrt(2)
    return B(name, (cx - h, cy - h, z0), (cx + h, cy + h, z1), R((cx, cy, (z0 + z1) / 2), z=45))


def prism(name, x0, x1, y0, y1, z0, z1, bt, bb=None):
    """Machined block with 45 deg chamfers on its long edges (top leg bt, bottom leg bb; 0 = square edge).
    Parts touch exactly (no overlap); chamfer bars are recessed 0.012 px at the ends so end faces never z-fight."""
    bb = bt if bb is None else bb; ei = .012
    out = [B(name, (x0, y0 + bb, z0), (x1, y1 - bt, z1))]
    if bt: out.append(B(name + '_t', (x0 + bt, y1 - bt, z0), (x1 - bt, y1, z1)))
    if bb: out.append(B(name + '_b', (x0 + bb, y0, z0), (x1 - bb, y0 + bb, z1)))
    for tag, cy, b in (('t', y1 - bt, bt), ('b', y0 + bb, bb)):
        if not b: continue
        for sd, cx in (('l', x0 + b), ('r', x1 - b)):
            out.append(bar45(f'{name}_c{tag}{sd}', cx, cy, b, z0 + ei, z1 - ei))
    return out


def _rkey(e):
    r = e.get('rotation')
    if not r or not any(r.get(a, 0) for a in 'xyz'): return None
    return (tuple(round(v, 4) for v in r['origin']), r.get('x', 0), r.get('y', 0), r.get('z', 0))


def tidy(E, eps=.012):
    """No coplanar overlaps (z-fighting / crossing bevel lines): where two parts with the same frame share a face
    plane and overlap on it, the face of the smaller part is pulled back by eps so the larger face wins cleanly.
    Faces along a pure z rotation axis (chamfer bars) are compared with unrotated parts too."""
    def zonly(e):
        k = _rkey(e); return k is None or (k[1] == 0 and k[2] == 0)
    def vol(e): return abs((e['to'][0] - e['from'][0]) * (e['to'][1] - e['from'][1]) * (e['to'][2] - e['from'][2]))
    for _ in range(3):
        moved = False
        for i, a in enumerate(E):
            for b in E[i + 1:]:
                same = _rkey(a) == _rkey(b)
                for ax in range(3):
                    if not same and not (ax == 2 and zonly(a) and zonly(b)): continue
                    for side in ('from', 'to'):
                        if abs(a[side][ax] - b[side][ax]) > 1e-4: continue
                        if same:
                            area = 1
                            for k in range(3):
                                if k == ax: continue
                                area *= max(0, min(a['to'][k], b['to'][k]) - max(a['from'][k], b['from'][k]))
                        else:
                            area = 1 if (min(a['to'][0], b['to'][0]) > max(a['from'][0], b['from'][0]) - .3 and
                                         min(a['to'][1], b['to'][1]) > max(a['from'][1], b['from'][1]) - .3) else 0
                        if area <= 1e-4: continue
                        lo = a if vol(a) < vol(b) else b
                        lo[side] = list(lo[side]); lo[side][ax] += eps if side == 'from' else -eps; moved = True
        if not moved: break
    return E


def flat(e, fn):
    c = FLAT.get(e['name'], {}).get(fn)
    return None if c is None else (c[0], c[1], c[2], 255)
# ---------------------------------------------------------------- end helpers


FONT = {'S': ('111', '100', '111', '001', '111'), 'U': ('101', '101', '101', '101', '111'),
        'R': ('110', '101', '110', '101', '101'), 'O': ('111', '101', '101', '101', '111'),
        'H': ('101', '101', '111', '101', '101'), 'A': ('010', '101', '111', '101', '101'),
        'K': ('101', '110', '100', '110', '101'), 'E': ('111', '100', '110', '100', '111'),
        'V': ('101', '101', '101', '101', '010'), 'I': ('111', '010', '010', '010', '111'),
        'T': ('111', '010', '010', '010', '010'), 'M': ('101', '111', '111', '101', '101'),
        'G': ('111', '100', '101', '101', '111'), 'N': ('111', '101', '101', '101', '101'),
        'C': ('111', '100', '100', '100', '111'), 'D': ('110', '101', '101', '101', '110'),
        'L': ('100', '100', '100', '100', '111'), '#': ('111', '111', '111', '111', '111')}


def text_hit(e, fn, s, t, txt, z0, y0, cw, ch):
    """True if face point lies on a lit glyph texel of txt written along the gun side (west face: reads rear->muzzle
    starting at z0 going +z ... east face: starting at z0 going -z). z0 = start z, y0 = top y, cw/ch = cell size."""
    if fn not in ('east', 'west'): return False
    import kit as _k
    x, y, z = _k.face_point(e, fn, s, t)
    d = -1 if fn == 'west' else 1
    u = (z - z0) if fn == 'west' else (z0 - z)
    if u < 0: return False
    col = int(u / cw); row = int((y0 - y) / ch)
    if row < 0 or row > 4: return False
    gi, gc = divmod(col, 4)
    if gi >= len(txt) or gc == 3: return False
    g = FONT.get(txt[gi])
    return bool(g) and g[row][gc] == '1'


def holes_hit(e, fn, s, t, centres, r):
    if fn not in ('east', 'west'): return False
    import kit as _k
    x, y, z = _k.face_point(e, fn, s, t)
    return any(math.hypot(z - cz, y - cy) < r for cz, cy in centres)


S = 32.0
T = 20
PALETTE = 20
FLAT_TOL = 30
PALETTE_KEEP = [(196, 40, 40), (70, 230, 90), (24, 70, 140)]

LILAC, BLACK, BLUE, WOOD, CHROME, DARK = (176, 176, 196), (42, 42, 46), (24, 70, 140), (66, 58, 52), (214, 216, 220), (22, 22, 24)


def _elements():
    E = []
    X0, X1 = 7.38, 8.62
    # ---- slide in three machined segments (front block, mid with side window, rear), chamfered top edges
    E += prism('slideF', X0, X1, 11.95, 13.25, 1.3, 4.55, .2, .08)
    E += prism('slideM', 7.42, 8.58, 12.0, 13.2, 4.55, 6.0, .2, .08)
    E += prism('slideR', X0, X1, 11.95, 13.25, 6.0, 8.3, .2, .08)
    E += prism('nose_top', X0, X1, 12.85, 13.25, 1.0, 1.3, .2, 0)
    E.append(B('nose_bottom', (X0, 11.95, 1.0), (X1, 12.3, 1.3)))
    E.append(B('nose_l', (X0, 12.3, 1.0), (7.76, 12.85, 1.3)))
    E.append(B('nose_r', (8.24, 12.3, 1.0), (X1, 12.85, 1.3)))
    E.append(B('bore_stop', (7.76, 12.3, 1.3), (8.24, 12.85, 1.36)))
    for i in range(3):
        z = 2.9 + i * .3
        E.append(B(f'vent_{i}', (7.34, 12.12, z), (8.66, 12.22, z + .16), R((7.34, 12.17, z + .08), x=-35)))
    E.append(B('front_blade', (7.92, 13.25, 1.75), (8.08, 13.43, 2.09)))
    E.append(B('blade_base', (7.76, 13.2, 1.66), (8.24, 13.29, 2.2)))
    E.append(B('sight_dot', (7.9, 13.2, 5.75), (8.1, 13.27, 6.05)))
    # ---- frame: chamfered dust cover with rail teeth, mid frame, rear receiver, beavertail
    E += prism('dust_cover', 7.42, 8.58, 11.4, 11.96, 1.55, 4.45, 0, .12)
    for i, z in enumerate((1.7, 2.35, 3.0, 3.65)):
        E.append(B(f'rail_tooth_{i}', (7.5, 11.22, z), (8.5, 11.4, z + .4)))
    E.append(B('frame_mid', (7.42, 11.0, 4.45), (8.58, 11.96, 7.6)))
    E.append(B('frame_step', (7.42, 11.0, 4.45), (8.58, 11.4, 4.75)))
    E += prism('frame_rear', 7.4, 8.6, 10.75, 12.95, 7.6, 9.35, .2, 0)
    E.append(B('rear_cap', (7.46, 11.4, 9.35), (8.54, 12.8, 9.48)))
    E.append(B('beavertail', (7.44, 10.95, 9.3), (8.56, 11.7, 9.65)))
    E.append(B('beavertail_tip', (7.46, 10.92, 9.6), (8.54, 11.32, 10.2)))
    E.append(B('hammer_body', (7.62, 12.95, 8.19), (8.38, 13.12, 8.95)))
    E.append(B('rear_sight_l', (7.66, 13.12, 8.19), (7.84, 13.43, 8.61)))
    E.append(B('rear_sight_r', (8.16, 13.12, 8.19), (8.34, 13.43, 8.61)))
    # emblem plate (proud), chrome dial with bezel, pins
    E.append(B('emblem', (7.34, 12.1, 6.15), (8.66, 12.92, 6.95)))
    E.append(B('dial', (7.28, 12.1, 7.02), (8.72, 12.8, 7.72)))
    E.append(B('dial_cap', (7.24, 12.2, 7.12), (8.76, 12.7, 7.62)))
    E.append(B('pin_rear', (7.33, 11.55, 7.9), (8.67, 11.8, 8.15)))
    E.append(B('pin_front', (7.36, 11.15, 5.0), (8.64, 11.35, 5.2)))
    # ---- trigger guard (real opening, chamfered corners) and trigger
    E.append(B('guard_front', (7.8, 10.3, 4.5), (8.2, 11.05, 4.8), R((8, 10.7, 4.65), x=-8)))
    E.append(B('guard_corner', (7.8, 9.98, 4.62), (8.2, 10.42, 5.06), R((8, 10.2, 4.84), x=45)))
    E.append(B('guard_bottom', (7.8, 9.95, 4.85), (8.2, 10.22, 7.25)))
    E.append(B('guard_rear', (7.8, 10.05, 7.0), (8.2, 10.7, 7.4), R((8, 10.4, 7.2), x=-20)))
    E.append(B('trigger_blade', (7.92, 10.5, 6.02), (8.08, 11.0, 6.22), R((8, 10.75, 6.12), x=-12)))
    E.append(B('trigger_tip', (7.92, 10.2, 6.18), (8.08, 10.55, 6.36), R((8, 10.4, 6.27), x=35)))
    # ---- raked grip: lilac frame core, backstrap, heel, proud wood panels split in two
    G = R((8, 8.9, 8.75), x=-18)
    E.append(B('grip_core', (7.45, 7.0, 7.95), (8.55, 11.2, 9.55), G))
    E.append(B('grip_back', (7.45, 7.0, 9.55), (8.55, 10.75, 10.1), G))
    for sd, (xa, xb) in (('l', (7.38, 7.45)), ('r', (8.55, 8.62))):
        E.append(B(f'wood_up_{sd}', (xa, 9.15, 8.15), (xb, 10.35, 9.25), G))
        E.append(B(f'wood_lo_{sd}', (xa, 7.65, 8.15), (xb, 9.0, 9.25), G))
    # ---- magazine (moving leaf): body inside the grip + floorplate with lip
    E.append(B('mag_body', (7.58, 7.3, 8.2), (8.42, 10.6, 9.3), G))
    E.append(B('mag_floor', (7.42, 6.72, 8.25), (8.58, 7.05, 9.95), R((8, 6.9, 9.1), x=-9)))
    E.append(B('mag_lip', (7.48, 7.0, 8.35), (8.52, 7.12, 9.75), R((8, 6.9, 9.1), x=-9)))
    return E


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / S, 0.028 + (z - 10.0) / S, 0.155 + (y - 13.25) / S)


def _c(c): return tuple(c) + (255,)


def slide_side(z, y):
    """Rip slide side panels as flat blocks: raised black window band front-top, black lower band rising rearward,
    blue receiver patch at the rear."""
    if 2.6 < z < 5.3 and 12.62 < y < 13.05: return BLACK
    if z < 6.3 and y < 12.05 + (6.3 - z) * .1 and y < 12.5: return BLACK
    if z > 7.85 and y > 12.25: return BLUE
    if 5.6 < z < 6.15 and y > 12.75: return BLUE
    return LILAC




def _faces_bore(e, fn):
    f, t = e['from'], e['to']
    cx, cy = (f[0] + t[0]) / 2, (f[1] + t[1]) / 2
    nx, ny = {'east': (1, 0), 'west': (-1, 0), 'up': (0, 1), 'down': (0, -1)}[fn]
    return nx * (8.0 - cx) + ny * (12.575 - cy) > 0.05


def elements():
    return tidy(_elements())


# W325 material pass 2: lilac outer coat, exposed metal receiver/rail, chrome control and dark wood grip.
STYLE='material'
MATERIALS={
 'lilac':dict(kind='paint',color=(170,172,191),wear=(47,52,59),detail=.25,amp=2),
 'blue':dict(kind='metal',color=(28,68,114),detail=.2,amp=4),
 'receiver':dict(kind='steel',color=(79,88,100),detail=.2,amp=5),
 'guard':dict(kind='metal',color=(106,118,131),detail=.15,amp=4),
 'grip_frame':dict(kind='steel',color=(145,150,166),detail=.15,amp=5),
 'chrome':dict(kind='steel',color=(192,201,209),detail=0,amp=3),
 'wood':dict(kind='wood',color=(62,46,33),detail=0,amp=7),
 'rubber':dict(kind='rubber',color=(18,20,22),detail=0,amp=3),
 'polymer':dict(kind='polymer',color=(58,66,73),detail=.15,amp=2),
 'bore':dict(kind='dark',color=(12,16,20),detail=0),
 'magazine':dict(kind='steel',color=(72,83,94),detail=0,amp=5)}
def material(n,fn):
 if n.startswith('wood'):key='wood'
 elif n.startswith('dial') or n.startswith('pin_'):key='chrome'
 elif n.startswith(('guard','trigger')):key='guard'
 elif n.startswith('grip_core'):key='grip_frame'
 elif n.startswith('grip_back'):key='rubber'
 elif n.startswith(('mag_','rail','dust','beavertail','frame_mid','frame_step')):key='magazine'
 elif n.startswith(('frame_rear','rear_cap')):key='blue'
 elif n.startswith(('front_blade','rear_sight','bore','vent_')):key='bore'
 elif n in ('blade_base','hammer_body'):key='polymer'
 elif n.startswith('slideM'):key='receiver'
 elif n.startswith(('slide','nose','emblem')):key='lilac'
 else:key='receiver'
 m=dict(MATERIALS[key])
 if fn not in ('east','west'):m['detail']=0
 if n=='emblem':m['wear']=False
 return m

def special(e,fn,s,t):
 import kit as _k
 n=e['name'];side=fn in ('east','west');x,y,z=_k.face_point(e,fn,s,t)
 if n=='sight_dot':return (73,220,87,255)
 if n=='front_blade' and fn=='south':return (228,231,219,255)
 if n=='emblem' and side:
  # Traveler emblem: blue centre and six tiny red wreath spokes, at one-texel stroke width.
  dz,dy=z-6.55,y-12.50;r=math.hypot(dz,dy)
  if r<.09:return (27,68,143,255)
  if .12<r<.30:
   a=math.atan2(dy,dz)
   if abs(math.sin(a*3))<.28 or (.20<r<.25 and int((a+math.pi)*5)%3!=0):return (174,36,35,255)
 if n=='dial_cap' and side:
  dz,dy=z-7.37,y-12.45;r=math.hypot(dz,dy)
  if .18<r<.23:return (74,85,99,255)
  if .06<r<.20 and abs(math.sin(math.atan2(dy,dz)*4))<.20:return (234,239,240,255)
 if n.startswith('wood') and side:
  f,to=e['from'],e['to'];i=int(s*(to[2]-f[2])*T);j=int(t*(to[1]-f[1])*T)
  if (i+int(j*.28))%9==0:return (38,27,19,255)
 return None
