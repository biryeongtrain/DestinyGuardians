"""W325 Lionheart (rare auto rifle, Adaptive frame) on the gnawing_hunger layout contract (same base as W302 Khvostov).

The Lionheart rip is the Pariah body (same mesh placement) with a camo finish, a long slotted brake, a translucent
magazine and a boxed optic with a round eyecup.  The body solids are therefore authored once in the Pariah frame
(art/weapons/w325/pariah/design.py, reused here without its sight, its deepened rail and its magazine/lower-receiver
shift) and moved into the gnawing_hunger frame by DZ -0.44 (grip lands on the gnawing grip, butt 15.31 vs 15.44)
and DY -0.2 (scope axis on the gnawing ADS eye line y 12.785 = W151 sightCenter 12.95 - 0.165, same as the W302
Khvostov reticle).  The brake/barrel ahead of the handguard is compressed 10% so the muzzle stops at -9.6 (contract
-9.54).  Texture = Pariah rip map applied to the Lionheart rip.  NO_OVERLAY + red reticle geometry inside the scope.
"""
import importlib.util, math, sys
from pathlib import Path
_p = Path(__file__).resolve().parent.parent / 'pariah' / 'design.py'
_s = importlib.util.spec_from_file_location('w325_pariah_for_lionheart', _p); P = importlib.util.module_from_spec(_s); _s.loader.exec_module(P)
import kit, types
from detail import Flat, blob, engrave

DZ, DY = -0.44, -0.2
FZ, FK = -5.75, 0.897               # Pariah-frame z ahead of FZ compressed by FK
EYE = 12.785
EYE_Q = EYE - DY                    # eye line in the Pariah frame (12.985 = rip lens centre)
NO_OVERLAY = True
T = 20
RETICLE = (225, 52, 40, 255)


def to_l(p):
    x, y, z = p
    z = z + DZ if z >= FZ else FZ + DZ + (z - FZ) * FK
    return (x, y + DY, z)


def to_q(p):
    x, y, z = p
    z = z - DZ if z >= FZ + DZ else FZ + (z - FZ - DZ) / FK
    return (x, y - DY, z)


def model2world(name, p):
    x, y, z = to_q(p)
    if name.startswith('reticle'):          # reticle samples nothing (special colour)
        pass
    return (-(x - 8.0) / P.S, P.z2w(z), y / P.S + P.YOFF)


def move(e):
    f, t = to_l(e['from']), to_l(e['to'])
    e['from'] = [round(v, 5) for v in f]; e['to'] = [round(v, 5) for v in t]
    if 'rotation' in e:
        e['rotation']['origin'] = [round(v, 5) for v in to_l(e['rotation']['origin'])]
    return e


def box(name, lo, hi, **kw):
    e = {'name': name, 'from': list(lo), 'to': list(hi)}; e.update(kw); return e


B = 10.97                            # bore (Pariah frame)


def muzzle(E):
    b = B
    E.append(box('brake_lip_top', (7.62, b + .12, -9.55), (8.38, b + .38, -9.35)))
    E.append(box('brake_lip_bottom', (7.62, b - .38, -9.55), (8.38, b - .12, -9.35)))
    E.append(box('brake_lip_l', (7.62, b - .12, -9.55), (7.86, b + .12, -9.35)))
    E.append(box('brake_lip_r', (8.14, b - .12, -9.55), (8.38, b + .12, -9.35)))
    E.append(box('brake_bore', (7.86, b - .12, -9.37), (8.14, b + .12, -9.35)))
    E.append(box('brake_body_top',(7.62,b+.18,-9.35),(8.38,b+.38,-7.7)))
    E.append(box('brake_body_bottom',(7.62,b-.38,-9.35),(8.38,b-.18,-7.7)))
    for i,(a,z) in enumerate(((-9.35,-9.2),(-8.9,-8.7),(-8.4,-7.7))):
        E.append(box('brake_body_web_'+str(i),(7.62,b-.18,a),(8.38,b+.18,z)))
    E.append(box('brake_sleeve', (7.6, b - .33, -7.7), (8.4, b + .38, -6.6)))
    E.append(box('barrel', (7.75, b - .22, -6.6), (8.25, b + .28, -5.7)))


