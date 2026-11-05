"""W325 Psi Cirrus II (rare, Rapid-Fire pulse rifle; Veist-style bullpup) over claws_of_the_wolf.

Rip measured in nx / pz / ny views.  Uniform map 25.76 px/m (rip length 0.986 m), width x1.1.  Authoring frame:
rip butt (Y 0.3084) -> z 16.8, rip Z 0.12 -> y 10; the whole model is then shifted DZ = -0.6 px so the rip's
enclosed grip/trigger land on the base grip (rip hand sits ~0.8 px further back than claws_of_the_wolf).
Result: muzzle -8.95, butt pad 16.0 (base -8.61 / 16.8), magazine z 9.95-12.15 (base 9.7-12.9).
Sight: the rip reflex box sat over the canisters (z 6.3-8.9); it is moved 1.8 px forward (z 3.9-6.5, inside the base
optic window z 4.0-7.0) and kept as a hollow box (elements sight_*) with its aperture centred on x 8 / y 12.48.

W325 detail pass: chamfered receiver/stock/shroud edges, layered top rail, octagonal canisters, ribbed grip and
magazine, clean flat paint where the projection smears.  ADS: everything behind z 0.9 outside the optic window is held
under the claws_of_the_wolf top profile (receiver 11.70, stock 11.66, canisters lowered 0.13); the rip's taller
receiver/stock are squeezed vertically above y 10.6 in the texture map (YK) so their camo texture still reads.
"""
import math
from w325_5_lib import box, bx, bar, vbar, ring, chbox, Uniform, along, bar_on, Painter

M = Uniform(25.76, 16.8, 0.3084, 10.0, 0.12, 0.0, kx=1.1)
DZ = -0.6
SIGHT_DZ = -1.8
NO_OVERLAY = False
T = 15
YP = 10.6
YK = {'rcv_upper': 1.318, 'stk_top': 1.46, 'stk_strut': 1.5, 'butt_': 1.2, 'rcv_tube': 1.25}
CAN_DY = -0.13
RT, ST = 11.70, 11.66

RV, LW = .78, .85


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    z -= DZ
    if name.startswith('sight_'):
        z -= SIGHT_DZ
    if name.startswith('can'):
        y -= CAN_DY
    for pre, k in YK.items():
        if name.startswith(pre) and y > YP:
            y = YP + (y - YP) * k
    return M((x, y, z))


def front():
    S = []
    S += chbox('muzzle_tip', .27, 10.02, 10.56, -8.35, -8.1, c=.08, bottom=True)
    S.append(bx('muzzle_slot_top', .27, 10.37, 10.56, -8.1, -7.35))
    S.append(bx('muzzle_slot_bottom', .27, 10.02, 10.2, -8.1, -7.35))
    S += chbox('muzzle_rod', .27, 10.02, 10.56, -7.35, -5.85, c=.08, bottom=True)
    S += chbox('muzzle_collar', .34, 9.94, 10.63, -5.85, -5.3, c=.1, bottom=True)
    for k, z in enumerate((-5.75, -5.55)):
        S.append(bx(f'muzzle_knurl_{k}', .37, 9.91, 10.66, z, z + .1))
    S += chbox('front_cap', .72, 9.45, 11.55, -5.15, -4.4, c=.16)
    S.append(bx('fsight_post', .05, 11.55, 12.22, -5.03, -4.91))
    S.append(bx('fsight_base', .18, 11.55, 11.7, -5.1, -4.85))
    S += chbox('shroud', RV, 10.55, 11.8, -4.4, 1.7, c=.2)
    S.append(box('shroud_port_r', (8 + RV - .06, 10.95, -3.3), (8 + RV + .02, 11.25, -1.7)))
    S.append(box('shroud_port_l', (8 - RV - .02, 10.95, -3.3), (8 - RV + .06, 11.25, -1.7)))
    S.append(bx('bracket_top', .5, 11.95, 12.07, -1.45, 0.05))
    S.append(bx('bracket_leg_f', .5, 11.8, 11.95, -1.45, -1.28))
    S.append(bx('bracket_leg_r', .5, 11.8, 11.95, -0.12, 0.05))
    S.append(bx('band_upper', RV - .08, 10.05, 10.55, -4.4, 3.8))
    S.append(bx('band_lower', LW - .05, 9.45, 9.95, -4.4, 3.8))
    S.append(bx('band_gap_core', RV - .25, 9.95, 10.05, -3.7, 0.25))
    S.append(bx('band_gap_f', LW - .05, 9.95, 10.05, -4.4, -3.7))
    S.append(bx('band_gap_r', LW - .05, 9.95, 10.05, 0.25, 3.8))
    S.append(box('band_pin', (8 + RV - .1, 10.2, 1.9), (8 + RV + .02, 10.42, 2.2)))
    # white C-frame lower handguard with a recessed dark panel, chamfered belly
    S.append(bar('hg_nose', LW, (-4.7, 9.45), (-3.5, 7.92), .5, side='centre'))
    S += chbox('hg_bottom', LW, 7.9, 8.42, -3.65, 1.2, c=.14, top=False, bottom=True)
    S.append(bx('hg_post', LW, 8.42, 9.45, 0.3, 1.2))
    S.append(bx('hg_panel', LW - .2, 8.42, 9.45, -3.75, 0.3))
    for k, z in enumerate((-2.8, -1.4)):
        S.append(bx(f'hg_screw_{k}', LW - .12, 8.8, 9.05, z, z + .25))
    return S


