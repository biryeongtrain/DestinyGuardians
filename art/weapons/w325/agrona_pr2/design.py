"""W325 Agrona PR2 (rare, Lightweight pulse rifle; Omolon, battery-cell magazine behind the grip) over chattering_bone.

Rip measured in nx / pz / ny views.  The rip is stubby and tall (0.77 m long, 0.34 m tall with the scope), so the map
is non-uniform: 30 px/m along the length, 26 px/m across (height and width, width x1.07) - a mild 1.15 stretch that
keeps the Omolon silhouette but brings receiver height (3.0 px) and length close to the base.  Authoring frame:
rip butt (Y 0.3101) -> z 16.8, rip Z 0.11 -> y 10; the whole model is then shifted DZ = +0.6 so the grip/trigger and
the battery magazine sit on chattering_bone's grip (top ~7.7-9.6) and moving magazine (z 10.8-13.3).
Muzzle -5.45 (base -8.66): the rip has a short nose; kept rather than stretched.
W325 detail pass + ADS fix: the rip's tall box scope (top 14.15) blocked the ADS view.  It is now a compact hollow
box (elements sight_*) fitted inside chattering_bone's own optic hood envelope (z 6.8-8.2, top 13.5 vs base hood 13.47):
aperture 0.8 x 0.8 centred x 8 / y 13.0 (base hood centre 12.99, W151 pin tip 12.93); its texture samples the rip
scope squeezed into that box (SCOPE map).  Mount/rail stay under the base optic rail (12.54).  Detail: chamfered
receiver/stock/nose edges, vent slats, side hose clamps, layered butt pad, ribbed grip, battery cell contacts; clean
flat paint where the projection smears (Painter).
"""
from w325_5_lib import box, bx, bar, vbar, chbox, along, bar_on, Uniform, Painter

M = Uniform(30.0, 16.8, 0.3101, 10.0, 0.11, 0.0003, kx=1.07, sy=26.0)
DZ = 0.6
SCOPE = ((6.85, 8.12), (4.8, 9.95), (12.5, 13.5), (12.07, 13.55))   # model z/y box -> rip-frame scope box
NO_OVERLAY = False
B = .78


def is_magazine(n): return n.startswith('mag_')


def model2world(name, p):
    x, y, z = p
    if name.startswith('sight_'):
        (a, b), (c, d), (e, f), (g, h) = SCOPE
        return M((x, g + (y - e) * (h - g) / (f - e), c + (z - a) * (d - c) / (b - a)))
    return M((x, y, z - DZ))


def front():
    S = []
    S.append(bx('muzzle_cap', .36, 9.85, 10.65, -6.05, -5.85))
    S.append(bx('muzzle_crown', .26, 9.95, 10.55, -6.15, -6.05))
    S += chbox('nose', B, 9.0, 11.95, -5.85, -4.45, c=.22, bottom=True)
    S.append(bar('nose_slope', B - .04, (-4.5, 11.95), (-3.85, 11.0), .5, side='below'))
    S.append(box('nose_light', (8 + B - .02, 10.9, -5.5), (8 + B + .06, 11.3, -5.1)))
    S += chbox('lower_body', B, 9.25, 10.62, -4.45, 4.4, c=.0001, top=False)[:1]
    S += chbox('lower_lip', B, 9.0, 9.25, -4.45, -1.9, c=.0001, top=False)[:1]
    S.append(bx('under_rail', .6, 9.05, 9.25, -1.9, 4.6))
    for k in range(5):
        z = -1.5 + k * 1.15
        S.append(bx(f'under_rail_tooth_{k}', .5, 8.92, 9.05, z, z + .5))
    S += chbox('tube_white', .45, 10.95, 11.85, -4.45, -1.6, c=.14, bottom=True)
    S.append(bx('tube_white_ring', .48, 10.92, 11.88, -2.55, -2.35))
    S += chbox('tube_grey', .42, 11.0, 11.8, -1.6, 4.5, c=.14, bottom=True)
    S += chbox('vent_block', B - .04, 10.62, 11.0, 2.0, 4.4, c=.0001, top=False)[:1]
    for k in range(4):
        z = 2.3 + k * .5
        S.append(box(f'vent_slat_r{k}', (8 + B - .04, 10.68, z), (8 + B + .04, 10.82, z + .25)))
        S.append(box(f'vent_slat_l{k}', (8 - B - .04, 10.68, z), (8 - B + .04, 10.82, z + .25)))
    # one continuous hump ramp (was vent ramp + hump at 3 deg apart); top meets the receiver face under its chamfer
    S.append(bar('hump', B, (1.35, 10.62), (4.4, 11.78), .8, side='below'))
    return S


