"""W325 Allegro-34 (rare Adaptive hand cannon) over base austringer.  Authored in rip-image px (nx view) -> model px.
Calibration: rip cylinder centre (img 140,56.5) -> austringer cylinder centre (z 4.34, y 12.43); S 36 px/m, SX 38.
Detail pass (W325b): chamfered shroud/rail/guard edges, real bores (muzzle cap + main bore), crisp light window rims,
octagonal banded cylinder, rounded guard loop, notch rear sight + front blade, bolts.  ADS: every body element is clipped
to the austringer top profile (hc.ads_clip, mirrors kit adscheck): top strap <= 13.86, tang stops at z 8.24, the grip's
upper back corner is lowered under the base backstrap.  Grip squeezed to 0.7 of the rip thickness about the front strap."""
import math
from pathlib import Path
from hc import (Cal, box, tilt_box, perp_warp, lin_warp, bev_z, bev_x, drum, bolt, muzzle_ring, ads_clip, rip_colour, stack, Painter, slab, grip_stack, along, deconflict)

HERE = Path(__file__).parent
C = Cal(HERE / 'proj_cache', (140, 56.5), (4.34, 12.43), 36.0, 38.0)
T = 20
ATLAS = 1024  # 1024x512 after crop; 512 overflow after recessed muzzle cavities.
OCC_TOL = 0.02
GT = 22.7
GP0 = (C.z(107.5), C.y(82))
GK = 0.7
CLIPPED = []

C.warps += [('shroud', lin_warp('y', C.y(80), 13.80, C.y(80), C.y(23))),
            ('top_strap', lin_warp('y', C.y(37), 13.86, C.y(37), C.y(15))),
            ('tang', lin_warp('z', C.z(100), 8.10, C.z(100), C.z(45))),
            ('grip', perp_warp(GP0, GT, GK))]

LIGHT = rip_colour(HERE / 'proj_cache', 171, 60)        # white frame rim
DARK = rip_colour(HERE / 'proj_cache', 190, 100)        # dark lower frame
FLAT = {'rim_': LIGHT, 'bolt_': (52, 52, 54, 255), 'sight_': (40, 40, 42, 255)}


def model2world(name, p): return C.model2world(name, p)


