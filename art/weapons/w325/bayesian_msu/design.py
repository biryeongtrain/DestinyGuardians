"""W325 Bayesian MSu (rare, Adaptive pulse rifle; Veist bullpup with enclosed hand loop and a splayed bipod) over bygones.

Rip measured in nx / pz / ny views.  Uniform map 26.6 px/m (rip 0.94 m with the bipod), authoring frame rip butt
(Y 0.296) -> z 16.8, rip Z 0.12 -> y 10; whole model shifted DZ = -0.3.  The rip's grip sits ~1 px behind bygones'
grip while its magazine already matches, so the grip/trigger are moved a further 0.4 px forward (part transform) and the
hand-loop bar is re-aimed at the moved grip foot.  The screen sight block (rip z 6.3-8.9, over the eye) is moved
1.8 px forward and 0.09 up: hollow box with its 0.76 px aperture centred x 8 / y 12.74 (bygones W151 pin tip 12.74).
Muzzle -6.45 (base -8.54): short rip barrel kept; the bipod legs reach -8.4.

W325 detail/style pass: the screen sight is shortened to the rear 1.3 px of the rip block and placed at z 5.2-6.5,
inside bygones' optic tube window (z 5.18-6.77, top 13.4) - hollow box (elements sight_*) whose aperture surrounds
the aim point x 8 / y 12.74; nothing else rises above the bygones roof (adscheck OK).  Dead Man Walking break-up of
the long upper rail / receiver / stock slabs (machined segments, chamfered edges), rail teeth, handguard slots as
real dark recesses, bipod hinge/feet, ribbed grip and magazine, layered butt pad; Minecraft pixel palette with the
ivory / yellow-camo / teal-black blocks painted flat.
"""
from w325_5_lib import box, bx, bar, bar3, vbar, ring, chbox, machined, Uniform, along, bar_on, Painter

M = Uniform(26.6, 16.8, 0.296, 10.0, 0.12, 0.0025)
DZ, G_DZ = -0.3, -0.4
S_DZ, S_DY = -2.1, 0.09
NO_OVERLAY = False
B = .82


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    z -= DZ
    if name.startswith('grip_') or name.startswith('trigger_'):
        z -= G_DZ
    if name.startswith('sight_'):
        z -= S_DZ; y -= S_DY
    return M((x, y, z))


def front():
    S = []
    S += chbox('muzzle_tip', .32, 9.68, 10.32, -6.15, -5.3, c=.1, bottom=True)
    S.append(bx('muzzle_crown', .26, 9.75, 10.25, -6.25, -6.15))
    for k, z in enumerate((-5.95, -5.65)):
        S.append(bx(f'muzzle_knurl_{k}', .35, 9.65, 10.35, z, z + .12))
    S += chbox('muzzle_collar', .37, 9.6, 10.4, -5.3, -4.95, c=.1, bottom=True)
    S += chbox('fblock', .55, 9.95, 11.7, -4.95, -3.85, c=.16)
    S += chbox('rail_upper', B, 11.0, 12.0, -3.7, 9.1, c=.2)
    for k in range(6):
        z = -3.2 + k * .7
        S.append(bx(f'rail_tooth_{k}', .36, 12.0, 12.07, z, z + .32))
    S.append(box('rail_line_r', (8 + B - .02, 11.45, -3.5), (8 + B + .03, 11.58, 3.5)))
    S.append(box('rail_line_l', (8 - B - .03, 11.45, -3.5), (8 - B + .02, 11.58, 3.5)))
    S += chbox('hg', B - .02, 9.45, 11.0, -3.85, 2.9, c=.0001, top=False)[:1]
    for k in range(5):
        z = -3.4 + k * 1.2
        for t, y in (('u', 10.42), ('d', 9.85)):
            S.append(box(f'hg_slot_{t}{k}', (8 - B - .02, y, z), (8 + B + .02, y + .2, z + .7)))
    S += chbox('module_main', B - .02, 8.0, 9.25, -3.25, 3.0, c=.16, top=False, bottom=True)
    S += [box(f'module_chin{i}', (8 - B + .06, 7.4 + .2 * (2 - i), -2.4 + .6 * i), (8 + B - .06, 8.0, -1.8 + .6 * i))
          for i in range(3)]                    # axis-aligned steps instead of an 18 deg chin slab
    S.append(bx('module_belly', B - .06, 7.4, 8.0, -0.6, 2.4))
    S.append(bx('module_end', .7, 7.35, 9.0, 3.0, 3.4))
    S.append(bx('module_window', B, 8.45, 8.85, -1.8, 0.6))
    S.append(bx('bipod_hinge', .5, 7.75, 8.1, -3.6, -3.2))
    for sx in (-1, 1):
        t = 'r' if sx > 0 else 'l'
        S.append(bar3(f'bipod_leg_{t}', (8 + sx * .35, 7.9, -3.4), (8 + sx * 1.5, 6.35, -7.75), .36))
        S.append(box(f'bipod_foot_{t}', (8 + sx * 1.5 - .22, 5.6, -8.05), (8 + sx * 1.5 + .22, 6.5, -7.6)))
    return S


