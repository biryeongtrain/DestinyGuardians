"""W325 Refrain-23 (rare auto rifle, Adaptive frame) on the gnawing_hunger layout contract (W302 Khvostov base).

Model px: muzzle -z, up +y, gun right +x, centred x=8.  Rip (Refrain-23.blend, read-only) at 25.4 px/m with the
muzzle tip on the contract; grip, magazine and trigger land on the gnawing boxes at this scale.  The rip is a tall
gun (wide pale hood 2.7 px above the bore).  ADS rule (kit adscheck): nothing behind the front third may rise above
the gnawing body top (12.04 / 12.23 / 12.06 / 11.9 / 11.32 from front to stock), so:
  * everything above y 10.6 is compressed to 53% height and the gun lowered 0.25 px -> hood top 12.12;
  * the stock (behind z 9) is additionally compressed to 92% about y 8.1 -> stock top 11.42 (gnawing 11.32 + 0.15 tol);
  * the hood stops at z 8 where the gnawing top drops.
The only parts above the profile are the hollow reflex sight frame (sight_*), whose 0.48 x 0.52 px window surrounds
the ADS aim point y 12.785 (W151 sightCenter 12.95 - 0.165, as on W302 Khvostov), and its foot directly below it.
Front of z -6 compressed 7% (muzzle -9.3 vs -9.54), stock behind z 11 stretched 18% (butt 15.05 vs 15.44).
NO_OVERLAY + red reticle geometry.  Detail pass: chamfered hood/nose/stock edges, ribbed fore-end pad, proud bands,
flat-painted faces where the projection smears (detail.Cleaner).
"""
import math, sys, types
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts/art/w325'))
import kit
from detail import chamfer, chamfer_seg, Cleaner, Flat, blob
import re

S = 25.4
YOFF = -0.33
ZOFF = -0.68 + 9.54 / 25.4
DY, YA, KY = 0.25, 10.6, 0.53
KS = 0.917                           # extra stock compression about y 8.1
FZ, FK = -6.0, 3.54 / 3.79
RS, RK = 11.0, 1.18
EYE = 12.785
LENS_R, LENS_Z = 14.13, 6.95       # rip lens centre (rip-frame y, model z)
NO_OVERLAY = True
T = 20
ATLAS = 1024  # atlas crops to 1024x512; 20px/unit keeps the near-camera panel / optic lines crisp
OCC_TOL = 0.02
RETICLE = (225, 52, 40, 255)


def N(y_old):
    """first-pass model y (hood at 66%, knee y 11) -> current model y (keeps all contract positions below y 10.6)"""
    r = y_old + .25 if y_old <= 11 else 11.25 + (y_old - 11) / .66
    return round(r - DY if r <= YA + DY else YA + (r - YA - DY) * KY, 4)


def NS(y_old):
    return round(8.1 + (N(y_old) - 8.1) * KS, 4)


def y2r(y):
    return y + DY if y <= YA else YA + DY + (y - YA) / KY


def z2r(z):
    if z < FZ: return FZ + (z - FZ) / FK
    if z > RS: return RS + (z - RS) / RK
    return z


def base_name(name):
    for suf in ('_bevel_', '_crown', '_keel'):
        if suf in name: name = name.split(suf)[0]
    return re.sub(r'_s\d+$', '', name)


def model2world(name, p):
    x, y, z = p
    name = base_name(name)
    if name.startswith('sight_') or name.startswith('reticle'):
        r = LENS_R + (y - EYE) * 0.8; x = 8 + (x - 8) * 0.8; zr = LENS_Z + (z - 7.0) * 0.5
        return (-(x - 8.0) / S, zr / S + ZOFF, r / S + YOFF)
    if name.startswith(('stock_', 'butt_')):
        y = 8.1 + (y - 8.1) / KS
    return (-(x - 8.0) / S, z2r(z) / S + ZOFF, y2r(y) / S + YOFF)


def box(name, lo, hi, **kw):
    e = {'name': name, 'from': [round(v, 5) for v in lo], 'to': [round(v, 5) for v in hi]}; e.update(kw); return e


def rot(e, axis, ang, origin):
    e['rotation'] = {'origin': [round(v, 5) for v in origin], 'x': 0, 'y': 0, 'z': 0}; e['rotation'][axis] = round(ang, 4); return e


