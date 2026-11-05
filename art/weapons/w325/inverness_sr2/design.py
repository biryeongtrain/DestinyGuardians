"""W325 Inverness-SR2 (uncommon scout rifle, Precision) over base distant_relation.

Authored in rip-image coordinates of the calibrated nx view (proj_cache/nx_albedo.png, 800 px/m, muzzle right),
converted by a station map: trigger ix 310 -> z 7.47 (base trigger), rear 0.0313 / forward 0.0321 model px per image px
(butt z 16.9, muzzle -8.26 = base); vertical 0.0317 anchored on the receiver top (iy 52 -> y 11.15, base action top),
which puts the bore at y 10.33 (base 10.36).  Lateral 20 px/m about the rip centreline (x offset 5.6 mm).
Contract moves (undone in model2world):
  * the reflex sight (rip: over the trigger) is moved 2.91 px forward / 0.20 down onto the base W151 sight box
    (z 4.3..6.6, window x 7.68..8.32, y 11.42..12.3) so the kept W148 aim tip (z 4.3) is framed and the ADS camera is clear;
  * the magazine is shortened 25% along its axis and raised 0.5 so its floor ends near the base floor (y ~5.1 vs 5.7).
"""
import json, math
from pathlib import Path
from _w3lib import bevel, clamp_tops, FlatPainter, fit, machine, adopt, tidy, stairs_for
B = 'distant_relation'

_M = json.loads((Path(__file__).parent / 'proj_cache/manifest.json').read_text())
_V = _M['views']['nx']; PPM = _M['ppm']; W, H = _V['res']; CX, CY, CZ = _V['centre']

TRIG_IX, TRIG_Z, REAR_K, FRONT_K = 310, 7.47, 0.0313, 0.0321
ANCH_IY, ANCH_Y, VK = 52, 11.15, 0.0317
LAT = 20.0
XW0 = CX - 0.14 / 25          # rip centreline (world x)
MAG_SHORTEN, MAG_DY = 0.75, 0.5
SIGHT_DY = -0.20


def Z(ix): return TRIG_Z + (TRIG_IX - ix) * (REAR_K if ix <= TRIG_IX else FRONT_K)
def Y(iy): return ANCH_Y - (iy - ANCH_IY) * VK
def ix_of(z): return TRIG_IX - (z - TRIG_Z) / (REAR_K if z >= TRIG_Z else FRONT_K)
def iy_of(y): return ANCH_IY - (y - ANCH_Y) / VK


SIGHT_DZ = 4.3 - Z(318)


def box(name, ix0, ix1, iy0, iy1, hw, xc=8.0, dz=0.0, dy=0.0):
    z0, z1 = sorted((Z(ix0), Z(ix1))); y0, y1 = sorted((Y(iy0), Y(iy1)))
    return {'name': name, 'from': [xc - hw, y0 + dy, z0 + dz], 'to': [xc + hw, y1 + dy, z1 + dz]}


def mbox(name, f, t): return {'name': name, 'from': list(f), 'to': list(t)}


def rbox(name, top, bot, width, hw, shorten=1.0, xc=8.0, dy=0.0):
    zt, yt = Z(top[0]), Y(top[1]); zb, yb = Z(bot[0]), Y(bot[1])
    dz, dyy = zb - zt, yb - yt; L = math.hypot(dz, dyy) * shorten; a = math.degrees(math.atan2(-dz, -dyy))
    yt += dy
    return {'name': name, 'from': [xc - hw, yt - L, zt - width / 2], 'to': [xc + hw, yt, zt + width / 2],
            'rotation': {'origin': [xc, yt, zt], 'x': round(a, 4), 'y': 0, 'z': 0}}


def _rot(p, o, a, inv=False):
    a = math.radians(-a if inv else a); c, s = math.cos(a), math.sin(a)
    y, z = p[1] - o[1], p[2] - o[2]
    return (p[0], o[1] + y * c - z * s, o[2] + y * s + z * c)


def octa(name, ix0, ix1, iy0, iy1, hw):
    b = box(name, ix0, ix1, iy0, iy1, hw)
    yc = (b['from'][1] + b['to'][1]) / 2; zc = (b['from'][2] + b['to'][2]) / 2; r = hw * 0.93
    return [b, {'name': name + '_r45', 'from': [8 - r, yc - r, b['from'][2] + 0.02], 'to': [8 + r, yc + r, b['to'][2] - 0.02],
                'rotation': {'origin': [8.0, yc, zc], 'x': 0, 'y': 0, 'z': 45}}]


_mag = rbox('mag_body', (220, 182), (197, 278), 3.0, 0.45, MAG_SHORTEN, dy=MAG_DY)


