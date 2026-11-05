"""W325 Sonata-48 (rare scout rifle, Precision, SUROS) over base distant_relation.

Authored in rip-image coordinates of the calibrated nx view (proj_cache/nx_albedo.png, 800 px/m, muzzle right),
converted by a station map: trigger ix 302 -> z 7.47 (base trigger), rear 0.031 / forward 0.033 model px per image px
(the rip is a short bullpup: muzzle spike ends z -7.3, base -8.26; butt z 16.6, base 17.39); vertical 0.031 anchored on
the receiver top (iy 43 -> y 11.15, the base action top) so the base ADS line clears it (bore y 9.93, trigger y 8.6 =
base trigger height).  Lateral 20 px/m.
Contract moves (undone in model2world):
  * magazine (vertical box behind the grip) moved 1.0 px forward and shortened 15% from its top so it sits closer to the
    base moving-magazine box (z 9.72..13.0, floor 5.7);
  * the rear peep sight is widened/raised to a ring around the base W151 ADS window (x 7.72..8.28, y 11.5..12.25);
    the kept W148 aim tip (z 4.3) is seen through it.
"""
import json, math
from pathlib import Path
from _w3lib import bevel, clamp_tops, FlatPainter, fit, machine, face_pt, adopt, tidy
B = 'distant_relation'

_M = json.loads((Path(__file__).parent / 'proj_cache/manifest.json').read_text())
_V = _M['views']['nx']; PPM = _M['ppm']; W, H = _V['res']; CX, CY, CZ = _V['centre']

TRIG_IX, TRIG_Z, REAR_K, FRONT_K = 302, 7.47, 0.031, 0.033
ANCH_IY, ANCH_Y, VK = 43, 11.15, 0.031
LAT = 20.0
MAG_TOP_IY, MAG_K, MAG_DZ = 128, 0.85, -1.0


def Z(ix): return TRIG_Z + (TRIG_IX - ix) * (REAR_K if ix <= TRIG_IX else FRONT_K)
def Y(iy): return ANCH_Y - (iy - ANCH_IY) * VK
def ix_of(z): return TRIG_IX - (z - TRIG_Z) / (REAR_K if z >= TRIG_Z else FRONT_K)
def iy_of(y): return ANCH_IY - (y - ANCH_Y) / VK


def box(name, ix0, ix1, iy0, iy1, hw, xc=8.0):
    z0, z1 = sorted((Z(ix0), Z(ix1))); y0, y1 = sorted((Y(iy0), Y(iy1)))
    return {'name': name, 'from': [xc - hw, y0, z0], 'to': [xc + hw, y1, z1]}


def mbox(name, f, t): return {'name': name, 'from': list(f), 'to': list(t)}


def rbox(name, top, bot, width, hw, xc=8.0):
    zt, yt = Z(top[0]), Y(top[1]); zb, yb = Z(bot[0]), Y(bot[1])
    dz, dy = zb - zt, yb - yt; L = math.hypot(dz, dy); a = math.degrees(math.atan2(-dz, -dy))
    return {'name': name, 'from': [xc - hw, yt - L, zt - width / 2], 'to': [xc + hw, yt, zt + width / 2],
            'rotation': {'origin': [xc, yt, zt], 'x': round(a, 4), 'y': 0, 'z': 0}}


MAG_Y0 = Y(MAG_TOP_IY)
def _mag_y(y): return MAG_Y0 - (MAG_Y0 - y) * MAG_K


def magbox(name, ix0, ix1, iy0, iy1, hw):
    b = box(name, ix0, ix1, iy0, iy1, hw)
    b['from'] = [b['from'][0], _mag_y(b['from'][1]), b['from'][2] + MAG_DZ]
    b['to'] = [b['to'][0], _mag_y(b['to'][1]), b['to'][2] + MAG_DZ]
    return b


def octa(name, ix0, ix1, iy0, iy1, hw):
    b = box(name, ix0, ix1, iy0, iy1, hw)
    yc = (b['from'][1] + b['to'][1]) / 2; zc = (b['from'][2] + b['to'][2]) / 2; r = hw * 0.93
    return [b, {'name': name + '_r45', 'from': [8 - r, yc - r, b['from'][2] + 0.02], 'to': [8 + r, yc + r, b['to'][2] - 0.02],
                'rotation': {'origin': [8.0, yc, zc], 'x': 0, 'y': 0, 'z': 45}}]