def middle():
    S = []
    rc = chbox('rcv', B + .02, 9.3, 12.0, 4.4, 9.9, c=.22)
    S += rc[1:]
    S += [bx('rcv_window_front', B + .02, 9.3, 11.78, 4.4, 4.85),
          bx('rcv_window_rear', B + .02, 9.3, 11.78, 6.65, 9.9),
          bx('rcv_window_floor', B + .02, 9.3, 10.1, 4.85, 6.65),
          bx('rcv_window_roof', B + .02, 11.35, 11.78, 4.85, 6.65),
          bx('rcv_window_step', B + .02, 10.1, 10.36, 6.35, 6.65)]
    S.append(bx('rcv_rail', .36, 12.0, 12.1, 4.6, 9.4))
    for k in range(4):
        z = 4.8 + k * .95
        S.append(bx(f'rcv_rail_tooth_{k}', .4, 12.1, 12.18, z, z + .45))
    S.append(box('rcv_sel_r', (8 + B + .02, 9.75, 6.6), (8 + B + .12, 10.05, 7.3)))
    S.append(box('rcv_port_r', (8 + B - .04, 10.55, 7.5), (8 + B + .04, 11.2, 9.3)))
    S.append(bx('frame_lower', .6, 9.02, 9.3, 4.85, 9.2))
    for side, (xa, xb) in (('r', (8 + B + .02, 8 + B + .17)), ('l', (8 - B - .17, 8 - B - .02))):
        h = bar(f'hose_{side}', .1, (8.95, 11.72), (6.75, 10.2), .2)
        h['from'][0], h['to'][0] = xa, xb
        S.append(h)
        for k, f in enumerate((.3, .73)):      # clamps on the hose's own axis (no crossing edges)
            c = bar_on(f'hose_clamp_{side}{k}', .1, (8.95, 11.72), (6.75, 10.2), .34, f - .045, f + .045)
            c['from'][0], c['to'][0] = xa - .025, xb + .025
            S.append(c)
    S.append(bx('guard_front', .1, 8.45, 9.02, 4.6, 4.85))
    S.append(bx('guard_bottom', .1, 8.2, 8.45, 4.6, 6.75))
    S.append(bx('guard_rear', .1, 8.45, 8.9, 6.6, 6.75))
    S.append(bx('trigger_blade', .07, 8.65, 9.3, 5.62, 5.78))
    S.append(bar('trigger_hook', .07, (5.7, 8.72), (5.95, 8.45), .14))
    G = ((7.25, 9.3), (8.5, 6.3))             # one grip axis shared by every grip part
    S.append(vbar('grip_main', .4, *G, 1.6))
    S.append(along('grip_panel', .48, *G, 1.15, .14, .88, off=-.1))
    S.append(along('grip_backstrap', .42, *G, .3, .06, .92, off=.72))
    S.append(along('grip_foot', .48, *G, 2.0, .93, 1.03, off=.1))
    return S


def stock():
    S = []
    S += chbox('stk_body', B, 10.3, 11.4, 9.9, 15.2, c=.0001, top=False)[:1]
    # tapered comb as an axis-aligned step sequence (was a 6.7 deg wedge + cap crossing the stock body)
    for i, top in enumerate((11.95, 11.8, 11.65, 11.5)):
        S += chbox(f'stk_comb{i}', B - .02, 11.4, top, 9.9 + i * 1.325, 9.9 + (i + 1) * 1.325, c=.1)
    S += chbox('stk_tube', .48, 9.6, 10.3, 9.6, 15.2, c=.14, bottom=True, top=False)
    S.append(bx('stk_tube_ring', .52, 9.55, 10.35, 12.4, 12.65))
    S.append(bx('stk_lock', .2, 9.35, 9.6, 13.2, 13.8))
    S.append(bx('butt_trim', B + .02, 8.15, 11.42, 15.1, 15.3))
    S += chbox('butt_pad', B + .05, 8.1, 11.4, 15.3, 16.35, c=.2, bottom=True)
    for k, y in enumerate((8.8, 9.6, 10.4)):
        S.append(bx(f'butt_rib_{k}', B + .09, y, y + .14, 15.5, 16.15))
    return S


def sight():
    # compact box scope inside chattering_bone's hood envelope; aperture y 12.6..13.4, x 7.6..8.4
    S = [bx('sight_bottom', .53, 12.5, 12.6, 6.85, 8.12),
         bx('sight_top', .53, 13.4, 13.5, 6.85, 8.12),
         box('sight_left', (7.47, 12.6, 6.85), (7.6, 13.4, 8.12)),
         box('sight_right', (8.4, 12.6, 6.85), (8.53, 13.4, 8.12)),
         box('sight_dial', (8.53, 12.75, 7.15), (8.72, 13.25, 7.75)),
         bx('sight_hood', .5, 13.35, 13.5, 6.72, 6.85),
         bx('sight_mount', .36, 12.18, 12.5, 7.0, 8.0),
         bx('sight_mount_foot', .42, 12.18, 12.3, 6.7, 8.1)]
    return S


