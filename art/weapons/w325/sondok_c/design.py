"""W325 Sondok-C (rare, precision SMG, Hakke snow camo + orange panel + red-brown polymer) over base antiope_d (W182/W212 reload, W153 sight).
Detail pass v2: geometry in art/weapons/w325/_lib_m8/hakke.py (shared with Sondok-C), sight variant 'reflex'.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '_lib_m8'))
import hakke  # noqa: E402

S, SY, SW, BP = hakke.S, hakke.SY, hakke.SW, hakke.BP
model2world = hakke.model2world


def elements():
    return hakke.common('reflex')


special = hakke.make_painter({'camo': ((220, 222, 218), (150, 156, 150), (186, 182, 140)), 'poly': (78, 50, 38),
                               'poly_l': (100, 66, 50), 'white': (226, 226, 222), 'steel': (150, 150, 146),
                               'accent': (224, 92, 50), 'accent_text': 'HAKKE', 'mark': (224, 92, 50)})
PALETTE = 24
FLAT_TOL = 6
PALETTE_KEEP = [(220, 222, 218), (150, 156, 150), (186, 182, 140), (78, 50, 38), (100, 66, 50), (226, 226, 222),
                (224, 92, 50), (18, 18, 20), (40, 140, 60)]

# Ace/Izanagi identity pass: exact face paint and a denser 1P atlas.
T = 20
ATLAS = 1024
from identity import enhance
special = enhance("sondok_c", special, T)

# W123 material pass replaces full-face flat special paint.
STYLE = "material"
from surface import setup as material_setup
MATERIALS, material, special = material_setup("sondok_c")
