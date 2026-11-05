"""W325 Ballyhoo Mk.27 (rare Adaptive hand cannon) over base austringer.  Authored in rip-image px (nx view) -> model px.
Calibration: rip cylinder centre (img 128.5,56.5) -> austringer cylinder centre (z 4.34, y 12.43); S 38 px/m, SX 38;
the short barrel ahead of the frame (img x>195) is stretched 1.115x so the muzzle reaches z -5.7 (base -6.32).
Fits: wide brown shroud / top strap lowered under the austringer sight line (<=13.85/13.92, ears 14.10); grip and the
light frame rear squeezed horizontally to 0.75 behind the front strap (front strap ~0.2 px behind the base)."""
import math
from pathlib import Path
from hc import Cal, box, tb_from, hwarp, hsq, lin_warp, bev_z, bev_x, drum, bolt, muzzle_ring, ads_clip, rip_colour, slab, Painter, grip_stack, deconflict

C = Cal(Path(__file__).parent / 'proj_cache', (128.5, 56.5), (4.34, 12.43), 38.0, 38.0, front=(195, 1.115))
T = 20
ATLAS = 1024  # 1024x512 after crop: readable 1P glyphs, fine grooves and grip texels.
OCC_TOL = 0.02
GT = 17.0
GP0 = (C.z(80), C.y(105))
GK = 0.75

C.warps += [('shroud', lin_warp('y', C.y(62), 13.85, C.y(62), C.y(15))),
            ('top_strap', lin_warp('y', C.y(33), 13.86, C.y(33), C.y(15))),
            ('grip', hwarp(GP0, GT, GK))]


HERE = Path(__file__).parent
CLIPPED = []
LIGHT = rip_colour(HERE / 'proj_cache', 172, 60, rad=1)
FLAT = {'rim_': LIGHT, 'strap_': LIGHT, 'bolt_': (190, 200, 205, 255), 'sight_': (40, 40, 42, 255)}


def sq(xi, yi): return hsq(GP0, GT, GK, C.z(xi), C.y(yi))


def model2world(name, p): return C.model2world(name, p)


def elements():
    R, z, y = C.R, C.z, C.y; E = []
    # wide brown front shroud (chamfered top), teal barrel, muzzle crown with real bore, under lug with pins,
    # hanging front loop on its mount, light diagonal straps on both shroud sides, front sight blade
    E += slab('shroud_front', 6.95, 9.05, y(62), 13.85, z(318), z(194), c=.2, cuts=(z(282), z(240)))
    E.append(box('shroud_endcap', [7.1, y(58), z(318) - .06], [8.9, 13.7, z(318) + .1]))
    E += bev_z('barrel_lower', 7.3, 8.7, y(88), y(62), z(300), z(190), .14, top=False, bottom=True)
    E += muzzle_ring('muzzle_crown', 8.0, y(71.5), .55, .24, z(325), z(298), depth=.4)
    E += slab('front_lug', 7.02, 8.98, y(108), y(62), z(278), z(218), c=.14, cuts=(z(248),), top=False)
    E.append(R('loop_mount', 282, 83, 318, 98, 7.6, 8.4))
    E.append(R('loop_l', 284, 98, 288, 140, 7.86, 8.14))
    E.append(R('loop_r', 293, 98, 297, 140, 7.86, 8.14))
    E.append(R('loop_bottom', 284, 135, 297, 141, 7.86, 8.14))
    E.append(box('sight_front', [7.93, 13.85 - .28, z(316)], [8.07, 13.94, z(306)]))
    for t_ in ('w', 'e'):
        sd = -1 if t_ == 'w' else 1; xf = 7.02 if sd < 0 else 8.98
        for i, xi in enumerate((232, 258)):
            E.append(bolt(f'bolt_{t_}_lug{i}', z(xi), y(78), xf, sd, s=.3))
        E.append(bolt(f'bolt_{t_}_loop', z(313), y(92), 7.6 if sd < 0 else 8.4, sd, s=.24))
    # frame: top strap over the cylinder, light front, lower frame, recoil shield, crisp window rims
    E += slab('top_strap', 7.4, 8.6, y(33), 13.86, z(210), z(88), c=.12, cuts=(z(162), z(99)), bottom=False)
    E.append(R('frame_front', 160, 30, 194, 88, 7.2, 8.8))
    E += slab('frame_lower', 7.2, 8.8, y(95), y(83), z(180), z(80), c=.12, cuts=(z(138),), top=False)
    E.append(R('frame_rear', 90, 30, 99, 83, 7.2, 8.8))
    for sd in (-1, 1):
        t_ = 'w' if sd < 0 else 'e'; xa, xb = (6.97, 7.22) if sd < 0 else (8.78, 9.03)
        E.append(box(f'rim_{t_}_top', [xa, y(33), z(162)], [xb, y(30), z(95)]))
        E.append(box(f'rim_{t_}_bot', [xa, y(83), z(162)], [xb, y(80), z(95)]))
        E.append(box(f'rim_{t_}_front', [xa, y(80), z(162)], [xb, y(33), z(158)]))
        E.append(box(f'rim_{t_}_rear', [xa, y(80), z(99)], [xb, y(33), z(95)]))
    # light frame rear / backstrap (squeezed with the grip), hammer with ring spur
    z0, _ = sq(46, 60); z1 = z(92)
    E.append(box('grip_frame', [7.25, y(100), z1], [8.75, y(30), z0]))
    E.append(R('hammer', 62, 26, 82, 40, 7.65, 8.35))
    E.append(R('hammer_ring_f', 74, 20, 80, 30, 7.75, 8.25))
    E.append(R('hammer_ring_t', 63, 19, 80, 23, 7.75, 8.25))
    # round trigger guard (real opening) and trigger
    E.append(R('guard_bottom', 95, 120, 138, 128, 7.72, 8.28))
    E.append(R('guard_front', 138, 92, 148, 120, 7.72, 8.28))
    E.append(R('guard_rear', 82, 95, 96, 124, 7.72, 8.28))
    for tag, xi, yi in (('f', 140, 121), ('r', 93, 121)):
        zz, yy = z(xi), y(yi)
        E.append(box(f'guard_corner_{tag}', [7.72, yy - .22, zz - .22], [8.28, yy + .22, zz + .22],
                     rotation={'origin': [8.0, yy, zz], 'x': 45, 'y': 0, 'z': 0}))
    E.append(R('trigger', 103, 98, 112, 117, 7.88, 8.12))
    # grip: dark wood-brown stock, light heel plate, side medallions
    def gline(f_top, f_bot, back_top, back_bot):
        t = sq(*f_top); bt = sq(*f_bot)
        return t, bt, sq(back_top, f_top[1])[0] - t[0], sq(back_bot, f_bot[1])[0] - bt[0]
    t, bt, wt, wb = gline((83, 84), (58, 182), 42, 12)
    E += grip_stack('grip_core', t, bt, wt, wb, 7.2, 8.8, 4, heel=('grip_heel', .55, wb + .15, 7.18, 8.82))
    mz, my = sq(40, 125)
    for tag, xa, xb in (('l', 7.12, 7.2), ('r', 8.8, 8.88)):
        E.append(box(f'grip_medallion_{tag}', [xa, my - .3, mz - .3], [xb, my + .3, mz + .3]))
    # notch rear sight on the austringer notch (x=8 eye ray open)
    E.append(box('sight_rear_base', [7.42, 13.84, 4.82], [8.58, 13.94, 5.48]))
    for tag, xa, xb in (('l', 7.42, 7.72), ('r', 8.28, 8.58)):
        E.append(box(f'sight_rear_{tag}', [xa, 13.94, 4.82], [xb, 14.12, 5.48]))
    E = deconflict(ads_clip(E, 'austringer', log=CLIPPED))
    # cylinder (moving part): octagonal teal drum with end bands + centre pin
    E += drum('mag_drum', (8.0, y(56.5)), 1.0, z(158), z(99), n=4, band=(.14, .04))
    E.append(box('mag_core', [7.8, y(56.5) - .2, z(158) - .08], [8.2, y(56.5) + .2, z(99) + .02]))
    return E


