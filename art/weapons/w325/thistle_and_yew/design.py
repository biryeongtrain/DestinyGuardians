"""W325 Thistle and Yew (common scout rifle, Precision) over base distant_relation (W151 scope layout).

Authoring frame: every solid is written in rip-image coordinates of the calibrated nx view (proj_cache/nx_albedo.png,
800 px/m, muzzle right) and converted to model px by a two-scale station map anchored at the trigger (ix 318 -> z 7.47,
the base trigger) and the bore (iy 48.5 -> y 10.36, the base bore).  Rear of the trigger 0.030 px/img-px (butt ends at
z 16.7, base 17.39), forward 0.028 (muzzle -8.27 = base).  Lateral 25 model px per metre.  The rip has no optic: the
scope is authored to the base W151 scope box (open tube z 4.21..7.09, y 11.23..12.53) so the kept W148 aim tip lines up,
and is painted with specials.  The magazine (behind the grip like the base) is shortened 15% along its own axis so its
floor ends at the base magazine floor height (y 5.7); the projection undoes that shortening (part transform).
"""
import json, math
from pathlib import Path
from _w3lib import bevel, clamp_tops, FlatPainter, fit, machine, adopt, tidy
B = 'distant_relation'

_M = json.loads((Path(__file__).parent / 'proj_cache/manifest.json').read_text())
_V = _M['views']['nx']; PPM = _M['ppm']; W, H = _V['res']; CX, CY, CZ = _V['centre']

TRIG_IX, TRIG_Z, REAR_K, FRONT_K = 318, 7.47, 0.030, 0.028
BORE_IY, BORE_Y, VK = 48.5, 10.36, 0.028
LAT = 25.0          # model px per metre across the gun
MAG_SHORTEN = 0.85


def Z(ix): return TRIG_Z + (TRIG_IX - ix) * (REAR_K if ix <= TRIG_IX else FRONT_K)
def Y(iy): return BORE_Y - (iy - BORE_IY) * VK
def ix_of(z): return TRIG_IX - (z - TRIG_Z) / (REAR_K if z >= TRIG_Z else FRONT_K)
def iy_of(y): return BORE_IY - (y - BORE_Y) / VK


def box(name, ix0, ix1, iy0, iy1, hw, xc=8.0, **kw):
    z0, z1 = sorted((Z(ix0), Z(ix1))); y0, y1 = sorted((Y(iy0), Y(iy1)))
    e = {'name': name, 'from': [xc - hw, y0, z0], 'to': [xc + hw, y1, z1]}; e.update(kw); return e


def mbox(name, f, t, **kw):
    e = {'name': name, 'from': list(f), 'to': list(t)}; e.update(kw); return e


def rbox(name, top, bot, width, hw, shorten=1.0, xc=8.0):
    """Bar from image point top to bot (axis), given model width across the axis; rotated about x at the top."""
    zt, yt = Z(top[0]), Y(top[1]); zb, yb = Z(bot[0]), Y(bot[1])
    dz, dy = zb - zt, yb - yt; L = math.hypot(dz, dy) * shorten; a = math.degrees(math.atan2(-dz, -dy))
    return {'name': name, 'from': [xc - hw, yt - L, zt - width / 2], 'to': [xc + hw, yt, zt + width / 2],
            'rotation': {'origin': [xc, yt, zt], 'x': round(a, 4), 'y': 0, 'z': 0}}


MAG_TOP, MAG_BOT = (165, 125), (212, 228)
_mag = rbox('mag_body', MAG_TOP, MAG_BOT, 2.2, 0.42, MAG_SHORTEN)


def _rot(p, o, a, inv=False):
    a = math.radians(-a if inv else a); c, s = math.cos(a), math.sin(a)
    y, z = p[1] - o[1], p[2] - o[2]
    return (p[0], o[1] + y * c - z * s, o[2] + y * s + z * c)


# scope: base W151 box (do not move: ADS aim tip of the base is kept by the pack builder)
SZ0, SZ1 = 4.21, 7.09