def rail(E):
    E.append(box('rail_base', (7.42, 10.2, -5.5), (8.58, 10.45, -0.6)))
    for i in range(10):
        z = -5.42 + i * 0.47
        E.append(box(f'rail_tooth_{i}', (7.45, 9.97, z), (8.55, 10.2, z + .26)))


def scope(E):
    c = EYE_Q; a = 0.3                                # aperture half size around the rip lens axis
    E.append(box('mount_rail', (7.55, 12.07, 2.75), (8.45, 12.35, 5.7)))
    E.append(box('mount_block', (7.6, 12.35, 2.95), (8.4, 12.55, 5.1)))
    z0, z1 = 2.85, 5.6
    E.append(box('sight_scope_top', (7.42, c + a, z0), (8.58, 13.75, z1)))
    E.append(box('sight_scope_bottom', (7.42, 12.5, z0), (8.58, c - a, z1)))
    E.append(box('sight_scope_l', (7.42, c - a, z0), (8.0 - a, c + a, z1)))
    E.append(box('sight_scope_r', (8.0 + a, c - a, z0), (8.58, c + a, z1)))
    f0, f1 = 2.62, 2.85                                 # objective ring
    E.append(box('sight_scope_ring_top', (7.47, c + a, f0), (8.53, 13.52, f1)))
    E.append(box('sight_scope_ring_bottom', (7.47, 12.55, f0), (8.53, c - a, f1)))
    E.append(box('sight_scope_ring_l', (7.47, c - a, f0), (8.0 - a, c + a, f1)))
    E.append(box('sight_scope_ring_r', (8.0 + a, c - a, f0), (8.53, c + a, f1)))
    E.append(box('sight_scope_dial', (8.58, 12.86, 3.7), (8.84, 13.34, 4.25)))
    E.append(box('sight_scope_turret', (7.75, 13.75, 5.0), (8.25, 13.9, 5.6)))
    # round rubber eyecup: 8 staves around the axis (real aperture)
    R, W_ = 0.6, 0.2; side = 2 * R * math.tan(math.radians(22.5))
    for k in range(8):
        e = box(f'sight_eyecup_{k}', (8 - side / 2, c + R - W_, 5.6), (8 + side / 2, c + R, 6.6))
        if k: e['rotation'] = {'origin': [8.0, c, 6.1], 'x': 0, 'y': 0, 'z': k * 45}
        E.append(e)
    zc = 3.0
    for n, (xa, ya, xb, yb) in {'reticle_dot': (7.985, c - .015, 8.015, c + .015),
                                 'reticle_l': (7.76, c - .01, 7.88, c + .01),
                                 'reticle_r': (8.12, c - .01, 8.24, c + .01)}.items():
        E.append(box(n, (xa, ya, zc - .01), (xb, yb, zc + .01), shade=False, light_emission=15))


SKIP_FRONT = ('brake_', 'barrel', 'gas_tube', 'rail_')


def elements():
    P.L = lambda zr: zr                  # Lionheart keeps the rip magwell/lever positions ...
    P.MAG_DZ = 0.0                       # ... and the rip magazine position (gnawing magazine box z 2.1..4.6)
    E = []
    tmp = []; P.front(tmp); E += [e for e in tmp if not e['name'].startswith(SKIP_FRONT)]
    muzzle(E); rail(E)
    P.receiver(E); P.rear(E); P.magazine(E); scope(E)
    return [move(e) for e in P.open_shroud(E)]


def is_magazine(name):
    return name.startswith('mag_') and name not in P.LOWER



