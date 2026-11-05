"""W325 Nox Lumen II (High-Impact fusion rifle, rare, Omolon) over base erentil_fr4 (W189/W217 reload + W153 sight).

Rip at a uniform 33 px/m: front cap z -9.1 / butt 15.5 (base -9.41..15.56), top 13.5 (rip front sight 14.55).
Anchor y 14.6 = rip Z 0.205, z 6.9 = rip Y -0.0084. As in D2, the battery ("Magazine" mesh) is the whole lower module
under the receiver (z -1.5..8.4, y 3.45..7.2): it becomes the moving magazine leaf in place of the base's thin cartridge
(z 2.02..3.38, y 2.79..7.55), and it drops as one block. Real C-frame opening z 4..6.3, y 6.7..8.75. W153 ADS aim tip
(z 2.4..2.52, y 14.2..14.52) is kept as overlay and framed by the rip front sight ears (centre open above 13.9).
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_w9'))
from w9 import tidy, box, bar, post, chamfer_box, RipMap, lens, flat, material, model_pt
PALETTE = 12
FLAT_TOL = 28

M = RipMap(33.0, (14.6, 6.9), (0.205, -0.0084), '-y')
T = 14


def elements():
    E = []
    # --- white front cap (stepped) with muzzle nub and pointed lower fin
    E.append(box('muzzle_nub', (7.55, 11.05, -9.15), (8.45, 11.95, -8.6)))
    E.append(box('muzzle_nub_ring', (7.48, 10.98, -8.75), (8.52, 12.02, -8.6)))
    E += chamfer_box('cap', (7.2, 10.2, -8.6), (8.8, 13.3, -7.15), 0.15, bottom=True)
    E.append(box('cap_step_l', (7.1, 11.0, -8.3), (7.2, 12.9, -7.3)))
    E.append(box('cap_step_r', (8.8, 11.0, -8.3), (8.9, 12.9, -7.3)))
    E.append(post('cap_fin', 7.4, 8.6, (-7.45, 10.3), (-7.9, 8.4), 0.42))
    # --- long dark shroud: core + top plates in 3 panels + toothed rail + side vent rows + end lip
    E.append(box('shroud', (6.7, 10.3, -7.15), (9.3, 13.2, 2.0)))
    E += chamfer_box('shroud_top', (6.7, 13.2, -7.15), (9.3, 13.45, 2.0), 0.0, top=False)
    for k, (za, zb) in enumerate(((-7.0, -4.1), (-3.95, -1.05), (-0.9, 1.9))):
        E.append(box(f'shroud_plate_{k}', (7.0, 13.2, za), (9.0, 13.42, zb)))
    for sd, (a, b) in (('l', (6.65, 6.7)), ('r', (9.3, 9.35))):
        E.append(box(f'shroud_vents_{sd}', (a, 11.6, -6.4), (b, 12.3, -2.3)))
        E.append(box(f'shroud_line_{sd}', (a, 12.7, -7.0), (b, 12.8, 1.6)))
    E.append(box('shroud_lip', (6.65, 10.33, 1.85), (9.35, 13.3, 2.02)))
    E += chamfer_box('shroud_low', (6.85, 8.85, -7.15), (9.15, 10.0, -1.4), 0.12, top=False, bottom=True)
    for k in range(5):
        z = -6.8 + k * 1.05
        E.append(box(f'shroud_low_cell_{k}', (6.8, 9.05, z), (9.2, 9.8, z + 0.8)))
    E.append(box('rail_white', (6.8, 10.0, -7.15), (9.2, 10.3, -1.5)))
    E.append(box('rail_white_drop_a', (6.8, 9.55, -1.5), (9.2, 10.3, -0.85)))
    E.append(box('rail_white_drop_b', (6.8, 8.9, -0.85), (9.2, 9.55, -0.2)))
    E.append(box('canister', (6.55, 8.1, -1.45), (7.1, 9.25, -0.35)))
    E.append(box('canister_cap', (6.5, 8.2, -1.55), (7.0, 9.15, -1.45)))
    # --- receiver: front block (13.3) with grille, rear block dropped to 12.4 behind z 5.2 (base profile 12.46)
    E += chamfer_box('recv', (6.95, 9.85, 2.0), (9.05, 13.3, 5.2), 0.15)
    E.append(box('recv_grille', (6.9, 11.8, 2.6), (6.95, 12.9, 4.8)))
    E.append(box('recv_grille_r', (9.05, 11.8, 2.6), (9.1, 12.9, 4.8)))
    E.append(box('recv_slot', (6.9, 10.6, 3.2), (6.95, 10.85, 4.8)))
    E += chamfer_box('recv_rear', (7.15, 10.6, 5.2), (8.85, 12.4, 8.8), 0.12, segs=2)
    E.append(box('recv_rear_win', (7.1, 11.3, 5.6), (8.9, 11.8, 8.4)))
    E.append(box('recv_tail', (7.25, 11.5, 8.8), (8.75, 12.3, 9.5)))
    E.append(box('recv_tail_b', (7.25, 11.5, 9.5), (8.75, 12.0, 10.2)))
    E.append(box('recv_tail_low', (7.25, 10.6, 8.8), (8.75, 11.5, 10.2)))
    E += chamfer_box('mech', (7.15, 6.7, 0.3), (8.85, 9.85, 4.0), 0.12, top=False)
    for sd, (a, b) in (('l', (7.1, 7.15)), ('r', (8.85, 8.9))):
        E.append(box(f'mech_panel_{sd}', (a, 7.2, 1.0), (b, 8.4, 2.6)))
        E.append(box(f'mech_bolt_{sd}', (a, 8.8, 3.3), (b, 9.1, 3.6)))
    E.append(bar('arm_white', 6.95, 9.05, (2.75, 11.35), (0.05, 6.5), 0.45))
    # --- front sight: hollow two-ear frame around the W153 aim tip (open centre above 13.9)
    E.append(box('sight_base', (7.55, 13.45, 1.6), (8.45, 13.9, 2.75)))
    E.append(box('sight_ear_l', (7.55, 13.9, 2.27), (7.8, 14.55, 2.75)))
    E.append(box('sight_ear_r', (8.2, 13.9, 2.27), (8.45, 14.55, 2.75)))
    # --- trigger + raked grip with side texture
    E.append(post('trigger', 7.93, 8.07, (5.85, 9.85), (6.1, 8.9), 0.22))
    E.append(post('grip', 7.2, 8.8, (7.05, 9.9), (7.95, 5.45), 1.6))
    E.append(post('grip_tex_l', 7.15, 7.2, (7.05, 9.9), (7.95, 5.45), 0.9, ext=(-1.3, -0.8)))
    E.append(post('grip_tex_r', 8.8, 8.85, (7.05, 9.9), (7.95, 5.45), 0.9, ext=(-1.3, -0.8)))
    # --- stock: top tube, diagonal strut, ribbed butt
    E += chamfer_box('stock_tube', (7.55, 10.7, 10.2), (8.45, 11.9, 14.4), 0.1, segs=2)
    E.append(bar('stock_strut', 7.55, 8.45, (11.6, 10.9), (14.4, 8.1), 0.7, ext=(0, .1)))
    E += chamfer_box('stock_butt', (7.25, 8.0, 14.0), (8.75, 11.75, 15.0), 0.12, bottom=True)
    E.append(box('butt_pad', (7.45, 7.75, 15.0), (8.55, 11.45, 15.5)))
    for k in range(5):
        y = 8.0 + k * 0.7
        E.append(box(f'butt_rib_{k}', (7.4, y, 15.5), (8.6, y + 0.35, 15.58)))
    # --- battery = lower module (moving magazine leaf)
    E += chamfer_box('mag_block', (7.2, 4.2, 0.4), (8.8, 6.2, 7.6), 0.12, top=False, segs=1)
    for k, (za, yb) in enumerate(((-1.3, 5.3), (-0.6, 4.55), (0.1, 3.8))):   # stepped battery nose (shared edges)
        E.append(box(f'mag_nose_{k}', (7.2, yb, za), (8.8, 6.2, za + 0.7 if k < 2 else 0.4)))
    E.append(box('mag_belly', (7.25, 3.45, 0.2), (8.75, 4.2, 2.3)))
    E.append(box('mag_rail', (7.1, 6.2, 0.15), (8.9, 6.7, 8.4)))
    E.append(box('mag_tail', (7.3, 4.05, 7.6), (8.7, 6.2, 8.4)))
    E.append(box('mag_win_l', (7.15, 4.7, 4.6), (7.2, 5.7, 7.0)))
    E.append(box('mag_win_r', (8.8, 4.7, 4.6), (8.85, 5.7, 7.0)))
    return tidy(E)


def model2world(name, p): return M(p)


GUN, GUN2, WHITE, BLACK, GREY = (78, 74, 70), (64, 61, 58), (196, 198, 198), (34, 33, 32), (112, 108, 102)
MATS = [(('muzzle_nub_ring', 'cap', 'rail_white', 'arm_white', 'mag_rail', 'canister', 'shroud_line'), WHITE),
        (('shroud', 'recv', 'mech', 'mag_block', 'mag_nose', 'mag_belly', 'mag_tail', 'stock_tube', 'stock_butt'), GUN),
        (('grip', 'trigger', 'stock_strut', 'butt', 'sight', 'muzzle_nub'), BLACK)]


# r5: material response is assigned per part; only identity accents use exact special texels.
from identity import geometry as _identity_geometry
from materials9 import MATERIALS as _MATERIALS, choose as _choose_material, decal as _decal, register as _register
_base_elements = elements
T = 20
ATLAS = 1024
STYLE = 'material'
MATERIALS = _MATERIALS['nox_lumen_ii']
_register('nox_lumen_ii', model2world)
def elements(): return _identity_geometry('nox_lumen_ii', _base_elements())
def material(name, face): return _choose_material('nox_lumen_ii', name, face)
def special(e, fn, s, t): return _decal('nox_lumen_ii', e, fn, s, t)
