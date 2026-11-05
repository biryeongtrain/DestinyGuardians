"""W325 Mos Ultima II (uncommon Adaptive hand cannon) over base austringer.  Authored in rip-image px (nx view) -> model px.
Calibration: rip cylinder centre (img 131,55) -> austringer cylinder centre (z 4.34, y 12.43); S 36 px/m, SX 38; the long
shroud ahead of the frame front (img x 215) is compressed 0.88x so the muzzle lands on the base muzzle (-6.3).
Fits: dark top strap lowered 14.14 -> 13.92 under the sight line; grip/rear frame squeezed horizontally to 0.9."""
import math
from pathlib import Path
from hc import Cal, box, tb_from, hwarp, hsq, lin_warp, Painter
from frame_mos import frame

C = Cal(Path(__file__).parent / 'proj_cache', (131, 55), (4.34, 12.43), 36.0, 38.0, front=(215, 0.88))
T = 20
ATLAS = 1024  # 1024x512 after crop: readable 1P glyphs, fine grooves and grip texels.
OCC_TOL = 0.02
GT = 26.0
GP0 = (C.z(96), C.y(92))
GK = 0.9

C.warps += [('top_strap', lin_warp('y', C.y(30), 13.86, C.y(30), C.y(17))),
            ('grip', hwarp(GP0, GT, GK))]


def sq(xi, yi): return hsq(GP0, GT, GK, C.z(xi), C.y(yi))


def model2world(name, p): return C.model2world(name, p)


CLIPPED = []


def elements():
    return frame(C, GP0, GT, GK, 'austringer', top_y=None, front_cuts=(C.z(300), C.z(230)), clipped=CLIPPED, strap_cap=13.86)


PALETTE = 14
SLATE, DSLATE, RIB, GRIPC, BLACK, LIGHT = ((98, 112, 128, 255), (80, 92, 106, 255), (86, 84, 82, 255),
                                           (58, 58, 58, 255), (20, 20, 22, 255), (176, 186, 196, 255))
PALETTE_KEEP = [SLATE[:3]]
SIDE = [(('top_rib',), 215, 255, 24, 28, BLACK), (('top_rib',), 262, 340, 24, 28, BLACK),
        (('shroud',), 255, 360, 49, 51, LIGHT), (('shroud',), 255, 257, 49, 80, LIGHT),     # engraved panel lines
        (('shroud',), 172, 362, 34, 35, DSLATE)]
for i in range(9):
    SIDE.append((('shroud',), 220 + i * 13, 226 + i * 13, 38, 40, DSLATE))
PAINT = Painter(
    parts=[('bolt_', LIGHT), ('sight_', BLACK), ('rim_', LIGHT), ('guard_', GRIPC), ('trigger', GRIPC), ('hammer', GRIPC),
           ('grip_heel', RIB), ('grip_medallion', (150, 152, 152, 255)), ('grip_panel', (46, 46, 46, 255)), ('grip_', GRIPC),
           ('top_rib', RIB), ('top_strap', RIB), ('shroud_face', DSLATE), ('muzzle', DSLATE), ('latch', GRIPC),
           ('mag_core', BLACK), ('mag_drum_fband', DSLATE), ('mag_drum_rband', DSLATE), ('mag_drum', LIGHT),
           ('frame_', SLATE), ('shroud', SLATE)],
    side=SIDE, cal=C, top=[(('top_rib',), -9, 9, 7.92, 8.08, BLACK)])


def special(e, fn, s, t):
    n = e['name']
    if n.endswith('_bore') and fn == 'north': return (10, 10, 11, 255)
    return PAINT(e, fn, s, t)

# Identity pass: all visible faces are hand painted at close-view density.
from identity import detail as identity_detail
_base_special = special
def special(e, fn, s, t):
    base = _base_special(e, fn, s, t)
    if e['name'].endswith('_bore') and fn == 'north': return base
    return identity_detail('mos_ultima_ii', e, fn, s, t, base, C, T)

from hc import carve_bores
_identity_elements = elements
def elements(): return carve_bores(_identity_elements())

# W325 material pass: material grain and rip relief replace whole-face flat fills.
STYLE = 'material'
from surface import materials as _surface_materials, material as _surface_material, decals as _surface_decals
MATERIALS = _surface_materials('mos_ultima_ii')
def material(name, face): return _surface_material('mos_ultima_ii', name, face)
def special(e, fn, s, t): return _surface_decals('mos_ultima_ii', e, fn, s, t, C)
