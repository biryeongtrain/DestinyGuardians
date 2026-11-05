"""W325 Roderic-C (rare sidearm, Precision) over base lonesome (W164/W213 reload banks + W151 sight).

Rip -> model: uniform 48 px/m, rip rear (y 0.039) -> z 11.0, rip slide top (z 0.15) -> y 14.69 (base breech top).
The HAKKE compact is short: muzzle at -1.6 (base barrel -4.3).  The whole gun is pushed 0.8 px rearward against the
pure height fit so the trigger (z 5.75..6.25) and fat grip land on the base trigger 5.9..6.8 / grip 7.7..10.0.
Grip rake 22 deg (base 10), floorplate perpendicular to the grip axis like the rip; magazine body sits on the base
magazine box (local z 8.2..9.5).  Detail pass (W325 r2): ADS fix — slide top lowered from 14.85 to 14.6 (base shield roof 14.62) by compressing
the slide height (model2world stretches it back onto the rip), chamfered slide/frame edges, real bore and recoil
spring guide, slide serrations, front rail slots, beavertail, proud grip panels and stippled
finger grooves.
Sight: front blade z -1.2..-0.75 top 15.06 / rear wings z 8.4..9.0 top 15.15 =
base W151 heights.
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


S = 48.0
PALETTE = 18
FLAT_TOL = 30
ORANGE, SILVER, BLACK, DARK = (186, 104, 44), (196, 210, 204), (34, 38, 38), (18, 18, 20)
SY0, SY1, RY1 = 13.2, 14.6, 14.85      # slide built 13.2..14.6, samples rip slide 13.2..14.85
T = 20


def _elements():
    E = []
    X0, X1 = 7.38, 8.62
    # ---- slide (orange rear / silver front split is UV), chamfered top edges, 4-piece nose around a real bore
    E += prism('slideF', X0, X1, SY0, SY1, -1.25, 3.4, .22, .08)
    E += prism('slideM', 7.42, 8.58, 13.25, 14.55, 3.4, 3.55, .22, .08)
    E += prism('slideR', X0, X1, SY0, SY1, 3.55, 6.55, .22, .08)
    E += prism('slideG', 7.42, 8.58, 13.25, 14.42, 6.55, 7.0, .22, .08)       # seam groove (base top dips here)
    E += prism('slideS', X0, X1, SY0, SY1, 7.0, 9.55, .22, .08)
    E += bevel('slide_nose_top', X0, X1, 14.2, SY1, -1.55, -1.25, .2)
    E.append(B('slide_nose_bot', (X0, SY0, -1.55), (X1, 13.75, -1.25)))
    E.append(B('slide_nose_l', (X0, 13.75, -1.55), (7.74, 14.2, -1.25)))
    E.append(B('slide_nose_r', (8.26, 13.75, -1.55), (X1, 14.2, -1.25)))
    E.append(B('bore_stop', (7.74, 13.75, -1.25), (8.26, 14.2, -1.18)))
    E.append(B('slide_rear', (7.42, 13.25, 9.55), (8.58, 14.45, 9.75)))
    for i in range(4):
        z = 7.0 + i * .5
        for s, x in (('l', 7.34), ('r', 8.62)):
            E.append(B(f'serr_{s}{i}', (x, 13.5, z), (x + .04, 14.4, z + .22)))
    E.append(B('front_sight', (7.88, SY1, -1.2), (8.12, 15.06, -0.75)))
    E.append(B('rear_sight_base', (7.44, SY1, 8.4), (8.56, 14.7, 9.0)))
    E.append(B('rear_sight_l', (7.44, SY1, 8.44), (7.72, 15.15, 8.98)))
    E.append(B('rear_sight_r', (8.28, SY1, 8.44), (8.56, 15.15, 8.98)))
    # ---- silver recoil housing with guide rod, black frame (chamfered), slide stop lever and takedown button
    E += bevel('recoil_housing', 7.42, 8.58, 12.05, 13.2, -1.55, 0.55, .15, top=False, bottom=True)
    E.append(B('guide_rod', (7.86, 12.45, -1.62), (8.14, 12.75, -1.55)))
    E += prism('frameF', 7.28, 8.72, 11.35, 13.2, 0.55, 3.7, 0, .16)
    E += prism('frameR', 7.28, 8.72, 11.35, 13.2, 3.7, 9.75, 0, .16)
    for i in range(3):
        E.append(B(f'rail_slot_{i}', (7.36, 11.28, 0.8 + i * .7), (8.64, 11.36, 1.1 + i * .7)))
    E.append(B('frame_tail', (7.3, 12.4, 9.2), (8.7, 13.1, 9.75), R((8, 12.75, 9.5), x=-20)))
    E.append(B('beavertail', (7.34, 12.45, 9.7), (8.66, 12.9, 10.25)))
    E.append(B('slide_stop', (7.2, 12.5, 4.45), (8.8, 12.8, 6.5)))
    E.append(B('slide_stop_tab', (7.18, 12.42, 6.2), (8.82, 12.9, 6.55)))
    E.append(B('takedown', (7.2, 11.85, 6.25), (8.8, 12.35, 6.75)))
    E.append(B('takedown_v', (7.2, 11.95, 6.15), (8.8, 12.25, 6.85)))
    E.append(B('frame_catch', (7.20, 11.15, 7.0), (8.80, 11.5, 7.4)))
    # ---- trigger guard (open, squared front) and white trigger
    E.append(B('guard_front', (7.78, 9.45, 3.7), (8.22, 11.5, 4.15), R((8, 10.8, 3.92), x=-11)))
    E.append(B('guard_corner', (7.82, 9.4, 3.95), (8.18, 9.84, 4.39), R((8, 9.62, 4.17), x=45)))
    E.append(B('guard_bottom', (7.80, 9.45, 4.05), (8.20, 9.8, 6.8)))
    E.append(B('trigger_blade', (7.86, 10.0, 5.8), (8.14, 11.25, 6.22), R((8, 10.6, 6.0), x=18)))
    E.append(B('trigger_tip', (7.88, 9.88, 5.72), (8.12, 10.25, 6.0), R((8, 10.06, 5.86), x=35)))
    E.append(B('trigger_safety', (7.97, 10.4, 5.76), (8.03, 10.9, 5.82), R((8, 10.6, 6.0), x=18)))
    # ---- fat Glock grip, 22 deg rake; proud stippled side panels, finger grooves on the front strap
    G = R((8, 9.0, 8.85), x=-22)
    E.append(B('grip_core', (7.22, 6.25, 7.1), (8.78, 12.6, 10.4), G))
    for s, (xa, xb) in (('l', (7.18, 7.22)), ('r', (8.78, 8.82))):
        E.append(B(f'grip_panel_{s}', (xa, 6.7, 7.5), (xb, 11.3, 10.0), G))
    for i in range(3):
        E.append(B(f'finger_{i}', (7.3, 7.4 + i * 1.15, 6.98), (8.7, 7.75 + i * 1.15, 7.12), G))
    # ---- magazine (moving leaf): white floorplate perpendicular to the grip + body on the base magazine box
    E.append(B('mag_floor', (7.24, 5.85, 7.2), (8.76, 6.27, 10.3), G))
    E.append(B('mag_floor_lip', (7.3, 5.75, 7.3), (8.7, 5.87, 10.15), G))
    E.append(B('mag_body', (7.5, 6.2, 8.2), (8.5, 11.8, 9.5), G))
    return E


def model2world(name, p):
    x, y, z = p
    if y > SY0 and not name.startswith(('front_sight', 'rear_sight')):
        y = SY0 + (y - SY0) * (RY1 - SY0) / (SY1 - SY0)
    elif name.startswith(('front_sight', 'rear_sight')):
        y += RY1 - SY1
    return (-(x - 8.0) / S, 0.039 + (z - 11.0) / S, 0.15 + (y - 14.69) / S)




def _faces_bore(e, fn):
    if fn not in ('east', 'west', 'up', 'down'): return False
    f, t = e['from'], e['to']; cx, cy = (f[0] + t[0]) / 2, (f[1] + t[1]) / 2
    nx, ny = {'east': (1, 0), 'west': (-1, 0), 'up': (0, 1), 'down': (0, -1)}[fn]
    return nx * (8.0 - cx) + ny * (13.975 - cy) > 0.05


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
MATERIAL_WID='roderic_c'
MATERIALS={
 'orange':dict(kind='paint',color=(175,96,39),detail=.55,amp=2),
 'silver':dict(kind='steel',color=(181,197,187),detail=.45,amp=9,field=.06),
 'frame':dict(kind='polymer',color=(29,38,34),detail=.5,amp=3),
 'grip':dict(kind='rubber',color=(24,28,27),detail=0,amp=5),
 'lever':dict(kind='steel',color=(184,191,181),detail=.25,amp=8),
 'magazine':dict(kind='metal',color=(42,49,49),detail=0,amp=7),
 'bore':dict(kind='dark',color=(13,17,17),detail=0),
 'serration':dict(kind='metal',color=(100,63,30),detail=0,amp=5)}
def material(n,fn):
 if n.startswith(('bore','front_sight','rear_sight')):k='bore'
 elif n.startswith('serr_'):k='serration'
 elif n in ('slide_stop','takedown','takedown_v','guide_rod') or n.startswith(('trigger','mag_floor')):k='lever'
 elif n.startswith(('slideR','slideG','slideS','slide_rear')):k='orange'
 elif n.startswith(('slideF','slideM','slide_nose','recoil')):k='silver'
 elif n.startswith('grip_panel'):k='grip'
 elif n=='mag_body':k='magazine'
 else:k='frame'
 return _mat(k,fn)
def special(e,fn,s,t):
 import kit as _k
 n=e['name'];x,y,z=_k.face_point(e,fn,s,t);side=fn in ('east','west')
 if n.startswith(('slideR','slideG','slideS')) and side and text_hit(e,fn,s,t,'HAKKE',4.55 if fn=='west' else 6.65,14.32,.11,.1):return (17,20,18,255)
 if n.startswith('slideR') and z<3.8+(y-13.2)*.55:return _mark((181,197,187),e,fn,s,t,'steel')
 if n.startswith('grip_panel') and side:
  for ps,pt in ((.5,.12),(.5,.87)):
   d=math.hypot((s-ps)*2.5,(t-pt)*4.6)
   if d<.045:return (48,56,52,255)
   if d<.13:return _mark((162,174,164),e,fn,s,t,'steel')
 return None

# Material pass 2: orange coat is confined to the rear slide; frame/guard/rail are exposed metal.
MATERIALS['orange'].update(wear=(116,111,93))
MATERIALS['frame'].update(color=(56,65,59),detail=.15)
MATERIALS['grip'].update(color=(18,24,20),amp=3)
MATERIALS['frame_metal']=dict(kind='metal',color=(78,91,82),detail=.25,amp=5)
MATERIALS['guard_steel']=dict(kind='steel',color=(106,119,110),detail=.15,amp=5)
_r2_material_before=material
_r2_special_before=special
def material(n,fn):
 if n.startswith(('frameF','frameR','frame_tail','beavertail','rail_slot','frame_catch')):return _mat('frame_metal',fn)
 if n.startswith('guard'):return _mat('guard_steel',fn)
 return _r2_material_before(n,fn)
def special(e,fn,s,t):
 c=_r2_special_before(e,fn,s,t)
 if c is not None:return c
 if fn in ('east','west') and e['name'].startswith(('slideR','slideG')):
  import kit as _k
  x,y,z=_k.face_point(e,fn,s,t)
  if 4.55<z<6.65 and abs(y-13.62)<.025:return (88,61,36,255)
 if fn in ('east','west') and e['name'].startswith('mag_floor'):
  # Two short pressed floorplate ribs, one texel wide.
  if .22<t<.78 and (abs(s-.25)<.015 or abs(s-.75)<.015):return (100,115,104,255)
 return None
