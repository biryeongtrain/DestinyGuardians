"""W123 material pass. Colour/material assignments follow each weapon's supplied rip.
Relief uses the source projection; unsupported/adapted faces disable it explicitly.
Special is sparse ink, lights, bore darkness and source-aligned camo only.
"""
import json, math
from pathlib import Path
from m10 import face_xyz
from identity import text_pixel

def mat(kind,color,detail=.75,**kw): return dict(kind=kind,color=color,detail=detail,**kw)
COMMON={
 'steel':mat('steel',(151,158,156),.7,amp=10,field=.09),
 'gunmetal':mat('metal',(65,69,69),.85,amp=7,field=.08),
 'polymer':mat('polymer',(45,48,46),.45,amp=5),
 'rubber':mat('rubber',(17,20,19),.25,amp=4,plate=False),
 'dark':mat('dark',(15,19,19),.15),
 'ivory':mat('paint',(210,207,192),1.2,amp=3),
 'red':mat('paint',(151,39,30),.4),
 'amber':mat('glow',(218,145,33),0),
 'blue_glass':mat('lens',(28,80,120),0),
 'green_glass':mat('lens',(44,91,48),0),
}
CONFIG={
 'cup_bearer_sa_2':{'ivory':mat('paint',(211,201,186),1.1),'olive':mat('metal',(103,108,80),.9),'polymer':mat('polymer',(49,49,39),.5),'steel':mat('steel',(157,158,143),.5)},
 'reginar_b':{'charcoal':mat('metal',(78,80,76),.9),'olive':mat('paint',(78,89,44),1.1),'ivory':mat('paint',(205,207,199),1.0),'steel':mat('steel',(155,160,158),.7)},
 'weaver_c':{'cream':mat('paint',(204,200,173),.35),'orange':mat('paint',(197,85,47),1.0),'brown':mat('polymer',(58,43,34),.4),'brown_rubber':mat('rubber',(23,17,13),.2,amp=4,plate=False),'ivory':mat('paint',(215,214,201),1.0)},
 'plemusa_b':{'teal':mat('paint',(48,88,77),1.1),'yellow':mat('paint',(188,180,100),1.1),'ivory':mat('paint',(218,211,192),1.2),'polymer':mat('polymer',(51,59,54),.5),'gunmetal':mat('metal',(100,107,100),.7)},
 'stampede_mk_32':{'olive':mat('paint',(66,88,45),1.25),'ivory':mat('paint',(210,207,191),1.1),'gunmetal':mat('metal',(104,109,101),.8),'polymer':mat('polymer',(54,58,50),.4)},
 'future_imperfect':{'blade':mat('steel',(205,209,201),.85,amp=12,field=.12),'edge':mat('steel',(144,152,147),.35,amp=9),'ivory':mat('paint',(211,211,198),1.0),'wrap':mat('cloth',(70,73,70),.35,amp=10),'wrap_ridge':mat('cloth',(111,115,107),.25,amp=8)},
 'rest_for_the_wicked':{'blacksteel':mat('metal',(37,43,45),.85,amp=6),'panelsteel':mat('steel',(117,125,121),1.0,amp=11,field=.1),'edge':mat('steel',(209,217,212),.35,amp=11),'wrap':mat('rubber',(81,87,81),.25,amp=5,plate=False)},
}

