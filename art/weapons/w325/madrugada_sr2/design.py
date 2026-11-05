"""W325 Madrugada SR2 (rare scout rifle, Lightweight, Omolon) over base patron_of_lost_causes (W153 sight layout).

Authored in rip-image coordinates of the calibrated nx view (proj_cache/nx_albedo.png, 800 px/m, muzzle right),
converted with one uniform scale 0.036 model px per image px (45 px/m; the rip is a compact 0.8 m gun): trigger ix 288 ->
z 6.67 (base trigger), so the butt ends z 16.5 (base 16.1) and the front block -5.6 (base muzzle -8.93); vertical anchored
on the bore (iy 77 -> y 10.52, the base threaded-muzzle centre).  Lateral 30 px/m.
Iron sights: the rear post is rebuilt as an open peep ring around the base W153 ADS line (opening x 7.75..8.25, y 12.4..12.95,
z 5.9..6.6); the kept W148 aim tip (z 6.05..6.15, y 12.66..12.7) sits in its centre.  Magazine: Omolon layout keeps the
magazine in front of the trigger (z 2.6..5.2); the base moving magazine is behind the grip (z 10.6..13.4) — see notes.
"""
import json, math
from _w3lib import bevel, clamp_tops, machine, face_pt, blob, adopt, tidy, stairs_for
B = 'patron_of_lost_causes'
from pathlib import Path

_M = json.loads((Path(__file__).parent / 'proj_cache/manifest.json').read_text())
_V = _M['views']['nx']; PPM = _M['ppm']; W, H = _V['res']; CX, CY, CZ = _V['centre']

TRIG_IX, TRIG_Z, K = 288, 6.67, 0.036
BORE_IY, BORE_Y = 77, 10.52
LAT = 30.0


def Z(ix): return TRIG_Z + (TRIG_IX - ix) * K
def Y(iy): return BORE_Y - (iy - BORE_IY) * K
def ix_of(z): return TRIG_IX - (z - TRIG_Z) / K
def iy_of(y): return BORE_IY - (y - BORE_Y) / K


def box(name, ix0, ix1, iy0, iy1, hw, xc=8.0):
    z0, z1 = sorted((Z(ix0), Z(ix1))); y0, y1 = sorted((Y(iy0), Y(iy1)))
    return {'name': name, 'from': [xc - hw, y0, z0], 'to': [xc + hw, y1, z1]}


def mbox(name, f, t): return {'name': name, 'from': list(f), 'to': list(t)}


def rbox(name, top, bot, width, hw, xc=8.0):
    zt, yt = Z(top[0]), Y(top[1]); zb, yb = Z(bot[0]), Y(bot[1])
    dz, dy = zb - zt, yb - yt; L = math.hypot(dz, dy); a = math.degrees(math.atan2(-dz, -dy))
    return {'name': name, 'from': [xc - hw, yt - L, zt - width / 2], 'to': [xc + hw, yt, zt + width / 2],
            'rotation': {'origin': [xc, yt, zt], 'x': round(a, 4), 'y': 0, 'z': 0}}


def sbar(name, p0, p1, thick, hw, xc=8.0):
    """Bar whose top edge runs along image segment p0 (rear) -> p1 (front), thickness below it."""
    z0, y0 = Z(p0[0]), Y(p0[1]); z1, y1 = Z(p1[0]), Y(p1[1])
    L = math.hypot(z1 - z0, y1 - y0); a = math.degrees(math.atan2(y1 - y0, z0 - z1))
    return {'name': name, 'from': [xc - hw, y0 - thick, z0 - L], 'to': [xc + hw, y0, z0],
            'rotation': {'origin': [xc, y0, z0], 'x': round(a, 4), 'y': 0, 'z': 0}}


def octa(name, ix0, ix1, iy0, iy1, hw):
    b = box(name, ix0, ix1, iy0, iy1, hw)
    yc = (b['from'][1] + b['to'][1]) / 2; zc = (b['from'][2] + b['to'][2]) / 2; r = hw * 0.93
    return [b, {'name': name + '_r45', 'from': [8 - r, yc - r, b['from'][2] + 0.02], 'to': [8 + r, yc + r, b['to'][2] - 0.02],
                'rotation': {'origin': [8.0, yc, zc], 'x': 0, 'y': 0, 'z': 45}}]


