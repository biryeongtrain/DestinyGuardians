"""W325 Nox Cordis II (Rapid-Fire fusion rifle, rare) over base null_composure (W179/W217 reload + W153 sight).

Rip at a uniform 37 px/m (compact rip, 22.9 px long vs base 24.95). Anchor: rip top rail 13.2 and the rip battery centre
on the base battery centre (z 0.23). Battery (moving magazine leaf) = upright block + front box of the lower frame
(z -2.1..1.8, y 2.05..9.0) around the base battery (z -1.47..1.93, y 4.11..10.86). Grip post on the base grip region.
W153 ADS: kept overlay aim tip (z 0.34..0.46, y 14.15..14.21) sits in a notched rear sight (named sight_*: hollow notch,
ears x 7.55..7.82 / 8.18..8.45 up to 14.05, centre open above 13.45).
r2 (detail + ADS + W30 pixel style): top rail 13.05 in front / 12.9 behind the sight (base 13.07 / 12.92), receiver,
stock and butt lowered to 12.25 (base 12.28). Shroud built from DMW-style segments: separate side window panels, end
caps, chamfered top plates, toothed rail. Paint = navy/white blob camo on the shroud, white rail, black furniture.
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_w9'))
from w9 import tidy, box, bar, post, chamfer_box, RipMap, lens, flat, material, camo, model_pt

M = RipMap(37.0, (13.2, 0.23), (0.17, -0.1475), '-y')
T = 14
PALETTE = 14
FLAT_TOL = 28
PALETTE_KEEP = [(70, 150, 190), (90, 200, 120)]


def elements():
    E = []
    # --- muzzle: stepped white nozzle with cyan bore, open front cage
    E.append(box('muzzle_tip', (7.7, 10.2, -11.7), (8.3, 10.8, -11.0)))
    E.append(box('muzzle_ring', (7.62, 10.12, -11.2), (8.38, 10.88, -11.0)))
    E.append(box('muzzle_cone', (7.55, 10.0, -11.0), (8.45, 10.95, -10.3)))
    E += chamfer_box('barrel_core', (7.5, 9.95, -10.3), (8.5, 11.05, -8.0), 0.1, bottom=True)
    E += chamfer_box('cage_top', (6.95, 11.95, -10.4), (9.05, 12.45, -8.0), 0.15)
    E += chamfer_box('cage_low', (6.95, 7.9, -10.6), (9.05, 9.35, -8.0), 0.15, top=False, bottom=True)
    E.append(box('cage_post_l', (6.95, 9.35, -8.6), (7.3, 11.95, -8.0)))
    E.append(box('cage_post_r', (8.7, 9.35, -8.6), (9.05, 11.95, -8.0)))
    E.append(box('cage_bolt_l', (6.9, 8.4, -10.2), (6.95, 8.7, -9.9)))
    E.append(box('cage_bolt_r', (9.05, 8.4, -10.2), (9.1, 8.7, -9.9)))
    # --- top rail with teeth (front of the sight <= 13.05, behind <= 12.9)
    E.append(box('rail_front', (7.6, 12.45, -10.5), (8.4, 12.85, -0.4)))
    for i in range(9):
        z = -10.2 + i * 1.08
        E.append(box(f'rail_tooth_{i}', (7.62, 12.85, z), (8.38, 13.05, z + 0.55)))
    # --- shroud: core + separate side panels with window recesses + top plates + end caps
    E.append(box('shroud', (7.0, 8.15, -8.0), (9.0, 12.3, -2.5)))
    E += chamfer_box('shroud_top', (6.9, 12.0, -8.0), (9.1, 12.4, -2.5), 0.15, segs=2)
    for sd, (a, b) in (('l', (6.9, 7.0)), ('r', (9.0, 9.1))):
        E.append(box(f'shroud_panel_hi_{sd}', (a, 11.2, -7.8), (b, 12.0, -2.7)))
        E.append(box(f'shroud_panel_lo_{sd}', (a, 8.2, -7.8), (b, 9.3, -2.7)))
        for k in range(4):
            z = -7.6 + k * 1.2
            E.append(box(f'shroud_rib_{sd}{k}', (a, 9.3, z), (b, 11.2, z + 0.25)))
    E.append(box('shroud_cap_f', (6.85, 8.2, -8.15), (9.15, 12.25, -8.0)))
    E.append(bar('shroud_belly', 6.95, 9.05, (-4.2, 8.15), (-1.6, 6.45), 1.0, 'above', ext=(0, .1)))
    E.append(box('belly_light', (6.92, 7.3, -2.9), (9.08, 7.6, -2.3)))
    # --- receiver, hollow notched rear sight around the W153 aim tip
    E += chamfer_box('recv_front', (6.85, 8.5, -2.5), (9.15, 12.45, 1.8), 0.15)
    E.append(box('recv_logo_plate', (6.8, 10.6, -1.5), (6.85, 11.3, 0.2)))
    E.append(box('recv_pin', (6.8, 9.2, 0.6), (6.85, 9.6, 1.0)))
    E += chamfer_box('recv_rear', (7.0, 9.25, 1.8), (9.0, 12.25, 7.0), 0.15, segs=2)
    E.append(box('recv_grille', (6.95, 10.4, 2.4), (7.0, 11.8, 4.6)))
    E.append(box('recv_grille_r', (9.0, 10.4, 2.4), (9.05, 11.8, 4.6)))
    E.append(box('sight_base', (7.5, 12.45, -0.4), (8.5, 13.45, 1.2)))
    E.append(box('sight_ear_l', (7.55, 13.45, 0.0), (7.82, 14.05, 0.8)))
    E.append(box('sight_ear_r', (8.18, 13.45, 0.0), (8.45, 14.05, 0.8)))
    E.append(box('rail_rear', (7.6, 12.25, 1.5), (8.4, 12.75, 4.0)))
    for i in range(3):
        z = 1.65 + i * 0.8
        E.append(box(f'rail_rear_tooth_{i}', (7.62, 12.75, z), (8.38, 12.9, z + 0.45)))
    # --- trigger, grip, lower frame
    E.append(box('lower_band', (7.2, 8.6, 1.8), (8.8, 9.25, 6.0)))
    E.append(box('guard_bot', (7.9, 7.9, 1.8), (8.1, 8.12, 4.9)))
    E.append(box('guard_rear', (7.9, 8.12, 4.75), (8.1, 8.6, 4.9)))
    E.append(post('trigger', 7.93, 8.07, (3.45, 9.25), (3.75, 8.3), 0.2))
    E.append(post('grip', 7.3, 8.7, (5.35, 9.0), (6.45, 5.2), 1.65))
    E.append(post('grip_tex_l', 7.25, 7.3, (5.35, 9.0), (6.45, 5.2), 0.9, ext=(-0.75, -0.7)))
    E.append(post('grip_tex_r', 8.7, 8.75, (5.35, 9.0), (6.45, 5.2), 0.9, ext=(-0.75, -0.7)))
    E += chamfer_box('frame_bar', (7.3, 2.4, 1.8), (8.7, 5.0, 7.75), 0.15, top=False, bottom=True)
    for sd, (a, b) in (('l', (7.25, 7.3)), ('r', (8.7, 8.75))):
        E.append(box(f'frame_window_a_{sd}', (a, 3.2, 2.4), (b, 4.3, 4.6)))
        E.append(box(f'frame_window_b_{sd}', (a, 3.2, 5.0), (b, 4.3, 7.2)))
    E.append(box('frame_strip', (7.25, 5.0, 1.8), (8.75, 5.3, 8.2)))
    E.append(box('frame_heel', (7.35, 2.6, 7.75), (8.65, 4.9, 8.1)))
    # --- stock (top <= 12.25)
    E += chamfer_box('stock_top', (7.5, 11.2, 7.0), (8.5, 12.25, 9.6), 0.12)
    E.append(box('stock_low', (7.5, 9.2, 7.0), (8.5, 10.35, 9.6)))
    E.append(box('stock_strut', (7.65, 10.35, 7.4), (8.35, 11.2, 7.8)))
    E += chamfer_box('stock_butt', (7.55, 9.15, 9.6), (8.45, 12.25, 10.3), 0.1, bottom=True)
    for i in range(4):
        y = 9.4 + i * 0.7
        E.append(box(f'butt_rib_{i}', (7.6, y, 10.3), (8.4, y + 0.35, 10.38)))
    # --- battery (moving magazine leaf)
    E += chamfer_box('mag_upper', (7.2, 5.3, -1.55), (8.8, 9.0, 1.65), 0.12, top=False)
    E += chamfer_box('mag_lower', (7.05, 2.05, -2.1), (8.95, 5.3, 1.8), 0.15, top=False, bottom=True)
    E.append(box('mag_cell_l', (7.0, 3.0, -1.6), (7.05, 4.6, 1.3)))
    E.append(box('mag_cell_r', (8.95, 3.0, -1.6), (9.0, 4.6, 1.3)))
    E.append(box('mag_latch', (7.15, 6.6, -1.65), (8.85, 7.4, -1.55)))
    return tidy(E)


def model2world(name, p): return M(p)


NAVY, NAVY2, WHITE, PINK, BLACK, GREY = (56, 64, 84), (78, 88, 108), (214, 206, 204), (220, 196, 192), (40, 40, 42), (96, 98, 104)
CAMO = ('shroud', 'recv_front', 'recv_rear', 'cage_top', 'cage_low', 'barrel_core', 'mag_upper', 'mag_lower')
MATS = [(('muzzle', 'rail', 'stock_strut', 'frame_strip', 'sight_base'), PINK),
        (('cage_post', 'grip', 'trigger', 'guard', 'lower_band', 'frame', 'stock', 'butt', 'sight_ear', 'mag_latch'), BLACK),
        (('cage_bolt', 'recv_pin'), GREY)]


# r5: material response is assigned per part; only identity accents use exact special texels.
from identity import geometry as _identity_geometry
from materials9 import MATERIALS as _MATERIALS, choose as _choose_material, decal as _decal, register as _register
_base_elements = elements
T = 20
ATLAS = 1024
STYLE = 'material'
MATERIALS = _MATERIALS['nox_cordis_ii']
_register('nox_cordis_ii', model2world)
def elements(): return _identity_geometry('nox_cordis_ii', _base_elements())
def material(name, face): return _choose_material('nox_cordis_ii', name, face)
def special(e, fn, s, t): return _decal('nox_cordis_ii', e, fn, s, t)