# MATERIAL PASS (2026-11-05): replaces whole-face flat painting.
STYLE = 'material'
from detail import resolve_coplanar, line2, rim, face_pixels
_elements_identity = elements
def elements():
    return resolve_coplanar(_elements_identity())

def _rgba(c): return tuple(c)+(255,)
def _surface(key, name, face):
    m=dict(MATERIALS[key])
    # End caps / bevels / remapped optics have no reliable source projection.
    if face in ('north','south') or '_bevel_' in name or name.startswith(('sight_','reticle')):
        m['detail']=0
    elif face in ('up','down'):m['detail']*=.35
    return m

_stencil_views={}
def source_colour(e,fn,s,t):
    if not _stencil_views:
        cache=Path(__file__).resolve().parent/'proj_cache'
        import json
        man=json.loads((cache/'manifest.json').read_text())
        _stencil_views.update({k:kit.View(cache,k,man) for k in man['views']})
        from PIL import Image,ImageFilter
        for k,view in _stencil_views.items():
            clean=Image.open(cache/f'{k}_albedo.png').convert('RGBA').filter(ImageFilter.MedianFilter(9)).filter(ImageFilter.GaussianBlur(5))
            view.alb=clean.load()
    p=kit.face_point(e,fn,s,t);n=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e));a=model2world(e['name'],p)
    b=model2world(e['name'],tuple(p[i]+n[i]*.25 for i in range(3)));wn=[b[i]-a[i] for i in range(3)];ax=max(range(3),key=lambda i:abs(wn[i]))
    view=_stencil_views[('p' if wn[ax]>0 else 'n')+'xyz'[ax]];u,v=view.project(a)
    return view.sample(u,v)

def accent_paint(e,fn,s,t,c):
    # Camo and broad identity paint still carry the same quiet satin grain as adjacent coating.
    i,j,w,h=face_pixels(e,fn,s,t,T);g=(((i*17+j*29)%23)-11)*.17;f=1+.04*math.cos(t*math.pi)
    return tuple(max(0,min(255,round(a*f+g))) for a in c)+(255,)

MATERIALS = {'green_camo_paint': {'kind': 'paint', 'color': (65, 78, 43), 'detail': 0.8, 'amp': 2.5, 'wear': False},
 'ivory_ceramic': {'kind': 'steel',
                   'color': (204, 206, 190),
                   'detail': 0.65,
                   'amp': 5,
                   'field': 0.035,
                   'wear': False},
 'gunmetal': {'kind': 'steel', 'color': (83, 89, 86), 'detail': 0.75, 'amp': 7},
 'silver': {'kind': 'metal', 'color': (166, 168, 160), 'detail': 0.7, 'amp': 6},
 'polymer': {'kind': 'polymer', 'color': (52, 56, 54), 'detail': 0.8, 'amp': 3},
 'grip_brown_wrap': {'kind': 'cloth', 'color': (110, 72, 46), 'detail': 0.9, 'amp': 6},
 'rubber': {'kind': 'rubber', 'color': (17, 20, 18), 'detail': 0.5, 'amp': 3, 'plate': False, 'rim': 0.025},
 'ivory_magazine': {'kind': 'polymer', 'color': (196, 189, 175), 'detail': 0.9, 'amp': 3, 'field': 0.06},
 'lens': {'kind': 'lens', 'color': (53, 101, 119)},
 'recess': {'kind': 'dark', 'color': (16, 18, 18), 'detail': 0.1},
 'emitter': {'kind': 'glow', 'color': (225, 52, 40)},
 'shroud_steel': {'kind': 'metal',
                  'color': (48, 53, 54),
                  'detail': 0.65,
                  'amp': 3,
                  'field': 0.035,
                  'wear': False}}
