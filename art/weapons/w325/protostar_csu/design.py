"""W325 Protostar CSu (rare, adaptive SMG, tan/olive camo) over base bug_out_bag (W166/W212 reload, W153 sight).
Detail pass v2.

Model px, muzzle -z, up +y, centre x=8.  Uniform map 28 px/m; grip centre on the base grip (z 7.4).
v2: chamfered shroud/receiver/stock/grip/magazine, real square muzzle with bore, rail ribs, instrument-panel
inset, screws, flat-painted caps/strips.  ADS: the low irons are replaced by one open front sight frame (sight_*)
around the W153 aim point (aperture x 7.74..8.26, y 13.5..13.98); the receiver top is 13.3 with a 13.36 rail; the stock behind z 12.95 is
lowered to the base stock profile (top 12.45, sampled 0.75 px higher in the rip so the camo/olive split is kept).
"""
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib_m8'))
from detail import box, rx, slope, cham, chamy, zsplit, Flat, bore_disc, separate  # noqa: E402

S = 28.0
GZ, GW = 7.4, 0.012
SY, SW = 13.75, 0.165
BORE = (8.0, 12.475)
LOW_Z, LOW_DY = 12.82, 0.75


def model2world(name, p):
    x, y, z = p
    if name.startswith(('stock_top', 'butt')):
        y += LOW_DY
    return (-(x - 8.0) / S, GW + (z - GZ) / S, SW + (y - SY) / S)


def elements():
    E = []
    a = E.append; ex = E.extend
    # square shroud with a stepped muzzle and a real bore
    ex(zsplit('shroud', 7.65, 8.35, 11.95, 13.0, [-3.45, -1.9, -0.5], r=0.12, corners='tltrblbr'))
    for nm, lo, hi in (('t', (7.6, 12.78, -3.75), (8.4, 13.05, -3.45)), ('b', (7.6, 11.9, -3.75), (8.4, 12.17, -3.45)),
                       ('l', (7.6, 12.17, -3.75), (7.87, 12.78, -3.45)), ('r', (8.13, 12.17, -3.75), (8.4, 12.78, -3.45))):
        a(box(f'muzzle_{nm}', lo, hi))
    a(box('muzzle_bore', (7.87, 12.17, -3.47), (8.13, 12.78, -3.45)))
    for i in range(3):
        z = -2.9 + i * 0.5
        a(box(f'shroud_vent_{i}', (7.62, 12.3, z), (8.38, 12.65, z + 0.22)))
    # upper receiver in three chamfered steps
    ex(cham('rcv_front', 7.3, 8.7, 11.7, 13.3, -0.5, 2.5, 0.22, corners='tltr'))
    ex(cham('rcv_main', 7.4, 8.6, 11.1, 13.3, 2.5, 8.2, 0.22, corners='tltr'))
    ex(zsplit('rcv_rear', 7.45, 8.55, 11.35, 13.2, [8.2, 10.5, 12.82], r=0.2, corners='tltr'))
    a(box('panel_l', (7.33, 12.15, 4.2), (7.4, 12.7, 6.9)))
    a(box('panel_r', (8.6, 12.15, 4.2), (8.67, 12.7, 6.9)))
    for i, (z, x) in enumerate(((0.0, 7.26), (0.0, 8.7), (9.3, 7.41), (9.3, 8.55))):
        a(box(f'screw_{i}', (x, 12.4, z), (x + 0.04, 12.6, z + 0.2)))
    ex(cham('handguard', 7.35, 8.65, 10.62, 11.7, 0.3, 2.6, 0.2, corners='blbr'))
    for i in range(4):
        a(box(f'hg_rib_{i}', (7.31, 10.84, 0.6 + i * 0.5), (8.69, 11.6, 0.8 + i * 0.5)))
    a(box('lower_rail', (7.42, 11.25, 2.6), (8.58, 11.7, 4.6)))
    # top rail with ribs (top 13.5) and the open front sight frame around the aim point
    a(box('rail', (7.62, 13.3, 2.7), (8.38, 13.33, 7.9)))
    for i in range(8):
        z = 2.85 + i * 0.62
        if 2.6 < z < 3.5:
            continue
        a(box(f'rail_rib_{i}', (7.6, 13.3, z), (8.4, 13.36, z + 0.3)))
    a(box('sight_base', (7.5, 13.33, 2.75), (8.5, 13.5, 3.45)))
    a(box('sight_post_l', (7.5, 13.5, 2.85), (7.74, 14.1, 3.35)))
    a(box('sight_post_r', (8.26, 13.5, 2.85), (8.5, 14.1, 3.35)))
    a(box('sight_hood', (7.5, 13.98, 2.85), (8.5, 14.1, 3.35)))
    a(box('charge_handle', (8.6, 12.0, 0.6), (8.82, 12.35, 1.4)))
    a(box('charge_knob', (8.82, 11.95, 0.6), (8.95, 12.4, 0.85)))
    # D trigger guard frame: raked front leg, bottom bar, trigger, pistol grip
    a(slope('guard_front', (4.05, 7.55), (2.6, 10.9), 0.95, 7.45, 8.55, side='above', ext=(0.15, 0.1)))
    ex(cham('guard_bar', 7.45, 8.55, 7.5, 8.05, 3.75, 6.8, 0.15, corners='blbr'))
    a(box('guard_screw', (7.4, 7.62, 3.95), (8.6, 7.9, 4.25)))
    a(box('trigger', (7.9, 10.05, 6.0), (8.1, 11.1, 6.22), {'origin': [8.0, 11.1, 6.1], 'x': -15}))
    for e in chamy('grip', 7.43, 8.57, 7.45, 11.1, 6.6, 8.25, 0.2):
        e['rotation'] = {'origin': [8.0, 9.3, 7.4], 'x': -6}
        a(e)
    # stock: lowered top section, sloped belly, web, heel, butt pad
    ex(cham('stock_top', 7.45, 8.55, 11.35, 12.45, 12.82, 15.05, 0.2, corners='tltr'))
    # stepped (axis-aligned) belly following the rip slope, each step flush with the stock top above it
    a(box('stock_step0', (7.45, 10.6, 12.95), (8.55, 11.35, 13.45)))
    a(box('stock_step1', (7.45, 9.75, 13.45), (8.55, 11.35, 13.9)))
    ex(chamy('stock_heel', 7.45, 8.55, 8.9, 11.35, 13.9, 15.05, 0.15, corners='bB'))
    ex(cham('butt_pad', 7.38, 8.62, 8.45, 12.45, 15.05, 15.45, 0.15))
    a(box('stock_screw', (7.41, 10.4, 14.3), (8.59, 10.65, 14.55)))
    # magazine (moving leaf)
    ex(cham('mag_body', 7.66, 8.34, 5.65, 7.6, 6.8, 7.8, 0.1, corners='blbr'))
    ex(cham('mag_floor', 7.6, 8.4, 5.35, 5.65, 6.72, 7.9, 0.08, corners='blbr'))
    return separate(E)


