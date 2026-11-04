"""W302 Stubborn Oak authored solids (model px, muzzle -z, up +y, gun right +x).

Proportions measured from the read-only Stubborn Oak.blend at a uniform 24.102 px/m.
Contract v2 = mindbender_s_ambition_adept (aggressive shotgun).  Placement: rip
z - 3.15 (trigger and butt land on the contract), rip y + 0.88 (bore 11.84);
deliberate fits: barrel/fore-end +1 px longer to reach muzzle -9.75, stock
lowered 0.25 px, grip moved 0.95 px forward, everything z -8.6..4.4 kept under
y 12.45 for the W148 overlay sight line, front-sight hood raised to frame the
W148 bead, receiver floor kept clear of the inserted-shell path.
"""
import math
from oak_math import chamfer_section

BORE = (8.0, 11.84)
MUZZLE_Z, BUTT_Z = -9.75, 16.03
DZ, DY_STOCK = -3.15, 0.63      # rip -> contract for stock slopes (rip frame values below)


def box(name, lo, hi, mat, group=None, pitch=0.0, pivot=None):
    return dict(name=name, lo=list(lo), hi=list(hi), mat=mat, group=group or name.split('_')[0],
                pitch=pitch, pivot=pivot)


def slope(name, p0, p1, thick, x0, x1, mat, side='below', ext=(0.0, 0.0), group=None,
          chamfer=0.0):
    """Box whose top (side='below') or bottom (side='above') face lies on the
    (z,y) line p0->p1; ends perpendicular to the line."""
    dz, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dz, dy)
    ux, uy = dz / L, dy / L
    theta = math.degrees(math.atan2(-uy, ux))
    ny, nz = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    mz, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    shift = (ext[1] - ext[0]) / 2
    mz, my = mz + ux * shift, my + uy * shift
    sgn = -1 if side == 'below' else 1
    cy, cz = my + sgn * ny * thick / 2, mz + sgn * nz * thick / 2
    half = (L + ext[0] + ext[1]) / 2
    if chamfer:
        top = side == 'below'
        return chamfer_section(name, x0, x1, cy - thick / 2, cy + thick / 2, cz - half, cz + half,
                               chamfer, mat, top=top, bottom=not top, pitch=theta,
                               pivot=[8.0, cy, cz], group=group or name)
    return [box(name, (x0, cy - thick / 2, cz - half), (x1, cy + thick / 2, cz + half), mat,
                group, pitch=theta, pivot=[(x0 + x1) / 2, cy, cz])]


def st(z, y):
    """rip-frame stock point -> contract."""
    return (round(z + DZ, 4), round(y + DY_STOCK, 4))


