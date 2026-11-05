"""W325 Badlands Mk.24 (rare, lightweight shotgun, red camo shroud, hex fore-end, no stock) over base
parcel_of_stardust_fell_to_earth (W221 shell insert, W148 sight).  Detail/style pass v2 (W30/DMW look).

Model px, muzzle -z, up +y, centre x=8.  Uniform 27.6 px/m map (kept for reference/proj only; faces are flat-painted);
trigger on the base trigger (z 7.36), muzzle -9.3, bore y 11.45.  Shell port open over the base shell path (z 3.41..4.95).
ADS: shroud crown top 12.33 (base top 12.18..12.33 behind z -1.42), rear sight = two lateral notch ears (sight_*) on
the base W148 notch z with tops 12.8 (base 12.80 there), receiver top steps 12.25 -> 12.0 -> 11.98, tail <= 11.85.  The rip has no stock.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib_m8'))
from detail import box, rx, cham, chamy, zsplit, strut, separate  # noqa: E402
from paint import painter, camo, line, every  # noqa: E402

S = 27.6
GZ, GW = 7.36, -0.08
SY, SW = 11.45, 0.142
BORE = (8.0, 11.45)
PALETTE = 24
FLAT_TOL = 6

RED, RED_D, RED_L = (128, 56, 54), (98, 42, 42), (152, 84, 74)
TAN, BLACK, POLY, POLY_L, STEEL, BRASS = (196, 176, 138), (18, 18, 20), (40, 40, 43), (58, 58, 62), (92, 94, 98), (176, 150, 96)
PALETTE_KEEP = [RED, RED_D, RED_L, TAN, BLACK, POLY, POLY_L, STEEL, BRASS]


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / S, GW + (z - GZ) / S, SW + (y - SY) / S)


def elements():
    E = []
    a = E.append; ex = E.extend
    cuts = [-9.05, -5.6, -1.5, 2.3]
    # muzzle face: square frame around the bore + bore stop
    for nm, lo, hi in (('t', (7.55, 11.85, -9.3), (8.45, 12.05, -9.05)), ('b', (7.55, 10.85, -9.3), (8.45, 11.05, -9.05)),
                       ('l', (7.55, 11.05, -9.3), (7.75, 11.85, -9.05)), ('r', (8.25, 11.05, -9.3), (8.45, 11.85, -9.05))):
        a(box(f'muzzle_{nm}', lo, hi))
    a(box('muzzle_bore', (7.75, 11.05, -9.12), (8.25, 11.85, -9.05)))
    # stepped triangular shroud, three segments with grooves (low band, chamfered mid, crown)
    ex(zsplit('shroud_low', 6.8, 9.2, 10.45, 11.25, cuts, r=0.22, corners='blbr', gtop=False))
    ex(zsplit('shroud_mid', 7.1, 8.9, 11.25, 11.95, cuts, r=0.28, corners='tltr', gtop=False))
    ex(zsplit('shroud_top', 7.45, 8.55, 11.95, 12.33, cuts, r=0.1, corners='tltr'))
    for t, x0, x1 in (('l', 6.74, 6.8), ('r', 9.2, 9.26)):
        a(box(f'shroud_trim_{t}', (x0, 10.95, -8.7), (x1, 11.12, 1.9)))
    a(box('top_rail', (7.85, 12.33, -8.6), (8.15, 12.42, -1.7)))
    for i in range(5):
        z = -8.3 + i * 1.5
        a(box(f'top_post_{i}', (7.78, 12.33, z), (8.22, 12.5, z + 0.3)))
    # tube magazine, cap, clip ring with bolt
    ex(cham('tube', 7.5, 8.5, 9.4, 10.45, -9.05, -5.5, 0.18, corners='blbr'))
    a(box('tube_cap', (7.6, 9.55, -9.3), (8.4, 10.3, -9.05)))
    ex(cham('tube_clip', 7.35, 8.65, 9.3, 10.45, -6.3, -5.6, 0.15, corners='blbr'))
    a(box('clip_bolt', (8.65, 9.65, -6.1), (8.75, 9.95, -5.8)))
    # hex pump fore-end: chamfered body, belly, end collars, side grip ribs
    ex(cham('pump', 7.0, 9.0, 8.9, 10.45, -5.3, 0.8, 0.3, corners='blbr'))
    a(box('pump_belly', (7.4, 8.55, -4.9), (8.6, 8.9, 0.4)))
    ex(cham('pump_front', 7.1, 8.9, 8.75, 10.45, -5.55, -5.3, 0.25, corners='blbr'))
    ex(cham('pump_rear', 7.15, 8.85, 8.6, 10.45, 0.8, 1.9, 0.25, corners='blbr'))
    for i in range(3):
        z = -4.3 + i * 1.6
        for t, x0, x1 in (('l', 6.94, 7.0), ('r', 9.0, 9.06)):
            a(box(f'pump_rib_{t}{i}', (x0, 9.1, z), (x1, 10.2, z + 0.9)))
    a(box('pump_lug', (7.7, 8.55, 1.0), (8.3, 8.75, 1.7)))
    # receiver: collar, chamfered upper, open shell port, rear lower, side bolt slot + knob
    ex(cham('recv_collar', 7.2, 8.8, 9.05, 12.3, 2.3, 3.0, 0.25, corners='tltr'))
    ex(cham('recv_upper0', 7.25, 8.75, 10.4, 12.25, 3.0, 6.3, 0.22, corners='tltr'))
    a(box('recv_upper_groove0', (7.31, 10.4, 6.3), (8.69, 12.0, 6.44)))
    ex(cham('recv_upper1', 7.25, 8.75, 10.4, 12.0, 6.44, 7.6, 0.22, corners='tltr'))
    ex(cham('recv_upper2', 7.3, 8.7, 10.4, 11.98, 7.6, 9.0, 0.2, corners='tltr'))
    a(box('port_front', (7.25, 9.35, 3.0), (8.75, 10.4, 3.3)))
    a(box('port_wall_l', (7.25, 9.5, 3.3), (7.45, 10.4, 5.1)))
    a(box('port_wall_r', (8.55, 9.5, 3.3), (8.75, 10.4, 5.1)))
    a(box('port_roof', (7.45, 10.12, 3.3), (8.55, 10.4, 5.1)))
    ex(cham('recv_lower', 7.25, 8.75, 9.6, 10.4, 5.1, 9.0, 0.15, corners='blbr'))
    a(box('bolt_slot', (8.75, 11.2, 6.6), (8.8, 11.7, 8.6)))
    a(box('bolt_knob', (8.75, 11.25, 6.7), (9.1, 11.65, 7.2)))
    a(box('recv_pin', (7.2, 9.75, 8.3), (8.8, 10.0, 8.55)))
    # rounded tail block (no stock on the rip)
    ex(cham('tail', 7.3, 8.7, 9.8, 11.85, 9.0, 10.7, 0.3))
    ex(cham('tail_cap', 7.5, 8.5, 10.15, 11.6, 10.7, 11.05, 0.18))
    # rear notch sight: base plate + lateral ears (open notch; the W148 line passes between them)
    a(box('sight_base', (7.45, 12.25, 4.75), (8.55, 12.4, 5.85)))
    a(box('sight_ear_l', (7.45, 12.4, 5.36), (7.72, 12.8, 5.78)))
    a(box('sight_ear_r', (8.28, 12.4, 5.36), (8.55, 12.8, 5.78)))
    # trigger guard (real opening), trigger, raked pistol grip with cap
    a(box('guard_front', (7.75, 8.65, 6.45), (8.25, 9.6, 6.7)))
    a(box('guard_bar', (7.75, 8.65, 6.7), (8.25, 8.85, 8.4)))
    a(rx('trigger', (7.9, 8.95, 7.0), (8.1, 9.6, 7.2), -15))
    g = chamy('grip', 7.3, 8.7, 6.3, 9.8, 8.6, 10.2, 0.25)
    for e in g:
        e['rotation'] = {'origin': [8.0, 8.0, 9.4], 'x': -26}
    ex(g)
    a(rx('grip_cap', (7.25, 5.95, 8.5), (8.75, 6.3, 10.3), -26, [8.0, 8.0, 9.4]))
    return separate(E)


def is_magazine(name):
    return False


def region(n, fn, p, s, t, e):
    x, y, z = p
    side = fn in ('east', 'west')
    if n == 'muzzle_bore':
        return BLACK
    if n.startswith('muzzle') or n.startswith('top_post') or n.startswith('shroud_trim') or n == 'top_rail':
        return TAN
    if '_groove' in n:
        return RED_D if n.startswith('shroud') else POLY
    if n.startswith('shroud'):
        if fn == 'north' and abs(x - 8) < 0.42 and abs(y - BORE[1]) < 0.42:
            return BLACK
        if side and (line(y, 11.27, 0.05) or line(y, 11.93, 0.05)):
            return TAN
        if side and n.startswith('shroud_mid') and line(y, 11.6, 0.06) and every(z, -8.5, 0.6, 0.12):
            return TAN
        return camo(p, (RED, RED_D, RED_L), cell=1.5, seed=3)
    if n.startswith(('tube', 'clip')):
        return STEEL if n != 'tube_clip' else POLY_L
    if n.startswith('pump'):
        if n.startswith('pump_rib'):
            return POLY_L
        if side and n == 'pump' and 9.05 < y < 10.3:
            row = int((y - 9.05) / 0.32)
            zz = z + (0.25 if row % 2 else 0)
            if every(zz, -5.0, 0.5, 0.07) or every(y, 9.05, 0.32, 0.05):
                return BLACK
        return POLY
    if n.startswith(('recv_collar', 'port', 'recv_lower', 'recv_pin', 'tail', 'bolt', 'guard', 'trigger', 'grip')):
        if n.startswith('grip') and side and every(y, 6.6, 0.32, 0.07) and 6.5 < y < 8.8:
            return BLACK
        if n == 'bolt_slot':
            return BLACK
        return POLY if not n.startswith(('recv_pin', 'bolt_knob')) else STEEL
    if n.startswith('recv_upper'):
        if side and line(y, 10.45, 0.05):
            return TAN
        if side and n.startswith('recv_upper0') and 10.9 < y < 11.6 and 3.4 < z < 5.8:
            return BLACK if (line(y, 10.95, .05) or line(y, 11.55, .05) or line(z, 3.45, .05) or line(z, 5.75, .05)) else POLY_L
        return camo(p, (RED, RED_D, RED_L), cell=1.5, seed=3)
    if n.startswith('sight'):
        return POLY if n == 'sight_base' else BRASS
    return POLY


special = painter(region)

# Ace/Izanagi identity pass: exact face paint and a denser 1P atlas.
T = 20
ATLAS = 1024
from identity import enhance
special = enhance("badlands_mk_24", special, T)

# W123 material pass replaces full-face flat special paint.
STYLE = "material"
from surface import setup as material_setup
MATERIALS, material, special = material_setup("badlands_mk_24")
