"""W325 Encore-25 (rare, Adaptive pulse rifle; bullpup with a full-length trigger guard and a raked banded magazine)
over bygones.

Rip measured in nx / pz / ny views.  Uniform map 30 px/m (rip 0.824 m), authoring frame rip butt (Y 0.322) -> z 16.8,
rip Z 0.12 -> y 10; whole model shifted DZ = +0.4 so the grip (top z 7.0-8.7) sits on bygones' grip (~7.0-9.0) and the
magazine top (z 10.3-12.9) overlaps bygones' moving magazine (10.7-13.4).  Muzzle -7.25 (base -8.54).

W325 detail/style pass (Dead Man Walking break-up + Minecraft palette): the red top cover is lowered from 12.42 to the
bygones roof (top 12.0, hump 12.08) and its rip texture squeezed above y 11.4 (YK) so the cover still reads red with
its rail slots; the rip's tall rear ear (13.3, z 9.25) is replaced by an open two-post notch sight (elements sight_*)
inside bygones' optic window (placed z 6.0-6.3, posts to 12.95 either side of the aim point x 8 / y 12.74; base optic
tube reaches 13.4 there).  Big slabs split into machined segments with chamfered edges; perforated shroud with end
rings, guard as separate bars, ribbed magazine, stepped butt pad.  W148 overlay dot kept.
"""
from w325_5_lib import box, bx, bar, vbar, chbox, machined, Uniform, along, Painter

M = Uniform(30.0, 16.8, 0.322, 10.0, 0.12, 0.0)
DZ = 0.4
NO_OVERLAY = False
B = .95


def is_magazine(n): return n.startswith('mag_')


YP, YK = 11.2, {'cover': 1.4}


def model2world(name, p):
    x, y, z = p
    if name.startswith('cover') and y > YP:
        y = YP + (y - YP) * YK['cover']
    return M((x, y, z - DZ))


def front():
    S = []
    # perforated shroud: body + end rings, bore cap
    S += [bx('shroud_top', .45, 10.23, 10.4, -7.45, -3.65),
          bx('shroud_bottom', .45, 9.2, 9.37, -7.45, -3.65),
          bx('shroud_spine', .45, 9.73, 9.87, -7.45, -3.65),
          bx('shroud_inner_barrel', .16, 9.58, 10.02, -7.45, -3.65)]
    for i in range(6):
        z = -7.45 + i * .73
        S.append(bx(f'shroud_bridge_{i}', .45, 9.37, 10.23, z, min(z + .15, -3.65)))
    S.append(bx('shroud_ring_f', .5, 9.15, 10.45, -7.65, -7.45))
    S.append(bx('shroud_ring_r', .5, 9.15, 10.45, -3.65, -3.45))
    S.append(bx('shroud_bore', .22, 9.52, 10.08, -7.7, -7.65))
    S.append(bx('front_post', .12, 11.6, 12.0, -3.78, -3.56))
    S.append(bx('front_post_tip', .12, 11.9, 12.05, -3.88, -3.6))
    S += chbox('body_front', B, 8.4, 11.6, -3.45, -1.8, c=.24, bottom=True)
    S += chbox('body', B, 8.25, 11.4, -1.8, 4.0, c=.0001, top=False)[:1]
    S += chbox('body_belly', B, 8.25, 8.65, -1.8, 3.6, c=.16, top=False, bottom=True)[1:]
    S.append(box('body_slot_r', (8 + B - .03, 10.25, 1.2), (8 + B + .02, 10.45, 3.7)))
    S.append(box('body_slot_l', (8 - B - .02, 10.25, 1.2), (8 - B + .03, 10.45, 3.7)))
    S.append(box('body_band_r', (8 + B - .02, 10.9, -1.75), (8 + B + .05, 11.05, 8.4)))
    S.append(box('body_band_l', (8 - B - .05, 10.9, -1.75), (8 - B + .02, 11.05, 8.4)))
    # red top cover, lowered to the bygones roof; rail with teeth, low hump
    S += chbox('cover', .66, 11.2, 12.0, -1.8, 9.1, c=.18)
    for k in range(4):
        z = 4.75 + k * .45
        S.append(bx(f'cover_rail_tooth_{k}', .3, 12.0, 12.08, z, z + .22))
    S.append(bx('cover_hump', .56, 11.9, 12.08, 7.55, 9.1))
    S.append(bar('cover_tail', .56, (9.1, 12.08), (11.4, 11.6), .5, side='below'))
    # open two-post notch sight on the rail (inside bygones' optic window)
    S.append(bx('sight_base', .42, 12.08, 12.2, 5.5, 6.0))
    S.append(box('sight_post_l', (7.55, 12.2, 5.6), (7.7, 12.95, 5.9)))
    S.append(box('sight_post_r', (8.3, 12.2, 5.6), (8.45, 12.95, 5.9)))
    return S


