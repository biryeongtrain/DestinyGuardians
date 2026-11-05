"""W325 m8 identity pass: authored material edges and rip-specific face graphics.
No rip grime, arbitrary lettering, geometric screw confetti or projection fallback.
"""
import math
import kit
from paint import text_hit, line, every


def tint(c, delta):
    return tuple(max(0,min(255,k+delta)) for k in c[:3])


def rectline(u,v,a,b,c,d,w=.05):
    return a-w < u < b+w and c-w < v < d+w and (abs(u-a)<w or abs(u-b)<w or abs(v-c)<w or abs(v-d)<w)


def screw(u,v,cu,cv,r=.1):
    q=max(abs(u-cu),abs(v-cv))
    if q<r*.4:return (36,37,38)
    if q<r:return (158,162,158) if v>cv else (74,78,75)


def enhance(wid, old, density):
    def special(e,fn,s,t):
        n=e['name']; side=fn in ('west','east')
        x,y,z=kit.face_point(e,fn,s,t)
        c=old(e,fn,s,t) or (65,67,66,255)
        c=c[:3]
        # Authored per-face 1-texel machining edges survive special() preservation.
        _,fu,fv=kit.face_frame(e,fn)
        w=max(1,round(math.dist((0,0,0),fu)*density)); h=max(1,round(math.dist((0,0,0),fv)*density))
        ix,iy=min(w-1,int(s*w)),min(h-1,int(t*h))
        if w>=3 and h>=3:
            if iy==0:c=tint(c,26)
            elif iy==h-1:c=tint(c,-20)
            elif ix==0:c=tint(c,13)
            elif ix==w-1:c=tint(c,-13)
        # Grip checkering uses local face pixels so raked grips keep coherent rows.
        if side and n.startswith(('grip','foregrip')) and not any(q in n for q in ('cap','ch','heel')) and .12<s<.88 and .14<t<.86:
            if (ix%4==0 and iy%4==0) or (ix%4==2 and iy%4==2):c=tint(c,-16)
        if side and any(k in n for k in ('bolt','screw','pin')) and 'slot' not in n:
            c=(144,148,144) if .18<s<.82 and .18<t<.82 else (45,47,45)
            if abs(t-.5)<1/max(h,1):c=(28,29,30)
        if side and n.startswith('mag_body'):
            if every(z,e['from'][2]+.2,.4,.045) and y>e['from'][1]+.6:c=tint(c,-37)
            if line(y,e['from'][1]+.3,.05):c=(72,75,73)
        if wid=='harmony_21':
            if side and n.startswith(('shell_body','shell_tail')) and '_groove' not in n:
                # Long orange SUROS swoosh, tapering toward the forward shell.
                if z>5.3 and 10.5<y<10.5+min(1.4,(z-5.3)*.33):c=(211,116,48)
                if 10.7<y<11.8 and (line(z,4.65,.045) or line(y,11.82,.04)):c=(145,159,153)
                sc=screw(z,y,4.7,11.6,.08)
                if sc:c=sc
            if side and n.startswith('frame_bar'):
                c=(40,44,43) if 0<iy<h-1 else c
                if text_hit(s*w, t*h, 'SUROS', w*.27, 2, 1.5):c=(222,132,61)
            if n.startswith('sight') and fn=='south':
                if .25<s<.75 and .2<t<.45:c=(230,132,54)
            if n.startswith('shell_slot_floor') and fn=='up' and .2<s<.8:c=(60,75,68)
            if side and n.startswith('spine') and 10.45<y<11.15:
                if rectline(z,y,9.3,13.8,10.48,11.12):c=(81,87,81)
        elif wid=='protostar_csu':
            if side and n.startswith('panel'):
                if .08<s<.92 and .16<t<.84:
                    # Cyan screen and twin blue/red indicator lamps with metal bezel.
                    if 6.18<z<6.76:c=(72,155,175) if y<12.49 else (160,220,215)
                    if 5.35<z<6.02 and every(z,5.36,.19,.06):c=(145,151,141) if y>12.44 else (21,29,27)
                    if abs(z-5.28)<.16 and abs(y-12.43)<.16:c=(100,103,89) if max(abs(z-5.28),abs(y-12.43))>.09 else (28,32,29)
                if rectline(s,t,.04,.96,.09,.91,.035):c=(153,156,135)
            if side and n.startswith('rcv'):
                if line(y,11.82,.04):c=(187,193,164)
                for zz in (1.8,8.9,11.8):
                    sc=screw(z,y,zz,12.45,.09)
                    if sc:c=sc
            if side and n.startswith('grip') and .12<s<.85 and .1<t<.83:
                c=(219,205,182) if (ix+iy)%4 else (171,167,140)
            if side and n.startswith('shroud') and not n.startswith('shroud_vent') and 12.2<y<12.75:
                if (int(z*20)+int(y*20))%4==0:c=(181,177,158)
        elif wid in ('philippis_b','sondok_c'):
            import hakke
            zz=hakke.zo(z)
            if n.startswith(('stock_arm','stock_bracket')) and 'web' not in n:
                c=(216,218,205)
                if side and rectline(zz,y,12.3,15.1,11.25,12.1):c=(96,106,94)
            if side and n.startswith('panel'):
                if wid=='sondok_c':
                    # Orange HAKKE plate is at the rear shoulder, not a stripe across the entire receiver.
                    c=(224,92,50) if zz>6.4 else (213,216,204)
                    u=zz if fn=='west' else -zz
                    if text_hit(u,13.4-y,'HAKKE',6.55 if fn=='west' else -8.2,0,.075):c=(242,238,218)
                else:c=(132,134,122)
                if line(y,12.81,.04):c=(55,62,56)
            if side and n.startswith('selector'):
                c=(42,43,37)
                for zz0 in (2.9,4.0):
                    rr=max(abs(zz-zz0),abs(y-12.23))
                    if rr<.2:c=(150,153,135) if rr>.12 else (30,31,27)
                    if abs(zz-zz0)<.04 and 12.22<y<12.39:c=(225,229,214)
                if y>12.58 and every(zz,2.6,.4,.12):c=(219,222,203)
            if side and n.startswith('rcv_main'):
                if 11.74<y<12.24 and 5.25<zz<5.95:
                    if (abs(y-11.98)<.05 or abs(zz-5.42)<.045 or abs(zz-5.8)<.045):c=(225,99,54) if wid=='sondok_c' else (89,105,56)
                if line(y,11.42,.045):c=(103,96,78)
            if side and n.startswith('foregrip') and '_ch' not in n:
                if .15<s<.85 and .18<t<.82:c=(36,40,40)
                if rectline(s,t,.15,.85,.18,.82,.025):c=(116,104,80)
            if side and n.startswith('stock_comb') and line(y,13.22,.045):c=(89,91,80)
            if n.startswith('light_bezel') and fn=='north':
                if .24<s<.64 and .2<t<.35:c=(250,250,223)
        elif wid=='badlands_mk_24':
            if side and n.startswith('shroud_low') and '_groove' not in n:
                # Continuous cream pinstripe with stepped terminations and paired rivets.
                seam=10.64 if z<-.5 else 10.81
                if line(y,seam,.04):c=(210,189,146)
                for zz in (-8.45,-6.8,-4.2,-2,.3,1.65):
                    sc=screw(z,y,zz,11.06,.075)
                    if sc:c=(204,184,143) if sc[0]>100 else (45,43,35)
            if side and n=='pump':
                # Hard-edged hexagonal grip cells, not rectangular masonry.
                row=round((y-9.15)/.34); uz=((z+4.8+(row%2)*.25)%.5)-.25; vy=y-(9.15+row*.34)
                d=max(abs(uz)*.8+abs(vy)*.65,abs(vy))
                c=(67,67,66) if .15<d<.19 else (34,35,35)
            if side and n.startswith('recv_upper'):
                if rectline(z,y,6.65,8.6,10.72,11.6,.04):c=(196,176,139)
        elif wid in ('botheration_mk_28','fussed_dark_mk_21'):
            if n.startswith('can_lip'):c=(100,133,135) if wid=='botheration_mk_28' else (167,177,135)
            if n=='can_face':c=(12,15,15)
            if side and n.startswith(('rcv_upper','recv_rear','recv_front')):
                y0=11.22 if wid=='botheration_mk_28' else 9.65
                if line(y,y0,.045):c=(177,200,190) if wid=='botheration_mk_28' else (208,205,173)
            if side and n.startswith('pump_body'):
                lo=e['from']; hi=e['to']
                if .14<t<.76 and every(z,-4 if wid=='botheration_mk_28' else -1.6,.38,.045):c=(110,88,64) if wid=='botheration_mk_28' else (101,99,79)
                if rectline(s,t,.06,.94,.12,.84,.025):c=(112,91,69) if wid=='botheration_mk_28' else (100,102,82)
            if side and n.startswith(('stock_strut','stock_tube')) and .2<t<.8:
                if rectline(s,t,.12,.88,.24,.7,.025):c=(150,177,170) if wid=='botheration_mk_28' else (192,194,155)
            if side and n=='side_vent':
                if every(z,e['from'][2]+.08,.19,.055):c=(139,159,147)
            if wid=='fussed_dark_mk_21' and n=='bracket_lens' and fn=='north':
                c=(158,183,177)
                if .15<s<.85 and .17<t<.8:c=(221,230,202)
                if .23<s<.45 and .23<t<.35:c=(255,255,243)
            if wid=='fussed_dark_mk_21' and side and n.startswith('shield'):
                if line(y,10.27,.045) or line(y,11.69,.045):c=(218,216,180)
        return tuple(c)+(255,)
    return special