def elements():
    R, z, y = C.R, C.z, C.y; E = []
    # ---- barrel shroud: chamfered slab, under rail, muzzle cap with bore, main bore, front blade
    zf, zr = z(378), z(240); L = zr - zf
    E += slab('shroud_main', 7.35, 8.65, y(47), 13.80, zf, zr, c=.16, cuts=(zf + L * .36,), bottom=False)
    E += slab('shroud_low', 7.42, 8.58, y(80), y(47), zf + .12, zr, c=.12, cuts=(zf + L * .36,), top=False)
    E.append(box('shroud_endcap', [7.5, y(76), zf - .06], [8.5, 13.6, zf + .12]))
    E.append(R('shroud_lip', 232, 40, 240, 80, 7.3, 8.7))
    E += muzzle_ring('muzzle_cap', 8.0, y(37.5), .42, .17, z(386), z(375), depth=.25)
    E += muzzle_ring('muzzle_bore', 8.0, y(68), .5, .24, z(378) - .12, z(372), depth=.3)
    E += bev_z('rail_under', 7.55, 8.45, y(88), y(80), z(340), z(180), .1, top=False, bottom=True)
    E.append(R('rail_tip', 340, 80, 352, 85, 7.65, 8.35))
    E.append(box('sight_front', [7.93, 13.80, z(372)], [8.07, 13.93, z(360)]))
    # ---- frame
    E += slab('top_strap', 7.25, 8.75, y(37), 13.86, z(240), 5.98, c=.14, cuts=(z(172), z(108)), bottom=False)
    E += slab('frame_fore', 7.15, 8.85, y(82), y(37), z(240), z(170), c=.12, top=False, bottom=False, cuts=(z(205),))
    E.append(R('frame_rear', 100, 37, 110, 80, 7.2, 8.8))
    E += slab('frame_lower', 7.2, 8.8, y(98), y(78), z(232), z(95), c=.12, cuts=(z(150),), top=False)
    E.append(R('frame_guard_front', 150, 98, 228, 108, 7.45, 8.55))
    E += bev_z('frame_guard_low', 7.45, 8.55, y(117), y(108), z(208), z(150), .12, top=False, bottom=True)
    # crisp white window rims around the cylinder (both sides)
    for sd, xf in ((-1, 7.15), (1, 8.85)):
        t = 'w' if sd < 0 else 'e'; xa, xb = (6.99, 7.18) if sd < 0 else (8.82, 9.01)
        E.append(box(f'rim_{t}_top', [xa, y(37), z(172)], [xb, y(33), z(108)]))
        E.append(box(f'rim_{t}_bot', [xa, y(82), z(172)], [xb, y(78), z(108)]))
        E.append(box(f'rim_{t}_front', [xa, y(78), z(172)], [xb, y(37), z(168)]))
        E.append(box(f'rim_{t}_rear', [xa, y(78), z(112)], [xb, y(37), z(108)]))
        E.append(bolt(f'bolt_{t}_frame', z(152), y(70), xf, sd))
        E.append(bolt(f'bolt_{t}_guard', z(183), y(100), 8.55 if sd > 0 else 7.45, sd))
        E.append(bolt(f'bolt_{t}_lug', z(195), y(85), xf, sd))
    # ---- rounded trigger guard loop (real opening) + trigger
    E.append(R('guard_bottom', 106, 119, 158, 127, 7.72, 8.28))
    E.append(R('guard_rear', 99, 98, 109, 121, 7.75, 8.25))
    E.append(R('guard_front', 153, 108, 168, 121, 7.72, 8.28))
    for tag, xi, yi in (('r', 105, 121), ('f', 159, 121)):
        zz, yy = z(xi), y(yi)
        E.append(box(f'guard_corner_{tag}', [7.72, yy - .22, zz - .22], [8.28, yy + .22, zz + .22],
                     rotation={'origin': [8.0, yy, zz], 'x': 45, 'y': 0, 'z': 0}))
    E.append(R('trigger_blade', 113, 98, 122, 110, 7.88, 8.12))
    E.append(R('trigger_tip', 116, 110, 125, 118, 7.88, 8.12))
    # ---- hammer (rounded hub + spur), beavertail tang, notch rear sight on the austringer notch
    E.append(R('hammer', 80, 36, 100, 52, 7.62, 8.38))
    hz, hy = z(86), y(42)
    E.append(box('hammer_hub_v', [7.6, hy - .42, hz - .22], [8.4, hy + .42, hz + .22]))   # stepped round hub
    E.append(box('hammer_hub_h', [7.62, hy - .22, hz - .42], [8.38, hy + .22, hz + .42]))
    s = R('tang', 45, 52, 100, 82, 7.3, 8.7); s['to'][2] = 8.10; E.append(s)
    E.append(box('sight_rear_base', [7.42, 13.84, 4.82], [8.58, 13.94, 5.48]))
    for tag, xa, xb in (('l', 7.42, 7.72), ('r', 8.28, 8.58)):
        E.append(box(f'sight_rear_{tag}', [xa, 13.94, 4.82], [xb, 14.12, 5.48]))
    # ---- grip: squeezed raked stock, slanted butt, proud side panels with screws
    W = 2.85 * GK
    a = math.radians(GT); d = (math.sin(a), -math.cos(a)); n = (math.cos(a), math.sin(a))
    gb = (GP0[0] + d[0] * 4.55, GP0[1] + d[1] * 4.55); wh = W / math.cos(a)
    # one rake line: core (4 segments) + heel continuing the same line + side panels flush on the core
    E += grip_stack('grip_core', GP0, gb, wh, wh, 7.22, 8.78, 4, heel=('grip_butt', .45, wh + .12, 7.2, 8.8),
                    panels=('grip_panel_l', 'grip_panel_r', .2, .95, .15, wh * .78, wh * .78, .1))
    for sd, xf, t_ in ((-1, 7.12, 'w'), (1, 8.88, 't')):
        q = (GP0[0] + d[0] * 1.9 + n[0] * W * .45, GP0[1] + d[1] * 1.9 + n[1] * W * .45)
        E.append(bolt(f'bolt_grip_{t_}', q[0], q[1], xf, sd, s=.26))
    E = deconflict(ads_clip(E, 'austringer', log=CLIPPED))
    # ---- cylinder (moving part): octagonal banded drum + centre pin
    E += drum('mag_drum', (8.0, 12.43), .97, z(168), z(112), n=4, band=(.14, .04))
    E.append(box('mag_core', [7.8, 12.23, z(168) - .08], [8.2, 12.63, z(112) + .02]))
    return E