def middle():
    S = []
    S += chbox('rcv_upper', RV, 10.55, RT, 1.7, 9.6, c=.2)
    S.append(bx('rcv_rail', .34, RT, RT + .1, 4.6, 7.4))
    for k in range(4):
        z = 4.75 + k * .65
        S.append(bx(f'rcv_rail_tooth_{k}', .38, RT + .1, RT + .2, z, z + .3))
    S.append(box('rcv_bolt_r', (8 + RV - .02, 10.75, 3.0), (8 + RV + .1, 11.05, 4.2)))
    S += chbox('rcv_lower', LW - .03, 8.85, 10.55, 3.8, 9.6, c=.0001, top=False)[:1]
    S.append(bx('lower_front', LW - .03, 8.5, 9.45, 1.2, 3.8))
    S.append(bx('lower_mid', LW - .03, 8.5, 8.85, 3.8, 5.6))
    S.append(box('rcv_selector', (8 + LW - .03, 9.6, 6.2), (8 + LW + .08, 9.9, 6.9)))
    # three side canisters (cylinders across x): octagon = two crossed boxes + 45 deg rim slabs read as discs
    for k, c in enumerate((6.5, 7.6, 8.72)):
        S.append(box(f'can{k}_a', (8 - 1.22, 10.93 + CAN_DY, c - .4), (8 + 1.22, 11.83 + CAN_DY, c + .4)))
        S.append(box(f'can{k}_b', (8 - 1.22, 11.0 + CAN_DY, c - .47), (8 + 1.22, 11.76 + CAN_DY, c + .47)))
        S.append(box(f'can{k}_cap', (8 - 1.3, 11.08 + CAN_DY, c - .32), (8 + 1.3, 11.68 + CAN_DY, c + .32)))
    S.append(bx('rcv_tube', .6, 11.05, RT - .02, 9.6, 11.9))
    # hand loop: diagonal bar from the lower front to the grip foot, enclosed trigger
    LB = ((1.7, 8.7), (8.35, 6.2))            # loop bar axis: web and rim ride on it (no 1-2 deg crossings)
    S.append(bar('loop_bar', LW - .1, *LB, .68))
    S.append(bar_on('loop_web', LW - .06, *LB, 1.0, 0.0, .62, off=.84))
    S.append(bar_on('loop_rim', LW - .02, *LB, .16, .08, .92, off=-.25))
    S.append(bx('trigger_blade', .07, 8.2, 8.85, 6.95, 7.1))
    S.append(bar('trigger_hook', .07, (7.0, 8.25), (7.32, 7.95), .14))
    G = ((8.85, 8.9), (9.3, 6.2))
    S.append(vbar('grip_main', .58, *G, 1.65))
    S.append(along('grip_panel', .66, *G, 1.2, .13, .85, off=-.05))
    S.append(along('grip_foot', .64, *G, 2.0, .92, 1.04, off=.1))
    # reflex box moved forward 1.8 px (part transform): hollow, aperture centred on y 12.48
    S += ring('sight_box_', 12.48, 6.3, 8.9, .48, .1, corners=False)
    S.append(bx('sight_cap', .3, 12.96, 13.05, 6.6, 8.6))
    S.append(bx('sight_foot', .34, RT + .2, 12.0, 6.6, 8.6))
    S.append(box('sight_knob', (8.48, 12.3, 7.3), (8.62, 12.66, 7.8)))
    return S