def front(S):
    by = BORE[1]
    # barrel with a real 0.4 px bore, 0.34 px deep
    S.append(box('barrel_tube', (7.6, by - .4, -9.41), (8.4, by + .4, 1.4), 'steel'))
    S.append(box('barrel_lip_top', (7.6, by + .2, MUZZLE_Z), (8.4, by + .4, -9.41), 'steel', 'barrel'))
    S.append(box('barrel_lip_bottom', (7.6, by - .4, MUZZLE_Z), (8.4, by - .2, -9.41), 'steel', 'barrel'))
    S.append(box('barrel_lip_left', (7.6, by - .2, MUZZLE_Z), (7.8, by + .2, -9.41), 'steel', 'barrel'))
    S.append(box('barrel_lip_right', (8.2, by - .2, MUZZLE_Z), (8.4, by + .2, -9.41), 'steel', 'barrel'))
    S.append(box('barrel_bore_stop', (7.8, by - .2, -9.43), (8.2, by + .2, -9.41), 'bore', 'barrel'))
    # hooded front sight; window x 7.68..8.32 frames the W148 bead (top 13.15)
    S.append(box('fsight_base', (7.5, 12.2, -9.5), (8.5, 12.42, -8.0), 'ivory', 'fsight'))
    for side, (xa, xb) in (('l', (7.5, 7.68)), ('r', (8.32, 8.5))):
        S.append(box(f'fsight_leg_front_{side}', (xa, 12.35, -9.38), (xb, 13.45, -9.22), 'ivory',
                     'fsight', pitch=28, pivot=[8, 12.9, -9.3]))
        S.append(box(f'fsight_leg_rear_{side}', (xa, 12.35, -8.48), (xb, 13.45, -8.32), 'ivory',
                     'fsight', pitch=-28, pivot=[8, 12.9, -8.4]))
    S.append(box('fsight_hood', (7.5, 13.3, -9.1), (8.5, 13.44, -8.6), 'ivory', 'fsight'))
    S.append(box('fsight_post', (7.94, 12.42, -8.98), (8.06, 12.8, -8.86), 'dark', 'fsight'))
    # barrel clamp, tube magazine, knurled cap
    S.append(box('clamp_strut', (7.66, 10.9, -8.55), (8.34, 11.5, -7.95), 'ivory', 'clamp'))
    S.append(box('tube_mag', (7.72, 10.42, -9.2), (8.28, 10.98, 1.5), 'steel', 'tube'))
    S.append(box('tube_cap', (7.6, 10.31, -9.7), (8.4, 11.09, -9.2), 'knurl', 'tube'))
    # pump fore-end (support hand): rounded belly, olive ribs painted, dark collars
    S += chamfer_section('pump', 7.2, 8.8, 9.75, 10.98, -5.4, 0.5, .22, 'pump', top=False,
                         bottom=True)
    for tag, (za, zb) in (('front', (-5.7, -5.4)), ('rear', (0.5, 0.8))):
        S.append(box(f'pump_collar_{tag}', (7.15, 9.7, za), (8.85, 10.98, zb), 'collar', 'pump'))
    # rip-identity grip ribs: ten proud rings wrapping sides + belly (silhouette teeth)
    for i in range(10):
        z = -4.45 + i * 0.44
        S.append(box(f'pump_rib_{i}', (7.16, 9.71, z), (8.84, 10.96, z + .2), 'pump', 'pump'))
    for tag, xa, xb in (('l', 7.4, 7.5), ('r', 8.5, 8.6)):
        S.append(box(f'action_bar_{tag}', (xa, 10.5, 0.8), (xb, 10.75, 1.45), 'dark', 'action'))
    # perforated heat shield (top <= 12.44): two chamfered segments + low bridge notch
    S += chamfer_section('shield_front', 7.4, 8.6, 11.0, 12.44, -6.05, -1.4, .24, 'ivory',
                         group='shield')
    S += chamfer_section('shield_rear', 7.4, 8.6, 11.0, 12.44, -0.3, 1.3, .24, 'ivory',
                         group='shield')
    S.append(box('shield_bridge', (7.4, 11.0, -1.4), (8.6, 12.0, -0.3), 'ivory', 'shield'))


