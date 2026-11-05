"""W325 Plemusa-B (rare grenade launcher, Adaptive; no exact frame row) over base salvager_s_salvo (W173/W220:
moving `_barrel` leaf, static `_body` leaf, `_round` shell).

Rip (muzzle at rip -y, up +z) at a uniform 26 px/m proper rotation anchored on the base W201 grip hand: pistol-grip
middle rip (y 0.02, z 0.023) -> model (z 8.24, y 8.18).  The front D-loop foregrip then lands at z ~-1.8, y ~8.6
(base support hand -2.14 / 8.9); muzzle z -6.8 (base -7.83), butt z 15.2 (base 17.17).
The base iron sight centre (8, 14.30, -2.1) is 2.4 px above Plemusa's shroud, so a front ring sight on a short tower
(textured from the rip's open front O-frame) frames the W148 aim dot there.
parts.magazine = the moving front group (prefix brl_: shroud, front window, foregrip loop, foot, sight tower), meant for
the base `_barrel` leaf; parts.body = drum, receiver, grip, stock.  The `_round` leaf should keep the base shell art.
"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_m10'))
from m10 import RipMap, box, bar, post, disc, rc, seg, face_xyz, rgbn

S = 26.0
M = RipMap(S, (0.02, 0.023), (8.24, 8.18), along='y', up='z', muzzle='-')
T = 20
ATLAS = 1024
FLAT_TOL = 34
PALETTE = 16
SIGHT = (8.0, 14.30, -2.1)
RING_RIP = (-0.525, 0.135)        # rip (y, z) centre of the front O-frame window, texture source for the sight ring


def is_magazine(n): return n.startswith('brl_')


def R(name, hw, yr, zr, **kw): return M.rb(name, hw, yr, zr, **kw)


def RC(name, hw, yr, zr, c=0.3, top=True, bottom=True, axis='z'): return rc(M, name, hw, yr, zr, c, top, bottom, axis)


def elements():
    E = []
    # ---- moving front group (base `_barrel` leaf): chamfered white shroud with the open O-window, toothed rail,
    # D-loop grip, foot block, front ring sight
    E += RC('brl_shroud_top', 0.033, (-0.548, -0.267), (0.147, 0.167), 0.26, bottom=False)
    E += RC('brl_shroud', 0.033, (-0.490, -0.267), (0.108, 0.147), 0.22, top=False)
    E += RC('brl_window_front', 0.033, (-0.562, -0.548), (0.108, 0.167), 0.26)
    E.append(R('brl_window_bot', 0.033, (-0.548, -0.490), (0.108, 0.118)))
    E.append(R('brl_band', (-0.035, 0.035), (-0.470, -0.458), (0.106, 0.169)))
    E.append(R('brl_band2', (-0.035, 0.035), (-0.300, -0.288), (0.106, 0.169)))
    E.append(R('brl_rail', 0.028, (-0.540, -0.420), (0.100, 0.108)))
    for i in range(5):
        y = -0.534 + i * 0.022
        E.append(R(f'brl_tooth{i}', 0.030, (y, y + 0.010), (0.096, 0.100)))
    E += RC('brl_loop_top', 0.034, (-0.420, -0.267), (0.078, 0.108), 0.22, top=False)
    g0 = M.m(0, -0.385, 0.078); g1 = M.m(0, -0.345, -0.002)
    E.append(post('brl_fgrip', 8 - 0.030 * S, 8 + 0.030 * S, (g0[2], g0[1]), (g1[2], g1[1]), 0.034 * S, ext=(0.1, 0.1)))
    _L = math.hypot(g1[2] - g0[2], g1[1] - g0[1]); _nz, _ny = -(g1[1] - g0[1]) / _L, (g1[2] - g0[2]) / _L
    _o = 0.034 * S / 2 + 0.05
    E.append(post('brl_fgrip_face', 8 - 0.026 * S, 8 + 0.026 * S, (g0[2] + _nz * _o, g0[1] + _ny * _o), (g1[2] + _nz * _o, g1[1] + _ny * _o), 0.12, ext=(-0.15, -0.1)))
    E.append(R('brl_loop_bot', 0.026, (-0.360, -0.272), (-0.012, -0.002)))
    E.append(R('brl_loop_rear', 0.026, (-0.282, -0.267), (-0.012, 0.078)))
    E += RC('brl_foot', 0.033, (-0.395, -0.267), (-0.074, -0.012), 0.24, top=False)
    cx, cy, cz = SIGHT
    E.append(box('brl_sight_post', (cx - 0.22, M.m(0, 0, 0.162)[1], cz - 0.25), (cx + 0.22, cy - 0.62, cz + 0.25)))
    E.append(box('brl_sight_base', (cx - 0.4, M.m(0, 0, 0.162)[1], cz - 0.45), (cx + 0.4, M.m(0, 0, 0.167)[1] + 0.25, cz + 0.45)))
    E.append(box('brl_sight_bot', (cx - 0.62, cy - 0.62, cz - 0.15), (cx + 0.62, cy - 0.36, cz + 0.15)))
    E.append(box('brl_sight_top', (cx - 0.62, cy + 0.36, cz - 0.15), (cx + 0.62, cy + 0.62, cz + 0.15)))
    E.append(box('brl_sight_l', (cx - 0.62, cy - 0.36, cz - 0.15), (cx - 0.36, cy + 0.36, cz + 0.15)))
    E.append(box('brl_sight_r', (cx + 0.36, cy - 0.36, cz - 0.15), (cx + 0.62, cy + 0.36, cz + 0.15)))
    # ---- static body: drum front plate, octagonal yellow drum with bands, black side plate
    oc = 0.055
    E += RC('drum_plate', (-0.115, 0.095), (-0.267, -0.249), (-0.044, 0.162), 0.4)
    E += RC('drum_plate2', (-0.105, 0.085), (-0.249, -0.205), (-0.034, 0.152), 0.4)
    dc = M.m(-0.011, 0, oc); hw = 0.068 * S
    for k, (ya, yb) in enumerate(((-0.205, -0.180), (-0.180, -0.113), (-0.113, -0.088))):
        r_ = hw + (0.12 if k != 1 else 0)
        a_ = r_ * 0.4142
        za, zb = M.m(0, ya, 0)[2], M.m(0, yb, 0)[2]
        E.append(box(f'drum{k}_w', (dc[0] - r_, dc[1] - a_, za), (dc[0] + r_, dc[1] + a_, zb)))
        E.append(box(f'drum{k}_v', (dc[0] - a_, dc[1] - r_, za), (dc[0] + a_, dc[1] + r_, zb)))
        for d, ang in (('a', 45), ('b', -45)):
            E.append(box(f'drum{k}_{d}', (dc[0] - r_, dc[1] - a_, za), (dc[0] + r_, dc[1] + a_, zb),
                         rot={'origin': [round(dc[0], 4), round(dc[1], 4), round((za + zb) / 2, 4)], 'z': ang}))
    E += RC('side_plate', (0.090, 0.140), (-0.238, -0.085), (0.062, 0.100), 0.2)
    for i in range(3):
        E.append(box(f'side_dot{i}', (M.m(0.141, 0, 0)[0] - 0.06, M.m(0, 0, 0.078)[1], M.m(0, -0.18 + i * 0.012, 0)[2]),
                     (M.m(0.141, 0, 0)[0], M.m(0, 0, 0.084)[1], M.m(0, -0.172 + i * 0.012, 0)[2])))
    # ---- receiver: white front block, hump with screws, green HAKKE upper split in panels
    E += RC('recv_front', 0.036, (-0.115, -0.042), (-0.014, 0.168), 0.3, bottom=False)
    E += RC('recv_hump', 0.030, (-0.058, 0.052), (0.166, 0.195), 0.22, bottom=False)
    for i, y in enumerate((-0.045, 0.040)):
        E.append(R(f'hump_screw{i}', 0.031, (y, y + 0.006), (0.183, 0.189)))
    E += RC('recv_top', 0.034, (-0.042, 0.236), (0.120, 0.163), 0.28, bottom=False)
    E += RC('recv_low', 0.032, (-0.042, 0.236), (0.086, 0.120), 0.22, top=False)
    E.append(R('recv_seam', 0.0335, (-0.042, 0.236), (0.118, 0.122)))
    E.append(R('ejector', (0.034, 0.038), (0.030, 0.080), (0.130, 0.140)))
    E.append(R('rear_pin', (0.034, 0.039), (0.170, 0.180), (0.100, 0.112)))
    # ---- trigger group: frame, guard loop, trigger, raked grip with back strap
    E.append(R('grip_frame', 0.034, (-0.042, 0.068), (0.060, 0.086)))
    E.append(R('guard_front', 0.012, (-0.072, -0.062), (-0.006, 0.060)))
    E.append(R('guard_bar', 0.012, (-0.072, -0.008), (-0.010, 0.000)))
    E.append(R('trigger', 0.006, (-0.050, -0.040), (0.026, 0.060)))
    p0 = M.m(0, -0.002, 0.062); p1 = M.m(0, 0.046, -0.016)
    E.append(post('grip', 8 - 0.030 * S, 8 + 0.030 * S, (p0[2], p0[1]), (p1[2], p1[1]), 0.050 * S, ext=(0.1, 0.1)))
    E.append(post('grip_strap', 8 - 0.026 * S, 8 + 0.026 * S, (p0[2] + 0.7, p0[1]), (p1[2] + 0.7, p1[1]), 0.25, ext=(0, 0.1)))
    E += RC('grip_floor', 0.030, (-0.042, 0.068), (-0.030, -0.014), 0.18, top=False)
    E += RC('rail_low', 0.034, (-0.205, 0.072), (-0.074, -0.030), 0.24, top=False)
    for i in range(2):
        y = -0.010 + i * 0.05
        E.append(R(f'rail_bolt{i}', (0.034, 0.038), (y, y + 0.010), (-0.058, -0.048)))
    # ---- skeleton stock: strut, lower bar, tall chamfered butt pad
    s0 = M.m(0, 0.075, 0.086); s1 = M.m(0, 0.236, 0.010)
    E.append(bar('stock_strut', 8 - 0.020 * S, 8 + 0.020 * S, (s0[2], s0[1]), (s1[2], s1[1]), 0.020 * S, side='above', ext=(0, 0)))
    E += RC('stock_low', 0.020, (0.150, 0.236), (-0.030, 0.010), 0.16)
    E += RC('butt_pad', 0.036, (0.236, 0.262), (-0.044, 0.163), 0.3)
    E += RC('butt_rubber', 0.032, (0.262, 0.288), (-0.040, 0.159), 0.3)
    return E


def model2world(name, p):
    if name.startswith('brl_sight'):
        # sample the rip's front O-frame around its window centre
        dy, dz = M.m(0, RING_RIP[0], RING_RIP[1])[1] - SIGHT[1], M.m(0, RING_RIP[0], 0)[2] - SIGHT[2]
        return M.w((p[0], p[1] + dy, p[2] + dz))
    return M.w(p)


COL = {'brl_shroud': (222, 216, 198), 'brl_window': (222, 216, 198), 'brl_band': (46, 58, 56), 'brl_rail': (52, 60, 58),
       'brl_tooth': (40, 46, 44), 'brl_loop': (46, 58, 56), 'brl_fgrip': (40, 46, 44), 'brl_foot': (46, 58, 56),
       'brl_sight': (222, 216, 198), 'drum_plate': (44, 56, 54), 'drum0': (196, 188, 104), 'drum1': (214, 206, 122),
       'drum2': (196, 188, 104), 'side_plate': (34, 36, 38), 'side_dot': (92, 170, 92), 'recv_front': (214, 206, 122),
       'recv_hump': (226, 220, 202), 'hump_screw': (120, 120, 116), 'recv_top': (62, 104, 92), 'recv_low': (56, 94, 84),
       'recv_seam': (40, 66, 60), 'ejector': (220, 214, 196), 'rear_pin': (210, 206, 190), 'grip_frame': (222, 216, 198),
       'guard': (44, 52, 50), 'trigger': (210, 206, 190), 'grip': (40, 46, 44), 'rail_low': (214, 206, 122),
       'rail_bolt': (44, 52, 50), 'stock': (44, 56, 54), 'butt_pad': (44, 56, 54), 'butt_rubber': (30, 32, 34)}


def base_col(n):
    best = None
    for k in COL:
        if n.startswith(k) and (best is None or len(k) > len(best)): best = k
    return COL[best] if best else None


def special(e, fn, s, t):
    n = e['name']
    if n.startswith('brl_window_front') and fn == 'north':
        x, y, z = face_xyz(e, fn, s, t)
        if abs(x - 8) < 0.5 and abs(y - M.m(0, 0, 0.130)[1]) < 0.42: return (14, 14, 16, 255)
    if n.startswith('brl_sight_') and n not in ('brl_sight_post', 'brl_sight_base'):
        inner = {'brl_sight_bot': 'up', 'brl_sight_top': 'down', 'brl_sight_l': 'east', 'brl_sight_r': 'west'}[n]
        if fn == inner: return (36, 40, 40, 255)
    if n.startswith('drum_plate') and fn == 'north':
        x, y, z = face_xyz(e, fn, s, t)
        if (x - 8) ** 2 + (y - M.m(0, 0, 0.130)[1]) ** 2 < 0.62 ** 2: return (10, 10, 12, 255)
    if n.startswith('drum') and fn in ('north', 'south') and n[4:5].isdigit():
        x, y, z = face_xyz(e, fn, s, t); dc = M.m(-0.011, 0, 0.055)
        for k in range(6):
            a = math.radians(30 + 60 * k); hx, hy = dc[0] + 1.05 * math.cos(a), dc[1] + 1.05 * math.sin(a)
            if (x - hx) ** 2 + (y - hy) ** 2 < 0.3 ** 2: return (40, 40, 30, 255)
    if n.startswith('recv_top') and fn in ('east', 'west'):
        x, y, z = face_xyz(e, fn, s, t)
        if abs(y - M.m(0, 0, 0.145)[1]) < 0.06 and M.m(0, 0.030, 0)[2] < z < M.m(0, 0.085, 0)[2]: return (24, 26, 26, 255)
    if n.startswith('grip') and n != 'grip_frame' and fn in ('east', 'west'):
        x, y, z = face_xyz(e, fn, s, t)
        if (int(y * 4) + int(z * 4)) % 2 == 0: return (30, 34, 34, 255)
    if n.startswith('brl_shroud') and fn in ('east', 'west'):
        x, y, z = face_xyz(e, fn, s, t)
        if y < M.m(0, 0, 0.118)[1]: return (46, 58, 56, 255)
    c = base_col(n)
    if c is None: return None
    return c + (255,)


# Identity pass: direct face paint with crisp material edges and source-specific markings.
from identity import install
install(globals(), 'plemusa_b')

# Material pass supersedes all-face flat paint; geometry retained.
from materials import install as install_materials
install_materials(globals(), 'plemusa_b')