def stock():
    S = []
    S.append(bar('stk_strut', LW - .05, (9.75, 10.6), (11.7, ST - .02), .55, side='below'))
    S += chbox('stk_top', LW - .05, 11.0, ST, 11.35, 15.95, c=.2)
    S.append(bx('stk_mid', LW - .05, 9.3, 11.0, 9.6, 14.2))
    S.append(bx('stk_hole_top', LW - .05, 10.3, 11.0, 14.2, 15.95))
    S.append(bx('stk_hole_rim', LW - .17, 10.22, 10.3, 14.2, 15.5))
    S.append(bx('stk_post', LW - .05, 7.75, 10.3, 15.5, 15.95))
    S.append(bx('stk_hole_floor', LW - .05, 7.6, 8.9, 14.2, 15.5))
    S += chbox('stk_lower', LW - .05, 7.6, 9.3, 12.8, 14.2, c=.16, top=False, bottom=True)
    S.append(bx('stk_magwell', LW - .05, 8.55, 9.3, 9.6, 12.8))
    S.append(bar('stk_flap', LW + .02, (10.65, 7.95), (12.35, 9.05), .35))   # 33 deg flap, proud of the magwell sides
    S += chbox('butt_pad', LW, 8.05, ST - .05, 15.95, 16.6, c=.18, bottom=True)
    S.append(bx('butt_cap_bottom', LW - .1, 7.8, 8.05, 15.95, 16.4))
    for k, y in enumerate((8.9, 9.8, 10.7)):
        S.append(bx(f'butt_groove_{k}', LW + .02, y, y + .12, 16.15, 16.45))
    return S


def magazine():
    S = [bx('mag_body', .46, 5.45, 8.7, 10.55, 12.75),
         bx('mag_base', .5, 5.22, 5.45, 10.65, 12.55)]
    for k, y in enumerate((6.1, 6.9, 7.7)):
        S.append(bx(f'mag_rib_{k}', .52, y, y + .3, 10.75, 12.55))
    return S


def _shift(e):
    e['from'][2] += DZ; e['to'][2] += DZ
    if 'rotation' in e: e['rotation']['origin'][2] += DZ
    if e['name'].startswith('sight_'):
        e['from'][2] += SIGHT_DZ; e['to'][2] += SIGHT_DZ
        if 'rotation' in e: e['rotation']['origin'][2] += SIGHT_DZ
    return e


def elements():
    return [_shift(e) for e in front() + middle() + stock() + magazine()]


def _extra(e, fn, s, t):
    n = e['name']
    if n.startswith('sight_box_') and fn in ('north', 'south'):
        return (64, 66, 62, 255) if min(s, 1 - s, t, 1 - t) < .25 else (40, 42, 40, 255)
    if n.startswith('rcv_rail') or n.startswith('shroud_port'):
        return (38, 40, 40, 255)
    if n.startswith('butt_groove'):
        return (34, 36, 36, 255)
    return None


WHITE, OLIVE, DARKG, BLACK = (214, 208, 196), (96, 112, 64), (150, 146, 138), (54, 56, 54)
PALETTE_KEEP = [WHITE, OLIVE, DARKG, BLACK]
CAMO = ('front_cap', 'shroud', 'rcv_upper', 'stk_top', 'stk_mid', 'stk_hole', 'stk_post', 'stk_flap', 'hg_nose',
        'hg_bottom', 'hg_post', 'can', 'butt_cap', 'stk_strut', 'sight_cap', 'sight_box', 'stk_lower')
CELL = 0.5                                   # model px per camo cell -> big flat blobs


def _camo(e, fn, s, t):
    import kit
    o, u, v = kit.face_frame(e, fn); lu = math.dist((0, 0, 0), u) or 1; lv = math.dist((0, 0, 0), v) or 1
    cs = (math.floor(s * lu / CELL) + .5) * CELL / lu; ct = (math.floor(t * lv / CELL) + .5) * CELL / lv
    key = (e['name'], fn, round(cs, 4), round(ct, 4))
    if key in _CAMO_MEMO: return _CAMO_MEMO[key]
    view = special._view(e, fn); acc = []
    for ds in (-.3, 0, .3):
        for dt in (-.3, 0, .3):
            ss = min(1, max(0, cs + ds * CELL / lu)); tt = min(1, max(0, ct + dt * CELL / lv))
            wp = model2world(e['name'], kit.face_point(e, fn, ss, tt)); x, y = view.project(wp); c = view.sample(x, y)
            if c is not None: acc.append(c)
    if not acc: r = WHITE
    else:
        votes = {}
        for c in acc:
            l = .299 * c[0] + .587 * c[1] + .114 * c[2]
            k = OLIVE if c[1] > c[0] + 6 and c[1] > c[2] + 10 else WHITE if l > 105 else BLACK
            votes[k] = votes.get(k, 0) + 1
        n = len(acc)
        r = OLIVE if votes.get(OLIVE, 0) >= .45 * n else BLACK if votes.get(BLACK, 0) > .6 * n else WHITE
    _CAMO_MEMO[key] = r + (255,)
    return _CAMO_MEMO[key]


