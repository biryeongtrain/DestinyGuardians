"""W325 Black Tiger-2sr (rare scout rifle, Rapid-Fire, VEIST) over base aishas_embrace (W153 sight layout).

Authored in rip-image coordinates of the calibrated nx view (proj_cache/nx_albedo.png, 800 px/m, muzzle right).
Station map anchored on the grip bar between the thumbhole and the trigger opening (ix 275 -> z 10.2, the base grip
front strap); rear 0.026 / forward 0.035 model px per image px (the rip grip sits much further from the muzzle than the
base: butt ends z 17.1 (base 15.78), muzzle -6.1 (base -9.22)).  Vertical 0.031 anchored on the rip reticle centre
(iy 22.3 -> y 12.3, centre of the base W153 optic window y 12.11..12.48); bore y 10.5 (base 10.09).  Lateral 25 px/m about
the rip centreline (13 mm off the rip origin).
Contract moves (undone in model2world): the window sight (hood, side walls, sloped side fins) moves 0.9 px forward so
its reticle plane sits on the base aim tip (z 6.8); the window x 7.67..8.33 / y 12.06..12.62 frames the kept W148 tip.
Magazine: P90-style top magazine (rip object 'Magazine') kept where it is, inside a real side window in the upper body;
it is the moving part even though the base moving magazine hangs below the stock (see notes).
"""
import json, math
from _w3lib import bevel, clamp_tops, machine, zslice, adopt, tidy, stairs_for
B = 'aishas_embrace'
from pathlib import Path

_M = json.loads((Path(__file__).parent / 'proj_cache/manifest.json').read_text())
_V = _M['views']['nx']; PPM = _M['ppm']; W, H = _V['res']; CX, CY, CZ = _V['centre']

ANCH_IX, ANCH_Z, REAR_K, FRONT_K = 275, 10.2, 0.026, 0.035
ANCH_IY, ANCH_Y, VK = 22.3, 12.3, 0.031
LAT = 25.0
XW0 = CX - 0.33 / 25
SIGHT_DZ = -1.35


def Z(ix): return ANCH_Z + (ANCH_IX - ix) * (REAR_K if ix <= ANCH_IX else FRONT_K)
def Y(iy): return ANCH_Y - (iy - ANCH_IY) * VK
def ix_of(z): return ANCH_IX - (z - ANCH_Z) / (REAR_K if z >= ANCH_Z else FRONT_K)
def iy_of(y): return ANCH_IY - (y - ANCH_Y) / VK


def box(name, ix0, ix1, iy0, iy1, hw, xc=8.0, dz=0.0):
    z0, z1 = sorted((Z(ix0), Z(ix1))); y0, y1 = sorted((Y(iy0), Y(iy1)))
    return {'name': name, 'from': [xc - hw, y0, z0 + dz], 'to': [xc + hw, y1, z1 + dz]}


def xbox(name, ix0, ix1, iy0, iy1, x0, x1, dz=0.0):
    b = box(name, ix0, ix1, iy0, iy1, 0.1, dz=dz); b['from'][0], b['to'][0] = x0, x1; return b


def rbox(name, top, bot, width, hw, xc=8.0):
    zt, yt = Z(top[0]), Y(top[1]); zb, yb = Z(bot[0]), Y(bot[1])
    dz, dy = zb - zt, yb - yt; L = math.hypot(dz, dy); a = math.degrees(math.atan2(-dz, -dy))
    return {'name': name, 'from': [xc - hw, yt - L, zt - width / 2], 'to': [xc + hw, yt, zt + width / 2],
            'rotation': {'origin': [xc, yt, zt], 'x': round(a, 4), 'y': 0, 'z': 0}}


def sbar(name, p0, p1, thick, x0, x1, dz=0.0):
    """Bar whose top edge runs along the image segment p0 -> p1 (rear -> front), thickness below it."""
    z0, y0 = Z(p0[0]) + dz, Y(p0[1]); z1, y1 = Z(p1[0]) + dz, Y(p1[1])
    L = math.hypot(z1 - z0, y1 - y0); a = math.degrees(math.atan2(y1 - y0, z0 - z1))   # rise toward -z
    return {'name': name, 'from': [x0, y0 - thick, z0 - L], 'to': [x1, y0, z0],
            'rotation': {'origin': [(x0 + x1) / 2, y0, z0], 'x': round(a, 4), 'y': 0, 'z': 0}}


STEPS = ((-16, 11.5, 11.8), (11.5, 12.75, 11.45), (12.75, 32, 10.76))


