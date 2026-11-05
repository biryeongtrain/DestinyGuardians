"""W325 Reginar-B (rare rocket launcher, Precision) over base pyroclastic_flow (W221 body + rear-loaded rocket).

Rip (muzzle at rip -y, up +z) at a uniform 24 px/m, anchored on the W201 hand contacts of the base: pistol-grip middle
(rip y 0.012, z 0.006) -> model (z 14.53, y 7.7); the vertical foregrip then lands at z ~8.1, y ~8.8 (base support
hand 7.5 / 9.38).  Because Reginar's grips sit near its front while Pyroclastic Flow is a rear-gripped launcher, the
whole tube spans z 0.7..27.1 (base -7.8..19.2): ~8 px less ahead of the hands, ~8 px more behind the shoulder.
Tube axis y 11.71 (base 11.9).  Proper rotation (model X = -rip x, decals not mirrored); side optic (rip +x, model -X) mirrored onto +X and moved +0.55 x / +1.05 y so its open aperture is centred on the
base ADS sight (10.132, 12.69, eye +z) with an amber pin below centre.  Magazine = base reload rocket envelope
(z 10.7..17.5, rear-loaded), hand painted.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_m10'))
from m10 import RipMap, PwMap, box, bar, post, disc, side_part, rc, cbox, rgbn, face_xyz

S = 24.0
M = PwMap(S, (0.012, 0.006), (14.53, 7.7), along='y', up='z', muzzle='-', a_cut=0.107, k=0.50)
T = 20
ATLAS = 1024
FLAT_TOL = 34
PALETTE = 16
SIGHT = (10.132, 12.69)
OPT_RIP = (0.066, 0.170)
OPT_D = (0.0, SIGHT[1] - M.m(0, 0, OPT_RIP[1])[1])
OPTF = side_part(M, SIGHT[0], OPT_RIP[0])


def R(name, hw, yr, zr, **kw): return M.rb(name, hw, yr, zr, **kw)


def RC(name, hw, yr, zr, c=0.32, top=True, bottom=True, axis='z'): return rc(M, name, hw, yr, zr, c, top, bottom, axis)


def elements():
    E = []
    # ---- front tube, muzzle cap, band, front housing, carry handle
    E += RC('muzzle_cap', 0.047, (-0.565, -0.548), (0.127, 0.219), 0.4)
    E += RC('muzzle_lip', 0.042, (-0.571, -0.565), (0.132, 0.214), 0.36)
    E += RC('tube_front', 0.040, (-0.548, -0.318), (0.134, 0.209), 0.36)
    E += RC('tube_band', 0.044, (-0.392, -0.379), (0.131, 0.213), 0.4)
    E += RC('front_housing', 0.056, (-0.318, -0.186), (0.134, 0.214), 0.4)
    for sx, xr in (('l', (-0.059, -0.056)), ('r', (0.056, 0.059))):
        E.append(R(f'housing_panel_{sx}', xr, (-0.305, -0.200), (0.146, 0.202)))
    E.append(R('handle_top', 0.009, (-0.272, -0.058), (0.236, 0.249)))
    for tag, (ya, yb) in (('a', (-0.292, -0.272)), ('b', (-0.058, -0.036))):
        E.append(R(f'handle_leg_{tag}', 0.008, (ya, yb), (0.212, 0.243)))
    # under rail + vertical foregrip
    E.append(R('under_rail', 0.034, (-0.477, -0.186), (0.103, 0.134)))
    E.append(R('fgrip_mount', 0.022, (-0.290, -0.222), (0.096, 0.112)))
    E += RC('fgrip', 0.017, (-0.284, -0.228), (-0.004, 0.100), 0.22, axis='y')
    for i in range(3):
        z = 0.012 + i * 0.026
        E.append(R(f'fgrip_rib_{i}', 0.0185, (-0.286, -0.226), (z, z + 0.006)))
    E.append(R('fgrip_cap', 0.013, (-0.280, -0.234), (-0.018, -0.004)))
    # ---- receiver: upper tube section, light band, dark lower with magwell + trigger
    E += RC('recv_upper', 0.041, (-0.186, 0.107), (0.140, 0.2125), 0.36, bottom=False)
    E.append(R('port_rim', (0.041, 0.044), (-0.092, -0.050), (0.158, 0.196)))
    E.append(R('recv_band', 0.042, (-0.186, 0.010), (0.1125, 0.140)))
    E += RC('recv_lower', 0.040, (-0.186, 0.014), (0.059, 0.1125), 0.28, top=False)
    for i, y in enumerate((-0.160, -0.030)):
        E.append(R(f'pin_{i}', (0.040, 0.043), (y, y + 0.008), (0.076, 0.084)))
    E.append(R('magwell', 0.038, (-0.112, -0.012), (0.042, 0.059)))
    E.append(R('guard_bar', 0.010, (-0.110, -0.040), (0.031, 0.040)))
    E.append(R('guard_front', 0.010, (-0.112, -0.102), (0.031, 0.059)))
    E.append(R('trigger', 0.004, (-0.070, -0.062), (0.040, 0.059)))
    g0 = M.m(0, -0.008, 0.059); g1 = M.m(0, 0.035, -0.047)
    E.append(post('grip', 8 - 0.026 * S, 8 + 0.026 * S, (g0[2], g0[1]), (g1[2], g1[1]), 0.046 * S, ext=(0.15, 0)))
    E.append(box('grip_heel', (8 - 0.028 * S, g1[1] - 0.15, g1[2] - 0.55), (8 + 0.028 * S, g1[1] + 0.25, g1[2] + 0.45)))
    E.append(R('grip_root', 0.030, (-0.030, 0.022), (0.042, 0.062)))
    # side optic (+x), moved onto the base sight line
    E.append(box('opt_mount', (8 + 0.040 * S, OPT_D[1] + M.m(0, 0, 0.152)[1], M.m(0, -0.150, 0)[2]),
                 (SIGHT[0] - 0.55, OPT_D[1] + M.m(0, 0, 0.170)[1], M.m(0, -0.080, 0)[2])))
    cx, cy = SIGHT
    z0, z1 = M.m(0, -0.160, 0)[2], M.m(0, -0.050, 0)[2]
    E.append(box('opt_top', (cx - 0.55, cy + 0.38, z0), (cx + 0.55, cy + 0.62, z1)))
    E.append(box('opt_bot', (cx - 0.55, cy - 0.62, z0), (cx + 0.55, cy - 0.38, z1)))
    E.append(box('opt_out', (cx + 0.38, cy - 0.38, z0), (cx + 0.55, cy + 0.38, z1)))
    E.append(box('opt_in', (cx - 0.55, cy - 0.38, z0), (cx - 0.38, cy + 0.38, z1)))
    E.append(box('opt_pin', (cx - 0.04, cy - 0.38, (z0 + z1) / 2 - 0.06), (cx + 0.04, cy - 0.07, (z0 + z1) / 2 + 0.06)))
    E.append(box('opt_eye_rim', (cx - 0.62, cy - 0.69, z1), (cx + 0.62, cy - 0.38, z1 + 0.35)))
    for k, (a0, a1, b0, b1) in {'t': (cx - 0.66, cx + 0.66, cy + 0.32, cy + 0.44), 'l': (cx - 0.66, cx - 0.32, cy - 0.32, cy + 0.32),
                                'r': (cx + 0.32, cx + 0.66, cy - 0.32, cy + 0.32)}.items():
        E.append(box(f'opt_lip_{k}', (a0, b0, z0 - 0.16), (a1, b1, z0)))
    # ---- rear: sloped grey rail, white collar block, olive tube with white rails/bands, end cap
    r0 = M.m(0, 0.014, 0.1125); r1 = M.m(0, 0.258, 0.134)
    E.append(R('rear_rail', 0.036, (0.010, 0.258), (0.112, 0.134)))
    E.append(R('rear_trig_lug', 0.006, (0.155, 0.165), (0.098, 0.112)))
    E += RC('collar', 0.044, (0.107, 0.164), (0.130, 0.214), 0.4)
    E += RC('rear_tube', 0.036, (0.164, 0.512), (0.134, 0.2125), 0.34)
    E.append(R('rail_top', 0.012, (0.130, 0.512), (0.2125, 0.219)))
    for i, yb in enumerate((0.287, 0.493)):
        E.append(R(f'rear_band_{i}', 0.040, (yb - 0.006, yb + 0.006), (0.128, 0.218)))
    E.append(R('rail_low_l', (-0.040, -0.034), (0.258, 0.512), (0.125, 0.134)))
    E.append(R('rail_low_r', (0.034, 0.040), (0.258, 0.512), (0.125, 0.134)))
    E += RC('end_cap', 0.038, (0.512, 0.533), (0.130, 0.216), 0.36)
    E += RC('end_lip', 0.034, (0.533, 0.538), (0.135, 0.211), 0.3)
    E.append(R('ammo_box', 0.030, (0.208, 0.258), (0.134, 0.152), ))
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


ROCKET = {'core': (88, 96, 52), 'core45': (88, 96, 52), 'nose': (190, 190, 182), 'collar': (60, 60, 58),
          'fin_v': (48, 48, 46), 'fin_h': (48, 48, 46)}


def special(e, fn, s, t):
    n = e['name']
    if n.startswith('mag_'):
        c = ROCKET[n[4:]]
        if n in ('mag_core', 'mag_core45') and fn in ('east', 'west', 'up', 'down') and s > 0.9:
            return (196, 196, 188, 255)
        return c + (255,)
    if (n.startswith('muzzle_lip') and fn == 'north') or (n.startswith('end_lip') and fn == 'south'):
        x, y, z = face_xyz(e, fn, s, t); r = max(abs(x - 8), abs(y - M.m(0, 0, 0.1715)[1]))
        if r < 0.62: return (14, 14, 16, 255)
        if r < 0.72: return (70, 70, 70, 255)
        return (196, 196, 192, 255) if n.startswith('muzzle') else (80, 86, 52, 255)
    if n == 'muzzle_cap' and fn == 'north':
        w, h = 0.094 * S, 0.092 * S
        if disc(s, t, w / 2, h / 2, w, h, 0.78): return (14, 14, 16, 255)
        if disc(s, t, w / 2, h / 2, w, h, 0.95): return (96, 96, 94, 255)
    if n == 'end_cap' and fn == 'south':
        w, h = 0.076 * S, 0.086 * S
        if disc(s, t, w / 2, h / 2, w, h, 0.62): return (16, 16, 18, 255)
    if n.startswith('opt_lip'): return (40, 40, 42, 255) if fn == 'north' else (176, 176, 172, 255)
    if n.startswith('pin_'): return (150, 150, 146, 255) if fn in ('east', 'west') else (60, 60, 60, 255)
    if n.startswith('fgrip_rib'): return rgbn((44, 44, 44), s, t, 3)
    if n.startswith('opt_') and n not in ('opt_pin', 'opt_mount'):
        if n == 'opt_eye_rim': return (40, 40, 42, 255)
        inner = {'opt_top': 'down', 'opt_bot': 'up', 'opt_out': 'west', 'opt_in': 'east'}[n]
        if fn == inner: return (30, 30, 32, 255)
        if fn in ('north', 'south'): return (176, 176, 172, 255)
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


def _tube(e, fn, s, t):
    x, y, z = face_xyz(e, fn, s, t)
    # data strip decal on the front tube sides, dark weld seams
    if fn in ('east', 'west') and abs(y - M.m(0, 0, 0.1715)[1]) < 0.28 and M.m(0, -0.520, 0)[2] < z < M.m(0, -0.440, 0)[2]:
        return (214, 214, 210, 255) if int(z * 5) % 3 else (40, 40, 40, 255)
    return (86, 84, 80, 255)


def _recv(e, fn, s, t):
    x, y, z = face_xyz(e, fn, s, t)
    if fn in ('east', 'west') and abs(y - M.m(0, 0, 0.176)[1]) < 0.3 and M.m(0, -0.092, 0)[2] < z < M.m(0, -0.050, 0)[2]:
        return (20, 20, 22, 255)      # ejection port
    return (80, 78, 74, 255)


def _rear(e, fn, s, t):
    x, y, z = face_xyz(e, fn, s, t)
    if fn in ('east', 'west') and abs(y - M.m(0, 0, 0.190)[1]) < 0.12 and M.m(0, 0.205, 0)[2] < z < M.m(0, 0.245, 0)[2]:
        return (176, 52, 40, 255)     # red HAKKE stamp as a flat bar
    return (88, 98, 52, 255)


COL = {'muzzle_cap': (214, 214, 210), 'muzzle_lip': (214, 214, 210), 'tube_front': _tube, 'tube_band': (214, 214, 210),
       'front_housing': (62, 60, 58), 'housing_panel': (70, 68, 64), 'handle_top': (40, 40, 40), 'handle_leg': (150, 146, 136),
       'under_rail': (176, 176, 172), 'fgrip': (46, 46, 46), 'fgrip_mount': (60, 60, 60), 'recv_upper': _recv,
       'port_rim': (60, 60, 58), 'recv_band': (206, 208, 208), 'recv_lower': (64, 60, 56), 'pin': (150, 150, 146),
       'magwell': (56, 54, 50), 'guard': (52, 50, 48), 'trigger': (40, 40, 40), 'grip': (50, 48, 46),
       'rear_rail': (190, 192, 192), 'rear_trig_lug': (40, 40, 40), 'collar': (226, 226, 222), 'rear_tube': _rear,
       'rail_top': (220, 220, 216), 'rear_band': (220, 220, 216), 'rail_low': (210, 210, 206), 'end_cap': (80, 88, 48),
       'end_lip': (80, 88, 48), 'ammo_box': (220, 220, 216), 'opt_mount': (60, 60, 60), 'opt_eye_rim': (40, 40, 42),
       'opt_': (176, 176, 172)}


# Identity pass: direct face paint with crisp material edges and source-specific markings.
from identity import install
install(globals(), 'reginar_b')

# Material pass supersedes all-face flat paint; geometry retained.
from materials import install as install_materials
install_materials(globals(), 'reginar_b')
