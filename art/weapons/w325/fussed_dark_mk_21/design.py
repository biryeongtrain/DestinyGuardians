"""W325 Fussed Dark Mk.21 (rare, precision shotgun, tan/green camo, windowed heat shield, perforated suppressor)
over base dust_rock_blues (W207 shell insert, W148 sight).  Detail/style pass v2 (W30/DMW look).

Model px, muzzle -z, up +y, centre x=8.  Rip station-mapped around the trigger (z 9.45): front 19.5 px/m (muzzle -6.8),
stock 26.5 px/m (butt 18.3); height 21.2 px/m, bore y 11.1 (base 10.96).  Heat-shield windows are real openings.
Base inserted shell (x 7.04..7.56, y 8.89..9.41, z 6.42..7.78) stays free (receiver floor y 9.45).
v2 ADS: receiver steps down to the base top (11.6 behind z 6.3); rear sight = lateral ears (sight_*) on the base W148
notch z (10.0..10.3, top 12.5); stock tops follow the base stock profile (11.6 -> 11.4 -> 11.2 -> 11.0, butt 11.4).
Faces flat-painted: 3-colour camo blobs (tan / sage / pale pink), dark olive polymer, black pump, silver details.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib_m8'))
from detail import box, rx, cham, chamy, zsplit, strut, separate  # noqa: E402
from paint import painter, camo, line, every  # noqa: E402

S = 21.2
TZ, TW = 9.45, -0.071
SF, SR = 19.5, 26.5
SY, SW = 11.0, 0.1445
BORE = (8.0, 11.1)
PALETTE = 24
FLAT_TOL = 6
SAGE, TAN, PINK = (150, 166, 120), (206, 196, 168), (226, 200, 190)
OLIVE, OLIVE_L, BLACK, PUMP, SILVER, SILVER_D = (66, 66, 52), (88, 88, 70), (18, 18, 18), (44, 44, 40), (190, 192, 190), (130, 132, 132)
PALETTE_KEEP = [SAGE, TAN, PINK, OLIVE, OLIVE_L, BLACK, PUMP, SILVER, SILVER_D]
WINDOWS = [(-4.15, -1.85), (-1.25, -0.35), (0.25, 1.15), (1.75, 2.65), (3.3, 4.7)]


def model2world(name, p):
    x, y, z = p
    wy = TW + (z - TZ) / (SF if z <= TZ else SR)
    return (-(x - 8.0) / S, wy, SW + (y - SY) / S)


def elements():
    E = []
    a = E.append; ex = E.extend
    # suppressor: camo can in two segments, perforated drum, muzzle face with bore
    ex(zsplit('can', 7.62, 8.38, 10.7, 11.5, [-6.5, -5.5, -4.3], r=0.12, corners='tltrblbr'))
    # Open muzzle lip with a recessed dark bore stop.
    a(box('can_face', (7.8, 10.9, -6.52), (8.2, 11.299999999999999, -6.5)))
    a(box('can_lip_t', (7.62, 11.299999999999999, -6.86), (8.38, 11.48, -6.5)))
    a(box('can_lip_b', (7.62, 10.719999999999999, -6.86), (8.38, 10.9, -6.5)))
    a(box('can_lip_l', (7.62, 10.9, -6.86), (7.8, 11.299999999999999, -6.5)))
    a(box('can_lip_r', (8.2, 10.9, -6.86), (8.38, 11.299999999999999, -6.5)))
    ex(cham('drum', 7.35, 8.65, 10.55, 11.8, -4.3, -3.65, 0.25))
    # windowed heat shield: chamfered top rail, lower body, posts, dark inner barrel
    ex(cham('shield_top', 7.25, 8.75, 11.45, 11.9, -3.65, 4.75, 0.2, corners='tltr'))
    ex(cham('shield_low', 7.25, 8.75, 10.1, 10.75, -3.65, 4.75, 0.15, corners='blbr'))
    a(box('barrel_in', (7.6, 10.75, -3.65), (8.4, 11.45, 4.75)))
    edges = [-3.65] + [v for w in WINDOWS for v in w] + [4.75]
    for i in range(0, len(edges), 2):
        z0, z1 = edges[i], edges[i + 1]
        if z1 - z0 > 0.05:
            a(box(f'post_{i // 2}', (7.05, 10.05, z0), (8.95, 11.95, z1)))
    for i, (z0, z1) in enumerate(WINDOWS):
        for t, x0, x1 in (('l', 7.0, 7.05), ('r', 8.95, 9.0)):
            a(box(f'post_bolt_{t}{i}', (x0, 11.6, z1 + 0.1), (x1, 11.8, z1 + 0.3)))
    # silver tube, underbarrel bracket with light, pump in two segments
    ex(cham('tube', 7.45, 8.55, 9.85, 10.1, -3.65, 4.75, 0.08, corners='blbr'))
    ex(cham('bracket', 7.35, 8.65, 9.05, 9.85, -3.6, -1.9, 0.18, corners='blbr'))
    a(box('bracket_lens', (7.55, 9.2, -3.66), (8.45, 9.7, -3.6)))
    ex(zsplit('pump_body', 7.2, 8.8, 8.55, 9.95, [-1.85, 1.0, 3.9], r=0.28, corners='blbr', gtop=False, gbot=True))
    ex(cham('pump_belly', 7.4, 8.6, 8.4, 8.6, -1.4, 3.6, 0.08, corners='blbr'))
    # receiver: front block (to 6.3), lower top behind, side box with vent, bolt knob, dark lower
    ex(cham('recv_front', 7.3, 8.7, 9.45, 11.75, 4.75, 6.3, 0.22, corners='tltr'))
    ex(cham('recv_rear', 7.3, 8.7, 9.45, 11.6, 6.3, 9.75, 0.22, corners='tltr'))
    ex(cham('side_box', 7.0, 7.3, 10.2, 11.6, 4.75, 6.25, 0.1, corners='tlbl'))
    a(box('side_vent', (6.97, 10.5, 5.0), (7.0, 11.3, 6.0)))
    ex(cham('recv_bolt', 8.7, 9.0, 10.45, 10.95, 7.0, 8.2, 0.08))
    a(box('recv_knob', (8.7, 10.3, 7.0), (9.15, 11.1, 7.45)))
    ex(cham('recv_tail', 7.3, 8.7, 8.9, 11.45, 9.75, 11.0, 0.2, corners='tltrblbr'))
    # rear notch sight on the base notch z: plate + two lateral ears
    a(box('sight_base', (7.6, 11.45, 9.95), (8.4, 11.6, 10.45)))
    a(box('sight_ear_l', (7.6, 11.6, 10.0), (7.78, 12.5, 10.3)))
    a(box('sight_ear_r', (8.22, 11.6, 10.0), (8.4, 12.5, 10.3)))
    # trigger guard (open), trigger, raked pistol grip with cap and side panels
    a(box('guard_front', (7.85, 8.85, 8.85), (8.15, 9.45, 9.05)))
    a(box('guard_bar', (7.85, 8.85, 9.05), (8.15, 9.0, 10.0)))
    a(box('trigger', (7.9, 9.0, 9.35), (8.1, 9.45, 9.55), {'origin': [8.0, 9.45, 9.45], 'x': -10}))
    a(strut('grip', (11.3, 9.0), (11.95, 7.05), 1.35, 7.42, 8.58, ext=0.1))
    a(strut('grip_cap', (11.95, 7.05), (12.04, 6.77), 1.55, 7.38, 8.62))
    for t, x0, x1 in (('l', 7.37, 7.42), ('r', 8.58, 8.63)):
        a(strut(f'grip_panel_{t}', (11.4, 8.7), (11.85, 7.4), 0.8, x0, x1))
    # skeletal stock stepping down along the base stock profile
    ex(cham('stock_tube0', 7.55, 8.45, 10.75, 11.6, 11.0, 12.88, 0.15, corners='tltr'))
    ex(cham('stock_tube1', 7.55, 8.45, 10.75, 11.4, 12.88, 14.1, 0.15, corners='tltr'))
    ex(cham('stock_tube2', 7.55, 8.45, 10.6, 11.2, 14.1, 15.1, 0.15, corners='tltr'))
    ex(cham('stock_tube3', 7.55, 8.45, 10.6, 11.0, 15.1, 17.68, 0.12, corners='tltr'))
    ex(cham('stock_lower', 7.6, 8.4, 9.85, 10.6, 13.0, 16.3, 0.12, corners='blbr'))
    a(box('stock_web', (7.55, 9.7, 12.0), (8.45, 10.75, 13.0)))
    a(strut('stock_brace', (16.1, 9.75), (17.1, 8.7), 0.35, 7.55, 8.45, ext=0.1))
    ex(chamy('butt', 7.5, 8.5, 8.6, 11.4, 17.68, 18.3, 0.2, corners='bB'))
    ex(cham('butt_low', 7.5, 8.5, 8.6, 10.6, 16.6, 17.68, 0.15, corners='blbr'))
    a(box('butt_pad', (7.55, 8.7, 18.3), (8.45, 11.3, 18.42)))
    return separate(E)


def is_magazine(name):
    return False


CAMO = (SAGE, TAN, PINK)


def region(n, fn, p, s, t, e):
    x, y, z = p
    side = fn in ('east', 'west')
    if n == 'can_face':
        return BLACK if abs(x - 8) < 0.2 and abs(y - BORE[1]) < 0.2 else SAGE
    if n.startswith('drum'):
        if side or fn in ('up', 'down'):
            v = y if side else x * 1.2
            row = int((v - 10) / 0.3)
            if math.hypot(((z + 4.3 + (0.15 if row % 2 else 0)) % 0.3) - 0.15, ((v - 10) % 0.3) - 0.15) < 0.08:
                return BLACK
        return SILVER
    if n == 'barrel_in':
        return BLACK
    if n.startswith('post_bolt'):
        return OLIVE
    if '_groove' in n:
        return BLACK if n.startswith('pump') else SAGE
    if n.startswith(('can', 'shield', 'post', 'recv_front', 'recv_rear', 'stock_tube')):
        if n.startswith('recv_rear') and side and 10.4 < y < 11.2 and 7.6 < z < 9.2:
            return BLACK if (line(y, 10.43, .04) or line(y, 11.17, .04) or line(z, 7.63, .04) or line(z, 9.17, .04)) else OLIVE_L
        if n.startswith('shield_low') and side and line(y, 10.15, 0.05):
            return SILVER_D
        return camo(p, CAMO, cell=1.5, seed=9, cuts=(0.4, 0.64))
    if n.startswith(('tube', 'bracket_lens', 'sight_ear', 'recv_knob')):
        if n == 'bracket_lens':
            return (236, 236, 214)
        return SILVER
    if n.startswith('pump'):
        if side and n.startswith('pump_body') and 9.0 < y < 9.7 and every(z, -1.6, 0.35, 0.08):
            return BLACK
        return PUMP
    if n == 'side_vent':
        return BLACK
    if n.startswith('grip_panel'):
        return BLACK if every(y, 7.5, 0.3, 0.08) else OLIVE_L
    if n.startswith(('trigger',)):
        return BLACK
    if n == 'butt_pad':
        return (30, 30, 28)
    return OLIVE


special = painter(region)

# Ace/Izanagi identity pass: exact face paint and a denser 1P atlas.
T = 20
ATLAS = 1024
from identity import enhance
special = enhance("fussed_dark_mk_21", special, T)

# W123 material pass replaces full-face flat special paint.
STYLE = "material"
from surface import setup as material_setup
MATERIALS, material, special = material_setup("fussed_dark_mk_21")
