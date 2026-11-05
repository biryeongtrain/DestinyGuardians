"""W325 Pariah (common auto rifle, Precision frame) on the ammit_ar2 layout contract.

Model px: muzzle -z, up +y, gun right +x, centred x=8.  The rip (Pariah.blend, read-only) is mapped uniformly at
25.06 px/m (muzzle -8.99, contract -9.04) with the stock stretched 5% behind z 11 so the butt meets the contract
15.92; the gun sits so the handguard belly is y 10.0 and the pistol grip lands on the ammit grip box.  The small
round reflex sight is enlarged (rip dia 0.78 -> 1.1 px) and raised 0.855 px on a riser so its centre is on the
ammit ADS eye line (sightCenter y 14.0 - 0.165 = 13.835, same offset as the W302 Khvostov reticle); NO_OVERLAY with
a green reticle drawn as geometry.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts/art/w325'))
import kit
from detail import chamfer, chamfer_seg, engrave, Cleaner, Flat
import re
import types

S = 25.06                      # model px per metre (rip)
YOFF = -0.3281                 # rip z (up) at model y 0 (bore 10.96, handguard belly 10.0)
ZOFF = -0.3309                 # rip y (length) at model z 0; muzzle lands on -8.99 (contract -9.04)
ZS, KS = 11.0, 1.0513          # stock stretched behind z 11 so the butt reaches the contract 15.92
EYE = 13.835                   # ammit ADS eye line (W151 sightCenter 14.0 - 0.165)
RIP_SIGHT = 12.98              # rip lens centre in this frame
SIGHT_UP = EYE - RIP_SIGHT
SC = (2.6, 3.4)                # sight tube z
R_OUT, WALL = 0.55, 0.12
NO_OVERLAY = True
MAG_DZ = 0.6                   # magazine moved 0.6 forward toward the ammit magazine box (rip mag is aft) ...
LOWER = ('rcv_well', 'rcv_well_rear', 'rcv_well_back', 'mag_release', 'mag_release_knob')
LK = (5.95 - 2.4) / (5.95 - 1.8)   # ... and the lower receiver (magwell..guard) compressed so its front moves 0.6 too


def L(zr):
    """rip-frame z of the lower receiver -> model z"""
    return zr if zr >= 5.95 else 1.8 + (zr - 2.4) / LK
T = 20
RETICLE = (110, 235, 95, 255)


def z2w(z):
    if z > ZS: z = ZS + (z - ZS) / KS
    return z / S + ZOFF


def base_name(name):
    for suf in ('_bevel_', '_crown', '_keel'):
        if suf in name: name = name.split(suf)[0]
    return re.sub(r'_s\d+$', '', name)


def part_transform(name, p):
    x, y, z = p
    name = base_name(name)
    if name.startswith('sight_tube') or name.startswith('reticle'):
        # enlarged tube: scale about the eye-line centre back to the rip lens size, then lower to the rip lens
        k = 0.78 / (2 * R_OUT)
        return (8 + (x - 8) * k, RIP_SIGHT + (y - EYE) * k, z)
    if name in LOWER or name == 'rcv_plate':
        return (x, y, z if z >= 5.95 else 2.4 + (z - 1.8) * LK)
    if name.startswith('mag_'):
        return (x, y, z + MAG_DZ)
    if name.startswith('rail_'):
        return (x, 10.45 + (y - 10.45) * 0.6575 if y < 10.45 else y, z)
    if name == 'sight_riser':
        # riser samples the rip mount strip just under the tube
        return (x, 12.3 + (y - 12.6) * 0.25, z)
    return p


def model2world(name, p):
    x, y, z = part_transform(name, p)
    return (-(x - 8.0) / S, z2w(z), y / S + YOFF)


def box(name, lo, hi, **kw):
    e = {'name': name, 'from': list(lo), 'to': list(hi)}
    e.update(kw); return e


def rot(e, axis, ang, origin):
    e['rotation'] = {'origin': list(origin), 'x': 0, 'y': 0, 'z': 0}; e['rotation'][axis] = ang
    return e


def slope(name, p0, p1, thick, x0, x1, side='below', ext=(0.0, 0.0)):
    """Box whose top (side='below') or bottom (side='above') face lies on the (z,y) line p0->p1."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dz, dy)
    ang = math.degrees(math.atan2(-dy, dz))          # rotation about +x that tilts +z toward the line
    mz, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    sh = (ext[1] - ext[0]) / 2; mz += dz / L * sh; my += dy / L * sh
    half = (L + ext[0] + ext[1]) / 2
    cy = my - thick / 2 if side == 'below' else my + thick / 2
    return rot(box(name, (x0, cy - thick / 2, mz - half), (x1, cy + thick / 2, mz + half)), 'x', round(ang, 4), (8.0, my, mz))