def peep():
    z0, z1 = Z(312), Z(290)
    return [mbox('peep_l', (7.52, Y(40), z0), (7.75, 12.95, z1)),
            mbox('peep_r', (8.25, Y(40), z0), (8.48, 12.95, z1)),
            mbox('peep_top', (7.52, 12.95, z0), (8.48, 13.15, z1)),
            mbox('peep_base', (7.6, Y(40), z0 - 0.05), (8.4, 12.4, z1 + 0.05))]


def fillet(name, ix, iy, size, hw):
    zc, yc = Z(ix), Y(iy); h = size * 0.7071
    return {'name': name, 'from': [8 - hw, yc - h, zc - h], 'to': [8 + hw, yc + h, zc + h],
            'rotation': {'origin': [8.0, yc, zc], 'x': 45, 'y': 0, 'z': 0}}


GRIP_HW = 0.52


def _base_elements():
    e = [
        *bevel(box('butt_pad', 10, 50, 60, 190, 0.5), 0.12, top=True, bottom=True),
        box('butt_slot_rim', 26, 34, 80, 140, 0.53),
        *bevel(box('stock_top', 50, 176, 62, 150, 0.58), 0.16),
        box('stock_rim_top', 50, 176, 60, 66, 0.6),
        *bevel(box('stock_top_front', 175, 229, 62, 108, 0.58), 0.14),
        sbar('stock_lower', (50, 85), (236, 172), 2.0, 0.56),
        sbar('stock_pad', (95, 118), (205, 172), 0.9, 0.6),
        box('stock_front', 229, 262, 62, 166, 0.58),
        fillet('fil_t0', 175, 108, 0.5, 0.58), fillet('fil_t1', 229, 108, 0.45, 0.58),
        box('hinge', 85, 125, 47, 62, 0.25),
        box('hinge_knob', 92, 104, 42, 52, 0.32),
        rbox('grip', (266, 140), (242, 222), 1.15, 0.52),
        rbox('grip_ribs', (262, 150), (246, 212), 0.7, 0.55),
        box('trigger', 284, 292, 138, 160, 0.08),
        rbox('tg_loop', (296, 128), (288, 156), 0.25, 0.12),
        box('tg_base', 262, 300, 154, 160, 0.14),
        *bevel(box('receiver', 262, 415, 45, 135, 0.7), 0.16, top=True, bottom=False),
        box('rcv_frame_f', 405, 415, 45, 135, 0.73),
        box('rcv_frame_r', 262, 272, 45, 135, 0.73),
        box('port_ring', 302, 353, 85, 136, 0.72),
        box('rcv_low', 330, 415, 135, 165, 0.66),
        box('port_ring_low', 344, 386, 145, 190, 0.69),
        box('rail', 290, 410, 35, 45, 0.42),
        box('top_strut', 120, 262, 54, 62, 0.3),
        rbox('canister', (164, 40), (170, 63), 1.95, 0.4),
        rbox('canister_band', (166, 46), (167, 52), 2.0, 0.43),
        sbar('lever', (355, 102), (408, 150), 0.45, 0.12, xc=8.8),
        box('ch_disc', 400, 430, 125, 150, 0.2, xc=8.75),
        box('rod_top', 410, 595, 45, 56, 0.2),
        box('rod_low', 415, 595, 114, 126, 0.2),
        box('rod_clamp', 452, 462, 43, 128, 0.26),
        rbox('strut', (412, 94), (438, 116), 0.3, 0.18),
        *bevel(box('front_block', 582, 632, 48, 132, 0.62), 0.12, top=True, bottom=True),
        box('front_plate', 600, 630, 60, 120, 0.65),
        box('front_vents', 612, 626, 80, 110, 0.67),
        box('front_sight', 604, 626, 40, 48, 0.18),
        box('front_sight_ear', 604, 626, 36, 40, 0.28),
    ]
    e += octa('barrel', 415, 584, 67, 87, 0.3)
    e += [box('barrel_collar', 415, 426, 64, 90, 0.34), box('barrel_ring', 560, 568, 64, 90, 0.34)]
    e += peep()
    e += [box('peep_ring_l', 290, 312, 15, 40, 0.0), box('peep_ring_r', 290, 312, 15, 40, 0.0)][:0]
    e += [box('fixed_mag', 330, 400, 165, 230, 0.48), box('fixed_mag_floor', 326, 404, 226, 233, 0.52),
          box('fixed_mag_rib', 340, 390, 175, 222, 0.51)]
    e = adopt(e, 'stock_pad', 'stock_lower', 0.6, 0.45, 1.0, 0.3, 0.8)
    e = clamp_tops(e, B)
    e = adopt(e, 'grip_ribs', 'grip', GRIP_HW + 0.015, 0.12, 0.88, 0.15, 0.85)
    e = adopt(e, 'canister_band', 'canister', 0.43, 0.55, 0.75, -0.03, 1.03)
    e = machine(e, target=120, maxlen=2.4)
    e = tidy(e)
    # reload part: small stub magazine in the base patron magazine box (the real Omolon magazine is fixed in front)
    r = {'origin': [8, 6.97, 12.14], 'x': -8, 'y': 0, 'z': 0}
    e += [{'name': 'mag_stub', 'from': [7.55, 6.0, 11.3], 'to': [8.45, 7.6, 12.9], 'rotation': dict(r)},
          {'name': 'mag_stub_floor', 'from': [7.5, 5.82, 11.2], 'to': [8.5, 6.02, 13.0], 'rotation': dict(r)}]
    return e


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('peep_'):
        y = min(y, Y(15))
    ix, iy = ix_of(z), iy_of(y)
    return (-(x - 8) / LAT, CY - (ix - W / 2) / PPM, CZ - (iy - H / 2) / PPM)


