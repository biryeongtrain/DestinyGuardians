"""W325 identity pass. Explicit rip-derived structural and hand-painted face details.
All coordinates are model pixels. No source-image projection is used by the final paint pass.
"""
import math
from w9 import box, tidy, face_xy, model_pt, flat

IDS = 'requiem_43 aachen_lr2 damietta_lr2 tongeren_lr3 nox_cordis_ii nox_lumen_ii parsec_tsu'.split()
FALLBACK = [(150,172,168),(58,60,54),(94,86,80),(66,66,64),(56,64,84),(78,74,70),(206,214,212)]

def geometry(wid, els):
    E=[dict(e, **{'from':list(e['from']),'to':list(e['to'])}) for e in els]
    def add(n,a,b): E.append(box(n,a,b))
    def ribs(prefix,x0,x1,y0,y1,z0,step,num,width):
        for i in range(num): add(prefix+str(i),(x0,y0,z0+i*step),(x1,y1,z0+i*step+width))
    if wid=='requiem_43':
        # SUROS receiver ejection lip, under-barrel cooling bands and butt tread.
        for sd,x in [('l',(7.21,7.25)),('r',(8.75,8.79))]:
            add('id_port_rail_'+sd,(x[0],10.79,1.55),(x[1],10.88,3.55))
            add('id_port_latch_'+sd,(x[0],11.0,3.4),(x[1],11.11,3.6))
        ribs('id_barrel_collar_',7.54,8.46,10.0,10.76,-7.4,1.25,6,.13)
        for i in range(7):
            y=7.55+i*.48; add('id_butt_tread_'+str(i),(7.45,y,16.48),(8.55,y+.18,16.54))
        # Long stock slot is genuinely open across the comb, not a black decal.
        src=next(e for e in E if e['name']=='stock_comb'); E.remove(src)
        x0,y0,z0=src['from']; x1,y1,z1=src['to']; a,b,c,d=13.7,15.5,11.05,11.28
        for n,lo,hi in [('a',(x0,y0,z0),(x1,y1,a)),('b',(x0,y0,b),(x1,y1,z1)),('c',(x0,y0,a),(x1,c,b)),('d',(x0,d,a),(x1,y1,b))]:add('stock_comb_slot_'+n,lo,hi)
    elif wid=='aachen_lr2':
        # Serrated longitudinal vent strip: actual fins separate a recessed dark core.
        for sd,(a,b) in [('l',(7.39,7.46)),('r',(8.54,8.61))]:
            ribs('id_hg_fin_'+sd,a,b,9.85,10.09,-4.65,.38,9,.10)
        # Magazine pressed strengthening ribs remain in moving leaf.
        for sd,(a,b) in [('l',(7.55,7.58)),('r',(8.5,8.55))]:
            ribs('mag_id_rib_'+sd,a,b,6.9,8.3,4.25,.65,3,.12)
        add('id_scope_ring_l',(7.19,11.2,5.7),(7.25,12.1,5.82));add('id_scope_ring_r',(8.75,11.2,5.7),(8.81,12.1,5.82))
    elif wid=='damietta_lr2':
        # Banded muzzle's real lateral port pockets, leaving a central bore tube.
        src=next(e for e in E if e['name']=='brake'); src['from'][0]=7.76;src['to'][0]=8.24
        for sd,(a,b) in [('l',(7.6,7.76)),('r',(8.24,8.4))]:
            ribs('id_brake_web_'+sd,a,b,9.0,9.75,-15.05,.54,5,.16)
        for sd,(a,b) in [('l',(7.45,7.5)),('r',(8.5,8.55))]:
            ribs('mag_id_rib_'+sd,a,b,7.55,8.7,4.4,.53,4,.10)
        for sd,(a,b) in [('l',(7.1,7.15)),('r',(8.5,8.55))]:
            ribs('id_scope_dial_'+sd,a,b,11.17,11.52,3.02,.14,4,.06)
    elif wid=='tongeren_lr3':
        # Distinct two-row hex stock insets replace the generic three rectangular slabs.
        E=[e for e in E if not e['name'].startswith('stock_hex')]
        for sd,(a,b) in [('l',(7.09,7.15)),('r',(8.85,8.91))]:
            for row in range(2):
                for k in range(3):
                    z=7.65+k*1.38+(row*.15);y=8.09+row*.83
                    add('id_hex_'+sd+str(row)+str(k),(a,y,z),(b,y+.72,z+1.2))
        # Preserve the base stock-neck dip at z 8.9..9.2; decorative top row must also clear it.
        for e in E:
            if e['name'].startswith('id_hex') and e['to'][1]>9.4:
                if e['from'][2]<8.9<e['to'][2]:e['to'][2]=8.88
                if e['from'][2]<9.2<e['to'][2]:e['from'][2]=9.22
        # Front shroud ports show collar depth; collar side fins remain orthogonal.
        for sd,(a,b) in [('l',(7.43,7.5)),('r',(8.5,8.57))]:
            ribs('id_shroud_fin_'+sd,a,b,8.8,9.3,-13.8,1.3,3,.18)
    elif wid=='nox_cordis_ii':
        # Three black recessed rectangular cells and chevron panel observed on the rip.
        sh=next(e for e in E if e['name']=='shroud');sh['from'][0]=7.13;sh['to'][0]=8.87
        for sd,(a,b) in [('l',(6.9,7.13)),('r',(8.87,9.1))]:
            for k in range(4):
                z=-7.65+k*1.18
                add('id_cell_header_'+sd+str(k),(a,11.05,z),(b,11.22,z+.93))
                add('id_cell_footer_'+sd+str(k),(a,9.28,z),(b,9.45,z+.93))
            add('id_chevron_'+sd,(a,9.48,-7.5),(b,11.0,-6.65))
        for sd,(a,b) in [('l',(6.92,7.0)),('r',(9.0,9.08))]:
            ribs('mag_id_cell_'+sd,a,b,3.15,4.45,-1.4,.65,4,.12)
    elif wid=='nox_lumen_ii':
        # Rear pull loop of the lower battery, missing in previous pass; actual through opening.
        for n,a,b in [('top',(7.35,4.9,8.4),(8.65,5.15,10.0)),('bot',(7.35,3.55,8.4),(8.65,3.8,10.0)),('end',(7.35,3.8,9.75),(8.65,4.9,10.0))]:add('mag_id_loop_'+n,a,b)
        # Top rail lowered to leave room for real rail teeth inside the previous ADS envelope.
        for e in E:
            if e['name']=='shroud_top' or e['name'].startswith('shroud_plate'):
                e['to'][1]=min(e['to'][1],13.25)
        ribs('id_top_tooth_',7.0,9.0,13.25,13.45,-6.95,.51,17,.25)
        # Cooling fins project out of recessed shroud slots.
        for sd,(a,b) in [('l',(6.59,6.65)),('r',(9.35,9.41))]:
            ribs('id_vent_fin_'+sd,a,b,11.62,12.28,-6.3,.39,10,.12)
        add('id_canister_band',(6.47,8.35,-1.2),(6.55,9.05,-.95))
    elif wid=='parsec_tsu':
        # 3D inset cover on side window (clean stepped corners, not rotated slabs).
        for sd,(a,b) in [('l',(6.43,6.5)),('r',(9.5,9.57))]:
            for k in range(3):
                y=10.35+k*.52
                add('id_window_bar_'+sd+str(k),(a,y,-2.45),(b,y+.12,.45))
            ribs('id_recv_fin_'+sd,a+.15,b+.15,11.35,12.0,5.85,.24,5,.08)
        # Lower battery door rim and latch: part of moving battery.
        for sd,(a,b) in [('l',(6.52,6.6)),('r',(9.4,9.48))]:
            for k in range(3):
                z=.8+k*.65;add('mag_id_lug_'+sd+str(k),(a,2.8,z),(b,4.95,z+.14))
    return tidy(E)

