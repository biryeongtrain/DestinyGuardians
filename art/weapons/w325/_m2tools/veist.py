"""Shared VEIST rapid-fire frame (Sand Wasp-3au / Yellowjacket-3au use the identical rip frame mesh) - W325 detail pass.

Model px, muzzle -z, up +y, centred x 8.  Layout contract steelfeather_repeater (grip top z 7.6, muzzle z -8.3, butt
z 16.55, eye line y 12.95).  ADS rule: behind z 5.2 nothing on the centre band rises above y 12.84 (base top 12.86 for
z 5.5..9, 12.72 behind z 9.5); the optic frame elements are named 'sight_*' (hollow frame around the aim line).
"""
from solid import B, bar, vbar, octo, clean


def suppressor(a):
    for e in octo('sup_tip', 8, 10.5, .44, -8.3, -8.0): a(e)
    a(B('sup_bore', (7.82, 10.32, -8.32), (8.18, 10.68, -8.3)))
    for e in octo('sup', 8, 10.5, .55, -8.0, -4.85): a(e)
    for e in octo('sup_rear', 8, 10.5, .55, -4.75, -1.6): a(e)
    for e in octo('sup_mid_band', 8, 10.5, .6, -4.85, -4.75): a(e)
    for e in octo('sup_collar', 8, 10.5, .6, -1.6, -0.05): a(e)
    for e in octo('sup_band', 8, 10.5, .64, -1.95, -1.75): a(e)
    for e in octo('barrel_stub', 8, 10.5, .33, -0.05, 1.0): a(e)
    for e in octo('barrel_ring', 8, 10.5, .42, 0.3, 0.55): a(e)


def front(a):
    for e in bar('front_housing', 7.36, 8.64, 10.95, 12.22, 0.55, 2.0, c=.2): a(e)
    a(B('front_housing_lip', (7.42, 10.1, 0.85), (8.58, 10.95, 1.95)))
    a(B('rail_cap', (7.55, 12.22, 1.7), (8.45, 12.7, 2.45)))
    a(B('rail', (7.62, 12.22, 2.45), (8.38, 12.42, 4.1)))
    for i in range(4):
        z = 2.62 + i * .38
        a(B(f'rail_tooth_{i}', (7.58, 12.42, z), (8.42, 12.56, z + .18)))


def receiver(a):
    for e in bar('recv_upper', 7.3, 8.7, 10.85, 12.3, 1.95, 9.1, c=.22, at=[5.2]): a(e)
    for s, (x0, x1) in (('l', (7.19, 7.3)), ('r', (8.7, 8.81))):
        a(B(f'plate_{s}', (x0, 10.95, 2.75), (x1, 12.2, 5.6)))
        a(B(f'plate_{s}_aft', (x0, 10.95, 5.68), (x1, 12.2, 8.55)))
        a(B(f'plate_{s}_vent', (x0 - .04 if s == 'l' else x1, 11.75, 3.2), (x0 if s == 'l' else x1 + .04, 11.95, 4.9)))
        a(B(f'plate_{s}_nose', (x0, 11.35, 2.35), (x1, 12.2, 2.75)))
        a(B(f'plate_{s}_rear', (x0, 11.35, 8.55), (x1, 12.2, 8.95)))
        a(B(f'plate_{s}_bolt', (x0 - .05 if s == 'l' else x1, 11.62, 7.55), (x0 if s == 'l' else x1 + .05, 11.82, 7.75)))
    a(B('recv_band', (7.42, 12.3, 5.2), (8.58, 12.46, 9.1)))
    # magazine window: lower receiver (chamfered belly), lips, back wall, ejection housing, end blocks
    for e in bar('recv_lower', 7.3, 8.7, 9.3, 9.78, 1.6, 9.3, c=.16, top=False, bottom=True, at=[5.0]): a(e)
    for k, (za, zb) in enumerate(((1.95, 4.7), (4.76, 8.1), (8.16, 11.45))):
        a(B(f'win_lip_top_{k}', (7.26, 10.72, za), (8.74, 10.87, zb)))
        a(B(f'win_lip_bot_{k}', (7.26, 9.76, za), (8.74, 9.9, zb)))
    a(B('win_back', (7.6, 9.9, 1.95), (8.4, 10.72, 11.4)))
    a(B('eject_housing', (7.24, 9.9, 3.15), (8.76, 10.72, 4.7)))
    a(B('eject_slot_l', (7.2, 10.12, 3.4), (7.24, 10.5, 4.45)))
    a(B('eject_slot_r', (8.76, 10.12, 3.4), (8.8, 10.5, 4.45)))
    a(B('win_end_front', (7.3, 9.9, 1.95), (8.7, 10.72, 3.15)))
    a(B('win_end_rear', (7.3, 9.78, 11.35), (8.7, 10.87, 11.6)))
    a(B('cam_disc', (7.22, 9.3, 4.95), (8.78, 9.75, 5.55)))
    a(B('cam_disc_oct', (7.23, 9.31, 4.96), (8.77, 9.74, 5.54), ('x', 45), (8, 9.52, 5.25)))
    # horizontal VEIST magazine seen through the window (moving part)
    a(B('mag_body', (7.33, 9.92, 4.75), (8.67, 10.7, 11.3)))
    a(B('mag_front', (7.28, 9.95, 4.72), (8.72, 10.67, 5.62)))
    a(B('mag_spine', (7.4, 10.7, 5.62), (8.6, 10.78, 11.2)))