def scope():
    s = []
    s.append(mbox('sc_floor', (7.61, 11.23, SZ0), (8.39, 11.49, SZ1)))
    s.append(mbox('sc_ceiling', (7.61, 12.27, SZ0), (8.39, 12.53, SZ1)))
    s.append(mbox('sc_wall_in_l', (7.61, 11.49, SZ0), (7.72, 12.27, SZ1)))
    s.append(mbox('sc_wall_in_r', (8.28, 11.49, SZ0), (8.39, 12.27, SZ1)))
    s.append(mbox('sc_wall_out_l', (7.46, 11.43, SZ0 + 0.3), (7.61, 12.34, SZ1 - 0.25)))
    s.append(mbox('sc_wall_out_r', (8.39, 11.43, SZ0 + 0.3), (8.54, 12.34, SZ1 - 0.25)))
    for tag, z0, z1 in (('obj', 3.7, SZ0 + 0.3), ('ocu', SZ1 - 0.25, 7.5)):
        s.append(mbox(f'sc_{tag}_top', (7.4, 12.53, z0), (8.6, 12.56, z1)))
        s.append(mbox(f'sc_{tag}_bot', (7.4, 11.1, z0), (8.6, 11.23, z1)))
        s.append(mbox(f'sc_{tag}_l', (7.4, 11.23, z0), (7.61, 12.53, z1)))
        s.append(mbox(f'sc_{tag}_r', (8.39, 11.23, z0), (8.6, 12.53, z1)))
    s.append(mbox('sc_turret', (7.8, 12.53, 5.35), (8.2, 12.74, 5.95)))
    s.append(mbox('sc_turret_side', (8.54, 11.65, 5.35), (8.78, 12.11, 5.95)))
    for tag, z0, z1, x0, x1, y0, y1, c in (('tube', SZ0 + 0.3, SZ1 - 0.25, 7.46, 8.54, 11.43, 12.53, 0.12),
                                          ('obj', 3.7, SZ0 + 0.3, 7.4, 8.6, 11.1, 12.56, 0.14),
                                          ('ocu', SZ1 - 0.25, 7.5, 7.4, 8.6, 11.1, 12.56, 0.14)):
        h = c * 0.7071
        for k, (xc, yc) in enumerate(((x0 + c, y1 - c), (x1 - c, y1 - c), (x0 + c, y0 + c), (x1 - c, y0 + c))):
            s.append({'name': f'sc_{tag}_bev{k}', 'from': [xc - h, yc - h, z0 + 0.01], 'to': [xc + h, yc + h, z1 - 0.01],
                      'rotation': {'origin': [xc, yc, (z0 + z1) / 2], 'x': 0, 'y': 0, 'z': 45}})
    for i, z0 in enumerate((4.55, 6.3)):
        s.append(mbox(f'sc_mount_{i}', (7.5, 11.0, z0), (8.5, 11.23, z0 + 0.42)))
    return s


def F(*a, **k): return fit(box(*a, **k), B)


