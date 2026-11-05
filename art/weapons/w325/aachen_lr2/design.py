"""W325 Aachen-LR2 (Adaptive sniper, rare) over base beloved (W208 reload: body + magazine leaf).

Rip at a uniform 17.3 px/m: muzzle z -15.58, butt z 13.45 (base -15.5..13.5); vertical datum y 12.6 = rip Z 0.27 puts
barrel (y 9.4..10.3), trigger guard (y 7.9) and thumbhole stock on the base layout. Magazine re-placed onto the base
moving magazine (z 3.95..6.55, y 6.45..8.6) sampling the rip mag through MAG_Z.
r2 (detail + ADS): the rip scope (rip z 2.9..9.95) is compressed into the base scope box z 4.85..8.85, top <= 12.55,
via SCOPE_Z (z-warped projection) so nothing rises above the base top profile; stock/butt top lowered to 10.6.
Sniper first-person ADS hides the gun (WeaponScopes W45): the scope matters for hip/3P only.
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_w9'))
from w9 import tidy, box, bar, post, segbar, chamfer_box, RipMap, lens, palette, snapper, zwarp, flat, material, camo, model_pt

M = RipMap(17.3, (12.6, -15.5), (0.27, -1.40), '-y')
T = 16
MAG_Z = (4.0, 4.85, 2.25 / 2.55)
SCOPE_Z = zwarp([(4.95, 2.9), (6.05, 5.55), (7.0, 7.0), (8.5, 9.5), (8.85, 9.95)])
PALETTE = 14
FLAT_TOL = 28
PALETTE_KEEP = [(150, 30, 28), (34, 58, 74), (16, 16, 18)]


def elements():
    E = []
    # --- muzzle brake: crown with bore, two real lateral ports, chamfered top
    E.append(box('brake_crown', (7.72, 9.55, -15.58), (8.28, 10.0, -15.3)))
    E.append(box('brake_core', (7.74, 9.56, -15.3), (8.26, 9.99, -11.1)))
    E += chamfer_box('brake_top', (7.05, 10.0, -15.3), (8.95, 10.15, -11.1), 0.0, top=False)
    E.append(box('brake_bot', (7.05, 9.4, -15.3), (8.95, 9.55, -11.1)))
    E.append(box('brake_front', (7.05, 9.55, -15.28), (8.95, 10.0, -14.55)))
    E.append(box('brake_mid', (7.05, 9.55, -13.35), (8.95, 10.0, -12.55)))
    E.append(box('brake_rear', (7.05, 9.55, -11.35), (8.95, 10.0, -11.12)))
    E.append(box('brake_bolt_l', (7.0, 9.65, -14.95), (7.05, 9.9, -14.75)))
    E.append(box('brake_bolt_r', (8.95, 9.65, -14.95), (9.0, 9.9, -14.75)))
    E.append(box('barrel', (7.72, 9.6, -11.1), (8.28, 10.05, -10.75)))
    # --- handguard: chamfered top, recessed vent strip, under rail with slots
    E += chamfer_box('hg_upper', (7.5, 9.6, -10.8), (8.5, 10.3, -0.35), 0.14, segs=3)
    E.append(box('hg_vent_l', (7.46, 9.85, -4.7), (7.5, 10.1, -1.2)))
    E.append(box('hg_vent_r', (8.5, 9.85, -4.7), (8.54, 10.1, -1.2)))
    E.append(box('hg_lower', (7.6, 9.4, -10.8), (8.4, 9.6, -4.0)))
    E.append(box('hg_rail', (7.4, 9.3, -4.0), (8.6, 9.6, -0.35)))
    for i in range(4):
        z = -3.7 + i * 0.85
        E.append(box(f'hg_rail_slot_{i}', (7.36, 9.36, z), (8.64, 9.5, z + 0.3)))
    E.append(box('hg_rod', (7.65, 10.3, -2.7), (8.35, 10.62, 0.45)))
    E.append(box('barrel_nut', (7.55, 9.2, -0.35), (8.45, 10.05, 0.45)))
    E.append(box('laser', (7.55, 8.05, -0.7), (8.45, 9.0, 0.45)))
    E.append(box('laser_lens', (7.75, 8.3, -0.78), (8.25, 8.75, -0.7)))
    # --- receiver: chamfered roof, bolt window with real depth, magwell
    E += chamfer_box('front_block', (7.3, 8.1, 0.45), (8.7, 10.65, 1.35), 0.15)
    E.append(box('lower_box', (7.35, 8.15, 1.35), (8.65, 9.15, 3.7)))
    E.append(box('recv_front', (7.3, 9.15, 1.35), (8.7, 10.2, 3.0)))
    E += chamfer_box('recv_top', (7.3, 10.2, 1.35), (8.7, 10.75, 7.0), 0.14, segs=2)
    E.append(box('recv_bolt', (7.55, 9.5, 3.0), (8.45, 10.2, 5.5)))
    E.append(box('recv_bolt_rod', (7.42, 9.75, 3.2), (7.55, 9.95, 5.2)))
    E.append(box('recv_sill', (7.3, 9.15, 3.0), (8.7, 9.5, 5.5)))
    E.append(box('recv_rear', (7.3, 9.15, 5.5), (8.7, 10.2, 7.0)))
    E.append(box('magwell', (7.4, 8.0, 3.7), (8.6, 9.15, 7.0)))
    E.append(box('magwell_lip', (7.36, 7.9, 3.72), (8.64, 8.05, 3.9)))
    E.append(box('bolt_lever', (8.7, 9.3, 4.88), (9.05, 9.48, 5.18)))
    E.append(box('bolt_knob', (8.98, 9.02, 4.8), (9.36, 9.62, 5.26)))
    E += chamfer_box('recv_tail', (7.35, 9.1, 7.0), (8.65, 10.62, 8.6), 0.15)
    # --- trigger group (closed guard loop)
    E.append(box('guard_bot', (7.9, 7.92, 6.8), (8.1, 8.06, 8.55)))
    E.append(box('guard_front', (7.9, 8.06, 6.8), (8.1, 8.2, 6.95)))
    E.append(box('guard_rear', (7.9, 8.06, 8.4), (8.1, 9.1, 8.55)))
    E.append(post('trigger', 7.93, 8.07, (7.62, 9.12), (7.88, 8.4), 0.15))
    # --- thumbhole stock (real thumbhole), top <= base profile
    E.append(post('stock_grip', 7.45, 8.55, (8.35, 9.4), (8.95, 7.25), 0.95))
    E += chamfer_box('stock_top', (7.45, 9.1, 8.6), (8.55, 10.3, 10.95), 0.15)
    E.append(box('stock_lower', (7.45, 7.25, 8.95), (8.55, 8.0, 9.95)))      # lower arm as 2 flush steps
    E.append(box('stock_lower_b', (7.45, 7.45, 9.95), (8.55, 8.2, 10.95)))
    E += chamfer_box('stock_rear', (7.4, 7.72, 10.95), (8.6, 10.55, 12.45), 0.14, bottom=True, rb=0.12)
    E.append(box('stock_cheek', (7.36, 8.6, 11.2), (7.4, 9.9, 12.2)))
    E.append(box('stock_cheek_r', (8.6, 8.6, 11.2), (8.64, 9.9, 12.2)))
    E.append(box('stock_butt', (7.45, 7.5, 12.45), (8.55, 10.55, 13.45)))
    E.append(box('stock_heel', (7.55, 7.38, 12.3), (8.45, 7.5, 13.25)))
    for i in range(3):
        y = 7.8 + i * 0.85
        E.append(box(f'butt_groove_{i}', (7.5, y, 13.45), (8.5, y + 0.4, 13.5)))
    # --- scope (compressed into the base scope box z 4.85..8.85, top <= 12.55)
    E.append(box('sc_mount_front', (7.65, 10.75, 5.15), (8.35, 11.1, 5.6)))
    E.append(box('sc_mount_rear', (7.6, 10.75, 7.65), (8.4, 11.1, 8.3)))
    E += chamfer_box('sc_obj', (7.25, 10.95, 4.95), (8.75, 12.42, 6.05), 0.2)
    E.append(box('sc_visor', (7.35, 12.42, 4.95), (8.65, 12.55, 5.3)))
    E.append(box('sc_mid', (7.45, 11.05, 6.05), (8.55, 12.2, 7.0)))
    E.append(box('sc_turret_top', (7.7, 12.2, 6.3), (8.3, 12.36, 6.85)))
    E.append(box('sc_turret_side', (7.1, 11.35, 6.35), (7.45, 11.85, 6.8)))
    E.append(box('sc_tube', (7.55, 11.2, 7.0), (8.45, 12.0, 7.65)))
    E += chamfer_box('sc_ocular', (7.45, 11.0, 7.65), (8.55, 12.2, 8.5), 0.15)
    E.append(box('sc_eyecup', (7.6, 11.25, 8.5), (8.4, 11.9, 8.85)))
    # --- magazine (moving leaf), on the base magazine
    E.append(box('mag_body', (7.62, 6.62, 4.0), (8.5, 8.6, 6.55)))
    E.append(box('mag_plate', (7.58, 6.45, 3.95), (8.54, 6.65, 5.3)))
    E.append(box('mag_rib', (7.58, 7.3, 4.4), (7.62, 8.3, 6.2)))
    return tidy(E)


def model2world(name, p):
    if name.startswith('mag_'):
        z0, r0, k = MAG_Z
        p = (p[0], p[1], r0 + (p[2] - z0) * k)
    elif name.startswith('sc_'):
        p = (p[0], p[1], SCOPE_Z(p[2]))
    return M(p)


BONE, GREEN, OLIVE, DARK, BLACK = (198, 190, 176), (74, 88, 52), (128, 128, 104), (58, 60, 54), (36, 36, 33)
CAMO = (('hg_upper', 'hg_rod', 'front_block', 'recv_front', 'recv_top', 'recv_rear', 'recv_sill', 'sc_obj', 'sc_visor',
         'sc_mid', 'sc_tube', 'sc_ocular', 'stock_top', 'mag_plate'))
MATS = [(('brake', 'barrel', 'laser', 'lower_box', 'magwell', 'bolt_lever', 'guard', 'trigger', 'stock_grip', 'stock_lower',
          'stock_rear', 'stock_butt', 'stock_heel', 'sc_mount', 'sc_turret', 'sc_eyecup', 'mag_body', 'mag_rib', 'hg_lower',
          'hg_rail', 'recv_tail', 'recv_bolt'), DARK),
        (('bolt_knob', 'recv_bolt_rod'), BONE)]


# r5: material response is assigned per part; only identity accents use exact special texels.
from identity import geometry as _identity_geometry
from materials9 import MATERIALS as _MATERIALS, choose as _choose_material, decal as _decal, register as _register
_base_elements = elements
T = 20
ATLAS = 1024
STYLE = 'material'
MATERIALS = _MATERIALS['aachen_lr2']
_register('aachen_lr2', model2world)
def elements(): return _identity_geometry('aachen_lr2', _base_elements())
def material(name, face): return _choose_material('aachen_lr2', name, face)
def special(e, fn, s, t): return _decal('aachen_lr2', e, fn, s, t)