def sight():
    f, r = 4.3, Z(245) + SIGHT_DZ
    yb, yt = Y(38) + SIGHT_DY, Y(8) + SIGHT_DY
    return [mbox('sight_floor', (7.42, yb, f), (8.58, 11.42, r)),
            mbox('sight_roof', (7.42, 12.3, f), (8.58, yt, r)),
            mbox('sight_wall_l', (7.42, 11.42, f), (7.68, 12.3, r)),
            mbox('sight_wall_r', (8.32, 11.42, f), (8.58, 12.3, r)),
            box('sight_mount', 255, 315, 38, 53, 0.42, dz=SIGHT_DZ, dy=SIGHT_DY),
            {'name': 'sight_bev_l', 'from': [7.54 - 0.085, 12.4, f + 0.02], 'to': [7.54 + 0.085, 12.57, r - 0.02],
             'rotation': {'origin': [7.54, 12.48, (f + r) / 2], 'x': 0, 'y': 0, 'z': 45}},
            {'name': 'sight_bev_r', 'from': [8.46 - 0.085, 12.4, f + 0.02], 'to': [8.46 + 0.085, 12.57, r - 0.02],
             'rotation': {'origin': [8.46, 12.48, (f + r) / 2], 'x': 0, 'y': 0, 'z': 45}}]


def F(*a, **k): return fit(box(*a, **k), B)


def fillet(name, ix, iy, size, hw):
    zc, yc = Z(ix), Y(iy); h = size * 0.7071
    return {'name': name, 'from': [8 - hw, yc - h, zc - h], 'to': [8 + hw, yc + h, zc + h],
            'rotation': {'origin': [8.0, yc, zc], 'x': 45, 'y': 0, 'z': 0}}


IX0 = ix_of(0.0)    # front block split: the part behind z 0 is held to the base action-top height (ADS)


GRIP_HW = 0.5


def _base_elements():
    e = [
        *bevel(box('butt_plate', 10, 40, 70, 180, 0.5), 0.12, top=True, bottom=True),
        box('butt_pad', 4, 10, 76, 174, 0.46),
        *bevel(F('stock_top', 40, 140, 70, 140, 0.5), 0.14),
        box('stock_ribs', 45, 70, 82, 104, 0.53),
        rbox('stock_strut', (36, 166), (142, 182), 0.72, 0.48),
        *bevel(box('stock_mid', 106, 200, 140, 186, 0.5), 0.14, top=False, bottom=True),
        fillet('fil_s0', 140, 140, 0.4, 0.5),
        *bevel(F('body_upper', 140, 310, 52, 128, 0.55), 0.16),
        box('body_panel', 175, 300, 70, 100, 0.58),
        box('body_rail', 230, 330, 96, 101, 0.59),
        box('under_thumb', 200, 268, 170, 196, 0.5),
        fillet('fil_t0', 200, 128, 0.6, 0.5), fillet('fil_t1', 268, 128, 0.5, 0.5),
        fillet('fil_t2', 200, 170, 0.4, 0.5), fillet('fil_t3', 268, 170, 0.4, 0.5),
        rbox('grip', (286, 128), (274, 205), 1.1, 0.5),
        rbox('grip_panel', (284, 140), (277, 196), 0.7, 0.53),
        box('trigger', 306, 315, 130, 150, 0.08),
        *bevel(box('tg_front', 345, 376, 128, 195, 0.5), 0.12, top=False, bottom=True),
        *bevel(box('tg_bottom', 300, 345, 160, 195, 0.5), 0.12, top=False, bottom=True),
        fillet('fil_g0', 315, 160, 0.3, 0.5), fillet('fil_g1', 345, 160, 0.3, 0.5),
        *bevel(F('receiver', 310, 520, 52, 118, 0.58), 0.16),
        box('rcv_vents', 505, 545, 102, 112, 0.6),
        box('rcv_port', 380, 470, 92, 100, 0.6),
        box('rcv_low_rear', 310, 376, 118, 130, 0.58),
        rbox('forend_low', (376, 139), (622, 102), 1.2, 0.56),
        *bevel(F('front_block_rear', 520, IX0, 45, 118, 0.62), 0.16),
        *bevel(box('front_block', IX0, 620, 45, 118, 0.62), 0.16),
        box('front_rail', 528, 600, 40, 45, 0.3),
        box('barrel_neck', 620, 672, 72, 88, 0.2),
        box('neck_collar', 620, 630, 68, 92, 0.3),
        rbox('bracket', (612, 103), (632, 150), 0.55, 0.1),
        box('bracket_ring', 628, 688, 116, 124, 0.08),
        box('bracket_ring_b', 680, 688, 110, 128, 0.08),
    ]
    e += octa('barrel', 672, 800, 65, 92, 0.42)
    e += [box('barrel_collar', 672, 682, 63, 94, 0.45), box('barrel_tip', 784, 802, 66, 91, 0.45)]
    e += sight()
    e = stairs_for(e, ('stock_strut',), 3)
    e = stairs_for(e, ('forend_low',), 4)
    e = clamp_tops(e, B)
    e = adopt(e, 'grip_panel', 'grip', GRIP_HW + 0.015, 0.1, 0.88, 0.18, 0.82)
    e = machine(e, target=144, maxlen=2.2)
    e = tidy(e)
    e.append(_mag)
    mr = dict(_mag['rotation']); o = mr['origin']; L = _mag['to'][1] - _mag['from'][1]
    e.append({'name': 'mag_floor', 'from': [7.51, o[1] - L - 0.04, o[2] - 1.56], 'to': [8.49, o[1] - L + 0.2, o[2] + 1.56], 'rotation': dict(mr)})
    e.append({'name': 'mag_panel', 'from': [7.52, o[1] - L + 0.45, o[2] - 1.1], 'to': [8.48, o[1] - 0.5, o[2] + 1.1], 'rotation': dict(mr)})
    return e


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('mag_'):
        r = _mag['rotation']; o = r['origin']
        q = _rot(p, o, r['x'], inv=True)
        q = (q[0], o[1] - (o[1] - q[1]) / MAG_SHORTEN, q[2])
        x, y, z = _rot(q, o, r['x']); y -= MAG_DY
    elif name.startswith('sight_'):
        z -= SIGHT_DZ; y -= SIGHT_DY
        y = min(max(y, Y(38)), Y(8))
    ix, iy = ix_of(z), iy_of(y)
    return (XW0 - (x - 8) / LAT, CY - (ix - W / 2) / PPM, CZ - (iy - H / 2) / PPM)