def fillet(name, ix, iy, size, hw):
    """45-degree rod along x filling the corner of an opening at image point (ix, iy)."""
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
        # stock (polymer) with two real thumbholes: rear ix 50-103 / iy 55-110, front ix 200-250 / iy 55-98
        box('butt_pad', 12, 26, 33, 170, 0.6),
        box('butt_rubber', 8, 12, 40, 166, 0.56),
        box('stock_post', 28, 50, 35, 168, 0.57),
        *bevel(F('stock_top', 50, 250, 35, 55, 0.57), 0.16),
        *bevel(F('cheek_pad', 75, 165, 21, 35, 0.5), 0.12),
        box('stock_web', 103, 200, 55, 110, 0.57),
        box('web_plate', 125, 178, 60, 100, 0.6),
        *bevel(F('stock_low_rear', 50, 130, 110, 166, 0.57), 0.16, top=False, bottom=True),
        *bevel(F('stock_low_mid', 130, 200, 110, 152, 0.57), 0.14, top=False, bottom=True),
        box('stock_low_front', 200, 250, 98, 150, 0.57),
        box('strap_band', 100, 110, 34, 168, 0.6),
        box('sling_loop', 30, 44, 168, 176, 0.2),
        fillet('fil_r0', 50, 55, 0.3, 0.57), fillet('fil_r1', 103, 55, 0.3, 0.57),
        fillet('fil_r2', 50, 110, 0.3, 0.57), fillet('fil_r3', 103, 110, 0.3, 0.57),
        fillet('fil_f0', 200, 55, 0.4, 0.57), fillet('fil_f1', 250, 55, 0.3, 0.57),
        fillet('fil_f2', 200, 98, 0.5, 0.57), fillet('fil_f3', 250, 98, 0.4, 0.57),
        # grip + trigger group
        rbox('grip', (268, 92), (254, 176), 1.3, 0.5),
        rbox('grip_insert', (266, 104), (256, 168), 0.75, 0.53),
        *bevel(F('lower_rcv', 250, 430, 60, 85, 0.55), 0.12, top=False, bottom=True),
        box('tg_bottom', 300, 345, 104, 109, 0.16),
        box('tg_front', 339, 345, 85, 104, 0.16),
        box('tg_back', 298, 304, 96, 106, 0.16),
        box('trigger', 314, 321, 85, 102, 0.07),
        rbox('trigger_tip', (321, 96), (325, 104), 0.14, 0.07),
        # receiver (blue) + rail + charging handle (tops lowered to the base action top by clamp_tops)
        *bevel(F('receiver', 250, 500, 15, 60, 0.53), 0.14),
        box('rcv_rear_slope', 250, 262, 15, 60, 0.55),
        box('port_lip_t', 382, 458, 28, 30, 0.56),
        box('port_lip_b', 382, 458, 47, 49, 0.56),
        box('bolt', 390, 450, 32, 44, 0.54),
        box('rail', 272, 500, 9.5, 15, 0.38),
        *teeth('rail_t', Z(500), 4.0, 4, 11.1, 11.24, 0.42),
        *teeth('rail_r', 7.3, Z(272), 4, 11.1, 11.24, 0.42),
        mbox('ch_arm', (6.78, Y(57), Z(270)), (7.47, Y(50), Z(262))),
        mbox('ch_rod', (6.72, Y(58), Z(300)), (6.98, Y(49), Z(270))),
        mbox('ch_knob', (6.6, Y(60), Z(304)), (7.0, Y(47), Z(296))),
        # forend
        *bevel(F('forend_upper', 500, 590, 15, 60, 0.53), 0.14),
        *bevel(F('forend_lower', 430, 590, 60, 80, 0.53), 0.12, top=False, bottom=True),
        box('forend_slot', 512, 572, 35, 48, 0.55),
        box('forend_cap', 575, 600, 13, 77, 0.6),
        mbox('cap_screw_l', (7.34, Y(52), Z(590)), (7.4, Y(44), Z(582))),
        mbox('cap_screw_r', (8.6, Y(52), Z(590)), (8.66, Y(44), Z(582))),
        # barrel / gas / suppressor
        box('barrel', 600, 740, 41, 56, 0.22),
        box('gas_tube', 600, 690, 20, 30, 0.15),
        box('gas_block', 685, 735, 18, 62, 0.27),
        box('gas_lug', 712, 722, 62, 72, 0.1),
        box('front_post', 700, 712, 12, 18, 0.08),
        box('supp_clamp', 735, 760, 30, 69, 0.56),
        mbox('clamp_bolt_l', (7.38, Y(56), Z(752)), (7.44, Y(44), Z(743))),
        mbox('clamp_bolt_r', (8.56, Y(56), Z(752)), (8.62, Y(44), Z(743))),
        box('supp', 760, 880, 32, 67, 0.5),
        box('supp_ring', 790, 796, 30.5, 68.5, 0.53),
        box('supp_cap', 872, 882, 35, 64, 0.42),
    ]
    sc = e[[x['name'] for x in e].index('supp')]; o = [8.0, (sc['from'][1] + sc['to'][1]) / 2, (sc['from'][2] + sc['to'][2]) / 2]
    e.append({'name': 'supp_r45', 'from': [8 - 0.47, o[1] - 0.47, sc['from'][2] + 0.02], 'to': [8 + 0.47, o[1] + 0.47, sc['to'][2] - 0.02],
              'rotation': {'origin': o, 'x': 0, 'y': 0, 'z': 45}})
    b = e[[x['name'] for x in e].index('barrel')]; ob = [8.0, (b['from'][1] + b['to'][1]) / 2, 0]
    e.append({'name': 'barrel_r45', 'from': [8 - 0.2, ob[1] - 0.2, b['from'][2] + 0.01], 'to': [8 + 0.2, ob[1] + 0.2, b['to'][2] - 0.01],
              'rotation': {'origin': ob, 'x': 0, 'y': 0, 'z': 45}})
    e += scope()
    e = clamp_tops(e, 'distant_relation')
    e = adopt(e, 'grip_insert', 'grip', GRIP_HW + 0.015, 0.1, 0.86, 0.2, 0.8)
    e = machine(e, target=143)
    e = tidy(e)
    e.append(_mag)
    mr = dict(_mag['rotation']); L = _mag['to'][1] - _mag['from'][1]; top = mr['origin']; yb = top[1] - L
    e.append({'name': 'mag_floor', 'from': [8 - 0.46, yb - 0.02, top[2] - 1.15], 'to': [8 + 0.46, yb + 0.22, top[2] + 1.15], 'rotation': dict(mr)})
    e.append({'name': 'mag_rib_f', 'from': [8 - 0.45, yb + 0.35, top[2] - 1.1], 'to': [8 + 0.45, top[1] - 0.5, top[2] - 0.92], 'rotation': dict(mr)})
    e.append({'name': 'mag_rib_r', 'from': [8 - 0.45, yb + 0.35, top[2] + 0.92], 'to': [8 + 0.45, top[1] - 0.5, top[2] + 1.1], 'rotation': dict(mr)})
    e.append({'name': 'mag_window', 'from': [8 - 0.44, yb + 0.6, top[2] - 0.55], 'to': [8 + 0.44, top[1] - 0.9, top[2] + 0.55], 'rotation': dict(mr)})
    return e


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('mag_'):
        r = _mag['rotation']; o = r['origin']
        q = _rot(p, o, r['x'], inv=True)
        q = (q[0], o[1] - (o[1] - q[1]) / MAG_SHORTEN, q[2])
        x, y, z = _rot(q, o, r['x'])
    ix, iy = ix_of(z), iy_of(y)
    return (-(x - 8) / LAT, CY - (ix - W / 2) / PPM, CZ - (iy - H / 2) / PPM)


