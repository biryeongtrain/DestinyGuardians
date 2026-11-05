"""W325 Parsec TSu (High-Impact fusion rifle, rare, Häkke) over base erentil_fr4 (W189/W217 reload + W153 sight).

Rip at a uniform 36 px/m: muzzle z -9.05 / butt 14.6 (base -9.41..15.56), anchor y 14.6 = rip Z 0.205,
z -9.4 = rip Y -0.4778. The rip "Magazine" mesh is the lower battery block (z 0.2..9.4, y 2.45..5.4): it becomes the
moving magazine leaf in place of the base's thin cartridge (z 2.02..3.38, y 2.79..7.55) and drops as one block.
White frame strip (y 5.4..5.75) and the front frame block stay on the body. Grip post (8.6,9.4)->(9.8,6.0) over the
base grip. W153 aim tip (z 2.4..2.52, y 14.2..14.52) kept as overlay, framed by sight ears (top 14.55, centre open
above 13.85); the rip TrueSight post behind it is left out so the eye line stays clear.
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_w9'))
from w9 import tidy, box, bar, post, chamfer_box, RipMap, lens, flat, material, camo, model_pt
PALETTE = 12
FLAT_TOL = 24
PALETTE_KEEP = [(204, 102, 40)]

M = RipMap(36.0, (14.6, -9.4), (0.205, -0.4778), '-y')
T = 14


def elements():
    E = []
    # --- front: lower white bumper with bore rod, dark face plate with vent rows
    E.append(box('bore_rod', (7.8, 8.75, -9.05), (8.2, 9.3, -8.55)))
    E += chamfer_box('bumper', (7.15, 8.55, -8.6), (8.85, 9.7, -7.5), 0.12, bottom=True)
    E.append(box('face_plate', (6.9, 9.7, -8.25), (9.1, 12.8, -7.55)))
    for k in range(4):
        y = 10.1 + k * 0.62
        E.append(box(f'face_vent_{k}', (7.2, y, -8.3), (8.8, y + 0.3, -8.25)))
    # --- big white shroud: core, chamfered top in 2 panels, toothed rail, side window panel + recessed strips
    E.append(box('shroud', (6.55, 8.4, -7.55), (9.45, 12.8, 1.6)))
    E += chamfer_box('shroud_top', (6.55, 12.8, -7.55), (9.45, 13.3, 1.6), 0.2, segs=2)
    E.append(box('rail_top', (7.4, 13.3, -7.5), (8.6, 13.36, 1.4)))
    for i in range(9):
        z = -7.3 + i * 0.95
        E.append(box(f'rail_tooth_{i}', (7.45, 13.36, z), (8.55, 13.45, z + 0.5)))
    for sd, (a, b) in (('l', (6.5, 6.55)), ('r', (9.45, 9.5))):
        E.append(box(f'shroud_window_{sd}', (a, 10.3, -2.6), (b, 12.0, 0.6)))
        E.append(box(f'shroud_strip_hi_{sd}', (a, 11.5, -7.1), (b, 11.75, -3.2)))
        E.append(box(f'shroud_strip_lo_{sd}', (a, 10.5, -7.1), (b, 10.75, -3.2)))
        E.append(box(f'shroud_square_{sd}', (a + 0.01, 10.95, -1.5), (b - 0.01, 11.45, -1.0)))
    E.append(box('under_lip', (6.95, 8.0, -7.6), (9.05, 8.4, -1.4)))
    for k, (za, yb) in enumerate(((-1.4, 7.45), (-0.4, 6.7), (0.5, 5.9))):
        E.append(box(f'under_step_{k}', (6.95, yb, za), (9.05, 8.4, za + 1.0 if k < 2 else 1.3)))
    # --- receiver (front block 13.3, rear dropped to 12.4 behind z 4.4), front sight, side box
    E += chamfer_box('recv_front', (6.65, 8.5, 1.6), (9.35, 12.8, 3.8), 0.15)
    E.append(box('recv_top', (7.0, 12.8, 1.6), (9.0, 13.3, 4.0)))
    E += chamfer_box('recv', (6.65, 9.5, 3.8), (9.35, 12.4, 7.5), 0.15)
    E.append(box('recv_disc_l', (6.6, 10.2, 4.7), (6.65, 10.9, 5.4)))
    E.append(box('recv_vents_l', (6.6, 11.3, 5.8), (6.65, 12.1, 7.2)))
    E.append(box('recv_vents_r', (9.35, 11.3, 5.8), (9.4, 12.1, 7.2)))
    E.append(box('guard_bar', (7.9, 8.2, 3.8), (8.1, 8.36, 7.3)))
    E += chamfer_box('recv_rear', (6.75, 9.5, 7.5), (9.25, 12.4, 9.0), 0.15)
    E.append(box('recv_rear_band', (6.7, 9.53, 7.5), (9.3, 12.35, 7.75)))
    E.append(box('sight_base', (7.55, 13.3, 1.5), (8.45, 13.85, 3.0)))
    E.append(box('sight_ear_l', (7.55, 13.85, 2.27), (7.8, 14.55, 2.8)))
    E.append(box('sight_ear_r', (8.2, 13.85, 2.27), (8.45, 14.55, 2.8)))
    E.append(box('side_box', (9.35, 7.0, 3.4), (9.55, 8.4, 4.1)))
    # --- lower frame front block + strip (stay on the body)
    E += chamfer_box('frame_front', (6.75, 5.75, 1.3), (9.25, 8.5, 4.0), 0.12, top=False, bottom=True)
    E.append(box('frame_pin_l', (6.7, 7.4, 2.0), (6.75, 7.7, 2.3)))
    E.append(box('frame_pin_r', (9.25, 7.4, 2.0), (9.3, 7.7, 2.3)))
    E.append(box('frame_strip', (6.65, 5.4, 0.3), (9.35, 5.75, 9.0)))
    # --- trigger, grip with texture rows
    E.append(post('trigger', 7.93, 8.07, (6.1, 9.5), (6.4, 8.5), 0.2))
    E.append(post('grip', 7.25, 8.75, (8.35, 9.5), (9.3, 5.9), 1.5))
    E.append(post('grip_tex_l', 7.2, 7.25, (8.35, 9.5), (9.3, 5.9), 0.8, ext=(-0.75, -0.6)))
    E.append(post('grip_tex_r', 8.75, 8.8, (8.35, 9.5), (9.3, 5.9), 0.8, ext=(-0.75, -0.6)))
    # --- stock: top tube, butt, dark rear post with ribs, white lower wedge
    E += chamfer_box('stock_tube', (7.25, 11.0, 9.0), (8.75, 12.4, 13.0), 0.12)
    E.append(box('stock_tube_slot', (7.2, 11.4, 10.0), (7.25, 11.9, 12.2)))
    E.append(box('stock_post', (7.25, 6.3, 12.3), (8.75, 11.0, 13.4)))
    for k in range(4):
        y = 6.8 + k * 1.0
        E.append(box(f'stock_post_rib_{k}', (7.2, y, 12.5), (8.8, y + 0.4, 13.2)))
    E += chamfer_box('stock_butt', (7.25, 10.4, 13.4), (8.75, 12.4, 14.6), 0.12)
    for k, (za, zb, yt) in enumerate(((9.85, 10.75, 6.15), (10.75, 11.55, 6.75), (11.55, 12.3, 7.35))):
        E.append(box(f'stock_wedge_{k}', (7.25, 5.4, za), (8.75, yt, zb)))   # stepped lower stock, shared edges
    # --- battery block (moving magazine leaf)
    E += chamfer_box('mag_main', (6.6, 2.45, 0.2), (9.4, 5.4, 8.2), 0.15, top=False, bottom=True)
    E.append(box('mag_tail_a', (6.6, 3.2, 8.2), (9.4, 5.4, 8.8)))
    E.append(box('mag_tail_b', (6.6, 4.1, 8.8), (9.4, 5.4, 9.4)))
    E.append(box('mag_slot_a', (6.55, 2.95, 5.2), (6.6, 3.3, 6.4)))
    E.append(box('mag_slot_b', (6.55, 2.95, 6.7), (6.6, 3.3, 7.6)))
    E.append(box('mag_stripe', (6.9, 2.4, 6.0), (9.1, 2.45, 7.9)))
    return tidy(E)


def model2world(name, p): return M(p)


WHITE, MINT, GREEN, DARK, BLACK, ORANGE = (206, 214, 212), (176, 196, 186), (138, 152, 142), (40, 48, 44), (24, 28, 26), (204, 102, 40)
MATS = [(('face_plate', 'under_lip', 'under_step', 'recv_rear_band', 'guard_bar', 'trigger', 'grip', 'stock_post',
          'frame_strip', 'sight_ear', 'side_box', 'bore_rod'), DARK),
        (('shroud_strip', 'shroud_square'), MINT)]


# r5: material response is assigned per part; only identity accents use exact special texels.
from identity import geometry as _identity_geometry
from materials9 import MATERIALS as _MATERIALS, choose as _choose_material, decal as _decal, register as _register
_base_elements = elements
T = 20
ATLAS = 1024
STYLE = 'material'
MATERIALS = _MATERIALS['parsec_tsu']
_register('parsec_tsu', model2world)
def elements(): return _identity_geometry('parsec_tsu', _base_elements())
def material(name, face): return _choose_material('parsec_tsu', name, face)
def special(e, fn, s, t): return _decal('parsec_tsu', e, fn, s, t)