def magazine():
    return [bx('mag_front', .42, 5.75, 9.6, 9.9, 10.28),
            bx('mag_rear', .42, 5.75, 9.6, 11.45, 11.92),
            bx('mag_bottom', .42, 5.7, 6.42, 10.28, 11.45),
            bx('mag_cell', .3, 6.42, 7.05, 10.28, 11.45),
            bx('mag_contact', .16, 7.05, 7.25, 10.55, 11.15),
            bx('mag_top_lip', .45, 9.35, 9.6, 9.85, 11.97),
            bar('mag_cable', .12, (11.35, 9.0), (10.95, 7.1), .22)]


def _move(e, dz, dy=0.0):
    e['from'][2] += dz; e['to'][2] += dz; e['from'][1] += dy; e['to'][1] += dy
    if 'rotation' in e: e['rotation']['origin'][2] += dz; e['rotation']['origin'][1] += dy
    return e


def elements():
    out = [_move(e, DZ) for e in front() + middle() + stock() + magazine()]
    out += sight()
    return out


def _extra(e, fn, s, t):
    n = e['name']
    if n in ('sight_bottom', 'sight_top', 'sight_left', 'sight_right', 'sight_hood') and fn in ('north', 'south'):
        return (52, 64, 68, 255) if min(s, 1 - s, t, 1 - t) < .3 else (30, 36, 38, 255)
    if n.startswith('rcv_rail') or n.startswith('vent_slat') or n.startswith('under_rail_tooth') or n == 'rcv_port_r':
        return (40, 44, 46, 255)
    if n.startswith('hose_clamp') or n == 'mag_contact' or n == 'stk_tube_ring':
        return (176, 190, 196, 255)
    if n == 'nose_light':
        return (120, 200, 210, 255)
    return None


special = Painter(__file__, model2world, extra=_extra,
                  flat={'grip_panel': (78, 72, 68), 'grip_backstrap': (66, 62, 60), 'grip_foot': (60, 56, 54), 'butt_rib': (44, 42, 42),
                        'stk_lock': (60, 62, 64), 'muzzle_crown': (36, 38, 40), 'guard_rear': (78, 74, 70)})


# W325 style pass: Dead Man Walking break-up of long slabs + Minecraft pixel palette (kit STYLE 'pixel')
from w325_5_lib import machined as _machined
_elements_raw = elements


def elements():
    return _machined(_elements_raw())


PALETTE = 18


# W325 cleanup pass: no coplanar overlapping faces (z-fight slivers)
from w325_5_lib import dezfight as _dezfight
_elements_unclean = elements


def elements():
    return _dezfight(_elements_unclean())


# Pixel glyphs retained solely for source manufacturer decals.
import kit as _kit
_FONT = {
 'O': ('111','101','101','101','111'), 'M': ('10001','11011','10101','10101','10001'),
 'L': ('100','100','100','100','111'), 'N': ('1001','1101','1011','1001','1001'),
 'S': ('111','100','111','001','111'), 'U': ('101','101','101','101','111'),
 'R': ('110','101','110','101','101')}

def _lettering(text, s, t, rect):
    a,b,c,d=rect
    if not a <= s < c or not b <= t < d: return False
    glyphs=[_FONT[x] for x in text]
    width=sum(len(g[0])+1 for g in glyphs)-1
    x=int((s-a)/(c-a)*width); y=min(4,int((t-b)/(d-b)*5))
    for g in glyphs:
        if x < len(g[0]): return g[y][x]=='1'
        x-=len(g[0])+1
        if x < 0: return False
    return False

# Remove shared world-plane slivers even when rotations have different origins.
from identity_geometry import clean as _identity_clean
_identity_unclean = elements
def elements():
    return _identity_clean(_identity_unclean())


# W325 material pass: original relief over explicitly assigned W123-like surfaces.
STYLE = 'material'
T = 20
ATLAS = 1024  # scratch atlas; identity_pack.py repacks losslessly after the material bake

def grade(rgb): return tuple(int(max(0,min(255,c))) for c in rgb)
_material_source = Painter(__file__, model2world)
_material_geometry = {e['name']:e for e in elements()}
_material_quality = {}

def _source_sample(e, face, s, t):
    view=_material_source._view(e,face)
    wp=model2world(e['name'],_kit.face_point(e,face,s,t)); x,y=view.project(wp)
    depth=view.depth_at(x,y)
    if depth is None or depth>sum(wp[k]*view.d[k] for k in range(3))+_material_source.occ: return None
    return view.sample(x,y)