def slope(name, p0, p1, thick, x0, x1, side='below', ext=(0.0, 0.0)):
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dz, dy)
    ang = math.degrees(math.atan2(-dy, dz))
    mz, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    sh = (ext[1] - ext[0]) / 2; mz += dz / L * sh; my += dy / L * sh
    half = (L + ext[0] + ext[1]) / 2
    cy = my - thick / 2 if side == 'below' else my + thick / 2
    return rot(box(name, (x0, cy - thick / 2, mz - half), (x1, cy + thick / 2, mz + half)), 'x', ang, (8.0, my, mz))


B = 11.4                             # bore (first pass); N(B) is the current bore
HX0, HX1 = 7.13, 8.87               # hood width
LX0, LX1 = 7.5, 8.5                 # lower body / stock width


def front(E):
    b = N(B); h = N(B + .3) - b
    E.append(box('muzzle_top', (7.68, b + .1, -9.32), (8.32, b + h, -9.12)))
    E.append(box('muzzle_bottom', (7.68, b - .3, -9.32), (8.32, b - .1, -9.12)))
    E.append(box('muzzle_l', (7.68, b - .1, -9.32), (7.88, b + .1, -9.12)))
    E.append(box('muzzle_r', (8.12, b - .1, -9.32), (8.32, b + .1, -9.12)))
    E.append(box('muzzle_bore', (7.88, b - .1, -9.14), (8.12, b + .1, -9.12)))
    E += chamfer('muzzle_body', (7.68, b - .3, -9.12), (8.32, b + h, -8.55), .08, ('tl', 'tr', 'bl', 'br'))
    E += chamfer('nose', (LX0, 9.85, -8.55), (LX1, N(11.6), -7.4), .14)
    E += chamfer('nose_chin', (LX0, 9.75, -7.95), (LX1, 9.85, -7.4), .05, ('bl', 'br'))   # axis step under the nose
    E += chamfer('nose_low', (LX0, 9.65, -7.4), (LX1, N(11.6), -6.1), .12, ('bl', 'br'))
    E += chamfer_seg('handguard', (LX0, 9.4, -6.1), (LX1, N(11.6), 1.65), .14, ('bl', 'br'), cuts=(-5.4, 1.0), inset=.03)
    # black fore-end pad panel with vertical ribs (rip identity), slightly proud of the handguard
    E.append(box('pad_panel', (7.46, 9.55, -5.3), (8.54, 10.45, 0.9)))
    for i in range(8):
        z = -5.05 + i * 0.75
        E.append(box(f'pad_rib_{i}', (7.43, 9.62, z), (8.57, 10.38, z + .14)))


def hood(E):
    # hood nose: one axis-aligned step in front of the roof (no shallow rotated slab), same width as the roof
    E += chamfer('hood_nose', (HX0, N(11.55), -8.45), (HX1, N(11.88), -7.55), .12)
    E += chamfer_seg('hood_roof', (HX0, N(11.55), -7.55), (HX1, N(12.1), 8.0), .18, cuts=(-1.6, 1.9), inset=.04)
    for s, (a, b) in (('l', (HX0, HX0 + .18)), ('r', (HX1 - .18, HX1))):
        E.append(box(f'hood_skirt_{s}', (a, N(10.95), -7.3), (b, N(11.55), 7.8)))
    # ochre band: a proud strip along the hood flank (rip yellow stripe), both sides
    for s, (a, b) in (('l', (HX0 - .03, HX0 + .1)), ('r', (HX1 - .1, HX1 + .03))):
        E.append(box(f'hood_band_{s}', (a, N(11.55), -6.6), (b, N(11.75), 7.6)))
    E += chamfer('hood_crown_front', (7.4, N(12.1), -6.7), (8.62, N(12.35), -1.6), .1)
    E += chamfer('hood_crown_rear', (7.4, N(12.1), 1.9), (8.62, N(12.35), 8.0), .1)
    E.append(box('top_rail', (7.75, N(12.1), -1.6), (8.25, N(12.3), 1.9)))   # bridges the see-through slot
    for i in range(4):
        z = 2.4 + i * 0.9                                                         # rail notches (rip dashes)
        E.append(box(f'rail_lug_{i}', (7.62, N(12.3), z), (8.38, N(12.35) + .04, z + .4)))


