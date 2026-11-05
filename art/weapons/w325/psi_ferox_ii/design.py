"""W325 Psi Ferox II (uncommon, Lightweight pulse rifle; Veist bullpup with enclosed hand loop) over chattering_bone.

Rip measured in nx / pz views.  Authoring ("read") frame: uniform 25 px/m, rip butt (Y 0.3025) -> z 16.8, rip
Z 0.12 -> y 10.  Model = read frame with (1) the barrel/suppressor ahead of the handguard cap (z < -5.3) compressed
to 0.62 so the muzzle lands at -9.0 instead of -11.25 (base -8.66), and (2) a DZ = -0.2 shift so the grip (top
z 8.1-9.8) and the magazine (z 10.6-12.8) straddle chattering_bone's grip (~7.7-9.6) and moving magazine (10.8-13.3).
No optic: the receiver hump is the rip's integrated rear hood; its top is kept at y 12.78, just under the base ADS
line (chattering_bone W151 pin tip 12.93), and the W148 overlay dot provides the aim point.

W325 detail/style pass: hump shortened to the base optic hood span (top 12.72 over z 7.05-7.95 placed), a 12.5 step in
front and a lower tail (12.32) behind it, so nothing rises above chattering_bone's top profile (adscheck OK).  Chamfered receiver/stock
edges, rail teeth, vents, bracket posts, ribbed grip/magazine, stepped butt; long slabs broken into machined segments
(machined()); Minecraft pixel palette bake (kit STYLE pixel) + Painter flat colours where the projection smears.
"""
from w325_5_lib import box, bx, bar, vbar, chbox, machined, Uniform, along, bar_on, Painter

M = Uniform(25.0, 16.8, 0.3025, 10.0, 0.12, 0.0, kx=1.05)
ZB, KB, DZ = -5.3, 0.62, -0.2
NO_OVERLAY = False
B = .8


def zmap(z): return z if z >= ZB else ZB + (z - ZB) * KB
def zinv(z): return z if z >= ZB else ZB + (z - ZB) / KB


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    return M((x, y, zinv(z - DZ)))


def barrel():
    S = [bx('brl_sup_lip', .42, 9.72, 10.55, -11.25, -11.05)]
    S += chbox('brl_sup', .48, 9.65, 10.6, -11.05, -7.3, c=.14, bottom=True)
    S.append(box('brl_sup_slot', (8.46, 9.95, -10.6), (8.5, 10.3, -8.0)))
    S.append(bx('brl_barrel', .27, 9.9, 10.45, -7.3, -5.05))
    S.append(bx('brl_collar', .32, 9.85, 10.5, -6.85, -6.2))
    S.append(bx('brl_collar_r', .35, 9.82, 10.53, -6.6, -6.45))
    return S


def front():
    S = []
    S += chbox('hg_cap', B + .02, 8.4, 11.15, -5.15, -4.85, c=.16, bottom=True)
    S.append(bx('hg_hook', .3, 8.45, 9.1, -5.75, -5.15))
    S += chbox('hg_top', B, 10.15, 11.15, -4.85, 1.0, c=.2)
    # Open truss windows: no opaque core behind the diagonal struts.
    for k, (a, b) in enumerate(((-4.85, -4.42), (-3.5, -3.3), (-2.0, -1.72), (-0.42, 3.0))):
        S.append(bx(f'hg_post{k}', B, 9.25, 10.15, a, b))
    for k, z in enumerate((-3.95, -2.65, -1.2)):          # diagonal truss struts (real bars, both sides as one)
        S.append(bar(f'hg_strut{k}_a', B - .1, (z - .4, 9.25), (z, 10.15), .16))
        S.append(bar(f'hg_strut{k}_b', B - .1, (z, 10.15), (z + .4, 9.25), .16))  # connected triangular bracing
    S.append(bx('hg_rail', B - .05, 8.62, 9.25, -4.85, 2.9))
    S += chbox('hg_bottom', B - .1, 8.25, 8.62, -4.85, 0.2, c=.12, top=False, bottom=True)
    for k in range(4):
        z = -4.4 + k * 1.1
        S.append(bx(f'hg_rail_tooth{k}', B - .02, 8.75, 8.95, z, z + .5))
    S.append(bx('swivel_a', .25, 7.72, 8.38, 0.3, 0.9))
    S.append(bx('swivel_b', .25, 7.85, 8.25, 0.15, 1.05))
    S.append(bx('swivel_pin', .32, 7.98, 8.12, 0.52, 0.68))
    S.append(bx('bracket_front', .45, 11.15, 11.68, -4.62, -4.5))
    S.append(bx('bracket_top', .45, 11.66, 11.78, -4.62, 0.45))
    S.append(bar('bracket_rear', .45, (0.4, 11.72), (1.0, 11.22), .12))
    return S


