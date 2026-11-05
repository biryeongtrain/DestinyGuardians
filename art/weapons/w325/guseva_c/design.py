"""W325 Guseva-C (rare Aggressive Hakke hand cannon) over base duke_mk_44.  Authored in rip-image px (nx view) -> model px.
Calibration: rip cylinder centre (img 142,59) -> duke cylinder centre (z 3.77, y 12.80); S 39 px/m, SX 38; the shroud
ahead of img x 175 compressed 0.94x (muzzle -6.22, base -6.17).  Top rail clamped to 14.88 (duke sight line ~14.95);
grip/rear stock squeezed horizontally to 0.85 behind the front strap.  The rip's side flashlight sits on the rip +x side
(model west / -x)."""
import math
from pathlib import Path
from hc import Cal, box, tb_from, hwarp, hsq, lin_warp, slab, bev_x, drum, bolt, muzzle_ring, ads_clip, Painter, grip_stack, deconflict

C = Cal(Path(__file__).parent / 'proj_cache', (142, 59), (3.77, 12.80), 39.0, 38.0, front=(175, 0.94))
T = 20
ATLAS = 1024  # 1024x512 after crop: readable 1P glyphs, fine grooves and grip texels.
OCC_TOL = 0.02
GT = 22.4
GP0 = (C.z(100), C.y(100))
GK = 0.85

C.warps += [('top_rail', lin_warp('y', C.y(20), 14.88, C.y(20), C.y(15))),
            ('grip', hwarp(GP0, GT, GK))]


def sq(xi, yi): return hsq(GP0, GT, GK, C.z(xi), C.y(yi))


def model2world(name, p): return C.model2world(name, p)


CLIPPED = []


def elements():
    R = C.R; E = []
    # light "glass"-finish shroud, top rail, toothed bottom rail, hanging front peg, muzzle face
    z, y = C.z, C.y
    E += slab('shroud', 7.15, 8.85, y(85), y(20), z(355), z(172), c=.18, cuts=(z(300), z(240)))
    E += slab('top_rail', 7.5, 8.5, y(20), 14.88, z(350), z(190), c=.08, cuts=(z(300), z(240)), bottom=False)
    E.append(box('shroud_face', [7.27, y(82), z(359)], [8.73, y(24), z(355)]))
    E += muzzle_ring('muzzle_bore', 8.0, y(35), .46, .24, z(359) - .06, z(356), depth=.3)
    E.append(R('bottom_rail', 248, 85, 357, 90, 7.55, 8.45))
    for i in range(10):                                   # rail teeth
        za = z(254 + i * 10)
        E.append(box(f'bottom_rail_t{i}', [7.6, y(95), za - .26], [8.4, y(90), za]))
    for sd, t in ((-1, 'w'), (1, 'e')):
        xf = 7.15 if sd < 0 else 8.85
        for i, (xi, yi) in ([(0, (207, 70)), (2, (190, 35))] if sd < 0 else enumerate(((207, 70), (322, 70), (190, 35)))):
            E.append(bolt(f'bolt_{t}{i}', z(xi), y(yi), xf, sd, s=.22))
        xa, xb = (6.98, 7.18) if sd < 0 else (8.82, 9.02)
        E.append(box(f'rim_{t}_top', [xa, y(36), z(172)], [xb, y(33), z(112)]))
        E.append(box(f'rim_{t}_bot', [xa, y(88), z(172)], [xb, y(85), z(112)]))
    E.append(R('peg_base', 332, 85, 348, 97, 7.75, 8.25))
    E.append(R('peg_pin', 336, 97, 344, 115, 7.88, 8.12))
    # side flashlight on the rip +x side (model west)
    E += [dict(e, **{'name': e['name'].replace('lightb', 'light_body')}) for e in
          slab('lightb', 6.16, 7.16, C.y(85), C.y(60), C.z(350), C.z(240), c=.12, cuts=(C.z(300),))]
    E.append(box('light_band', [6.1, C.y(86), C.z(320)], [7.16, C.y(59), C.z(312)]))
    E.append(box('light_head', [6.1, C.y(87), C.z(356)], [7.16, C.y(58), C.z(348)]))
    # frame around the cylinder: orange top strap, window bottom, recoil shield; rear sight ears
    E += slab('top_strap', 7.4, 8.6, y(33), y(22), z(190), z(108), c=.1, cuts=(z(150),), bottom=False)
    E.append(R('frame_window_low', 108, 85, 175, 92, 7.2, 8.8))
    E.append(R('frame_rear', 103, 30, 112, 92, 7.2, 8.8))
    for tag, xa, xb in (('l', 7.42, 7.72), ('r', 8.28, 8.58)):
        E.append(box(f'sight_rear_{tag}', [xa, C.y(22), C.z(150)], [xb, C.y(22) + .18, C.z(134)]))
    E.append(box('sight_front', [7.93, 14.88, z(348)], [8.07, 14.98, z(340)]))
    # rear stock block with the orange sloped top, dark butt plate (squeezed with the grip)
    E.append(box('grip_stock', [7.12, C.y(92), C.z(105)], [8.88, C.y(45), sq(48, 60)[0]]))
    # orange sloped stock top as two flush axis-aligned steps (no rotated slab)
    zs0, zs1 = C.z(108), sq(48, 60)[0]
    E.append(box('grip_stock_slope_a', [7.2, C.y(45), zs0], [8.8, C.y(35), zs0 + (zs1 - zs0) * .45]))
    E.append(box('grip_stock_slope_b', [7.2, C.y(45), zs0 + (zs1 - zs0) * .45], [8.8, C.y(40), zs1]))
    z0 = sq(52, 60)[0]
    E.append(box('grip_buttplate', [7.2, C.y(76), z0 - .05], [8.8, C.y(45), z0 + .35]))
    # dark trigger group (real guard opening)
    E += slab('frame_lower', 7.3, 8.7, y(100), y(88), z(172), z(104), c=.1, top=False)
    E.append(R('guard_front', 150, 98, 172, 112, 7.4, 8.6))
    E.append(bev_x('guard_front_nose', 7.4, 8.6, y(98) + .01, z(172), .3, -1))
    E.append(R('guard_front_low', 152, 112, 166, 118, 7.45, 8.55))
    E.append(R('guard_bottom', 108, 122, 160, 130, 7.74, 8.26))
    E.append(R('guard_rear', 103, 98, 111, 126, 7.74, 8.26))
    E.append(R('guard_link', 152, 116, 162, 125, 7.74, 8.26))
    E.append(R('trigger', 115, 103, 125, 124, 7.88, 8.12))
    # raked brown grip (two sections) + slanted base
    def gline(f_top, f_bot, back_top, back_bot):
        t = sq(*f_top); bt = sq(*f_bot)
        return t, bt, sq(back_top, f_top[1])[0] - t[0], sq(back_bot, f_bot[1])[0] - bt[0]
    t, bt, wt, wb = gline((103, 86), (69, 193), 52, 12)
    E += grip_stack('grip_core', t, bt, wt, wb, 7.3, 8.7, 4, heel=('grip_base', .55, wb + .15, 7.28, 8.72))
    E = deconflict(ads_clip(E, 'duke_mk_44', log=CLIPPED))
    # cylinder (moving part): dark square drum with chamfered corners (rip) + end bands
    cy = y(59); E += drum('mag_drum', (8.0, cy), (y(33) - y(85)) / 2, z(170), z(114), n=2, band=(.14, .03))
    E.append(box('mag_core', [7.75, cy - .25, z(170) - .08], [8.25, cy + .25, z(114) + .02]))
    return E


