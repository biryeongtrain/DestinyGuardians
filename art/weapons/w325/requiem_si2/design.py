"""W325 Requiem SI2 (rare sidearm, Adaptive Burst) over base high_albedo (W183 reload bank + W153 sight).

Rip -> model: 40 px/m, rip receiver rear (y 0.086) -> z 11.32 (base receiver rear), rip top (z 0.157) -> y 14.11
(base top spine); muzzle lands at -2.95 (base barrel/brace -1.6, cylinder nozzle -3.48).  The rip is long and low,
so everything below the frame line y 12.3 is stretched x1.1 downwards (model2world inverts it) to bring the grip
foot to the base magazine base (y 5.8).  Signature long raked heel plate kept but shortened from rip z 13.55 to 12.9
so it stays under the wrist.  Detail pass (W325 r2): chamfered receiver/housing/frame edges, real bore through a 4-piece muzzle face, bevelled
screen frame, raised housing sill/rear sight, frame rail steps and pins, proud grip side panels, heel plate rib.
ADS: housing top 14.2 (base spine 14.11), rear cap lowered to 13.8 behind z 11.3; sight dot is paint only.
Sight: front post z -1.6..-1.3 top 14.45 / rear ears z 8.7..9.3 top 14.62 on the
white sight housing = base W153 aim tip 14.44 / rear 14.64.
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


S = 40.0
PALETTE = 18
FLAT_TOL = 30
PALETTE_KEEP = [(110, 140, 220), (210, 60, 60), (80, 220, 90), (120, 130, 150)]
YS, K = 12.3, 1.1
T = 20


def _elements():
    E = []
    X0, X1 = 7.32, 8.68
    # ---- upper receiver (blue camo) with chamfered top edges and a 4-piece muzzle face around a real bore
    E += prism('recvF', X0, X1, 13.1, 14.1, -2.6, 1.7, .2, .1)
    E += prism('recvM', 7.36, 8.64, 13.15, 14.05, 1.7, 2.05, .2, .1)
    E += prism('recvR', X0, X1, 13.1, 14.1, 2.05, 7.0, .2, .1)
    E.append(B('recv_slot', (8.66, 13.5, 2.5), (8.7, 13.75, 4.3)))
    E.append(B('recv_slot_l', (7.3, 13.5, 2.5), (7.34, 13.75, 4.3)))
    E += bevel('recv_nose_top', X0, X1, 13.88, 14.1, -2.95, -2.6, .17)
    E.append(B('recv_nose_bot', (X0, 13.1, -2.95), (X1, 13.32, -2.6)))
    E.append(B('recv_nose_l', (X0, 13.32, -2.95), (7.72, 13.88, -2.6)))
    E.append(B('recv_nose_r', (8.28, 13.32, -2.95), (X1, 13.88, -2.6)))
    E.append(B('bore_stop', (7.72, 13.32, -2.6), (8.28, 13.88, -2.52)))
    E.append(B('port_frame', (8.66, 13.3, 3.0), (8.72, 13.9, 4.6)))
    # ---- white sight housing: bevelled box with a recessed black screen window, rear cap
    E += bevel('housing_front', 7.28, 8.72, 13.1, 14.2, 7.0, 7.3, .15)
    E += bevel('housing_back', 7.28, 8.72, 13.1, 14.2, 9.8, 11.3, .15)
    E += bevel('housing_top', 7.28, 8.72, 14.05, 14.2, 7.3, 9.8, .12)
    E.append(B('housing_sill', (7.28, 13.1, 7.3), (8.72, 13.25, 9.8)))
    E.append(B('screen', (7.36, 13.25, 7.3), (8.64, 14.05, 9.8)))
    E += bevel('rear_cap', 7.34, 8.66, 13.12, 13.8, 11.3, 11.62, .14)
    E.append(B('rear_bump', (7.4, 12.35, 10.9), (8.6, 13.12, 11.5)))
    E.append(B('rear_pin', (7.3, 12.55, 11.05), (8.7, 12.8, 11.3)))
    E.append(B('front_post', (7.92, 14.1, -1.6), (8.08, 14.45, -1.3)))
    E.append(B('front_post_base', (7.78, 14.05, -1.7), (8.22, 14.16, -1.2)))
    E.append(B('rear_sill', (7.57, 14.2, 8.7), (8.43, 14.33, 9.3)))
    E.append(B('rear_ear_l', (7.57, 14.2, 8.7), (7.67, 14.62, 9.3)))
    E.append(B('rear_ear_r', (8.33, 14.2, 8.7), (8.43, 14.62, 9.3)))
    # ---- dark frame: long lower rail (chamfered belly) to the muzzle, deeper body over the trigger and grip
    E += prism('frame_railF', 7.38, 8.62, 12.6, 13.12, -2.85, 0.4, 0, .14)
    E += prism('frame_railR', 7.38, 8.62, 12.6, 13.12, 0.4, 3.6, 0, .14)
    E += prism('frame_bodyF', 7.38, 8.62, 12.245, 13.12, 3.6, 7.4, 0, .14)
    E += prism('frame_bodyR', 7.38, 8.62, 12.245, 13.12, 7.4, 11.0, 0, .14)
    E.append(B('led_blue', (8.62, 12.7, 5.0), (8.66, 12.85, 5.4)))
    E.append(B('led_red', (8.62, 12.7, 5.6), (8.66, 12.85, 6.0)))
    E.append(B('rail_lip', (7.42, 12.5, -2.85), (8.58, 12.62, -2.5)))
    E.append(B('rail_step', (7.34, 12.7, -1.2), (8.66, 13.0, 2.9)))
    for i, z in enumerate((4.3, 9.6)):
        E.append(B(f'frame_pin_{i}', (7.33, 12.5, z), (8.67, 12.75, z + .25)))
    E.append(B('selector', (7.3, 12.55, 6.3), (8.7, 12.95, 6.85)))
    # ---- trigger guard (open) and white trigger
    E.append(B('guard_front', (7.8, 9.72, 3.6), (8.2, 12.25, 3.95)))
    E.append(B('guard_bottom', (7.8, 9.72, 3.75), (8.2, 9.98, 6.2)))
    E.append(B('guard_corner', (7.82, 9.6, 3.62), (8.18, 10.0, 4.02), R((8, 9.8, 3.82), x=45)))
    E.append(B('guard_rear', (7.8, 9.6, 6.27), (8.2, 10.56, 6.57), R((8, 10.08, 6.42), x=42)))
    E.append(B('trigger_upper', (7.88, 11.0, 4.95), (8.12, 12.35, 5.22), R((8, 11.4, 5.1), x=-8)))
    E.append(B('trigger_lower', (7.90, 10.2, 5.05), (8.10, 11.05, 5.32), R((8, 10.6, 5.2), x=-22)))
    # ---- raked grip: 17 deg core + 29 deg backstrap, proud side panels; magazine channel line is UV
    G = R((8, 10.0, 7.35), x=-17)
    E.append(B('grip_core', (7.4, 6.55, 6.35), (8.6, 12.9, 8.3), G))
    E.append(B('grip_back', (7.4, 7.1, 8.3), (8.6, 12.4, 8.95), G))
    for s, (xa, xb) in (('l', (7.36, 7.4)), ('r', (8.6, 8.64))):
        E.append(B(f'grip_panel_{s}', (xa, 8.1, 6.6), (xb, 11.6, 7.9), G))
    # long raked heel plate (rip signature) with a raised rib, body part behind the magazine foot
    HP = R((8, 7.645, 10.88), x=-21.3)
    E.append(B('heel_plate', (7.32, 7.42, 8.86), (8.68, 7.87, 12.9), HP))
    # ---- magazine (moving leaf): sloped foot + shaft inside the grip
    E.append(B('mag_foot', (7.32, 7.42, 6.95), (8.68, 7.87, 8.86), HP))
    E.append(B('mag_foot_lip', (7.4, 7.28, 7.1), (8.6, 7.42, 8.75), HP))
    E.append(B('mag_shaft', (7.5, 6.3, 7.2), (8.5, 11.4, 8.2), G))
    return E


def model2world(name, p):
    x, y, z = p
    if y < YS: y = YS - (YS - y) / K
    return (-(x - 8.0) / S, 0.086 + (z - 11.32) / S, 0.157 + (y - 14.11) / S)




def _faces_bore(e, fn):
    if fn not in ('east', 'west', 'up', 'down'): return False
    f, t = e['from'], e['to']; cx, cy = (f[0] + t[0]) / 2, (f[1] + t[1]) / 2
    nx, ny = {'east': (1, 0), 'west': (-1, 0), 'up': (0, 1), 'down': (0, -1)}[fn]
    return nx * (8.0 - cx) + ny * (13.6 - cy) > 0.05


def camo(e, fn, s, t, cols, scale=1.0, seed=0.0):
    """W30-style camo: a few large flat blobs (2-3 colours) from smooth model-space noise."""
    import kit as _k
    x, y, z = _k.face_point(e, fn, s, t)
    v = (math.sin(z * .9 / scale + seed) + math.sin((y * 1.3 + z * .4) / scale + 1.7 + seed)
         + math.sin((x * 1.1 - z * .7 + y * .5) / scale + 4.1 + seed))
    k = 0 if v < -.6 else (1 if v < .8 else 2)
    return tuple(cols[min(k, len(cols) - 1)]) + (255,)


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
        from PIL import Image,ImageFilter
        for key,view in _RIP_VIEWS.items():
            # Filter source dust/wear into coherent camo islands before the two-colour threshold.
            view.alb=Image.open(p/f'{key}_albedo.png').convert('RGBA').filter(ImageFilter.GaussianBlur(5)).load()
    p=_k.face_point(e,fn,s,t);normal=_k.rotate_vec(_k.NORMALS[fn],_k.rot_of(e));a=model2world(e['name'],p)
    b=model2world(e['name'],tuple(p[i]+normal[i]*.25 for i in range(3)))
    wn=[b[i]-a[i] for i in range(3)];axis=max(range(3),key=lambda i:abs(wn[i]));v=_RIP_VIEWS[('p' if wn[axis]>0 else 'n')+'xyz'[axis]]
    return v.sample(*v.project(a))

def _camo_chip(e,fn,s,t,light,threshold=125):
    if fn not in ('east','west','up'):return None
    c=_source(e,fn,s,t)
    if c is None or sum(c[:3])/3<threshold:return None
    return _mark(light,e,fn,s,t)
MATERIAL_WID='requiem_si2'
MATERIALS={
 'navy':dict(kind='paint',color=(36,49,73),detail=.8,amp=2),
 'ivory':dict(kind='paint',color=(209,205,198),detail=.4,amp=2),
 'frame':dict(kind='polymer',color=(38,42,44),detail=.45,amp=3),
 'grip':dict(kind='rubber',color=(27,31,33),detail=0,amp=5),
 'steel':dict(kind='steel',color=(113,123,127),detail=.3,amp=9),
 'darksteel':dict(kind='metal',color=(43,49,52),detail=.35,amp=6),
 'screen':dict(kind='lens',color=(18,34,47),detail=0,field=.18),
 'bore':dict(kind='dark',color=(12,16,20),detail=0),
 'magazine':dict(kind='steel',color=(57,64,68),detail=0,amp=7)}
def material(n,fn):
 if n=='screen':k='screen'
 elif n.startswith(('housing','rear_cap','trigger')):k='ivory'
 elif n.startswith(('recv_slot','bore','port_frame','front_post','rear_ear','rear_sill')):k='bore'
 elif n.startswith('recv'):k='navy'
 elif n.startswith('grip_panel'):k='grip'
 elif n.startswith(('rear_pin','frame_pin','selector')):k='steel'
 elif n.startswith(('rail','heel','guard')):k='darksteel'
 elif n=='mag_shaft':k='magazine'
 else:k='frame'
 return _mat(k,fn)
def special(e,fn,s,t):
 import kit as _k
 n=e['name'];x,y,z=_k.face_point(e,fn,s,t);side=fn in ('east','west')
 if n.startswith('recv') and not n.startswith('recv_slot'):
  c=_camo_chip(e,fn,s,t,(191,200,208),105)
  if c:return c
 if n.startswith('frame_body') and side:
  if text_hit(e,fn,s,t,'OMOLON',7.0 if fn=='west' else 9.45,13.0,.1,.07):return (103,126,147,255)
 if n=='led_blue':return (113,147,212,255)
 if n=='led_red':return (181,55,49,255)
 if n=='housing_top' and fn=='up' and 7.85<x<8.15 and 7.4<z<7.8:return (80,205,85,255)
 if n=='screen' and side and 8.75<z<9.45 and 13.40<y<13.45:return (88,136,153,255)
 return None

# Material pass 2: steel lower receiver/rail, painted outer sleeve only.
MATERIALS['navy'].update(color=(34,46,68),wear=False)
MATERIALS['ivory'].update(wear=False)
MATERIALS['frame'].update(color=(62,68,72),detail=.15)
MATERIALS['grip'].update(color=(19,23,26),amp=3)
MATERIALS['darksteel'].update(color=(78,88,96))
MATERIALS['receiver_steel']=dict(kind='metal',color=(79,91,103),detail=.25,amp=5)
MATERIALS['trigger_steel']=dict(kind='steel',color=(174,182,178),detail=0,amp=5)
_r2_material_before=material
_r2_special_before=special
def material(n,fn):
 if n.startswith(('frame_body','frame_rail','recvM','housing_sill','recv_slot')):return _mat('receiver_steel',fn)
 if n.startswith('trigger'):return _mat('trigger_steel',fn)
 if n.startswith(('rear_pin','frame_pin','selector','rail','guard')):return _mat('steel',fn)
 return _r2_material_before(n,fn)
def special(e,fn,s,t):
 if e['name'].startswith('recvM'):return None
 c=_r2_special_before(e,fn,s,t)
 if c is not None:return c
 if fn in ('east','west') and e['name'].startswith('frame_body'):
  import kit as _k
  x,y,z=_k.face_point(e,fn,s,t)
  # The OMOLON three-dot emblem is a tiny triangle beside the wordmark.
  if any(math.hypot(y-cy,z-cz)<.055 for cy,cz in [(12.76,10.02),(12.57,9.88),(12.57,10.16)]):return (20,33,43,255)
  if 7.0<z<9.45 and abs(y-12.48)<.025:return (37,54,68,255)
 return None
