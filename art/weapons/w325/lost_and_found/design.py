"""W325 Lost and Found (common, Rapid-Fire pulse rifle; bullpup, magazine behind the grip) over claws_of_the_wolf.

Rip measured in its nx (right side) / pz (top) / ny (muzzle) projection views.  Uniform map 27.73 px/m: rip butt
(Y 0.331) -> model z 16.8, rip Z 0.10 -> model y 10; muzzle lands at z -8.65 (base -8.61), butt 16.9 (base 16.8).
Model widened 1.2x laterally (rip receiver is only ~1.2 px wide).

W325 detail pass: chamfered silhouette edges (chbox), layered handguard/receiver steps, ribbed magazine, clean flat
paint where the projection smears (Painter).  ADS: everything behind the handguard is held under the claws_of_the_wolf
top profile (receiver 11.70, stock/cheek 11.66, handguard 11.86); the rip's taller receiver/cheek/stock are squeezed
vertically above y 10.6 in the texture map (YK) so their texture still reads.  The mini tube sight (elements named
sight_*) sits inside the base optic window z 4.05-5.25 (base optic shell up to y 13.26) and is a hollow ring whose
0.54 px aperture is centred on the ADS line x 8 / y 12.5.
"""
from w325_5_lib import box, bx, bar, vbar, ring, chbox, along, steps, Uniform, Painter

M = Uniform(27.73, 16.8, 0.331, 10.0, 0.10, -0.00406, kx=1.2)
SIGHT_DY, SIGHT_DZ = -0.22, 0.6
YP = 10.6                                  # vertical squeeze pivot (texture map only)
YK = {'rcv': 1.245, 'stk': 1.5, 'butt': 1.5}
NO_OVERLAY = False

RCV, STK, HG = 0.72, 0.62, 0.72        # stock narrowed to the base stock width (1.2 px) for ADS
RT, ST = 11.70, 11.66
RB = 11.42                                 # lowered rear (top bar / butt) so the ADS view clears                      # receiver / stock top (claws_of_the_wolf profile 11.56-11.84 -> +0.15 tol)


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('sight_'):
        y -= SIGHT_DY; z -= SIGHT_DZ
    for pre, k in YK.items():
        if name.startswith(pre) and y > YP:
            y = YP + (y - YP) * k
    return M((x, y, z))


def front():
    S = []
    # muzzle: octagonal brake with two real side ports, crown ring, sleeve
    S += chbox('muzzle_brake_f', .34, 10.42, 11.06, -8.65, -8.25, c=.12, bottom=True)
    S += chbox('muzzle_brake_r', .34, 10.42, 11.06, -7.75, -7.35, c=.12, bottom=True)
    S.append(bx('muzzle_port_top', .34, 10.92, 11.06, -8.25, -7.75))
    S.append(bx('muzzle_port_bot', .34, 10.42, 10.56, -8.25, -7.75))
    S.append(bx('muzzle_port_bore', .2, 10.56, 10.92, -8.25, -7.75))
    S += chbox('muzzle_sleeve', .29, 10.47, 11.02, -7.35, -6.0, c=.1, bottom=True)
    S.append(bx('muzzle_ring', .32, 10.45, 11.04, -6.35, -6.15))
    S.append(bx('barrel', .22, 10.53, 10.95, -6.0, -0.55))
    S.append(bx('gas_rod', .09, 11.03, 11.2, -7.3, -4.75))
    S.append(bx('gas_rod_clamp', .14, 10.98, 11.25, -6.9, -6.7))
    S += chbox('gas_block', .36, 10.28, 11.3, -5.15, -4.0, c=.1, bottom=True, top=False)
    S.append(bar('gas_block_ramp', .3, (-5.05, 11.05), (-4.6, 11.72), .5, side='below'))
    S.append(bx('gas_block_top', .3, 11.3, 11.72, -4.62, -4.0))
    S.append(bx('gas_block_pin', .4, 10.62, 10.78, -4.75, -4.45))
    # upper tube with a through slot (reads from the side)
    S += chbox('tube_front', .28, 11.25, 11.72, -4.0, -3.05, c=.08)
    S += chbox('tube_rear', .28, 11.25, 11.72, -1.95, -0.98, c=.08)
    S.append(bx('tube_slot_top', .28, 11.58, 11.72, -3.05, -1.95))
    S.append(bx('tube_slot_bottom', .28, 11.25, 11.39, -3.05, -1.95))
    S.append(bx('tube_cap', .33, 11.2, 11.78, -1.0, -0.62))
    # tan collar + two-tone handguard with two recessed slots, chamfered top/bottom edges
    S += chbox('hg_collar', HG + .04, 9.98, 11.86, -0.98, -0.55, c=.16, bottom=True)
    S += chbox('hg_upper', HG, 11.13, 11.86, -0.55, 2.45, c=.2)
    S += chbox('hg_lower', HG, 9.98, 10.92, -0.55, 2.45, c=.18, top=False, bottom=True)
    S.append(bx('hg_slot_core', HG - .16, 10.92, 11.13, -0.55, 2.45))
    for k, (a, b) in enumerate(((-0.55, -0.22), (0.76, 1.2), (2.24, 2.45))):
        S.append(bx(f'hg_bridge_{k}', HG, 10.92, 11.13, a, b))
    S.append(bx('hg_sling_loop', .1, 10.15, 10.7, 2.05, 2.35))
    return S


