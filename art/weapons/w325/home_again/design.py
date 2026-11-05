"""W325 Home Again (Red War uncommon, rapid-fire auto rifle) over steelfeather_repeater (layout contract:
weapon_reload_w213_steelfeather_repeater + weapon_sight_w151).

Identity kept: olive receiver with the framed magwell plate and ejection port, curved black magazine with the rubber
floor bulge, worn dark handguard (two oval slots + under-rail teeth, projected) with the curved belly, thin barrel with
sleeve and slotted brake, small hooded red-dot, brown wrapped pistol grip, skeleton stock with two real windows,
centre post, diagonal lower bar and flared butt pad.
Rip -> model: one uniform 24 px/m map (the rip already matches the base proportions): rip magazine centre -> z 3.3,
red-dot reticle centre -> eye line y 12.95.
Detail pass: chamfered handguard/receiver/stock/grip, octagonal barrel parts, slotted brake, framed magwell plate,
flat paint on the smeared small metal parts; the red-dot is a hollow 'sight_*' frame around the aim line (allowed
above the base top by the ADS rule).
"""
S = 24.0
ZM, YM = 3.3, -0.185
YE, ZE = 12.95, 0.182


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / S, YM + (z - ZM) / S, ZE + (y - YE) / S)


def is_magazine(n): return n.startswith('mag_')


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_m2tools'))
from solid import B, bar, vbar, octo, Flat, clean


