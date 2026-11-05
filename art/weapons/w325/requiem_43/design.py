"""W325 Requiem-43 (SUROS Pinpoint Slug shotgun, rare) over base first_in_last_out (W178/W208 shell-insert).

Rip at a uniform 24.67 px/m: muzzle z -8.36, butt z 16.48 (base -8.38..16.56). Receiver top 12.25 (+hump 12.38,
bead 12.24) stays under the base top profile and the W148 optic eye line (~13.4). Raked grip/trigger on the base grip
(z 7.5..9.5). Wrist top follows the base's falling profile in short segments (adscheck). Shell port under the
receiver (z 3.7..5.6, y < 10.32) is open for the base shell path (z 3.88..5.42). Body only (insert reload).
Detail pass (W325 r2): 45-degree chamfers on the shroud/receiver/stock long edges, real bore opening, under-barrel
ribs, stock tube collars, palette-snapped bake (flat SUROS mint/red/grey panels instead of smeared projection).
"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_w9'))
from w9 import tidy, box, bar, post, segbar, chamfer_box, RipMap, palette, snapper, lens, flat, material, model_pt

M = RipMap(24.67, (13.0, -8.37), (0.21, -0.662), '-y')
T = 18
PALETTE = 14
FLAT_TOL = 30
PALETTE_KEEP = [(196, 36, 34), (12, 12, 13)]


def elements():
    E = []
    # --- muzzle: crown frame around a real bore, dark tip ring
    E.append(box('muzzle_frame_top', (7.42, 11.85, -8.36), (8.58, 11.98, -8.05)))
    E.append(box('muzzle_frame_bot', (7.42, 9.45, -8.36), (8.58, 11.15, -8.05)))
    E.append(box('muzzle_frame_l', (7.42, 11.15, -8.36), (7.65, 11.85, -8.05)))
    E.append(box('muzzle_frame_r', (8.35, 11.15, -8.36), (8.58, 11.85, -8.05)))
    E.append(box('muzzle_bore', (7.65, 11.15, -8.12), (8.35, 11.85, -8.05)))
    E.append(box('muzzle_lug', (7.3, 9.55, -8.25), (7.42, 10.4, -8.1)))
    # --- dark under-barrel (ribbed) + shroud with chamfered top edges
    E += chamfer_box('barrel', (7.62, 9.8, -8.05), (8.38, 10.82, 3.7), 0.12, top=False, bottom=True, segs=2)
    for i in range(6):
        z = -7.6 + i * 1.05
        E.append(box(f'barrel_rib_{i}', (7.56, 9.78, z), (8.44, 9.9, z + 0.35)))
    E += chamfer_box('shroud_front', (7.52, 10.82, -8.05), (8.48, 12.0, -3.0), 0.14, segs=3)
    E.append(box('shroud_front_lip', (7.48, 10.82, -3.25), (8.52, 11.9, -3.0)))
    E += chamfer_box('shroud_mid', (7.4, 10.82, -3.0), (8.6, 12.15, 1.2), 0.15, segs=2)
    E += chamfer_box('fore_grip', (7.45, 9.62, -1.4), (8.55, 10.82, 0.75), 0.18, top=False, bottom=True)
    # --- receiver with recessed ejection window, chamfered roof
    E += chamfer_box('recv_upper', (7.25, 11.15, 1.2), (8.75, 12.25, 5.2), 0.25)
    E.append(box('recv_window_core', (7.45, 10.75, 1.45), (8.55, 11.15, 3.65)))
    E.append(box('recv_window_post', (7.25, 10.5, 1.2), (8.75, 11.15, 1.45)))
    E.append(box('recv_window_sill', (7.25, 10.5, 1.45), (8.75, 10.75, 3.65)))
    E.append(box('recv_rear', (7.25, 10.5, 3.65), (8.75, 11.15, 5.2)))
    E.append(box('recv_pin_l', (7.19, 10.7, 4.55), (7.25, 10.9, 4.75)))
    E.append(box('rsight_hump', (7.62, 12.25, 4.15), (8.38, 12.38, 4.95)))
    E.append(box('rsight_bead', (7.88, 12.05, 6.34), (8.12, 12.24, 6.66)))
    E.append(box('recv_button', (8.75, 10.65, 4.4), (8.85, 10.95, 4.7)))
    # shell port (open floor) under the receiver
    E.append(box('port_wall_l', (7.35, 9.75, 3.7), (7.5, 10.5, 5.6)))
    E.append(box('port_wall_r', (8.5, 9.75, 3.7), (8.65, 10.5, 5.6)))
    E.append(box('port_roof', (7.5, 10.32, 3.7), (8.5, 10.5, 5.6)))
    E.append(box('port_lip', (7.35, 9.68, 5.45), (8.65, 9.75, 5.6)))
    # rear receiver / wrist (top follows the base's falling profile)
    E += chamfer_box('recv_tail', (7.35, 10.5, 5.2), (8.65, 12.15, 7.3), 0.15)
    E.append(box('recv_tail_low', (7.35, 9.75, 5.6), (8.65, 10.5, 7.3)))
    # wrist top as an axis-aligned step sequence (shared edges) following the base's falling profile
    for k, (za, zb, yt) in enumerate(((7.3, 8.1, 11.92), (8.1, 8.7, 11.62), (8.7, 9.3, 11.32), (9.3, 9.9, 11.02), (9.9, 10.45, 10.72))):
        E.append(box(f'wrist_step_{k}', (7.45, 10.5 if k < 3 else 10.0, za), (8.55, yt, zb)))
    E.append(box('wrist_core', (7.45, 9.4, 7.3), (8.55, 10.9, 8.6)))
    # trigger group: guard loop with a real opening
    E.append(box('guard_front', (7.9, 9.15, 6.3), (8.1, 9.75, 6.48)))
    E.append(box('guard_bar', (7.9, 9.15, 6.48), (8.1, 9.28, 7.6)))
    E.append(box('guard_rear', (7.9, 9.15, 7.6), (8.1, 9.5, 7.75)))
    E.append(post('trigger', 7.93, 8.07, (6.95, 9.75), (7.15, 9.35), 0.16))
    # raked pistol grip (27 deg) with dark rubber side inserts
    E.append(post('grip', 7.5, 8.5, (7.5, 10.2), (9.22, 6.78), 1.25))
    E.append(post('grip_insert_l', 7.44, 7.5, (8.05, 8.7), (8.7, 7.4), 0.55))
    E.append(post('grip_insert_r', 8.5, 8.56, (8.05, 8.7), (8.7, 7.4), 0.55))
    E.append(post('grip_heel', 7.48, 8.52, (8.92, 7.35), (9.12, 6.95), 0.55))
    # stock: white tube with collars, lower arm, comb (chamfered), rear block, pad
    E.append(bar('stock_tube', 7.6, 8.4, (9.9, 10.0), (12.8, 8.82), 1.0, ext=(.1, .35)))
    lp = lambda z: (z, 10.0 + (z - 9.9) * (8.82 - 10.0) / (12.8 - 9.9))   # exact points on the tube axis
    E.append(bar('stock_collar_f', 7.52, 8.48, lp(10.1), lp(10.45), 1.12))
    E.append(bar('stock_collar_r', 7.52, 8.48, lp(12.2), lp(12.55), 1.12))
    E += chamfer_box('stock_comb', (7.4, 10.9, 11.02), (8.6, 11.9, 16.15), 0.14, segs=2, gap=0.12)
    # rear block: axis-aligned steps falling toward the butt (replaces the old crossing lower arm)
    E.append(box('stock_block', (7.4, 8.15, 13.15), (8.6, 10.9, 14.15)))
    E.append(box('stock_block_b', (7.4, 7.85, 14.15), (8.6, 10.9, 15.15)))
    E.append(box('stock_block_c', (7.4, 7.4, 15.15), (8.6, 10.9, 16.15)))
    E.append(box('stock_side_l', (7.34, 9.0, 13.6), (7.4, 10.6, 15.8)))
    E.append(box('stock_side_r', (8.6, 9.0, 13.6), (8.66, 10.6, 15.8)))
    E.append(box('butt_pad', (7.46, 7.32, 16.15), (8.54, 11.1, 16.48)))
    E.append(box('butt_pad_top', (7.52, 11.1, 16.15), (8.48, 11.5, 16.4)))
    return tidy(E)


def model2world(name, p): return M(p)


MINT, RED, DARK, GREY, WHITE = (150, 172, 168), (150, 40, 40), (52, 51, 51), (74, 72, 71), (206, 210, 208)
MATS = [(('muzzle_frame', 'muzzle_lug', 'butt_pad', 'stock_tube', 'fore_grip', 'port_lip', 'shroud_front_lip'), WHITE),
        (('barrel', 'recv_window_post', 'recv_window_sill', 'recv_rear', 'recv_tail', 'recv_tail_low', 'wrist', 'port_',
          'guard', 'trigger', 'grip', 'stock_collar', 'stock_lower', 'stock_block', 'stock_front', 'recv_button', 'recv_pin'), DARK),
        (('rsight_hump',), GREY)]


# r5: material response is assigned per part; only identity accents use exact special texels.
from identity import geometry as _identity_geometry
from materials9 import MATERIALS as _MATERIALS, choose as _choose_material, decal as _decal, register as _register
_base_elements = elements
T = 20
ATLAS = 1024
STYLE = 'material'
MATERIALS = _MATERIALS['requiem_43']
_register('requiem_43', model2world)
def elements(): return _identity_geometry('requiem_43', _base_elements())
def material(name, face): return _choose_material('requiem_43', name, face)
def special(e, fn, s, t): return _decal('requiem_43', e, fn, s, t)