def install(ns,wid):
    ns['STYLE']='material';mats=dict(COMMON);mats.update(CONFIG[wid])
    mats.update({
        'lightsteel':mat('steel',(184,190,183),.55,amp=7,wear=False),
        'warmsteel':mat('metal',(143,144,128),.45,amp=5,wear=False),
        'darksteel':mat('metal',(84,92,87),.55,amp=5,wear=False),
        'brownsteel':mat('metal',(95,75,58),.5,amp=5,wear=False),
    })
    if wid=='plemusa_b':mats['lightsteel']=mat('steel',(210,216,205),.55,amp=7,wear=False)
    # Wear is part-specific, never blanket pale grime on every panel.
    for key,m in mats.items():
        if m['kind']=='paint':
            m=dict(m);m['wear']=False if key in ('ivory','cream','olive','red') else (126,130,116);mats[key]=m
    ns['MATERIALS']=mats
    M=ns['M']; oldmap=ns['model2world']; elements={e['name']:e for e in ns['elements']()}
    # Invert the previous ADS fit before sampling the original rip; prevents compressed/repeated relief.
    def model2world(n,p):
        q=list(p)
        if wid=='cup_bearer_sa_2': eligible=n.startswith('tube'); cut=10.; k=.30
        elif wid in ('reginar_b','weaver_c'):
            eligible=n.startswith(('recv_upper','recv_band','rear_','collar','end_','rail_top','rail_low','ammo_box','hoop','top_rail','band_tail','mag_'));cut=12.3;k=.50 if n.startswith('mag_') else .28
        else:eligible=False;cut=0;k=1
        if eligible and q[2]>cut:q[2]=cut+(q[2]-cut)/k
        return oldmap(n,tuple(q))
    ns['model2world']=model2world

    def material_key(n,fn):
        # R2: preserve coated shell panels, expose machined receivers, structure and fittings.
        if wid=='cup_bearer_sa_2':
            if n.startswith(('frame','rail_','lower_beam','thumb_floor','stock_post','fg_cap')):return 'warmsteel'
            if n.startswith(('deck_panel','lower_panel','deck_side')):return 'ivory'
            if n.startswith(('deck_tail','lower_front','lower_nose','guard')):return 'darksteel'
        elif wid=='reginar_b':
            if n.startswith(('muzzle','tube_band','collar','rear_band','recv_band')):return 'lightsteel'
            if n.startswith(('guard','magwell','fgrip_mount','grip_root')):return 'darksteel'
        elif wid=='weaver_c':
            if n.startswith(('muzzle','collar','recv_band')):return 'lightsteel'
            if n.startswith('recv_upper'):return 'warmsteel'
            if n.startswith(('recv_lower','guard','magwell','fgrip_mount','grip_root')):return 'brownsteel'
        elif wid=='plemusa_b':
            if n.startswith(('brl_window','brl_sight','recv_front','grip_frame','ejector')):return 'lightsteel'
            if n.startswith(('side_plate','drum_plate','stock','brl_loop','brl_foot','rail_low','guard')):return 'gunmetal'
        elif wid=='stampede_mk_32':
            if n.startswith(('brl_cap','brl_band','band_rear','brl_sight','sight_block','butt_pad')):return 'lightsteel'
            if n.startswith(('recv_mid','brl_loop','side_lug','drum_post','guard')):return 'gunmetal'
        elif wid=='future_imperfect':
            if n.startswith(('pommel','ferrule')):return 'lightsteel'
            if n.startswith(('ricasso','identity_ricasso')):return 'warmsteel'
        elif wid=='rest_for_the_wicked':
            if n.startswith('guard_collar'):return 'darksteel'
        if n=='opt_pin': return 'red' if wid=='cup_bearer_sa_2' else 'amber'
        if n=='display': return 'blue_glass'
        if n.startswith('side_dot'):return 'green_glass'
        if wid=='future_imperfect':
            if n.startswith('grip_wrap'):return 'wrap_ridge'
            if n=='grip':return 'wrap'
            if n.startswith(('blade_edge','blade_spine','collar','ferrule_ring','ricasso_root')):return 'edge'
            if n.startswith(('blade','tip')):return 'blade'
            if n.startswith('identity_ricasso'):return 'steel'
            return 'ivory'
        if wid=='rest_for_the_wicked':
            if n.startswith('grip_screw'):return 'steel'
            if n.startswith('grip'):return 'wrap'
            if n.startswith(('edge','spine_edge')) or n=='tip_slant' and fn=='up':return 'edge'
            if n=='panel' or n.startswith('pommel'):return 'panelsteel'
            return 'blacksteel'
        if n.startswith('mag_'):
            if any(a in n for a in ('fin','collar','tail')):return 'gunmetal'
            if 'tip' in n:return 'red'
            if 'nose' in n:return 'steel'
            return 'orange' if wid=='weaver_c' else 'olive'
        if n.startswith(('butt_rubber','butt_plate')):return 'rubber'
        if n.startswith(('opt_lip','opt_eye')):return 'polymer'
        if n.startswith('opt_'):
            inner={'opt_top':'down','opt_bot':'up','opt_out':'west','opt_in':'east'}.get(n)
            return 'dark' if fn==inner else 'steel'
        if n.startswith(('pin_','hump_screw','rear_pin','rail_bolt','grip_screw')):return 'steel'
        if n.startswith(('trigger','identity_rail','rail_tooth')):return 'gunmetal'
        if wid=='cup_bearer_sa_2':
            if n.startswith('red_lever'):return 'red'
            if n.startswith(('fg_','grip','guard','identity_vent')):return 'polymer'
            if n.startswith(('tube_band','tube_cap','deck_vent')):return 'gunmetal'
            if n.startswith(('tube','shroud')):return 'olive'
            return 'ivory'
        if wid=='reginar_b':
            if n=='grip' or n.startswith('fgrip_rib'):return 'rubber'
            if n.startswith(('rear_tube','end_')):return 'olive'
            if n.startswith(('grip','fgrip','guard','magwell','handle_top')):return 'polymer'
            if n.startswith(('muzzle','tube_band','recv_band','collar','rear_band','ammo_box')):return 'ivory'
            if n.startswith(('under_rail','rail_top','rail_low','rear_rail','handle_leg')):return 'steel'
            if n.startswith(('port','rear_trig')):return 'dark'
            return 'charcoal'
        if wid=='weaver_c':
            if n=='grip' or n.startswith('fgrip_rib'):return 'brown_rubber'
            if n.startswith(('rear_tube','end_lip','top_fin')) and not n.startswith('top_fin_base'):return 'orange'
            if n.startswith(('grip','fgrip','recv_lower','guard','magwell')):return 'brown'
            if n.startswith(('recv_window','top_shroud')):return 'polymer'
            if n.startswith(('cage','under_rail','top_strip','top_rail','rear_rail','hoop','band_tail','top_fin_base')):return 'steel'
            if n.startswith(('muzzle','recv_band','collar','ammo_box')):return 'ivory'
            return 'cream'
        if wid=='plemusa_b':
            if n.startswith(('recv_top','recv_low')):return 'teal'
            if n.startswith(('drum0','drum1','drum2','recv_front','rail_low')):return 'yellow'
            if n.startswith(('brl_shroud','brl_window','brl_sight','recv_hump','grip_frame','ejector')):return 'ivory'
            if n.startswith(('side_plate','drum_plate','stock','brl_loop','brl_fgrip','brl_foot')):return 'polymer'
            if n.startswith('grip'):return 'rubber'
            if n.startswith(('recv_seam','brl_band')):return 'gunmetal'
            return 'gunmetal'
        if wid=='stampede_mk_32':
            if n.startswith(('brl_shroud','shroud_rear','recv_upper','recv_mid')):return 'olive'
            if n.startswith(('brl_cap','brl_band','band_rear','brl_sight','sight_block','butt_pad')):return 'ivory'
            if n.startswith('grip'):return 'rubber'
            if n.startswith(('stock','brl_loop')):return 'polymer'
            if n in ('drum_window','brl_slot'):return 'dark'
            return 'gunmetal'
        raise ValueError((wid,n))

    def material(n,fn):
        key=material_key(n,fn)
        # These parts were adapted to new positions/angles, not directly coincident with source surfaces.
        bad=n.startswith(('mag_','opt_','brl_sight','identity_','brl_identity')) or bool(elements[n].get('rotation'))
        # Sword edge is thinner than the source; thin end faces have no stable projection.
        if wid in ('future_imperfect','rest_for_the_wicked') and fn not in ('east','west'):bad=True
        if wid=='cup_bearer_sa_2' and n.startswith(('deck','lower','stock','thumb','top_bracket','frame','rail_')):bad=True
        if wid=='weaver_c' and n.startswith(('recv_upper','under_rail','cage')):bad=True
        if bad:return dict(mats[key],detail=0)
        return key
    ns['material']=material
    # Source-aligned colour stencils preserve the actual worn camo placement, rather than random blobs.
    import kit
    cache=kit.art(wid)/'proj_cache';manifest=json.loads((cache/'manifest.json').read_text())
    views={k:kit.View(cache,k,manifest) for k in manifest['views']}; faceviews={}
    from PIL import Image, ImageFilter
    camo_views={}
    for key,view in views.items():
        im=Image.open(cache/f'{key}_albedo.png').convert('RGBA')
        mask=Image.new('L',im.size);src=im.load();dst=mask.load()
        for u in range(im.width):
            for v in range(im.height):
                r,g,b,a=src[u,v];lum=(r+g+b)/3
                if a>127:
                    if wid=='cup_bearer_sa_2':dst[u,v]=255 if g>b+12 and r>b+10 and g>r-8 and 60<lum<192 else 0
                    elif wid=='stampede_mk_32':dst[u,v]=255 if lum<48 and g>b+8 else 128 if lum>115 and g>b+10 else 0
        small=(max(2,im.width//55),max(2,im.height//(18 if wid=='stampede_mk_32' else 55)))
        broad=mask.resize(small,Image.Resampling.BOX)
        if wid=='cup_bearer_sa_2':broad=broad.filter(ImageFilter.MedianFilter(3))
        camo_views[key]=broad.resize(im.size,Image.Resampling.NEAREST).load()
    def source(e,fn,p):
        key=(e['name'],fn)
        if key not in faceviews:
            nm=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e));a=model2world(e['name'],p)
            b=model2world(e['name'],tuple(p[i]+nm[i]*.25 for i in range(3)))
            wn=[b[i]-a[i] for i in range(3)];i=max(range(3),key=lambda k:abs(wn[k]))
            faceviews[key]=views[('p' if wn[i]>0 else 'n')+'xyz'[i]]
        view=faceviews[key];u,v=view.project(model2world(e['name'],p));u=int(u);v=int(v)
        if 0<=u<view.W and 0<=v<view.H:
            c=view.alb[u,v]
            if c[3]>127:
                vk=next(k for k,vw in views.items() if vw is view)
                return c[:3]+(camo_views[vk][u,v],)
        return None

    def special(e,fn,s,t):
        n=e['name']; side=fn in ('east','west');x,y,z=face_xyz(e,fn,s,t)
        dims=[e['to'][i]-e['from'][i] for i in range(3)];T=ns['T']
        # Precisely bounded manufacturer decals and source data stripes.
        if side and wid in ('reginar_b','weaver_c','plemusa_b'):
            want=n=='recv_lower_1' if wid!='plemusa_b' else n=='recv_top'
            if want and text_pixel('HAKKE',s*dims[2]-.22,t*dims[1]-.18,1/T):
                return ((178,55,38) if wid=='reginar_b' else (207,206,190) if wid=='weaver_c' else (143,166,154))+(255,)
        if side and wid=='reginar_b' and n.startswith('tube_front') and .15<s<.55 and .36<t<.60:
            if int(s*dims[2]*T)%4<2:return (207,211,197,255)
        if n.startswith('mag_core') and .80<s<.84:return (211,207,183,255)
        if side and wid=='cup_bearer_sa_2':
            if n.startswith('red_lever') and .35<s<.65 and .14<t<.25:return (231,218,196,255)
            if n.startswith('deck_side') and '_g' not in n and .22<s<.78 and .27<t<.66 and int(t*dims[1]*T)%4<2:return (43,49,37,255)
        if side and wid=='stampede_mk_32':
            if n=='display' and .52<s<.84 and .20<t<.80 and int(t*dims[1]*T)%5<3:return (47,131,213,255)
            if n=='display' and (s-.29)**2+(t-.5)**2<.012:return (172,183,163,255)
            if n=='brl_vent' and int(s*dims[2]*T)%4<2 and int(t*dims[1]*T)%4<2:return (19,27,18,255)
        if side and wid=='plemusa_b' and n=='side_plate' and .45<s<.8 and .32<t<.65 and int(s*dims[2]*T)%5<3:return (88,165,77,255)
        if side and wid=='future_imperfect' and n=='ricasso':
            if .30<s<.75 and .63<t<.85 and int(t*dims[1]*T)%4<2:return (35,42,38,255)
        if side and wid=='rest_for_the_wicked' and n=='panel':
            w=M.w((x,y,z))
            for rz in (.30,.42,.54,.66,.78,.90):
                for ry in (-.036,.003):
                    if abs(w[2]-rz)<.006 and abs(w[1]-ry)<.004:return (211,219,209,255)
        if side and wid=='weaver_c' and n.startswith('rear_tube'):
            W=max(1,round(dims[2]*T));H=max(1,round(dims[1]*T));px=int(s*W);py=int(t*H)
            # The source rear casing's recessed hexagonal tiles, one texel wide.
            span=max(6,W//2);u=px%span;edge=1+max(0,abs(py-H//2)-H//4)
            if 2<py<H-3 and (u==edge or u==span-edge-1 or py in (3,H-4) and edge<u<span-edge-1):return (133,51,27,255)
        if side and wid=='plemusa_b' and n.startswith('drum1'):
            W=max(1,round(dims[2]*T));H=max(1,round(dims[1]*T));px=int(s*W);py=int(t*H)
            if px%8==2 and py in (3,H-4):return (99,103,88,255)
        if side and wid=='future_imperfect' and n=='blade':
            W=max(1,round(dims[2]*T));px=int(s*W)
            if px==2:return (164,176,166,255)
        # Bore interiors remain dark bounded masks. The surrounding rim gets the actual material bake.
        if fn in ('north','south'):
            if wid in ('reginar_b','weaver_c') and n.startswith(('muzzle','end_lip')):
                cy=M.m(0,0,.1715 if wid=='reginar_b' else .1735)[1]
                if (x-8)**2+(y-cy)**2<.58**2:return (11,15,14,255)
            if wid=='cup_bearer_sa_2' and ((n.startswith('shroud') and fn=='north') or (n.startswith('tube_cap') and fn=='south')):
                if (x-8)**2+(y-ns['TY'])**2<.66**2:return (12,15,12,255)
            if wid=='stampede_mk_32' and n.startswith('brl_cap') and fn=='north':
                if (x-8)**2+(y-M.m(0,0,.14)[1])**2<.62**2:return (12,16,12,255)
        if wid in ('cup_bearer_sa_2','stampede_mk_32'):
            pigment=material_key(n,fn)
            target=(wid=='cup_bearer_sa_2' and pigment=='ivory') or (wid=='stampede_mk_32' and pigment=='olive')
            if target:
                c=source(e,fn,(x,y,z))
                if c:
                    r,g,b,blob=c;lum=(r+g+b)/3
                    ink=None
                    if wid=='cup_bearer_sa_2' and blob>60:ink=(128,143,100)
                    if wid=='stampede_mk_32':
                        if blob>120:ink=(34,52,25)
                        elif blob>40:ink=(109,128,76)
                    if ink:
                        grain=((int(s*1009)*17+int(t*1013)*29)%23-11)*.16
                        field=.98+.035*math.cos(t*math.pi)
                        return tuple(max(0,min(255,round(v*field+grain))) for v in ink)+(255,)
        return None
    ns['special']=special