def middle():
    S = []
    S += chbox('rcv_front', B, 10.15, 11.38, 1.0, 4.6, c=.18)
    S.append(bar('rcv_ramp', B - .2, (4.3, 11.38), (4.75, 12.07), .4, side='below'))   # ends under the chamfer
    S += chbox('rcv_upper', B, 10.3, 12.25, 4.6, 9.3, c=.22)
    S += chbox('rcv_rear_upper', B, 10.3, 11.95, 9.3, 14.5, c=.2)
    S.append(bx('hump_step', .5, 12.25, 12.5, 6.25, 7.25))
    S.append(bx('hump', .5, 12.25, 12.72, 7.25, 8.15))
    S.append(bx('hump_tail', .5, 12.25, 12.32, 8.15, 9.2))
    S.append(bx('hump_window', .32, 12.4, 12.6, 7.4, 8.0))
    for k, z in enumerate((5.0, 5.55, 6.1)):
        S.append(box(f'rcv_vent_r{k}', (8 + B - .03, 10.7, z), (8 + B + .04, 11.6, z + .25)))
    S.append(box('rcv_bolt_r', (8 + B, 10.5, 9.8), (8 + B + .1, 10.85, 11.4)))
    S += chbox('rcv_lower', B + .02, 8.45, 10.3, 3.0, 10.4, c=.0001, top=False)[:1]
    LB = ((3.6, 8.46), (8.7, 6.31))            # loop bar centre axis (was side='above' of (3.6,8.1)-(8.7,5.95))
    S.append(bar('loop_bar', B - .08, *LB, .72))
    S.append(bar_on('loop_web', B - .06, *LB, .9, -.1, .55, off=.8))
    S.append(bar_on('loop_rim', B - .02, *LB, .14, .1, .92, off=-.29))
    S.append(bx('trigger_blade', .07, 7.95, 8.45, 7.32, 7.48))
    S.append(bar('trigger_hook', .07, (7.4, 8.0), (7.65, 7.75), .14))
    G = ((8.95, 8.9), (9.65, 6.25))
    S.append(vbar('grip_main', .5, *G, 1.55))
    S.append(along('grip_panel', .6, *G, 1.15, .14, .86, off=-.05))
    S.append(along('grip_foot', .6, *G, 1.95, .93, 1.05, off=.1))
    return S


def stock():
    S = chbox('stk_lower', B + .02, 8.3, 10.3, 10.4, 14.5, c=.18, top=False, bottom=True)
    S.append(box('stk_panel_r', (8 + B + .02, 8.75, 11.0), (8 + B + .08, 9.9, 13.9)))
    S.append(box('stk_panel_l', (8 - B - .08, 8.75, 11.0), (8 - B - .02, 9.9, 13.9)))
    S.append(bx('stk_cage_top', 1.0, 11.45, 11.95, 14.5, 15.3))
    S.append(bx('stk_cage_bot', 1.0, 8.3, 8.8, 14.5, 15.3))
    S.append(box('stk_cage_l', (7.0, 8.8, 14.5), (7.25, 11.45, 15.3)))
    S.append(box('stk_cage_r', (8.75, 8.8, 14.5), (9.0, 11.45, 15.3)))
    S.append(bx('stk_cage_core', .75, 8.8, 11.45, 14.75, 15.05))
    S += chbox('butt_pad', .55, 8.3, 11.8, 15.3, 16.55, c=.16, bottom=True)
    for k, y in enumerate((9.0, 9.9, 10.8)):
        S.append(bx(f'butt_rib{k}', .59, y, y + .14, 15.6, 16.35))
    return S


def magazine():
    S = [box('mag_body', (7.53, 5.5, 10.85), (8.47, 8.4, 13.0)),
         box('mag_base', (7.48, 5.05, 10.6), (8.52, 5.5, 13.05))]
    for k, y in enumerate((6.3, 7.1, 7.9)):
        S.append(box(f'mag_rib_{k}', (7.48, y, 11.1), (8.52, y + .22, 12.8)))
    return S


def _place(e):
    for k in ('from', 'to'):
        e[k][2] = zmap(e[k][2]) + DZ
    if 'rotation' in e:
        e['rotation']['origin'][2] = zmap(e['rotation']['origin'][2]) + DZ
    return e


def elements():
    return machined([_place(e) for e in barrel() + front() + middle() + stock() + magazine()])


PALETTE = 18
FLAT_TOL = 18
PURPLE = (84, 70, 92)
PALETTE_KEEP = [PURPLE, (64, 52, 72)]


