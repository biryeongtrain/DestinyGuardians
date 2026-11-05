"""W325 m8: shared Hakke SMG frame (Philippis-B / Sondok-C, identical rip geometry) over base antiope_d.

Rip -> 'old' frame: uniform 38 px/m, rip magazine centre at old z 8.7, receiver top (rip z 0.155 m) at y 14.0.  Old ->
model z is piecewise (BP): the grip/magazine zone is shifted +0.6 px so magazine and grip land on the base
magazine/grip, the front stretched to the base muzzle (-2.8), the rear to the base butt (~16.9).  Elements are
authored in old z (box(..., old=True)) unless they must sit on a base model-z feature (sights: old=False).
"""
import math
from types import SimpleNamespace
from detail import separate, box as _box, cham as _cham, chamy as _chamy, zsplit as _zsplit, Flat

S = 38.0
GZ, GW = 8.7, 0.033
SY, SW = 14.0, 0.155
BP = [(-2.8, -2.8), (6.5, 5.9), (10.3, 9.7), (16.95, 16.0)]   # (model z, old z)
BORE = (8.0, 12.65)


def _pw(v, a):
    for i in range(len(BP) - 1):
        (m0, o0), (m1, o1) = BP[i], BP[i + 1]
        p0, q0, p1, q1 = (m0, o0, m1, o1) if a == 0 else (o0, m0, o1, m1)
        if v <= p1 or i == len(BP) - 2:
            return q0 + (v - p0) * (q1 - q0) / (p1 - p0)


def zo(z): return _pw(z, 0)
def zm(z): return round(_pw(z, 1), 4)


def model2world(name, p):
    x, y, z = p
    return (-(x - 8.0) / S, GW + (zo(z) - GZ) / S, SW + (y - SY) / S)


def _mz(lo, hi, old):
    lo, hi = list(lo), list(hi)
    if old:
        lo[2], hi[2] = zm(lo[2]), zm(hi[2])
    return lo, hi


def box(name, lo, hi, rot=None, old=True):
    lo, hi = _mz(lo, hi, old)
    if rot and old:
        rot = dict(rot); o = list(rot['origin']); o[2] = zm(o[2]); rot['origin'] = o
    return _box(name, lo, hi, rot)


def rx(name, lo, hi, ang, old=True):
    lo, hi = _mz(lo, hi, old)
    return _box(name, lo, hi, {'origin': [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2], 'x': ang})


def cham(name, x0, x1, y0, y1, z0, z1, r, corners='tltrblbr', old=True, rb=None):
    if old:
        z0, z1 = zm(z0), zm(z1)
    return _cham(name, x0, x1, y0, y1, z0, z1, r, corners, rb)


def chamy(name, x0, x1, y0, y1, z0, z1, r, corners='fbFB', old=True):
    if old:
        z0, z1 = zm(z0), zm(z1)
    return _chamy(name, x0, x1, y0, y1, z0, z1, r, corners)


def tilt(els, ang, origin):
    for e in els:
        e['rotation'] = {'origin': [round(v, 4) for v in origin], 'x': ang}
    return els


