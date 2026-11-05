"""W325 Lamia HC2 (rare Adaptive Omolon hand cannon) over base austringer.  Authored in rip-image px (nx view) -> model px.
Calibration: rip energy-cell centre (img 149,59.5) -> z 3.70, y 12.43 (0.64 ahead of the austringer cylinder centre: the
Lamia cell sits further forward of its grip than the austringer cylinder, so cell and grip each give 0.64); S 36, SX 38;
the short barrel block ahead of img x 185 is stretched 1.12x (muzzle -4.6).  Top slab lowered under the sight line,
grip/rear body squeezed horizontally to 0.8 behind the front strap."""
import math
from pathlib import Path
from hc import Cal, box, tb_from, hwarp, hsq, lin_warp, bev_z, bev_x, drum, bolt, muzzle_ring, ads_clip, rip_colour, stack, slab, Painter, grip_stack, deconflict

C = Cal(Path(__file__).parent / 'proj_cache', (149, 59.5), (3.40, 12.10), 40.0, 38.0, front=(185, 1.10))
T = 20
OCC_TOL = 0.02
GT = 22.4
GP0 = (C.z(98), C.y(72))
GK = 0.72

C.warps += [('shroud', lin_warp('y', C.y(37), 13.86, C.y(37), C.y(17))),
            ('grip', hwarp(GP0, GT, GK))]


HERE = Path(__file__).parent
CLIPPED = []
TRIM = rip_colour(HERE / 'proj_cache', 225, 96, rad=1)
FLAT = {'bolt_': (30, 28, 28, 255), 'sight_': (40, 40, 42, 255), 'lamp_red': (205, 40, 45, 255),
        'lamp_blue': (60, 150, 210, 255), 'lamp_frame': TRIM}


def sq(xi, yi): return hsq(GP0, GT, GK, C.z(xi), C.y(yi))


def model2world(name, p): return C.model2world(name, p)


def elements():
    R, z, y = C.R, C.z, C.y; E = []
    zr = sq(52, 30)[0]
    # upper slab: chamfered top ahead of the breech, stepped down behind it (austringer ADS profile)
    E += slab('shroud_upper', 7.4, 8.6, y(37), 13.86, z(317), 5.99, c=.16, cuts=(z(255), z(180), z(118)), bottom=False)
    E.append(box('shroud_endcap', [7.52, y(66), z(317) - .05], [8.48, 13.7, z(317) + .1]))
    E.append(box('shroud_rear', [7.4, y(37), 6.0], [8.6, 13.43, min(zr, 7.49)]))
    E += slab('barrel_block', 7.4, 8.6, y(68), y(37), z(317), z(180), c=.12, cuts=(z(255),), top=False)
    # muzzle: main bore crown (lower) + small upper port, front blade
    E += muzzle_ring('muzzle_main', 8.0, y(57), .5, .24, z(320), z(314), depth=.35)
    E += muzzle_ring('muzzle_port', 8.0, y(43), .32, .13, z(319), z(316), depth=.2)
    E.append(box('sight_front', [7.93, 13.86 - .22, z(315)], [8.07, 13.93, z(306)]))
    # lower front block with chamfered belly, status lamps, screws
    E += slab('lower_front', 7.25, 8.75, y(112), y(73), z(317), z(190), c=.16, cuts=(z(270), z(225)))
    E.append(bev_x('lower_nose', 7.25, 8.75, y(73) + .01, z(317), .2, -1))
    E.append(R('lower_tail', 190, 112, 232, 118, 7.3, 8.7))
    E.append(box('lamp_frame', [7.21, y(92), z(264)], [7.25, y(86), z(229)]))
    E.append(box('lamp_red', [7.19, y(91), z(256)], [7.22, y(87), z(248)]))
    E.append(box('lamp_blue', [7.19, y(91), z(244)], [7.22, y(87), z(236)]))
    E += slab('frame_mid', 7.25, 8.75, y(95), y(80), z(232), z(100), c=.1, cuts=(z(176),), top=False)
    E.append(R('frame_cell_front', 176, 68, 192, 82, 7.3, 8.7))
    for sd, t_ in ((-1, 'w'), (1, 'e')):
        xf = 7.25 if sd < 0 else 8.75
        for i, (xi, yi) in enumerate(((143, 104), (215, 104), (300, 82))):
            E.append(bolt(f'bolt_{t_}{i}', z(xi), y(yi), xf, sd, s=.2))
        E.append(bolt(f'bolt_{t_}top', z(305), y(26), 7.4 if sd < 0 else 8.6, sd, s=.2))
    # trigger guard (real opening, rounded corners) + trigger
    E.append(R('guard_bottom', 78, 122, 124, 130, 7.74, 8.26))
    E.append(R('guard_front', 120, 95, 130, 124, 7.74, 8.26))
    for tag, xi, yi in (('f', 123, 125), ('r', 78, 125)):
        zz, yy = z(xi), y(yi)
        E.append(box(f'guard_corner_{tag}', [7.74, yy - .2, zz - .2], [8.26, yy + .2, zz + .2],
                     rotation={'origin': [8.0, yy, zz], 'x': 45, 'y': 0, 'z': 0}))
    E.append(R('trigger', 86, 98, 97, 120, 7.88, 8.12))
    # rear body + beavertail, lowered to the austringer breech/tang profile
    z1 = z(118)
    E.append(box('grip_frame', [7.3, y(80), z1], [8.7, 13.43, min(sq(46, 50)[0], 7.49)]))
    E.append(box('grip_frame_low', [7.3, y(80), 7.49], [8.7, 12.13, sq(46, 50)[0]]))
    E.append(box('grip_tail', [7.35, y(68), sq(55, 58)[0]], [8.65, min(y(48), 12.13), min(sq(34, 58)[0], 8.24)]))
    # notch rear sight on the austringer notch
    E.append(box('sight_rear_base', [7.42, 13.84, 4.82], [8.58, 13.94, 5.48]))
    for tag, xa, xb in (('l', 7.42, 7.72), ('r', 8.28, 8.58)):
        E.append(box(f'sight_rear_{tag}', [xa, 13.94, 4.82], [xb, 14.12, 5.48]))
    # grip: red frame core, proud stippled side panels, finger hook
    def gline(f_top, f_bot, back_top, back_bot):
        t = sq(*f_top); bt = sq(*f_bot)
        return t, bt, sq(back_top, f_top[1])[0] - t[0], sq(back_bot, f_bot[1])[0] - bt[0]
    t, bt, wt, wb = gline((101, 64), (60, 170), 46, 5)
    E += grip_stack('grip_core', t, bt, wt, wb, 7.28, 8.72, 5,
                    panels=('grip_panel_w', 'grip_panel_e', .15, .92, .55, wt * .55, wb * .7, .08))
    E.append(R('grip_hook', 48, 158, 64, 176, 7.32, 8.68))
    E = deconflict(ads_clip(E, 'austringer', log=CLIPPED))
    # energy cell (moving part): octagonal green drum with end bands + core
    cy = y(59.5)
    E += drum('mag_drum', (8.0, cy), 1.05, z(180), z(118), n=4, band=(.15, .04))
    E.append(box('mag_core', [7.75, cy - .25, z(180) - .08], [8.25, cy + .25, z(118) + .02]))
    return E