def receiver(E):
    E += chamfer('receiver', (LX0, 9.2, 1.65), (LX1, N(11.6), 5.3), .12, ('bl', 'br'))
    E.append(box('receiver_plate', (7.46, 9.35, 1.95), (8.54, 10.7, 4.95)))     # pale mag-well plate
    E.append(box('receiver_button', (7.38, 9.65, 1.7), (8.62, 10.25, 2.3)))
    E.append(box('receiver_button_cap', (7.33, 9.78, 1.83), (8.67, 10.12, 2.17)))
    E.append(box('lower_rear', (LX0, 9.95, 5.3), (LX1, N(11.6), 9.0)))
    E.append(box('lower_slot', (7.47, N(10.8), 5.8), (8.53, N(11.0), 8.2)))       # dark side slot strip
    E.append(slope('guard_front', (5.25, 9.2), (5.75, 9.95), 0.3, 7.6, 8.4, side='above', ext=(.05, .05)))
    E.append(box('guard_bar', (7.88, 9.15, 5.55), (8.12, 9.3, 7.2)))
    E.append(box('trigger_blade', (7.92, 9.6, 6.2), (8.08, 9.95, 6.38)))
    E.append(rot(box('trigger_hook', (7.92, 9.2, 6.26), (8.08, 9.62, 6.4)), 'x', 25, (8.0, 9.6, 6.33)))
    gp = (8.0, 8.5, 8.4)
    E.append(rot(box('grip', (7.52, 6.95, 7.9), (8.48, 10.2, 8.95)), 'x', -17.6, gp))
    E.append(rot(box('grip_panel', (7.49, 7.5, 8.05), (8.51, 9.6, 8.8)), 'x', -17.6, gp))
    E.append(rot(box('grip_heel', (7.5, 6.95, 7.8), (8.5, 7.35, 9.15)), 'x', -17.6, gp))


def stock(E):
    E += chamfer('stock_main', (LX0, NS(10.25), 9.0), (LX1, NS(12.15), 14.75), .16, ('tl', 'tr'))
    E += chamfer('stock_drop_edge', (LX0, NS(9.3), 13.05), (LX1, NS(10.25), 13.55), .12, ('bl', 'br'))   # axis step (was a 58-degree slab)
    E += chamfer('stock_drop', (LX0, NS(8.1), 13.55), (LX1, NS(10.25), 14.75), .12, ('bl', 'br'))
    E.append(box('stock_recess', (7.46, NS(10.55), 9.6), (8.54, NS(11.35), 13.0)))  # dark recessed panel
    E += chamfer('butt_pad', (7.62, NS(8.7), 14.75), (8.38, NS(11.85), 15.05), .1, ('tl', 'tr', 'bl', 'br'))


def sight(E):
    z0, z1 = 6.6, 7.4
    fx, fy = 0.42, 0.42
    wx, wy = 0.24, 0.26
    E.append(box('sight_base', (7.65, N(12.35) - .02, 6.5), (8.35, EYE - fy + .02, 7.5)))
    E.append(box('sight_top', (8 - fx, EYE + wy, z0), (8 + fx, EYE + fy, z1)))
    E.append(box('sight_bottom', (8 - fx, EYE - fy, z0), (8 + fx, EYE - wy, z1)))
    E.append(box('sight_l', (8 - fx, EYE - wy, z0), (8 - wx, EYE + wy, z1)))
    E.append(box('sight_r', (8 + wx, EYE - wy, z0), (8 + fx, EYE + wy, z1)))
    zc = 6.75
    for n, (xa, ya, xb, yb) in {'reticle_dot': (7.985, EYE - .015, 8.015, EYE + .015),
                                 'reticle_l': (7.8, EYE - .01, 7.9, EYE + .01),
                                 'reticle_r': (8.1, EYE - .01, 8.2, EYE + .01)}.items():
        E.append(box(n, (xa, ya, zc - .01), (xb, yb, zc + .01), shade=False, light_emission=15))


def magazine(E):
    E += chamfer('mag_body', (7.55, 6.1, 2.25), (8.45, 9.25, 4.6), .08, ('bl', 'br'))
    E.append(box('mag_spine', (7.6, 6.35, 1.96), (8.4, 9.25, 2.25)))
    E.append(box('mag_window', (7.52, 6.6, 2.6), (8.48, 8.7, 4.25)))       # pale window panel (proud)


def elements():
    E = []
    front(E); hood(E); receiver(E); stock(E); sight(E); magazine(E)
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

