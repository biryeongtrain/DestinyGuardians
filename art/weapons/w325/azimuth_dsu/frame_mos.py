"""Shared Mos Ultima / Azimuth frame (identical receiver and grip in both rips): DMW-style machined geometry in rip
image px (nx view) through the design's calibration.  Copied verbatim into mos_ultima_ii/ and azimuth_dsu/."""
import math
from hc import box, tb_from, hsq, bev_x, drum, bolt, muzzle_ring, ads_clip, slab, grip_stack, deconflict


def frame(C, GP0, GT, GK, base, top_y=None, front_cuts=(), extra=None, clipped=None, strap_cap=99.0):
    z, y = C.z, C.y; R = C.R; E = []
    sq = lambda xi, yi: hsq(GP0, GT, GK, z(xi), y(yi))
    ty = top_y if top_y is not None else y(30)
    # long shroud: chamfered segments, dark top rib with slots (painted), separate front face plate
    E += slab('shroud', 7.12, 8.88, y(85), ty, z(386), z(163), c=.18, cuts=front_cuts)
    ry = min(ty + (y(22) - y(30)), strap_cap - .1)
    E.append(box('top_rib_floor', [7.4, ty, z(386)], [8.6, ty + .05, z(150)]))
    E.append(box('top_rib_roof', [7.4, ry - .06, z(386)], [8.6, ry, z(150)]))
    for i, xi in enumerate((150, 180, 211, 242, 273, 304, 335, 366, 382)):
        E.append(box(f'top_rib_spacer_{i}', [7.4, ty+.05, z(xi+4)], [8.6, ry-.06, z(xi)]))
    E.append(box('shroud_face', [7.24, y(83), z(391)], [8.76, ty - .06, z(386)]))
    E += muzzle_ring('muzzle_bore', 8.0, y(68), .48, .24, z(391) - .06, z(388), depth=.3)
    E.append(box('sight_front', [7.93, ty + (y(22) - y(30)), z(384)], [8.07, ty + (y(22) - y(30)) + .14, z(376)]))
    # frame: top strap (segmented), window bottom, recoil shield, lower front with chin, latch
    sy = min(ty + (y(17) - y(30)), strap_cap)
    E += slab('top_strap', 7.4, 8.6, ty, sy, z(163), z(95), c=.1, cuts=(z(130),), bottom=False)
    E.append(R('frame_window_low', 92, 80, 163, 92, 7.2, 8.8))
    E.append(R('frame_rear', 88, 28, 102, 92, 7.2, 8.8))
    E += slab('frame_lower', 7.25, 8.75, y(113), y(85), z(198), z(150), c=.14, top=False)
    E.append(R('frame_chin', 195, 85, 215, 100, 7.25, 8.75))
    E.append(bev_x('frame_chin_nose', 7.25, 8.75, y(85) + .01, z(215), .22, -1))
    E.append(R('latch', 160, 55, 177, 72, 7.08, 8.92))
    for sd, t in ((-1, 'w'), (1, 'e')):
        xf = 7.12 if sd < 0 else 8.88
        E.append(bolt(f'bolt_{t}0', z(178), y(39), xf, sd, s=.24))
        E.append(bolt(f'bolt_{t}1', z(208), y(84), 7.25 if sd < 0 else 8.75, sd, s=.22))
        xa, xb = (6.98, 7.16) if sd < 0 else (8.84, 9.02)        # crisp window rims
        E.append(box(f'rim_{t}_top', [xa, y(33), z(163)], [xb, y(30), z(100)]))
        E.append(box(f'rim_{t}_bot', [xa, y(82), z(163)], [xb, y(79), z(100)]))
    # trigger guard (real opening, rounded corners) + trigger
    E.append(R('guard_bottom', 95, 121, 142, 128, 7.74, 8.26))
    E.append(R('guard_front', 140, 96, 150, 122, 7.74, 8.26))
    E.append(R('guard_rear', 88, 96, 96, 124, 7.74, 8.26))
    for tag, xi, yi in (('f', 141, 121), ('r', 94, 121)):
        zz, yy = z(xi), y(yi)
        E.append(box(f'guard_corner_{tag}', [7.74, yy - .2, zz - .2], [8.26, yy + .2, zz + .2],
                     rotation={'origin': [8.0, yy, zz], 'x': 45, 'y': 0, 'z': 0}))
    E.append(R('trigger', 103, 98, 112, 119, 7.88, 8.12))
    # hammer with spur, notch rear sight
    E.append(R('hammer', 70, 30, 88, 44, 7.62, 8.38))
    E.append(R('hammer_spur', 64, 26, 76, 32, 7.7, 8.3))
    E.append(box('sight_rear_base', [7.42, sy - .02, z(110)], [8.58, sy + .08, z(90)]))
    for tag, xa, xb in (('l', 7.42, 7.72), ('r', 8.28, 8.58)):
        E.append(box(f'sight_rear_{tag}', [xa, sy + .08, z(110)], [xb, sy + .26, z(90)]))
    # dark rear frame + grip (squeezed): two raked blocks, side panels, medallions, slanted heel plate
    E.append(box('grip_frame', [7.25, y(100), z(100)], [8.75, y(40), sq(52, 60)[0]]))
    def gline(f_top, f_bot, back_top, back_bot):
        t = sq(*f_top); bt = sq(*f_bot)
        return t, bt, sq(back_top, f_top[1])[0] - t[0], sq(back_bot, f_bot[1])[0] - bt[0]
    t, bt, wt, wb = gline((97, 88), (60, 186), 46, 12)
    E += grip_stack('grip_core', t, bt, wt, wb, 7.22, 8.78, 4, heel=('grip_heel', .6, wb + .2, 7.2, 8.8),
                    panels=('grip_panel_w', 'grip_panel_e', .2, .9, .35, wt * .6, wb * .75, .08))
    mz, my = sq(44, 124)
    for tag, xa, xb in (('l', 7.08, 7.14), ('r', 8.86, 8.92)):
        E.append(box(f'grip_medallion_{tag}', [xa, my - .3, mz - .3], [xb, my + .3, mz + .3]))
    if extra: E += extra()
    E = deconflict(ads_clip(E, base, log=clipped))
    # cylinder (moving part): octagonal drum with end bands + core
    cy = y(55)
    E += drum('mag_drum', (8.0, cy), (y(30) - y(80)) / 2, z(162), z(102), n=4, band=(.14, .04))
    E.append(box('mag_core', [7.78, cy - .22, z(162) - .08], [8.22, cy + .22, z(102) + .02]))
    return E
