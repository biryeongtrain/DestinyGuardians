"""W325 Cup-Bearer SA/2 (rare rocket launcher, Adaptive) over base bellowing_giant (W187/W218 body + rocket magazine).

Rip (muzzle at rip -y, up +z) placed at a uniform 22.7 px/m: trigger (rip y -0.04, z 0.045) -> model z 6.3, y 9.2.
That puts the launch-tube axis at y 12.04 (base 11.9), muzzle cage front z -2.66, rear tube end z 24.1
(base -5.55..21.45) and the thumbhole lower/grip bottom at y 7.0 (base pistol heel 7.07).
Proper rotation (model X = -rip x, decals not mirrored); the rip's side optic (rip +x) is mirrored onto +X where the base sight is.
Deliberate fits: side optic moved (-0.33 x, -1.0 y) so its open aperture is centred on the base sight line
(9.55, 12.05) with a pin below centre; foregrip pivoted from ~47 to 25 deg rake and moved +0.6 z toward the
base support-hand position (z 2.2).  Magazine = base reload rocket envelope (z -2.4..3.2), hand painted.
"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_m10'))
from m10 import RipMap, PwMap, camo, seg, rc, box, bar, post, rot_zy, disc, side_part, cbox, tube8, face_xyz, rgbn

S = 22.7
M = RipMap(S, (-0.04, 0.045), (6.8, 9.2), along='y', up='z', muzzle='-')
# rear launch tube compressed behind rip y 0.10 so it ends at z ~15.7, before the 1P ADS camera (~z 18, beside x 8)
TM = PwMap(S, (-0.04, 0.045), (6.8, 9.2), along='y', up='z', muzzle='-', a_cut=0.10, k=0.40)
T = 20
FLAT_TOL = 34
PALETTE = 16
ATLAS = 1024

# optic: rip housing centre (x .083, z .215) -> moved onto the base sight line
OPT_D = (0.0, 12.10 - (9.2 + (0.215 - 0.045) * S))
OPTF = side_part(M, 9.55, 0.083)
# foregrip pivot (rip hinge y -0.257, z 0.037)
HINGE0 = M.m(0, -0.257, 0.037)                  # (X, Y, Z)
_low0 = M.m(0, -0.37, -0.082)
RAKE0 = math.degrees(math.atan2(-(_low0[2] - HINGE0[2]), HINGE0[1] - _low0[1]))  # forward rake from vertical
RAKE1 = 15.0
Y_LO = 9.2 + (0.117 - 0.045) * S                    # receiver floor (rip z 0.117)
DECK_Z0, DECK_Z1, TAIL_Z1 = 3.40, 7.7, 10.4
DECK_TOP, TAIL_TOP = 13.2, 13.04
FG_DZ = 0.3
HINGE1 = (HINGE0[0], HINGE0[1], HINGE0[2] + FG_DZ)
FG_LEN = math.hypot(_low0[2] - HINGE0[2], _low0[1] - HINGE0[1])


def rbm(name, xr, ar, hr, **kw): return M.rb(name, xr, ar, hr, **kw)


def elements():
    E = []
    tc = M.m(0, 0, 0.170)                                  # tube axis y
    ty = tc[1]
    # ---- launch tube (rear section, compressed): octagonal tube in three segments, bands, ribbed end cap
    r = 0.039 * S
    zs = [TM.m(0, y, 0)[2] for y in (0.10, 0.30, 0.50, 0.695)]
    for i in range(3):
        E += tube8(f'tube{i}', 8, ty, r, zs[i] + (0.08 if i else 0), zs[i + 1] - (0.08 if i < 2 else 0))
    for i, zc in enumerate(zs[1:3]):
        E += tube8(f'tube_band{i}', 8, ty, r + 0.08, zc - 0.18, zc + 0.18)
    E += tube8('tube_band2', 8, ty, r + 0.08, zs[0], zs[0] + 0.3)
    E += tube8('tube_cap', 8, ty, 0.0435 * S, zs[3], TM.m(0, 0.733, 0)[2])
    E += tube8('tube_capring', 8, ty, 0.0445 * S, zs[3] + 0.15, zs[3] + 0.35)
    # ---- front: octagonal shroud with bore, open cage + end frame
    E += tube8('shroud', 8, ty, 0.040 * S, M.m(0, -0.405, 0)[2], M.m(0, -0.20, 0)[2])
    for sx, xr in (('l', (-0.055, -0.040)), ('r', (0.040, 0.055))):
        E.append(rbm(f'rail_top_{sx}', xr, (-0.448, -0.23), (0.207, 0.222)))
        E.append(rbm(f'rail_bot_{sx}', xr, (-0.448, -0.23), (0.116, 0.131)))
        E.append(rbm(f'frame_post_{sx}', xr, (-0.454, -0.432), (0.116, 0.222)))
    E.append(rbm('frame_top', (-0.040, 0.040), (-0.454, -0.432), (0.207, 0.222)))
    E.append(rbm('frame_bot', (-0.040, 0.040), (-0.454, -0.432), (0.116, 0.131)))
    E.append(rbm('frame_mid', (-0.040, 0.040), (-0.33, -0.318), (0.219, 0.226)))
    # ---- upper receiver.  ADS: only the front block (z < 3.45, front third) may rise above the base roof (13.14);
    # the deck behind it is a squashed copy of the rip's tall receiver (top 13.2) and the tail sits at tube level.
    zf0, zf1 = M.m(0, -0.235, 0)[2], DECK_Z0
    X0, X1 = 8 - 0.054 * S, 8 + 0.054 * S
    # front third: low ramp + the rip's top bracket as a short rear hood (z < 3.4 so it may sit above the base roof)
    E.append(box('top_bracket', (8 - 0.4, DECK_TOP, zf0 + 0.1), (8 + 0.4, DECK_TOP + 0.55, zf0 + 0.35)))
    E.append(box('top_bracket_lip', (8 - 0.5, DECK_TOP + 0.55, zf0 - 0.15), (8 + 0.5, DECK_TOP + 0.7, zf0 + 0.45)))
    for sx, xr in (('l', (X0 - 0.12, X0)), ('r', (X1, X1 + 0.12))):
        E.append(box(f'red_lever_{sx}', (xr[0], DECK_TOP - 1.3, 2.75), (xr[1], DECK_TOP - 0.25, 3.15)))
    zf1 = zf0
    E += cbox('deck', (X0 + 0.1, Y_LO, zf1), (X1 - 0.1, DECK_TOP, DECK_Z1), 0.28)
    for sx, xr in (('l', (X0, X0 + 0.1)), ('r', (X1 - 0.1, X1))):
        E += seg(f'deck_side{sx}', (xr[0], Y_LO + 0.2, zf1 + 0.1), (xr[1], DECK_TOP - 0.3, DECK_Z1 - 0.1), [5.0, 6.4], groove=0.035)
    E.append(box('deck_vent', (8 - 0.45, DECK_TOP - 0.02, 4.4), (8 + 0.45, DECK_TOP + 0.04, 5.6)))
    for sx, xr in (('l', (X0 - 0.06, X0)), ('r', (X1, X1 + 0.06))):
        E.append(box(f'deck_panel_{sx}', (xr[0], Y_LO + 0.45, zf1 + 0.5), (xr[1], DECK_TOP - 0.45, DECK_Z1 - 0.6)))
    E += cbox('deck_tail', (X0 + 0.1, Y_LO, DECK_Z1), (X1 - 0.1, TAIL_TOP, TAIL_Z1), 0.25)
    # ---- side optic (+X), open aperture on the base sight line
    cx, cy = 9.55, 12.10
    z0, z1 = 4.0, 5.6
    E.append(box('opt_top', (8.95, cy + 0.42, z0), (10.27, cy + 1.02, z1)))
    E.append(box('opt_bot', (8.95, cy - 1.0, z0), (10.27, cy - 0.42, z1)))
    E.append(box('opt_out', (9.97, cy - 0.42, z0), (10.27, cy + 0.42, z1)))
    E.append(box('opt_in', (8.95, cy - 0.42, z0), (9.15, cy + 0.42, z1)))
    E.append(box('opt_pin', (9.51, cy - 0.42, (z0 + z1) / 2 - 0.06), (9.59, cy - 0.05, (z0 + z1) / 2 + 0.06)))
    E.append(box('opt_hood', (9.0, cy + 1.02, z0 + 0.2), (10.22, cy + 1.19, 5.3)))
    for k, (a0, a1, b0, b1) in {'t': (8.88, 10.34, cy + 0.36, cy + 0.48), 'b': (8.88, 10.34, cy - 0.48, cy - 0.36),
                                'l': (8.88, 9.21, cy - 0.36, cy + 0.36), 'r': (9.89, 10.34, cy - 0.36, cy + 0.36)}.items():
        E.append(box(f'opt_lip_{k}', (a0, b0, z0 - 0.18), (a1, b1, z0)))
    # ---- lower stock / thumbhole grip frame
    lb = M.rb('_', 0.049, (-0.30, 0.255), (0.062, 0.117))
    E += cbox('lower_beam', lb['from'], lb['to'], 0.22, top=False, bottom=True)
    for sx, xr in (('l', (lb['from'][0] - 0.05, lb['from'][0])), ('r', (lb['to'][0], lb['to'][0] + 0.05))):
        E += seg(f'lower_panel{sx}', (xr[0], lb['from'][1] + 0.25, lb['from'][2] + 0.4), (xr[1], lb['to'][1] - 0.2, lb['to'][2] - 0.6), [3.0, 6.0, 9.0], groove=0.03)
    E.append(rbm('lower_front', 0.049, (-0.288, -0.100), (0.020, 0.062)))
    q0 = M.m(0, -0.30, 0.062); q1 = M.m(0, -0.282, 0.020)
    E.append(box('lower_nose', (8 - 0.049 * S, q1[1], q0[2]), (8 + 0.049 * S, q0[1], q1[2])))
    # trigger guard loop (dark), ring trigger, raked pistol grip, closed thumbhole, rear stock block
    E.append(rbm('guard_bar', 0.030, (-0.105, -0.022), (0.020, 0.034)))
    E.append(rbm('grip_screw', (0.049, 0.053), (0.060, 0.072), (0.072, 0.084)))
    E.append(rbm('guard_front', 0.040, (-0.108, -0.094), (0.020, 0.064)))
    E.append(rbm('trigger', 0.008, (-0.062, -0.046), (0.034, 0.062)))
    g0 = M.m(0, -0.012, 0.064); g1 = M.m(0, 0.046, -0.036)
    E.append(post('grip', 8 - 0.046 * S, 8 + 0.046 * S, (g0[2], g0[1]), (g1[2], g1[1]), 0.034 * S, ext=(0, 0.1)))
    E.append(rbm('thumb_floor', 0.044, (0.030, 0.128), (-0.050, -0.030)))
    E.append(rbm('stock_post', 0.049, (0.118, 0.150), (-0.056, 0.064)))
    sb = M.rb('_', 0.049, (0.150, 0.262), (0.024, 0.064))
    E += cbox('stock_block', sb['from'], sb['to'], 0.2, top=False, bottom=True)
    E.append(rbm('butt_plate', 0.051, (0.255, 0.268), (-0.056, 0.117)))
    b0 = M.m(0, 0.150, -0.056); b1 = M.m(0, 0.262, 0.024)
    E.append(bar('stock_belly', 8 - 0.049 * S, 8 + 0.049 * S, (b0[2], b0[1]), (b1[2], b1[1]), 0.5, side='above', ext=(0, 0.02)))
    E.append(rbm('stock_fill', 0.049, (0.150, 0.200), (-0.030, 0.024)))
    # ---- foregrip (pivoted / moved, see doc)
    hz, hy = HINGE1[2], HINGE1[1]
    E.append(box('fg_hinge', (8 - 0.30, hy - 0.45, hz - 0.45), (8 + 0.30, hy + 0.65, hz + 0.45)))
    a = math.radians(RAKE1)
    lo = (hz - math.sin(a) * FG_LEN, hy - math.cos(a) * FG_LEN)
    mid = (hz - math.sin(a) * (FG_LEN - 0.35), hy - math.cos(a) * (FG_LEN - 0.35))
    E.append(post('fg_handle', 8 - 0.36, 8 + 0.36, (hz, hy), mid, 0.72))
    E.append(post('fg_cap', 8 - 0.32, 8 + 0.32, mid, lo, 0.66))
    mid2 = (hz - math.sin(a) * 0.55, hy - math.cos(a) * 0.55)
    E.append(post('fg_collar', 8 - 0.42, 8 + 0.42, (hz, hy), mid2, 0.84))
    # ---- magazine: base reload rocket envelope (fins toward the muzzle)
    E.append(box('mag_core', (7.65, 11.7, -1.8), (8.35, 12.4, 2.25)))
    E.append(box('mag_core45', (7.65, 11.7, -1.8), (8.35, 12.4, 2.25), rot={'origin': [8, 12.05, 0], 'z': 45}))
    E.append(box('mag_nose', (7.72, 11.77, 2.15), (8.28, 12.33, 2.85)))
    E.append(box('mag_tip', (7.84, 11.89, 2.8), (8.16, 12.21, 3.2)))
    E.append(box('mag_tail', (7.73, 11.78, -2.4), (8.27, 12.32, -1.65)))
    E.append(box('mag_fin_h', (7.46, 11.99, -2.3), (8.54, 12.11, -1.6)))
    E.append(box('mag_fin_v', (7.94, 11.51, -2.3), (8.06, 12.59, -1.6)))
    return E


def model2world(name, p):
    if name.startswith('tube'):
        return TM.w(p)
    if name.startswith('opt_'):
        return OPTF(p, dy=OPT_D[1])
    if name.startswith('fg_'):
        q = (p[0], p[1], p[2] - FG_DZ)
        q = rot_zy(q, (HINGE0[1], HINGE0[2]), RAKE0 - RAKE1)
        return M.w(q)
    if name.startswith('mag_'):
        return M.w((p[0], p[1], -2.5))     # (painted by special)
    if name.startswith('deck_front'):
        w = list(M.w(p)); w[2] = 0.117 + (p[1] - Y_LO) / (DECK_TOP - Y_LO) * (0.30 - 0.117); return tuple(w)
    if name.startswith('deck_side') or name == 'deck_vent':
        w = list(M.w(p)); w[2] = 0.117 + (p[1] - Y_LO) / (DECK_TOP - Y_LO) * (0.30 - 0.117); return tuple(w)
    if name.startswith('deck'):
        # squashed receiver: model y Y_LO..DECK_TOP samples rip z 0.117..0.30
        top = TAIL_TOP if name.startswith('deck_tail') else DECK_TOP
        rz_top = 0.24 if name.startswith('deck_tail') else 0.30
        w = M.w(p); w = list(w); w[2] = 0.117 + (p[1] - Y_LO) / (top - Y_LO) * (rz_top - 0.117); return tuple(w)
    if name.startswith('red_lever'):
        return M.w((p[0], p[1] + 1.7, p[2] + 0.55))
    if name.startswith('top_bracket'):
        return M.w((p[0], p[1] + 1.9, p[2] - 0.1))
    return M.w(p)


TY = 9.2 + (0.170 - 0.045) * S
CAMO_PARTS = {'butt', 'guard'} - {'guard'}

ROCKET = {'core': (96, 98, 78), 'core45': (96, 98, 78), 'nose': (214, 204, 186), 'tip': (176, 40, 34),
          'tail': (70, 70, 64), 'fin_h': (52, 52, 50), 'fin_v': (52, 52, 50)}


def special(e, fn, s, t):
    n = e['name']
    if n.startswith('mag_'):
        c = ROCKET[n[4:]]
        if n in ('mag_core', 'mag_core45') and fn in ('east', 'west', 'up', 'down'):
            # cream band behind the nose and a thin red stripe (rip rocket nose is cream with red marks)
            if s > 0.86: return (205, 196, 176, 255)
            if 0.80 < s <= 0.83: return (160, 38, 32, 255)
        return c + (255,)
    if (n.startswith('shroud') and fn == 'north') or (n.startswith('tube_cap') and fn == 'south'):
        x, y, z = face_xyz(e, fn, s, t); r = ((x - 8) ** 2 + (y - TY) ** 2) ** .5
        if r < 0.66: return (14, 14, 16, 255)
        if r < 0.78: return (64, 64, 58, 255)
        return rgbn((112, 110, 92), s, t)
    if n.startswith('tube_band'): return (82, 80, 68, 255)
    if n.startswith('tube_capring'): return (64, 62, 54, 255)
    if n.startswith('tube'): return (112, 110, 90, 255) if not n[4:5].isdigit() or fn not in ('up',) else (120, 118, 98, 255)
    if n == 'deck_vent': return (40, 40, 38, 255) if int(s * 8) % 2 else (70, 70, 64, 255)
    if n.split('_')[0] in CAMO_PARTS or n.startswith(('deck', 'lower', 'stock', 'thumb', 'top_bracket')):
        if n.startswith(('deck_side', 'lower_panel')) and '_g' in n: return (150, 138, 128, 255)
        c = camo(face_xyz(e, fn, s, t), cell=1.4, seed=3)
        return (226, 212, 198, 255) if c == 0 else (148, 164, 118, 255)
    if n == 'butt_plate' and fn == 'south': return rgbn((58, 56, 50), s, t)
    if n.startswith('opt_lip'): return rgbn((40, 40, 42), s, t, 3) if fn in ('north',) else (196, 196, 190, 255)
    if n.startswith('opt_') and n not in ('opt_hood', 'opt_pin'):
        inner = {'opt_top': 'down', 'opt_bot': 'up', 'opt_out': 'west', 'opt_in': 'east'}[n]
        if fn == inner: return (34, 34, 36, 255)
        if fn in ('north', 'south'): return (196, 196, 190, 255) if n != 'opt_in' else (60, 60, 58, 255)
    if n == 'opt_pin': return (170, 36, 30, 255)
    return None


# Identity pass: direct face paint with crisp material edges and source-specific markings.
from identity import install
install(globals(), 'cup_bearer_sa_2')

# Material pass supersedes all-face flat paint; geometry retained.
from materials import install as install_materials
install_materials(globals(), 'cup_bearer_sa_2')
