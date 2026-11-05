"""W325 Armillary PSu (rare scout rifle, Precision) over base distant_relation.

Authored in rip-image coordinates of the calibrated nx view (proj_cache/nx_albedo.png, 800 px/m, muzzle right) and
converted to model px by a two-scale station map: trigger ix 302 -> z 7.47 (base trigger), rear 0.0317 / forward 0.0289
model px per image px; vertical anchored on the receiver top (iy 58 -> y 11.15, the base action top) so the base ADS line
(aim tip y 11.63..11.79 at z 4.3) clears the receiver; the bore therefore sits at y 9.85 (base 10.36).  Lateral 21 px/m.
Contract moves (projection undoes them in model2world):
  * the reflex sight is moved 2.36 px forward and 0.10 down onto the base W151 sight box (z 4.3..7.08), the rip mounts
    it above the trigger where it would sit in the ADS camera; its long light arm to the receiver is dropped;
  * the large magazine (behind the grip like the base) is shortened 25% along its own axis.
"""
import json, math
from pathlib import Path
from _w3lib import bevel, clamp_tops, FlatPainter, fit, machine, face_pt, blob, adopt, tidy, stairs_for
B = 'distant_relation'

_M = json.loads((Path(__file__).parent / 'proj_cache/manifest.json').read_text())
_V = _M['views']['nx']; PPM = _M['ppm']; W, H = _V['res']; CX, CY, CZ = _V['centre']

TRIG_IX, TRIG_Z, REAR_K, FRONT_K = 302, 7.47, 0.0317, 0.0289
ANCH_IY, ANCH_Y, VK = 58, 11.15, 0.0289
LAT = 21.0
MAG_SHORTEN = 0.75
SIGHT_DZ, SIGHT_DY = -2.36, -0.10


def Z(ix): return TRIG_Z + (TRIG_IX - ix) * (REAR_K if ix <= TRIG_IX else FRONT_K)
def Y(iy): return ANCH_Y - (iy - ANCH_IY) * VK
def ix_of(z): return TRIG_IX - (z - TRIG_Z) / (REAR_K if z >= TRIG_Z else FRONT_K)
def iy_of(y): return ANCH_IY - (y - ANCH_Y) / VK


def box(name, ix0, ix1, iy0, iy1, hw, xc=8.0, dz=0.0, dy=0.0):
    z0, z1 = sorted((Z(ix0), Z(ix1))); y0, y1 = sorted((Y(iy0), Y(iy1)))
    return {'name': name, 'from': [xc - hw, y0 + dy, z0 + dz], 'to': [xc + hw, y1 + dy, z1 + dz]}


def mbox(name, f, t): return {'name': name, 'from': list(f), 'to': list(t)}


def rbox(name, top, bot, width, hw, shorten=1.0, xc=8.0):
    zt, yt = Z(top[0]), Y(top[1]); zb, yb = Z(bot[0]), Y(bot[1])
    dz, dy = zb - zt, yb - yt; L = math.hypot(dz, dy) * shorten; a = math.degrees(math.atan2(-dz, -dy))
    return {'name': name, 'from': [xc - hw, yt - L, zt - width / 2], 'to': [xc + hw, yt, zt + width / 2],
            'rotation': {'origin': [xc, yt, zt], 'x': round(a, 4), 'y': 0, 'z': 0}}


def _rot(p, o, a, inv=False):
    a = math.radians(-a if inv else a); c, s = math.cos(a), math.sin(a)
    y, z = p[1] - o[1], p[2] - o[2]
    return (p[0], o[1] + y * c - z * s, o[2] + y * s + z * c)


_mag = rbox('mag_body', (197, 182), (178, 290), 4.3, 0.42, MAG_SHORTEN)