BORE = 10.96


def front(E):
    b = BORE
    # muzzle brake with a real bore at the tip
    E.append(box('brake_lip_top', (7.73, b + .1, -8.99), (8.27, b + .27, -8.78)))
    E.append(box('brake_lip_bottom', (7.73, b - .27, -8.99), (8.27, b - .1, -8.78)))
    E.append(box('brake_lip_l', (7.73, b - .1, -8.99), (7.9, b + .1, -8.78)))
    E.append(box('brake_lip_r', (8.1, b - .1, -8.99), (8.27, b + .1, -8.78)))
    E.append(box('brake_bore', (7.9, b - .1, -8.8), (8.1, b + .1, -8.78)))
    E.append(box('brake_body', (7.73, b - .27, -8.78), (8.27, b + .27, -7.9)))
    for k, z in (('a', -8.62), ('b', -8.2)):                 # raised brake rings (rip fins)
        E.append(box(f'brake_ring_{k}', (7.69, b - .31, z), (8.31, b + .31, z + .12)))
    E.append(box('brake_neck', (7.77, b - .22, -7.9), (8.23, b + .22, -7.65)))
    E += chamfer('barrel_collar', (7.7, b - .27, -7.65), (8.3, b + .38, -6.45), .1, ('tl', 'tr', 'bl', 'br'))
    E.append(box('barrel', (7.8, b - .19, -6.45), (8.2, b + .19, -5.6)))
    E.append(box('gas_tube', (7.9, 11.22, -6.3), (8.1, 11.34, -5.6)))
    # handguard: long dark shroud, slanted nose, toothed lower rail, belly dip toward the magwell
    E += chamfer_seg('hg_main', (7.35, 10.45, -4.65), (8.65, 12.07, 0.6), .22, cuts=(-4.2, -0.2))
    E += chamfer('hg_nose', (7.35, 10.45, -5.55), (8.65, 11.62, -4.6), .15)
    E.append(slope('hg_nose_slope', (-5.6, 11.6), (-4.6, 12.07), 0.5, 7.35, 8.65, ext=(0, .05)))
    E += chamfer('hg_nose_plate', (7.3, 10.6, -5.95), (8.7, 11.45, -5.55), .08, ('tl', 'tr', 'bl', 'br'))
    # lower rail deepened 0.25 px toward the ammit fore-end (support hand); teeth keep the rip pitch
    E.append(box('rail_base', (7.42, 9.95, -5.5), (8.58, 10.45, -0.6)))
    for i in range(10):
        z = -5.42 + i * 0.47
        E.append(box(f'rail_tooth_{i}', (7.45, 9.72, z), (8.55, 9.95, z + .26)))
    E.append(box('hg_belly', (7.38, 9.5, -0.6), (8.62, 10.45, 0.95)))
    E.append(box('hg_belly_front', (7.38, 9.72, -1.1), (8.62, 10.45, -0.6)))   # axis-aligned step (was a thin rotated strip)
    E.append(box('hg_belly_rear', (7.38, 9.75, 0.95), (8.62, 10.45, 1.3)))


