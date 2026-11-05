"""W325 Yellowjacket-3au (VEIST rapid-fire auto rifle, Red War rare) over steelfeather_repeater (layout contract:
weapon_reload_w213_steelfeather_repeater + weapon_sight_w151).

The rip uses the identical VEIST frame mesh as Sand Wasp-3au (same Back/Front/Magazine/Stock objects), so the body
solids (_m2tools/veist.py) and the rip->model map are shared; only the optic (compact upright red-dot frame, all
'sight_*' elements, open window around the eye line) and the paint differ.
Identity kept: grey/black VEIST camo, lime magazine in the side window with the white chevron front, white
suppressor, dark C-ring front grip + raked pistol grip, VEIST logo on the receiver (projected).
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


def elements(): return veist.build('reddot')


special = veist.painter({'sup': (224, 223, 224), 'metal': (66, 66, 66), 'plate': (60, 58, 56),
                         'grip': (78, 76, 71), 'pad': (52, 51, 46),
                         'rounds': (164, 200, 84), 'mag_front': (208, 212, 200), 'accent': (150, 186, 70)})
PALETTE_KEEP = [(164, 200, 84), (208, 212, 200), (150, 186, 70)]
PALETTE = 16
FLAT_TOL = 34

# W325 identity pass: every face is hand-painted at 20 texels/model px.
from identity import Painter
T = 20
ATLAS = 1024
special = Painter('yellow', T)

# W325 MATERIAL pass supersedes whole-face identity.Painter fills.
from materials import Materials, Decals
STYLE = "material"
material = Materials('yellow')
MATERIALS = material.palette
special = Decals('yellow', model2world, 'yellowjacket_3au', T)
