"""W325 Botheration Mk.28 (rare, aggressive shotgun, teal camo / dark polymer, perforated suppressor) over base
mindbender_s_ambition_adept (W221 shell insert, W148 sight) — same base as W302 Stubborn Oak.  Detail/style pass v2.

Model px (final frame), muzzle -z, up +y, centre x=8.  Rip scale 21.2 px/m, station map (BP): muzzle -9.75, rip trigger
on the base trigger (6.6), stock x1.38 so the butt ends at ~15.9 (base 16.07).  Bore y 11.8.  Contract as Stubborn Oak:
everything z -8.6..4.4 under y 12.45, receiver floor open over the base shell path (z 3.68..5.22, y 9.75..10.33).
v2 ADS: rear sight = lateral ears (sight_*) on the base W148 notch z (5.0..5.22, top 12.72), receiver steps down behind
z 6.6 (12.3 -> 12.12 -> 11.98), stock tops <= 11.88 (base 11.89..12.15).  Faces flat-painted (W30/DMW look): teal 3-colour camo
blobs, dark brown polymer, silver tube, white perforated band.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib_m8'))
from detail import box, rx, cham, chamy, zsplit, strut, separate  # noqa: E402
from paint import painter, camo, line, every  # noqa: E402

S = 21.2
GW = -0.9433
SY, SW = 12.34, 0.17
BP = [(-9.75, -9.75), (6.6, 9.2), (16.25, 16.2)]
BORE = (8.0, 11.8)
PALETTE = 24
FLAT_TOL = 6
TEAL, TEAL_D, TEAL_L = (54, 84, 88), (36, 58, 62), (150, 184, 192)
POLY, POLY_L, BLACK, SILVER, SILVER_D, WHITE = (62, 46, 38), (84, 64, 52), (18, 18, 20), (176, 188, 194), (128, 138, 144), (222, 228, 230)
PALETTE_KEEP = [TEAL, TEAL_D, TEAL_L, POLY, POLY_L, BLACK, SILVER, SILVER_D, WHITE]


def zu(z):
    for i in range(len(BP) - 1):
        (m0, u0), (m1, u1) = BP[i], BP[i + 1]
        if z <= m1 or i == len(BP) - 2:
            return u0 + (z - m0) * (u1 - u0) / (m1 - m0)


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / S, GW + (zu(z) + 9.75) / S, SW + (y - SY) / S)


def elements():
    E = []
    a = E.append; ex = E.extend
    # suppressor: camo can in two segments, perforated band, dark collar, bore
    ex(cham('can', 7.35, 8.65, 11.14, 12.45, -9.35, -6.57, 0.22))
    # Open muzzle lip with a recessed dark bore stop.
    a(box('can_face', (7.7, 11.5, -9.37), (8.3, 12.100000000000001, -9.35)))
    a(box('can_lip_t', (7.45, 12.100000000000001, -9.75), (8.55, 12.350000000000001, -9.35)))
    a(box('can_lip_b', (7.45, 11.25, -9.75), (8.55, 11.5, -9.35)))
    a(box('can_lip_l', (7.45, 11.5, -9.75), (7.7, 12.100000000000001, -9.35)))
    a(box('can_lip_r', (8.3, 11.5, -9.75), (8.55, 12.100000000000001, -9.35)))
    ex(cham('can_perf', 7.33, 8.67, 11.12, 12.47, -6.57, -5.57, 0.22))
    ex(cham('can_collar', 7.4, 8.6, 11.2, 12.4, -5.57, -5.07, 0.2))
    # barrel shroud in three segments, U-ear front sight on a base, silver tube with front cap
    ex(zsplit('barrel', 7.35, 8.65, 11.21, 12.36, [-5.07, -2.2, 1.15], r=0.2, corners='tltrblbr'))
    a(box('fsight_base', (7.6, 12.36, -4.86), (8.4, 12.45, -3.43)))
    a(box('fsight_ear_l', (7.6, 12.45, -4.8), (7.78, 12.95, -4.38)))
    a(box('fsight_ear_r', (8.22, 12.45, -4.8), (8.4, 12.95, -4.38)))
    ex(cham('tube', 7.55, 8.45, 10.3, 11.21, -4.86, 2.4, 0.18, corners='blbr'))
    a(box('tube_cap', (7.62, 10.36, -5.0), (8.38, 11.15, -4.86)))
    # pump fore-end: chamfered body in 2 segments, belly, nose, side windows (real steps)
    ex(zsplit('pump_body', 7.25, 8.75, 9.55, 10.95, [-4.2, -1.2, 1.8], r=0.28, corners='blbr', gtop=False, gbot=True))
    ex(cham('pump_belly', 7.4, 8.6, 9.25, 9.6, -3.7, 1.5, 0.12, corners='blbr'))
    ex(cham('pump_nose', 7.35, 8.65, 9.8, 10.9, -4.45, -4.2, 0.2, corners='blbr'))
    for i in range(3):
        z = -3.2 + i * 1.6
        for t, x0, x1 in (('l', 7.19, 7.25), ('r', 8.75, 8.81)):
            a(box(f'pump_pad_{t}{i}', (x0, 9.75, z), (x1, 10.15, z + 0.55)))
    # receiver: collar, camo upper stepping down behind the trigger, dark lower, open shell port with silver loop
    ex(cham('rcv_collar', 7.3, 8.7, 10.35, 12.42, 1.15, 2.4, 0.22, corners='tltr'))
    ex(cham('rcv_upper', 7.3, 8.7, 11.05, 12.42, 2.4, 6.6, 0.22, corners='tltr'))
    ex(cham('rcv_upper_rear', 7.3, 8.7, 11.05, 12.12, 6.6, 8.6, 0.22, corners='tltr'))
    ex(cham('rcv_upper_tail', 7.3, 8.7, 11.05, 11.98, 8.6, 9.2, 0.22, corners='tltr'))
    ex(cham('rcv_lower_front', 7.3, 8.7, 10.35, 11.05, 2.4, 3.6, 0.15, corners='blbr'))
    a(box('port_wall_l', (7.3, 10.4, 3.6), (7.5, 11.05, 5.3)))
    a(box('port_wall_r', (8.5, 10.4, 3.6), (8.7, 11.05, 5.3)))
    a(box('port_roof', (7.5, 10.75, 3.6), (8.5, 11.05, 5.3)))
    a(box('loop_front', (7.55, 10.2, 4.05), (8.45, 10.4, 4.25)))
    a(box('loop_rear', (7.55, 10.2, 5.15), (8.45, 10.4, 5.35)))
    ex(cham('rcv_lower_rear', 7.3, 8.7, 10.35, 11.05, 5.3, 9.6, 0.15, corners='blbr'))
    ex(cham('side_box', 6.95, 7.3, 11.1, 12.15, 4.2, 5.75, 0.12, corners='tlbl'))
    a(box('side_vent', (6.92, 11.4, 4.45), (6.95, 11.85, 5.5)))
    a(box('bolt_knob', (8.7, 11.3, 7.3), (9.0, 11.7, 7.8)))
    # rear notch sight ears on the base notch z, drum to the side
    a(box('sight_base', (7.55, 12.42, 4.9), (8.45, 12.5, 5.3)))
    a(box('sight_ear_l', (7.55, 12.5, 5.0), (7.75, 12.66, 5.22)))
    a(box('sight_ear_r', (8.25, 12.5, 5.0), (8.45, 12.66, 5.22)))
    ex(cham('sight_drum', 8.7, 8.95, 11.6, 12.05, 5.9, 6.4, 0.06))
    # trigger guard, trigger, raked pistol grip with cap and panel
    a(box('guard_front', (7.85, 9.65, 5.55), (8.15, 10.35, 5.75)))
    a(box('guard_bar', (7.85, 9.65, 5.75), (8.15, 9.85, 7.0)))
    a(rx('trigger', (7.9, 9.9, 6.15), (8.1, 10.35, 6.33), -10))
    a(strut('grip', (7.5, 10.35), (8.45, 7.75), 1.55, 7.35, 8.65, ext=0.05))
    a(strut('grip_cap', (8.45, 7.75), (8.55, 7.47), 1.75, 7.3, 8.7))
    for t, x0, x1 in (('l', 7.3, 7.35), ('r', 8.65, 8.7)):
        a(strut(f'grip_panel_{t}', (7.7, 9.8), (8.35, 8.1), 0.8, x0, x1))
    # skeletal stock (final z): dark tube, camo strut + drop arm, lower bar, brace, butt pad
    ex(cham('stock_tube', 7.55, 8.45, 11.3, 11.75, 8.67, 14.3, 0.1, corners='tltr'))
    ex(zsplit('stock_strut', 7.5, 8.5, 11.5, 11.88, [10.16, 12.2, 13.95], r=0.1, corners='tltr'))
    a(box('stock_arm', (7.55, 10.6, 10.22), (8.45, 11.6, 10.74)))
    ex(cham('stock_lower', 7.6, 8.4, 10.85, 11.35, 9.36, 14.3, 0.12, corners='blbr'))
    a(strut('stock_brace', (14.24, 9.55), (12.92, 10.7), 0.42, 7.6, 8.4, ext=0.1))
    ex(chamy('butt_pad', 7.45, 8.55, 9.4, 11.88, 14.18, 15.9, 0.25, corners='bB'))
    a(box('butt_plate', (7.5, 9.5, 15.9), (8.5, 11.8, 16.02)))
    return separate(E)


def is_magazine(name):
    return False


CAMO = (TEAL, TEAL_D, TEAL_L)


def region(n, fn, p, s, t, e):
    x, y, z = p
    side = fn in ('east', 'west')
    if n == 'can_face':
        return BLACK if abs(x - 8) < 0.3 and abs(y - BORE[1]) < 0.3 else TEAL_D
    if n.startswith('can_perf'):
        if side or fn in ('up', 'down'):
            u = z if side else z
            v = y if side else x * 1.3
            row = int((v - 10) / 0.33)
            if math.hypot(((u + 6.57 + (0.16 if row % 2 else 0)) % 0.33) - 0.165, ((v - 10) % 0.33) - 0.165) < 0.1:
                return BLACK
        return WHITE
    if n.startswith('can_collar'):
        return POLY
    if '_groove' in n:
        return POLY if n.startswith('pump') else TEAL_D
    if n.startswith(('can', 'barrel', 'rcv_upper', 'stock_strut', 'side_box')):
        if n.startswith('barrel') and side and line(y, 11.3, 0.05):
            return SILVER_D
        if n.startswith('rcv_upper') and side and 11.4 < y < 11.9 and 2.9 < z < 4.4:
            return BLACK if (line(y, 11.43, .04) or line(y, 11.87, .04) or line(z, 2.93, .04) or line(z, 4.37, .04)) else SILVER
        return camo(p, CAMO, cell=1.4, seed=5)
    if n == 'side_vent':
        return BLACK
    if n.startswith(('fsight', 'tube', 'loop', 'rcv_rail', 'sight_base', 'sight_ear', 'bolt_knob')):
        if n == 'tube' and side and every(z, -4.6, 1.2, 0.08):
            return SILVER_D
        return SILVER
    if n.startswith('pump_pad'):
        return (40, 30, 26)
    if n.startswith('pump'):
        if side and n.startswith('pump_body') and every(z, -4.0, 0.4, 0.07) and 10.25 < y < 10.85:
            return (40, 30, 26)
        return POLY
    if n.startswith(('grip_panel',)):
        if every(y, 8.1, 0.3, 0.08):
            return BLACK
        return POLY_L
    if n.startswith(('rcv_collar', 'rcv_lower', 'port', 'guard', 'trigger', 'grip', 'sight_drum', 'stock', 'butt')):
        if n.startswith('trigger') or n == 'sight_drum':
            return BLACK
        if n.startswith('butt_rib'):
            return (40, 30, 26)
        return POLY
    return POLY


special = painter(region)

# Ace/Izanagi identity pass: exact face paint and a denser 1P atlas.
T = 20
ATLAS = 512
from identity import enhance
special = enhance("botheration_mk_28", special, T)

# W123 material pass replaces full-face flat special paint.
STYLE = "material"
from surface import setup as material_setup
MATERIALS, material, special = material_setup("botheration_mk_28")