RING_DZ = -0.84      # peep ring moved forward into the base scope zone (base top 12.62 there) so ADS stays open


def F(*a, **k): return fit(box(*a, **k), B)


def fillet(name, ix, iy, size, hw):
    zc, yc = Z(ix), Y(iy); h = size * 0.7071
    return {'name': name, 'from': [8 - hw, yc - h, zc - h], 'to': [8 + hw, yc + h, zc + h],
            'rotation': {'origin': [8.0, yc, zc], 'x': 45, 'y': 0, 'z': 0}}


GRIP_HW = 0.5


def _base_elements():
    zf, zr = Z(318) + RING_DZ, Z(292) + RING_DZ
    e = [
        rbox('butt_plate', (50, 69), (21, 158), 0.55, 0.36),
        rbox('butt_pad', (44, 72), (16, 156), 0.25, 0.4),
        box('butt_link', 52, 78, 68, 128, 0.45),
        *bevel(box('body_rear', 78, 180, 75, 128, 0.64), 0.16, top=False, bottom=True),
        box('body_rear_panel', 85, 172, 82, 102, 0.67),
        *bevel(F('handle_rear', 110, 143, 48, 75, 0.5), 0.12),
        *bevel(F('handle_top', 143, 180, 48, 55, 0.5), 0.1),
        box('handle_low', 143, 180, 68, 75, 0.5),
        fillet('fil_h0', 143, 55, 0.25, 0.5), fillet('fil_h1', 180, 55, 0.25, 0.5),
        *bevel(F('body_upper', 180, 283, 43, 75, 0.64), 0.16),
        box('body_mid', 180, 545, 75, 115, 0.62),
        box('red_band', 180, 545, 82, 100, 0.65),
        box('logo_slot', 218, 262, 81, 88, 0.66),
        *bevel(F('top_front', 390, 553, 43, 75, 0.64), 0.16),
        *bevel(F('sight_house', 283, 390, 38, 75, 0.6), 0.14),
        box('sight_vents', 300, 370, 50, 70, 0.62),
        F('sight_bar', 322, 365, 31, 38, 0.2),
        mbox('sight_ring_l', (7.5, Y(38), zf), (7.72, 12.25, zr)),
        mbox('sight_ring_r', (8.28, Y(38), zf), (8.5, 12.25, zr)),
        mbox('sight_ring_t', (7.5, 12.25, zf), (8.5, 12.45, zr)),
        {'name': 'sight_ring_bl', 'from': [7.61 - 0.08, 12.36 - 0.08, zf + 0.02], 'to': [7.61 + 0.08, 12.36 + 0.08, zr - 0.02],
         'rotation': {'origin': [7.61, 12.36, (zf + zr) / 2], 'x': 0, 'y': 0, 'z': 45}},
        {'name': 'sight_ring_br', 'from': [8.39 - 0.08, 12.36 - 0.08, zf + 0.02], 'to': [8.39 + 0.08, 12.36 + 0.08, zr - 0.02],
         'rotation': {'origin': [8.39, 12.36, (zf + zr) / 2], 'x': 0, 'y': 0, 'z': 45}},
        rbox('grip', (263, 113), (244, 216), 1.15, 0.5),
        rbox('grip_panel', (260, 125), (247, 205), 0.75, 0.53),
        box('grip_heel', 222, 246, 192, 217, 0.47),
        box('trigger', 297, 305, 115, 134, 0.08),
        box('tg_bar', 286, 330, 132, 136, 0.12),
        box('lower_block', 345, 390, 115, 126, 0.58),
        *bevel(box('handguard', 390, 520, 115, 133, 0.72), 0.14, top=False, bottom=True),
        box('hg_rib0', 410, 418, 112, 134, 0.74), box('hg_rib1', 445, 453, 112, 134, 0.74),
        box('hg_rib2', 480, 488, 112, 134, 0.74),
        box('front_cap', 520, 547, 72, 112, 0.66),
        box('front_vent', 524, 543, 92, 102, 0.68),
    ]
    e += octa('muzzle', 547, 678, 65, 100, 0.46)
    e += [box('muzzle_collar', 547, 556, 63, 102, 0.5), box('muzzle_tip', 670, 680, 66, 99, 0.49)]
    e += octa('spike', 678, 748, 72, 91, 0.25)
    e = clamp_tops(e, B)
    e = adopt(e, 'grip_panel', 'grip', GRIP_HW + 0.015, 0.1, 0.88, 0.18, 0.82)
    e = adopt(e, 'butt_pad', 'butt_plate', 0.4, 0.03, 0.97, 1.0, 1.45)
    e = machine(e, target=140, maxlen=2.0)
    e = tidy(e)
    e += [magbox('mag_body', 70, 168, 128, 215, 0.5), magbox('mag_toe', 92, 166, 215, 238, 0.5),
          magbox('mag_heel', 63, 70, 195, 215, 0.42), magbox('mag_rib', 88, 150, 140, 205, 0.53),
          magbox('mag_lip', 72, 166, 128, 134, 0.53)]
    return e


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('mag_'):
        z -= MAG_DZ; y = MAG_Y0 - (MAG_Y0 - y) / MAG_K
    elif name.startswith('sight_ring'):
        y = min(y, Y(8)); z -= RING_DZ
    ix, iy = ix_of(z), iy_of(y)
    return (-(x - 8) / LAT, CY - (ix - W / 2) / PPM, CZ - (iy - H / 2) / PPM)


