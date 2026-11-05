"""W325 Rest for the Wicked (rare sword, Adaptive) over base abide_the_return (single sword leaf, no magazine).

Rip: blade along rip +z, width along rip y (point on +y, slotted spine bar on -y), thickness rip x.  Uniform 21.6 px/m
proper rotation: grip centre (rip z 0.02, hilt axis y -0.015) -> model (Y 6.07, Z 7.7, X 8) = base grip centre; point
side (+y) -> -Z like the base cutting margin.  Pommel Y 3.3 (base 2.5), tip Y 31.3 (base 31.5); blade Z 6.8..9.4
(the wide cleaver blade reaches 0.8 px further toward +Z than the base back rail).  The open slot between the spine
bar and the blade (rip z 0.44..1.0) is real geometry, bridged at z 0.54-0.56 like the rip.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_m10'))
from m10 import RipMap, box, bar, slant_tip, rc, face_xyz

S = 21.6
M = RipMap(S, (-0.015, 0.02), (7.7, 6.07), along='y', up='z', muzzle='+')
T = 20
FLAT_TOL = 34
PALETTE = 16


def is_magazine(n): return False


def R(name, hw, yr, zr, **kw): return M.rb(name, hw, yr, zr, **kw)


def RC(name, hw, yr, zr, c, top=True, bottom=True): return rc(M, name, hw, yr, zr, c, top, bottom, axis='y')


def elements():
    E = []
    # pommel + ribbed grip with screw
    E += RC('pommel', 0.0175, (-0.040, 0.011), (-0.105, -0.075), 0.12)
    E.append(R('pommel_cap', 0.0150, (-0.036, 0.007), (-0.110, -0.105)))
    E.append(R('grip', 0.0140, (-0.033, 0.0025), (-0.075, 0.115)))
    for i in range(6):
        z = -0.060 + i * 0.026
        E.append(R(f'grip_rib{i}', 0.0155, (-0.0345, 0.004), (z, z + 0.010)))
    E.append(R('grip_screw', 0.0165, (-0.020, -0.010), (0.098, 0.108)))
    # stepped black guard: neck, two collars, chamfered plate
    E += RC('guard_neck', 0.0095, (-0.0427, 0.0135), (0.115, 0.180), 0.1)
    for i, z in enumerate((0.125, 0.160)):
        E.append(R(f'guard_collar{i}', 0.0110, (-0.046, 0.017), (z, z + 0.010)))
    E += RC('guard_plate', 0.012, (-0.050, 0.021), (0.180, 0.205), 0.12)
    # blade: dark frame, grey riveted centre panel (raised), open slot to the spine bar, white bevelled point edge
    E.append(R('blade_root', 0.0112, (-0.0477, 0.0185), (0.205, 0.300)))
    E.append(R('blade_low', 0.0100, (-0.0515, 0.0185), (0.300, 0.760)))
    E.append(R('blade_high', 0.0100, (-0.0515, 0.0273), (0.760, 0.960)))
    E.append(R('panel', 0.0118, (-0.044, 0.010), (0.215, 0.955)))
    E.append(R('edge_low', 0.0070, (0.0185, 0.0215), (0.300, 0.760)))
    E.append(R('edge_high', 0.0070, (0.0273, 0.0303), (0.760, 1.000)))
    E.append(R('web_low', 0.0112, (-0.094, -0.0515), (0.300, 0.440)))
    E.append(R('web_mid', 0.0112, (-0.094, -0.0515), (0.540, 0.565)))
    E.append(R('spine', 0.0112, (-0.094, -0.0677), (0.440, 1.000)))
    E.append(R('spine_edge', 0.0070, (-0.097, -0.094), (0.440, 1.000)))
    E.append(R('tip_body', 0.0112, (-0.0515, 0.0273), (0.960, 1.040)))
    E += slant_tip(M, 'tip', 0.0112, (-0.094, 1.0), (0.0273, 1.150), 0.995, t_px=0.9, steps=5)
    return E


def model2world(name, p):
    return M.w(p)


COL = {'pommel': (150, 152, 150), 'pommel_cap': (120, 122, 120), 'grip': (140, 142, 140), 'grip_rib': (104, 106, 104),
       'grip_screw': (200, 200, 196), 'guard': (36, 38, 40), 'guard_collar': (60, 62, 64), 'blade': (52, 54, 56),
       'panel': (132, 134, 132), 'edge': (214, 216, 214), 'web': (40, 42, 44), 'spine': (40, 42, 44),
       'spine_edge': (90, 92, 94), 'tip': (44, 46, 48), 'tip_slant': (214, 216, 214)}


def special(e, fn, s, t):
    n = e['name']
    if n == 'tip_slant': return (214, 216, 214, 255) if fn == 'up' else (44, 46, 48, 255)
    if n == 'panel' and fn in ('east', 'west'):
        x, y, z = face_xyz(e, fn, s, t); w = M.w((x, y, z))
        for rz in (0.30, 0.42, 0.54, 0.66, 0.78, 0.90):
            for ry in (-0.036, 0.003):
                if abs(w[2] - rz) < 0.006 and abs(w[1] - ry) < 0.004: return (200, 200, 196, 255)
        if abs(w[2] - 0.215) < 0.004 or abs(w[2] - 0.955) < 0.004: return (90, 92, 94, 255)
    best = None
    for k in COL:
        if n.startswith(k) and (best is None or len(k) > len(best)): best = k
    return COL[best] + (255,) if best else None


# Identity pass: direct face paint with crisp material edges and source-specific markings.
from identity import install
install(globals(), 'rest_for_the_wicked')

# Material pass supersedes all-face flat paint; geometry retained.
from materials import install as install_materials
install_materials(globals(), 'rest_for_the_wicked')
