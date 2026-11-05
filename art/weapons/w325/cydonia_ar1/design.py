"""W325 Cydonia-AR1 (Red War uncommon, Adaptive auto rifle) over gnawing_hunger (layout contract:
weapon_reload_w208_gnawing_hunger + weapon_sight_w151, same base as W302 Khvostov).

Identity kept: maroon + gunmetal paint, long slotted suppressor on a thin neck, maroon top cover with the raised
rear section and dark front cap, vented dark mid rail, maroon under-tube with dark front cap, maroon fore plates,
skeleton grip frame (front post + bottom bar) with raked grip, small reflex sight on the receiver rail, and the
skeleton stock: maroon block with dark insets, rear upright, slotted dark pad and the long diagonal bar to the grip.
The receiver/grip/magazine mesh ("Middle"/"Magazine") is the same as Ros Lysis II's; the rip carries two nested
optics (TrueSight + Fastdraw), modelled as one reflex frame.
Rip -> model: one uniform 25.7 px/m map (23 across): rip magazine centre -> z 3.3, reticle centre -> base eye line
y 12.79; this rip already spans the base length (muzzle z -9.45, butt z 15.2).
Detail/pixel pass: segmented chamfered cover/rail/receiver/stock blocks (Dead Man Walking style), vent teeth, ribbed
tube, slotted suppressor, flat maroon/gunmetal palette; the cover/receiver/rails stay under the base top profile and
the reflex sight is a hollow 'sight_*' frame (ADS).
"""
S, SX = 25.7, 23.0
ZM, YM = 3.3, -0.169
YE, ZE = 12.79, 0.2305


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / SX, YM + (z - ZM) / S, ZE + (y - YE) / S)


def is_magazine(n): return n.startswith('mag_')


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_m2tools'))
from solid import B, bar, vbar, octo, Flat, clean