MATERIAL_RULES = [('hg_main', 'shroud_steel'),
 ('hg_nose', 'shroud_steel'),
 ('rcv_lower', 'gunmetal'),
 ('rcv_post', 'gunmetal'),
 ('rcv_well_back', 'gunmetal'),
 ('rcv_well_rear', 'gunmetal'),
 ('mount_block', 'silver'),
 ('barrel', 'silver'),
 ('reticle', 'emitter'),
 ('brake_bore', 'recess'),
 ('sight_eyecup', 'rubber'),
 ('sight_scope_ring', 'gunmetal'),
 ('sight_scope_dial', 'gunmetal'),
 ('sight_scope_turret', 'gunmetal'),
 ('sight_scope', 'green_camo_paint'),
 ('mount_block', 'green_camo_paint'),
 ('mount_', 'gunmetal'),
 ('grip_panel', 'grip_brown_wrap'),
 ('grip_base', 'rubber'),
 ('grip_', 'polymer'),
 ('butt_', 'rubber'),
 ('stock_', 'gunmetal'),
 ('rcv_', 'green_camo_paint'),
 ('charging', 'silver'),
 ('mag_release', 'silver'),
 ('guard', 'silver'),
 ('trigger', 'gunmetal'),
 ('hg_', 'polymer'),
 ('rail', 'gunmetal'),
 ('brake_sleeve', 'gunmetal'),
 ('brake', 'ivory_ceramic'),
 ('barrel', 'ivory_ceramic'),
 ('mag_plate', 'rubber'),
 ('mag_', 'ivory_magazine')]

def material(name,face):
    inner={'sight_top':'down','sight_bottom':'up','sight_l':'east','sight_r':'west','sight_scope_top':'down','sight_scope_bottom':'up','sight_scope_l':'east','sight_scope_r':'west','sight_scope_ring_top':'down','sight_scope_ring_bottom':'up','sight_scope_ring_l':'east','sight_scope_ring_r':'west'}
    if inner.get(name)==face or name.startswith(('sight_tube','sight_eyecup')) and face=='down':return _surface('recess',name,face)
    if name.startswith('sight_scope_ring') and face in ('north','south'):return _surface('lens',name,face)
    key=next((key for pre,key in MATERIAL_RULES if name.startswith(pre)), 'recess')
    return _surface(key,name,face)

def special(e,fn,s,t):
    n=e['name'];x,y,z=to_q(kit.face_point(e,fn,s,t))
    if n.startswith('reticle'):return RETICLE
    if material(n,fn)['kind']=='paint' and n.startswith(('rcv_','sight_scope_top','sight_scope_bottom','sight_scope_l','sight_scope_r')):
        c=source_colour(e,fn,s,t)
        if c:
            if min(c[:3])>111 and max(c[:3])-min(c[:3])<65:return accent_paint(e,fn,s,t,(202,196,181))
            if c[1]>c[2]+8 and sum(c[:3])/3<61:return accent_paint(e,fn,s,t,(43,57,31))
    if n.startswith('stock_') and fn in ('east','west','up'):
        if abs(z-12.4)<.13 or n.startswith('stock_top') and abs(z-10.55)<.13:return accent_paint(e,fn,s,t,(209,204,191))
    if n=='rcv_plate' and fn in ('east','west') and (min(s,1-s)<.065 or min(t,1-t)<.075):return (173,180,162,255)
    if n.startswith('sight_scope_ring') and fn=='south' and .15<s<.25 and .1<t<.35:return (153,201,220,255)
    return None

# R2 source-based sparse motif, separate from automatic material grain.
_special_material_r1 = special
def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if n=='sight_scope_dial' and fn in ('east','west'):
        i,j,w,h=face_pixels(e,fn,s,t,T)
        if (j==2 or j==h-3) and 2<i<w-3 and i%3==0:return (213,218,198,255)
        if i==w//2 and h//3<j<2*h//3:return (213,218,198,255)
    if n=='grip_panel' and fn in ('east','west'):
        i,j,w,h=face_pixels(e,fn,s,t,T)
        if 2<i<w-3 and 2<j<h-3 and (i+j)%13==0:return (151,106,74,255)
    return _special_material_r1(e,fn,s,t)
