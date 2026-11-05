"""W325 Weaver-C (rare rocket launcher, Precision) over base pyroclastic_flow (W221 body + rear-loaded rocket).

Same HAKKE family/layout as Reginar-B: uniform 24 px/m proper rotation anchored on the base W201 hand contacts
(pistol-grip middle rip (y 0.012, z 0.006) -> model (z 14.53, y 7.7); foregrip lands z ~8.1).  Tube spans z 0.4..27.0
(base -7.8..19.2).  Side optic (rip +x, x .04-.09, z .153-.195) mirrored to +X and centred on the base ADS sight
(10.132, 12.69, eye +z).  Magazine = base reload rocket envelope (z 10.7..17.5), hand painted orange/cream.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_m10'))
from m10 import RipMap, PwMap, box, bar, post, disc, side_part, rc, cbox, rgbn, face_xyz

S = 24.0
M = PwMap(S, (0.012, 0.006), (14.53, 7.7), along='y', up='z', muzzle='-', a_cut=0.097, k=0.50)
T = 20
ATLAS = 1024
FLAT_TOL = 34
PALETTE = 16
SIGHT = (10.132, 12.69)
OPT_RIP = (0.066, 0.174)
OPT_D = (0.0, SIGHT[1] - M.m(0, 0, OPT_RIP[1])[1])
OPTF = side_part(M, SIGHT[0], OPT_RIP[0])


def R(name, hw, yr, zr, **kw): return M.rb(name, hw, yr, zr, **kw)


def RC(name, hw, yr, zr, c=0.32, top=True, bottom=True, axis='z'): return rc(M, name, hw, yr, zr, c, top, bottom, axis)


def elements():
    E = []
    # ---- front: cream tube, white muzzle cap, dark top shroud, side rail cages, under rail, foregrip
    E += RC('muzzle_cap', 0.040, (-0.574, -0.522), (0.133, 0.216), 0.36)
    E += RC('muzzle_lip', 0.036, (-0.580, -0.574), (0.137, 0.212), 0.32)
    E += RC('tube_front', 0.036, (-0.522, -0.198), (0.138, 0.211), 0.32, top=False)
    E += RC('top_strip', 0.030, (-0.570, -0.387), (0.211, 0.228), 0.16, bottom=False)
    E += RC('top_shroud', 0.034, (-0.387, -0.148), (0.208, 0.236), 0.24, bottom=False)
    for tag, xr in (('l', (-0.048, -0.036)), ('r', (0.036, 0.048))):
        E.append(R(f'cage_top_{tag}', xr, (-0.492, -0.198), (0.168, 0.177)))
        E.append(R(f'cage_bot_{tag}', xr, (-0.492, -0.198), (0.138, 0.146)))
        E.append(R(f'cage_end_{tag}', xr, (-0.492, -0.480), (0.138, 0.177)))
    E.append(R('under_rail', 0.034, (-0.494, -0.198), (0.104, 0.138)))
    E.append(R('fgrip_mount', 0.022, (-0.302, -0.234), (0.098, 0.114)))
    E += RC('fgrip', 0.017, (-0.298, -0.240), (-0.004, 0.102), 0.22, axis='y')
    for i in range(3):
        z = 0.012 + i * 0.026
        E.append(R(f'fgrip_rib_{i}', 0.0185, (-0.300, -0.238), (z, z + 0.006)))
    E.append(R('fgrip_cap', 0.013, (-0.292, -0.246), (-0.018, -0.004)))
    # ---- receiver: cream upper with dark window, orange top fin, top rail, light band, dark lower, trigger, grip
    E += RC('recv_upper', 0.037, (-0.198, 0.097), (0.140, 0.208), 0.3, bottom=False)
    E.append(R('recv_window', 0.039, (-0.084, 0.034), (0.153, 0.196)))
    f0 = M.m(0, -0.148, 0.239); f1 = M.m(0, -0.060, 0.212)
    E.append(bar('top_fin', 8 - 0.014 * S, 8 + 0.014 * S, (f0[2], f0[1]), (f1[2], f1[1]), 0.030 * S, ext=(0, 0)))
    E.append(R('top_fin_base', 0.020, (-0.148, -0.060), (0.208, 0.214)))
    E.append(R('top_rail', 0.016, (-0.057, 0.094), (0.208, 0.226)))
    E.append(R('recv_band', 0.040, (-0.198, 0.123), (0.113, 0.140)))
    r0 = M.m(0, 0.123, 0.140); r1 = M.m(0, 0.249, 0.124)
    E.append(bar('band_tail', 8 - 0.030 * S, 8 + 0.030 * S, (r0[2], r0[1]), (r1[2], r1[1]), 0.012 * S, ext=(0, 0)))
    E.append(R('rear_lug', 0.005, (0.150, 0.160), (0.098, 0.115)))
    E += RC('recv_lower', 0.038, (-0.198, 0.025), (0.063, 0.113), 0.28, top=False)
    for i, y in enumerate((-0.170, -0.040)):
        E.append(R(f'pin_{i}', (0.038, 0.041), (y, y + 0.008), (0.080, 0.088)))
    E.append(R('magwell', 0.036, (-0.122, -0.003), (0.042, 0.063)))
    E.append(R('guard_bar', 0.010, (-0.118, -0.048), (0.030, 0.040)))
    E.append(R('guard_front', 0.010, (-0.122, -0.110), (0.030, 0.063)))
    E.append(R('trigger', 0.004, (-0.072, -0.064), (0.040, 0.063)))
    g0 = M.m(0, -0.008, 0.059); g1 = M.m(0, 0.035, -0.047)
    E.append(post('grip', 8 - 0.026 * S, 8 + 0.026 * S, (g0[2], g0[1]), (g1[2], g1[1]), 0.046 * S, ext=(0.15, 0)))
    E.append(box('grip_heel', (8 - 0.028 * S, g1[1] - 0.15, g1[2] - 0.55), (8 + 0.028 * S, g1[1] + 0.25, g1[2] + 0.45)))
    E.append(R('grip_root', 0.030, (-0.030, 0.022), (0.042, 0.063)))
    # side optic on +X over the base sight line
    cx, cy = SIGHT
    z0, z1 = M.m(0, -0.165, 0)[2], M.m(0, -0.070, 0)[2]
    E.append(box('opt_mount', (8 + 0.037 * S, cy - 0.62, M.m(0, -0.150, 0)[2]), (cx - 0.55, cy - 0.2, M.m(0, -0.085, 0)[2])))
    E.append(box('opt_top', (cx - 0.55, cy + 0.38, z0), (cx + 0.55, cy + 0.62, z1)))
    E.append(box('opt_bot', (cx - 0.55, cy - 0.62, z0), (cx + 0.55, cy - 0.38, z1)))
    E.append(box('opt_out', (cx + 0.38, cy - 0.38, z0), (cx + 0.55, cy + 0.38, z1)))
    E.append(box('opt_in', (cx - 0.55, cy - 0.38, z0), (cx - 0.38, cy + 0.38, z1)))
    E.append(box('opt_pin', (cx - 0.04, cy - 0.38, (z0 + z1) / 2 - 0.06), (cx + 0.04, cy - 0.07, (z0 + z1) / 2 + 0.06)))
    for k, (a0, a1, b0, b1) in {'t': (cx - 0.66, cx + 0.66, cy + 0.32, cy + 0.44), 'l': (cx - 0.66, cx - 0.32, cy - 0.32, cy + 0.32),
                                'r': (cx + 0.32, cx + 0.66, cy - 0.32, cy + 0.32), 'b': (cx - 0.66, cx + 0.66, cy - 0.44, cy - 0.32)}.items():
        E.append(box(f'opt_lip_{k}', (a0, b0, z0 - 0.16), (a1, b1, z0)))
    # ---- rear: grey collar, orange tube, top rail + carry hoop, end cap
    E += RC('collar', 0.040, (0.097, 0.116), (0.134, 0.214), 0.36)
    E += RC('rear_tube', 0.034, (0.116, 0.519), (0.138, 0.209), 0.32)
    E += RC('end_lip', 0.031, (0.519, 0.525), (0.141, 0.206), 0.28)
    E.append(R('rear_rail', 0.012, (0.122, 0.515), (0.209, 0.219)))
    E.append(R('hoop_top', 0.006, (0.418, 0.505), (0.236, 0.244)))
    E.append(R('hoop_leg_a', 0.006, (0.410, 0.420), (0.219, 0.244)))
    E.append(R('hoop_leg_b', 0.006, (0.503, 0.513), (0.219, 0.244)))
    E.append(R('ammo_box', 0.036, (0.198, 0.244), (0.140, 0.162)))
    # ---- magazine: base reload rocket envelope
    E.append(box('mag_core', (7.55, 11.25, 12.0), (8.45, 12.15, 17.5)))
    E.append(box('mag_core45', (7.55, 11.25, 12.0), (8.45, 12.15, 17.5), rot={'origin': [8, 11.7, 14.75], 'z': 45}))
    E.append(box('mag_nose', (7.7, 11.4, 10.7), (8.3, 12.0, 12.1)))
    E.append(box('mag_collar', (7.5, 11.2, 16.9), (8.5, 12.2, 17.5)))
    E.append(box('mag_fin_v', (7.92, 10.95, 16.0), (8.08, 12.45, 17.3)))
    E.append(box('mag_fin_h', (7.25, 11.62, 16.0), (8.75, 11.78, 17.3)))
    return E


def model2world(name, p):
    if name.startswith('opt_'):
        return OPTF(p, dy=OPT_D[1])
    return M.w(p)


ROCKET = {'core': (206, 96, 60), 'core45': (206, 96, 60), 'nose': (214, 206, 176), 'collar': (60, 58, 56),
          'fin_v': (52, 50, 48), 'fin_h': (52, 50, 48)}


def special(e, fn, s, t):
    n = e['name']
    if n.startswith('mag_'):
        c = ROCKET[n[4:]]
        if n in ('mag_core', 'mag_core45') and fn in ('east', 'west', 'up', 'down') and s > 0.9:
            return (214, 206, 176, 255)
        return c + (255,)
    if n == 'muzzle_cap' and fn == 'north':
        w, h = 0.080 * S, 0.083 * S
        if disc(s, t, w / 2, h / 2, w, h, 0.72): return (16, 16, 18, 255)
        if disc(s, t, w / 2, h / 2, w, h, 0.88): return (150, 146, 128, 255)
    if n == 'rear_tube' and fn == 'south':
        w, h = 0.068 * S, 0.071 * S
        if disc(s, t, w / 2, h / 2, w, h, 0.6): return (20, 20, 22, 255)
    if n.startswith('opt_lip'): return (40, 40, 42, 255) if fn == 'north' else (184, 184, 178, 255)
    if n.startswith('pin_'): return (150, 150, 146, 255) if fn in ('east', 'west') else (60, 60, 60, 255)
    if n.startswith('fgrip_rib'): return rgbn((44, 40, 36), s, t, 3)
    if (n.startswith('muzzle_lip') and fn == 'north') or (n.startswith('end_lip') and fn == 'south'):
        x, y, z = face_xyz(e, fn, s, t); r = max(abs(x - 8), abs(y - M.m(0, 0, 0.1735)[1]))
        if r < 0.58: return (14, 14, 16, 255)
        if r < 0.68: return (70, 70, 70, 255)
        return (204, 200, 186, 255) if n.startswith('muzzle') else (204, 92, 58, 255)
    if n.startswith('opt_') and n not in ('opt_pin', 'opt_mount'):
        inner = {'opt_top': 'down', 'opt_bot': 'up', 'opt_out': 'west', 'opt_in': 'east'}[n]
        if fn == inner: return (30, 30, 32, 255)
        if fn in ('north', 'south'): return (184, 184, 178, 255)
    if n == 'opt_pin': return (214, 150, 40, 255)
    return flat(n, e, fn, s, t)


def flat(n, e, fn, s, t):
    best = None
    for k in COL:
        if n.startswith(k) and (best is None or len(k) > len(best)): best = k
    if best is None: return None
    c = COL[best]
    if callable(c): return c(e, fn, s, t)
    return tuple(c) + (255,)


def _cream(e, fn, s, t):
    x, y, z = face_xyz(e, fn, s, t)
    if fn in ('east', 'west') and M.m(0, -0.492, 0)[2] < z < M.m(0, -0.198, 0)[2] and M.m(0, 0, 0.146)[1] < y < M.m(0, 0, 0.168)[1]:
        # zig-zag brace of the side cage painted as a 1-texel dark line
        u = (z - M.m(0, -0.492, 0)[2]) / 2.4; f = abs((u % 2) - 1)
        yy = M.m(0, 0, 0.146)[1] + f * (M.m(0, 0, 0.168)[1] - M.m(0, 0, 0.146)[1])
        if abs(y - yy) < 0.07: return (120, 118, 104, 255)
    return (216, 212, 184, 255)


def _orange(e, fn, s, t):
    x, y, z = face_xyz(e, fn, s, t)
    if fn in ('east', 'west'):
        zz = (z - M.m(0, 0.130, 0)[2]) % 2.2; yy = y - M.m(0, 0, 0.1735)[1]
        if 0.25 < zz < 1.95 and 0.12 < abs(yy) < 0.62 and (abs(zz - 0.25) < 0.08 or abs(zz - 1.95) < 0.08 or abs(abs(yy) - 0.62) < 0.08):
            return (162, 70, 44, 255)  # recessed panel outlines
        if abs(yy - 0.28) < 0.1 and M.m(0, 0.140, 0)[2] < z < M.m(0, 0.175, 0)[2]: return (236, 232, 222, 255)  # HAKKE
    return (212, 98, 62, 255)


def _recv(e, fn, s, t):
    return _cream(e, fn, s, t)


COL = {'muzzle_cap': (226, 224, 214), 'muzzle_lip': (226, 224, 214), 'tube_front': _cream, 'top_strip': (200, 200, 194),
       'top_shroud': (62, 60, 56), 'cage': (204, 204, 200), 'under_rail': (196, 196, 192), 'fgrip': (60, 46, 38),
       'fgrip_rib': (48, 36, 30), 'fgrip_mount': (70, 60, 52), 'recv_upper': _recv, 'recv_window': (40, 40, 40),
       'top_fin': (212, 98, 62), 'top_fin_base': (200, 200, 194), 'top_rail': (196, 196, 192), 'recv_band': (206, 208, 206),
       'band_tail': (196, 196, 192), 'rear_lug': (40, 40, 40), 'recv_lower': (78, 58, 46), 'pin': (150, 140, 130),
       'magwell': (70, 52, 42), 'guard': (64, 48, 40), 'trigger': (50, 40, 34), 'grip': (60, 46, 38),
       'collar': (190, 190, 186), 'rear_tube': _orange, 'end_lip': (212, 98, 62), 'rear_rail': (196, 196, 192),
       'hoop': (196, 196, 192), 'ammo_box': (228, 226, 220), 'opt_mount': (60, 60, 60), 'opt_': (184, 184, 178)}


# Identity pass: direct face paint with crisp material edges and source-specific markings.
from identity import install
install(globals(), 'weaver_c')

# Material pass supersedes all-face flat paint; geometry retained.
from materials import install as install_materials
install_materials(globals(), 'weaver_c')