def holo(a):
    """Long-hooded VEIST holo (Sand Wasp): open frame z 3.95..5.15, window x 7.62..8.38 / y 12.62..13.18."""
    a(B('sight_base', (7.5, 12.3, 3.8), (8.5, 12.46, 5.2)))
    a(B('sight_sill', (7.62, 12.46, 3.95), (8.38, 12.62, 5.15)))
    for s, (x0, x1) in (('l', (7.42, 7.62)), ('r', (8.38, 8.58))):
        a(B(f'sight_cheek_{s}', (x0, 12.46, 3.95), (x1, 13.22, 5.15)))
        a(B(f'sight_cheek_{s}_step', (x0, 12.46, 3.75), (x1, 12.9, 3.95)))
        # low hood rails running back over the receiver (kept under the base top profile)
        a(B(f'holo_rail_{s}', (x0 + .04, 12.3, 5.15), (x1 - .04, 12.58, 8.9)))
        a(B(f'holo_rail_{s}_tip', (x0 + .04, 12.3, 8.9), (x1 - .04, 12.45, 9.3)))
    a(B('sight_hood', (7.42, 13.22, 3.75), (8.58, 13.4, 5.15)))


def reddot(a):
    """Compact upright red-dot (Yellowjacket): open frame z 3.95..5.05, window x 7.6..8.4 / y 12.62..13.24."""
    a(B('sight_base', (7.58, 12.3, 3.7), (8.42, 12.62, 6.0)))
    a(B('sight_sill', (7.6, 12.46, 3.95), (8.4, 12.62, 5.05)))
    for s, (x0, x1) in (('l', (7.4, 7.6)), ('r', (8.4, 8.6))):
        a(B(f'sight_cheek_{s}', (x0, 12.46, 3.95), (x1, 13.24, 5.05)))
        a(B(f'sight_lobe_{s}', (x0 - .03, 12.45, 4.85), (x1 + .03, 12.7, 5.3)))
        a(B(f'sight_knob_{s}', (x0 - .12 if s == 'l' else x1, 12.62, 4.3), (x0 if s == 'l' else x1 + .12, 12.86, 4.6)))
    a(B('sight_top', (7.4, 13.24, 3.9), (8.6, 13.4, 4.85)))
    a(B('rear_rail', (7.62, 12.3, 6.0), (8.38, 12.5, 9.0)))


def stock(a):
    for e in bar('stock_top', 7.36, 8.64, 11.7, 12.5, 8.9, 15.6, c=.2, at=[12.3]): a(e)
    a(B('stock_over_win', (7.32, 10.87, 9.1), (8.68, 11.95, 11.6)))
    for e in bar('stock_main', 7.32, 8.68, 7.9, 12.0, 11.45, 15.65, c=.2, top=False, bottom=True): a(e)
    a(B('stock_under_win', (7.32, 9.05, 9.3), (8.68, 9.78, 11.6)))
    a(B('stock_chin', (7.32, 8.4, 10.6), (8.68, 9.05, 11.45)))
    for e in vbar('pad_upper', 7.28, 8.72, 11.45, 12.45, 15.6, 16.55, c=.18, front=False): a(e)
    a(B('pad_mid', (7.28, 9.55, 15.6), (8.72, 11.45, 16.08)))
    for e in vbar('pad_lower', 7.28, 8.72, 7.85, 9.55, 15.6, 16.55, c=.18, front=False): a(e)
    a(B('pad_toe', (7.36, 7.7, 15.2), (8.64, 8.1, 16.3)))


