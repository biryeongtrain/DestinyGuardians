"""W325 Philippis-B (rare, precision SMG, grey camo / dark polymer) over base antiope_d (W182/W212 reload, W153 sight).
Detail pass v2: geometry in art/weapons/w325/_lib_m8/hakke.py (shared with Sondok-C), sight variant 'peep'.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib_m8'))
import hakke  # noqa: E402

S, SY, SW, BP = hakke.S, hakke.SY, hakke.SW, hakke.BP
model2world = hakke.model2world


def elements():
    return hakke.common('peep')


special = hakke.make_painter({'camo': ((150, 148, 140), (104, 102, 98), (196, 194, 188)), 'poly': (62, 56, 50),
                               'poly_l': (84, 76, 68), 'white': (214, 214, 208), 'steel': (150, 150, 146),
                               'accent': None, 'mark': None})
PALETTE = 24
FLAT_TOL = 6
PALETTE_KEEP = [(150, 148, 140), (104, 102, 98), (196, 194, 188), (62, 56, 50), (84, 76, 68), (214, 214, 208), (18, 18, 20)]

# Ace/Izanagi identity pass: exact face paint and a denser 1P atlas.
T = 20
ATLAS = 1024
from identity import enhance
special = enhance("philippis_b", special, T)

# W123 material pass replaces full-face flat special paint.
STYLE = "material"
from surface import setup as material_setup
MATERIALS, material, special = material_setup("philippis_b")