def receiver(E):
    # olive receiver: top cover strip with two see-through gaps under it, magwell block, rear chamfer
    E += chamfer_seg('rcv_cover', (7.36, 11.6, 0.6), (8.64, 12.07, 8.2), .15, cuts=(2.45, 6.0))
    E += chamfer('rcv_cover_tail', (7.36, 11.6, 8.2), (8.64, 11.85, 8.55), .08)   # stepped tail flush with cover/body
    E += chamfer('rcv_front', (7.36, 10.0, 0.6), (8.64, 11.25, 3.9), .12, ('bl', 'br'))
    E.append(box('rcv_plate', (7.31, 9.35, L(2.55)), (8.69, 10.85, L(4.45))))   # mag-well window plate (proud)
    E.append(box('rcv_post', (7.4, 11.25, 1.9), (8.6, 11.6, 2.35)))
    E.append(box('rcv_body', (7.35, 10.3, 3.9), (8.65, 11.6, 8.55)))
    E.append(box('rcv_well', (7.35, 8.68, L(2.4)), (8.65, 10.3, L(5.0))))
    E.append(slope('rcv_well_rear', (L(4.95), 8.7), (5.95, 9.35), 0.6, 7.35, 8.65, side='above', ext=(0, .1)))
    E.append(box('rcv_well_back', (7.35, 9.35, L(5.0)), (8.65, 10.3, 5.95)))
    E.append(box('rcv_lower', (7.4, 9.95, 5.95), (8.6, 10.3, 8.75)))
    E.append(box('charging_handle', (6.68, 11.0, 7.12), (7.36, 11.26, 7.32)))
    # mag release lever (both sides) and its knob
    E.append(box('mag_release', (7.22, 9.47, L(4.35)), (8.73, 9.83, L(5.3))))
    E.append(box('mag_release_knob', (7.24, 9.28, L(5.25)), (8.71, 10.02, L(5.82))))
    # silver trigger guard loop (open) and trigger
    E.append(box('guard_bottom', (7.9, 8.95, 6.0), (8.1, 9.1, 7.25)))
    E.append(box('guard_front', (7.9, 9.05, 5.85), (8.1, 9.95, 6.02)))
    E.append(box('guard_rear', (7.9, 9.05, 7.2), (8.1, 9.95, 7.37)))
    E.append(box('trigger_blade', (7.93, 9.6, 6.62), (8.07, 9.95, 6.78)))
    E.append(rot(box('trigger_hook', (7.93, 9.25, 6.7), (8.07, 9.65, 6.84)), 'x', 25, (8.0, 9.62, 6.77)))


def sight(E):
    z0, z1 = SC
    # grey mount with rear ear, narrow riser up to the raised tube
    E.append(box('mount_base', (7.5, 12.07, 2.6), (8.5, 12.6, 5.1)))
    E.append(box('mount_ear', (7.5, 12.07, 5.1), (8.5, 12.78, 5.5)))
    E.append(box('mount_knob', (7.22, 12.18, 3.7), (7.5, 12.5, 4.3)))
    E.append(box('sight_riser', (7.72, 12.6, 2.72), (8.28, EYE - R_OUT + .05, 3.28)))
    # octagonal tube: 8 staves around the eye line (real open aperture)
    side = 2 * R_OUT * math.tan(math.radians(22.5))   # exact octagon: stave outer corners meet
    for k in range(8):
        e = box(f'sight_tube_{k}', (8 - side / 2, EYE + R_OUT - WALL, z0), (8 + side / 2, EYE + R_OUT, z1))
        if k: rot(e, 'z', k * 45, (8.0, EYE, (z0 + z1) / 2))
        E.append(e)
    # green reticle geometry on the tube mid-plane (no W148 overlay dot)
    zc = (z0 + z1) / 2
    for n, (xa, ya, xb, yb) in {'reticle_dot': (7.985, EYE - .015, 8.015, EYE + .015),
                                 'reticle_l': (7.66, EYE - .01, 7.8, EYE + .01),
                                 'reticle_r': (8.2, EYE - .01, 8.34, EYE + .01)}.items():
        E.append(box(n, (xa, ya, zc - .01), (xb, yb, zc + .01), shade=False, light_emission=15))