def grade(rgb):
    r, g, b = rgb; y = .299 * r + .587 * g + .114 * b; y2 = 80 + (y - 70) * 1.15
    return tuple(max(0, min(255, int(round(y2 + (c - y) * 2.4)))) for c in (r, g, b))   # keep the violet tint


def _extra(e, fn, s, t):
    n = e['name']
    if n.startswith(('hg_rail_tooth', 'rcv_vent', 'brl_sup_slot')): return (30, 28, 34, 255)
    if n.startswith(('swivel_pin', 'brl_collar_r', 'rcv_bolt')): return (128, 124, 132, 255)
    if n == 'hump_window': return (54, 70, 74, 255)
    if n.startswith(('rcv_upper', 'rcv_front', 'hg_top', 'hump', 'rcv_ramp')) and fn in ('east', 'west', 'up'):
        if fn != 'up' and t > .82: return (64, 52, 72, 255)            # darker lower lip line
        return PURPLE + (255,)
    return None


special = Painter(__file__, model2world, extra=_extra,
                  flat={'grip_panel': (52, 54, 52), 'mag_rib': (58, 60, 58), 'loop_rim': (60, 58, 66),
                        'butt_rib': (38, 38, 40), 'stk_cage_core': (40, 40, 44)})


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
 'violet_enamel':dict(kind='paint',color=(78,65,85),detail=.85,amp=3),
 'green_polymer':dict(kind='polymer',color=(39,47,42),detail=.7,amp=5),
 'gunmetal':dict(kind='metal',color=(58,62,59),detail=.6,amp=8),
 'steel':dict(kind='steel',color=(120,126,125),detail=.4,amp=10),
 'rubber':dict(kind='rubber',color=(27,31,28),detail=.3,amp=6),
 'recess':dict(kind='dark',color=(21,23,25),detail=0),
 'lens':dict(kind='lens',color=(40,83,90),detail=0)}
def material(name,face):
    key='violet_enamel'
    if name.startswith(('rcv_lower','loop','grip_main','grip_foot','stk_lower','stk_panel','mag_body')): key='green_polymer'
    if name.startswith(('stk_cage','hg_rail','swivel','bracket','brl_barrel','brl_collar','mag_rib','mag_base')): key='gunmetal'
    if name.startswith(('rcv_bolt','brl_collar_r','swivel_pin')): key='steel'
    if name.startswith(('butt','grip_panel')): key='rubber'
    if name.startswith(('rcv_vent','brl_sup_slot')): key='recess'
    if name=='hump_window': key='lens'
    return _finish_material(key,name,face)
def special(e,fn,s,t):
    n=e['name']; x,y,z=_kit.face_point(e,fn,s,t)
    if n=='hump_window' and .15<s<.23 and .15<t<.3: return (160,209,211,255)
    if n.startswith('brl_sup_lip') and fn=='north' and abs(x-8)<.2 and abs(y-10.135)<.2: return (15,19,20,255)
    return None

# W325 material R2: exposed mechanisms, legible material contrast, restrained hand-painted motifs.
_material_r1 = material
_special_r1 = special

def _r2_pixels(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    w=max(1,round(sum(c*c for c in u)**.5*T)); h=max(1,round(sum(c*c for c in v)**.5*T))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

FINAL_ATLAS = (1024, 512)
MATERIALS['green_polymer']['color'] = (45, 58, 48)
MATERIALS['rubber']['color'] = (17, 23, 19)
MATERIALS['gunmetal']['color'] = (78, 88, 80)
MATERIALS['steel']['color'] = (153, 163, 159)
MATERIALS['tinted_steel']=dict(kind='metal',color=(108,98,116),detail=.55,amp=9)

def material(name,face):
    original=_material_r1(name,face)
    m=MATERIALS[original] if isinstance(original,str) else original
    if m['kind'] in ('dark','lens','glow'): return original
    if name.startswith(('rcv_rear_upper', 'rcv_front', 'brl_sup')): return _finish_material('tinted_steel',name,face)
    if name.startswith(('rcv_lower', 'stk_lower', 'stk_panel', 'loop', 'trigger', 'hg_strut', 'hg_post')): return _finish_material('gunmetal',name,face)
    return original

def special(e,fn,s,t):
    n=e['name']; side=fn in ('east','west'); i,j,w,h=_r2_pixels(e,fn,s,t)
    if n.startswith('rcv_rear_upper') and side and '_top' not in n:
        x,y,z=_kit.face_point(e,fn,s,t)
        if 11.3<y<11.55 and int(z*T)%6==0: return (38,42,41,255)
        if 11.55<=y<11.6 and int(z*T)%6==0: return (161,155,169,255)
    return _special_r1(e,fn,s,t)