def sight():
    d = SIGHT_DZ
    return [box('sight_floor', 316, 368, 30, 42, 0.62, dz=d),
            box('sight_hood', 335, 368, 8, 12, 0.62, dz=d),
            xbox('sight_wall_l', 335, 368, 12, 30, 7.38, 7.67, dz=d),
            xbox('sight_wall_r', 335, 368, 12, 30, 8.33, 8.62, dz=d),
            xbox('sight_post_l', 316, 335, 18, 30, 7.42, 7.67, dz=d),
            xbox('sight_post_r', 316, 335, 18, 30, 8.33, 8.58, dz=d),
            {'name': 'sight_bev_l', 'from': [7.5 - 0.085, Y(10) - 0.085, Z(368) + d + 0.02], 'to': [7.5 + 0.085, Y(10) + 0.085, Z(335) + d - 0.02],
             'rotation': {'origin': [7.5, Y(10), (Z(368) + Z(335)) / 2 + d], 'x': 0, 'y': 0, 'z': 45}},
            {'name': 'sight_bev_r', 'from': [8.5 - 0.085, Y(10) - 0.085, Z(368) + d + 0.02], 'to': [8.5 + 0.085, Y(10) + 0.085, Z(335) + d - 0.02],
             'rotation': {'origin': [8.5, Y(10), (Z(368) + Z(335)) / 2 + d], 'x': 0, 'y': 0, 'z': 45}}]


def fillet(name, ix, iy, size, hw):
    zc, yc = Z(ix), Y(iy); h = size * 0.7071
    return {'name': name, 'from': [8 - hw, yc - h, zc - h], 'to': [8 + hw, yc + h, zc + h],
            'rotation': {'origin': [8.0, yc, zc], 'x': 45, 'y': 0, 'z': 0}}


def _base_elements():
    upper = [box('upper_rear', 35, 100, 58, 128, 0.5), box('up_top', 100, 280, 46, 65, 0.52),
             box('up_bot', 100, 280, 90, 128, 0.52), box('win_rear', 100, 138, 65, 90, 0.5),
             box('win_mag', 138, 280, 65, 90, 0.42), box('win_cart', 160, 262, 70, 84, 0.45)]
    e = [*bevel(box('butt', 8, 35, 58, 178, 0.5), 0.12, top=False, bottom=True),
         box('butt_pad', 4, 10, 64, 172, 0.46)]
    # three deliberate flat steps that follow the base stock top (ADS), each step shares exact planes with its neighbours
    for u in upper:
        f, t = u['from'], u['to']
        for k, (z0, z1, ymax) in enumerate(STEPS):
            a, b = max(f[2], z0), min(t[2], z1)
            if b - a < 0.05: continue
            top = min(t[1], ymax)
            if top - f[1] < 0.05: continue
            e.append(dict(u, name=f"{u['name']}_s{k}", **{'from': [f[0], f[1], a], 'to': [t[0], top, b]}))
    e += [
        *bevel(box('low_rear', 35, 180, 128, 176, 0.5), 0.14, top=False, bottom=True),
        sbar('low_sweep', (118, 150), (192, 177), 0.85, 7.52, 8.48),
        box('side_rail', 100, 280, 88, 92, 0.55),
        box('veist_plate', 150, 215, 108, 120, 0.54),
        *bevel(box('upper_front', 280, 370, 42, 128, 0.62), 0.16),
        box('front_band', 340, 352, 40, 130, 0.65),
        box('low_under_thumb', 180, 262, 162, 205, 0.5),
        fillet('fil_t0', 180, 128, 0.5, 0.5), fillet('fil_t1', 262, 128, 0.4, 0.5),
        box('grip_bar', 262, 287, 128, 192, 0.5),
        box('grip_panel', 265, 284, 140, 185, 0.53),
        *bevel(box('tg_bottom', 287, 330, 165, 190, 0.5), 0.12, top=False, bottom=True),
        *bevel(box('tg_front', 330, 372, 128, 170, 0.5), 0.12, top=False, bottom=True),
        fillet('fil_g0', 298, 165, 0.3, 0.5), fillet('fil_g1', 330, 165, 0.3, 0.5),
        box('tg_lip', 372, 400, 128, 152, 0.48),
        box('trigger', 291, 298, 134, 158, 0.08),
        *bevel(box('shroud', 370, 741, 60, 100, 0.45), 0.1, top=True, bottom=True),
        box('shroud_rib0', 430, 438, 58, 102, 0.47), box('shroud_rib1', 600, 608, 58, 102, 0.47),
        box('shroud_tip', 728, 744, 62, 98, 0.43),
        box('ejector', 372, 400, 64, 82, 0.47),
        box('claw_root', 398, 445, 100, 116, 0.3),
        rbox('claw_tip', (440, 108), (498, 137), 0.38, 0.25),
        rbox('claw_teeth', (400, 113), (440, 116), 0.25, 0.32),
    ]
    e += sight()
    e = stairs_for(e, ('low_sweep',), 4)
    e = clamp_tops(e, B)
    e = [x for x in e if x['name'] != 'claw_teeth']
    e = machine(e, target=132, maxlen=2.4)
    e = tidy(e)
    # reload part: small stub magazine in the base aishas_embrace moving-magazine box (the real P90 top magazine is fixed)
    e += [{'name': 'mag_stub', 'from': [7.6, 5.75, 10.75], 'to': [8.4, 6.9, 12.25], 'rotation': {'origin': [8, 6.3, 11.5], 'x': 28, 'y': 0, 'z': 0}},
          {'name': 'mag_stub_floor', 'from': [7.55, 5.6, 10.65], 'to': [8.45, 5.82, 12.35], 'rotation': {'origin': [8, 6.3, 11.5], 'x': 28, 'y': 0, 'z': 0}}]
    return e


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('sight_'):
        z -= SIGHT_DZ
    ix, iy = ix_of(z), iy_of(y)
    return (XW0 - (x - 8) / LAT, CY - (ix - W / 2) / PPM, CZ - (iy - H / 2) / PPM)