MINTG, RED_, DARK_, WHITE_ = (178, 196, 190), (150, 36, 40), (52, 54, 56), (220, 222, 224)
BLOCKS = (('butt', DARK_), ('handle', DARK_), ('fil_h', DARK_), ('grip', DARK_), ('tg_', DARK_), ('trigger', WHITE_),
          ('lower_block', DARK_), ('handguard', DARK_), ('hg_rib', (36, 38, 40)), ('front_cap', DARK_), ('front_vent', (30, 30, 32)),
          ('sight_bar', DARK_), ('sight_vents', DARK_), ('sight_ring', MINTG), ('red_band', RED_), ('body_rear_panel', MINTG),
          ('mag_rib', (40, 42, 44)), ('mag_', DARK_), ('body_mid', RED_), ('body_rear', RED_), ('body_upper', MINTG),
          ('top_front', MINTG), ('sight_house', DARK_), ('muzzle_collar', WHITE_), ('muzzle_tip', WHITE_), ('spike', WHITE_))
PALETTE = 18
FLAT_TOL = 30
PALETTE_KEEP = [MINTG, RED_, DARK_, WHITE_]


_flat = FlatPainter(Path(__file__).parent, globals())


def _base_paint(e, fn, s, t):
    n = e['name']
    if n.startswith('logo_slot') or (n.startswith(('red_band', 'body_mid')) and fn in ('east', 'west')):
        p = face_pt(e, fn, s, t); ix, iy = ix_of(p[2]), iy_of(p[1])
        if 278 <= ix <= 345 and 88 <= iy <= 100:                       # SUROS: flat mint letter strokes on red
            k = int((ix - 278) / 2.6)
            if 300 <= ix and (k % 4 != 3) and (90 <= iy <= 98) and (iy <= 91.5 or iy >= 96.5 or k % 4 == 0 or k % 4 == 2): return MINTG + (255,)
            if ix < 300 and 89 <= iy <= 99 and (iy >= 93 or ix > 286): return MINTG + (255,)
            return RED_ + (255,)
        if 218 <= ix <= 262 and 81 <= iy <= 88: return (24, 24, 26, 255)
        if n.startswith('body_mid') and fn in ('east', 'west') and iy > 104: return DARK_ + (255,)
    if not (n == 'spike' and fn == 'north') and not (n.startswith('sight_ring') and fn in ('east', 'west', 'down')):
        for pre, c in BLOCKS:
            if n.startswith(pre): return c + (255,)
    if n.startswith('sight_ring') and fn in ('north', 'south', 'east', 'west', 'down', 'up'):
        inner = (n == 'sight_ring_l' and fn == 'east') or (n == 'sight_ring_r' and fn == 'west') or (n == 'sight_ring_t' and fn == 'down')
        if inner: return (24, 25, 28, 255)
        return None
    if n == 'spike' and fn == 'north':
        d = math.hypot(s - .5, t - .5)
        if d < 0.25: return (12, 12, 13, 255)
    return None


T = 20

# Identity pass: explicit per-face pixel paint, with real depth for signature apertures.
from _identity import enrich_geometry
IDENTITY_ID = 'sonata_48'
T = 20
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
