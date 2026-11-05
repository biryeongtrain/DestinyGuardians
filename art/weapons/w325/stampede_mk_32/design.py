"""W325 Stampede Mk.32 (rare grenade launcher, Rapid-Fire; no exact frame row) over base salvager_s_salvo
(W173/W220: moving `_barrel` leaf, static `_body` leaf, `_round` shell).

Rip (muzzle at rip -y, up +z) at a uniform 27.7 px/m proper rotation, scaled so both hands land on the base W201
contacts: pistol grip rip (y -0.015, z 0.027) -> model (z 8.24, y 8.18); the slanted front post of the trapezoid grip
loop (rip y ~-0.39) then sits at z ~-2.1 (base support hand -2.14).  Muzzle z -6.5 (base -7.83), butt z 16.4 (17.17).
A small front ring sight on a 1.1 px tower frames the base iron sight centre (8, 14.30, -2.1); ring textured from
the rip's white muzzle cap.  parts.magazine = moving front group (prefix brl_: shroud + grip loop + ring sight) for the
base `_barrel` leaf; parts.body = drum, receiver, thumbhole stock.  `_round` should keep the base shell art.
"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_m10'))
from m10 import RipMap, box, bar, post, disc, rc, face_xyz, camo

S = 27.7
M = RipMap(S, (-0.015, 0.027), (8.24, 8.18), along='y', up='z', muzzle='-')
T = 20
ATLAS = 1024
FLAT_TOL = 34
PALETTE = 16
SIGHT = (8.0, 14.30, -2.1)


def RC(name, hw, yr, zr, c=0.3, top=True, bottom=True, axis='z'): return rc(M, name, hw, yr, zr, c, top, bottom, axis)


def is_magazine(n): return n.startswith('brl_')


def R(name, hw, yr, zr, **kw): return M.rb(name, hw, yr, zr, **kw)


def elements():
    E = []
    # ---- moving front group: chamfered camo shroud with white top band + cap, vent block, grip loop, ring sight
    E += RC('brl_cap', 0.032, (-0.546, -0.528), (0.104, 0.180), 0.34)
    E += RC('brl_shroud', 0.031, (-0.528, -0.294), (0.107, 0.160), 0.26, top=False)
    E += RC('brl_band', 0.032, (-0.528, -0.294), (0.160, 0.180), 0.22, bottom=False)
    E.append(R('brl_vent', (-0.0325, 0.0325), (-0.420, -0.350), (0.122, 0.150)))
    E.append(R('brl_slot', (-0.0322, 0.0322), (-0.520, -0.440), (0.135, 0.140)))
    E += RC('brl_loop_top', 0.030, (-0.450, -0.294), (0.092, 0.107), 0.18, top=False)
    f0 = M.m(0, -0.437, 0.096); f1 = M.m(0, -0.362, -0.034)
    E.append(post('brl_loop_front', 8 - 0.028 * S, 8 + 0.028 * S, (f0[2], f0[1]), (f1[2], f1[1]), 0.026 * S, ext=(0, 0.1)))
    E.append(R('brl_loop_bot', 0.028, (-0.380, -0.294), (-0.040, -0.020)))
    E.append(R('brl_loop_rear', 0.030, (-0.315, -0.294), (-0.040, 0.092)))
    E.append(R('brl_loop_bolt', (0.028, 0.032), (-0.380, -0.370), (-0.036, -0.026)))
    cx, cy, cz = SIGHT
    E.append(box('brl_sight_base', (cx - 0.35, M.m(0, 0, 0.180)[1], cz - 0.4), (cx + 0.35, M.m(0, 0, 0.180)[1] + 0.2, cz + 0.4)))
    E.append(box('brl_sight_post', (cx - 0.2, M.m(0, 0, 0.180)[1] + 0.2, cz - 0.2), (cx + 0.2, cy - 0.58, cz + 0.2)))
    E.append(box('brl_sight_bot', (cx - 0.58, cy - 0.58, cz - 0.14), (cx + 0.58, cy - 0.34, cz + 0.14)))
    E.append(box('brl_sight_top', (cx - 0.58, cy + 0.34, cz - 0.14), (cx + 0.58, cy + 0.58, cz + 0.14)))
    E.append(box('brl_sight_l', (cx - 0.58, cy - 0.34, cz - 0.14), (cx - 0.34, cy + 0.34, cz + 0.14)))
    E.append(box('brl_sight_r', (cx + 0.34, cy - 0.34, cz - 0.14), (cx + 0.58, cy + 0.34, cz + 0.14)))
    # ---- drum cage: chamfered front post, drum box (cylinder ends + round visible), rear post, side lug
    E += RC('drum_post_f', 0.080, (-0.294, -0.244), (-0.034, 0.160), 0.4)
    E += RC('drum_box', 0.074, (-0.244, -0.104), (-0.027, 0.107), 0.4)
    for i, y in enumerate((-0.230, -0.190, -0.150)):
        E.append(R(f'drum_rib{i}', 0.0755, (y, y + 0.010), (-0.020, 0.100)))
    E.append(R('drum_window', (0.0745, 0.0760), (-0.210, -0.130), (0.050, 0.095)))
    E += RC('drum_post_r', 0.030, (-0.104, -0.087), (-0.044, 0.107), 0.2)
    E += RC('side_lug', (0.074, 0.121), (-0.205, -0.150), (0.070, 0.090), 0.18)
    E += RC('shroud_rear', 0.031, (-0.244, -0.087), (0.107, 0.160), 0.24, top=False)
    E += RC('band_rear', 0.032, (-0.244, -0.087), (0.160, 0.180), 0.22, bottom=False)
    E.append(R('front_post', 0.006, (-0.204, -0.189), (0.180, 0.196)))
    # ---- receiver: camo upper split into upper/lower panels, display window, top rail with teeth, sight block
    E += RC('recv_upper', 0.037, (-0.087, 0.241), (0.135, 0.1865), 0.3, bottom=False)
    E += RC('recv_mid', 0.035, (-0.087, 0.241), (0.0965, 0.135), 0.2, top=False)
    E.append(R('recv_seam', 0.0365, (-0.087, 0.241), (0.133, 0.137)))
    E.append(R('display', (-0.0375, 0.0375), (-0.050, 0.060), (0.112, 0.130)))
    E.append(R('recv_rail', 0.024, (-0.040, 0.222), (0.1865, 0.192)))
    for i in range(6):
        y = -0.030 + i * 0.040
        if -0.12 < y < 0.02: continue
        E.append(R(f'rail_tooth{i}', 0.025, (y, y + 0.014), (0.192, 0.196)))
    E += RC('sight_block', 0.020, (-0.116, 0.011), (0.180, 0.206), 0.16, bottom=False)
    # ---- lower: guard, trigger, raked grip, thumbhole stock (frame pieces), butt pad
    E.append(R('guard_bar', 0.034, (-0.087, 0.020), (-0.044, -0.024)))
    E.append(R('trigger', 0.006, (-0.060, -0.040), (0.047, 0.0965)))
    g0 = M.m(0, -0.035, 0.0965); g1 = M.m(0, 0.005, -0.030)
    E.append(post('grip', 8 - 0.036 * S, 8 + 0.036 * S, (g0[2], g0[1]), (g1[2], g1[1]), 0.042 * S, ext=(0, 0)))
    E += RC('stock_low', 0.038, (0.005, 0.240), (-0.010, 0.0415), 0.3, top=False)
    b0 = M.m(0, 0.010, -0.040); b1 = M.m(0, 0.240, 0.000)
    # belly as two axis-aligned steps (shared planes) instead of a shallow rotated slab
    E.append(box('stock_belly0', (8 - 0.038 * S, b0[1], b0[2]), (8 + 0.038 * S, M.m(0, 0, -0.010)[1], M.m(0, 0.120, 0)[2])))
    E.append(box('stock_belly1', (8 - 0.038 * S, M.m(0, 0, -0.022)[1], M.m(0, 0.120, 0)[2]), (8 + 0.038 * S, M.m(0, 0, -0.010)[1], b1[2])))
    E += RC('stock_web', 0.038, (0.086, 0.240), (0.0415, 0.0965), 0.2, bottom=False)
    for i, y in enumerate((0.150, 0.172)):
        E.append(R(f'stock_cut{i}', (0.0375, 0.0385), (y, y + 0.016), (0.010, 0.030)))
    E += RC('butt_pad', 0.030, (0.240, 0.262), (0.000, 0.180), 0.26)
    E += RC('butt_rubber', 0.026, (0.262, 0.278), (0.004, 0.176), 0.24)
    return E


def model2world(name, p):
    if name.startswith('brl_sight'):
        # ring textured from the white muzzle cap
        dz = M.m(0, -0.536, 0)[2] - SIGHT[2]; dy = M.m(0, 0, 0.140)[1] - SIGHT[1]
        return M.w((p[0], p[1] + dy, p[2] + dz))
    return M.w(p)


COL = {'brl_cap': (220, 216, 204), 'brl_band': (220, 216, 204), 'band_rear': (220, 216, 204), 'brl_vent': (40, 44, 38),
       'brl_slot': (30, 32, 30), 'brl_loop': (58, 62, 56), 'brl_sight': (220, 216, 204), 'drum_post': (52, 52, 48),
       'drum_box': (64, 64, 58), 'drum_rib': (48, 48, 44), 'drum_window': (26, 26, 26), 'side_lug': (52, 52, 48),
       'front_post': (52, 52, 48), 'recv_seam': (34, 44, 28), 'display': (30, 40, 44), 'recv_rail': (60, 64, 56),
       'rail_tooth': (46, 50, 44), 'sight_block': (220, 216, 204), 'guard': (58, 62, 56), 'trigger': (220, 216, 204),
       'grip': (58, 62, 56), 'stock': (66, 70, 62), 'stock_cut': (30, 32, 30), 'butt_pad': (220, 216, 204), 'butt_rubber': (30, 30, 30)}
CAMO = ('brl_shroud', 'shroud_rear', 'recv_upper', 'recv_mid')


def special(e, fn, s, t):
    n = e['name']
    if n.startswith('brl_cap') and fn == 'north':
        x, y, z = face_xyz(e, fn, s, t)
        if (x - 8) ** 2 + (y - M.m(0, 0, 0.140)[1]) ** 2 < 0.62 ** 2: return (12, 12, 14, 255)
    if n.startswith('brl_sight_') and n not in ('brl_sight_post', 'brl_sight_base'):
        inner = {'brl_sight_bot': 'up', 'brl_sight_top': 'down', 'brl_sight_l': 'east', 'brl_sight_r': 'west'}[n]
        if fn == inner: return (34, 36, 34, 255)
    if n == 'display' and fn in ('east', 'west'):
        x, y, z = face_xyz(e, fn, s, t); u = (z - M.m(0, -0.050, 0)[2]) / (M.m(0, 0.060, 0)[2] - M.m(0, -0.050, 0)[2])
        if 0.3 < u < 0.45 or 0.55 < u < 0.7: return (60, 140, 220, 255)
        if 0.78 < u < 0.9: return (200, 200, 196, 255)
    if n == 'brl_vent' and fn in ('east', 'west'):
        x, y, z = face_xyz(e, fn, s, t)
        return (24, 26, 24, 255) if int(z * 3.0) % 2 else (64, 70, 56, 255)
    if n.startswith(CAMO):
        c = camo(face_xyz(e, fn, s, t), cell=1.5, seed=7, levels=(0.45, 0.68))
        return ((86, 104, 58), (62, 80, 44), (128, 140, 92))[c] + (255,)
    best = None
    for k in COL:
        if n.startswith(k) and (best is None or len(k) > len(best)): best = k
    return COL[best] + (255,) if best else None


# Identity pass: direct face paint with crisp material edges and source-specific markings.
from identity import install
install(globals(), 'stampede_mk_32')

# Material pass supersedes all-face flat paint; geometry retained.
from materials import install as install_materials
install_materials(globals(), 'stampede_mk_32')