PALETTE = 16
WHITE, GLASS, OLIVE, ORANGE, RED, DARK, BROWN, BLACK, BLUE = (
    (236, 234, 230, 255), (204, 206, 200, 255), (170, 168, 128, 255), (222, 104, 72, 255), (200, 40, 36, 255),
    (52, 50, 46, 255), (74, 56, 46, 255), (20, 20, 22, 255), (150, 175, 215, 255))
PALETTE_KEEP = [ORANGE[:3], RED[:3], OLIVE[:3], BLUE[:3]]
SH = ('shroud',)
SIDE = [(SH, 200, 350, 30, 40, OLIVE), (SH, 212, 340, 58, 64, OLIVE), (SH, 180, 352, 44, 46, DARK),
        (SH, 172, 200, 72, 84, DARK), (('grip_stock',), 40, 100, 50, 53, ORANGE)]
for i, xi in enumerate((206, 213, 220, 227, 234, 241)):      # HAKKE lettering block
    SIDE.append((SH, xi, xi + 4, 49, 55, DARK))
SIDE += [(('grip_stock',), 72, 80, 50, 62, RED), (('grip_stock',), 84, 92, 50, 62, RED),
         (('grip_stock',), 70, 94, 55, 57, RED)]                 # ++ mark
POLY = [(('top_strap',), [(108, 18), (190, 18), (190, 36), (108, 36)], ORANGE),
        (('top_strap', 'shroud'), [(172, 18), (195, 18), (195, 48), (172, 48)], ORANGE)]
PAINT = Painter(
    parts=[('bolt_', DARK), ('sight_', BLACK), ('rim_', WHITE), ('light_head', BLUE), ('light_band', DARK),
           ('light_body', DARK), ('peg', DARK), ('bottom_rail', GLASS), ('top_rail', GLASS),
           ('guard', DARK), ('trigger', DARK), ('frame_lower', DARK), ('grip_stock_slope', ORANGE),
           ('grip_buttplate', DARK), ('grip_stock', GLASS), ('grip_', BROWN), ('muzzle', GLASS), ('shroud_face', WHITE),
           ('top_strap', ORANGE), ('frame_', WHITE), ('mag_core', BLACK), ('mag_drum_fband', DARK),
           ('mag_drum_rband', DARK), ('mag_drum', (60, 52, 48, 255)), ('shroud', WHITE)],
    side=SIDE, poly=POLY, cal=C, top=[(('top_rail',), -9, 9, 7.9, 8.1, DARK)])


def special(e, fn, s, t):
    n = e['name']
    if n.endswith('_bore') and fn == 'north': return (10, 10, 11, 255)
    if n == 'light_head' and fn == 'north':
        r = math.hypot(s - .5, t - .5)
        return (210, 225, 245, 255) if r < .3 else BLUE
    return PAINT(e, fn, s, t)

# Identity pass: all visible faces are hand painted at close-view density.
from identity import detail as identity_detail
_base_special = special
def special(e, fn, s, t):
    base = _base_special(e, fn, s, t)
    if e['name'].endswith('_bore') and fn == 'north': return base
    return identity_detail('guseva_c', e, fn, s, t, base, C, T)

from hc import carve_bores
_identity_elements = elements
def elements(): return carve_bores(_identity_elements())

# W325 material pass: material grain and rip relief replace whole-face flat fills.
STYLE = 'material'
from surface import materials as _surface_materials, material as _surface_material, decals as _surface_decals
MATERIALS = _surface_materials('guseva_c')
def material(name, face): return _surface_material('guseva_c', name, face)
def special(e, fn, s, t): return _surface_decals('guseva_c', e, fn, s, t, C)