PALETTE = 16
MAROON, TAN, CELL, STIP, BLACK, DARK = ((104, 62, 60, 255), (190, 176, 152, 255), (98, 112, 98, 255),
                                     (58, 58, 58, 255), (22, 20, 20, 255), (44, 40, 40, 255))
PALETTE_KEEP = [MAROON[:3], TAN[:3], CELL[:3], (205, 40, 45), (60, 150, 210)]
UP = ('shroud', 'barrel_block')
SIDE = [(UP, 210, 318, 50, 54, TAN), (UP, 183, 210, 37, 54, DARK),            # perforated band + dark port
        (('shroud', 'grip_frame'), 60, 98, 26, 30, TAN), (('shroud', 'grip_frame'), 64, 94, 36, 40, TAN),   # logo plate
        (('frame_mid',), 125, 160, 86, 88, TAN),                                 # OMOLON plate
        (('lower_front',), 192, 318, 73, 76, TAN), (('lower_front',), 300, 318, 76, 112, TAN)]
for i in range(18):                                                              # perforation dots
    SIDE.append((UP, 212 + i * 6, 214 + i * 6, 55, 57, BLACK))
    if i % 2: SIDE.append((UP, 215 + i * 6, 217 + i * 6, 52, 53, BLACK))
for cx in (242, 268):                                                            # Omolon rings (squares of texels)
    SIDE += [(UP, cx - 6, cx + 6, 29, 31, TAN), (UP, cx - 6, cx + 6, 41, 43, TAN),
             (UP, cx - 7, cx - 5, 29, 43, TAN), (UP, cx + 5, cx + 7, 29, 43, TAN)]
for i in range(6):                                                               # OMOLON lettering
    SIDE.append((('frame_mid',), 128 + i * 5.5, 131 + i * 5.5, 89, 92, TAN))
SIDE = SIDE[7:] + SIDE[:7]
PAINT = Painter(
    parts=[('lamp_', None), ('bolt_', BLACK), ('sight_', BLACK), ('guard_', MAROON), ('trigger', TAN),
           ('grip_panel', STIP), ('grip_hook', MAROON), ('grip_', MAROON), ('muzzle', TAN),
           ('shroud_endcap', TAN), ('shroud', MAROON), ('barrel_block', MAROON), ('lower_tail', TAN), ('lower', MAROON),
           ('frame_cell', DARK), ('frame', MAROON), ('mag_core', DARK), ('mag_drum_fband', TAN),
           ('mag_drum_rband', TAN), ('mag_drum', CELL)],
    side=SIDE, cal=C, top=[(UP, -9, 9, 7.62, 7.72, TAN), (UP, -9, 9, 8.28, 8.38, TAN)])


def special(e, fn, s, t):
    n = e['name']
    if n.endswith('_bore') and fn == 'north': return (10, 10, 11, 255)
    for k, c in FLAT.items():
        if n.startswith(k): return c
    return PAINT(e, fn, s, t)

# Identity pass: all visible faces are hand painted at close-view density.
from identity import detail as identity_detail
_base_special = special
def special(e, fn, s, t):
    base = _base_special(e, fn, s, t)
    if e['name'].endswith('_bore') and fn == 'north': return base
    return identity_detail('lamia_hc2', e, fn, s, t, base, C, T)

from hc import carve_bores
_identity_elements = elements
def elements(): return carve_bores(_identity_elements())

# W325 material pass: material grain and rip relief replace whole-face flat fills.
STYLE = 'material'
from surface import materials as _surface_materials, material as _surface_material, decals as _surface_decals
MATERIALS = _surface_materials('lamia_hc2')
def material(name, face): return _surface_material('lamia_hc2', name, face)
def special(e, fn, s, t): return _surface_decals('lamia_hc2', e, fn, s, t, C)