def elements():
    E = []; a = E.append
    # ---- slotted octagonal suppressor (two segments + band), bore, neck, collar, barrel block
    for e in octo('sup', 8, 10.23, .45, -9.45, -7.75): a(e)
    for e in octo('sup_rear', 8, 10.23, .45, -7.65, -5.95): a(e)
    for e in octo('sup_band', 8, 10.23, .5, -7.75, -7.65): a(e)
    a(B('sup_bore', (7.85, 10.08, -9.47), (8.15, 10.38, -9.45)))
    for e in octo('sup_neck', 8, 10.22, .22, -5.95, -5.4): a(e)
    a(B('sup_collar', (7.66, 9.85, -5.78), (8.34, 11.0, -5.48)))
    for e in bar('barrel_block', 7.45, 8.55, 9.75, 11.15, -5.4, -4.55, c=.15, top=True, bottom=True): a(e)
    # ---- maroon top cover (kept under the base top 12.04): front with dark cap, rear section, chamfered
    for e in bar('cover', 7.25, 8.75, 11.15, 11.98, -4.6, 4.3, c=.22, at=[-1.2, 1.4]): a(e)
    a(B('cover_front_cap', (7.4, 11.98, -4.25), (8.6, 12.02, -3.05)))
    for s, (x0, x1) in (('l', (7.18, 7.25)), ('r', (8.75, 8.82))):
        a(B(f'cover_slot_{s}', (x0, 11.5, -3.6), (x1, 11.65, -2.5)))
    # ---- vented dark mid rail (vent teeth), side brackets
    for e in bar('mid_rail', 7.3, 8.7, 9.4, 11.15, -4.55, 4.3, c=.12, top=False, bottom=True, at=[0.6]): a(e)
    for k in range(7):
        z = -3.9 + k * .52
        for s, (x0, x1) in (('l', (7.24, 7.3)), ('r', (8.7, 8.76))):
            a(B(f'vent_{s}{k}', (x0, 10.3, z), (x1, 10.75, z + .24)))
    a(B('cover_bracket', (7.22, 9.5, 3.75), (8.78, 11.2, 4.45)))
    # ---- under tube with ribbed sides + cap, fore plates
    for e in bar('tube', 7.45, 8.55, 8.0, 9.4, -4.1, 0.6, c=.16, top=False, bottom=True): a(e)
    for k in range(4):
        z = -3.5 + k * .95
        a(B(f'tube_rib_{k}', (7.4, 8.25, z), (8.6, 9.15, z + .5)))
    for e in octo('tube_nose', 8, 8.55, .45, -5.05, -4.1): a(e)
    for s, (x0, x1) in (('l', (7.18, 7.32)), ('r', (8.68, 8.82))):
        a(B(f'fore_plate_{s}', (x0, 7.95, 0.8), (x1, 9.4, 4.95)))
        a(B(f'fore_bolt_{s}', (x0 - .05 if s == 'l' else x1, 8.55, 1.25), (x0 if s == 'l' else x1 + .05, 8.75, 1.45)))
    # ---- receiver: lower core, trigger opening, side lever, upper (steps down behind z 8.4 for the ADS line)
    a(B('rcv_lower', (7.32, 7.8, 0.6), (8.68, 9.6, 5.0)))
    a(B('rcv_lower_rear', (7.32, 8.45, 5.0), (8.68, 9.6, 7.2)))
    a(B('guard_post', (7.6, 7.7, 6.75), (8.4, 8.5, 7.2)))
    a(B('trigger', (7.93, 7.85, 6.15), (8.07, 8.45, 6.33), ('x', -12), (8, 8.45, 6.24)))
    a(B('side_lever', (7.0, 8.65, 6.25), (7.32, 9.65, 6.8)))
    for e in bar('rcv_upper', 7.28, 8.72, 9.6, 11.88, 4.3, 8.45, c=.2, at=[6.2]): a(e)
    a(B('rcv_upper_tail', (7.32, 9.6, 8.45), (8.68, 11.25, 9.7)))
    a(B('rcv_window', (8.72, 10.4, 5.0), (8.76, 11.2, 6.0)))
    a(B('rcv_rail', (7.45, 11.88, 4.45), (8.55, 11.98, 8.3)))
    for k in range(4):
        z = 4.6 + k * .4
        a(B(f'rcv_rail_tooth_{k}', (7.5, 11.98, z), (8.5, 12.03, z + .2)))
    # ---- grip frame + grip
    a(B('frame_post', (7.62, 5.18, 4.64), (8.38, 7.8, 5.09)))
    a(B('frame_bottom', (7.62, 5.23, 4.64), (8.38, 5.63, 8.0), ('x', -11), (8, 5.43, 4.64)))
    a(B('grip', (7.4, 5.93, 7.14), (8.6, 9.28, 8.29), ('x', -18), (8, 9.28, 7.69)))
    a(B('grip_panel', (7.36, 6.4, 7.34), (8.64, 8.6, 8.09), ('x', -18), (8, 9.28, 7.69)))
    # ---- reflex sight: hollow frame around the aim line (all 'sight_*'; window x 7.68..8.32 / y 12.45..13.0)
    a(B('sight_base', (7.58, 11.98, 6.1), (8.42, 12.45, 7.0)))
    for s, (x0, x1) in (('l', (7.52, 7.68)), ('r', (8.32, 8.48))):
        a(B(f'sight_cheek_{s}', (x0, 12.45, 6.3), (x1, 13.15, 6.95)))
    a(B('sight_top', (7.52, 13.0, 6.25), (8.48, 13.18, 6.95)))
    a(B('sight_tail', (7.6, 11.98, 7.0), (8.4, 12.05, 8.0)))
    # ---- skeleton stock (top <= base 11.33)
    for e in bar('st_block', 7.58, 8.42, 9.36, 11.3, 9.7, 13.3, c=.16, at=[11.5]): a(e)
    for s, (x0, x1) in (('l', (7.54, 7.58)), ('r', (8.42, 8.46))):
        a(B(f'st_inset_{s}', (x0, 10.05, 10.1), (x1, 10.95, 13.0)))
    a(B('st_front_drop', (7.58, 8.8, 9.7), (8.42, 9.36, 10.75)))
    for e in vbar('st_rear_vert', 7.58, 8.42, 7.25, 11.3, 13.3, 14.25, c=.12, front=False): a(e)
    a(B('st_pad', (7.52, 7.33, 14.25), (8.48, 11.08, 15.2)))
    for k in range(3):
        y = 8.0 + k * .9
        a(B(f'st_pad_slot_{k}', (7.48, y, 14.5), (8.52, y + .45, 14.95)))
    a(B('st_bar', (7.6, 6.3, 8.9), (8.4, 6.82, 14.35), ('x', -11), (8, 6.3, 8.9)))
    # ---- magazine
    a(B('mag_body', (7.6, 5.18, 2.19), (8.4, 8.13, 4.59)))
    a(B('mag_window', (7.56, 6.2, 3.0), (8.44, 6.95, 3.5)))
    a(B('mag_pad', (7.52, 4.66, 2.09), (8.48, 5.23, 4.66)))
    return clean(E)


MAROON, DARK, GUN, BLACK = (100, 54, 54), (54, 54, 56), (84, 84, 86), (30, 30, 32)
_flat = Flat([
    (lambda n, f: n in ('sup_bore', 'mag_window', 'rcv_window') or n.startswith(('sup_slot', 'vent_', 'st_pad_slot', 'cover_slot')) or '_joint_' in n, BLACK),
    (lambda n, f: n.startswith(('sup', 'barrel', 'tube_nose', 'cover_front_cap', 'sight_', 'st_pad', 'grip', 'frame_', 'guard_', 'trigger', 'side_lever', 'mag_', 'tube_rib', 'rcv_rail', 'st_inset')), DARK),
    (lambda n, f: n.startswith(('cover', 'tube', 'fore_plate', 'st_block', 'st_rear', 'st_front', 'st_bar')), MAROON),
    (lambda n, f: n.startswith(('fore_bolt', 'rcv_upper')), GUN),
])


def special(e, fn, s, t):
    if e['name'] == 'sup' and fn in ('east', 'west') and .4 < t < .6 and .15 < s < .85:
        return BLACK + (255,)
    return _flat(e, fn, s, t)


PALETTE = 14
FLAT_TOL = 30
PALETTE_KEEP = [MAROON, DARK, BLACK]

# W325 identity pass: every face is hand-painted at 20 texels/model px.
from identity import Painter
T = 20
ATLAS = 1024
special = Painter('cyd', T)

from identity import geometry
_base_elements = elements
def elements(): return geometry(_base_elements(), 'cyd')

# W325 MATERIAL pass supersedes whole-face identity.Painter fills.
from materials import Materials, Decals
STYLE = "material"
material = Materials('cyd')
MATERIALS = material.palette
special = Decals('cyd', model2world, 'cydonia_ar1', T)
