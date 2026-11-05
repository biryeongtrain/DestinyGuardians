"""W325 SUROS Throwback (uncommon auto rifle, Precision frame) on the ammit_ar2 layout contract.

Model px: muzzle -z, up +y, gun right +x, centred x=8.  Rip (SUROS Throwback.blend, read-only) mapped at 25.7 px/m,
shifted 0.9 px forward so the Omolon-style skeleton grip lands on the ammit grip box; the front (barrel, fork hider,
under-tube) compressed 7% (muzzle -9.3, contract -9.04) and the stock behind z 11 stretched 18% (butt 15.65, contract
15.92).  Height: the green-lit reflex window centre is on the ammit ADS eye line y 13.835 with no riser; the fore-end
pads reach y 9.2 (ammit 9.0).  NO_OVERLAY + green reticle geometry like W302 Khvostov.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts/art/w325'))
import kit
from detail import chamfer, chamfer_seg, engrave, Cleaner, Flat
import re
import types

S = 25.7
YOFF = -0.3012
ZOFF = -0.3502
SH, FK, RS, RK = 0.9, 0.929, 11.0, 1.178
EYE = 13.835
SK = 1.2                           # sight enlarged about the eye line
MAG_DZ = 0.6
NO_OVERLAY = True
T = 20
ATLAS = 1024  # atlas crops to 1024x512; 20px/unit keeps the near-camera panel / optic lines crisp
OCC_TOL = 0.02
RETICLE = (110, 235, 95, 255)


def z2w(z):
    if z < -SH: zu = (z + SH) / FK
    elif z <= RS: zu = z + SH
    else: zu = RS + (z - RS) / RK + SH
    return zu / S + ZOFF


def base_name(name):
    for suf in ('_bevel_', '_crown', '_keel'):
        if suf in name: name = name.split(suf)[0]
    return re.sub(r'_s\d+$', '', name)


def part_transform(name, p):
    x, y, z = p
    name = base_name(name)
    if name.startswith('sight_') or name.startswith('reticle'):
        return (8 + (x - 8) / SK, EYE - 0.05 + (y - EYE) / SK, z)
    if name.startswith('mag_'):
        return (x, y, z + MAG_DZ)
    if name == 'frame_post':
        return (x, y, 5.0 + (z - 4.4) * (0.5 / 1.1))
    return p


def model2world(name, p):
    x, y, z = part_transform(name, p)
    return (-(x - 8.0) / S, z2w(z), y / S + YOFF)


def box(name, lo, hi, **kw):
    e = {'name': name, 'from': list(lo), 'to': list(hi)}; e.update(kw); return e


def rot(e, axis, ang, origin):
    e['rotation'] = {'origin': list(origin), 'x': 0, 'y': 0, 'z': 0}; e['rotation'][axis] = ang; return e


def slope(name, p0, p1, thick, x0, x1, side='below', ext=(0.0, 0.0)):
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dz, dy)
    ang = math.degrees(math.atan2(-dy, dz))
    mz, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    sh = (ext[1] - ext[0]) / 2; mz += dz / L * sh; my += dy / L * sh
    half = (L + ext[0] + ext[1]) / 2
    cy = my - thick / 2 if side == 'below' else my + thick / 2
    return rot(box(name, (x0, cy - thick / 2, mz - half), (x1, cy + thick / 2, mz + half)), 'x', round(ang, 4), (8.0, my, mz))


def yaw(name, p0, p1, w, y0, y1):
    """bar in the top view from (z,x) p0 to p1, width w (x), rotated about +y"""
    dz, dx = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dz, dx)
    ang = math.degrees(math.atan2(dx, dz))           # Ry: x' = x c + z s -> +z tilts toward +x
    mz, mx = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    return rot(box(name, (mx - w / 2, y0, mz - L / 2), (mx + w / 2, y1, mz + L / 2)), 'y', round(ang, 4), (mx, (y0 + y1) / 2, mz))


def roundbar(E, name, z0, z1, cy, r, k=0.72):
    E.append(box(name, (8 - r, cy - r * k, z0), (8 + r, cy + r * k, z1)))
    E.append(box(name + '_v', (8 - r * k, cy - r, z0), (8 + r * k, cy + r, z1)))


BORE = 11.03


def front(E):
    b = BORE
    E.append(box('hider_top', (7.8, b + .1, -9.3), (8.2, b + .24, -8.6)))
    E.append(box('hider_bottom', (7.8, b - .24, -9.3), (8.2, b - .1, -8.6)))
    E.append(box('barrel', (7.78, b - .22, -8.6), (8.22, b + .22, -7.3)))
    E += chamfer('barrel_shroud', (7.62, 10.6, -7.3), (8.38, 11.42, -6.0), .1, ('tl', 'tr', 'bl', 'br'))
    for k, z in (('a', -7.1), ('b', -6.55)):
        E.append(box(f'barrel_ring_{k}', (7.58, 10.56, z), (8.42, 11.46, z + .14)))
    roundbar(E, 'undertube', -8.0, -6.2, 9.62, .38)
    roundbar(E, 'undertube_collar', -6.2, -5.45, 9.65, .44)
    E.append(box('nose_plate', (7.42, 10.35, -6.4), (8.58, 12.0, -5.75)))
    E += chamfer('nose', (7.38, 10.2, -5.75), (8.62, 12.0, -4.5), .12, ('bl', 'br'))
    for k in range(3):                                         # three slanted vents on the nose (rip)
        z = -5.45 + k * .3
        E.append(rot(box(f'nose_vent_{k}', (7.35, 10.85, z), (8.65, 11.45, z + .1)), 'x', -25, (8.0, 11.15, z + .05)))
    E.append(slope('nose_slope', (-5.8, 11.95), (-4.5, 13.0), 0.6, 7.38, 8.62, ext=(0, .1)))
    E += chamfer('nose_lower', (7.48, 9.3, -5.5), (8.52, 10.2, -3.0), .12, ('bl', 'br'))


def shroud(E):
    E += chamfer_seg('shroud_top', (7.35, 12.2, -4.5), (8.65, 13.08, 4.0), .22, cuts=(-1.4, 1.5))
    E.append(box('top_rail', (7.68, 13.08, -3.1), (8.32, 13.12, 1.0)))
    for i in range(9):
        z=-3.1+i*.45
        E.append(box(f'top_rail_tooth_{i}',(7.63,13.12,z),(8.37,13.2,z+.24)))
    E += chamfer_seg('shroud_mid', (7.35, 10.0, -4.5), (8.65, 11.8, 4.0), .0001, (), cuts=(-1.4, 1.5), inset=.04)
    for n, (a, b) in (('a', (-4.5, -3.6)), ('b', (-1.4, 0.9)), ('c', (1.5, 4.0))):
        E.append(box(f'shroud_bridge_{n}', (7.35, 11.8, a), (8.65, 12.2, b)))
    E += chamfer('handguard', (7.35, 9.2, -3.0), (8.65, 10.0, 1.0), .12, ('bl', 'br'))
    for k in range(4):                                         # grey grip pads of the under-handguard
        z = -2.75 + k * .9
        E.append(box(f'hg_pad_{k}', (7.31, 9.32, z), (8.69, 9.9, z + .62)))
    E.append(slope('handguard_rear', (1.0, 9.2), (1.6, 10.0), 0.5, 7.35, 8.65, side='above', ext=(.05, 0)))
    for s, (a, b) in (('l', (6.85, 7.15)), ('r', (8.85, 9.15))):
        for k, (za, zb) in enumerate(((-4.4, -1.5), (-1.3, 1.3), (1.5, 4.4))):   # skirt in three plates
            E.append(box(f'skirt_{s}{k}', (a, 10.05 + .08 * (k == 1), za), (b, 11.55 - .08 * (k == 1), zb)))
    E.append(box('magwell', (7.35, 8.95, 2.0), (8.65, 10.0, 4.6)))
    E.append(slope('magwell_front', (1.3, 10.0), (2.1, 8.95), 0.5, 7.35, 8.65, side='above', ext=(.05, .05)))


def receiver(E):
    E += chamfer('rcv_upper', (7.05, 10.4, 4.0), (8.95, 13.05, 8.0), .25)
    E.append(box('rcv_port', (8.95, 11.35, 5.25), (9.05, 11.75, 6.6)))       # ejection port frame (right side)
    E += chamfer('rcv_tail', (7.1, 12.1, 8.0), (8.9, 12.6, 8.55), .15)   # axis step (was a crossing rotated slab)
    E += chamfer('rcv_rear', (7.1, 10.4, 8.0), (8.9, 12.1, 9.65), .18)
    E.append(box('rcv_lower', (7.15, 9.3, 4.6), (8.85, 10.4, 9.6)))
    E.append(box('guard_bar', (7.4, 8.25, 5.5), (8.6, 8.6, 8.1)))
    E.append(box('frame_front', (7.4, 7.55, 5.4), (8.6, 9.3, 6.12)))
    E.append(box('frame_post', (7.4, 5.95, 4.4), (8.6, 7.6, 5.5)))
    E.append(slope('frame_bar', (5.2, 6.35), (8.75, 7.25), 0.42, 7.45, 8.55, ext=(0, .1)))
    E.append(box('trigger_blade', (7.92, 8.95, 6.5), (8.08, 9.3, 6.72)))
    E.append(rot(box('trigger_hook', (7.92, 8.62, 6.55), (8.08, 9.0, 6.71)), 'x', 25, (8.0, 8.98, 6.63)))
    gp = (8.0, 8.4, 8.9)
    E.append(rot(box('grip', (7.42, 6.95, 8.32), (8.58, 10.2, 9.48)), 'x', -16.3, gp))
    E.append(rot(box('grip_heel', (7.4, 6.95, 8.25), (8.6, 7.4, 9.75)), 'x', -16.3, gp))
    # side cables bowing out from the receiver to the stock (top-view identity)
    for s, sg in (('l', -1), ('r', 1)):
        xo, xi = 8 + sg * 1.4, 8 + sg * 0.95
        E.append(yaw(f'cable_front_{s}', (5.3, xi), (6.6, xo), .2, 11.72, 11.94))
        E.append(box(f'cable_mid_{s}', (xo - .1, 11.72, 6.5), (xo + .1, 11.94, 9.1)))
        E.append(yaw(f'cable_rear_{s}', (9.0, xo), (10.7, 8 + sg * 0.72), .2, 11.72, 11.94))


def sight(E):
    z0, z1 = 6.4, 7.6
    fx, fb, ft = 0.55, 0.6, 0.58
    wx, wb, wt = 0.34, 0.24, 0.24
    E.append(box('sight_base', (7.6, 13.05, 6.0), (8.4, EYE - fb + .02, 7.45)))
    E.append(box('sight_top', (8 - fx, EYE + wt, z0), (8 + fx, EYE + ft, z1)))
    E.append(box('sight_bottom', (8 - fx, EYE - fb, z0), (8 + fx, EYE - wb, z1)))
    E.append(box('sight_l', (8 - fx, EYE - wb, z0), (8 - wx, EYE + wt, z1)))
    E.append(box('sight_r', (8 + wx, EYE - wb, z0), (8 + fx, EYE + wt, z1)))
    zc = 7.2
    for n, (xa, ya, xb, yb) in {'reticle_dot': (7.985, EYE - .015, 8.015, EYE + .015),
                                 'reticle_l': (7.72, EYE - .01, 7.84, EYE + .01),
                                 'reticle_r': (8.16, EYE - .01, 8.28, EYE + .01)}.items():
        E.append(box(n, (xa, ya, zc - .01), (xb, yb, zc + .01), shade=False, light_emission=15))


def stock(E):
    E.append(box('stock_rail', (7.35, 11.6, 9.6), (8.65, 12.05, 14.3)))
    E.append(box('stock_bump', (7.6, 12.05, 9.4), (8.4, 12.55, 10.05)))
    E += chamfer('stock_body', (7.28, 10.35, 9.6), (8.72, 11.6, 14.3), .12, ('bl', 'br'))
    for k in range(3):                                         # dark hex windows of the stock (rip)
        z = 10.4 + k * 1.2
        E.append(box(f'stock_window_{k}', (7.25, 11.0, z), (8.75, 11.45, z + .9)))
    E.append(slope('stock_strut', (10.9, 10.35), (14.15, 9.0), 0.75, 7.35, 8.65, side='above', ext=(0, .05)))
    E += chamfer('butt', (7.3, 8.4, 14.1), (8.7, 12.05, 15.1), .15, ('tl', 'tr', 'bl', 'br'))
    E.append(box('butt_pad', (7.33, 8.6, 15.1), (8.67, 12.05, 15.5)))


def magazine(E):
    d = MAG_DZ
    E += chamfer('mag_body', (7.4, 6.0, 2.6 - d), (8.6, 8.95, 4.95 - d), .1, ('bl', 'br'))
    E.append(box('mag_base', (7.32, 5.6, 2.55 - d), (8.68, 6.05, 5.05 - d)))


def elements():
    E = []
    front(E); shroud(E); receiver(E); sight(E); stock(E); magazine(E)
    return E



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

MATERIALS = {'suros_teal': {'kind': 'paint',
                'color': (51, 77, 72),
                'detail': 1.05,
                'amp': 2.5,
                'wear': (153, 171, 165)},
 'steel': {'kind': 'steel', 'color': (94, 101, 100), 'detail': 0.8, 'amp': 8},
 'gunmetal': {'kind': 'metal', 'color': (83, 88, 86), 'detail': 0.8, 'amp': 7},
 'polymer': {'kind': 'polymer', 'color': (52, 56, 54), 'detail': 0.7, 'amp': 3},
 'rubber': {'kind': 'rubber', 'color': (17, 20, 18), 'detail': 0.4, 'amp': 3, 'plate': False, 'rim': 0.025},
 'cable_rubber': {'kind': 'rubber',
                  'color': (18, 21, 20),
                  'detail': 0.15,
                  'amp': 3,
                  'plate': False,
                  'rim': 0.025},
 'lens': {'kind': 'lens', 'color': (49, 105, 63)},
 'recess': {'kind': 'dark', 'color': (16, 20, 19), 'detail': 0.2},
 'emitter': {'kind': 'glow', 'color': (110, 235, 95)},
 'magazine_steel': {'kind': 'metal', 'color': (49, 55, 54), 'detail': 0.65, 'amp': 4, 'wear': False}}
MATERIAL_RULES = [('mag_body', 'magazine_steel'),
 ('shroud_mid', 'gunmetal'),
 ('shroud_bridge', 'gunmetal'),
 ('stock_strut', 'gunmetal'),
 ('sight_base', 'steel'),
 ('guard', 'steel'),
 ('reticle', 'emitter'),
 ('sight_', 'suros_teal'),
 ('cable', 'cable_rubber'),
 ('butt_pad', 'rubber'),
 ('butt', 'suros_teal'),
 ('grip', 'polymer'),
 ('hg_pad', 'steel'),
 ('stock_window', 'recess'),
 ('stock_rail', 'gunmetal'),
 ('stock_bump', 'gunmetal'),
 ('stock_', 'suros_teal'),
 ('shroud', 'suros_teal'),
 ('skirt', 'suros_teal'),
 ('nose_vent', 'recess'),
 ('nose_lower', 'steel'),
 ('nose', 'suros_teal'),
 ('rcv_port', 'recess'),
 ('rcv_lower', 'gunmetal'),
 ('rcv_', 'suros_teal'),
 ('magwell', 'suros_teal'),
 ('handguard', 'gunmetal'),
 ('barrel_ring', 'steel'),
 ('barrel', 'gunmetal'),
 ('undertube', 'gunmetal'),
 ('hider', 'gunmetal'),
 ('top_rail', 'gunmetal'),
 ('guard', 'gunmetal'),
 ('frame', 'gunmetal'),
 ('trigger', 'steel'),
 ('mag_', 'polymer')]

def material(name,face):
    inner={'sight_top':'down','sight_bottom':'up','sight_l':'east','sight_r':'west','sight_scope_top':'down','sight_scope_bottom':'up','sight_scope_l':'east','sight_scope_r':'west','sight_scope_ring_top':'down','sight_scope_ring_bottom':'up','sight_scope_ring_l':'east','sight_scope_ring_r':'west'}
    if inner.get(name)==face or name.startswith(('sight_tube','sight_eyecup')) and face=='down':return _surface('recess',name,face)
    if name in ('sight_top','sight_bottom','sight_l','sight_r') and face in ('north','south'):return _surface('lens',name,face)
    key=next((key for pre,key in MATERIAL_RULES if name.startswith(pre)), 'recess')
    return _surface(key,name,face)

def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if n.startswith('reticle'):return RETICLE
    if n.startswith('mag_body') and fn in ('east','west'):
        q=z-.62*y
        if any(abs(q-a)<.035 for a in (-1.75,-1.18)):return (162,171,166,255)
    if n in ('sight_top','sight_bottom') and fn=='south' and .15<s<.25 and .1<t<.35:return (139,200,148,255)
    return None

# R2 source-based sparse motif, separate from automatic material grain.
_special_material_r1 = special
def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if n.startswith('rcv_upper') and fn in ('east','west'):
        for a,b in ((4.28,12.65),(6.45,12.6),(7.7,10.65)):
            if max(abs(z-a),abs(y-b))<.065:
                return (44,52,49,255) if abs(y-b)<.018 else (176,186,175,255)
    return _special_material_r1(e,fn,s,t)