PALETTE = 16
BROWN, TEAL, LBLUE, WHITE, BLACK, GRIP, GUN = ((96, 86, 78, 255), (58, 92, 98, 255), (180, 210, 220, 255),
                                              (226, 232, 234, 255), (22, 22, 24, 255), (52, 40, 34, 255), (46, 46, 46, 255))
PALETTE_KEEP = [TEAL[:3], LBLUE[:3]]
SIDE = [(('shroud_front',), 194, 318, 15, 22, (70, 64, 60, 255)),
        (('shroud_front',), 194, 260, 30, 52, (82, 74, 68, 255)),
        (('top_strap', 'frame_front'), 88, 210, 15, 22, (70, 64, 60, 255))]
for i in range(6):
    SIDE.append((('shroud_front', 'barrel_lower'), 262 + i * 6, 266 + i * 6, 25, 60, BLACK) if i % 2 else
                (('shroud_front',), 262 + i * 6, 264 + i * 6, 25, 55, (70, 64, 60, 255)))
PAINT = Painter(
    parts=[('rim_', LBLUE), ('strap_', LBLUE), ('bolt_', LBLUE), ('sight_', BLACK), ('loop', LBLUE), ('guard_', LBLUE),
           ('trigger', LBLUE), ('hammer', LBLUE), ('grip_frame', LBLUE), ('grip_heel', LBLUE), ('grip_medallion', (150, 150, 150, 255)),
           ('grip_', GRIP), ('front_lug', GUN), ('muzzle', (200, 205, 208, 255)), ('shroud', BROWN), ('barrel_lower', TEAL),
           ('top_strap', BROWN), ('frame_front', TEAL), ('frame_lower', LBLUE), ('frame_rear', LBLUE),
           ('mag_core', BLACK), ('mag_drum_fband', LBLUE), ('mag_drum_rband', LBLUE), ('mag_drum', TEAL)],
    side=SIDE, cal=C, poly=[(('shroud_front',), [(315, 22), (321, 22), (297, 62), (291, 62)], LBLUE)],
    top=[(('shroud', 'top_strap'), -9, 9, 7.9, 8.1, BLACK)])


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
    return identity_detail('ballyhoo_mk_27', e, fn, s, t, base, C, T)

from hc import carve_bores
_identity_elements = elements
def elements(): return carve_bores(_identity_elements())

# W325 material pass: material grain and rip relief replace whole-face flat fills.
STYLE = 'material'
from surface import materials as _surface_materials, material as _surface_material, decals as _surface_decals
MATERIALS = _surface_materials('ballyhoo_mk_27')
def material(name, face): return _surface_material('ballyhoo_mk_27', name, face)
def special(e, fn, s, t): return _surface_decals('ballyhoo_mk_27', e, fn, s, t, C)
