"""W325 m10 identity paint: material flats, measured-face texel edges and rip-specific markings.
No projection/noise fallback. Geometry and paint are separate so hand/reload anchors stay fixed.
"""
import math
from m10 import box, face_xyz, seg

GLYPHS = {
'H':('101','101','111','101','101'), 'A':('010','101','111','101','101'),
'K':('101','110','100','110','101'), 'E':('111','100','110','100','111'),
'B':('110','101','110','101','110'), 'C':('111','100','100','100','111'),
'0':('111','101','101','101','111'), '1':('010','110','010','010','111'),
'2':('110','001','010','100','111'), '-':('000','000','111','000','000')}

def text_pixel(word,u,v,scale):
    ix=int(u/scale); iy=int(v/scale)
    if u<0 or v<0 or iy>=5 or ix>=len(word)*4: return False
    return ix%4<3 and GLYPHS.get(word[ix//4],('000',)*5)[iy][ix%4]=='1'

def tint(c,d): return tuple(max(0,min(255,x+d)) for x in c[:3])+(255,)

def install(ns,wid):
    old_elements=ns['elements']; old_special=ns['special']; M=ns['M']; T=ns['T']
    # All returned visible surfaces get explicit pigment, no smeared rip projection.
    def elements():
        E=old_elements()
        if wid in ('cup_bearer_sa_2','reginar_b','weaver_c'):
            # Side-mounted sights retain their exact sight line; shorten only aft launch casing.
            for e in E:
                n=e['name']
                if wid=='cup_bearer_sa_2': eligible=n.startswith('tube'); cut=10.0; k=.30
                else:
                    eligible=n.startswith(('recv_upper','recv_band','rear_','collar','end_','rail_top','rail_low','ammo_box','hoop','top_rail','band_tail','mag_'))
                    cut=12.3; k=.50 if n.startswith('mag_') else .28
                if eligible:
                    for key in ('from','to'):
                        if e[key][2]>cut: e[key][2]=round(cut+(e[key][2]-cut)*k,4)
                    if e.get('rotation') and e['rotation']['origin'][2]>cut:
                        e['rotation']['origin'][2]=round(cut+(e['rotation']['origin'][2]-cut)*k,4)
        if wid in ('reginar_b','weaver_c'):
            # Recessed panel joints; no nearly parallel rotated surface plates.
            names=('front_housing','recv_lower') if wid=='reginar_b' else ('recv_lower','tube_front')
            out=[]
            for e in E:
                if e['name'] in names and not e.get('rotation'):
                    a,b=e['from'],e['to']; out+=seg(e['name'],a,b,[(a[2]+b[2])/2],groove=.045,gw=.10)
                else: out.append(e)
            E=out
            # Under-barrel rail teeth, separated by real gaps.
            for i in range(6):
                a=-.465+i*.024
                E.append(M.rb('identity_rail_tooth'+str(i),.036,(a,a+.012),(.096,.103)))
        if wid=='cup_bearer_sa_2':
            # Vent stack is physically stepped, keeping the open muzzle frame visible.
            for i in range(4):
                E.append(box('identity_vent_rib'+str(i),(6.70,11.65+i*.19,4.0),(6.78,11.74+i*.19,5.25)))
        if wid=='stampede_mk_32':
            # Front perforated shroud has a small raised rib bank, not flat photo dirt.
            for i in range(5):
                a=-.416+i*.013
                E.append(M.rb('brl_identity_rib'+str(i),(-.034,.034),(a,a+.006),(.124,.150)))
        if wid in ('future_imperfect','rest_for_the_wicked'):
            # The reference swords are genuinely sparse: preserve long clean blade instead of adding fake machinery.
            # One continuous inset panel with thin bright rails supplies depth at the ricasso.
            if wid=='future_imperfect':
                for xr in ((-.0140,-.0125),(.0125,.0140)):
                    E.append(M.rb('identity_ricasso_rail'+str(len(E)),xr,(-.049,-.046),(.258,.338)))
        return [e for e in E if all(a < b for a,b in zip(e['from'],e['to']))]

    def special(e,fn,s,t):
        n=e['name']; base=n
        # segmented names reuse original material rules
        if wid in ('reginar_b','weaver_c'):
            for name in ('front_housing','recv_lower','tube_front'):
                if n.startswith(name+'_') and n[len(name)+1:] in ('0','1','g0'): base=name
        ee=dict(e,name=base)
        if n.startswith('identity_rail'): c=(116,116,106,255)
        elif n.startswith('identity_vent'): c=(66,68,58,255)
        elif n.startswith('brl_identity'): c=(62,76,48,255)
        elif n.startswith('identity_ricasso'): c=(158,160,154,255)
        else:
            c=old_special(ee,fn,s,t)
        if c is None:
            if 'grip' in n: c=(55,52,47,255)
            elif n.startswith('red_lever'): c=(157,43,34,255)
            elif n.startswith('opt'): c=(198,196,184,255)
            elif n.startswith(('rail','frame','fg_cap')): c=(216,208,190,255)
            elif n.startswith('shroud'): c=(99,101,80,255)
            else: c=(79,80,69,255)
        # Remove old random grain on painted rubber / caps.
        if 'grip' in n and 'screw' not in n and 'frame' not in n:
            c=(55,53,49,255) if wid!='rest_for_the_wicked' else (130,132,130,255)
        x,y,z=face_xyz(e,fn,s,t)
        dims=[e['to'][i]-e['from'][i] for i in range(3)]
        uaxis,vaxis={'north':(0,1),'south':(0,1),'east':(2,1),'west':(2,1),'up':(0,2),'down':(0,2)}[fn]
        W=max(1,round(abs(dims[uaxis])*T)); H=max(1,round(abs(dims[vaxis])*T)); px=int(s*W); py=int(t*H)
        # Exactly one texel edge/seam, using only a few flat material shades.
        if py==0: c=tint(c,22)
        elif py==H-1: c=tint(c,-29)
        elif px==0: c=tint(c,10)
        elif px==W-1: c=tint(c,-17)
        if 'grip' in n and not any(k in n for k in ('frame','screw','mount','cap','root','heel','wrap','rib')):
            if fn in ('east','west','north','south') and 2<px<W-3 and 2<py<H-3:
                if (px+py)%5==0: c=tint(c,-18)
                elif (px+py)%5==1: c=tint(c,8)
        side=fn in ('east','west')
        # Broad side panels: seam frame and two flat screw heads.
        panels=('recv','housing_panel','deck_panel','lower_panel','stock_web','brl_shroud','rear_tube','panel','ricasso')
        if side and n.startswith(panels) and W>16 and H>12:
            if (px in (3,W-4) and 3<=py<=H-4) or (py in (3,H-4) and 3<=px<=W-4): c=tint(c,-22)
            if (px in (5,6,W-7,W-6)) and py in (5,6): c=(180,181,170,255)
        # Manufacturer wordmark positioned by face coordinates; a legible glyph, never a random bar.
        if side and wid in ('reginar_b','weaver_c','plemusa_b'):
            want=(wid in ('reginar_b','weaver_c') and n=='recv_lower_1') or (wid=='plemusa_b' and n=='recv_top')
            if want and text_pixel('HAKKE',s*abs(dims[2])-.22,t*abs(dims[1])-.18,1/T):
                c=(184,199,193,255) if wid=='plemusa_b' else ((190,59,43,255) if wid=='reginar_b' else (93,89,75,255))
        if side and wid=='cup_bearer_sa_2':
            if n.startswith('deck_side') and '_g' not in n:
                if .22<s<.78 and .27<t<.66 and py%4<2: c=(49,55,44,255)
            if n.startswith('lower_panel') and '_g' not in n and .2<s<.8 and .42<t<.55: c=(128,138,104,255)
            if n.startswith('tube') and not any(k in n for k in ('band','cap')) and .35<t<.4: c=(70,73,58,255)
            if n.startswith('red_lever') and .35<s<.65 and .14<t<.25: c=(233,222,207,255)
        if side and wid=='weaver_c' and n.startswith('rear_tube'):
            # Orange shell's repeated recessed hexagonal panels from the rip.
            u=(s*3)%1; v=t
            d=abs(v-.5)
            edge=.12+.32*max(0,(d-.22)/.22)
            if .08<v<.92 and (abs(u-edge)<.03 or abs(u-(1-edge))<.03 or (d>.39 and edge<u<1-edge)):
                c=(152,63,37,255)
        if side and wid=='reginar_b' and n.startswith('tube_front'):
            if .15<s<.55 and .36<t<.60: c=(220,220,211,255) if (px%4<2 or py in (int(H*.37),int(H*.58))) else (69,72,64,255)
        if side and wid=='plemusa_b':
            if n.startswith('drum') and n[4:5].isdigit() and .2<t<.8 and px%8<2: c=tint(c,-27)
            if n=='side_plate' and .45<s<.8 and .32<t<.65:
                c=(83,150,79,255) if px%5<3 else (21,27,24,255)
        if side and wid=='stampede_mk_32':
            if n=='brl_vent':
                c=(25,33,23,255) if px%4<2 and py%4<2 else (73,89,51,255)
            if n=='display':
                c=(22,31,29,255)
                if .18<s<.4 and .22<t<.78: c=(155,159,150,255) if .23<s<.35 and .3<t<.7 else (63,70,61,255)
                if .5<s<.84 and py%5<3: c=(47,117,183,255)
        if side and wid=='future_imperfect':
            if n=='blade':
                if px==W-3: c=(160,162,158,255)
                elif px==2: c=(247,245,235,255)
            if n=='ricasso' and .30<s<.75 and .63<t<.85 and py%4<2: c=(49,51,48,255)
        if side and wid=='rest_for_the_wicked' and n=='panel':
            if px in (2,W-3): c=(79,83,81,255)
            if px in (5,W-6) and py%49 in (11,12): c=(217,218,207,255)
        return c
    ns['elements']=elements;ns['special']=special