def middle():
    S = []
    S += chbox('body_mid', B, 8.9, 11.4, 4.0, 8.5, c=.0001, top=False)[:1]
    # beige side plates on the rear receiver (proud, both sides)
    S.append(box('plate_r', (8 + B, 9.45, 8.75), (8 + B + .06, 10.75, 11.9)))
    S.append(box('plate_l', (8 - B - .06, 9.45, 8.75), (8 - B, 10.75, 11.9)))
    S.append(box('plate_screw_r', (8 + B + .06, 10.0, 10.2), (8 + B + .1, 10.2, 10.4)))
    S.append(box('selector_r', (8 + B, 9.6, 6.4), (8 + B + .08, 9.85, 7.0)))
    S.append(bar('guard_front', .32, (3.55, 8.95), (4.45, 5.75), .45))
    S.append(bx('guard_bottom', .32, 5.4, 5.75, 4.2, 6.9))
    S.append(bx('trigger_blade', .07, 7.8, 8.9, 5.45, 5.65))
    S.append(bar('trigger_hook', .07, (5.55, 7.85), (5.85, 7.62), .14))
    G = ((7.4, 9.25), (7.75, 5.75))
    S.append(vbar('grip_main', .44, *G, 1.65))
    S.append(along('grip_panel', .52, *G, 1.25, .2, .87, off=-.04))
    S.append(along('grip_foot', .52, *G, 1.75, .94, 1.04, off=.05))
    S += chbox('rear_lower', B + .03, 8.6, 11.15, 8.5, 13.0, c=.2, bottom=True)
    S.append(bx('rear_cap', B - .1, 8.8, 10.9, 13.0, 13.15))
    return S


def stock():
    S = chbox('stk_neck', .6, 8.6, 10.4, 13.0, 14.2, c=.14, bottom=True)
    S.append(bx('stk_neck_ring', .64, 8.55, 10.45, 13.5, 13.7))
    S += chbox('pad_main', .5, 7.6, 10.6, 14.15, 16.45, c=.14)
    S += chbox('pad_upper', .5, 10.6, 11.2, 14.7, 16.3, c=.14)
    S.append(bx('pad_lower', .5, 6.6, 7.6, 14.9, 15.9))
    for k, y in enumerate((7.9, 8.8, 9.7)):
        S.append(bx(f'pad_rib_{k}', .54, y, y + .14, 15.0, 16.3))
    return S


def magazine():
    MG = ((11.25, 8.1), (10.4, 4.9))           # one magazine axis: bands and floor ride on it
    S = [vbar('mag_body', .49, *MG, 2.5),
         bx('mag_lip', .47, 7.75, 8.0, 9.9, 13.6)]
    for k, off in enumerate((-.7, 0.0, .7)):
        S.append(along(f'mag_band_{k}', .53, *MG, .22, .16, .9, off=off))
    S.append(along('mag_floor', .53, *MG, 2.62, .94, 1.04))
    return S


def _move(e):
    e['from'][2] += DZ; e['to'][2] += DZ
    if 'rotation' in e: e['rotation']['origin'][2] += DZ
    return e


def elements():
    return machined([_move(e) for e in front() + middle() + stock() + magazine()])


PALETTE = 18
RED, GREEN, BEIGE = (128, 62, 58), (84, 102, 90), (150, 136, 112)
PALETTE_KEEP = [RED, GREEN, BEIGE]


def _extra(e, fn, s, t):
    n = e['name']
    if n.startswith(('cover_rail_tooth', 'body_slot', 'shroud_bore')): return (28, 28, 28, 255)
    if n.startswith('sight_post'): return (40, 40, 40, 255)
    if n.startswith('shroud') and not n.startswith(('shroud_ring', 'shroud_bore')) and fn in ('east', 'west', 'up', 'down'):
        u = s * 16; v = t * 6                                # regular hole grid, staggered rows
        fu = (u + (0.5 if int(v) % 2 else 0)) % 1; fv = v % 1
        return (26, 24, 22, 255) if (fu - .5) ** 2 + (fv - .5) ** 2 < .09 else (150, 136, 112, 255)
    if n.startswith(('plate_r', 'plate_l')): return BEIGE + (255,)
    if n.startswith(('body_band', 'plate_screw', 'selector')): return (110, 106, 98, 255)
    if n.startswith('cover') and fn in ('east', 'west', 'up', 'north', 'south'):
        return RED + (255,)
    if n.startswith(('body_front', 'body_mid', 'body_s')) and fn in ('east', 'west') and t < .26:
        return GREEN + (255,)
    return None


