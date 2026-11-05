"""W325 Damietta-LR2 (Aggressive sniper, rare) over base bite_of_the_fox (W177/W214 reload: body + magazine).

Rip at a uniform 18.75 px/m: muzzle z -15.25, butt z 13.5 (rip shifted +0.3 px so the thumbhole grip post lands on the
base grip, z 8.05..8.85). Vertical datum y 12.2 = rip Z 0.25. Magazine kept at its rip place (z 4.25..6.4) around the
base moving magazine (z 4.12..5.79, y 7.63..8.89). Bipod: folded front leg + splayed feet + rear leg.
r2 (detail + ADS + W30 pixel style): the rip scope (rip-frame z 4.3..9.15, top 12.22) is moved forward into the base
scope box z 0.6..6.3 with top 11.9 (SCOPE_Z / SCOPE_DY warp the projection), mount/receiver tail lowered to the base
profile (10.2), top cover starts behind z -1.6. Big slabs split into DMW-style segments with 1-step chamfer plates;
paint = flat Arctic camo blobs (pale blue / teal) over brown furniture.
Sniper first-person ADS hides the gun (W45): the scope matters for hip/3P only.
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_w9'))
from w9 import tidy, box, bar, post, segbar, chamfer_box, RipMap, lens, zwarp, flat, material, camo, model_pt

M = RipMap(18.75, (12.2, -15.2), (0.25, -1.26), '-y')
T = 16
PALETTE = 14
FLAT_TOL = 28
PALETTE_KEEP = [(34, 58, 74), (20, 30, 40), (16, 16, 18)]
SCOPE_Z = zwarp([(0.6, 4.3), (1.8, 5.6), (4.4, 7.2), (5.0, 8.0), (6.3, 9.15)])
SCOPE_DY = 0.32


def elements():
    E = []
    # --- muzzle brake (banded) + barrel
    E.append(box('brake_tip', (7.66, 9.05, -15.25), (8.34, 9.8, -15.1)))
    E += chamfer_box('brake', (7.6, 9.0, -15.1), (8.4, 9.85, -12.6), 0.1, segs=2, gap=0.25)
    E.append(box('brake_band_a', (7.56, 9.1, -14.55), (8.44, 9.9, -14.3)))
    E.append(box('brake_band_b', (7.56, 9.1, -13.2), (8.44, 9.9, -12.95)))
    E.append(box('barrel', (7.74, 9.15, -12.6), (8.26, 9.72, -1.9)))
    E.append(box('barrel_collar', (7.68, 9.1, -2.3), (8.32, 9.78, -1.9)))
    # --- folded front bipod leg
    E.append(box('fold_hinge', (7.6, 8.72, -11.45), (8.4, 9.15, -10.95)))
    E.append(box('fold_leg', (7.5, 8.55, -10.95), (8.5, 8.78, -5.75)))
    for i in range(4):
        z = -10.2 + i * 1.1
        E.append(box(f'fold_hole_{i}', (7.46, 8.6, z), (8.54, 8.73, z + 0.4)))
    E.append(bar('fold_tab', 7.55, 8.45, (-6.2, 8.78), (-5.95, 9.15), 0.18, ext=(.05, .05)))
    E.append(box('fold_foot', (7.68, 8.5, -5.75), (8.32, 8.82, -5.4)))
    # --- truss handguard: frame bars around a recessed core (real side depth), top cover behind z -1.6
    E.append(box('hg_core', (7.45, 9.15, -1.9), (8.55, 10.05, 3.3)))
    for side, (a, b) in (('l', (7.3, 7.45)), ('r', (8.55, 8.7))):
        E.append(box(f'hg_rail_top_{side}', (a, 9.9, -1.9), (b, 10.2, 3.3)))
        E.append(box(f'hg_rail_bot_{side}', (a, 9.0, -1.9), (b, 9.3, 3.3)))
        E.append(box(f'hg_post_f_{side}', (a, 9.3, -1.9), (b, 9.9, -1.55)))
        E.append(box(f'hg_post_r_{side}', (a, 9.3, 2.9), (b, 9.9, 3.3)))
        E.append(bar(f'hg_truss_a_{side}', a, b, (-1.55, 9.32), (0.6, 9.88), 0.14))
        E.append(bar(f'hg_truss_b_{side}', a, b, (0.6, 9.88), (2.9, 9.32), 0.14))
    E.append(box('hg_floor', (7.45, 9.0, -1.9), (8.55, 9.15, 3.3)))
    E += chamfer_box('top_cover', (7.6, 10.2, -1.5), (8.4, 10.7, 1.95), 0.1, segs=2)
    E.append(box('top_cover_tail', (7.7, 10.2, 1.95), (8.3, 10.42, 2.25)))
    # --- deployed bipod under the handguard
    E.append(box('bip_mount', (7.45, 7.95, -1.0), (8.55, 9.0, 1.1)))
    E.append(bar('bip_leg_l', 6.95, 7.35, (0.0, 8.3), (-1.65, 7.3), 0.36, ext=(.1, 0)))
    E.append(bar('bip_leg_r', 8.65, 9.05, (0.0, 8.3), (-1.65, 7.3), 0.36, ext=(.1, 0)))
    E.append(box('bip_foot_l', (6.88, 7.12, -1.95), (7.42, 7.3, -1.45)))
    E.append(box('bip_foot_r', (8.58, 7.12, -1.95), (9.12, 7.3, -1.45)))
    E.append(box('bip_rod', (6.95, 8.0, 1.1), (7.3, 8.36, 3.6)))
    E.append(box('bip_rod_cap', (6.88, 7.92, 3.6), (7.38, 8.45, 3.95)))
    E.append(box('bip_rod_link', (7.3, 8.08, 1.1), (7.45, 8.28, 1.5)))
    # --- receiver: chamfered roof in two panels, ejection port, bolt
    E += chamfer_box('recv_upper', (7.35, 9.95, 3.3), (8.65, 10.62, 7.3), 0.12, segs=2)
    E.append(box('recv_spine', (7.6, 10.62, 5.6), (8.4, 10.72, 6.8)))
    E.append(box('recv_front', (7.35, 8.85, 3.3), (8.65, 9.95, 4.2)))
    E.append(box('recv_port', (7.55, 9.35, 4.2), (8.45, 9.95, 6.2)))
    E.append(box('recv_sill', (7.35, 8.85, 4.2), (8.65, 9.35, 6.2)))
    E.append(box('recv_rear', (7.35, 8.85, 6.2), (8.65, 9.95, 7.3)))
    E.append(box('recv_pin_a', (7.3, 9.05, 6.55), (7.35, 9.25, 6.75)))
    E.append(box('recv_pin_b', (8.65, 9.05, 6.55), (8.7, 9.25, 6.75)))
    E.append(box('bolt_lever', (8.65, 9.45, 4.4), (9.05, 9.62, 4.7)))
    E.append(box('bolt_knob', (8.98, 9.2, 4.33), (9.42, 9.76, 4.77)))
    E += chamfer_box('recv_tail', (7.4, 8.75, 7.3), (8.6, 10.18, 9.6), 0.1)
    E.append(box('mount_base', (7.6, 10.62, 0.9), (8.4, 10.92, 5.6)))
    # --- trigger group
    E.append(box('guard_front', (7.9, 7.6, 6.38), (8.1, 8.85, 6.52)))
    E.append(box('guard_bot', (7.9, 7.6, 6.52), (8.1, 7.74, 7.95)))
    E.append(box('guard_rear', (7.9, 7.74, 7.8), (8.1, 8.2, 7.95)))
    E.append(post('trigger', 7.93, 8.07, (7.3, 8.75), (7.5, 8.2), 0.15))
    # --- thumbhole stock (top <= base 10.45)
    E.append(post('stock_grip', 7.45, 8.55, (8.05, 8.85), (8.85, 6.85), 0.85))
    for k, (za, zb, yb) in enumerate(((8.8, 10.05, 6.9), (10.05, 11.3, 7.1), (11.3, 12.45, 7.3))):
        E.append(box('stock_lower' + ('' if k == 0 else f'_{k}'), (7.5, yb, za), (8.5, yb + 0.62, zb)))
    E += chamfer_box('stock_upper', (7.55, 8.78, 9.4), (8.45, 10.05, 12.4), 0.1)
    for k, z in enumerate((9.9, 11.0)):
        E.append(box(f'stock_pad_{k}', (7.42, 8.85, z), (8.58, 10.12, z + 0.75)))
        E.append(box(f'stock_pad_{k}_lip', (7.48, 10.12, z + 0.08), (8.52, 10.2, z + 0.67)))
    E += chamfer_box('stock_butt', (7.45, 7.3, 12.4), (8.55, 10.12, 13.3), 0.1, bottom=True)
    E.append(box('butt_pad', (7.5, 7.36, 13.3), (8.5, 10.05, 13.5)))
    # --- scope (moved forward into the base scope box, top 11.9)
    E += chamfer_box('sc_obj', (7.4, 10.95, 0.6), (8.6, 11.9, 1.8), 0.12)
    E.append(box('sc_obj_ring', (7.34, 10.9, 0.62), (8.66, 11.0, 0.8)))
    E.append(box('sc_body', (7.5, 11.0, 1.8), (8.5, 11.75, 4.4)))
    E.append(box('sc_ring_f', (7.45, 10.92, 2.2), (8.55, 11.82, 2.5)))
    E.append(box('sc_turret_top', (7.75, 11.75, 3.0), (8.25, 11.9, 3.6)))
    E.append(box('sc_turret_side', (7.15, 11.1, 3.0), (7.5, 11.6, 3.6)))
    E.append(box('sc_ring_r', (7.45, 10.92, 4.4), (8.55, 11.85, 5.0)))
    E.append(box('sc_eyepiece', (7.55, 11.1, 5.0), (8.45, 11.85, 6.3)))
    # --- magazine (moving leaf)
    E.append(box('mag_body', (7.55, 7.45, 4.3), (8.45, 8.9, 6.3)))
    E.append(box('mag_floor', (7.5, 6.85, 4.25), (8.5, 7.45, 5.35)))
    E.append(box('mag_floor_b', (7.5, 6.72, 5.35), (8.5, 7.45, 6.4)))
    E.append(box('mag_window', (7.51, 7.9, 4.7), (7.55, 8.5, 5.9)))
    return tidy(E)


def model2world(name, p):
    if name.startswith('sc_'):
        p = (p[0], p[1] + SCOPE_DY, SCOPE_Z(p[2]))
    return M(p)


ICE, ICE2, TEAL, BROWN, DARK, BLACK = (178, 206, 222), (150, 182, 198), (72, 92, 98), (94, 86, 80), (60, 56, 52), (32, 30, 28)
CAMO = ('brake', 'barrel', 'hg_rail', 'hg_post', 'hg_truss', 'top_cover', 'recv_upper', 'recv_spine', 'recv_front',
        'recv_sill', 'recv_rear', 'stock_pad', 'stock_butt', 'sc_obj', 'sc_body', 'mag_floor')
MATS = [(('brake_band', 'barrel_collar', 'fold_', 'bip_', 'bolt_lever', 'guard', 'trigger', 'stock_grip', 'stock_lower',
          'stock_upper', 'recv_tail', 'butt_pad', 'sc_ring', 'sc_turret', 'sc_eyepiece', 'mount_base', 'mag_body',
          'top_cover_tail', 'recv_pin'), BROWN),
        (('hg_core', 'hg_floor', 'recv_port', 'mag_window'), DARK),
        (('bolt_knob',), (220, 226, 228))]


# r5: material response is assigned per part; only identity accents use exact special texels.
from identity import geometry as _identity_geometry
from materials9 import MATERIALS as _MATERIALS, choose as _choose_material, decal as _decal, register as _register
_base_elements = elements
T = 20
ATLAS = 1024
STYLE = 'material'
MATERIALS = _MATERIALS['damietta_lr2']
_register('damietta_lr2', model2world)
def elements(): return _identity_geometry('damietta_lr2', _base_elements())
def material(name, face): return _choose_material('damietta_lr2', name, face)
def special(e, fn, s, t): return _decal('damietta_lr2', e, fn, s, t)