from paint import painter, camo, line, every  # noqa: E402

PALETTE = 24
FLAT_TOL = 6
CREAM, SAGE, BLUSH = (226, 212, 196), (150, 164, 120), (238, 222, 212)
OLIVE, OLIVE_L, BLACK, STEEL = (92, 90, 72), (116, 112, 92), (26, 26, 26), (186, 186, 182)
PALETTE_KEEP = [CREAM, SAGE, BLUSH, OLIVE, OLIVE_L, BLACK, STEEL, (60, 90, 200), (200, 50, 50), (80, 200, 220)]


def region(n, fn, p, s, t, e):
    x, y, z = p
    side = fn in ('east', 'west')
    if n == 'muzzle_bore':
        return BLACK
    if n.startswith(('muzzle', 'hg_rib', 'rail')):
        return STEEL if n.startswith('rail') else BLUSH
    if n.startswith('shroud_vent') or n.startswith(('screw', 'guard_screw', 'stock_screw', 'trigger')):
        return BLACK
    if n.startswith('panel'):
        if side and 12.25 < y < 12.6:
            for z0, z1, col in ((4.5, 4.8, (60, 90, 200)), (4.9, 5.2, (200, 50, 50)), (6.2, 6.7, (80, 200, 220))):
                if z0 < z < z1:
                    return col
        return (44, 44, 40)
    if n.startswith('sight') or n.startswith('charge'):
        return (64, 64, 60)
    if '_groove' in n:
        return SAGE
    if n.startswith(('shroud', 'handguard')):
        if n.startswith('handguard') and side and every(z, 0.4, 0.25, 0.06):
            return CREAM
        return BLUSH
    if n.startswith(('rcv',)):
        if side and line(y, 11.75, 0.05):
            return OLIVE
        return camo(p, (BLUSH, SAGE, CREAM), cell=1.3, seed=11, cuts=(0.55, 0.72))
    if n.startswith('lower_rail'):
        return STEEL
    if n.startswith('grip'):
        if side and z < 7.6 and y > 8.2:
            return camo(p, (CREAM, SAGE, BLUSH), cell=0.8, seed=12)
        return OLIVE
    if n.startswith('mag'):
        return BLUSH if not n.startswith('mag_floor') else STEEL
    if n == 'butt_pad' or n.startswith('butt_pad'):
        return (44, 44, 48)
    if n.startswith('stock_top'):
        return camo(p, (BLUSH, SAGE, CREAM), cell=1.3, seed=11, cuts=(0.55, 0.72)) if y > 12.0 else OLIVE
    return OLIVE


special = painter(region)

# Ace/Izanagi identity pass: exact face paint and a denser 1P atlas.
T = 20
ATLAS = 512
from identity import enhance
special = enhance("protostar_csu", special, T)

# W123 material pass replaces full-face flat special paint.
STYLE = "material"
from surface import setup as material_setup
MATERIALS, material, special = material_setup("protostar_csu")
