"""W325 Tongeren-LR3 (Rapid-Fire sniper, rare) over base apostate (W185/W215 reload: body + magazine).

Rip at a uniform 23.2 px/m; solids are authored in the rip frame (muzzle z -15.5) and shifted DZ=+0.4 px so the
thumbhole grip post lands on the base grip and the butt on z 13.5 (muzzle -15.1 vs base -15.49). Vertical datum
y 12.4 = rip Z 0.25. Magazine kept at the rip place (z 2.5..5.1 after shift), inside the base moving magazine span
(z 0.54..5.04, y 6.88..9.1, x 7.49..8.52). Sniper first-person ADS hides the gun (W45): scope is hip/3P only.
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_w9'))
from w9 import tidy, box, bar, post, segbar, chamfer_box, RipMap, lens, zwarp, flat, material, model_pt
PALETTE = 14
FLAT_TOL = 28
PALETTE_KEEP = [(34, 58, 74), (20, 30, 40), (16, 16, 18)]

M = RipMap(23.2, (12.4, -15.45), (0.25, -0.97), '-y')
DZ = 0.4
T = 16


SCOPE_Z = zwarp([(2.1, 2.0), (3.3, 3.4), (5.0, 6.6), (6.0, 7.6)])   # rip-frame z of the compressed scope


def _rip_frame():
    E = []
    # --- long boxy shroud in segments: open front window shows the barrel and its two collars
    E.append(box('barrel_tip', (7.68, 8.6, -15.5), (8.32, 9.6, -15.0)))
    E.append(box('barrel', (7.72, 8.8, -15.0), (8.28, 9.32, -4.0)))
    E.append(box('collar_a', (7.62, 8.68, -13.3), (8.38, 9.44, -12.6)))
    E.append(box('collar_b', (7.62, 8.68, -11.3), (8.38, 9.44, -10.8)))
    E.append(box('collar_c', (7.66, 8.72, -14.4), (8.34, 9.4, -14.1)))
    E += chamfer_box('shroud_top', (7.5, 9.32, -15.0), (8.5, 10.3, -4.2), 0.12, segs=3, gap=0.12)
    E.append(box('shroud_end_top', (7.46, 9.6, -15.08), (8.54, 10.2, -14.95)))
    E += chamfer_box('shroud_bot', (7.5, 7.8, -14.6), (8.5, 8.8, -4.2), 0.12, top=False, bottom=True)
    E.append(box('shroud_wall_l', (7.5, 8.8, -10.8), (7.72, 9.32, -4.2)))
    E.append(box('shroud_wall_r', (8.28, 8.8, -10.8), (8.5, 9.32, -4.2)))
    E.append(box('shroud_strip', (7.46, 7.62, -14.2), (8.54, 7.8, -4.2)))
    for sd, x in (('l', (7.46, 7.5)), ('r', (8.5, 8.54))):
        E.append(box(f'shroud_slot_{sd}', (x[0], 9.75, -8.6), (x[1], 10.05, -5.6)))
    E.append(bar('shroud_ramp', 7.45, 8.55, (-5.0, 10.3), (-4.0, 10.8), 0.3, 'below', ext=(0, .05)))
    E += chamfer_box('shroud_raise', (7.45, 10.3, -4.05), (8.55, 10.8, -1.0), 0.1)
    E.append(box('sight_band', (7.35, 10.0, -2.45), (8.65, 10.82, -1.9)))
    E.append(box('sight_band_lip_l', (7.31, 10.1, -2.4), (7.35, 10.7, -1.95)))
    E.append(box('sight_band_lip_r', (8.65, 10.1, -2.4), (8.69, 10.7, -1.95)))
    # --- under-shroud skid with a through slot, hinge post
    E.append(box('skid_top', (7.6, 7.15, -10.75), (8.4, 7.62, -4.4)))
    E.append(box('skid_bot', (7.6, 6.55, -10.75), (8.4, 6.8, -4.4)))
    E.append(box('skid_front', (7.6, 6.8, -10.75), (8.4, 7.15, -10.1)))
    E.append(box('skid_rear', (7.6, 6.8, -5.5), (8.4, 7.15, -4.4)))
    E.append(box('skid_pin', (7.55, 6.85, -7.7), (8.45, 7.05, -7.5)))
    E.append(box('hinge_post', (7.7, 6.4, -2.15), (8.3, 7.05, -1.7)))
    # --- receiver core with dark side armour plates (stepped)
    E.append(box('core', (7.3, 7.05, -4.2), (8.7, 10.75, 1.9)))
    for sd, (a, b) in (('l', (7.05, 7.3)), ('r', (8.7, 8.95))):
        E.append(box(f'plate_up_{sd}', (a, 8.6, -4.0), (b, 10.55, 1.9)))
        for k, (za, yb) in enumerate(((-3.1, 8.3), (-2.2, 8.0))):   # axis-aligned steps instead of a crossing slab
            E.append(box(f'plate_step_{sd}{k}', (a, yb, za), (b, 8.6, za + 0.9)))
        E.append(box(f'plate_step_{sd}2', (a, 7.75, -1.3), (b, 8.6, 1.9)))
        o = 0.05 if sd == 'r' else -0.05
        E.append(box(f'plate_inset_{sd}', (min(a, a + o), 9.3, -0.9), (max(b, b + o), 10.2, 1.5)))
        E.append(box(f'plate_bolt_{sd}', (min(a, a + 2 * o), 10.25, -3.6), (max(b, b + 2 * o), 10.4, -3.45)))
    E += chamfer_box('recv_upper', (7.35, 9.2, 1.9), (8.65, 10.2, 7.0), 0.1, segs=2)
    E.append(box('recv_rail', (7.6, 10.2, 2.0), (8.4, 10.3, 6.0)))
    for i in range(6):
        z = 2.15 + i * 0.6
        E.append(box(f'recv_rail_tooth_{i}', (7.62, 10.3, z), (8.38, 10.42, z + 0.3)))
    E.append(box('recv_port', (7.55, 8.6, 1.9), (8.45, 9.2, 4.2)))
    E.append(box('recv_mid', (7.35, 8.6, 4.2), (8.65, 9.2, 7.0)))
    E.append(box('recv_lower', (7.35, 7.6, 1.9), (8.65, 8.6, 6.9)))
    E.append(box('bolt_lever', (8.65, 8.85, 1.95), (9.4, 9.05, 2.2)))
    E.append(box('bolt_knob', (9.3, 8.7, 1.85), (9.75, 9.2, 2.35)))
    # --- trigger group
    E.append(box('guard_front', (7.9, 7.0, 4.85), (8.1, 7.6, 5.05)))
    E.append(box('guard_bot', (7.9, 6.95, 5.05), (8.1, 7.1, 6.9)))
    E.append(box('guard_loop', (7.92, 6.6, 4.9), (8.08, 6.95, 5.6)))
    E.append(post('trigger', 7.93, 8.07, (5.75, 8.1), (6.05, 7.5), 0.18))
    # --- thumbhole stock: hex-panel upper, lower arm, butt (top <= base 10.37)
    E.append(post('stock_grip', 7.4, 8.6, (6.95, 7.7), (7.55, 5.75), 0.95))
    E.append(bar('stock_lower', 7.45, 8.55, (7.8, 5.75), (11.4, 6.5), 0.72, 'above', ext=(0, .05)))
    E.append(box('stock_lower_rear', (7.45, 6.5, 11.35), (8.55, 7.2, 12.3)))
    E += chamfer_box('stock_upper', (7.15, 7.95, 6.9), (8.85, 9.9, 8.5), 0.12)
    E.append(box('stock_neck', (7.2, 7.95, 8.5), (8.8, 9.35, 8.8)))
    E += chamfer_box('stock_upper_b', (7.15, 7.95, 8.8), (8.85, 9.9, 12.3), 0.12)
    for sd, x in (('l', (7.1, 7.15)), ('r', (8.85, 8.9))):
        for k in range(3):
            z = 7.4 + k * 1.05
            E.append(box(f'stock_hex_{sd}{k}', (x[0], 8.35, z), (x[1], 9.5, z + 0.8)))
    E += chamfer_box('stock_butt', (7.15, 6.0, 12.3), (8.85, 9.95, 13.1), 0.12, bottom=True)
    E.append(box('butt_plate', (7.25, 6.1, 13.1), (8.75, 9.85, 13.15)))
    # --- scope (compressed into the base scope box, top 12.35, mount ends before the base drop)
    E += chamfer_box('scope_obj', (7.4, 10.85, 2.1), (8.6, 12.35, 3.3), 0.14)
    E.append(box('scope_obj_rim', (7.34, 10.8, 2.12), (8.66, 12.0, 2.25)))
    E += chamfer_box('scope_body', (7.5, 11.0, 3.3), (8.5, 12.25, 5.0), 0.1)
    E.append(box('scope_turret', (7.02, 11.3, 3.8), (7.5, 11.9, 4.4)))
    E.append(box('scope_turret_cap', (6.95, 11.35, 3.85), (7.02, 11.85, 4.35)))
    E += chamfer_box('scope_hood', (7.55, 11.2, 5.0), (8.45, 12.3, 6.0), 0.1)
    E.append(box('scope_mount', (7.6, 10.42, 3.4), (8.4, 11.0, 5.9)))
    # --- magazine (moving leaf)
    E.append(box('mag_body', (7.5, 6.0, 2.1), (8.5, 7.6, 4.7)))
    E.append(box('mag_lip', (7.46, 7.4, 2.05), (8.54, 7.6, 4.75)))
    return E


def _shift(e):
    e = dict(e); e['from'] = [e['from'][0], e['from'][1], e['from'][2] + DZ]; e['to'] = [e['to'][0], e['to'][1], e['to'][2] + DZ]
    if 'rotation' in e:
        r = dict(e['rotation']); o = list(r['origin']); o[2] += DZ; r['origin'] = o; e['rotation'] = r
    return e


def elements(): return tidy([_shift(e) for e in _rip_frame()])


def model2world(name, p):
    z = p[2] - DZ
    if name.startswith('scope_'): z = SCOPE_Z(z)
    return M((p[0], p[1], z))


MAROON, MAROON2, BONE, DARK, GUN, BLACK = (112, 58, 54), (92, 46, 44), (176, 160, 136), (66, 66, 64), (48, 48, 47), (26, 26, 26)
MATS = [(('shroud_top', 'shroud_bot', 'shroud_end', 'shroud_ramp', 'shroud_raise', 'recv_upper', 'scope_obj', 'scope_body'), MAROON),
        (('sight_band', 'collar', 'barrel_tip', 'stock_butt', 'stock_upper', 'mag_body', 'mag_lip', 'guard_loop', 'bolt_knob',
          'scope_turret', 'plate_inset'), BONE),
        (('barrel', 'shroud_wall', 'shroud_strip', 'skid', 'hinge', 'core', 'plate', 'recv_rail', 'recv_port', 'recv_mid',
          'recv_lower', 'bolt_lever', 'guard', 'trigger', 'stock', 'butt_plate', 'scope_hood', 'scope_mount', 'sight_band_lip'), DARK)]


# r5: material response is assigned per part; only identity accents use exact special texels.
from identity import geometry as _identity_geometry
from materials9 import MATERIALS as _MATERIALS, choose as _choose_material, decal as _decal, register as _register
_base_elements = elements
T = 20
ATLAS = 1024
STYLE = 'material'
MATERIALS = _MATERIALS['tongeren_lr3']
_register('tongeren_lr3', model2world)
def elements(): return _identity_geometry('tongeren_lr3', _base_elements())
def material(name, face): return _choose_material('tongeren_lr3', name, face)
def special(e, fn, s, t): return _decal('tongeren_lr3', e, fn, s, t)