def common(sight):
    """sight: 'peep' (Philippis-B) or 'reflex' (Sondok-C)."""
    E = []
    a = E.append; ex = E.extend
    # muzzle brake: two chamfered rings, open side slots between top/bottom bars, cored bore
    # Four bars around the actual bore; no painted solid front cap.
    for tag, lo, hi in [('t',(7.55,12.88,-2.8),(8.45,13.15,-2.5)),
                        ('b',(7.55,12.15,-2.8),(8.45,12.42,-2.5)),
                        ('l',(7.55,12.42,-2.8),(7.85,12.88,-2.5)),
                        ('r',(8.15,12.42,-2.8),(8.45,12.88,-2.5))]:
        a(box('brake_front_'+tag,lo,hi))
    a(box('brake_rear', (7.55, 12.15, -1.62), (8.45, 13.15, -1.35)))
    a(box('brake_top', (7.62, 12.88, -2.5), (8.38, 13.05, -1.62)))
    a(box('brake_bot', (7.62, 12.25, -2.5), (8.38, 12.42, -1.62)))
    a(box('brake_mid', (7.7, 12.6, -2.5), (8.3, 12.7, -1.62)))
    a(box('brake_core', (7.85, 12.42, -2.5), (8.15, 12.88, -1.62)))
    a(box('barrel', (7.76, 12.41, -1.35), (8.24, 12.89, -0.9)))
    # front cap: chamfered block, sight block with a centre notch, chin, sling loop (real hole)
    ex(cham('front_cap', 7.35, 8.7, 11.0, 14.1, -0.95, 1.0, 0.25, corners='tltr'))
    a(box('fsight_base', (7.55, 14.1, -0.95), (8.45, 14.2, -0.45)))
    a(box('fsight_l', (7.55, 14.2, -0.95), (7.88, 14.45, -0.45)))
    a(box('fsight_r', (8.12, 14.2, -0.95), (8.45, 14.45, -0.45)))
    ex(cham('front_chin', 7.42, 8.63, 10.6, 11.0, -1.0, -0.35, 0.12, corners='blbr'))
    a(box('sling_l', (7.72, 10.4, -0.85), (7.82, 10.6, -0.55)))
    a(box('sling_r', (8.18, 10.4, -0.85), (8.28, 10.6, -0.55)))
    a(box('sling_bot', (7.72, 10.3, -0.85), (8.28, 10.4, -0.55)))
    # receiver: chamfered body, raised side panel step, selector plate, bolts
    ex(_zsplit('rcv_main', 7.35, 8.65, 11.1, 14.05, [zm(1.0), zm(4.6), zm(7.2), zm(9.6)], r=0.22, corners='tltr'))
    ex(cham('rcv_rear', 7.35, 8.65, 11.6, 14.05, 9.6, 11.8, 0.22, corners='tltrbr'.replace('br', '')))
    for t, x0, x1 in (('l', 7.3, 7.35), ('r', 8.65, 8.7)):
        a(box(f'panel_{t}', (x0, 12.75, 1.6), (x1, 13.55, 8.3)))
    a(box('selector_plate', (8.7, 11.85, 2.4), (8.76, 12.75, 4.6)))
    for i, z in enumerate((1.6, 5.3, 9.1)):
        a(box(f'bolt_{i}', (8.7, 13.1, z), (8.76, 13.32, z + 0.22)))
    a(box('charge_slot', (8.65, 12.2, 5.6), (8.72, 12.45, 8.6)))
    a(box('charge_knob', (8.65, 12.15, 5.6), (8.95, 12.5, 6.1)))
    # top rails with ribs
    a(box('rail', (7.62, 14.05, 1.0), (8.38, 14.12, 6.4)))
    for i in range(6):
        z = 1.3 + i * 0.85
        a(box(f'rail_rib_{i}', (7.6, 14.12, z), (8.4, 14.25, z + 0.3)))
    a(box('rear_rail', (7.62, 14.05, 10.25), (8.38, 14.12, 11.3)))
    for i in range(2):
        a(box(f'rear_rib_{i}', (7.6, 14.12, 10.35 + i * 0.55), (8.4, 14.25, 10.65 + i * 0.55)))
    if sight == 'peep':
        # flip-up rear peep on the base peep z (7.27..7.7): hollow frame around the ADS line, drum to the side
        a(box('sight_base', (7.55, 14.05, 6.9), (8.45, 14.35, 7.9), old=False))
        a(box('sight_low', (7.55, 14.35, 7.27), (8.45, 14.92, 7.7), old=False))
        a(box('sight_ring_top', (7.55, 15.48, 7.27), (8.45, 15.72, 7.7), old=False))
        a(box('sight_ring_l', (7.55, 14.92, 7.27), (7.78, 15.48, 7.7), old=False))
        a(box('sight_ring_r', (8.22, 14.92, 7.27), (8.45, 15.48, 7.7), old=False))
        ex(cham('sight_drum', 8.45, 8.78, 14.1, 14.6, 7.3, 7.85, 0.08, old=False))
    else:
        # Hakke reflex: low mount, swept hood frame on the base peep z (7.27..7.7) with an open window around the
        # ADS line (x 7.74..8.26, y 14.75..15.5); top 15.72 stays under the base peep (15.76)
        a(box('sight_mount', (7.55, 14.05, 4.4), (8.45, 14.12, 7.75), old=False))
        a(box('sight_hood_l', (7.5, 14.12, 7.27), (7.74, 15.62, 7.7), old=False))
        a(box('sight_hood_r', (8.26, 14.12, 7.27), (8.5, 15.62, 7.7), old=False))
        a(box('sight_hood_top', (7.5, 15.5, 7.27), (8.5, 15.72, 7.7), old=False))
        a(box('sight_hood_sill', (7.74, 14.12, 7.27), (8.26, 14.75, 7.7), old=False))
        a(box('sight_lens_rim', (7.74, 15.46, 7.27), (8.26, 15.5, 7.32), old=False))
        for t, x0, x1 in (('l', 7.5, 7.74), ('r', 8.26, 8.5)):
            a(box(f'sight_strut_{t}', (x0, 14.12, 6.9), (x1, 14.75, 7.27), old=False))
        a(box('sight_fwd', (7.6, 14.12, 4.5), (8.4, 14.3, 5.3), old=False))
    # side flashlight: chamfered body, bezel, mount
    ex(cham('light_body', 6.25, 7.2, 12.95, 13.9, 0.6, 3.6, 0.18, corners='tlbl'))
    a(box('light_bezel', (6.15, 12.85, 0.25), (7.3, 14.0, 0.6)))
    a(box('light_grip_0', (6.2, 13.0, 2.3), (7.25, 13.85, 2.45)))
    a(box('light_mount', (7.15, 13.1, 1.6), (7.4, 13.7, 2.6)))
    # angled foregrip, trigger guard (real opening), trigger, pistol grip
    ex(tilt(chamy('foregrip', 7.4, 8.6, 7.5, 10.9, 2.0, 3.4, 0.2), -15, [8.0, 9.2, zm(2.7)]))
    ex(cham('frame_web', 7.4, 8.6, 10.4, 11.1, 1.0, 4.2, 0.15, corners='blbr'))
    a(box('guard_bar', (7.7, 9.6, 4.4), (8.3, 9.85, 6.9)))
    a(rx('guard_front', (7.7, 9.7, 4.0), (8.3, 11.1, 4.32), -20))
    a(box('guard_rear', (7.7, 9.6, 6.75), (8.3, 11.1, 6.95)))
    a(rx('trigger', (7.9, 10.1, 5.5), (8.1, 11.1, 5.72), -15))
    ex(chamy('grip', 7.35, 8.65, 7.45, 11.1, 6.8, 9.45, 0.25))
    ex(cham('grip_heel', 7.33, 8.67, 7.3, 7.6, 6.8, 9.62, 0.1, corners='blbr'))
    for t, x in (('l', 7.3), ('r', 8.65)):
        a(box(f'grip_panel_{t}', (x, 8.2, 7.3), (x + 0.05, 10.0, 8.9)))
    # folding stock: dark comb tube, white side arms (gap between them), hinge bracket, angled butt pad, brace
    ex(cham('stock_comb', 7.45, 8.55, 12.3, 13.55, 11.8, 14.6, 0.2, corners='tltr'))
    a(box('stock_comb_top', (7.55, 13.55, 11.8), (8.45, 13.75, 13.2)))
    for t, x0, x1 in (('l', 7.22, 7.45), ('r', 8.55, 8.78)):
        ex(cham(f'stock_arm_{t}', x0, x1, 11.05, 12.35, 12.15, 14.75, 0.10, corners='tltr'))
        a(box(f'stock_pin_{t}', (x0 - 0.04, 11.5, 12.4), (x1 + 0.04, 11.8, 12.7)))
    a(box('stock_arm_web', (7.45, 11.05, 13.9), (8.55, 11.3, 14.75)))
    ex(cham('stock_bracket', 7.2, 8.8, 11.0, 12.95, 14.6, 15.35, 0.2, corners='tltr'))
    ex(chamy('butt_pad', 7.45, 8.55, 9.1, 12.7, 15.35, 15.95, 0.15, corners='bB'))
    a(rx('butt_brace', (7.75, 10.85, 14.2), (8.25, 11.1, 15.4), 25))
    # magazine (moving leaf): chamfered body, ribs, floor plate with pull
    ex(cham('mag_body', 7.62, 8.38, 4.05, 7.45, 7.4, 9.0, 0.1, corners='blbr'))
    ex(cham('mag_floor', 7.58, 8.42, 3.75, 4.05, 7.3, 9.1, 0.08, corners='blbr'))
    a(box('mag_pull', (7.8, 3.6, 7.9), (8.2, 3.75, 8.8)))
    # Material boundary: painted upper receiver / polymer lower frame. Exact shared plane, same solid union.
    divided=[]
    for e in E:
        if e['name'] in ('rcv_main0','rcv_main1','rcv_main2'):
            import copy
            upper=copy.deepcopy(e); upper['name'] += '_paint'; upper['from'][1]=12.6
            e['to'][1]=12.6
            divided.extend((e,upper))
        else:divided.append(e)
    return separate(divided)