def _finish_material(key,name,face):
    # Thin bevels, end caps and poorly covered projections receive material grain without projected smears.
    m=MATERIALS[key]
    if m['kind'] in ('lens','glow','dark'): return key
    cache=(name,face)
    if cache not in _material_quality:
        e=_material_geometry[name]
        valid=sum(_source_sample(e,face,(i+.5)/5,(j+.5)/5) is not None for i in range(5) for j in range(5))
        _material_quality[cache]=valid/25
    if _material_quality[cache]<.6 or face in ('north','south') or '_topch_' in name or '_botch_' in name:
        return dict(m,detail=0)
    return key
MATERIALS = {
 'teal_enamel':dict(kind='paint',color=(43,78,86),detail=.8,amp=3),
 'white_ceramic':dict(kind='paint',color=(184,204,211),detail=.6,amp=2),
 'gunmetal':dict(kind='metal',color=(55,64,65),detail=.55,amp=8),
 'steel':dict(kind='steel',color=(143,172,183),detail=.5,amp=10),
 'polymer':dict(kind='polymer',color=(65,61,57),detail=.55,amp=5),
 'rubber':dict(kind='rubber',color=(28,31,31),detail=.3,amp=6),
 'recess':dict(kind='dark',color=(18,27,31),detail=0),
 'lens':dict(kind='lens',color=(41,94,111),detail=0),
 'cell_glow':dict(kind='glow',color=(94,174,187),detail=.1),
 'contact':dict(kind='steel',color=(170,186,163),detail=.3,amp=8)}
def material(name,face):
    key='teal_enamel'
    if name.startswith(('tube_white','rcv_window_rear','frame','guard','mag_bottom','mag_top','butt_trim')): key='white_ceramic'
    if name.startswith(('stk_tube','hose_clamp','rcv_sel')): key='steel'
    if name.startswith(('tube_grey','rcv_rail','under_rail','vent')): key='gunmetal'
    if name.startswith('grip'): key='polymer'
    if name.startswith(('grip_panel','butt_pad','butt_rib','hose_','mag_cable')): key='rubber'
    if name.startswith('hose_clamp'): key='steel'
    if name.startswith(('rcv_port','muzzle_crown','stk_lock')): key='recess'
    if name.startswith('sight_') and face in ('north','south'): key='lens'
    if name in ('nose_light','mag_cell'): key='cell_glow'
    if name=='mag_contact': key='contact'
    # Physical hose already carries the depth; its projected silhouette would double the hose on this panel.
    if name.startswith('rcv_window_rear'): return dict(MATERIALS[key],detail=0)
    return _finish_material(key,name,face)
def special(e,fn,s,t):
    n=e['name']; side=fn in ('east','west')
    if n=='tube_grey' and side and _lettering('OMOLON',s,t,(.06,.18,.94,.8)): return (81,159,156,255)
    if n=='stk_body_s1' and side and _lettering('OMOLON',s,t,(.2,.42,.64,.68)): return (191,213,217,255)
    if n=='nose_light' and s<.2: return (219,249,255,255)
    if n=='mag_cell' and .15<s<.24: return (185,238,238,255)
    if n=='sight_dial' and side:
        r=((s-.5)**2+(t-.5)**2)**.5
        if .3<r<.4: return (174,207,217,255)
    return None

# W325 material R2: exposed mechanisms, legible material contrast, restrained hand-painted motifs.
_material_r1 = material
_special_r1 = special

def _r2_pixels(e,fn,s,t):
    _,u,v=_kit.face_frame(e,fn)
    w=max(1,round(sum(c*c for c in u)**.5*T)); h=max(1,round(sum(c*c for c in v)**.5*T))
    return min(w-1,int(s*w)),min(h-1,int(t*h)),w,h

FINAL_ATLAS = (512, 512)
MATERIALS['polymer']['color'] = (66, 63, 59)
MATERIALS['rubber']['color'] = (20, 24, 22)
MATERIALS['gunmetal']['color'] = (85, 98, 103)
MATERIALS['steel']['color'] = (167, 190, 201)
MATERIALS['white_ceramic'].update(kind='steel',color=(167,190,201),amp=10)

def material(name,face):
    original=_material_r1(name,face)
    m=MATERIALS[original] if isinstance(original,str) else original
    if m['kind'] in ('dark','lens','glow'): return original
    if name.startswith(('tube_white', 'frame', 'guard', 'butt_trim', 'trigger', 'muzzle_cap')): return _finish_material('steel',name,face)
    return original

def special(e,fn,s,t):
    n=e['name']; side=fn in ('east','west'); i,j,w,h=_r2_pixels(e,fn,s,t)
    if n=='rcv_window_rear' and side:
        if i in (3,w-4) and j in (3,h-4): return (78,108,119,255)
        if j==h-5 and 5<i<w-5 and i%6<3: return (78,108,119,255)
    return _special_r1(e,fn,s,t)
