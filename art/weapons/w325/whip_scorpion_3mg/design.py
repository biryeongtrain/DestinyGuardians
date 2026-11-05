"""W325 Whip Scorpion-3mg (rare SMG, Lightweight) over base the_recluse.

Same VEIST lightweight SMG rip mesh as Furina-2mg (identical bounds/silhouette), so the geometry, model2world and
painting code come from ../furina_2mg/design.py; only the colour scheme differs (rip albedo): black/charcoal camo,
lime dotted rail windows and lime VEIST stock logo, pale shroud.  ADS fix and sight ring are inherited from Furina.
"""
import importlib.util
from pathlib import Path

_p = Path(__file__).resolve().parent.parent / 'furina_2mg' / 'design.py'
_s = importlib.util.spec_from_file_location('w325_furina_shared', _p); _m = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_m)
_m.COLS = dict(camo=((36, 36, 38), (36, 36, 38), (92, 92, 96)), dark=(34, 34, 36), shroud=(214, 210, 214),
               rail=(150, 150, 154), window=(150, 210, 60), accent=(150, 210, 60), logo=(150, 210, 60),
               knurl=(168, 164, 168))
_m.FLAT = {}
elements, model2world, special = _m.elements, _m.model2world, _m.special
T, PALETTE, FLAT_TOL = _m.T, _m.PALETTE, _m.FLAT_TOL
PALETTE_KEEP = [(150, 210, 60)]

ATLAS = _m.ATLAS

# Material pass uses this weapon's own source cache and gray/lime dye.
STYLE='material'
_m.MATERIAL_WID='whip_scorpion_3mg'
_m.MATERIALS['receiver'].update(color=(34,35,38),detail=.7)
_m.MATERIALS['shroud'].update(color=(205,201,208))
_m.MATERIALS['collar'].update(color=(156,151,160))
_m.MATERIALS['polymer'].update(color=(25,27,29))
_m.MATERIALS['rubber'].update(color=(21,23,25))
_m.CAMO_LIGHT=(103,102,112)
_m.WINDOW=(142,188,58)
_m.LOGO=(145,194,59)
_m.ACCENT=(132,178,51)
MATERIALS,material,special=_m.MATERIALS,_m.material,_m.special

# Second material pass inherits the revised maps and motifs, then preserves the gray/lime dye.
_m.MATERIALS['receiver'].update(color=(33,35,38),wear=False)
_m.MATERIALS['polymer'].update(color=(65,71,77),detail=.15)
_m.MATERIALS['rubber'].update(color=(16,20,24))
_m.MATERIALS['structure'].update(color=(92,105,114))
material,special=_m.material,_m.special
