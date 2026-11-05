"""W325 Ros Lysis II (Red War rare, Adaptive auto rifle) over gnawing_hunger (layout contract:
weapon_reload_w208_gnawing_hunger + weapon_sight_w151, same base as W302 Khvostov).

Identity kept: frost blue-teal camo over a brown frame; hexagonal shroud with the stepped nose, top fin, dark vent
cover and three round drums per side; twin muzzle prongs and the under-barrel spike; ribbed lower block; light angled
fore plate; skeleton grip frame (front post + bottom bar) with raked grip; boxy Red Dot-OAS scope with a green ring
reticle; stock with dark top, light rail strip, brown lower with chin slope, light rear upright and brown pad.
The rip carries two optics (Quickdraw nested inside the Red Dot-OAS); the outer OAS is the one modelled.
Rip -> model: 25.7 px/m (21 px/m across, drums kept inside the base cage width), rip magazine centre -> z 3.3,
OAS reticle centre -> the base eye line y 12.79; forward of the drums (z < -5) the shroud/barrel is compressed to
20.4 px/m so the muzzle lands at z -10 (base -9.54).
Reticle: own green ring (NO_OVERLAY) on the scope front window plane, like the W302 Khvostov holo.
Detail/pixel pass: chamfered shroud/receiver/stock, vent slats, ribs, drum hubs; the OAS scope is a hollow
'sight_*' box frame around the aim line (open front and back); receiver top steps down before the stock (ADS).
"""
S, SX = 25.7, 21.0
ZM, YM = 3.3, -0.1635
YE, ZE = 12.79, 0.2395
ZB, SF = -5.0, 20.4
NO_OVERLAY = True
OCC_TOL = 0.035                   # rip shroud sides sit ~1 px inside the drum/cage envelope: accept them
EY = 12.785                       # eye line (base W151 aim tip centre / Khvostov reticle centre)
RETICLE = (70, 235, 90, 255)


def station(z):
    return YM + (z - ZM) / S if z >= ZB else YM + (ZB - ZM) / S + (z - ZB) / SF


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / SX, station(z), ZE + (y - YE) / S)


def is_magazine(n): return n.startswith('mag_')


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_m2tools'))
from solid import B, bar, vbar, octo, Flat, clean


