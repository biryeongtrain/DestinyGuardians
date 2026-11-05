"""W325 Furina-2mg (rare SMG, Lightweight) over base the_recluse (W208 reload bank + W153 sight).

The Recluse is built on this same VEIST lightweight SMG chassis, so the rip lands on the base almost 1:1.
Rip -> model: uniform 32 px/m, rip stock end (y 0.289) -> z 17.0, rip receiver top (z 0.145) -> y 12.8, rip x
(centre +0.0024 m) -> x 8.  Muzzle fork -3.1 (base -2.58), stock pad 16..17 (base 16.5..17.3), trigger z 7.0..7.4
(base 7.0..7.7).  The grip insert below the batwing is the moving magazine leaf, as in the base (base magazine
core centred z 8.8 / y 8.1); the slotted front fin stays body like the base foregrip.
Sight: the rip's thin antenna post sits on the aim line, so it is replaced by a hoop (z 7.36..7.54) framing the base
W153 aim tip (y 13.75); the optic housing top stays under the eye line.
Whip Scorpion-3mg shares this exact rip mesh and imports this geometry.
Style pass (W325 r3, W30 look): ADS fix — optic housing lowered onto the base optic profile (front <= 13.25, crown
13.28 over z 4.85..7.6, rear 13.04); receiver split into three machined segments with chamfers and side ribs, rail
teeth, chamfered shroud with vents and knurled collar, proud fin ribs, flat 2-3 colour camo + VEIST stock logo.
The sight ring elements are named sight_hoop_* (hollow ring around the aim tip, allowed above the profile).
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


S = 32.0
XC = 0.00245
T = 20
ATLAS = 1024  # 1P receiver drilled rail windows and tiny stock wordmark need 20 texels/px; cropped to used rows.
PALETTE = 18
FLAT_TOL = 30

# per-weapon colour scheme (Whip Scorpion overrides COLS after importing this module)
COLS = dict(camo=((40, 56, 92), (40, 56, 92), (150, 160, 180)), dark=(46, 48, 52), shroud=(222, 206, 206),
            rail=(150, 156, 160), window=(118, 124, 128), accent=(206, 210, 218), logo=(206, 210, 218), knurl=(176, 162, 162))
PALETTE_KEEP = []


def slope(name, p0, p1, thick, x0, x1, side='below', ext=(0.0, 0.0)):
    """Box whose top (side='below') or bottom (side='above') face lies on the (z,y) line p0 -> p1."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dz, dy); uz, uy = dz / L, dy / L
    ang = math.degrees(math.atan2(-uy, uz))
    nz, ny = (uy, -uz) if uz >= 0 else (-uy, uz)
    if ny > 0: nz, ny = -nz, -ny
    sg = 1 if side == 'below' else -1
    mz = (p0[0] + p1[0]) / 2 + uz * (ext[1] - ext[0]) / 2 + nz * sg * thick / 2
    my = (p0[1] + p1[1]) / 2 + uy * (ext[1] - ext[0]) / 2 + ny * sg * thick / 2
    h = (L + ext[0] + ext[1]) / 2
    return B(name, (x0, my - thick / 2, mz - h), (x1, my + thick / 2, mz + h), R((8, my, mz), x=ang))