def rear(E):
    # raked pistol grip with flared base; top buried in the receiver floor
    gp = (8.0, 8.5, 8.52)
    E.append(rot(box('grip_core', (7.45, 6.85, 7.86), (8.6, 10.3, 9.2)), 'x', -18.4, gp))
    E.append(rot(box('grip_panel', (7.41, 7.4, 8.0), (8.64, 9.7, 9.05)), 'x', -18.4, gp))   # wrapped grip panel
    E.append(rot(box('grip_base', (7.42, 6.85, 7.75), (8.63, 7.35, 9.35)), 'x', -18.4, gp))
    # skeleton stock: top bar, sloped lower strut, centre web, rear lower block, butt + slanted pad (two real holes)
    X0, X1 = 7.42, 8.58
    E += chamfer_seg('stock_top', (X0, 10.75, 8.55), (X1, 11.4, 14.55), .15, ('tl', 'tr', 'bl', 'br'), cuts=(12.12, 12.75))
    E.append(slope('stock_strut', (9.3, 8.1), (15.4, 7.27), 0.62, X0, X1, side='above'))
    E.append(box('stock_web', (X0, 8.0, 12.12), (X1, 10.75, 12.75)))
    E += chamfer('stock_block', (X0, 7.5, 12.75), (X1, 9.05, 14.55), .12, ('bl', 'br'))
    E += chamfer('stock_butt', (X0, 7.32, 14.55), (X1, 11.4, 15.3), .15, ('tl', 'tr', 'bl', 'br'))
    # rounded window corners of the skeleton stock (45-degree gussets, rip fillets)
    for n, (cy, cz) in {'a': (10.75, 12.12), 'b': (10.75, 12.75), 'c': (10.75, 14.55), 'd': (9.05, 14.55), 'e': (9.05, 12.75)}.items():
        E.append(rot(box(f'stock_fillet_{n}', (X0 + .01, cy - .16, cz - .16), (X1 - .01, cy + .16, cz + .16)), 'x', 45, (8.0, cy, cz)))
    E.append(box('butt_pad', (7.45, 7.32, 15.3), (8.55, 11.4, 15.75)))   # axis-aligned (no 3-degree skew)


def magazine(E):
    d = MAG_DZ
    E.append(box('mag_body', (7.55, 7.0, 2.5 - d), (8.45, 8.7, 4.5 - d)))
    for k, z in (('a', 3.0), ('b', 3.75)):                  # side ribs of the rip magazine
        E.append(box(f'mag_rib_{k}', (7.5, 7.15, z - d), (8.5, 8.6, z + .22 - d)))
    E += chamfer('mag_plate', (7.48, 6.3, 2.2 - d), (8.52, 7.08, 4.65 - d), .1, ('bl', 'br'))   # axis-aligned base plate


def elements():
    E = []
    front(E); receiver(E); sight(E); rear(E); magazine(E)
    return E


def open_shroud(E):
    result=[]
    for e in E:
        if e['name'] != 'hg_main': result.append(e); continue
        lo,hi=e['from'],e['to']
        result.append(box('hg_main_floor',lo,(hi[0],11.3,hi[2])))
        result.append(box('hg_main_roof',(lo[0],11.5,lo[2]),hi))
        for i,(a,b) in enumerate(((lo[2],-4.35),(-3.45,-3.15),(-2.2,hi[2]))):
            result.append(box('hg_main_web_'+str(i),(lo[0],11.3,a),(hi[0],11.5,b)))
    return result


_elements_original = elements
def elements():
    return open_shroud(_elements_original())


def is_magazine(name):
    return name.startswith('mag_') and name not in LOWER


SLOTS = ((-4.35, -3.45), (-3.15, -2.2))



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