DARK_FLAT = {'peep': {}, 'reflex': {}}


def make_special(wid, colours, extra=None):
    """Flat paint for caps/strips/ends/small parts; the big side faces keep the clean projection (logos, panels)."""
    def policy(e, fn):
        n = e['name']
        if '_ch' in n or '_cap' in n:
            return True
        if n.startswith(('brake', 'barrel', 'fsight', 'sling', 'panel', 'bolt', 'charge', 'rail', 'rear_r', 'sight',
                         'light_grip', 'light_mount', 'guard', 'trigger', 'grip_heel', 'grip_panel', 'stock_pin',
                         'stock_arm_web', 'butt', 'mag_pull', 'stock_comb_top')):
            return True
        return fn in ('north', 'south', 'down') or (fn == 'up' and n.startswith(('front_chin', 'frame_web', 'grip',
                                                                                   'foregrip', 'mag', 'light')))
    flat = Flat(wid, SimpleNamespace(model2world=model2world), policy, colours=colours)

    def special(e, fn, s, t):
        n = e['name']
        if extra:
            r = extra(e, fn, s, t)
            if r is not None:
                return r
        if n == 'barrel' and fn == 'north':
            if math.hypot(s - .5, t - .5) < .3:
                return (14, 14, 16, 255)
        if n == 'brake_core' and fn == 'north':
            return (14, 14, 16, 255)
        if n == 'light_bezel' and fn == 'north':
            r = math.hypot(s - .5, t - .5)
            if r < .4:
                return (236, 236, 222, 255) if r < .3 else (150, 152, 150, 255)
        return flat(e, fn, s, t)
    return special