def _elements():
    E = []
    # ---- shroud: square tube with chamfered edges, forked muzzle, knurled collar, band, top vents
    E += prism('shroud', 7.5, 8.5, 11.05, 12.1, -2.1, 4.2, .15)
    E += prism('fork_top', 7.5, 8.5, 11.72, 12.1, -3.07, -2.1, .15, 0)
    E += prism('fork_bottom', 7.5, 8.5, 11.05, 11.43, -3.07, -2.1, 0, .15)
    E.append(B('bore_stop', (7.6, 11.43, -2.1), (8.4, 11.72, -2.04)))
    E += prism('collar', 7.28, 8.72, 10.95, 12.25, 2.85, 3.65, .2)
    E.append(B('band', (7.44, 11.0, 1.72), (8.56, 12.15, 1.98)))
    for i in range(3):
        E.append(B(f'shroud_vent_{i}', (7.75, 12.06, -1.6 + i * .9), (8.25, 12.14, -1.2 + i * .9)))
    # ---- receiver in three machined segments (front, mid, rear) with side seams; stock top lip
    E += prism('recvF', 7.32, 8.68, 10.35, 12.6, 3.3, 7.6, .2, .15)
    E += prism('recvM', 7.36, 8.64, 10.4, 12.55, 7.6, 7.85, .2, .15)
    E += prism('recvR', 7.32, 8.68, 10.35, 12.6, 7.85, 12.9, .2, .15)
    E += prism('stock_lip', 7.38, 8.62, 10.36, 12.95, 12.9, 16.1, .22, 0)
    E.append(B('side_rib_l', (7.28, 11.55, 4.2), (7.32, 11.7, 12.6)))
    E.append(B('side_rib_r', (8.68, 11.55, 4.2), (8.72, 11.7, 12.6)))
    # ---- optic housing kept on the base optic profile (ADS): front ramp <= 13.25, crown <= 13.3, rear <= 13.11
    E += prism('housing', 7.3, 8.7, 12.6, 13.04, 4.45, 8.55, .2, 0)
    E += prism('housing_crown', 7.45, 8.55, 13.0, 13.28, 4.85, 7.6, .12, 0)
    E.append(slope('housing_front', (3.35, 12.6), (4.5, 13.0), .4, 7.34, 8.66, ext=(0, .05)))
    E.append(B('housing_lens', (7.6, 12.7, 4.4), (8.4, 12.95, 4.47)))
    E.append(B('rail', (7.42, 12.6, 8.55), (8.58, 12.7, 13.0)))
    for i in range(5):
        E.append(B(f'rail_tooth_{i}', (7.48, 12.68, 9.0 + i * .8), (8.52, 12.75, 9.35 + i * .8)))
    # ---- sight ring framing the base W153 aim tip (y 13.75) at the base hoop z
    E.append(B('sight_hoop_l', (7.55, 12.95, 7.36), (7.67, 14.5, 7.54)))
    E.append(B('sight_hoop_r', (8.33, 12.95, 7.36), (8.45, 14.5, 7.54)))
    E.append(B('sight_hoop_top', (7.55, 14.38, 7.36), (8.45, 14.5, 7.54)))
    # ---- stock: pad (chamfered), rear block, toe, web, lower brace
    E += prism('stock_pad', 7.5, 8.5, 7.15, 12.95, 16.0, 16.75, .2)
    E.append(B('stock_pad_round', (7.5, 7.5, 16.6), (8.5, 12.6, 17.02)))
    E += prism('stock_block', 7.38, 8.62, 7.75, 10.36, 12.85, 16.0, 0, .15)
    E.append(B('stock_toe', (7.38, 7.2, 14.6), (8.62, 7.8, 16.0)))
    E.append(slope('stock_web', (10.1, 7.95), (12.9, 9.7), 1.0, 7.4, 8.6))
    E.append(slope('stock_brace', (8.0, 5.86), (12.9, 7.66), 1.3, 7.42, 8.58, side='above'))
    E.append(B('heel_bar', (7.45, 5.85, 3.85), (8.55, 6.25, 8.4)))
    E.append(B('heel_screw', (7.4, 5.95, 4.3), (8.6, 6.15, 4.5)))
    # ---- grip upper (body) and trigger crescent
    E.append(B('grip_wing', (7.45, 9.0, 7.25), (8.55, 10.36, 9.4)))
    E.append(B('trigger_upper', (7.9, 9.75, 6.95), (8.1, 10.36, 7.2), R((8, 10.05, 7.07), x=-10)))
    E.append(B('trigger_lower', (7.92, 9.25, 7.0), (8.08, 9.8, 7.25), R((8, 9.5, 7.12), x=20)))
    # ---- slotted front fin (raked 21 deg) with real proud slot ribs, claw under the shroud
    F = R((8, 8.2, 4.37), x=-21)
    E.append(B('fin_spine', (7.22, 5.95, 4.95), (8.78, 10.45, 5.32), F))
    E.append(B('fin_front', (7.22, 5.95, 3.42), (8.78, 10.45, 3.68), F))
    E.append(B('fin_foot', (7.22, 5.95, 3.68), (8.78, 6.45, 4.95), F))
    E.append(B('fin_crown', (7.22, 10.1, 3.68), (8.78, 10.45, 4.95), F))
    for i in range(3):
        E.append(B(f'fin_rib_{i}', (7.22, 6.84 + i * 1.0875, 3.68), (8.78, 7.54 + i * 1.0875, 4.95), F))
    E.append(B('claw', (7.4, 10.3, 0.95), (8.6, 11.05, 3.3)))
    E.append(slope('claw_tip', (0.3, 10.5), (0.95, 10.32), .5, 7.45, 8.55, side='above', ext=(0, .05)))
    # ---- magazine (moving leaf) = grip insert below the wing, as the base magazine
    E.append(B('mag_core', (7.48, 6.25, 7.45), (8.52, 9.05, 9.3)))
    E.append(B('mag_grip_l', (7.44, 6.5, 7.6), (7.48, 8.8, 9.15)))
    E.append(B('mag_grip_r', (8.52, 6.5, 7.6), (8.56, 8.8, 9.15)))
    return E


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / S + XC, 0.289 + (z - 17.0) / S, 0.145 + (y - 12.8) / S)


