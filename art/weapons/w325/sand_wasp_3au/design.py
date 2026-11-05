"""W325 Sand Wasp-3au (VEIST rapid-fire auto rifle, Red War rare) over steelfeather_repeater (layout contract:
weapon_reload_w213_steelfeather_repeater + weapon_sight_w151).  W325 detail pass: geometry in _m2tools/veist.py.

Identity kept: long white suppressor, dark C-ring front grip with forward hook, dark raked pistol grip, camo receiver
with the dark raised side plates, horizontal VEIST magazine seen through the side window (brass rounds + red/white
front), long-hooded holo over the receiver, camo slab stock with the dark top rail and notched butt pad.
Rip -> model: uniform 28 px/m (26 px/m across), grip top on the base grip, holo reticle centre on the W151 eye line
(y 12.95); the plain suppressor forward of the ring grip is stretched (46 px/m) so the muzzle reaches z -8.3.
Detail pass: chamfered receiver/stock/housing edges, octagonal suppressor/barrel, flat paint on the smeared
suppressor and the dark polymer parts; ADS: holo is an open 'sight_*' frame, the hood rails and the stock top were
lowered under the base top profile (the rip's rising stock rail and butt spike are flattened to y <= 12.62).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_m2tools'))
import veist

S, SX = 28.0, 26.0
YB, SF = -0.38, 46.0
ZG, YG = 7.6, -0.032
YE, ZE = 12.95, 0.195
NO_OVERLAY = False


def station(z):
    zb = ZG + (YB - YG) * S
    return (z - ZG) / S + YG if z >= zb else YB + (z - zb) / SF


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / SX, station(z), ZE + (y - YE) / S)


def is_magazine(n): return n.startswith('mag_')


def elements(): return veist.build('holo')


special = veist.painter({'sup': (236, 228, 216), 'metal': (66, 67, 66), 'plate': (69, 70, 64),
                         'grip': (64, 66, 62), 'pad': (62, 60, 56),
                         'rounds': (150, 140, 96), 'mag_front': (214, 206, 198), 'accent': (176, 52, 44)})
PALETTE_KEEP = [(150, 140, 96), (176, 52, 44), (214, 206, 198)]
PALETTE = 16
FLAT_TOL = 34

# W325 identity pass: every face is hand-painted at 20 texels/model px.
from identity import Painter
T = 20
ATLAS = 1024
special = Painter('sand', T)

# W325 MATERIAL pass supersedes whole-face identity.Painter fills.
from materials import Materials, Decals
STYLE = "material"
material = Materials('sand')
MATERIALS = material.palette
special = Decals('sand', model2world, 'sand_wasp_3au', T)