def octa(name, ix0, ix1, iy0, iy1, hw):
    b = box(name, ix0, ix1, iy0, iy1, hw)
    yc = (b['from'][1] + b['to'][1]) / 2; zc = (b['from'][2] + b['to'][2]) / 2; r = hw * 0.93
    return [b, {'name': name + '_r45', 'from': [8 - r, yc - r, b['from'][2] + 0.02], 'to': [8 + r, yc + r, b['to'][2] - 0.02],
                'rotation': {'origin': [8.0, yc, zc], 'x': 0, 'y': 0, 'z': 45}}]


def leg(name, start, end, xs, splay):
    zs, ys = Z(start[0]), Y(start[1]); ze, ye = Z(end[0]), Y(end[1])
    L = math.hypot(ze - zs, ye - ys); a = -math.degrees(math.atan2(ys - ye, zs - ze))
    return {'name': name, 'from': [xs - 0.11, ys - 0.11, zs - L], 'to': [xs + 0.11, ys + 0.11, zs],
            'rotation': {'origin': [xs, ys, zs], 'x': round(a, 4), 'y': splay, 'z': 0}}


def sight():
    # rip housing ix 240..330, iy 8..52; window opening around the base ADS line (y ~11.85)
    f, r = Z(330) + SIGHT_DZ, Z(240) + SIGHT_DZ
    s = [mbox('sight_floor', (7.4, 11.12, f), (8.6, 11.45, r)),
         mbox('sight_roof', (7.4, 12.3, f), (8.6, 12.62, r)),
         mbox('sight_wall_l', (7.4, 11.45, f), (7.66, 12.3, r)),
         mbox('sight_wall_r', (8.34, 11.45, f), (8.6, 12.3, r)),
         mbox('sight_dial', (7.18, 11.5, f + 1.25), (7.4, 12.3, f + 2.05)),
         mbox('sight_dial_s', (7.22, 11.62, f + 0.25), (7.4, 12.04, f + 0.7)),
         mbox('sight_hood', (7.45, 12.62, f - 0.02), (8.55, 12.74, f + 0.9)),
         mbox('sight_fin', (7.55, 11.6, r), (8.45, 12.25, r + 0.18)),
         mbox('sight_base', (7.55, 10.98, f + 0.4), (8.45, 11.12, r - 0.3))]
    for k, xc in enumerate((7.4 + 0.12, 8.6 - 0.12)):
        s.append({'name': f'sight_bev{k}', 'from': [xc - 0.085, 12.62 - 0.12 - 0.085, f + 0.02], 'to': [xc + 0.085, 12.62 - 0.12 + 0.085, r - 0.02],
                  'rotation': {'origin': [xc, 12.5, (f + r) / 2], 'x': 0, 'y': 0, 'z': 45}})
    for e in s: e['fz'] = True
    # fin: keep the rear eyepiece frame open in the middle -> split into a ring
    s[7] = mbox('sight_fin_t', (7.4, 12.12, r), (8.6, 12.3, r + 0.16))
    s.append(mbox('sight_fin_b', (7.4, 11.45, r), (8.6, 11.6, r + 0.16)))
    return s


def F(*a, **k): return fit(box(*a, **k), B)


def fillet(name, ix, iy, size, hw):
    zc, yc = Z(ix), Y(iy); h = size * 0.7071
    return {'name': name, 'from': [8 - hw, yc - h, zc - h], 'to': [8 + hw, yc + h, zc + h],
            'rotation': {'origin': [8.0, yc, zc], 'x': 45, 'y': 0, 'z': 0}}


def teeth(prefix, z0, z1, n, y0, y1, hw):
    out = []; step = (z1 - z0) / n
    for i in range(n):
        za = z0 + i * step + step * 0.25
        out.append({'name': f'{prefix}_{i}', 'from': [8 - hw, y0, za], 'to': [8 + hw, y1, za + step * 0.5]})
    return out


GRIP_HW = 0.5


