"""W325 Harmony-21 (SUROS adaptive SMG) over base bug_out_bag (W166/W212 reload, W153 sight).  Detail pass v2.

Model px, muzzle -z, up +y, centre x=8.  The rip (muzzle -y, up +z, metres) is mapped with a station map:
length 33 px/m, muzzle..grip stretched x1.075 to the base muzzle (-4.0), grip..butt compressed x0.88 to the base butt;
height 33 px/m with the hook-sight lens centre on the base ADS line (w153 aim tip y 13.75), everything under the
receiver floor (grip, frame struts, magazine) compressed x0.6 so grip/magazine land in the base grip/magazine boxes.
v2: chamfered shell/shroud/spine/magazine, slotted canopy, rail ribs, charging handle, port, frame bolts, flat-painted
end/cap/strip faces; ADS: hook-sight frame moved onto the base sight z (2.83..3.32, inside the base rim height 14.29); rear wires and butt plate lowered under the base top profile (<=12.34), the hook sight is an
open frame (elements named sight_*) around the aim point.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib_m8'))
from detail import box, rx, slope, cham, chamy, zsplit, Flat, bore_disc, separate  # noqa: E402

SX, S = 30.0, 33.0
GZ, GW = 7.4, 0.009
FRONT, REAR = 1.075, 0.88
SIGHT_Y, SIGHT_W = 13.75, 0.1975
YB = SIGHT_Y + (0.08 - SIGHT_W) * S   # 9.8725 receiver floor
LOW = 0.6
BORE = (8.0, 10.96)


def model2world(name, p):
    x, y, z = p
    wx = -(x - 8.0) / SX
    wy = GW + (z - GZ) / (S * (FRONT if z <= GZ else REAR))
    wz = SIGHT_W + (y - SIGHT_Y) / S if y >= YB else 0.08 + (y - YB) / (S * LOW)
    return (wx, wy, wz)


def elements():
    E = []
    a = E.append; ex = E.extend
    # muzzle device: flat SUROS prong plate with a V notch, black stepped shroud with a bore
    a(box('muzzle_plate', (7.75, 10.45, -3.45), (8.25, 11.5, -1.85)))
    a(box('muzzle_prong_top', (7.75, 11.28, -3.62), (8.25, 11.5, -3.45)))
    a(box('muzzle_prong_bot', (7.75, 10.45, -3.62), (8.25, 10.67, -3.45)))
    a(box('muzzle_pin', (7.68, 10.85, -2.95), (8.32, 11.1, -2.7)))
    ex(cham('shroud_front', 7.63, 8.37, 10.4, 11.56, -1.9, -1.2, 0.14))
    ex(cham('shroud_rear', 7.42, 8.58, 10.38, 11.58, -1.2, 0.1, 0.2))
    a(box('shroud_ring', (7.38, 10.34, -0.4), (8.62, 11.62, -0.25)))
    a(slope('chin_spike', (-1.6, 8.78), (-0.4, 9.95), 0.2, 7.88, 8.12, side='above', ext=(0, 0.3)))
    # white upper shell: slanted nose, chamfered body, canopy with a slot, tail onto the stock spine
    a(slope('shell_nose', (-0.95, 10.4), (0.75, 12.4), 1.3, 7.1, 8.9, side='below', ext=(0, 0.1)))
    ex(zsplit('shell_body', 7.05, 8.95, 10.4, 12.05, [0.5, 3.6, 6.2, 8.6], r=0.3, corners='tltr'))
    ex(cham('shell_canopy', 7.3, 8.7, 12.0, 12.58, 0.9, 3.0, 0.22, corners='tltr'))
    ex(cham('shell_canopy_r', 7.3, 8.7, 12.0, 12.58, 4.9, 8.2, 0.22, corners='tltr'))
    for t, x0, x1 in (('l', 7.3, 7.6), ('r', 8.4, 8.7)):
        a(box(f'shell_slot_rail_{t}', (x0, 12.0, 3.0), (x1, 12.42, 4.9)))
    a(box('shell_slot_floor', (7.6, 12.0, 3.0), (8.4, 12.12, 4.9)))
    ex(cham('shell_tail0', 7.3, 8.7, 11.85, 12.42, 8.2, 9.9, 0.15, corners='tltr'))
    ex(cham('shell_tail1', 7.35, 8.65, 11.85, 12.15, 9.9, 11.6, 0.12, corners='tltr'))
    a(box('rail_top', (7.66, 12.58, 1.1), (8.34, 12.7, 2.8)))
    for i in range(2):
        z = 1.25 + i * 0.4
        a(box(f'rail_rib_{i}', (7.62, 12.7, z), (8.38, 12.78, z + 0.18)))
    a(box('rear_nub', (7.86, 12.55, 7.4), (8.14, 12.9, 7.8)))
    # side details: ejection port
    a(box('port_recess', (8.95, 11.15, 5.6), (9.02, 11.75, 7.4)))
    # hook sight: swept arm, open frame around the ADS aim point (aperture x 7.64..8.36, y 13.25..14.1)
    a(box('sight_ramp', (7.62, 12.78, 2.0), (8.38, 13.02, 2.7)))
    ex(cham('sight_arm', 7.62, 8.38, 12.78, 13.25, 2.7, 5.0, 0.12, corners='tltr'))
    a(box('sight_post_l', (7.5, 12.78, 2.85), (7.64, 14.1, 3.3)))
    a(box('sight_post_r', (8.36, 12.78, 2.85), (8.5, 14.1, 3.3)))
    a(box('sight_cap', (7.5, 14.1, 2.83), (8.5, 14.22, 3.32)))
    a(box('sight_sill', (7.64, 12.78, 2.85), (8.36, 13.25, 3.3)))
    # dark lower receiver band, front frame strut (trigger-guard hole behind it), trigger
    ex(zsplit('lower_band', 7.15, 8.85, 9.75, 10.45, [-0.75, 3.2, 8.3], r=0.18, corners='blbr', gtop=False, gbot=True))
    a(slope('strut_front', (6.45, 6.62), (-0.75, 9.45), 1.05, 7.2, 8.8, side='above', ext=(0, 0.1)))
    a(slope('strut_web', (4.05, 8.69), (0.6, 10.04), 0.95, 7.2, 8.8, side='above'))
    a(box('trigger', (7.9, 9.15, 6.08), (8.1, 9.8, 6.3), {'origin': [8.0, 9.8, 6.2], 'x': -12}))
    # pistol grip (chamfered vertical edges), frame stock (open triangle), butt plate with bent side wires
    ex(chamy('grip', 7.25, 8.75, 6.95, 9.8, 6.5, 8.15, 0.22))
    a(box('frame_heel', (7.2, 6.62, 5.95), (8.8, 7.45, 8.7)))
    for t, x in (('l', 7.12), ('r', 8.8)):
        a(box(f'frame_bolt_{t}', (x, 6.9, 6.2), (x + 0.08, 7.15, 6.45)))
    a(slope('frame_bar', (8.4, 6.67), (15.1, 8.42), 0.62, 7.4, 8.6, side='above', ext=(0, 0)))
    ex(zsplit('spine', 7.4, 8.6, 10.0, 11.85, [8.3, 11.0, 13.0, 15.05], r=0.22, corners='tltrblbr'))
    ex(cham('butt_plate', 7.2, 8.8, 8.42, 12.3, 15.0, 15.68, 0.2))
    a(box('butt_pad', (7.32, 8.6, 15.68), (8.68, 12.12, 15.8)))
    for t, x0, x1 in (('l', 6.92, 7.08), ('r', 8.92, 9.08)):
        a(slope(f'wire_{t}', (13.35, 10.05), (15.0, 11.8), 0.14, x0, x1, side='below'))
    # magazine (moving leaf): chamfered body, floor plate, witness ribs
    ex(cham('mag_body', 7.68, 8.32, 4.8, 7.45, 6.62, 7.85, 0.12, corners='blbr'))
    ex(cham('mag_floor', 7.6, 8.4, 4.52, 4.85, 6.55, 7.92, 0.1, corners='blbr'))
    return separate(E)


from paint import painter, line, every, text_hit  # noqa: E402

PALETTE = 18
FLAT_TOL = 30
WHITE, WHITE_D, DARK, DARK_L, ORANGE, BLACK = (214, 222, 214), (176, 186, 180), (40, 44, 43), (62, 67, 66), (206, 112, 46), (20, 21, 22)
PALETTE_KEEP = [ORANGE, BLACK]


def region(n, fn, p, s, t, e):
    x, y, z = p
    side = fn in ('east', 'west')
    if n.startswith('shroud_front') and fn == 'north' and abs(x - 8) < 0.2 and abs(y - 10.96) < 0.2:
        return BLACK
    if n.startswith(('muzzle_plate', 'muzzle_prong')):
        return BLACK if (n == 'muzzle_plate' and side and (abs(z + 2.2) < 0.12 or abs(z + 3.0) < 0.12) and abs(y - 10.98) < 0.14) else WHITE
    if n.startswith(('muzzle_pin', 'port', 'shell_slot_floor', 'sight_cap', 'butt_pad')):
        return BLACK if not n.startswith('sight_cap') else DARK
    if n.startswith('shroud'):
        if side and n.startswith('shroud_rear') and every(z, -1.1, 0.3, 0.08) and 10.6 < y < 11.35:
            return BLACK
        return DARK_L if n == 'shroud_ring' else DARK
    if n.startswith('shell_body') and side and '_groove' not in n:
        # SUROS logo: orange block mark + 3x5 letters, reading left->right as seen from either side
        u = z if fn == 'west' else -z
        u0 = 1.15 if fn == 'west' else -3.5
        if u0 - 0.65 < u < u0 - 0.25 and 10.78 < y < 11.43:
            return ORANGE
        if text_hit(u, 11.43 - y, 'SUROS', u0, 0, 0.13):
            return ORANGE
        # orange swoosh strip on the rear of the body
        if 0 < z - (6.0 + (y - 10.4) * 1.1) < 0.8:
            return ORANGE
        return WHITE
    if n.startswith('frame_bar') and side:
        u = s if fn == 'west' else 1 - s
        return ORANGE if (0.25 < u < 0.42 and 0.3 < t < 0.75) else DARK
    if n.startswith('shell_tail'):
        return ORANGE if z > 9.0 else WHITE
    if n.startswith(('shell', 'rail', 'rear_nub', 'sight')):
        if n.startswith('shell_body') and side and line(y, 10.5, 0.06):
            return WHITE_D
        return WHITE if not n.startswith('rail_top') else WHITE_D
    if n.startswith('mag'):
        if n.startswith('mag_floor'):
            return DARK
        return WHITE_D if (side and line(y, 7.2, 0.06)) else WHITE
    if n.startswith(('frame_bolt',)):
        return (120, 124, 122)
    if n.startswith('trigger'):
        return BLACK
    if n.startswith('grip') and side and every(y, 7.3, 0.35, 0.07) and y < 9.4:
        return BLACK
    if n.startswith(('lower_band', 'strut', 'grip', 'frame', 'spine', 'butt', 'wire', 'chin')):
        if n.startswith('lower_band') and side and line(y, 10.05, 0.05):
            return DARK_L
        return DARK
    return None


special = painter(region)

# Ace/Izanagi identity pass: exact face paint and a denser 1P atlas.
T = 20
ATLAS = 512
from identity import enhance
special = enhance("harmony_21", special, T)

# W123 material pass replaces full-face flat special paint.
STYLE = "material"
from surface import setup as material_setup
MATERIALS, material, special = material_setup("harmony_21")