INNER = (24, 25, 24, 255)
OLIVE, OLIVE_D, BONE, BLACK, ROD, RED = (88, 104, 60), (56, 70, 42), (214, 208, 196), (36, 36, 36), (52, 52, 54), (176, 44, 40)
PORTS = ((327.5, 110.0, 19.0), (365.0, 168.0, 13.0))   # rip image circles (ix, iy, radius of the black bore)
CAMO = ('stock_top', 'stock_lower', 'stock_front', 'receiver', 'rcv_low', 'fixed_mag', 'port_ring')
BONE_P = ('stock_rim', 'butt_slot', 'fil_', 'hinge', 'top_strut', 'rcv_frame', 'rail', 'barrel', 'front_plate',
          'front_sight', 'canister_band', 'peep', 'tg_')
BLACK_P = ('butt_pad', 'stock_pad', 'grip', 'trigger', 'lever', 'ch_disc', 'rod', 'strut', 'front_block', 'front_vents', 'mag_')
PALETTE = 16
FLAT_TOL = 30
PALETTE_KEEP = [OLIVE, OLIVE_D, BONE, RED]


def _base_paint(e, fn, s, t):
    n = e['name']
    if n == 'peep_l' and fn == 'east' or n == 'peep_r' and fn == 'west' or n == 'peep_top' and fn == 'down':
        return INNER
    if n.startswith('barrel') and fn == 'north' and n == 'barrel':
        if math.hypot(s - .5, t - .5) < 0.25: return (12, 12, 12, 255)
    p = face_pt(e, fn, s, t); ix, iy = ix_of(p[2]), iy_of(p[1])
    if fn in ('east', 'west') and n.startswith(('receiver', 'rcv_low', 'port_ring', 'fixed_mag')):
        for cx, cy, r in PORTS:
            d = math.hypot(ix - cx, iy - cy)
            if d < r - 3: return (8, 8, 9, 255)
            if d < r + 2: return (60, 60, 62, 255)
            if d < r + 7: return BONE + (255,)
        if n.startswith('receiver') and 312 <= ix <= 384 and 50 <= iy <= 62:     # OMOLON lettering
            if 54 <= iy <= 59 and int((ix - 312) / 3) % 4 != 3: return RED + (255,)
    if n == 'canister' or n.startswith('canister_') and not n.startswith('canister_band'):
        return (190, 168, 120, 255) if fn in ('east', 'west') and abs(t - .5) > .3 else (150, 130, 96, 255)
    if n.startswith('canister_band'): return RED + (255,)
    if n.startswith(BLACK_P) and not n.startswith('rod_clamp'):
        return (ROD if n.startswith(('rod', 'strut')) else BLACK) + (255,)
    if n.startswith('rod_clamp'): return BONE + (255,)
    if n.startswith(BONE_P): return BONE + (255,)
    if n.startswith(CAMO):
        v = blob(p, 0.8, 0.4)
        return (OLIVE_D if v > 0.15 else BONE if v < -0.45 else OLIVE) + (255,)
    return None


T = 18

# Identity pass: explicit per-face pixel paint, with real depth for signature apertures.
from _identity import enrich_geometry
IDENTITY_ID = 'madrugada_sr2'
T = 24
ATLAS = 1024

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