def middle():
    S = []
    S += chbox('rcv_lower', B, 8.5, 11.0, 2.9, 7.45, c=.0001, top=False)[:1]
    S += chbox('rcv_lower_rear', B, 9.0, 11.0, 7.45, 10.0, c=.0001, top=False)[:1]
    S += chbox('rcv_upper_rear', B, 10.6, 11.95, 9.1, 14.0, c=.2)
    S.append(box('rcv_port_r', (8 + B - .03, 10.0, 4.3), (8 + B + .03, 10.55, 6.5)))
    S.append(box('rcv_bolt_r', (8 + B, 10.1, 5.6), (8 + B + .12, 10.4, 6.0)))
    S.append(box('rcv_pin_r', (8 + B, 9.3, 7.9), (8 + B + .06, 9.5, 8.1)))
    LB = ((3.6, 7.83), (7.6, 6.24))
    S.append(bar('loop_bar', B - .08, *LB, .72))
    S.append(bar_on('loop_web', B - .06, *LB, .9, -.15, .45, off=.8))
    S.append(bar_on('loop_rim', B - .02, *LB, .14, .12, .92, off=-.29))
    S.append(bx('trigger_blade', .07, 7.95, 8.5, 6.6, 6.78))
    S.append(bar('trigger_hook', .07, (6.7, 8.0), (6.95, 7.75), .14))
    G = ((8.2, 8.9), (8.8, 6.2))
    S.append(vbar('grip_main', .44, *G, 1.7))
    S.append(along('grip_panel', .52, *G, 1.3, .14, .85, off=-.05))
    S.append(along('grip_foot', .52, *G, 2.0, .92, 1.04, off=.05))
    # screen sight block (rear 1.3 px of the rip block) moved into bygones' optic window: hollow, aperture on ADS line
    S += ring('sight_box_', 12.65, 7.6, 8.9, .48, .1, corners=False)
    S.append(bx('sight_rear_ear', .2, 13.13, 13.3, 8.2, 8.9))
    S.append(bx('sight_foot', .3, 12.07, 12.17, 7.7, 8.8))
    return S


def stock():
    S = chbox('stk_lower', B + .03, 7.6, 10.6, 10.0, 14.4, c=.2, top=False, bottom=True)
    S.append(box('stk_panel_r', (8 + B + .03, 8.0, 10.6), (8 + B + .09, 10.0, 13.0)))
    S.append(box('stk_panel_l', (8 - B - .09, 8.0, 10.6), (8 - B - .03, 10.0, 13.0)))
    S.append(bx('stk_frame_top', .75, 11.4, 11.9, 14.0, 14.8))
    S.append(bx('stk_frame_bot', .75, 8.0, 8.6, 14.0, 14.8))
    S.append(bx('stk_frame_core', .62, 8.6, 11.4, 14.15, 14.65))
    S.append(bx('stk_rod', .25, 10.3, 11.3, 14.8, 15.4))
    S.append(bx('stk_rod_low', .22, 8.5, 9.3, 14.8, 15.4))
    S += chbox('butt_pad', .55, 7.8, 12.0, 15.4, 16.5, c=.18, bottom=True)
    for k, y in enumerate((8.5, 9.4, 10.3, 11.2)):
        S.append(bx(f'butt_rib_{k}', .59, y, y + .14, 15.6, 16.3))
    return S