def elements():
    E = []; a = E.append
    # ---- slotted brake (octagonal, real side slots), sleeve, barrel
    for e in octo('brake', 8, 11.16, .3, -8.85, -7.6): a(e)
    a(B('brake_bore', (7.88, 11.04, -8.87), (8.12, 11.28, -8.85)))
    for e in octo('brake_ring', 8, 11.16, .34, -7.75, -7.55): a(e)
    for e in octo('sleeve', 8, 11.2, .26, -7.6, -6.55): a(e)
    for e in octo('barrel', 8, 11.21, .17, -6.55, -5.3): a(e)
    # ---- handguard: chamfered main body, slanted nose, under-rail teeth, curved belly
    for e in bar('hg_main', 7.3, 8.7, 10.58, 12.2, -5.3, 1.9, c=.24, at=[-1.6]): a(e)
    a(B('hg_nose', (7.34, 10.5, -5.62), (8.66, 11.96, -5.3)))
    a(B('hg_nose_cap', (7.54, 11.96, -5.5), (8.46, 12.16, -5.3)))
    for i in range(6):
        z = -5.05 + i * .46
        a(B(f'hg_tooth_{i}', (7.48, 10.26, z), (8.52, 10.58, z + .26)))
    for e in bar('hg_belly', 7.32, 8.68, 9.78, 10.58, -1.3, 1.9, c=.2, top=False, bottom=True): a(e)
    a(B('hg_belly_step_0', (7.34, 10.3, -2.6), (8.66, 10.58, -1.95)))
    a(B('hg_belly_step_1', (7.34, 10.02, -1.95), (8.66, 10.58, -1.3)))
    a(B('hg_rear_band', (7.26, 10.54, 1.6), (8.74, 12.24, 1.9)))
    # ---- receiver: chamfered upper, lower, magwell plate frame, end plate, port lip, lever, bolt
    for e in bar('rcv_upper', 7.3, 8.7, 11.35, 12.45, 0.35, 8.1, c=.22, at=[2.3, 5.2]): a(e)
    a(B('rcv_lower', (7.3, 10.88, 1.9), (8.7, 11.35, 5.1)))
    a(B('rcv_lower_aft', (7.3, 10.88, 5.16), (8.7, 11.35, 8.1)))
    a(B('rcv_well', (7.32, 8.85, 2.3), (8.68, 10.9, 5.1)))
    for s, (x0, x1) in (('l', (7.24, 7.32)), ('r', (8.68, 8.76))):
        a(B(f'well_frame_{s}_top', (x0, 10.62, 2.4), (x1, 10.78, 5.0)))
        a(B(f'well_frame_{s}_bot', (x0, 9.0, 2.4), (x1, 9.16, 5.0)))
        a(B(f'well_frame_{s}_front', (x0, 9.16, 2.4), (x1, 10.62, 2.56)))
        a(B(f'well_frame_{s}_rear', (x0, 9.16, 4.84), (x1, 10.62, 5.0)))
    a(B('well_lip', (7.38, 8.72, 2.35), (8.62, 8.86, 5.05)))
    a(B('rcv_trigger_box', (7.4, 10.45, 5.1), (8.6, 10.9, 8.1)))
    for e in vbar('rcv_endplate', 7.38, 8.62, 9.6, 12.2, 7.95, 8.4, c=.14, front=False): a(e)
    a(B('rcv_port_lip', (8.7, 11.25, 1.95), (8.8, 11.95, 4.7)))
    a(B('rcv_port', (8.7, 11.42, 2.25), (8.74, 11.78, 4.35)))
    a(B('bolt_handle', (8.7, 11.45, 4.45), (9.05, 11.72, 4.7)))
    a(B('lever_arm', (6.95, 9.68, 3.95), (7.3, 9.95, 5.0)))
    a(B('lever_ring', (7.0, 9.6, 4.95), (7.3, 10.05, 5.45)))
    a(B('pin_x', (7.24, 11.62, 6.6), (8.76, 11.86, 6.84)))
    # ---- trigger guard + trigger (real opening)
    a(B('guard_bottom', (7.88, 9.38, 5.4), (8.12, 9.54, 6.92)))
    a(B('guard_front', (7.88, 9.38, 5.35), (8.12, 10.45, 5.52)))
    a(B('guard_rear', (7.88, 9.38, 6.78), (8.12, 10.45, 6.94), ('x', 18), (8, 10.45, 6.86)))
    a(B('trigger', (7.93, 9.7, 6.22), (8.07, 10.45, 6.38), ('x', 14), (8, 10.45, 6.3)))
    # ---- grip (brown wrap, raked, chamfered), heel, wrap bands
    a(B('grip', (7.4, 7.35, 7.0), (8.6, 10.5, 8.35), ('x', -13), (8, 10.5, 7.65)))
    for s_, (x0, x1) in (('l', (7.36, 7.4)), ('r', (8.6, 8.64))):
        a(B(f'grip_wrap_{s_}', (x0, 7.8, 7.15), (x1, 10.0, 8.2), ('x', -13), (8, 10.5, 7.65)))
    a(B('grip_heel', (7.42, 7.3, 8.3), (8.58, 7.75, 9.0), ('x', -13), (8, 10.5, 7.65)))
    a(B('grip_cap', (7.44, 7.05, 6.95), (8.56, 7.4, 8.45), ('x', -13), (8, 10.5, 7.65)))
    # ---- red-dot (hollow frame around the aim line: all 'sight_*', window x 7.62..8.38 / y 12.75..13.15)
    a(B('sight_base', (7.6, 12.45, 2.4), (8.4, 12.75, 5.15)))
    for s, (x0, x1) in (('l', (7.44, 7.62)), ('r', (8.38, 8.56))):
        a(B(f'sight_cheek_{s}', (x0, 12.6, 2.75), (x1, 13.2, 3.75)))
        a(B(f'sight_screw_{s}', (x0 - .06 if s == 'l' else x1, 12.85, 3.1), (x0 if s == 'l' else x1 + .06, 13.05, 3.3)))
    a(B('sight_hood', (7.44, 13.15, 2.7), (8.56, 13.32, 3.75)))
    a(B('sight_hood_lip', (7.5, 13.05, 2.55), (8.5, 13.3, 2.95), ('x', -35), (8, 13.3, 2.95)))
    a(B('sight_rear', (7.62, 12.75, 4.75), (8.38, 12.84, 5.2)))
    # ---- skeleton stock (two real windows), chamfered bars, pad
    for e in bar('st_top', 7.45, 8.55, 10.97, 11.67, 8.35, 14.25, c=.18, top=True, bottom=True, at=[11.35]): a(e)
    a(B('st_lower', (7.45, 8.35, 8.5), (8.55, 9.0, 14.3), ('x', 7), (8, 9.0, 8.5)))
    for e in vbar('st_post_mid', 7.45, 8.55, 8.55, 10.97, 11.35, 12.0, c=.15): a(e)
    a(B('st_knob', (7.36, 9.75, 11.3), (8.64, 10.02, 12.05)))
    a(B('st_rear_plate', (7.45, 8.0, 12.0), (8.55, 9.48, 13.6)))
    a(B('st_post_rear', (7.45, 7.85, 13.55), (8.55, 10.97, 14.25)))
    for e in vbar('st_pad', 7.36, 8.64, 7.6, 11.67, 14.2, 14.6, c=.12, front=False): a(e)
    a(B('st_pad_toe', (7.38, 7.6, 14.6), (8.62, 8.9, 14.9)))
    # ---- magazine (curved forward): neck in the well, ribbed body, rubber floor bulge
    a(B('mag_neck', (7.5, 8.8, 2.45), (8.5, 9.9, 4.7)))
    M = (('x', 10), (8, 8.95, 3.45))          # one rigid curved-forward magazine: shared pivot, flush faces
    a(B('mag_body', (7.56, 7.6, 2.2), (8.44, 8.95, 4.7), *M))
    a(B('mag_rib', (7.52, 7.75, 3.1), (8.48, 8.85, 3.3), *M))
    a(B('mag_floor', (7.42, 6.35, 2.1), (8.58, 7.6, 4.8), *M))
    return clean(E)