MATERIALS = {'ivory_paint': {'kind': 'paint', 'color': (226, 210, 196), 'detail': 0.8, 'amp': 2.2, 'wear': False},
 'ochre_paint': {'kind': 'paint', 'color': (154, 145, 71), 'detail': 0.7, 'amp': 2.3, 'wear': False},
 'lower_metal': {'kind': 'metal', 'color': (83, 88, 81), 'detail': 1.0, 'amp': 6},
 'well_alloy': {'kind': 'metal', 'color': (141, 139, 122), 'detail': 0.8, 'amp': 6},
 'polymer': {'kind': 'polymer', 'color': (52, 56, 54), 'detail': 0.7, 'amp': 3},
 'rubber': {'kind': 'rubber', 'color': (17, 20, 18), 'detail': 0.5, 'amp': 3, 'plate': False, 'rim': 0.025},
 'ivory_magazine': {'kind': 'polymer', 'color': (218, 206, 192), 'detail': 0.7, 'amp': 3, 'field': 0.06},
 'steel': {'kind': 'steel', 'color': (160, 162, 150), 'detail': 0.6, 'amp': 6},
 'lens': {'kind': 'lens', 'color': (45, 73, 130)},
 'recess': {'kind': 'dark', 'color': (15, 19, 17), 'detail': 0.2},
 'emitter': {'kind': 'glow', 'color': (225, 52, 40)}}
MATERIAL_RULES = [('top_rail', 'steel'),
 ('rail_lug', 'steel'),
 ('reticle', 'emitter'),
 ('muzzle_bore', 'recess'),
 ('muzzle', 'steel'),
 ('hood_band', 'ochre_paint'),
 ('hood_skirt', 'ochre_paint'),
 ('hood_', 'ivory_paint'),
 ('pad_', 'rubber'),
 ('handguard', 'lower_metal'),
 ('nose', 'lower_metal'),
 ('top_rail', 'lower_metal'),
 ('rail_lug', 'lower_metal'),
 ('receiver_button_cap', 'steel'),
 ('receiver_button', 'well_alloy'),
 ('receiver_plate', 'well_alloy'),
 ('receiver', 'lower_metal'),
 ('lower_slot', 'recess'),
 ('lower_', 'lower_metal'),
 ('guard', 'steel'),
 ('trigger', 'steel'),
 ('grip_panel', 'rubber'),
 ('grip', 'polymer'),
 ('stock_recess', 'polymer'),
 ('stock_drop', 'ivory_paint'),
 ('stock_', 'lower_metal'),
 ('butt', 'rubber'),
 ('sight', 'lower_metal'),
 ('mag_spine', 'well_alloy'),
 ('mag_', 'ivory_magazine')]

def material(name,face):
    inner={'sight_top':'down','sight_bottom':'up','sight_l':'east','sight_r':'west','sight_scope_top':'down','sight_scope_bottom':'up','sight_scope_l':'east','sight_scope_r':'west','sight_scope_ring_top':'down','sight_scope_ring_bottom':'up','sight_scope_ring_l':'east','sight_scope_ring_r':'west'}
    if inner.get(name)==face or name.startswith(('sight_tube','sight_eyecup')) and face=='down':return _surface('recess',name,face)
    if name in ('sight_top','sight_bottom','sight_l','sight_r') and face in ('north','south'):return _surface('lens',name,face)
    if name.startswith('stock_main') and face=='up':return _surface('ivory_paint',name,face)
    key=next((key for pre,key in MATERIAL_RULES if name.startswith(pre)), 'recess')
    return _surface(key,name,face)

def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if n.startswith('reticle'):return RETICLE
    if n.startswith(('hood_roof','hood_crown','hood_nose')) or n.startswith('stock_main') and y>NS(11.65):
        c=source_colour(e,fn,s,t)
        if c and 100<sum(c[:3])/3<208 and c[1]>c[2]+5:return accent_paint(e,fn,s,t,(171,175,149))
        if n.startswith('stock_main') and fn in ('east','west'):return accent_paint(e,fn,s,t,(223,210,192))
    if n in ('sight_top','sight_bottom') and fn=='south' and .15<s<.25 and .1<t<.35:return (124,163,224,255)
    return None

# R2 source-based sparse motif, separate from automatic material grain.
_special_material_r1 = special
def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if n=='pad_panel' and fn in ('east','west') and 9.67<y<10.3:
        if any(abs(z-(-4.86+i*.75))<.025 for i in range(8)):return (48,53,46,255)
    if n=='receiver_button_cap' and fn in ('east','west'):
        i,j,w,h=face_pixels(e,fn,s,t,T);r=((i-(w-1)/2)**2+(j-(h-1)/2)**2)**.5
        if abs(r-min(w,h)*.31)<.55:return (209,211,191,255)
    return _special_material_r1(e,fn,s,t)