def magazine():
    S = [box('mag_body', (7.55, 5.4, 10.85), (8.45, 7.95, 13.25)),
         box('mag_base', (7.5, 5.0, 10.7), (8.5, 5.42, 13.3))]
    for k, y in enumerate((6.0, 6.7, 7.4)):
        S.append(box(f'mag_rib_{k}', (7.5, y, 11.1), (8.5, y + .2, 13.0)))
    return S


def _move(e, dz, dy=0.0):
    e['from'][2] += dz; e['to'][2] += dz; e['from'][1] += dy; e['to'][1] += dy
    if 'rotation' in e: e['rotation']['origin'][2] += dz; e['rotation']['origin'][1] += dy
    return e


def elements():
    out = []
    for e in front() + middle() + stock() + magazine():
        n = e['name']
        if n.startswith('sight_'): out.append(_move(e, DZ + S_DZ, S_DY))
        elif n.startswith('grip_') or n.startswith('trigger_'): out.append(_move(e, DZ + G_DZ))
        else: out.append(_move(e, DZ))
    return machined(out)


PALETTE = 18
IVORY, YELLOW, TEAL = (206, 200, 186), (196, 188, 112), (52, 60, 60)
PALETTE_KEEP = [IVORY, YELLOW, TEAL]


def _extra(e, fn, s, t):
    n = e['name']
    if n.startswith('sight_box_') and fn in ('north', 'south'):
        return (70, 72, 66, 255) if min(s, 1 - s, t, 1 - t) < .25 else (40, 44, 42, 255)
    if n.startswith(('hg_slot', 'rail_line', 'rcv_port', 'module_window')): return (22, 24, 26, 255)
    if n.startswith(('rail_tooth', 'rcv_bolt', 'rcv_pin', 'bipod_hinge', 'muzzle_knurl')): return (120, 118, 110, 255)
    if n.startswith(('stk_panel',)): return YELLOW + (255,)
    if n.startswith('rail_upper') and fn in ('east', 'west', 'up'):
        # ivory rail with two big yellow camo blobs (flat 2-colour block, W30 style)
        if fn != 'up' and 0.25 < s < 0.42 and t < .7: return YELLOW + (255,)
        if 0.62 < s < 0.74 and t > .3: return YELLOW + (255,)
        return IVORY + (255,)
    return None


special = Painter(__file__, model2world, extra=_extra,
                  flat={'grip_panel': (44, 42, 44), 'mag_rib': (60, 66, 66), 'loop_rim': (60, 68, 68),
                        'butt_rib': (40, 40, 44), 'stk_frame_core': (40, 44, 44), 'muzzle_crown': (30, 30, 30),
                        'stk_rod_low': (150, 146, 136)})


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
 'ivory_enamel':dict(kind='paint',color=(201,200,177),detail=.75,amp=3),
 'yellow_enamel':dict(kind='paint',color=(179,171,88),detail=.7,amp=3),
 'teal_enamel':dict(kind='paint',color=(35,57,55),detail=.8,amp=3),
 'polymer':dict(kind='polymer',color=(30,43,39),detail=.6,amp=5),
 'gunmetal':dict(kind='metal',color=(58,68,63),detail=.65,amp=8),
 'steel':dict(kind='steel',color=(137,151,137),detail=.4,amp=10),
 'rubber':dict(kind='rubber',color=(25,30,28),detail=.3,amp=6),
 'recess':dict(kind='dark',color=(17,26,23),detail=0),
 'lens':dict(kind='lens',color=(45,90,70),detail=0)}