# Tiny hand-authored pixel wordmark; not a font raster bake.
GLYPHS={'S':['111','100','111','001','111'],'U':['101','101','101','101','111'],'R':['110','101','110','101','101'],'O':['111','101','101','101','111']}
def glyph(text,u,v):
    x=int(u);y=int(v)
    if x<0 or y<0 or y>=5:return False
    i=x//4
    return i<len(text) and x%4<3 and GLYPHS[text[i]][y][x%4]=='1'

def paint(wid,e,fn,s,t,base,T):
    import kit
    n=e['name'];p=model_pt(e,fn,s,t);x,y,z=p
    c=base or flat(FALLBACK[IDS.index(wid)])
    # Material for structural additions explicitly follows adjacent original parts.
    if n.startswith('id_') or n.startswith('mag_id_'):
        if wid=='requiem_43':c=flat((74,72,71) if 'barrel' in n or 'butt' in n else (206,210,208))
        if wid=='aachen_lr2':c=flat((128,128,104) if 'hg' in n else (58,60,54))
        if wid=='damietta_lr2':c=flat((178,206,222) if 'brake' in n else (94,86,80))
        if wid=='tongeren_lr3':c=flat((48,48,47) if 'hex' in n else (176,160,136))
        if wid=='nox_cordis_ii':c=flat((214,206,204))
        if wid=='nox_lumen_ii':c=flat((112,108,102) if 'vent' in n else (64,61,58))
        if wid=='parsec_tsu':c=flat((138,152,142) if 'fin' in n else (176,196,186))
    o,u,v=kit.face_frame(e,fn);w=max(1,round(math.dist((0,0,0),u)*T));h=max(1,round(math.dist((0,0,0),v)*T))
    ix=min(w-1,int(s*w));iy=min(h-1,int(t*h));dark=(24,27,29,255);hi=(201,207,204,255)
    side=fn in ('east','west')
    # One-texel edge/seam paint on every visible face, including rear/top faces.
    if w>3 and h>3:
        if iy==0:c=tuple(min(255,k+24) for k in c[:3])+(255,)
        elif iy==h-1:c=tuple(max(10,k-24) for k in c[:3])+(255,)
        elif ix==0:c=tuple(min(255,k+12) for k in c[:3])+(255,)
        elif ix==w-1:c=tuple(max(10,k-16) for k in c[:3])+(255,)
    # Crosshatch rubber and recessed hardware seen on the original furniture.
    if side and ('grip' in n or 'butt' in n) and w>5 and h>5 and 2<ix<w-3 and 2<iy<h-3:
        if (ix+iy)%6==0:c=tuple(min(255,k+15) for k in c[:3])+(255,)
    if side and any(a in n for a in ('recv','shroud','mag_body','mag_main','mag_block','plate_up','stock_pad')) and w>16 and h>12:
        # Corner screw heads and a recessed inner panel boundary (1 texel each).
        if (ix in (3,w-4) and 3<=iy<=h-4) or (iy in (3,h-4) and 3<=ix<=w-4):c=tuple(max(12,k-18) for k in c[:3])+(255,)
        dx=min((ix-6,ix-(w-7)),key=abs);dy=min((iy-6,iy-(h-7)),key=abs)
        if abs(dx)<=1 and abs(dy)<=1:c=hi if (dx,dy)==(-1,-1) else dark
    if 'turret' in n and side and iy in (2,h-3) and ix%4==0:c=hi
    # Distinct tinted glass with a crisp reflection, never smeared projection.
    if fn in ('north','south') and ('obj' in n or 'eyecup' in n or 'eyepiece' in n or 'hood' in n) and .25<s<.75 and .25<t<.75:
        c=(33,64,82,255)
        if .31<s<.38 or (.37<t<.42 and .32<s<.59):c=(128,183,201,255)
    if not side:return c
    if wid=='requiem_43':
        if n.startswith('shroud'):
            c=flat((150,172,168)) if 1<ix<w-2 and 1<iy<h-2 else c
            if y<10.99:c=flat((150,40,40))
            q=z-(y-10.8)*.87
            if -.75<q<-.4 or .05<q<.4:c=flat((150,40,40))
        if n=='recv_upper' and 11.54<y<11.94:
            # Readable SUROS at 24 texels per model pixel; asymmetric lettering stays readable.
            zz=4.65-z if fn=='east' else z-1.7
            if glyph('SUROS',zz/.13,(11.94-y)/.07):c=(226,241,234,255)
        if n.startswith('stock_comb_slot'):c=flat((150,40,40) if y>11.4 else (150,172,168))
    elif wid=='aachen_lr2':
        if n.startswith('hg_upper') and -9.4<z<-5.0 and 9.77<y<10.11:
            if (z+(y-9.77)*.9)%.34<.11:c=dark
        if n.startswith(('mag_body','mag_id')) and 7.0<y<8.25 and abs((z-4.25)%.65)<.07:c=(100,102,90,255)
        if n=='stock_cheek' or n=='stock_cheek_r':
            if abs(s-.5)+abs(t-.5)<.42:c=(80,83,72,255)
    elif wid=='damietta_lr2':
        if n.startswith('stock_pad') and .12<s<.88 and .13<t<.87:
            c=flat((72,92,98));
            if min(abs(s-.18),abs(s-.82))<.05:c=flat((178,206,222))
        # Original pale-blue barrel camo retained; no invented longitudinal decal.
        if n.startswith('recv_upper') and 9.99<y<10.38 and (z+y)%.42<.12:c=dark
    elif wid=='tongeren_lr3':
        if n.startswith('id_hex'):
            # A bevelled hexagon painted within the shallow machined inset.
            qx=abs(s-.5);qy=abs(t-.5);d=max(qx/.43,(qy+qx*.5)/.43)
            c=flat((66,66,64) if d<.70 else (28,30,29) if d<.88 else (99,100,94))
        if n.startswith('plate_up') and 8.85<y<10.12 and -2.8<z<.6:
            if min(abs(y-8.95),abs(y-10.0))<.045:c=(103,104,97,255)
        if n.startswith('shroud') and y<8.1:c=(176,160,136,255)
    elif wid=='nox_cordis_ii':
        if n=='shroud' and 9.45<y<11.08:c=(27,29,34,255)
        if n.startswith('id_chevron'):
            c=(28,32,38,255)
            a=abs(t-.5)*.65
            u=s if fn=='east' else 1-s
            if min(abs(u-(.73-a)),abs(u-(.46-a)))<.055:c=(214,222,219,255)
        if n=='recv_logo_plate':
            c=(214,206,204,255)
            if (.45<s<.65 and .2<t<.8) or (.2<s<.65 and .2<t<.35):c=(56,64,84,255)
        if n.startswith('recv_grille') and ix%3==0:c=(190,191,190,255)
    elif wid=='nox_lumen_ii':
        if n.startswith('shroud') and n=='shroud' and 10.6<y<13.0 and -6.7<z<1.4:
            if abs(y-12.73)<.04 or abs(y-10.63)<.04:c=(150,148,138,255)
            if 12.33<y<12.42 and -6.4<z<-2.5:c=dark
        if n.startswith('recv_grille'):c=(196,198,198,255) if ix%3==0 or iy%3==0 else (65,66,63,255)
        if n.startswith('mag_block') and 4.5<y<5.8 and .7<z<6.8 and ((z*2)%1<.08 or abs(y-5.5)<.04):c=(124,122,114,255)
    elif wid=='parsec_tsu':
        if n.startswith('shroud_window'):
            c=(176,196,186,255)
            if .51<s<.73 and .38<t<.68:c=dark
            if ix in (3,w-4) or iy in (3,h-4):c=(117,138,129,255)
        if n=='shroud' and -6.8<z<-3.3 and 12.0<y<12.55:
            # Long inset upper arrow panel from the rip, light mint on white.
            if z>-6.8+(y-12.0)*.7:c=(176,196,186,255)
        if n=='mag_main' and 1.1<z<3.1 and 2.9<y<4.9:
            if abs(z-1.3)<.055 or abs(z-2.85)<.055 or abs(y-3.0)<.055 or abs(y-4.75)<.055:c=(116,139,125,255)
        if n.startswith('recv_vents') or n.startswith('id_recv_fin'):c=(130,151,142,255) if ix%3==0 else (49,62,55,255)
    return c
