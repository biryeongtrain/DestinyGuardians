"""W325 Azimuth DSu (rare Aggressive hand cannon) over base duke_mk_44.  Authored in rip-image px (nx view) -> model px.
Same frame family as Mos Ultima II (identical receiver/grip in the rip).  Calibration: rip cylinder centre (img 131,55) ->
duke cylinder centre (z 3.77, y 12.80); S 38 px/m, SX 38 (rear/grip land on the duke layout without squeeze); the long
shroud, side panel and protruding barrel ahead of the frame front (img x 215) are compressed 0.62x ; the protruding barrel is shortened to 0.37x (muzzle -6.67, base -6.2).
No top lowering needed: duke sight line is ~14.95, the Azimuth top rib is 14.37 (rear sight 14.7)."""
import math
from pathlib import Path
from hc import Cal, box, tb_from, hwarp, hsq, lin_warp, Painter, slab, bolt
from frame_mos import frame

C = Cal(Path(__file__).parent / 'proj_cache', (131, 55), (3.77, 12.80), 38.0, 38.0, front=(215, 0.62))
T = 20
ATLAS = 1024  # 1024x512 after crop: readable 1P glyphs, fine grooves and grip texels.
OCC_TOL = 0.02
GT = 26.0
GP0 = (C.z(96), C.y(92))
GK = 0.95

TUBE = (C.z(388), C.z(388) - 1.45, C.z(465))     # protruding barrel shortened again (model z0 -> z1, rip-equivalent z465)
C.warps += [('grip', hwarp(GP0, GT, GK)), ('muzzle_tube', lin_warp('z', TUBE[0], TUBE[1], TUBE[0], TUBE[2]))]


def sq(xi, yi): return hsq(GP0, GT, GK, C.z(xi), C.y(yi))


def model2world(name, p): return C.model2world(name, p)


CLIPPED = []


def extra():
    z, y, R = C.z, C.y, C.R; E = []
    E += slab('side_panel', 7.02, 8.98, y(95), y(52), z(362), z(255), c=.12, cuts=(z(310),))
    for sd, t in ((-1, 'w'), (1, 'e')):
        xf = 7.02 if sd < 0 else 8.98
        for i, xi in enumerate((270, 345)):
            E.append(bolt(f'bolt_{t}p{i}', z(xi), y(60), xf, sd, s=.22))
    z0, z1 = TUBE[1], TUBE[0]; y0, y1 = y(78), y(55); cy = (y0 + y1) / 2; r = (y1 - y0) / 2
    E.append(box('muzzle_tube_0', [8-r, cy-r*.42, z0], [8+r, cy+r*.42, z1]))
    E.append(box('muzzle_tube_1', [8-r*.42, cy+r*.42, z0], [8+r*.42, cy+r, z1]))
    E.append(box('muzzle_tube_2', [8-r*.42, cy-r, z0], [8+r*.42, cy-r*.42, z1]))
    c = R('muzzle_tube_core', 388, 57, 465, 76, 7.6, 8.4); c['from'][2] = TUBE[1]; E.append(c)
    E.append(box('muzzle_tube_ring', [8 - r - .06, cy - r - .06, z0 + .25], [8 + r + .06, cy + r + .06, z0 + .45]))
    return E


def elements():
    return frame(C, GP0, GT, GK, 'duke_mk_44', front_cuts=(C.z(300), C.z(230)), extra=extra, clipped=CLIPPED)


PALETTE = 14
SAGE, CREAM, OLIVE, DARK, BLACK, BLUSH = ((176, 186, 150, 255), (232, 222, 206, 255), (118, 112, 96, 255),
                                         (46, 48, 44, 255), (20, 20, 22, 255), (236, 214, 204, 255))
PALETTE_KEEP = [SAGE[:3], CREAM[:3]]
CAMO = (('shroud', 'frame_', 'top_strap'))
SIDE = [(('top_rib',), 215, 255, 24, 28, BLACK), (('top_rib',), 262, 340, 24, 28, BLACK)]
# camo: a few large cream blobs on the sage frame (rip pattern simplified)
POLY = [(CAMO, [(100, 30), (150, 30), (140, 50), (118, 60), (100, 55)], CREAM),
        (CAMO, [(165, 70), (215, 62), (240, 85), (200, 98), (160, 92)], CREAM),
        (CAMO, [(220, 30), (270, 32), (262, 46), (230, 50)], CREAM),
        (CAMO, [(330, 32), (385, 36), (385, 50), (350, 52)], CREAM),
        (CAMO, [(90, 80), (150, 82), (150, 92), (92, 92)], BLUSH)]
PAINT = Painter(
    parts=[('bolt_', OLIVE), ('sight_', BLACK), ('rim_', CREAM), ('guard_', BLUSH), ('trigger', BLUSH), ('hammer', BLUSH),
           ('grip_heel', OLIVE), ('grip_medallion', (150, 152, 152, 255)), ('grip_panel', (40, 42, 38, 255)),
           ('grip_frame', BLUSH), ('grip_', DARK), ('top_rib', OLIVE), ('top_strap', OLIVE), ('side_panel', DARK),
           ('muzzle_tube', OLIVE), ('shroud_face', SAGE), ('muzzle', SAGE), ('latch', DARK),
           ('mag_core', BLACK), ('mag_drum_fband', CREAM), ('mag_drum_rband', CREAM), ('mag_drum', SAGE),
           ('frame_', SAGE), ('shroud', SAGE)],
    side=SIDE, poly=POLY, cal=C, top=[(('top_rib',), -9, 9, 7.92, 8.08, BLACK)])


def special(e, fn, s, t):
    n = e['name']
    if (n.endswith('_bore') or n == 'muzzle_tube_core') and fn == 'north': return (10, 10, 11, 255)
    return PAINT(e, fn, s, t)

# Identity pass: all visible faces are hand painted at close-view density.
from identity import detail as identity_detail
_base_special = special
def special(e, fn, s, t):
    base = _base_special(e, fn, s, t)
    if e['name'].endswith('_bore') and fn == 'north': return base
    return identity_detail('azimuth_dsu', e, fn, s, t, base, C, T)

from hc import carve_bores
_identity_elements = elements
def elements(): return carve_bores(_identity_elements())

# W325 material pass: material grain and rip relief replace whole-face flat fills.
STYLE = 'material'
from surface import materials as _surface_materials, material as _surface_material, decals as _surface_decals
MATERIALS = _surface_materials('azimuth_dsu')
def material(name, face): return _surface_material('azimuth_dsu', name, face)
def special(e, fn, s, t): return _surface_decals('azimuth_dsu', e, fn, s, t, C)
