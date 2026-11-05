"""W325 Vinegaroon-2si (rare sidearm, Lightweight) over base farewell (W184/W215 reload banks + W151 sight).

Rip -> model: 34 px/m, z = 7.83 + rip_y*34 (trigger z ~5.8, muzzle -5.3; base 5.0..5.4 / -4.87), y = 13.75 +
(rip_z - 0.145)*34 (slide rear top 13.95, mag floor 6.85 vs base heel 6.88).  VEIST knuckle frame kept as real open
structure: trigger opening, lower finger opening, white spine bar and the hooked front fin; suppressor as three
octagonal sections.  The rip has no iron sights: a front blade is clamped on the suppressor at the base W151 aim
point (z -1.15..-0.85, top 14.1) and rear ears are added on the slide (z 7.0..7.8, top 14.3).
Detail pass (W325 r2): ADS fix — slide top lowered to 13.45 (front block) / 13.6 (rear block) to sit on the base upper rail
(13.61); bevelled slide/frame edges, real ejection slot and rear window openings in the slide, suppressor end cap
with bore, knurled ring and band, frame pins, magazine perforated block with lip.
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


S = 34.0
PALETTE = 18
PALETTE_KEEP = [(40, 90, 110), (226, 220, 150)]
FLAT_TOL = 30
YEL, TEAL, BLK, DGRN, WHITE = (226, 220, 150), (80, 150, 146), (34, 36, 36), (44, 66, 64), (226, 222, 206)
T = 20


def octa(name, cy, W, z0, z1):
    """Octagon-ish cylinder along z centred (8, cy): vertical + horizontal cores and four 45 deg corner strips."""
    h, k = W / 2, W * .36
    out = [B(f'{name}_v', (8 - k, cy - h, z0), (8 + k, cy + h, z1)), B(f'{name}_h', (8 - h, cy - k, z0), (8 + h, cy + k, z1))]
    s = (h - k) * 1.25; d = (h + k) / 2 * .97
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        cx, cc = 8 + sx * d, cy + sy * d
        out.append(B(f'{name}_c{i}', (cx - s / 2, cc - s / 2, z0), (cx + s / 2, cc + s / 2, z1), R((cx, cc, (z0 + z1) / 2), z=45)))
    return out


def _elements():
    E = []
    # ---- slide, axis-aligned (no tilted slabs): front block (top 13.45) and rear block (top 13.6) stepped at a
    #      recessed seam groove; rear block has a real ejection slot and rear window through its side walls
    E.append(B('slide_floor', (7.4, 12.55, 1.7), (8.6, 12.95, 8.65)))
    E += prism('slide_top_F', 7.4, 8.6, 12.95, 13.45, 1.7, 4.15, .15, 0)
    E += prism('slide_top_S', 7.48, 8.52, 12.95, 13.35, 4.15, 4.3, .12, 0)
    E += prism('slide_top_R', 7.4, 8.6, 13.3, 13.6, 4.3, 8.65, .15, 0)
    for z0, z1, tag in ((4.3, 4.45, 'a'), (5.95, 7.0, 'b'), (8.25, 8.65, 'c')):
        E.append(B(f'wall_{tag}', (7.4, 12.95, z0), (8.6, 13.3, z1)))
    for z0, z1, tag in ((4.45, 5.95, 'slot'), (7.0, 8.25, 'win')):
        E.append(B(f'{tag}_sill', (7.4, 12.95, z0), (8.6, 13.05, z1)))
        E.append(B(f'{tag}_core', (7.6, 13.05, z0), (8.4, 13.3, z1)))
    E.append(B('rear_ledge', (7.5, 13.0, 8.65), (8.5, 13.2, 9.2)))
    E.append(B('rear_ear_l', (7.5, 13.6, 7.02), (7.73, 14.3, 7.76)))
    E.append(B('rear_ear_r', (8.27, 13.6, 7.02), (8.5, 14.3, 7.76)))
    E.append(B('front_blade_clamp', (7.7, 13.45, -1.25), (8.3, 13.62, -0.75)))
    E.append(B('front_blade', (7.92, 13.55, -1.15), (8.08, 14.1, -0.85)))
    # ---- suppressor: collar, knurled grip ring, long tube with band and end cap
    E += octa('sup_collar', 12.85, 1.1, 1.05, 1.7)
    E += octa('sup_knurl', 12.85, 1.46, .3, 1.05)
    E += octa('sup_tube', 12.85, 1.36, -4.95, .3)
    E += octa('sup_band', 12.85, 1.42, -2.2, -1.9)
    E += octa('sup_cap', 12.85, 1.3, -5.3, -4.95)
    E.append(B('sup_bore', (7.82, 12.67, -5.32), (8.18, 13.03, -5.3)))
    # ---- knuckle frame: teal band (bevelled), rear hump, bridge over the trigger opening, spine bar, bottom bar
    E += bevel('frame_band', 7.35, 8.65, 12.0, 12.56, 1.7, 8.75, .12, top=False, bottom=True)
    E.append(B('frame_tail', (7.4, 12.05, 8.7), (8.6, 12.55, 9.1)))
    E += bevel('frame_rear', 7.35, 8.65, 11.2, 12.05, 7.4, 8.8, .14, top=False, bottom=False)
    E.append(B('frame_guard_rear', (7.4, 10.0, 5.8), (8.6, 11.65, 6.65)))
    E.append(B('guard_bridge', (7.4, 11.6, 4.3), (8.6, 12.02, 5.85)))
    E.append(B('guard_bar', (7.45, 10.0, 4.3), (8.55, 10.38, 6.65)))
    E.append(B('spine', (7.55, 7.55, 4.3), (8.45, 10.38, 4.95)))
    E.append(B('bottom_bar', (7.5, 7.55, 4.9), (8.5, 7.9, 7.5)))
    for i, (y, z) in enumerate(((11.75, 7.8), (11.1, 6.2), (9.4, 3.3))):
        E.append(B(f'frame_pin_{i}', (7.3, y, z), (8.7, y + .22, z + .22)))
    # hooked front fin: core + front slab (30 deg) + concave lower slab (15 deg) + tip
    # hooked front fin as an axis-aligned step sequence (W30 style; no stacked rotated slabs): each step shares its
    # neighbours' faces exactly, the hook narrows forward toward the tip
    # Twelve edge-sharing steps follow the hooked silhouette; no overlapping rotated shell plates.
    fin_sections = ((4.3,7.9,12.0),(3.3,7.9,12.0),(2.6,8.1,12.0),(1.9,8.4,11.6),
                    (1.25,8.6,10.6),(.65,8.65,9.4),(.2,8.6,9.0))
    for i, (back, front) in enumerate(zip(fin_sections,fin_sections[1:])):
        for j in range(2):
            t0=j/2; t1=(j+1)/2; tm=(t0+t1)/2
            z1=back[0]+(front[0]-back[0])*t0; z0=back[0]+(front[0]-back[0])*t1
            y0=back[1]+(front[1]-back[1])*tm; y1=back[2]+(front[2]-back[2])*tm
            E.append(B(f'fin_{i}_{j}', (7.62,y0,z0),(8.38,y1,z1)))
    E.append(B('trigger', (7.9, 10.75, 5.62), (8.1, 11.6, 5.88), R((8, 11.2, 5.75), x=12)))
    E.append(B('trigger_tip', (7.92, 10.45, 5.6), (8.08, 10.8, 5.8), R((8, 10.62, 5.7), x=-25)))
    # ---- grip (16 deg) with proud side shells; stipple is UV
    G = R((8, 9.2, 7.6), x=-16)
    E.append(B('grip', (7.38, 7.9, 6.55), (8.62, 11.8, 8.95), G))
    for s, (xa, xb) in (('l', (7.34, 7.38)), ('r', (8.62, 8.66))):
        E.append(B(f'grip_shell_{s}', (xa, 8.4, 6.8), (xb, 11.3, 8.7), G))
    # ---- magazine (moving leaf): green block + white floor + lip + shaft inside the grip
    E.append(B('mag_block', (7.32, 7.0, 7.2), (8.68, 8.25, 9.0), G))
    E.append(B('mag_floor', (7.3, 6.82, 7.15), (8.7, 7.02, 9.05), G))
    E.append(B('mag_lip', (7.36, 8.25, 7.3), (8.64, 8.38, 8.9), G))
    E.append(B('mag_shaft', (7.55, 8.2, 7.5), (8.45, 11.0, 8.7), G))
    return E


def model2world(name, p):
    x, y, z = p
    if name.startswith(('slide_top', 'wall_', 'slot_', 'win_')):
        y += 0.3             # lowered slide samples the rip slide 0.3 higher
    return (-(x - 8.0) / S, (z - 7.83) / S, 0.145 + (y - 13.75) / S)




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
MATERIAL_WID='vinegaroon_2si'
MATERIALS={
 'yellow':dict(kind='paint',color=(190,184,108),detail=.20,amp=2),
 'teal':dict(kind='polymer',color=(30,51,46),detail=.65,amp=3),
 'steel':dict(kind='steel',color=(117,125,121),detail=.4,amp=9),
 'suppressor':dict(kind='metal',color=(31,34,35),detail=.6,amp=8),
 'fin':dict(kind='metal',color=(28,30,32),detail=.6,amp=6,rim=.08),
 'grip':dict(kind='rubber',color=(25,33,31),detail=.15,amp=5),
 'ivory':dict(kind='steel',color=(183,190,171),detail=.3,amp=8),
 'green':dict(kind='paint',color=(61,105,86),detail=.4,amp=2),
 'bore':dict(kind='dark',color=(12,16,17),detail=0)}
def material(n,fn):
 if n=='sup_bore' or n.startswith(('slot_core','win_core','front_blade','rear_ear')):k='bore'
 elif n.startswith(('sup_knurl','sup_collar','frame_pin')):k='steel'
 elif n.startswith('sup_'):k='suppressor'
 elif n.startswith(('slide','wall','slot_sill','win_sill','rear_ledge')):k='yellow'
 elif n.startswith('grip_shell'):k='grip'
 elif n.startswith(('fin','bottom')):k='fin'
 elif n.startswith(('mag_floor','mag_lip','spine','trigger')):k='ivory'
 elif n.startswith('mag_block'):k='green'
 elif n=='mag_shaft':k='steel'
 else:k='teal'
 m=_mat(k,fn)
 if n=='spine' or n.startswith(('mag_floor','mag_lip')):m['detail']=0
 if n.startswith('sup_knurl'):m.update(grain='cross',amp=7,detail=.2)
 return m
def special(e,fn,s,t):
 import kit as _k
 n=e['name'];x,y,z=_k.face_point(e,fn,s,t);side=fn in ('east','west')
 if n.startswith('sup_tube') and (-.9<z<.3 or -3.9<z<-3.5):return _mark((201,194,165),e,fn,s,t)
 if n.startswith(('slide_top','wall','slide_floor')) and side:
  if text_hit(e,fn,s,t,'VEIST',2.1 if fn=='west' else 4.0,13.25,.09,.08):return (40,90,103,255)
  if n=='slide_floor' and z<3.5 and 12.57<y<12.74 and int((z-y)*4)%3==0:return (64,120,115,255)
 if n=='mag_block' and side and holes_hit(e,fn,s,t,[(7.5+i*.45,7.3+j*.35) for i in range(4) for j in range(3)],.12):return (18,28,26,255)
 return None

# Material pass 2: VEIST yellow outer slide is paint, structural teal band and triggerguard are anodized metal.
MATERIALS['yellow'].update(wear=(155,166,140))
MATERIALS['green'].update(wear=False)
MATERIALS['teal'].update(color=(62,82,72),detail=.25)
MATERIALS['grip'].update(color=(19,28,23),amp=3)
MATERIALS['fin'].update(color=(43,53,48),amp=4)
MATERIALS['frame_metal']=dict(kind='metal',color=(70,104,89),detail=.2,amp=4)
_r2_material_before=material
_r2_special_before=special
def material(n,fn):
 if n.startswith(('frame_band','frame_rear','frame_guard','guard','slide_floor','bottom')):return _mat('frame_metal',fn)
 return _r2_material_before(n,fn)
def special(e,fn,s,t):
 c=_r2_special_before(e,fn,s,t)
 if c is not None:return c
 if fn in ('east','west') and e['name'].startswith('sup_knurl'):
  # Engraved knurl crosses remain one texel strokes on the silver ring.
  f,to=e['from'],e['to'];i=int(s*(to[2]-f[2])*T);j=int(t*(to[1]-f[1])*T)
  if (i+j)%7==0 or (i-j)%7==0:return (67,80,72,255)
 return None