INNER = (22, 22, 26, 255)
PURPLE, PURPLE_D, GREY, DARK = (92, 80, 104), (70, 60, 82), (74, 74, 78), (30, 30, 34)
BLOCKS = (('butt_pad', DARK), ('stock_ribs', GREY), ('stock_strut', GREY), ('stock_mid', GREY), ('under_thumb', GREY),
          ('grip', GREY), ('tg_', GREY), ('fil_', GREY), ('rcv_low_rear', GREY), ('forend_low', GREY), ('rcv_vents', DARK),
          ('rcv_port', DARK), ('body_rail', DARK), ('front_rail', DARK), ('barrel_neck', DARK), ('neck_collar', GREY),
          ('bracket', DARK), ('barrel', PURPLE_D), ('sight_mount', DARK), ('trigger', DARK), ('body_panel', PURPLE_D),
          ('butt_plate', PURPLE), ('stock_top', PURPLE), ('body_upper', PURPLE), ('receiver', PURPLE), ('front_block', PURPLE),
          ('sight', PURPLE), ('mag_panel', GREY), ('mag_', DARK))
PALETTE = 14
FLAT_TOL = 34
PALETTE_KEEP = [PURPLE, PURPLE_D, GREY, DARK]


_flat = FlatPainter(Path(__file__).parent, globals())


def _base_paint(e, fn, s, t):
    n = e['name']
    inner = (n == 'sight_floor' and fn == 'up' or n == 'sight_roof' and fn == 'down'
             or n == 'sight_wall_l' and fn == 'east' or n == 'sight_wall_r' and fn == 'west')
    if not inner and not (n.startswith('barrel') and fn == 'north'):
        for pre, c in BLOCKS:
            if n.startswith(pre):
                if n.startswith('receiver') and fn in ('east', 'west') and t > 0.72: c = GREY      # grey lower band
                if n.startswith('front_block') and fn in ('east', 'west') and t > 0.6: c = GREY
                return c + (255,)
    fp = _flat(e, fn, s, t)
    if fp is not None: return fp
    if n == 'sight_floor' and fn == 'up' or n == 'sight_roof' and fn == 'down':
        return INNER
    if n == 'sight_wall_l' and fn == 'east' or n == 'sight_wall_r' and fn == 'west':
        return INNER
    if n == 'barrel' and fn == 'north':
        if math.hypot(s - .5, t - .5) < 0.24: return (10, 10, 11, 255)
    return None


T = 18

# Identity pass: explicit per-face pixel paint, with real depth for signature apertures.
from _identity import enrich_geometry
IDENTITY_ID = 'inverness_sr2'
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