def material(name,face):
    key='teal_enamel'
    if name.startswith(('rail_upper','sight_box','sight_rear_ear','muzzle','trigger')): key='ivory_enamel'
    if name.startswith('stk_panel'): key='yellow_enamel'
    if name.startswith(('rcv_lower','loop','grip_main','grip_foot','mag_body','module')): key='polymer'
    if name.startswith(('rail_tooth','bipod','stk_frame','mag_rib','mag_base')): key='gunmetal'
    if name.startswith(('rcv_pin','rcv_bolt','bipod_hinge','muzzle_knurl','stk_rod')): key='steel'
    if name.startswith(('butt','grip_panel')): key='rubber'
    if name.startswith(('hg_slot','rail_line','rcv_port','module_window')): key='recess'
    if name.startswith('sight_box') and face in ('north','south'): key='lens'
    return _finish_material(key,name,face)
def special(e,fn,s,t):
    n=e['name']; x,y,z=_kit.face_point(e,fn,s,t)
    if n.startswith(('rail_upper','sight_box')):
        c=_source_sample(e,fn,s,t)
        if c is not None and c[0]>105 and c[1]>105 and c[0]-c[2]>22 and c[1]-c[2]>20:
            d=max(-14,min(16,(sum(c)/3-155)*.25)); grain=((int(s*83)*17+int(t*49)*29)%7)-3
            return tuple(int(v+d+grain) for v in (179,171,88))+(255,)
    if n.startswith('muzzle_tip') and fn=='north' and abs(x-8)<.17 and abs(y-10)<.17: return (12,19,16,255)
    return None

# W325 material R2: exposed mechanisms, legible material contrast, restrained hand-painted motifs.
_material_r1 = material
_special_r1 = special

def _r2_pixels(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    w=max(1,round(sum(c*c for c in u)**.5*T)); h=max(1,round(sum(c*c for c in v)**.5*T))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

FINAL_ATLAS = (1024, 512)
MATERIALS['polymer']['color'] = (48, 61, 53)
MATERIALS['rubber']['color'] = (18, 24, 20)
MATERIALS['gunmetal']['color'] = (82, 101, 94)
MATERIALS['steel']['color'] = (155, 167, 148)

def material(name,face):
    original=_material_r1(name,face)
    m=MATERIALS[original] if isinstance(original,str) else original
    if m['kind'] in ('dark','lens','glow'): return original
    if name.startswith(('muzzle', 'stk_rod')): return _finish_material('steel',name,face)
    if name.startswith(('rcv_lower', 'rcv_upper', 'module', 'stk_lower', 'stk_frame', 'loop', 'trigger')): return _finish_material('gunmetal',name,face)
    return original
MATERIALS['ivory_enamel'].update(wear=False,detail=.25)
MATERIALS['yellow_enamel'].update(wear=False,detail=.25)

_r2_camo_cache={}
def _r2_camo(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    cols=max(1,round(sum(c*c for c in u)**.5/.7)); rows=max(1,round(sum(c*c for c in v)**.5/.7))
    col=min(cols-1,int(s*cols)); row=min(rows-1,int(t*rows)); key=(e['name'],fn,col,row)
    if key not in _r2_camo_cache:
        samples=[_source_sample(e,fn,(col+(a+.5)/3)/cols,(row+(b+.5)/3)/rows) for a in range(3) for b in range(3)]
        samples=[c for c in samples if c is not None]
        votes=sum(c[0]>105 and c[1]>105 and c[0]-c[2]>22 and c[1]-c[2]>20 for c in samples)
        _r2_camo_cache[key]=(179, 171, 88)+(255,) if samples and votes/len(samples)>=.4 else None
    return _r2_camo_cache[key]

def special(e,fn,s,t):
    n=e['name']; side=fn in ('east','west'); i,j,w,h=_r2_pixels(e,fn,s,t)
    if n=='mag_body' and side:
        if i in (4,w-5) and j in (5,h-6): return (174,185,159,255)
        if i in (5,w-4) and j in (6,h-5): return (24,36,29,255)
    if n.startswith(('rail_upper','sight_box')):
        if n.startswith('sight_box') and fn in ('north','south'): return None
        return _r2_camo(e,fn,s,t)
    return _special_r1(e,fn,s,t)
