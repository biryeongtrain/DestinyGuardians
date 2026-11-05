"""Deterministic W325 identity paint; explicit clean pixel details from the six rip views.
Copied into each owned weapon directory so every design remains independently reproducible.
"""
import math
from _w3lib import face_pt, tidy

FONT = {
'S':['111','100','111','001','111'], 'U':['101','101','101','101','111'],
'R':['110','101','110','101','101'], 'O':['111','101','101','101','111'],
'V':['101','101','101','101','010'], 'E':['111','100','110','100','111'],
'I':['111','010','010','010','111'], 'T':['111','010','010','010','010'],
'M':['10001','11011','10101','10101','10001'], 'L':['100','100','100','100','111'],
'N':['1001','1101','1011','1001','1001'],
}

def glyph(text, x, y, x0, y0, scale, mirror=False):
    if mirror:
        width=sum(len(FONT[ch][0])+1 for ch in text)-1
        x=2*x0+width*scale-x
    x = math.floor((x-x0)/scale); y = math.floor((y-y0)/scale)
    if not 0 <= y < 5: return False
    for ch in text:
        rows = FONT[ch]; w = len(rows[0])
        if 0 <= x < w: return rows[y][x] == '1'
        x -= w+1
    return False

def shade(c, k): return tuple(max(0,min(255,v+k)) for v in c[:3])
def inrect(x,y,r): return r[0] <= x <= r[2] and r[1] <= y <= r[3]
def line(x,y,x0,y0,x1,y1,width=1.5):
    dx,dy=x1-x0,y1-y0
    u=max(0,min(1,((x-x0)*dx+(y-y0)*dy)/(dx*dx+dy*dy)))
    return (x-x0-u*dx)**2+(y-y0-u*dy)**2 < width*width