def _base_elements():
    e = [
        *bevel(box('butt_plate', 8, 25, 72, 170, 0.6), 0.14, top=True, bottom=False),
        box('butt_pad', 4, 10, 78, 166, 0.55),
        rbox('butt_toe', (30, 168), (20, 210), 0.55, 0.55),
        *bevel(F('stock_cap', 25, 60, 72, 95, 0.58), 0.14),
        box('stock_upper', 60, 137, 85, 95, 0.52),
        box('stock_slot_rim', 60, 137, 83, 85, 0.54),
        *bevel(box('stock_body', 25, 125, 95, 176, 0.52), 0.14, top=False, bottom=True),
        box('stock_panel', 42, 112, 104, 160, 0.55),
        box('stock_vent', 52, 92, 160, 166, 0.54),
        *bevel(F('upper_block', 137, 165, 58, 105, 0.6), 0.14),
        *bevel(F('spine', 165, 330, 60, 75, 0.5), 0.1),
        box('mid_rear', 245, 330, 75, 95, 0.53),
        box('mid_body', 125, 330, 95, 130, 0.53),
        box('mid_strip', 125, 330, 99, 104, 0.56),
        *bevel(box('web_rear', 125, 190, 130, 185, 0.5), 0.14, top=False, bottom=True),
        box('web_under', 190, 258, 175, 187, 0.5),
        fillet('fil_t0', 190, 130, 0.5, 0.5), fillet('fil_t1', 258, 130, 0.5, 0.5),
        fillet('fil_t2', 190, 175, 0.4, 0.5), fillet('fil_t3', 258, 175, 0.4, 0.5),
        rbox('grip', (284, 130), (266, 208), 1.15, 0.5),
        rbox('grip_panel', (282, 140), (269, 200), 0.75, 0.53),
        *bevel(box('tg_front', 340, 366, 135, 200, 0.5), 0.12, top=False, bottom=True),
        *bevel(box('tg_bottom', 296, 340, 170, 200, 0.5), 0.12, top=False, bottom=True),
        fillet('fil_g0', 306, 170, 0.35, 0.5), fillet('fil_g1', 340, 170, 0.35, 0.5),
        box('trigger', 300, 306, 140, 162, 0.08),
        box('rcv_lower', 330, 430, 100, 150, 0.6),
        box('rcv_lower_plate', 345, 420, 108, 142, 0.63),
        *bevel(F('rcv_top', 330, 600, 58, 100, 0.68), 0.16),
        box('rcv_band', 330, 600, 78, 84, 0.7),
        box('eject_port', 440, 520, 86, 98, 0.7),
        box('ch_handle', 395, 410, 62, 74, 0.74),
        *bevel(box('forend', 430, 600, 100, 150, 0.66), 0.16, top=False, bottom=True),
        box('forend_rib', 440, 590, 118, 126, 0.69),
        F('rail', 500, 640, 50, 58, 0.35),
        F('rail_rib', 565, 622, 43, 50, 0.3),
        box('front_post', 615, 625, 34, 43, 0.12),
        box('top_bar', 620, 712, 78, 86, 0.18),
        box('top_bar_clamp', 700, 712, 74, 90, 0.24),
        box('bipod_mount', 574, 606, 140, 158, 0.42),
        box('bipod_pin', 584, 596, 146, 152, 0.5),
        leg('bipod_l', (592, 152), (732, 214), 7.72, 7.0),
        leg('bipod_r', (592, 152), (732, 214), 8.28, -7.0),
    ]
    e += teeth('rail_t', Z(640), Z(500), 6, 0, 0, 0.38)
    rt = [x for x in e if x['name'] == 'rail'][0]
    for x in e:
        if x['name'].startswith('rail_t_'): x['from'][1] = rt['to'][1] - 0.06; x['to'][1] = rt['to'][1] + 0.08
    e += octa('shroud', 600, 737, 85, 122, 0.46)
    e += [box('shroud_ring0', 640, 646, 84, 123, 0.49), box('shroud_ring1', 690, 696, 84, 123, 0.49)]
    e += octa('muzzle', 737, 852, 92, 120, 0.37)
    e += [box('muzzle_cap', 846, 856, 94, 118, 0.4), box('muzzle_collar', 737, 750, 90, 122, 0.41)]
    e += sight()
    e = stairs_for(e, ('butt_toe',), 3)
    e = clamp_tops(e, B)
    e = adopt(e, 'grip_panel', 'grip', GRIP_HW + 0.015, 0.1, 0.88, 0.18, 0.82)
    e = machine(e, target=144)
    e = tidy(e)
    e.append(_mag)
    e.append(box('mag_latch', 100, 122, 236, 256, 0.3))
    m = e[-1]; m['name'] = 'mag_latch'
    o = _mag['rotation']['origin']; L = _mag['to'][1] - _mag['from'][1]
    m['from'] = [7.7, o[1] - L * 0.62, o[2] + 2.15]; m['to'] = [8.3, o[1] - L * 0.45, o[2] + 2.45]
    m['rotation'] = dict(_mag['rotation'])
    mr = dict(_mag['rotation'])
    e.append({'name': 'mag_floor', 'from': [7.56, o[1] - L - 0.02, o[2] - 2.15], 'to': [8.44, o[1] - L + 0.22, o[2] + 2.15], 'rotation': dict(mr)})
    e.append({'name': 'mag_panel', 'from': [7.55, o[1] - L + 0.5, o[2] - 1.6], 'to': [8.45, o[1] - 0.6, o[2] + 1.6], 'rotation': dict(mr)})
    for x in e: x.pop('fz', None)
    return e


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('mag_'):
        r = _mag['rotation']; o = r['origin']
        q = _rot(p, o, r['x'], inv=True)
        q = (q[0], o[1] - (o[1] - q[1]) / MAG_SHORTEN, q[2])
        x, y, z = _rot(q, o, r['x'])
    elif name.startswith('sight_'):
        z -= SIGHT_DZ; y -= SIGHT_DY
    ix, iy = ix_of(z), iy_of(y)
    return (-(x - 8) / LAT, CY - (ix - W / 2) / PPM, CZ - (iy - H / 2) / PPM)


