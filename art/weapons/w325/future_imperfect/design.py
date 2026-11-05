"""W325 Future Imperfect (rare sword, Adaptive) over base abide_the_return (single sword leaf, no magazine).

Rip: blade along rip +z, width along rip y (point/edge on +y), thickness rip x.  Uniform 21.6 px/m proper rotation:
grip centre (rip z 0.047, hilt axis y -0.0145) -> model (Y 6.07, Z 7.7, X 8) = base grip centre; edge (+y) -> -Z
like the base cutting margin.  Pommel Y 2.0 (base 2.5), tip Y 31.0 (base 31.5); straight blade Z 7.2..8.6
(base curved 6.0..8.6).  Blade kept at 0.28 px thickness (rip 0.22) so it stays visible edge-on.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '_m10'))
from m10 import RipMap, box, bar, slant_tip, rc, face_xyz

S = 21.6
M = RipMap(S, (-0.0145, 0.047), (7.7, 6.07), along='y', up='z', muzzle='+')
T = 20
FLAT_TOL = 34
PALETTE = 16


def is_magazine(n): return False


def R(name, hw, yr, zr, **kw): return M.rb(name, hw, yr, zr, **kw)


def RC(name, hw, yr, zr, c, top=True, bottom=True): return rc(M, name, hw, yr, zr, c, top, bottom, axis='y')


def elements():
    E = []
    # pommel: chamfered white cap, neck, collar
    E += RC('pommel_cap', 0.021, (-0.035, 0.006), (-0.130, -0.103), 0.14)
    E.append(R('pommel_neck', 0.010, (-0.026, -0.001), (-0.103, -0.068)))
    E += RC('collar', 0.0175, (-0.032, 0.004), (-0.068, -0.048), 0.1)
    # wrapped grip: core + raised binding bands
    E.append(R('grip', 0.014, (-0.0335, 0.0045), (-0.048, 0.135)))
    for i in range(7):
        z = -0.040 + i * 0.025
        E.append(R(f'grip_wrap{i}', 0.0155, (-0.035, 0.006), (z, z + 0.012)))
    # ferrule with two rings, ricasso block with vents
    E.append(R('ferrule', 0.0160, (-0.034, 0.004), (0.135, 0.192)))
    for i, z in enumerate((0.140, 0.180)):
        E.append(R(f'ferrule_ring{i}', 0.0175, (-0.035, 0.005), (z, z + 0.007)))
    E.append(R('ricasso_root', 0.0115, (-0.045, 0.0074), (0.192, 0.215)))
    E.append(R('ricasso', 0.0125, (-0.0576, 0.0074), (0.215, 0.385)))
    E.append(R('ricasso_plate', 0.0135, (-0.050, -0.010), (0.300, 0.360)))
    # blade: body, darker worn cutting bevel on the edge side, raised spine strip
    E.append(R('blade', 0.0065, (-0.0551, -0.004), (0.385, 1.111)))
    E.append(R('blade_edge', 0.0040, (-0.004, 0.0062), (0.385, 1.111)))
    E.append(R('blade_spine', 0.0075, (-0.0551, -0.048), (0.385, 1.100)))
    E += slant_tip(M, 'tip', 0.0065, (-0.0551, 1.110), (0.0062, 1.165), 1.110)
    return E


def model2world(name, p):
    return M.w(p)


COL = {'pommel': (226, 224, 218), 'collar': (60, 60, 62), 'grip': (64, 64, 66), 'grip_wrap': (118, 118, 116),
       'ferrule': (222, 220, 214), 'ferrule_ring': (90, 90, 92), 'ricasso_root': (90, 90, 92), 'ricasso': (214, 212, 206),
       'ricasso_plate': (200, 198, 192), 'blade': (222, 220, 214), 'blade_edge': (160, 160, 158),
       'blade_spine': (196, 194, 188), 'tip': (222, 220, 214)}


def special(e, fn, s, t):
    n = e['name']
    x, y, z = face_xyz(e, fn, s, t)
    if n == 'ricasso' and fn in ('east', 'west'):
        # three dark vent slots + stamp, like the rip's ricasso
        zr = M.w((x, y, z))[1]
        rz = M.w((x, y, z))[2]
        if 0.235 < rz < 0.255 and -0.040 < zr < 0.0:
            if int((zr + 0.040) / 0.0066) % 2 == 0: return (36, 36, 38, 255)
        if 0.345 < rz < 0.370 and -0.030 < zr < -0.005: return (40, 40, 42, 255)
    if n == 'blade' and fn in ('east', 'west'):
        rz = M.w((x, y, z))[2]; ry = M.w((x, y, z))[1]
        # worn grime streak near the spine, as two flat grey blobs
        if (0.55 < rz < 0.62 or 0.88 < rz < 0.93) and ry < -0.040: return (176, 174, 168, 255)
    best = None
    for k in COL:
        if n.startswith(k) and (best is None or len(k) > len(best)): best = k
    return COL[best] + (255,) if best else None


# Identity pass: direct face paint with crisp material edges and source-specific markings.
from identity import install
install(globals(), 'future_imperfect')

# Material pass supersedes all-face flat paint; geometry retained.
from materials import install as install_materials
install_materials(globals(), 'future_imperfect')