def paint_identity(e, fn, s, t, g):
    n=e['name']; wid=g['IDENTITY_ID']; T=g['T']; f, to=e['from'],e['to']
    axes={'north':(0,1),'south':(0,1),'west':(2,1),'east':(2,1),'up':(0,2),'down':(0,2)}[fn]
    w=max(1,round((to[axes[0]]-f[axes[0]])*T)); h=max(1,round((to[axes[1]]-f[axes[1]])*T))
    i,j=min(w-1,int(s*w)),min(h-1,int(t*h))
    p=face_pt(e,fn,s,t); ix,iy=g['ix_of'](p[2]),g['iy_of'](p[1]); side=fn in ('east','west')
    old=g['_base_paint'](e,fn,s,t)
    c=old[:3] if old else (68,70,72)
    # Surface identity details use continuous gun coordinates across the flush body segments.
    if wid=='thistle_and_yew':
        if n.startswith(('forend_upper','forend_lower','lower_rcv')): c=g['POLY']
        if side and n.startswith(('stock','web_plate','grip')):
            c=g['POLY_D'] if n.startswith('web_plate') else c
            if n.startswith(('stock_low','stock_web','grip')) and 3<i<w-3 and 3<j<h-3 and (i+j)%6==0: c=shade(c,-19)
            # triangular reinforcement plate, accurately located in the rear stock web.
            if n.startswith('web_plate'):
                u,v=s,t
                if min(abs(v-.15),abs(v-(.15+.67*u)),abs(u-.85))<.045: c=(146,147,145)
                if .12<u<.84 and .2<v<.7 and abs(v-(.27+.45*u))<.035: c=(26,29,30)
        if side and n.startswith(('receiver','rcv_rear')):
            if line(ix,iy,278,55,480,55,1.1): c=(78,97,119)
            if 279<ix<285 and 23<iy<47: c=(182,193,204)
            if 350<ix<367 and 48<iy<50: c=(52,67,85)
        if n.startswith('bolt') and side:
            if .12<t<.35: c=(161,166,172)
            if .55<s<.62: c=(22,25,29)
        if n.startswith(('mag_body','mag_window')) and side:
            if i in (3,w-4) or j in (4,h-5): c=(110,114,118)
            if .22<s<.78 and .23<t<.77 and (i%12 in (0,1)): c=(20,23,25)
        if n.startswith('supp') and side and .2<t<.8:
            if .23<s<.25 or .74<s<.76: c=(99,102,106)
    elif wid=='armillary_psu':
        # Original is navy enamel with white edge abrasion, not blue/white camouflage.
        if n.startswith(g['CAMO']): c=g['NAVY']
        if n.startswith(('spine','mid_','stock_body','stock_panel','web_','grip','tg_','mag_','fil_')): c=(44,47,48)
        if n.startswith(('rcv_band','forend_rib','rail_rib','bipod','muzzle')): c=(211,211,205)
        if n.startswith(('shroud','top_bar')): c=(38,40,43)
        if side and n.startswith(('rcv_top','forend','stock_panel','rcv_lower')):
            if j in (3,h-4) or i in (3,w-4): c=(144,158,175) if n.startswith(('rcv_top','forend','rcv_lower')) else (75,81,83)
        if side and n.startswith(('forend_rib','rail_rib')) and 2<j<h-3:
            if i%7 in (0,1): c=(85,89,92)
        if n.startswith('mag_panel') and side:
            if i%max(8,w//4) in (1,2) or j in (h//3,2*h//3): c=(109,114,116)
        if n.startswith('sight') and side and .28<s<.72 and .25<t<.78:
            d=math.hypot((s-.5)*1.2,t-.5)
            if .19<d<.24:c=(184,192,202)
            elif d<.16:c=(51,63,80)
    elif wid=='sonata_48':
        if n.startswith(('muzzle','spike')): c=g['WHITE_']
        if n.startswith('logo_slot'): c=(18,23,25)
        if side and n.startswith(('body_mid','red_band')):
            c=g['RED_'] if iy<=104 else g['DARK_']
            if glyph('SUROS',ix,iy,288,88,2.2,fn=='west'):c=g['MINTG']
            if 278<ix<286 and 91<iy<99 or 280<ix<295 and 88<iy<91:c=g['MINTG']
            if line(ix,iy,186,102,516,102,1.0): c=(112,28,32)
        if side and n.startswith(('top_front','body_upper','body_rear_panel')):
            if j==3 or j==h-4: c=(127,154,148)
            if i==3 or i==w-4: c=(204,218,212)
        if n.startswith('sight_vents') and side:
            if .12<t<.88 and (i+int(j*.45))%16<3:c=(156,175,180)
        if n.startswith(('grip','handguard','mag_')) and side:
            if 3<i<w-3 and 3<j<h-3 and (i+j)%5==0:c=(33,36,38)
            if n.startswith('mag_rib') and (i in (3,w-4) or j in (3,h-4)):c=(98,105,106)
    elif wid=='inverness_sr2':
        if n.startswith('cable'): c=(26,29,28)
        if side and n.startswith(('body_upper','receiver','front_block','stock_top')):
            # Stamped border and silvery lower plate; purple enamel remains a clean flat material.
            if j in (3,h-4):c=(128,117,140)
            if i in (3,w-4):c=(58,52,66)
        if n.startswith(('rcv_vents','stock_ribs')) and side:
            c=(117,120,122) if i%5<2 else (25,28,31)
        if n.startswith('body_panel') and side:
            if .15<t<.85 and abs(s-.2)<.03:c=(161,159,165)
            if .62<t<.7 and .3<s<.9:c=(148,145,152)
        if n.startswith('mag_panel') and side:
            c=(55,62,61) if ((i//5+j//6)%3==0) else (40,46,44)
            if .11<t<.19 and .4<s<.6:c=(142,150,148)
            if i in (3,w-4) or j in (3,h-4):c=(102,110,108)
    elif wid=='black_tiger_2sr':
        if n.startswith('veist_plate'):
            c=g['MINT'];
            if side and glyph('VEIST',ix,iy,165,109,2.0,fn=='west'):c=(154,75,27)
            if side and 153<ix<164 and 110<iy<117 and iy-110<(ix-153)*.65:c=(154,75,27)
        if n.startswith('shroud'):c=g['MINT']
        if n.startswith(('upper','up_','shroud')) and side:
            if j in (3,h-4):c=(164,183,167)
            if n.startswith('shroud'):
                for cx,cy in ((535,72),(544,82),(535,92)):
                    if (ix-cx)**2+(iy-cy)**2 < 3.6**2:c=(15,25,21)
        if n.startswith('win_cart') and side:
            c=(194,107,45) if i%8<5 else (93,52,30)
            if j==2:c=(237,163,79)
        if n.startswith('win_mag') and side:
            if .65<s<.95 and (i+j)%12<3:c=(176,187,179)
        if n.startswith(('grip','low_')) and side and 3<i<w-3 and 3<j<h-3:
            if (i+j)%7==0:c=(22,28,25)
        if n.startswith('claw_'):c=g['MINT_D']
        if n.startswith('ejector') and side and i%5<2:c=(83,100,89)
    elif wid=='madrugada_sr2':
        if n.startswith('port_depth'):c=g['BONE']
        if n.startswith(g['CAMO']):
            # Rip has olive camouflage; bone is reserved for the structural frame.
            from _w3lib import blob
            v=blob(p,.65,.4); c=(57,75,35) if v>.2 else (98,117,59) if v<-.3 else (73,93,42)
        if side and n.startswith('receiver') and 48<iy<68:
            if glyph('OMOLON',ix,iy,310,51,2.25,fn=='west'):c=(163,53,41)
        if n.startswith('port_ring') and side:
            for cx,cy,r in g['PORTS']:
                d=math.hypot(ix-cx,iy-cy)
                if r-2<d<r+2:c=(55,58,51)
                elif r+2<d<r+5:c=g['BONE']
        if n.startswith(('stock','receiver','rcv_low','fixed_mag')) and side:
            if j in (3,h-4):c=(132,145,99)
        if n.startswith('front_vents') and side:
            c=(214,211,200) if j%6<3 else (22,24,25)
        if n.startswith('canister') and side and i in (3,w-4):c=(208,199,170)
        if n.startswith('grip') and side and j%5==0:c=(84,87,77)
    if n=='muzzle_inner':c=(27,29,31)
    if wid=='black_tiger_2sr' and n.startswith('shroud') and fn=='north' and not n.startswith('shroud_tip'):
        if .2<s<.8 and .2<t<.8:c=(21,28,24)
    # Material-grounded fasteners: receiver/stock panel corners only, 2 texels with a 1 texel slot.
    panel=n.startswith(('receiver','rcv_top','stock_panel','body_panel','upper_front','front_plate','mag_panel','web_plate'))
    if panel and side and w>=15 and h>=12:
        for xx in (4,w-5):
            for yy in (4,h-5):
                if abs(i-xx)<=1 and abs(j-yy)<=1:c=shade(c,45) if j!=yy else shade(c,-38)
    if n.startswith(('grip','mag_')) and side and w>12 and h>12:
        if i in (2,w-3) or j in (2,h-3):c=shade(c,15)
    # Crisp one-texel bright upper edge / dark lower seam on every visible face.
    if w>3 and h>3:
        if j==0:c=shade(c,23)
        elif j==h-1:c=shade(c,-27)
        elif i==0:c=shade(c,10)
        elif i==w-1:c=shade(c,-16)
    if n.startswith(('sight','peep','sc_')) and fn in ('north','south'):
        # small tinted emitter on the housing, never glass filling an open aim window.
        if w>=8 and h>=5 and i==w//2 and j==h//2:c=(110,190,194)
    return (*c,255)


def cube(n,f,t):return {'name':n,'from':list(f),'to':list(t)}

def hollow(e,thick=.11):
    f,t=e['from'],e['to'];n=e['name']
    return [cube(n+'_top',(f[0],t[1]-thick,f[2]),t),cube(n+'_bottom',f,(t[0],f[1]+thick,t[2])),
            cube(n+'_left',(f[0],f[1]+thick,f[2]),(f[0]+thick,t[1]-thick,t[2])),
            cube(n+'_right',(t[0]-thick,f[1]+thick,f[2]),(t[0],t[1]-thick,t[2]))]

def cage(e,bays=7):
    f,t=e['from'],e['to'];n=e['name'];out=[];th=.1
    out.extend([cube(n+'_top',(f[0],t[1]-th,f[2]),t),cube(n+'_bottom',f,(t[0],f[1]+th,t[2]))])
    # Real side windows between transverse ribs; recessed dark barrel is visible through them.
    yc=(f[1]+t[1])/2
    out.append(cube(n+'_centre_rail',(f[0],yc-.045,f[2]),(t[0],yc+.045,t[2])))
    out.append(cube(n+'_inner',(7.88,yc-.11,f[2]),(8.12,yc+.11,t[2])))
    step=(t[2]-f[2])/bays
    for k in range(bays+1):
        z=f[2]+k*step
        z0,z1=max(f[2],z-.065),min(t[2],z+.065)
        for tag,x0,x1 in [('l',f[0],f[0]+th),('r',t[0]-th,t[0])]:
            out.append(cube(n+'_vent_'+tag+str(k),(x0,f[1]+th,z0),(x1,t[1]-th,z1)))
    return out

def cut_yz(e,y0,y1,z0,z1):
    if e.get('rotation'):return [e]
    f,t=e['from'],e['to'];ya,yb=max(y0,f[1]),min(y1,t[1]);za,zb=max(z0,f[2]),min(z1,t[2])
    if ya>=yb or za>=zb:return [e]
    specs=[(f,(t[0],ya,t[2])),((f[0],yb,f[2]),t),((f[0],ya,f[2]),(t[0],yb,za)),((f[0],ya,zb),(t[0],yb,t[2]))]
    return [cube(e['name']+'_cut'+str(k),a,b) for k,(a,b) in enumerate(specs) if all(b[i]-a[i]>.015 for i in range(3))]

def enrich_geometry(els,g):
    wid=g['IDENTITY_ID'];out=[]
    for e in els:
        n=e['name']
        if wid in ('armillary_psu','sonata_48') and n=='muzzle':out+=cage(e,7);continue
        if wid in ('armillary_psu','sonata_48') and n=='muzzle_r45':continue
        if (wid in ('armillary_psu','sonata_48') and n in ('muzzle_cap','muzzle_tip','spike')) or (wid=='thistle_and_yew' and n=='supp_cap') or (wid=='black_tiger_2sr' and n=='shroud_tip'):
            out+=hollow(e,.10);continue
        if wid=='sonata_48' and n=='spike_r45':continue
        out.append(e)
    if wid=='inverness_sr2':
        # The characteristic dark external cable follows the reference rising curve; flush joined square elbows.
        pts=[(390,105),(430,101),(465,85),(505,75),(545,72)]
        for side,xc in [('l',7.37),('r',8.63)]:
            for k,((xa,ya),(xb,yb)) in enumerate(zip(pts,pts[1:])):
                z0,z1=sorted((g['Z'](xa),g['Z'](xb)));Y0,Y1=g['Y'](ya),g['Y'](yb);hw=.055
                out.append(cube('cable_'+side+str(k),(xc-hw,Y0-hw,z0),(xc+hw,Y0+hw,z1)))
                if abs(Y1-Y0)>.01:out.append(cube('cable_elbow_'+side+str(k),(xc-hw,min(Y0,Y1),z0-hw),(xc+hw,max(Y0,Y1),z0+hw)))
    if wid=='madrugada_sr2':
        # True through-body side apertures, square bevel interpretation of the two circular Omolon ports.
        for k,(ix,iy,r) in enumerate(g['PORTS']):
            zc,yc=g['Z'](ix),g['Y'](iy);rr=r*.036*.72
            tmp=[]
            for e in out:
                if e['name'].startswith(('receiver','rcv_low','port_ring','fixed_mag')):tmp+=cut_yz(e,yc-rr,yc+rr,zc-rr,zc+rr)
                else:tmp.append(e)
            out=tmp
            for side,xc in [('l',7.245),('r',8.755)]:
                d=.07
                out.extend([cube(f'port_depth_{k}_{side}_top',(xc-d,yc+rr,zc-rr-d),(xc+d,yc+rr+d,zc+rr+d)),
                            cube(f'port_depth_{k}_{side}_bot',(xc-d,yc-rr-d,zc-rr-d),(xc+d,yc-rr,zc+rr+d)),
                            cube(f'port_depth_{k}_{side}_l',(xc-d,yc-rr,zc-rr-d),(xc+d,yc+rr,zc-rr)),
                            cube(f'port_depth_{k}_{side}_r',(xc-d,yc-rr,zc+rr),(xc+d,yc+rr,zc+rr+d))])
    if wid=='sonata_48':
        for e in out:
            if e['name']=='mag_lip': e['to']=list(e['to']); e['to'][1]-=.012
    # Preserve reload anchors; Sonata's lip top alone is recessed to remove an existing coplanar face.
    return tidy([e for e in out if not e['name'].startswith('mag_')])+[e for e in out if e['name'].startswith('mag_')]