def middle():
    S = []
    # receiver: chamfered upper / port band / lower, ejection port recessed on the right (+x), bolt handle in the port
    S += chbox('rcv_upper', RCV, 11.18, RT, 2.45, 10.0, c=.18)
    S += chbox('rcv_lower', RCV, 9.72, 10.78, 2.45, 10.0, c=.14, top=False, bottom=True)
    S.append(bx('rcv_band_front', RCV, 10.78, 11.18, 2.45, 3.9))
    S.append(box('rcv_port_core', (8 - RCV, 10.78, 3.9), (8 + RCV - .14, 11.18, 5.7)))
    S.append(box('rcv_bolt_handle', (8 + RCV - .14, 10.88, 5.0), (8 + RCV + .12, 11.08, 5.35)))
    S.append(bx('rcv_band_rear', RCV, 10.78, 11.18, 5.7, 10.0))
    S.append(box('rcv_charge_slot', (8 - RCV - .06, 10.86, 7.0), (8 - RCV, 11.1, 9.7)))
    S.append(bx('rcv_front_lip', RCV + .03, 9.72, 11.72, 2.45, 2.62))
    # low rail under the sight, inside the base optic window
    S.append(bx('rail_base', .36, RT, RT + .1, 4.1, 7.0))
    for k in range(5):
        z = 4.25 + k * .55
        S.append(bx(f'rail_tooth_{k}', .4, RT + .1, RT + .2, z, z + .28))
    # mini tube sight (geometry moved y -0.22, z +0.6): hollow ring, aperture centred on y 12.5
    S += ring('sight_tube_', 12.5, 4.05, 5.22, .37, .1)
    S.append(bx('sight_foot', .3, RT + .2, 12.14, 4.15, 5.1))
    # trigger group
    S.append(bx('trig_housing', .56, 9.45, 9.72, 3.5, 6.45))
    S.append(bx('guard_post', .07, 8.6, 9.45, 4.9, 5.04))
    S.append(bx('guard_bar', .07, 8.48, 8.62, 4.9, 6.75))
    S.append(bar('guard_rear', .07, (6.7, 8.55), (6.95, 9.1), .14))
    S.append(bx('trigger_blade', .07, 9.05, 9.45, 5.9, 6.05))
    S.append(bar('trigger_hook', .07, (5.98, 9.1), (6.25, 8.85), .14))
    # raked pistol grip: core + proud side panels + flared base
    G = ((7.52, 9.72), (8.76, 6.4))           # one grip axis: every grip part shares it (clean seams)
    S.append(vbar('grip_main', .5, *G, 1.72))
    S.append(along('grip_panel', .6, *G, 1.3, .16, .86, off=-.1))
    S.append(along('grip_back', .52, *G, .3, .06, .9, off=.81))
    S.append(along('grip_base', .63, *G, 2.1, .9, 1.03, off=.1))
    return S


def stock():
    S = []
    S.append(bx('stk_front', STK, 9.0, 10.7, 10.0, 14.6))
    S += chbox('stk_cheek', STK + .02, 10.7, 11.6, 10.0, 14.6, c=.2)
    S.append(bx('stk_hole_floor', STK, 9.0, 10.0, 14.6, 15.75))
    S.append(bx('stk_hole_lip', STK - .12, 9.95, 10.08, 14.6, 15.75))
    S.append(bx('stk_post', STK, 9.0, 11.0, 15.75, 16.4))
    S += chbox('stk_top_bar', STK, 11.0, RB, 14.6, 15.95, c=.14)
    S += steps('stk_belly_', STK - .01, 10.0, 16.4, 9.05, 9.05, 7.45, 4)   # axis-aligned stepped belly
    S.append(bx('stk_sling_stud', .08, 7.7, 8.25, 13.95, 14.15))
    S.append(box('stk_knob', (8 + STK, 10.55, 13.35), (8 + STK + .12, 10.95, 13.9)))
    # rubber butt pad with chamfered heel and toe
    S += chbox('butt_pad', STK - .04, 7.45, 10.98, 16.4, 16.8, c=.12, bottom=True)
    return S


