"""W325 Dissonance-34 (rare sidearm, Rapid-Fire) over base dead_man_walking_xx7463 (W219 reload bank + W153 sight).

Rip -> model: uniform 45 px/m, rip rear (y 0.033) -> z 9.4, rip top (z 0.16) -> y 15.5, rip x -> -(x-8).
At this scale the rip lands on the base almost 1:1 (muzzle -4.6 vs -4.84, grip heel y 6.8 vs 6.63, casing width
+-1.6 vs +-1.5, rear slide +-1.04 vs +-0.97), so nothing is moved.  Cross sections follow the rip front view:
pointed roof (top +-0.55) over a wide side pod line (+-1.6 at y 13.6) on the front casing, narrower roof on the slide.
Detail pass (W325 r2, Dead Man Walking style): every long mass is split into machined segments with chamfered
edges (front casing in two pod sections around a recessed seam ring, side plate, three slide segments with steps),
flat clean panel colours, 1-texel engraved lines from the kit pixel style.  Earlier r2 notes: muzzle cap with a real raised bore ring, chamfered frame/rear cap, proud checkered grip
panels, guard and grip-rest blocks; slide lowered to the base rear-slide top (15.2) and rear posts aligned to the base
posts (z 7.45..7.71) so ADS stays clear (kit adscheck OK).
Sight: front blade z -3.65..-3.1 top 15.78 and rear posts z 7.45..7.75 top 16.2 = base W153 heights.
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
    col = int(u / cw); row = math.floor((y0 - y) / ch)
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


S = 45.0
T = 20
PALETTE = 18
FLAT_TOL = 30
PALETTE_KEEP = [(120, 170, 70), (214, 210, 200)]

PORTS = [(-1.65, 14.05), (-2.1, 14.05), (-2.55, 14.05), (-1.4, 13.72), (-1.85, 13.72), (-2.3, 13.72), (-2.75, 13.72)]
CASING, SLIDE, FRAME, DARK, LIGHT = (98, 96, 88), (82, 80, 74), (58, 57, 54), (30, 30, 32), (214, 210, 200)


def casing(name, z0, z1, k=1.0):
    """Front casing section (rip front view): pointed chamfered roof over wide side pods, chamfered belly."""
    out = prism(name + '_pod', 6.4 + (1 - k), 9.6 - (1 - k), 13.05, 13.95, z0, z1, .3)
    out += prism(name, 7.0 + (1 - k), 9.0 - (1 - k), 12.0, 15.45 - (1 - k) * .5, z0, z1, .62, .38)
    return out


def _elements():
    E = []
    # ---- front casing: two pod sections around a recessed seam ring, light muzzle cap with a raised bore ring
    E += casing('casA', -4.35, -2.35)
    E += casing('seam', -2.35, -2.1, .85)
    E += casing('casB', -2.1, -0.08)
    E += prism('muzzle_cap', 7.05, 8.95, 12.6, 14.45, -4.62, -4.35, .3)
    for tag, lo, hi in (('t', (7.64, 14.85, -4.72), (8.36, 15.05, -4.35)), ('b', (7.64, 14.15, -4.72), (8.36, 14.35, -4.35)),
                        ('l', (7.64, 14.35, -4.72), (7.84, 14.85, -4.35)), ('r', (8.16, 14.35, -4.72), (8.36, 14.85, -4.35))):
        E.append(B(f'bore_ring_{tag}', lo, hi))
    E.append(B('bore_stop', (7.84, 14.35, -4.66), (8.16, 14.85, -4.6)))
    E.append(B('muzzle_ledge', (7.6, 13.0, -4.75), (8.4, 13.5, -4.62)))
    E.append(B('front_sight_base', (7.65, 15.38, -3.8), (8.35, 15.56, -2.8)))
    E.append(B('front_sight_blade', (7.92, 15.5, -3.65), (8.08, 15.76, -3.1)))
    # ---- side plate over the slide front, then three slide segments (top at the base rear-slide 15.2)
    E += prism('side_plate', 6.62, 9.38, 13.1, 14.6, -0.08, 2.3, .25)
    E += prism('slideA', 6.96, 9.04, 13.2, 15.2, -0.08, 4.9, .55, .2)
    E += prism('slideB', 7.06, 8.94, 13.3, 15.1, 4.9, 7.15, .5, .2)
    E += prism('slideC', 6.96, 9.04, 13.2, 15.2, 7.15, 9.1, .55, .2)
    for i in range(4):
        z = 7.35 + i * .4
        E.append(B(f'serration_{i}', (7.0, 13.6, z), (9.0, 14.5, z + .2)))
    E += prism('rear_cap', 7.1, 8.9, 13.9, 14.95, 9.1, 9.3, .22)
    E.append(B('rear_sight_floor', (7.43, 15.2, 7.21), (8.57, 15.5, 7.95)))
    E.append(B('rear_sight_post_l', (7.42, 15.4, 7.45), (7.56, 16.2, 7.71)))
    E.append(B('rear_sight_post_r', (8.44, 15.4, 7.45), (8.58, 16.2, 7.71)))
    # ---- frame under the slide (chamfered bottom), rear haunch sweeping into the grip, pins, release
    E += prism('frame', 7.15, 8.85, 12.05, 13.3, -0.08, 7.4, 0, .18)
    E.append(B('frame_nose', (7.25, 11.85, -0.6), (8.75, 12.1, 1.6)))
    E.append(B('haunch', (7.05, 13.25, 6.75), (8.95, 14.0, 9.3), R((8, 13.25, 8.02), x=-36)))
    E.append(B('pin_front', (7.08, 13.0, 2.0), (8.92, 13.25, 2.25)))
    E.append(B('pin_rear', (7.08, 12.75, 3.0), (8.92, 13.0, 3.25)))
    E.append(B('frame_release', (7.05, 11.9, 4.9), (8.95, 12.3, 5.35)))
    E.append(B('port_frame', (6.9, 13.55, 3.0), (9.1, 14.4, 3.12)))
    # ---- trigger guard (open, chamfered corners) and trigger
    E.append(B('guard_front', (7.78, 10.65, 1.0), (8.22, 12.1, 1.35), R((8, 11.5, 1.18), x=-25)))
    E.append(B('guard_corner', (7.80, 10.25, 1.4), (8.20, 10.85, 2.0), R((8, 10.52, 1.72), x=45)))
    E.append(B('guard_bottom', (7.78, 10.25, 1.8), (8.22, 10.6, 4.7)))
    E.append(B('guard_rear', (7.81, 10.4, 4.55), (8.19, 12.25, 4.95), R((8, 10.8, 4.75), x=28)))
    E.append(B('trigger_blade', (7.88, 11.45, 3.72), (8.12, 12.1, 3.98)))
    E.append(B('trigger_mid', (7.88, 10.96, 3.8), (8.12, 11.45, 4.05)))
    E.append(B('trigger_tip', (7.88, 10.72, 3.98), (8.12, 10.96, 4.2)))
    # ---- grip (23 deg rake): core, front rest, proud checkered panels, backstrap lip
    G = R((8, 10.0, 6.98), x=-23)
    E.append(B('grip_core', (7.2, 7.15, 5.85), (8.8, 12.6, 8.1), G))
    E.append(B('grip_front_rest', (7.3, 7.2, 5.6), (8.7, 8.4, 5.9), G))
    for s, (xa, xb) in (('l', (7.15, 7.2)), ('r', (8.8, 8.85))):
        E.append(B(f'grip_panel_{s}', (xa, 7.6, 6.1), (xb, 11.6, 7.65), G))
    E.append(B('grip_backstrap_lip', (7.3, 11.2, 7.95), (8.7, 12.4, 8.3), G))
    # ---- magazine (moving leaf): white heel plate + lip + shaft inside the grip
    E.append(B('mag_heel', (7.08, 6.8, 6.35), (8.92, 7.3, 9.4), R((8, 7.05, 7.9), x=-5)))
    E.append(B('mag_shaft', (7.45, 7.2, 6.45), (8.55, 11.6, 7.65), G))
    return E


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / S, 0.033 + (z - 9.4) / S, 0.16 + (y - 15.5) / S)


def _c(c): return tuple(c) + (255,)




def elements():
    return tidy(_elements())




# W325 r6: material-aware surface; special() is reserved for sparse marks and source camo chips.
STYLE = 'material'
def _mat(key, face):
    m=dict(MATERIALS[key])
    # End faces and chamfer edges have no reliable source footprint; never stretch side relief over them.
    if face not in ('east','west'):m['detail']=0
    return m

def _mark(c,e,fn,s,t,kind='paint'):
    """Material-matched decal paint, preserving crisp boundaries without a flat plastic fill."""
    import kit as _k
    _,u,v=_k.face_frame(e,fn);w=max(1,round(math.dist((0,0,0),u)*T));h=max(1,round(math.dist((0,0,0),v)*T))
    i,j=int(s*w),int(t*h)
    grain=((j*37)%11-5)*1.2 if kind=='steel' else ((i*17+j*29)%23-11)*.13
    field=.98+.035*math.cos(t*math.pi)
    return tuple(max(0,min(255,round(x*field+grain))) for x in c)+(255,)

_RIP_VIEWS=None
def _source(e,fn,s,t):
    global _RIP_VIEWS
    import kit as _k
    if _RIP_VIEWS is None:
        p=_Path(__file__).resolve().parent.parent/MATERIAL_WID/'proj_cache'
        man=_json.loads((p/'manifest.json').read_text())
        _RIP_VIEWS={k:_k.View(p,k,man) for k in man['views']}
    p=_k.face_point(e,fn,s,t);normal=_k.rotate_vec(_k.NORMALS[fn],_k.rot_of(e));a=model2world(e['name'],p)
    b=model2world(e['name'],tuple(p[i]+normal[i]*.25 for i in range(3)))
    wn=[b[i]-a[i] for i in range(3)];axis=max(range(3),key=lambda i:abs(wn[i]));v=_RIP_VIEWS[('p' if wn[axis]>0 else 'n')+'xyz'[axis]]
    return v.sample(*v.project(a))

def _camo_chip(e,fn,s,t,light,threshold=125):
    if fn not in ('east','west','up'):return None
    c=_source(e,fn,s,t)
    if c is None or sum(c[:3])/3<threshold:return None
    lum=sum(c[:3])/3
    tone=.82+.18*min(1,max(0,(lum-threshold)/(220-threshold)))
    return _mark(tuple(round(x*tone) for x in light),e,fn,s,t)
MATERIAL_WID='dissonance_34'
MATERIALS={
 'casing':dict(kind='metal',color=(91,86,78),detail=.75,amp=6,field=.055),
 'slide':dict(kind='steel',color=(77,74,69),detail=.65,amp=8),
 'frame':dict(kind='polymer',color=(43,43,40),detail=.4,amp=3),
 'grip':dict(kind='rubber',color=(32,30,27),detail=0,amp=5),
 'silver':dict(kind='steel',color=(190,191,180),detail=.35,amp=8),
 'steel':dict(kind='metal',color=(92,96,94),detail=.35,amp=8),
 'bore':dict(kind='dark',color=(17,19,20),detail=0),
 'magazine':dict(kind='steel',color=(48,52,54),detail=0,amp=6)}
def material(n,fn):
 if n=='bore_stop':k='bore'
 elif n.startswith(('muzzle_cap','muzzle_ledge','mag_heel')):k='silver'
 elif n.startswith('grip_panel'):k='grip'
 elif n.startswith(('grip','frame','haunch','guard','seam')):k='frame'
 elif n.startswith(('pin_','frame_release','bore_ring','trigger','serration')):k='steel'
 elif n.startswith(('slide','rear_cap')):k='slide'
 elif n.startswith(('rear_sight','front_sight')):k='bore'
 elif n.startswith('mag_'):k='magazine'
 else:k='casing'
 return _mat(k,fn)
def special(e,fn,s,t):
 import kit as _k
 n=e['name'];x,y,z=_k.face_point(e,fn,s,t);side=fn in ('east','west')
 if n=='port_frame':return _mark((165,39,32),e,fn,s,t)
 if n.startswith('front_sight_blade') and fn=='up':return (220,221,209,255)
 if side and n.startswith(('slideA','slideB','slideC')):
  if text_hit(e,fn,s,t,'#SUROS',3.65 if fn=='west' else 6.8,14.56,.125,.075):return (144,177,83,255)
 if side and n.startswith(('cas','side_plate')):
  for cz,cy in PORTS:
   d=math.hypot(z-cz,y-cy)
   if d<.13:return (15,18,18,255)
   if d<.17:return (118,119,108,255)
 return None

# Material pass 2: exposed SUROS frame/guard and controls are metal; grip core and rubber are distinct.
MATERIALS['casing'].update(color=(101,97,88))
MATERIALS['slide'].update(color=(67,70,68))
MATERIALS['frame'].update(kind='metal',color=(69,72,67))
MATERIALS['grip'].update(color=(18,19,17),amp=3)
MATERIALS['steel'].update(color=(116,123,119))
MATERIALS['polymer']=dict(kind='polymer',color=(57,60,54),detail=0,amp=2)
_r2_material_before=material
_r2_special_before=special
def material(n,fn):
 if n.startswith(('grip_core','grip_front_rest','grip_backstrap')):return _mat('polymer',fn)
 if n.startswith(('frame_release','pin_','guard','trigger')):return _mat('steel',fn)
 return _r2_material_before(n,fn)
def special(e,fn,s,t):
 c=_r2_special_before(e,fn,s,t)
 if c is not None:return c
 if fn in ('east','west') and e['name'].startswith(('slideA','slideB','slideC')):
  import kit as _k
  x,y,z=_k.face_point(e,fn,s,t)
  # SUROS nameplate engraving: one texel lower rule and two end ticks, not a flat-filled plate.
  if 3.6<z<6.85 and abs(y-14.07)<.025:return (122,135,105,255)
  if (abs(z-3.6)<.025 or abs(z-6.85)<.025) and 14.07<y<14.22:return (122,135,105,255)
 return None
