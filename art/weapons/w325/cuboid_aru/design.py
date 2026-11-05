"""W325 Cuboid ARu (rare auto rifle, Precision frame) on the ammit_ar2 layout contract.

Model px: muzzle -z, up +y, gun right +x, centred x=8.  Rip (Cuboid ARu.blend, read-only) mapped at 23.97 px/m and
shifted 1.16 px forward so the skeleton pistol grip lands on the ammit grip box; the long perforated suppressor front
is compressed 7% (muzzle -9.5, contract -9.04) and the stock behind z 11 stretched 15% (butt 15.25, contract 15.92).
Height: the reflex window centre falls on the ammit ADS eye line y 13.835 with no riser.  The rip's sight material is
missing (magenta); it is regraded to dark gunmetal.  NO_OVERLAY + green reticle geometry like W302 Khvostov.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts/art/w325'))
import kit
from detail import chamfer, chamfer_seg, engrave, Cleaner, Flat
import re
import types

S = 23.97
YOFF = -0.3408
ZOFF = -0.4015
SH, FK, RS, RK = 1.16, 0.92667, 11.0, 1.15
EYE = 13.835
SK = 1.25                          # sight enlarged about the window centre
MAG_DZ = 0.6                       # magazine moved forward toward the ammit magazine box
NO_OVERLAY = True
T = 20
ATLAS = 1024  # atlas crops to 1024x512; 20px/unit keeps the near-camera panel / optic lines crisp
OCC_TOL = 0.035                    # rip side relief up to ~0.8 px proud of the authored faces still projects
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
        return (8 + (x - 8) / SK, EYE + (y - EYE) / SK, z)
    if name.startswith('mag_'):
        return (x, y, z + MAG_DZ)
    if name == 'frame_post':          # post widened forward to close the gap behind the moved magazine
        return (x, y, 5.0 + (z - 4.35) * (0.75 / 1.4))
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


def roundbar(E, name, z0, z1, cy, r, k=0.72):
    """two crossed boxes: reads round from the side, top and three-quarter views"""
    E.append(box(name, (8 - r, cy - r * k, z0), (8 + r, cy + r * k, z1)))
    E.append(box(name + '_v', (8 - r * k, cy - r, z0), (8 + r * k, cy + r, z1)))


BORE = 11.27


def front(E):
    b = BORE
    E.append(box('cap_top', (7.64, b + .13, -9.5), (8.36, b + .36, -9.3)))
    E.append(box('cap_bottom', (7.64, b - .36, -9.5), (8.36, b - .13, -9.3)))
    E.append(box('cap_l', (7.64, b - .13, -9.5), (7.87, b + .13, -9.3)))
    E.append(box('cap_r', (8.13, b - .13, -9.5), (8.36, b + .13, -9.3)))
    E.append(box('cap_bore', (7.87, b - .13, -9.32), (8.13, b + .13, -9.3)))
    for side,(x0,x1) in enumerate(((7.6,7.74),(8.26,8.4))):
        for row,(ya,yb) in enumerate(((-.4,-.24),(-.055,.055),(.24,.4))):
            E.append(box(f'suppressor_rail_{side}_{row}',(x0,b+ya,-9.3),(x1,b+yb,-6.85)))
    for i in range(6):
        a=-9.3+i*.445; z=min(-6.85,a+.225)
        E.append(box(f'suppressor_ring_top_{i}',(7.74,b+.24,a),(8.26,b+.4,z)))
        E.append(box(f'suppressor_ring_bottom_{i}',(7.74,b-.4,a),(8.26,b-.24,z)))
        for side,(x0,x1) in enumerate(((7.6,7.74),(8.26,8.4))):
            for row,(ya,yb) in enumerate(((-.24,-.055),(.055,.24))):
                E.append(box(f'suppressor_web_{i}_{side}_{row}',(x0,b+ya,a),(x1,b+yb,z)))
    E.append(box('suppressor_taper', (7.73, b - .24, -6.85), (8.27, b + .24, -6.35)))
    roundbar(E, 'collar', -6.35, -5.7, b, .35)
    # front sleeve with bumped top and the tan cap of the shroud
    E += chamfer('sleeve', (7.5, 10.75, -5.7), (8.5, 11.8, -2.45), .12, ('tl', 'tr', 'bl', 'br'))
    E += chamfer('sleeve_top', (7.55, 11.8, -5.62), (8.45, 12.05, -2.45), .08)
    for k, z in (('a', -5.45), ('b', -3.2)):                # tan clamp bands of the front sleeve
        E.append(box(f'sleeve_band_{k}', (7.46, 10.71, z), (8.54, 11.84, z + .3)))


def shroud(E):
    E += chamfer('hg_low', (7.33, 10.6, -2.45), (8.67, 11.12, 5.0), .12, ('bl', 'br'))
    E += chamfer_seg('hg_mid', (7.33, 11.12, -2.45), (8.67, 12.12, 5.0), .0001, (), cuts=(1.3, 3.3), inset=.04)
    E += chamfer_seg('hg_top', (7.33, 12.6, -2.5), (8.67, 13.12, 5.0), .16, cuts=(-0.3, 3.3))
    E.append(box('hg_end_cap', (7.3, 10.58, -2.62), (8.7, 13.0, -2.45)))     # tan front cap of the shroud
    E.append(box('hg_bridge_front', (7.33, 12.12, -2.5), (8.67, 12.6, -0.3)))
    E.append(box('hg_bridge_rear', (7.33, 12.12, 3.3), (8.67, 12.6, 5.0)))
    E.append(box('rail_lower', (7.45, 10.35, -0.3), (8.55, 10.6, 1.65)))
    E += chamfer('fore_block', (7.42, 9.2, -1.85), (8.58, 10.35, 1.42), .14, ('bl', 'br'))
    for k, z in enumerate((-1.2, -0.62, -0.04, 0.54)):        # black grip pad ribs (rip pad panel)
        E.append(box(f'fore_pad_{k}', (7.38, 9.38, z), (8.62, 9.95, z + .36)))
    E.append(box('knob', (8.67, 11.35, 2.0), (8.8, 11.85, 2.6)))


def receiver(E):
    E += chamfer('rcv_upper', (7.25, 11.85, 5.0), (8.75, 13.15, 8.0), .2)
    E.append(box('rcv_dial', (8.75, 12.05, 6.35), (8.88, 12.65, 6.95)))     # receiver dial (rip roundel)
    # receiver tail as two axis-aligned chamfered steps (was a rotated slab whose edges crossed the receiver)
    E += chamfer('rcv_tail', (7.25, 11.85, 8.0), (8.75, 12.65, 8.5), .15)
    E += chamfer('rcv_tail_low', (7.25, 11.85, 8.5), (8.75, 12.15, 8.95), .1)
    E.append(box('rcv_body', (7.25, 10.4, 5.0), (8.75, 11.85, 10.2)))
    E.append(box('rcv_rail', (7.4, 11.85, 8.0), (8.6, 12.15, 10.4)))
    E += chamfer('magwell', (7.25, 8.8, 2.1), (8.75, 10.45, 5.0), .12, ('bl', 'br'))
    E.append(box('rcv_lower', (7.3, 9.6, 5.0), (8.7, 10.4, 9.6)))
    E.append(box('frame_post', (7.4, 6.45, 4.35), (8.6, 9.6, 5.75)))
    E.append(box('guard_bar', (7.45, 8.55, 5.75), (8.55, 8.95, 8.2)))
    E.append(box('guard_front', (7.45, 8.95, 5.75), (8.55, 9.6, 6.15)))
    E.append(slope('frame_bar', (5.45, 6.9), (8.75, 7.5), 0.45, 7.45, 8.55, ext=(0, .2)))
    E.append(box('trigger_blade', (7.92, 9.25, 7.05), (8.08, 9.6, 7.25)))
    E.append(rot(box('trigger_hook', (7.92, 8.95, 7.1), (8.08, 9.3, 7.26)), 'x', 25, (8.0, 9.28, 7.18)))
    gp = (8.0, 8.6, 8.95)
    E.append(rot(box('grip', (7.4, 7.1, 8.25), (8.6, 10.1, 9.65)), 'x', -14.3, gp))
    E.append(rot(box('grip_heel', (7.38, 7.1, 8.15), (8.62, 7.6, 9.85)), 'x', -14.3, gp))


def sight(E):
    z0, z1 = 5.8, 8.15
    fx, fy = 0.6, 0.6                 # frame half sizes
    wx, wy = 0.36, 0.28               # window half sizes
    E.append(box('sight_top', (8 - fx, EYE + wy, z0), (8 + fx, EYE + fy, z1)))
    E.append(box('sight_bottom', (8 - fx, EYE - fy, z0), (8 + fx, EYE - wy, z1)))
    E.append(box('sight_l', (8 - fx, EYE - wy, z0), (8 - wx, EYE + wy, z1)))
    E.append(box('sight_r', (8 + wx, EYE - wy, z0), (8 + fx, EYE + wy, z1)))
    E.append(box('sight_base', (7.55, 13.1, 6.0), (8.45, EYE - fy + .02, 7.9)))
    zc = 7.6
    for n, (xa, ya, xb, yb) in {'reticle_dot': (7.985, EYE - .015, 8.015, EYE + .015),
                                 'reticle_l': (7.72, EYE - .01, 7.84, EYE + .01),
                                 'reticle_r': (8.16, EYE - .01, 8.28, EYE + .01)}.items():
        E.append(box(n, (xa, ya, zc - .01), (xb, yb, zc + .01), shade=False, light_emission=15))


def stock(E):
    X0, X1 = 7.3, 8.7
    E.append(box('stock_rail', (7.4, 11.65, 10.2), (8.6, 12.0, 14.2)))
    E += chamfer_seg('stock_bar', (X0, 10.85, 10.2), (X1, 11.65, 14.6), .12, ('tl', 'tr'), cuts=(11.6, 13.6))
    E.append(box('stock_strip', (7.4, 10.55, 10.2), (8.6, 10.85, 11.6)))
    E.append(box('stock_tab', (7.38, 10.1, 11.6), (8.62, 10.85, 12.2)))
    E.append(slope('stock_plate', (11.6, 10.1), (14.0, 9.15), 1.2, 7.38, 8.62, side='above', ext=(0, .05)))
    E.append(box('stock_plate_rear', (7.38, 9.1, 13.6), (8.62, 10.85, 14.6)))
    E += chamfer('butt_pad', (7.35, 9.15, 14.6), (8.65, 12.3, 15.25), .15, ('tl', 'tr', 'bl', 'br'))
    E += chamfer('butt_hook', (7.35, 11.65, 14.2), (8.65, 12.3, 14.6), .12)   # axis step rail -> pad top


def magazine(E):
    d = MAG_DZ
    E.append(box('mag_body', (7.45, 6.4, 2.8 - d), (8.55, 8.8, 4.95 - d)))
    for k, z in (('a', 3.3), ('b', 4.05)):                  # curved-rib relief of the rip magazine
        E.append(box(f'mag_rib_{k}', (7.4, 6.6, z - d), (8.6, 8.6, z + .22 - d)))
    E.append(box('mag_base', (7.35, 5.6, 2.72 - d), (8.65, 6.45, 5.05 - d)))


def elements():
    E = []
    front(E); shroud(E); receiver(E); sight(E); stock(E); magazine(E)
    return E


def grade(rgb):
    r, g, b = rgb
    if r > g + 18 and b > g + 18:                             # rip's missing sight texture (magenta)
        v = 30 + max(0, r - 80) * 0.1
        return (int(v), int(v), int(v + 2))
    return kit.default_grade(rgb)



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

MATERIALS = {'maroon_paint': {'kind': 'paint',
                  'color': (107, 62, 65),
                  'detail': 1.1,
                  'amp': 2.5,
                  'wear': (190, 180, 156)},
 'sand_anodized': {'kind': 'metal', 'color': (158, 143, 119), 'detail': 0.9, 'amp': 6},
 'steel': {'kind': 'steel', 'color': (121, 127, 126), 'detail': 0.75, 'amp': 8},
 'gunmetal': {'kind': 'metal', 'color': (83, 88, 90), 'detail': 0.7, 'amp': 6},
 'polymer': {'kind': 'polymer', 'color': (52, 56, 54), 'detail': 0.7, 'amp': 3},
 'rubber': {'kind': 'rubber',
            'color': (17, 20, 18),
            'detail': 0.45,
            'amp': 3,
            'plate': False,
            'rim': 0.025},
 'optic': {'kind': 'metal', 'color': (83, 88, 90), 'detail': 0, 'amp': 4},
 'lens': {'kind': 'lens', 'color': (58, 106, 82)},
 'recess': {'kind': 'dark', 'color': (17, 19, 20), 'detail': 0.2},
 'emitter': {'kind': 'glow', 'color': (110, 235, 95)},
 'magazine_steel': {'kind': 'metal', 'color': (49, 55, 54), 'detail': 0.65, 'amp': 4, 'wear': False}}
MATERIAL_RULES = [('mag_body', 'magazine_steel'),
 ('rcv_tail_low', 'steel'),
 ('rcv_lower', 'steel'),
 ('hg_bridge_front', 'gunmetal'),
 ('hg_bridge_rear', 'gunmetal'),
 ('sight_base', 'steel'),
 ('guard', 'steel'),
 ('rail_lower', 'gunmetal'),
 ('reticle', 'emitter'),
 ('cap_bore', 'recess'),
 ('sight_', 'optic'),
 ('butt_', 'rubber'),
 ('grip', 'polymer'),
 ('fore_pad', 'rubber'),
 ('fore_', 'maroon_paint'),
 ('hg_end_cap', 'sand_anodized'),
 ('hg_low', 'steel'),
 ('hg_', 'maroon_paint'),
 ('sleeve_band', 'maroon_paint'),
 ('sleeve', 'sand_anodized'),
 ('collar', 'maroon_paint'),
 ('suppressor', 'gunmetal'),
 ('cap_', 'gunmetal'),
 ('knob', 'gunmetal'),
 ('rcv_dial', 'gunmetal'),
 ('rcv_body', 'steel'),
 ('rcv_rail', 'gunmetal'),
 ('rcv_', 'maroon_paint'),
 ('magwell', 'maroon_paint'),
 ('stock_strip', 'sand_anodized'),
 ('stock_tab', 'sand_anodized'),
 ('stock_rail', 'gunmetal'),
 ('stock_', 'maroon_paint'),
 ('frame_', 'gunmetal'),
 ('guard', 'gunmetal'),
 ('trigger', 'sand_anodized'),
 ('mag_rib', 'steel'),
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
    if fn in ('east','west'):
        if n.startswith(('hg_top','hg_mid')) and (abs(y-12.95)<.027 or abs(y-11.25)<.027):return (177,165,140,255)
        if n=='sleeve' and rim(z,y,-4.62,10.93,-3.5,11.58,.025):return (98,61,55,255)
    if n in ('sight_top','sight_bottom') and fn=='south' and .15<s<.25 and .1<t<.35:return (144,193,162,255)
    return None

# R2 source-based sparse motif, separate from automatic material grain.
_special_material_r1 = special
def special(e,fn,s,t):
    n=e['name'];x,y,z=kit.face_point(e,fn,s,t)
    if fn in ('east','west'):
        if n=='mag_body' and 6.68<y<8.48 and any(abs(z-a)<.024 for a in (2.63,2.94,3.38,3.69)):return (128,135,130,255)
        if n=='sleeve' and (-5.35<z<-4.65 or -3.08<z<-2.7) and (z+5.35)%.28<.045:return (83,81,70,255)
    return _special_material_r1(e,fn,s,t)