def elements():
    E = []; a = E.append
    # ---- muzzle: twin prongs with tips, block with bore, stepped nose, chamfered shroud, fin, vent cover with slats
    for k, (y0, y1) in (('u', (10.05, 10.27)), ('l', (9.62, 9.84))):
        a(B(f'muz_prong_{k}', (7.88, y0, -10.05), (8.12, y1, -9.05)))
    for e in bar('muz_block', 7.45, 8.55, 9.55, 10.85, -9.1, -8.0, c=.16, top=True, bottom=True): a(e)
    a(B('muz_bore', (7.82, 9.82, -9.12), (8.18, 10.12, -9.1)))
    a(B('nose_low', (7.3, 9.15, -8.15), (8.7, 10.4, -6.85)))
    for e in bar('nose_high', 7.3, 8.7, 10.4, 11.4, -7.55, -6.85, c=.2): a(e)
    for e in bar('shroud', 7.2, 8.8, 9.0, 11.5, -6.9, 0.35, c=.24, at=[-4.1]): a(e)
    a(B('shroud_fin', (7.5, 11.5, -6.75), (8.5, 11.95, -5.8)))
    a(B('shroud_fin_rake', (7.5, 11.5, -5.95), (8.5, 11.85, -5.35), ('x', -35), (8, 11.5, -5.8)))
    a(B('vent_cover', (7.35, 11.35, -1.1), (8.65, 11.62, 2.25)))
    for k in range(5):
        z = -0.95 + k * .62
        a(B(f'vent_slat_{k}', (7.42, 11.62, z), (8.58, 11.72, z + .3)))
    a(B('spike_rod', (7.9, 7.9, -9.0), (8.1, 8.1, -6.3)))
    a(B('spike_tip', (7.92, 7.92, -9.3), (8.08, 8.08, -9.0)))
    a(B('spike_strut', (7.88, 7.95, -6.7), (8.12, 9.1, -6.45), ('x', 25), (8, 7.95, -6.58)))
    for e in bar('rib_block', 7.45, 8.55, 7.6, 9.0, -5.8, 0.35, c=.16, top=False, bottom=True, at=[-2.7]): a(e)
    for k in range(7):
        z = -5.55 + k * .82
        a(B(f'rib_{k}', (7.4, 7.7, z), (8.6, 8.85, z + .32)))
    # ---- drums: three discs per side (octagon) with a raised hub
    for s, (x0, x1) in (('l', (6.85, 7.22)), ('r', (8.78, 9.15))):
        for k, (cz, cy) in enumerate(((-2.06, 10.9), (-3.16, 9.72), (-2.06, 9.72))):
            r = .58
            for e in octo(f'drum_{s}{k}', cz, cy, r, x0, x1, axis='x'): a(e)
            hx = (x0 - .06, x0) if s == 'l' else (x1, x1 + .06)
            a(B(f'drum_{s}{k}_hub', (hx[0], cy - .2, cz - .2), (hx[1], cy + .2, cz + .2)))
    # ---- receiver: chamfered body, top (ends before the stock drop), ramp, lower, fore plates, grip frame, grip
    for e in bar('rcv_body', 7.25, 8.75, 9.0, 11.2, 0.3, 8.9, c=.2, at=[3.85, 6.5]): a(e)
    for e in bar('rcv_top', 7.3, 8.7, 11.2, 12.05, 3.85, 8.4, c=.2): a(e)
    a(B('rcv_top_tail', (7.3, 11.2, 8.4), (8.7, 11.6, 9.0), ('x', 32), (8, 11.6, 8.4)))
    a(B('rcv_ramp', (7.3, 11.2, 2.0), (8.7, 11.9, 3.9), ('x', -23.6), (8, 11.9, 3.9)))
    a(B('rcv_lower', (7.3, 7.5, 0.3), (8.7, 9.0, 5.0)))
    a(B('rcv_lower_rear', (7.3, 8.2, 5.0), (8.7, 9.0, 7.05)))
    a(B('ejector', (8.75, 9.7, 5.2), (8.95, 10.3, 6.4)))
    for s, (x0, x1) in (('l', (7.15, 7.3)), ('r', (8.7, 8.85))):
        a(B(f'fore_plate_{s}', (x0, 7.85, 0.65), (x1, 8.95, 4.9)))
        a(B(f'fore_bolt_{s}', (x0 - .05 if s == 'l' else x1, 8.4, 1.1), (x0 if s == 'l' else x1 + .05, 8.6, 1.3)))
    a(B('trigger', (7.93, 7.6, 6.0), (8.07, 8.2, 6.18), ('x', -12), (8, 8.2, 6.1)))
    a(B('frame_post', (7.62, 4.95, 4.5), (8.38, 7.55, 4.95)))
    a(B('frame_bottom', (7.62, 5.0, 4.5), (8.38, 5.4, 7.9), ('x', -11), (8, 5.2, 4.5)))
    a(B('guard_post', (7.6, 7.45, 6.6), (8.4, 8.25, 7.05)))
    a(B('grip', (7.4, 5.7, 7.0), (8.6, 9.05, 8.15), ('x', -18), (8, 9.05, 7.55)))
    a(B('grip_panel', (7.36, 6.2, 7.2), (8.64, 8.4, 7.95), ('x', -18), (8, 9.05, 7.55)))
    # ---- Red Dot-OAS scope: hollow box frame around the aim line (all 'sight_*', window x 7.68..8.32 / y 12.5..13.1)
    a(B('sight_mount', (7.55, 11.9, 3.8), (8.45, 12.4, 4.65)))
    a(B('sight_floor', (7.5, 12.1, 4.5), (8.5, 12.5, 7.75)))
    for s, (x0, x1) in (('l', (7.48, 7.68)), ('r', (8.32, 8.52))):
        a(B(f'sight_cheek_{s}', (x0, 12.5, 4.5), (x1, 13.1, 7.75)))
        a(B(f'sight_dial_{s}', (x0 - .08 if s == 'l' else x1, 12.6, 5.9), (x0 if s == 'l' else x1 + .08, 12.95, 6.3)))
    a(B('sight_roof', (7.48, 13.1, 4.5), (8.52, 13.27, 7.75)))
    a(B('sight_front_bezel', (7.46, 13.05, 4.4), (8.54, 13.3, 4.6)))
    a(B('sight_rear_bezel', (7.46, 12.08, 7.45), (8.54, 12.52, 7.78)))
    for n, (x0, x1, y0, y1) in {'l': (7.79, 7.86, EY - .05, EY + .05), 'r': (8.14, 8.21, EY - .05, EY + .05),
                                't': (7.95, 8.05, EY + .15, EY + .21), 'b': (7.95, 8.05, EY - .21, EY - .15),
                                'c': (7.985, 8.015, EY - .015, EY + .015)}.items():
        a(B(f'sight_reticle_{n}', (x0, y0, 4.55), (x1, y1, 4.57), shade=False, light_emission=15))
    # ---- stock (kept under the base top 11.33)
    for e in bar('st_top', 7.4, 8.6, 10.3, 11.1, 8.1, 14.15, c=.18, at=[11.1]): a(e)
    a(B('st_rail', (7.35, 9.83, 8.85), (8.65, 10.3, 13.5)))
    a(B('st_lower', (7.45, 7.95, 11.6), (8.55, 9.83, 13.4)))
    a(B('st_lower_front', (7.45, 9.2, 9.4), (8.55, 9.83, 10.6)))
    a(B('st_chin', (7.46, 8.6, 9.55), (8.54, 9.5, 12.45), ('x', 26.6), (8, 9.05, 11.0)))
    a(B('st_upright', (7.36, 7.85, 12.85), (8.64, 9.9, 13.55)))
    for e in vbar('st_pad', 7.4, 8.6, 7.48, 11.0, 13.45, 14.5, c=.16, front=False): a(e)
    a(B('st_pad_cap', (7.42, 11.0, 13.4), (8.58, 11.25, 14.25)))
    # ---- magazine
    a(B('mag_body', (7.6, 4.95, 2.05), (8.4, 7.9, 4.45)))
    a(B('mag_window', (7.56, 6.1, 2.8), (8.44, 6.6, 3.3)))
    a(B('mag_pad', (7.52, 4.43, 1.95), (8.48, 5.0, 4.52)))
    return clean(E)