def _c(c): return tuple(c) + (255,)




def camo(e, fn, s, t, cols, scale=1.0, seed=0.0):
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
MATERIAL_WID='furina_2mg'
MATERIALS={
 'receiver':dict(kind='paint',color=(36,51,79),detail=.75,amp=2),
 'shroud':dict(kind='steel',color=(205,191,190),detail=.45,amp=9),
 'rail':dict(kind='steel',color=(132,141,146),detail=.35,amp=8),
 'collar':dict(kind='steel',color=(153,141,141),detail=.6,amp=9),
 'polymer':dict(kind='polymer',color=(28,32,38),detail=.35,amp=4),
 'rubber':dict(kind='rubber',color=(23,26,31),detail=0,amp=5),
 'bore':dict(kind='dark',color=(12,17,20),detail=0),
 'lens':dict(kind='lens',color=(27,67,86),detail=0,field=.18)}
CAMO_LIGHT=(176,187,205)
WINDOW=(125,135,139)
LOGO=(202,210,217)
ACCENT=(182,193,201)
def material(n,fn):
 if n=='bore_stop' or n.startswith(('trigger','sight_hoop','shroud_vent')):k='bore'
 elif n=='housing_lens':k='lens'
 elif n.startswith(('shroud','fork','band')):k='shroud'
 elif n.startswith('collar'):k='collar'
 elif n.startswith(('rail','side_rib','heel_screw')):k='rail'
 elif n.startswith(('mag_grip','stock_pad')):k='rubber'
 elif n.startswith(('fin','grip','heel','mag_')):k='polymer'
 else:k='receiver'
 m=_mat(k,fn)
 if n in ('stock_web','stock_brace','housing_front'):m['detail']=0
 return m
def special(e,fn,s,t):
 import kit as _k
 n=e['name'];x,y,z=_k.face_point(e,fn,s,t);side=fn in ('east','west')
 if side and n.startswith('stock_lip') and text_hit(e,fn,s,t,'VEIST',13.15 if fn=='west' else 15.65,12.0,.12,.11):return LOGO+(255,)
 if side and n.startswith(('recvF','recvR')):
  if 11.95<y<12.45 and 5.2<z<11.4:
   iz=round((z-5.4)/.4);cz=5.4+iz*.4
   for cy in (12.08,12.31):
    d=math.hypot(z-cz,y-cy)
    if d<.065:return (23,28,31,255)
   return _mark(WINDOW,e,fn,s,t,'steel')
  if 11.25<y<11.3:return _mark(ACCENT,e,fn,s,t)
 if n.startswith(('housing','recv','stock_lip','stock_block','stock_toe','claw')):
  c=_camo_chip(e,fn,s,t,CAMO_LIGHT,105)
  if c:return c
 if n=='housing_lens' and s<.22 and t<.35:return (155,206,219,255)
 return None

# Material pass 2: outer camo side skins only; receiver rim, spine, claws, braces and controls expose steel.
MATERIALS['receiver'].update(color=(30,43,69),wear=False)
MATERIALS['polymer'].update(color=(66,73,81),detail=.15,amp=3)
MATERIALS['rubber'].update(color=(18,22,26),amp=3)
MATERIALS['structure']=dict(kind='metal',color=(89,105,118),detail=.15,amp=5)
MATERIALS['control']=dict(kind='steel',color=(131,145,152),detail=0,amp=5)
_r2_material_before=material
_r2_special_before=special
def material(n,fn):
 if n.startswith(('trigger','heel','sight_hoop')):return _mat('control',fn)
 if n.startswith(('stock_web','stock_brace','claw','housing_front','recvM')):return _mat('structure',fn)
 if n.startswith(('recv','stock_lip','stock_block','stock_toe','housing')) and n!='housing_lens':
  if fn not in ('east','west') or n.endswith(('_t','_b','_ctl','_ctr','_cbl','_cbr')):return _mat('structure',fn)
 return _r2_material_before(n,fn)
def special(e,fn,s,t):
 import kit as _k
 n=e['name'];x,y,z=_k.face_point(e,fn,s,t)
 if fn in ('east','west') and n.startswith(('recvF','recvR')) and 10.58<y<10.78:
  # A paired line of tiny retaining rivets follows the original lower receiver plate.
  if any(math.hypot(z-cz,y-10.68)<.045 for cz in (4.25,6.9,8.35,11.75)):return (177,188,193,255)
 if n.startswith(('stock_web','stock_brace','claw','housing_front','recvM')) or (n.startswith(('recv','stock_lip','stock_block','housing')) and (fn not in ('east','west') or n.endswith(('_t','_b','_ctl','_ctr','_cbl','_cbr')))):
  return None  # do not place the coat/camo onto newly exposed structural metal
 return _r2_special_before(e,fn,s,t)