INNER = (22, 24, 28, 255)
NAVY, WHITE, GREYB = (36, 50, 82), (210, 212, 216), (140, 146, 158)
CAMO = ('rcv_top', 'forend', 'upper_block', 'stock_cap', 'butt_plate', 'sight_roof', 'sight_wall', 'sight_floor',
        'sight_hood', 'sight_bev', 'rcv_lower_plate')
PALETTE = 16
FLAT_TOL = 30
PALETTE_KEEP = [NAVY, WHITE, GREYB]


_flat = FlatPainter(Path(__file__).parent, globals())


def _base_paint(e, fn, s, t):
    n = e['name']
    if n.startswith(CAMO) and not (n == 'sight_floor' and fn == 'up' or n == 'sight_roof' and fn == 'down'
                                   or n == 'sight_wall_l' and fn == 'east' or n == 'sight_wall_r' and fn == 'west'):
        v = blob(face_pt(e, fn, s, t), 0.9, 1.3)
        return (NAVY if v > 0.05 else WHITE if v < -0.35 else GREYB) + (255,)
    if n == 'rcv_band': return (214, 216, 220, 255)
    if n == 'eject_port' and fn in ('east', 'west'): return (18, 19, 22, 255)
    if n.startswith('stock_slot_rim'): return (196, 198, 204, 255)
    fp = _flat(e, fn, s, t)
    if fp is not None: return fp
    if n == 'sight_floor' and fn == 'up' or n == 'sight_roof' and fn == 'down':
        return INNER
    if n == 'sight_wall_l' and fn == 'east' or n == 'sight_wall_r' and fn == 'west':
        return INNER
    if n.startswith('sight_fin') and fn in ('up', 'down'):
        return INNER
    if n == 'muzzle' and fn == 'north':
        d = math.hypot(s - .5, t - .5)
        if d < 0.2: return (10, 10, 11, 255)
    if n == 'shroud' and fn == 'north':
        return (20, 20, 22, 255)
    return None


T = 18

# Identity pass: explicit per-face pixel paint, with real depth for signature apertures.
from _identity import enrich_geometry
IDENTITY_ID = 'armillary_psu'
T = 18
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