# ---------------------------------------------------------------- W30-style flat paint (rip colours, hand-placed blocks)
PALETTE = 16
OLIVE, GUN, STEEL, LGREY, WHITE, BLACK, GRIP = ((92, 108, 58, 255), (64, 63, 61, 255), (88, 87, 85, 255),
                                                (176, 178, 176, 255), (226, 226, 222, 255), (22, 22, 24, 255),
                                                (50, 50, 49, 255))
PALETTE_KEEP = [OLIVE[:3], WHITE[:3]]


def I(x0, y0, x1, y1): return x0, x1, y0, y1      # decals in rip nx image px


SH = ('shroud',)
POLY = [(('top_strap', 'shroud', 'frame_fore'), [(118, 10), (240, 10), (240, 26), (118, 26)], OLIVE),
        (('shroud', 'frame_fore'), [(196, 22), (240, 22), (334, 41), (344, 50), (300, 50), (228, 37), (196, 30)], OLIVE),
        (SH, [(330, 50), (343, 50), (374, 78), (360, 80)], OLIVE),
        (SH, [(350, 50), (360, 50), (380, 66), (380, 76)], OLIVE)]
side = [(SH, *I(253, 33, 277, 39), WHITE), (SH, *I(287, 33, 368, 39), WHITE),
        (SH, *I(222, 43, 372, 46), BLACK)]
for i in range(11):    # vent row: dark dots
    x0 = 274 + i * 5.5
    side.append((SH, *I(x0, 60, x0 + 3, 64), BLACK))
side += [(SH, *I(240, 50, 380, 82), LGREY), (('frame_fore',), *I(170, 60, 240, 82), WHITE)]
PAINT = Painter(
    parts=[('rim_', WHITE), ('bolt_', BLACK), ('sight_', BLACK), ('guard_', WHITE), ('trigger', WHITE),
           ('hammer', WHITE), ('rail_', WHITE), ('frame_guard', GUN), ('frame_lower', GUN), ('frame_rear', GUN),
           ('tang', STEEL), ('grip_panel', GRIP), ('grip_', (60, 60, 58, 255)), ('muzzle', STEEL),
           ('shroud', GUN), ('top_strap', GUN), ('frame_fore', LGREY), ('mag_core', BLACK),
           ('mag_drum_fband', LGREY), ('mag_drum_rband', LGREY), ('mag_drum', (70, 70, 70, 255))],
    side=side, poly=POLY, cal=C,
    top=[(('shroud', 'top_strap'), -9, 9, 7.85, 8.15, BLACK), (('top_strap',), -9, 9, 7.0, 9.0, OLIVE),
         (('shroud',), C.z(300), C.z(240), 7.0, 9.0, OLIVE)],
    end=[(('muzzle',), STEEL)])


def special(e, fn, s, t):
    n = e['name']
    if n.endswith('_bore') and fn == 'north': return (10, 10, 11, 255)
    return PAINT(e, fn, s, t)

# Identity pass: all visible faces are hand painted at close-view density.
from identity import detail as identity_detail
_base_special = special
def special(e, fn, s, t):
    base = _base_special(e, fn, s, t)
    if e['name'].endswith('_bore') and fn == 'north': return base
    return identity_detail('allegro_34', e, fn, s, t, base, C, T)

from hc import carve_bores
_identity_elements = elements
def elements(): return carve_bores(_identity_elements())

# W325 material pass: material grain and rip relief replace whole-face flat fills.
STYLE = 'material'
from surface import materials as _surface_materials, material as _surface_material, decals as _surface_decals
MATERIALS = _surface_materials('allegro_34')
def material(name, face): return _surface_material('allegro_34', name, face)
def special(e, fn, s, t): return _surface_decals('allegro_34', e, fn, s, t, C)