from paint import painter, camo, line, every, text_hit  # noqa: E402

BLACK = (18, 18, 20)


def make_painter(pal):
    """pal: dict of material colours: camo (3-tuple of rgb), poly, poly_l, white, steel, accent (rgb|None),
    accent_text (str|None), mark (rgb|None)."""
    C = pal

    def region(n, fn, p, s, t, e):
        x, y, z = p
        side = fn in ('east', 'west')
        if n in ('brake_core',) or (n == 'barrel' and fn == 'north' and abs(x - 8) < 0.15 and abs(y - 12.65) < 0.15):
            return BLACK
        if n.startswith(('brake', 'barrel', 'fsight', 'sling', 'rail', 'rear_r', 'stock_pin', 'charge_knob')):
            return C['white'] if not n.startswith(('barrel', 'stock_pin')) else C['steel']
        if n.startswith(('bolt_', 'charge_slot', 'trigger', 'light_grip', 'mag_pull', 'sight_drum')):
            return BLACK
        if n.startswith('sight'):
            if n == 'sight_lens_rim':
                return (40, 140, 60)
            return C['white']
        if n.startswith('light_bezel'):
            if fn == 'north':
                r = math.hypot(x - 6.725, y - 13.425)
                if r < 0.42:
                    return (238, 238, 220) if r < 0.3 else C['steel']
            return C['steel']
        if n.startswith(('light', 'selector')):
            if n.startswith('selector') and side:
                return BLACK if (line(z, zm(3.0), 0.08) or line(z, zm(4.0), 0.08)) else (56, 56, 56)
            return (52, 52, 54) if n.startswith('light_body') else C['poly']
        if '_groove' in n:
            return C['poly']
        if n.startswith('panel'):
            if C.get('accent'):
                if C.get('accent_text') and side:
                    u = z if fn == 'west' else -z
                    u0 = zm(3.0) if fn == 'west' else -zm(7.0)
                    if text_hit(u, 13.47 - y, C['accent_text'], u0, 0, 0.12):
                        return C['white']
                return C['accent']
            return C['poly_l']
        if n.startswith(('front_cap', 'rcv_main', 'rcv_rear', 'stock_arm', 'stock_bracket')) and not n.startswith('stock_arm_web'):
            if n.startswith('rcv_main') and side and y < 12.6:
                if C.get('mark') and fn == 'east' and line(y, 12.0, 0.12) and (zm(5.5) < z < zm(6.4)) and not line(z, zm(5.95), 0.07):
                    return C['mark']
                if line(y, 12.6, 0.05):
                    return C['poly_l']
                return C['poly']
            if n.startswith('rcv_main') and fn == 'up':
                return C['camo'][0]
            return camo(p, C['camo'], cell=1.4, seed=21, cuts=(0.48, 0.68))
        if n.startswith('mag'):
            if n.startswith('mag_body') and side and 4.6 < y < 5.1 and (line(z, 8.0, 0.18) or line(z, 8.6, 0.18)):
                return BLACK
            return C['white'] if n.startswith('mag_body') else BLACK
        if n.startswith('grip_panel'):
            return BLACK if every(y, 8.3, 0.3, 0.07) else C['poly_l']
        if n.startswith('foregrip') and side and 8.2 < y < 10.2:
            return BLACK if every(y, 8.2, 0.35, 0.08) else C['poly_l']
        if n.startswith(('stock_comb',)):
            return (40, 40, 42)
        return C['poly']
    return painter(region)