def magazine():
    S = [box('mag_body', (7.47, 5.22, 10.13), (8.53, 9.2, 12.85)),
         box('mag_plate', (7.42, 4.95, 10.0), (8.58, 5.32, 13.0))]
    for k, z in enumerate((10.55, 11.35, 12.15)):
        S.append(box(f'mag_rib_{k}', (7.4, 5.9, z), (8.6, 8.5, z + .28)))
    S.append(box('mag_spine', (7.62, 5.5, 12.85), (8.38, 8.9, 12.98)))
    return S


def elements():
    els = front() + middle() + stock() + magazine()
    return els


def _extra(e, fn, s, t):
    n = e['name']
    if n.startswith('sight_tube_') and fn in ('north', 'south'):
        return (58, 60, 63, 255) if min(s, 1 - s, t, 1 - t) < .2 else (36, 38, 40, 255)
    if n.startswith('rail_') or n == 'muzzle_port_bore' or n == 'rcv_port_core':
        return (34, 36, 38, 255)
    return None


special = Painter(__file__, model2world, extra=_extra,
                  flat={'grip_back': (52, 56, 54), 'trig_housing': (48, 50, 50), 'butt_plate': (40, 42, 42)})


# W325 style pass: Dead Man Walking break-up of long slabs + Minecraft pixel palette (kit STYLE 'pixel')
from w325_5_lib import machined as _machined
_elements_raw = elements


def elements():
    return _machined(_elements_raw())


PALETTE = 18


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
 'tan_enamel':dict(kind='paint',color=(126,99,74),detail=.8,amp=3),
 'green_polymer':dict(kind='polymer',color=(39,49,43),detail=.7,amp=5),
 'gunmetal':dict(kind='metal',color=(61,66,63),detail=.65,amp=8),
 'steel':dict(kind='steel',color=(134,145,139),detail=.45,amp=9),
 'rubber':dict(kind='rubber',color=(26,31,28),detail=.4,amp=6),
 'black_recess':dict(kind='dark',color=(19,25,23),detail=0),
 'optic_rim':dict(kind='lens',color=(49,83,72),detail=0)}
def material(name,face):
    key='gunmetal'
    if name.startswith(('rcv','stk','hg_collar')): key='tan_enamel'
    if name.startswith(('hg_upper','hg_lower','hg_bridge','trig_housing','grip_main','grip_base','stk_cheek','sight_foot')): key='green_polymer'
    if name.startswith(('butt','grip_panel','grip_back')): key='rubber'
    if name.startswith(('rcv_port','rcv_charge','muzzle_port_bore','hg_slot')): key='black_recess'
    if name.startswith(('rcv_bolt','gas_block_pin','stk_knob','stk_sling')): key='steel'
    if name.startswith('sight_tube') and face in ('north','south'): key='optic_rim'
    return _finish_material(key,name,face)
def special(e,fn,s,t):
    n=e['name']; x,y,z=_kit.face_point(e,fn,s,t)
    if n.startswith('muzzle_brake_f') and fn=='north' and abs(x-8)<.18 and abs(y-10.74)<.18: return (12,18,17,255)
    if n.startswith('sight_tube') and fn in ('north','south') and .1<s<.22 and t<.2: return (171,204,185,255)
    return None

# W325 material R2: exposed mechanisms, legible material contrast, restrained hand-painted motifs.
_material_r1 = material
_special_r1 = special

def _r2_pixels(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    w=max(1,round(sum(c*c for c in u)**.5*T)); h=max(1,round(sum(c*c for c in v)**.5*T))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

FINAL_ATLAS = (512, 512)
MATERIALS['green_polymer']['color'] = (57, 67, 59)
MATERIALS['rubber']['color'] = (20, 24, 21)
MATERIALS['gunmetal']['color'] = (88, 94, 90)
MATERIALS['steel']['color'] = (154, 163, 157)

def material(name,face):
    original=_material_r1(name,face)
    m=MATERIALS[original] if isinstance(original,str) else original
    if m['kind'] in ('dark','lens','glow'): return original
    if name.startswith(('barrel', 'muzzle_sleeve', 'muzzle_ring')): return _finish_material('steel',name,face)
    if name.startswith(('rcv_band', 'rcv_front_lip', 'rail_', 'guard', 'trigger', 'gas_')): return _finish_material('gunmetal',name,face)
    return original

def special(e,fn,s,t):
    n=e['name']; side=fn in ('east','west'); i,j,w,h=_r2_pixels(e,fn,s,t)
    if n=='mag_body' and side:
        if (i in (3,w-4) and 3<j<h-4) or (j in (4,h-5) and 3<i<w-4): return (42,49,44,255)
        if i in (4,w-5) and j%12 in (0,1) and 7<j<h-7: return (155,165,153,255)
    return _special_r1(e,fn,s,t)