_CAMO_MEMO = {}


def _extra2(e, fn, s, t):
    r = _extra(e, fn, s, t)
    if r is not None: return r
    if e['name'].startswith(CAMO): return _camo(e, fn, s, t)
    return None


special = Painter(__file__, model2world, extra=_extra2,
                  flat={'grip_panel': (50, 52, 50), 'mag_rib': (56, 58, 56), 'loop_rim': (60, 62, 60)})


# W325 style pass: Dead Man Walking break-up of long slabs + Minecraft pixel palette (kit STYLE 'pixel')
from w325_5_lib import machined as _machined
_elements_raw = elements


def elements():
    return _machined(_elements_raw())


PALETTE = 16
FLAT_TOL = 22


# W325 cleanup pass: no coplanar overlapping faces (z-fight slivers)
from w325_5_lib import dezfight as _dezfight
_elements_unclean = elements


def elements():
    return _dezfight(_elements_unclean())


# Pixel glyphs retained solely for source manufacturer decals.
import kit as _kit
_FONT = {
 'O': ('111','101','101','101','111'), 'M': ('10001','11011','10101','10101','10001'),
 'L': ('100','100','100','100','111'), 'N': ('1001','1101','1011','1001','1001'),
 'S': ('111','100','111','001','111'), 'U': ('101','101','101','101','111'),
 'R': ('110','101','110','101','101')}

def _lettering(text, s, t, rect):
    a,b,c,d=rect
    if not a <= s < c or not b <= t < d: return False
    glyphs=[_FONT[x] for x in text]
    width=sum(len(g[0])+1 for g in glyphs)-1
    x=int((s-a)/(c-a)*width); y=min(4,int((t-b)/(d-b)*5))
    for g in glyphs:
        if x < len(g[0]): return g[y][x]=='1'
        x-=len(g[0])+1
        if x < 0: return False
    return False

# Remove shared world-plane slivers even when rotations have different origins.
from identity_geometry import clean as _identity_clean
_identity_unclean = elements
def elements():
    return _identity_clean(_identity_unclean())


# W325 material pass: original relief over explicitly assigned W123-like surfaces.
STYLE = 'material'
T = 20
ATLAS = 1024  # scratch atlas; identity_pack.py repacks losslessly after the material bake

def grade(rgb): return tuple(int(max(0,min(255,c))) for c in rgb)
_material_source = Painter(__file__, model2world)
_material_geometry = {e['name']:e for e in elements()}
_material_quality = {}

def _source_sample(e, face, s, t):
    view=_material_source._view(e,face)
    wp=model2world(e['name'],_kit.face_point(e,face,s,t)); x,y=view.project(wp)
    depth=view.depth_at(x,y)
    if depth is None or depth>sum(wp[k]*view.d[k] for k in range(3))+_material_source.occ: return None
    return view.sample(x,y)

def _finish_material(key,name,face):
    # Thin bevels, end caps and poorly covered projections receive material grain without projected smears.
    m=MATERIALS[key]
    if m['kind'] in ('lens','glow','dark'): return key
    cache=(name,face)
    if cache not in _material_quality:
        e=_material_geometry[name]
        valid=sum(_source_sample(e,face,(i+.5)/5,(j+.5)/5) is not None for i in range(5) for j in range(5))
        _material_quality[cache]=valid/25
    if _material_quality[cache]<.6 or face in ('north','south') or '_topch_' in name or '_botch_' in name:
        return dict(m,detail=0)
    return key
MATERIALS = {
 'ivory_enamel':dict(kind='paint',color=(186,192,173),detail=.7,amp=3),
 'olive_enamel':dict(kind='paint',color=(69,84,43),detail=.7,amp=3),
 'green_polymer':dict(kind='polymer',color=(40,48,41),detail=.65,amp=5),
 'gunmetal':dict(kind='metal',color=(62,69,60),detail=.6,amp=8),
 'steel':dict(kind='steel',color=(160,176,160),detail=.45,amp=10),
 'rubber':dict(kind='rubber',color=(27,32,27),detail=.35,amp=6),
 'recess':dict(kind='dark',color=(18,25,20),detail=0),
 'optic_rim':dict(kind='lens',color=(55,105,77),detail=0)}