MATERIALS = {'olive_paint': {'kind': 'paint',
                 'color': (88, 89, 48),
                 'detail': 1.1,
                 'amp': 2.5,
                 'wear': (165, 166, 149)},
 'blued_steel': {'kind': 'steel', 'color': (83, 89, 92), 'detail': 0.8, 'amp': 7},
 'satin_aluminium': {'kind': 'metal', 'color': (157, 160, 156), 'detail': 0.65, 'amp': 6},
 'handguard_polymer': {'kind': 'polymer', 'color': (52, 56, 54), 'detail': 0.8, 'amp': 3},
 'grip_brown_wrap': {'kind': 'cloth', 'color': (110, 72, 46), 'detail': 0.9, 'amp': 6},
 'butt_rubber': {'kind': 'rubber',
                 'color': (17, 20, 18),
                 'detail': 0.45,
                 'amp': 3,
                 'plate': False,
                 'rim': 0.025},
 'optic_grey': {'kind': 'metal', 'color': (104, 109, 108), 'detail': 0.3, 'amp': 5},
 'optic_green': {'kind': 'lens', 'color': (62, 116, 75)},
 'recess': {'kind': 'dark', 'color': (17, 20, 20), 'detail': 0.2},
 'emitter': {'kind': 'glow', 'color': (110, 235, 95)},
 'shroud_steel': {'kind': 'metal',
                  'color': (48, 53, 54),
                  'detail': 0.65,
                  'amp': 3,
                  'field': 0.035,
                  'wear': False}}
MATERIAL_RULES = [('hg_main', 'shroud_steel'),
 ('hg_nose', 'shroud_steel'),
 ('rcv_lower', 'blued_steel'),
 ('rcv_post', 'blued_steel'),
 ('rcv_well_back', 'blued_steel'),
 ('rcv_well_rear', 'blued_steel'),
 ('reticle', 'emitter'),
 ('brake_bore', 'recess'),
 ('grip_panel', 'grip_brown_wrap'),
 ('grip_base', 'butt_rubber'),
 ('grip_', 'handguard_polymer'),
 ('butt_', 'butt_rubber'),
 ('rcv_', 'olive_paint'),
 ('charging', 'satin_aluminium'),
 ('mag_release', 'satin_aluminium'),
 ('guard', 'satin_aluminium'),
 ('trigger', 'blued_steel'),
 ('hg_', 'handguard_polymer'),
 ('rail_', 'blued_steel'),
 ('stock_', 'blued_steel'),
 ('brake', 'blued_steel'),
 ('barrel', 'blued_steel'),
 ('gas_', 'blued_steel'),
 ('sight_', 'optic_grey'),
 ('mount_', 'optic_grey'),
 ('mag_', 'blued_steel')]

def material(name,face):
    inner={'sight_top':'down','sight_bottom':'up','sight_l':'east','sight_r':'west','sight_scope_top':'down','sight_scope_bottom':'up','sight_scope_l':'east','sight_scope_r':'west','sight_scope_ring_top':'down','sight_scope_ring_bottom':'up','sight_scope_ring_l':'east','sight_scope_ring_r':'west'}
    if inner.get(name)==face or name.startswith(('sight_tube','sight_eyecup')) and face=='down':return _surface('recess',name,face)
    if name.startswith('sight_tube') and face in ('north','south'):return _surface('optic_green',name,face)
    key=next((key for pre,key in MATERIAL_RULES if name.startswith(pre)), 'recess')
    return _surface(key,name,face)

def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if n.startswith('reticle'):return RETICLE
    if fn in ('east','west'):
        if n.startswith('rcv_') and (line2(z,y,[(6.28,10.65),(6.56,10.93)],.04) or line2(z,y,[(6.28,10.93),(6.56,10.65)],.04)):return (39,43,26,255)
        if n=='rcv_plate' and (min(s,1-s)<.065 or min(t,1-t)<.075):return (151,157,147,255)
    if n.startswith('sight_tube') and fn=='south' and .14<s<.24 and .15<t<.25:return (162,211,159,255)
    return None

# R2 source-based sparse motif, separate from automatic material grain.
_special_material_r1 = special
def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if n=='grip_panel' and fn in ('east','west'):
        i,j,w,h=face_pixels(e,fn,s,t,T)
        if 2<i<w-3 and 2<j<h-3 and (i+j)%13==0:return (151,106,74,255)
    return _special_material_r1(e,fn,s,t)