special = Painter(__file__, model2world, extra=_extra,
                  flat={'grip_panel': (46, 46, 46), 'pad_rib': (34, 34, 34), 'mag_band': (150, 136, 112),
                        'mag_floor': (40, 40, 40), 'stk_neck_ring': (70, 70, 68), 'rear_cap': (52, 52, 52),
                        'guard_heel': (60, 60, 58), 'shroud_ring': (70, 68, 64)})


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
 'red_enamel':dict(kind='paint',color=(119,57,51),detail=.8,amp=3),
 'green_enamel':dict(kind='paint',color=(73,91,76),detail=.75,amp=3),
 'receiver_coating':dict(kind='paint',color=(45,54,49),detail=.7,amp=2),
 'polymer':dict(kind='polymer',color=(33,42,36),detail=.6,amp=5),
 'brass':dict(kind='gold',color=(151,130,83),detail=.65,amp=8,field=.09),
 'gunmetal':dict(kind='metal',color=(61,67,60),detail=.55,amp=8),
 'steel':dict(kind='steel',color=(123,133,115),detail=.4,amp=10),
 'rubber':dict(kind='rubber',color=(26,31,27),detail=.3,amp=6),
 'recess':dict(kind='dark',color=(18,24,20),detail=0)}
def material(name,face):
    key='receiver_coating'
    if name.startswith('cover'): key='red_enamel'
    if name.startswith(('body_band','body_mid','body_front')): key='green_enamel'
    if name.startswith(('body_s','grip_main','grip_foot','mag_body','plate')): key='polymer'
    if name.startswith(('shroud','mag_band','mag_floor','mag_lip')): key='brass'
    if name.startswith(('shroud_inner','shroud_bore','body_slot','cover_rail','sight')): key='recess'
    if name.startswith(('guard','trigger','stk_neck')): key='gunmetal'
    if name.startswith(('selector','plate_screw','stk_neck_ring')): key='steel'
    if name.startswith(('pad','grip_panel')): key='rubber'
    return _finish_material(key,name,face)
def special(e,fn,s,t):
    n=e['name']; x,y,z=_kit.face_point(e,fn,s,t); side=fn in ('east','west')
    if n.startswith('cover_tail') and side and _lettering('SUROS',s,t,(.08,.18,.9,.85)): return (180,153,96,255)
    if n.startswith('mag_floor') and side and _lettering('SUROS',s,t,(.08,.15,.92,.86)): return (28,34,28,255)
    if n.startswith(('plate_r','plate_l')) and side:
        if .08<s<.92 and .08<t<.92 and (s<.17 or s>.83 or t<.2 or t>.8):
            v=int(151+8*((int(s*37)%5)-2)/2)
            return (v,int(v*.86),int(v*.56),255)
    if n.startswith('cover') and side and 11.57<y<11.63: return (171,129,88,255)
    return None

# W325 material R2: exposed mechanisms, legible material contrast, restrained hand-painted motifs.
_material_r1 = material
_special_r1 = special

def _r2_pixels(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    w=max(1,round(sum(c*c for c in u)**.5*T)); h=max(1,round(sum(c*c for c in v)**.5*T))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

FINAL_ATLAS = (512, 512)
MATERIALS['polymer']['color'] = (48, 60, 50)
MATERIALS['rubber']['color'] = (18, 24, 20)
MATERIALS['gunmetal']['color'] = (85, 94, 83)
MATERIALS['steel']['color'] = (148, 162, 143)
MATERIALS['receiver_coating'].update(kind='metal',color=(85,94,83),amp=8)

def material(name,face):
    original=_material_r1(name,face)
    m=MATERIALS[original] if isinstance(original,str) else original
    if m['kind'] in ('dark','lens','glow'): return original
    if name.startswith(('plate_screw', 'stk_neck_ring')): return _finish_material('steel',name,face)
    if name.startswith(('body_mid', 'body_s', 'body_g', 'rear_', 'plate_r', 'plate_l', 'cover_rail', 'guard', 'stk_neck')): return _finish_material('gunmetal',name,face)
    return original

def special(e,fn,s,t):
    n=e['name']; side=fn in ('east','west'); i,j,w,h=_r2_pixels(e,fn,s,t)
    if n.startswith(('plate_r','plate_l')) and side:
        if (i in (2,w-3) and 2<=j<=h-3) or (j in (2,h-3) and 2<=i<=w-3): return (177,154,99,255)
        return None
    return _special_r1(e,fn,s,t)