_flat = Flat([
    (lambda n, f: n.startswith(('muz_prong', 'spike')), (190, 214, 222)),
    (lambda n, f: n in ('muz_bore', 'mag_window') or n.startswith(('vent_slat', 'rib_')) and n != 'rib_block', (40, 38, 36)),
    (lambda n, f: n.endswith('_hub') or n.startswith(('fore_bolt', 'sight_dial', 'ejector')), (60, 58, 56)),
    (lambda n, f: n.startswith('vent_cover'), (49, 47, 45)),
    (lambda n, f: '_joint_' in n, (40, 38, 36)),
    (lambda n, f: n.startswith(('grip', 'frame_', 'guard_')) and n != 'grip_panel' and f not in ('east', 'west'), (70, 66, 62)),
    (lambda n, f: n == 'grip_panel', (45, 44, 41)),
    (lambda n, f: n.startswith('st_pad'), (70, 60, 52)),
])


def special(e, fn, s, t):
    if 'reticle' in e['name']:
        return RETICLE
    return _flat(e, fn, s, t)


PALETTE_KEEP = [RETICLE[:3]]

PALETTE = 18
FLAT_TOL = 30
PALETTE_KEEP = [RETICLE[:3], (190, 214, 222), (40, 38, 36)]

# W325 identity pass: every face is hand-painted at 20 texels/model px.
from identity import Painter
T = 20
ATLAS = 1024
special = Painter('ros', T)

from identity import geometry
_base_elements = elements
def elements(): return geometry(_base_elements(), 'ros')

# W325 MATERIAL pass supersedes whole-face identity.Painter fills.
from materials import Materials, Decals
STYLE = "material"
material = Materials('ros')
MATERIALS = material.palette
special = Decals('ros', model2world, 'ros_lysis_ii', T)