def rear(S):
    # receiver [7.36,10.45..12.3, 1.3..9.2]; floor open over shell path z 3.68..5.22
    S += chamfer_section('recv_upper', 7.36, 8.64, 11.33, 12.3, 1.3, 9.2, .2, 'ivory',
                         group='recv')
    S.append(box('recv_lower_front', (7.36, 10.45, 1.3), (8.64, 11.33, 3.6), 'ivory', 'recv'))
    S.append(box('recv_drop', (7.36, 10.0, 1.45), (8.64, 10.45, 3.55), 'ivory', 'recv'))
    S.append(box('recv_lower_rear', (7.36, 10.45, 7.05), (8.64, 11.33, 8.85), 'ivory', 'recv'))
    S.append(box('recv_port_wall_l', (7.36, 10.45, 3.6), (7.5, 11.33, 7.05), 'ivory', 'recv'))
    S.append(box('recv_port_wall_r', (8.5, 10.45, 3.6), (8.64, 11.33, 7.05), 'ivory', 'recv'))
    S.append(box('recv_port_roof', (7.5, 10.9, 3.6), (8.5, 11.33, 7.05), 'dark', 'port'))
    S.append(box('recv_rail', (7.64, 12.3, 2.2), (8.36, 12.42, 4.9), 'ivory', 'rail'))
    # Stubborn Oak rear sight hump, kept under the W148 notch line (<= 12.48)
    S += slope('rsight_ramp', (5.3, 12.3), (5.62, 12.48), .16, 7.52, 8.48, 'ivory',
               ext=(0, .03), group='rsight')
    S.append(box('rsight_hump', (7.52, 12.3, 5.6), (8.48, 12.48, 7.6), 'ivory', 'rsight'))
    # rip rear-sight ears: lateral only (x <=7.74 / >=8.26) so the x=8 eye ray stays open
    for tag, xa, xb in (('l', 7.52, 7.74), ('r', 8.26, 8.48)):
        S.append(box(f'rsight_ear_{tag}', (xa, 12.3, 6.15), (xb, 12.82, 7.45), 'ivory', 'rsight'))
        S += slope(f'rsight_ear_ramp_{tag}', (5.7, 12.3), (6.25, 12.82), .3, xa, xb, 'ivory',
                   ext=(0, .03), group='rsight')
    # trigger group (front post clear of the shell path)
    S.append(box('guard_post', (7.9, 9.1, 5.3), (8.1, 10.45, 5.46), 'dark', 'guard'))
    S.append(box('guard_bar', (7.9, 9.1, 5.3), (8.1, 9.24, 7.45), 'dark', 'guard'))
    S.append(box('trigger_blade', (7.93, 9.86, 5.98), (8.07, 10.45, 6.16), 'dark', 'trigger'))
    S.append(box('trigger_hook', (7.93, 9.5, 5.95), (8.07, 9.92, 6.11), 'dark', 'trigger',
                 pitch=25, pivot=[8, 9.9, 6.07]))
    # raked pistol grip: rip-thick (1.45 px), 25 deg rake, top buried in receiver floor
    gp = [8.0, 8.786, 7.927]
    S.append(box('grip_core', (7.46, 6.651, 7.202), (8.54, 10.921, 8.652), 'grip', 'grip',
                 pitch=-25, pivot=gp))
    S.append(box('grip_heel', (7.44, 6.651, 7.202), (8.56, 7.05, 8.9), 'grip', 'grip',
                 pitch=-25, pivot=gp))
    S.append(box('grip_web', (7.46, 10.12, 7.0), (8.54, 10.47, 9.25), 'grip', 'grip'))
    # fixed full stock: rip profile (straight comb, wrist dip, sloped belly), 0.2 bevels
    X0, X1, R = 7.32, 8.68, .2
    S += chamfer_section('stock_butt', X0, X1, 9.9, 12.18, 11.5, 15.8, R, 'ivory', group='stock')
    S += chamfer_section('stock_wrist', X0, X1, 10.2, 11.88, 9.2, 11.6, R, 'ivory', group='stock')
    S += slope('stock_belly', (9.25, 10.23), (15.8, 8.76), 1.6, X0, X1, 'ivory', side='above', ext=(0, -.4),
               group='stock')
    S += slope('stock_neck', (9.2, 12.25), (10.3, 11.88), .6, X0, X1, 'ivory', ext=(0, .05),
               group='stock', chamfer=R)
    S += slope('stock_comb', (10.9, 11.88), (11.6, 12.18), .6, X0, X1, 'ivory', ext=(.05, 0),
               group='stock', chamfer=R)
    S.append(box('stock_toe', (X0, 8.82, 15.3), (X1, 10.0, 15.8), 'ivory', 'stock'))
    S.append(box('butt_pad', (7.27, 8.7, 15.8), (8.73, 12.25, BUTT_Z), 'rubber', 'pad'))


def design():
    S = []
    front(S)
    rear(S)
    return S