_flat = Flat([
    (lambda n, f: n.startswith(('brake', 'sleeve', 'barrel', 'bolt_')) and n != 'brake_bore', (86, 86, 86)),
    (lambda n, f: n == 'brake_bore' or n.startswith(('brake_slot', 'rcv_port')) and n != 'rcv_port_lip', (30, 31, 32)),
    (lambda n, f: n.startswith('well_frame') or n.startswith('lever_'), (158, 158, 146)),
    (lambda n, f: n.startswith('pin_'), (96, 96, 92)),
    (lambda n, f: n.startswith('hg_tooth'), (60, 60, 60)),
    (lambda n, f: '_joint_' in n, (40, 40, 40)),
    (lambda n, f: n in ('grip',) or n.startswith('grip_wrap'), (104, 62, 44)),
    (lambda n, f: n.startswith('mag_') and n != 'mag_floor', (46, 46, 47)),
    (lambda n, f: n == 'mag_floor', (64, 64, 63)),
    (lambda n, f: n.startswith('sight_') and n != 'sight_base', (52, 52, 54)),
    (lambda n, f: n.startswith(('st_', 'grip_heel', 'grip_cap')) and ('_ch_' in n or f in ('up', 'down')), (61, 61, 61)),
])


# ---- specials: the rip's oval handguard slots are through-holes (the projection sees background there and would be
# inpainted away); paint them as dark recesses on the handguard side faces.
_V = {}


def _view(name):
    if name not in _V:
        import json, sys
        from pathlib import Path
        here = Path(__file__).resolve().parent
        sys.path.insert(0, str(here.parents[3] / 'scripts/art/w325'))
        import kit
        man = json.loads((here / 'proj_cache/manifest.json').read_text())
        _V[name] = (kit, kit.View(here / 'proj_cache', name, man))
    return _V[name]


def special(e, fn, s, t):
    if e['name'] == 'brake' and fn in ('east', 'west') and .3 < t < .7:
        z = -8.85 + (s if fn == 'west' else 1 - s) * 1.25
        if -8.6 < z < -8.35 or -8.15 < z < -7.9:
            return (30, 31, 32, 255)
    f = _flat(e, fn, s, t)
    if f is not None:
        return f
    if not e['name'].startswith('hg_main') or '_ch_' in e['name'] or fn not in ('east', 'west'):
        return None
    kit, v = _view('nx' if fn == 'east' else 'px')
    p = kit.face_point(e, fn, s, t)
    if not (11.25 < p[1] < 11.95 and -4.8 < p[2] < -1.9):
        return None
    x, y = v.project(model2world(e['name'], p))
    if v.sample(x, y) is None:
        return (30, 31, 32, 255)
    return None

PALETTE = 16
FLAT_TOL = 30
PALETTE_KEEP = [(30, 31, 32), (158, 158, 146), (104, 62, 44)]

# W325 identity pass: every face is hand-painted at 20 texels/model px.
from identity import Painter
T = 20
ATLAS = 512
special = Painter('home', T)

from identity import geometry
_base_elements = elements
def elements(): return geometry(_base_elements(), 'home')

# W325 MATERIAL pass supersedes whole-face identity.Painter fills.
from materials import Materials, Decals
STYLE = "material"
material = Materials('home')
MATERIALS = material.palette
special = Decals('home', model2world, 'home_again', T)