# ---------------------------------------------------------------- paint
POLY, POLY_D, BLUE, BLUE_D, BLK, STEEL = (96, 92, 88), (72, 70, 68), (122, 140, 162), (92, 108, 128), (38, 38, 40), (64, 66, 70)
BLOCKS = (('cheek_pad', BLK), ('butt_rubber', BLK), ('strap_band', BLK), ('sling', STEEL), ('web_plate', STEEL),
          ('grip_insert', POLY_D), ('tg_', STEEL), ('trigger', BLK), ('port_lip', BLUE_D), ('bolt', STEEL),
          ('rail', BLUE_D), ('receiver', BLUE), ('rcv_rear', BLUE), ('ch_', STEEL), ('forend_slot', POLY_D),
          ('cap_screw', STEEL), ('forend_cap', STEEL), ('barrel', BLK), ('gas_', STEEL), ('front_post', BLK),
          ('clamp_bolt', STEEL), ('supp_ring', STEEL), ('supp_cap', BLK), ('supp_clamp', STEEL), ('supp', BLK),
          ('mag_window', STEEL), ('mag_', BLK), ('fil_', POLY), ('', POLY))
PALETTE = 16
FLAT_TOL = 34
PALETTE_KEEP = [POLY, BLUE, BLK]
SC_BODY = (52, 56, 62); SC_DARK = (24, 25, 28); SC_EDGE = (88, 96, 106)


_flat = FlatPainter(Path(__file__).parent, globals())


def _base_paint(e, fn, s, t):
    n = e['name']
    if not n.startswith('sc_') and not (n in ('supp', 'barrel') and fn == 'north'):
        for pre, c in BLOCKS:
            if n.startswith(pre):
                if pre == '' and fn in ('east', 'west') and n.startswith('stock_low'): c = POLY_D
                return c + (255,)
    if n.startswith('sc_'):
        inner = (n in ('sc_floor', 'sc_ceiling') and fn in ('up', 'down')) or n.startswith('sc_wall_in')
        if n == 'sc_floor' and fn == 'up' or n == 'sc_ceiling' and fn == 'down' or n.startswith('sc_wall_in'):
            return SC_DARK + (255,)
        if fn in ('north', 'south') and (n.startswith('sc_obj') or n.startswith('sc_ocu')):
            return (16, 17, 19, 255)
        c = SC_BODY
        if n.startswith(('sc_obj', 'sc_ocu', 'sc_turret')): c = (40, 43, 48)
        edge = min(s, 1 - s, t, 1 - t)
        if edge < 0.06: c = tuple(min(255, v + 18) for v in c)
        return c + (255,)
    if n == 'supp' and fn == 'north':
        d = math.hypot(s - .5, t - .5)
        if d < 0.17: return (10, 10, 11, 255)
        if d < 0.24: return (30, 30, 32, 255)
    if n == 'barrel' and fn == 'north':
        return (14, 14, 15, 255)
    return None


T = 18

# Identity pass: explicit per-face pixel paint, with real depth for signature apertures.
from _identity import enrich_geometry
IDENTITY_ID = 'thistle_and_yew'
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