def grip(a):
    # one rigid raked grip: every piece shares the core's -9 deg pivot and sits flush on a core face
    G = (('x', -9), (8, 9.35, 8.6))
    a(B('grip_core', (7.45, 5.75, 8.0), (8.55, 9.35, 9.35), *G))
    a(B('grip_front_strap', (7.5, 6.2, 7.85), (8.5, 8.6, 8.0), *G))
    a(B('grip_heel', (7.47, 5.45, 7.95), (8.53, 5.75, 9.75), *G))
    a(B('grip_back_fin', (7.52, 6.4, 9.35), (8.48, 8.0, 9.65), *G))
    a(B('grip_spur', (7.5, 8.35, 7.0), (8.5, 9.35, 7.9)))
    a(B('trigger', (7.92, 8.5, 6.65), (8.08, 9.3, 6.85), ('x', -15), (8, 9.3, 6.75)))


def foregrip(a):
    for e in bar('fg_rail', 7.3, 8.7, 9.25, 9.88, -0.65, 3.05, c=.15, top=False, bottom=True): a(e)
    a(B('fg_hook', (7.45, 9.0, -2.05), (8.55, 9.55, -0.45), ('x', -24), (8, 9.55, -0.45)))
    # C-ring claw and front grip as axis-aligned blocks that share faces (no near-parallel rotated slabs)
    a(B('fg_claw', (7.45, 7.9, -0.7), (8.55, 9.25, -0.25)))
    a(B('fg_claw_tip', (7.5, 7.8, -0.25), (8.5, 8.25, 0.25)))
    a(B('fg_grip', (7.45, 5.9, 1.4), (8.55, 9.25, 2.85)))
    a(B('fg_grip_front', (7.5, 7.6, 1.1), (8.5, 9.25, 1.4)))
    a(B('fg_fin', (7.5, 5.5, 1.25), (8.5, 5.9, 2.95)))


def build(optic):
    E = []; a = E.append
    suppressor(a); front(a); receiver(a)
    (holo if optic == 'holo' else reddot)(a)
    stock(a); grip(a); foregrip(a)
    return clean(E)


SIDE = ('east', 'west')
DARK = ('plate_', 'grip_', 'trigger', 'fg_', 'stock_top', 'pad_', 'barrel_')


def painter(c):
    """Flat paint for the parts whose projection smears (stretched suppressor, dark rubber/polymer parts)."""
    from solid import Flat
    rounds, front, accent = c['rounds'], c['mag_front'], c['accent']

    def mag(e, fn, s_, t):
        n = e['name']
        if not n.startswith('mag_') or fn not in SIDE: return None
        if n == 'mag_front':
            u = s_ if fn == 'west' else 1 - s_          # 0 = muzzle end
            if abs((u + t * .6) % .5 - .25) < .09: return accent + (255,)
            return front + (255,)
        if n == 'mag_body':
            u = s_ if fn == 'west' else 1 - s_
            if t < .14 or t > .86: return (60, 60, 58, 255)
            if int(u * 70) % 2 == 0 and .3 < t < .7: return tuple(int(v * .8) for v in rounds) + (255,)
            return rounds + (255,)
        return None
    flat = Flat([
        (lambda n, f: n.startswith('sup_mid_band'), c['metal']),
        (lambda n, f: n.startswith('sup') and n != 'sup_bore', c['sup']),
        (lambda n, f: n == 'sup_bore', (34, 34, 36)),
        (lambda n, f: n.startswith('barrel_'), c['metal']),
        (lambda n, f: n.startswith('stock_top') or (n.startswith('plate_') and f not in SIDE), c['plate']),
        (lambda n, f: n.startswith(('grip_', 'fg_', 'trigger')) and (f not in SIDE or '_ch_' in n or 'tip' in n or 'trigger' in n), c['grip']),
        (lambda n, f: n.startswith('pad_') and (f not in SIDE or '_ch_' in n), c['pad']),
        (lambda n, f: n.startswith('rail_tooth'), c['metal']),
        (lambda n, f: n.startswith('eject_slot') or n.endswith('_vent') or '_joint_' in n, (36, 36, 38)),
    ])
    return lambda e, fn, s_, t: mag(e, fn, s_, t) or flat(e, fn, s_, t)