_CAMO_PARTS=('front_cap','shroud','rcv_upper','stk_top','stk_mid','stk_hole','stk_post','stk_flap','hg_nose','hg_bottom','hg_post','stk_strut','stk_lower','sight_cap','sight_box','can')
def material(name,face):
    key='gunmetal'
    if name.startswith(_CAMO_PARTS): key='ivory_enamel'
    if name.startswith(('rcv_lower','lower_','loop','hg_panel','grip_main','grip_foot','mag_body')): key='green_polymer'
    if name.startswith(('muzzle','band_pin','hg_screw','rcv_bolt','rcv_selector','stk_flap','trigger','bracket','can')): key='steel'
    if name.startswith(('butt','grip_panel')): key='rubber'
    if name.startswith(('shroud_port','band_gap','rcv_rail')): key='recess'
    if name.startswith('sight_box') and face in ('north','south'): key='optic_rim'
    return _finish_material(key,name,face)
def special(e,fn,s,t):
    n=e['name']; x,y,z=_kit.face_point(e,fn,s,t); side=fn in ('east','west')
    if n.startswith(_CAMO_PARTS) and not n.startswith(('shroud_port','can','stk_flap')):
        c=_source_sample(e,fn,s,t)
        if c is not None and c[1]>c[0]+5 and c[1]>c[2]+10:
            l=.299*c[0]+.587*c[1]+.114*c[2]; d=max(-15,min(18,(l-70)*.3)); grain=((int(s*83)*17+int(t*49)*29)%7)-3
            return tuple(int(v+d+grain) for v in (69,84,43))+(255,)
    if n.startswith('can') and n.endswith('_cap') and side:
        r=((s-.5)**2+(t-.5)**2)**.5
        if .35<r<.44: return (209,222,199,255)
        if .29<r<.34: return (28,46,28,255)
        if r<.28 and (abs(s-.5)<.035 or abs(t-.5)<.035): return (93,128,59,255)
    if n.startswith('muzzle_tip') and fn=='north' and abs(x-8)<.16 and abs(y-10.29)<.16: return (13,20,15,255)
    return None

# W325 material R2: exposed mechanisms, legible material contrast, restrained hand-painted motifs.
_material_r1 = material
_special_r1 = special

def _r2_pixels(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    w=max(1,round(sum(c*c for c in u)**.5*T)); h=max(1,round(sum(c*c for c in v)**.5*T))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

FINAL_ATLAS = (1024, 512)
MATERIALS['green_polymer']['color'] = (50, 59, 49)
MATERIALS['rubber']['color'] = (18, 23, 19)
MATERIALS['gunmetal']['color'] = (80, 89, 79)

def material(name,face):
    original=_material_r1(name,face)
    m=MATERIALS[original] if isinstance(original,str) else original
    if m['kind'] in ('dark','lens','glow'): return original
    if name.startswith(('can0_cap', 'can1_cap', 'can2_cap')): return _finish_material('olive_enamel',name,face)
    if name.startswith(('rcv_lower', 'lower_', 'band_upper', 'band_lower', 'rcv_rail', 'loop')): return _finish_material('gunmetal',name,face)
    return original
MATERIALS['ivory_enamel'].update(wear=False,detail=.25)
MATERIALS['olive_enamel'].update(wear=False,detail=.25)

_r2_camo_cache={}
def _r2_camo(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    cols=max(1,round(sum(c*c for c in u)**.5/.7)); rows=max(1,round(sum(c*c for c in v)**.5/.7))
    col=min(cols-1,int(s*cols)); row=min(rows-1,int(t*rows)); key=(e['name'],fn,col,row)
    if key not in _r2_camo_cache:
        samples=[_source_sample(e,fn,(col+(a+.5)/3)/cols,(row+(b+.5)/3)/rows) for a in range(3) for b in range(3)]
        samples=[c for c in samples if c is not None]
        votes=sum(c[1]>c[0]+5 and c[1]>c[2]+10 for c in samples)
        _r2_camo_cache[key]=(69, 84, 43)+(255,) if samples and votes/len(samples)>=.4 else None
    return _r2_camo_cache[key]

def special(e,fn,s,t):
    n=e['name']; side=fn in ('east','west'); i,j,w,h=_r2_pixels(e,fn,s,t)
    if n.startswith('can') and n.endswith('_cap') and side:
        if j==3 and i%6==0 and 3<i<w-3: return (219,227,204,255)
    if n.startswith(_CAMO_PARTS) and not n.startswith(('shroud_port','can','stk_flap')):
        if n.startswith('sight_box') and fn in ('north','south'): return None
        return _r2_camo(e,fn,s,t)
    return _special_r1(e,fn,s,t)