INNER = (20, 22, 24, 255)
MINT, MINT_D, BLACK, GREYD, ORANGE, RUST = (206, 218, 206), (168, 182, 170), (34, 38, 36), (58, 62, 60), (196, 112, 54), (120, 48, 40)
WHITE_PARTS = ('upper_rear', 'up_top', 'up_bot', 'win_rear', 'upper_front', 'shroud', 'claw', 'sight', 'ejector', 'front_band')
PALETTE = 16
FLAT_TOL = 30
PALETTE_KEEP = [MINT, BLACK, ORANGE, RUST]


def _base_paint(e, fn, s, t):
    n = e['name']
    if n.startswith('sight_floor') and fn == 'up' or n == 'sight_hood' and fn == 'down':
        return INNER
    if n in ('sight_wall_l', 'sight_post_l') and fn == 'east' or n in ('sight_wall_r', 'sight_post_r') and fn == 'west':
        return INNER
    if n.startswith('shroud') and fn == 'north' and n == 'shroud':
        if math.hypot(s - .5, t - .5) < 0.22: return (10, 10, 11, 255)
    if n.startswith('win_cart'):
        if fn in ('east', 'west'): return (ORANGE if (int(s * 14) % 3) else RUST) + (255,)
        return ORANGE + (255,)
    if n.startswith('win_mag'): return GREYD + (255,)
    if n.startswith('veist_plate') and fn in ('east', 'west'): return None     # VEIST logo projects cleanly
    if n.startswith('side_rail'): return (150, 160, 152, 255)
    if n.startswith('shroud_rib') or n.startswith('front_band'): return MINT_D + (255,)
    if n.startswith('shroud') and fn in ('east', 'west'):
        z = e['from'][2] + (s if fn == 'west' else 1 - s) * (e['to'][2] - e['from'][2])
        y = e['to'][1] - t * (e['to'][1] - e['from'][1])
        for dz, dy in ((0, 0.16), (-0.3, -0.04), (0, -0.24)):
            if abs(z - (-1.0 + dz)) < 0.11 and abs(y - (10.55 + dy)) < 0.11: return BLACK + (255,)
        return MINT + (255,)
    if n.startswith(WHITE_PARTS): return MINT + (255,)
    if n.startswith(('mag_', 'butt', 'low_', 'grip', 'tg_', 'fil_', 'trigger')): return BLACK + (255,)
    return None


T = 18

# Identity pass: explicit per-face pixel paint, with real depth for signature apertures.
from _identity import enrich_geometry
IDENTITY_ID = 'black_tiger_2sr'
T = 19
ATLAS = 512

def elements():
    return enrich_geometry(_base_elements(), globals())

def special(e, fn, s, t):
    return material_decals(e, fn, s, t, globals())

# W123 material pass: semantic surfaces with source relief; special only marks decals.
from _materials import material_specs, choose_material, material_decals
STYLE = "material"
MATERIALS = material_specs(IDENTITY_ID)

def material(name, face):
    return choose_material(name, face, globals())
