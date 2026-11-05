"""W325 material pass. Per-part W123 material treatment; special paints sparse source decals only."""
import math
import kit
from paint import text_hit,line,every


def spec(kind,color,detail=.6,amp=None):
    m={'kind':kind,'color':tuple(color),'detail':detail}
    if amp is not None:m['amp']=amp
    return m

BASE={
'black_steel':spec('metal',(38,44,43),.45,7),
'steel':spec('steel',(142,154,153),.55,9),
'aluminum':spec('steel',(192,202,197),.45,8),
'polymer':spec('polymer',(44,43,38),.55,5),
'rubber':spec('rubber',(24,27,26),.35,5),
'recess':spec('dark',(13,17,17),0,1),
'lens':spec('lens',(192,220,205),0),
'green_emitter':spec('glow',(49,150,69),0),
'orange':spec('paint',(191,103,42),.3,2),
}


def setup(wid):
    M={k:dict(v) for k,v in BASE.items()}
    if wid=='harmony_21':
        M.update(shell=spec('paint',(194,209,198),.8,2),frame=spec('metal',(29,39,34),.45,6),polymer=spec('polymer',(32,37,32),.45,5))
    elif wid=='protostar_csu':
        M.update(shell=spec('paint',(176,184,149),.9,3),cream=spec('paint',(215,200,180),.8,2),polymer=spec('polymer',(79,79,58),.6,5),grip=spec('rubber',(205,191,168),.5,5))
    elif wid in ('philippis_b','sondok_c'):
        snow=wid=='sondok_c'
        M.update(shell=spec('paint',(184,191,168) if snow else (119,119,108),.95,3),polymer=spec('polymer',(70,46,33) if snow else (51,46,38),.65,5),orange=spec('paint',(199,83,41),.3,2))
    elif wid=='badlands_mk_24':
        M.update(shell=spec('paint',(115,49,46),1.,3),brass=spec('gold',(170,143,91),.5,6),polymer=spec('polymer',(35,37,36),.65,4),steel=spec('steel',(82,91,91),.7,10))
    elif wid=='botheration_mk_28':
        M.update(shell=spec('paint',(48,79,81),1.,3),polymer=spec('polymer',(61,44,32),.7,5),steel=spec('steel',(155,174,178),.65,10),aluminum=spec('steel',(210,222,220),.5,8),rubber=spec('rubber',(29,26,22),.4,5))
    else:
        M.update(shell=spec('paint',(154,164,125),1.,3),polymer=spec('polymer',(65,68,49),.7,5),steel=spec('steel',(175,183,175),.6,10),rubber=spec('rubber',(34,36,29),.4,5))

    for m in M.values():
        if m['kind']=='paint':m['amp']=1.5  # subdued W123 paint grain; metal keeps directional brushing

    def key(n,fn):
        # The mapping is exhaustive: fallback is an explicit frame polymer, never auto guess.
        if wid=='harmony_21':
            if n.startswith(('muzzle_pin','port','shell_slot_floor')):return 'recess'
            if n.startswith('shell_tail') and not n.startswith('shell_tail0'):return 'orange' if fn in ('east','west') else 'frame'
            if n.startswith(('shell','muzzle_plate','muzzle_prong','rail','rear_nub','sight')):return 'shell'
            if n.startswith('shroud'):return 'black_steel'
            if n.startswith('mag_floor'):return 'rubber'
            if n.startswith('mag'):return 'aluminum'
            if n.startswith(('frame_bolt','trigger','chin','wire')):return 'steel' if 'bolt' in n else 'black_steel'
            if n.startswith(('grip','butt_pad')):return 'rubber'
            return 'frame'
        if wid=='protostar_csu':
            if n=='muzzle_bore':return 'recess'
            if n.startswith(('panel','sight','charge')):return 'black_steel'
            if n.startswith(('rcv','stock_top')):return 'shell'
            if n.startswith(('shroud','muzzle','handguard','hg_rib')):return 'cream'
            if n.startswith('grip'):return 'grip' if fn in ('east','west') and '_ch' not in n else 'polymer'
            if n.startswith(('mag','rail','lower_rail','screw','guard_screw','stock_screw','trigger')):return 'steel'
            if n.startswith('butt_pad'):return 'rubber'
            return 'polymer'
        if wid in ('philippis_b','sondok_c'):
            if n.startswith(('brake_core','charge_slot','barrel_in')):return 'recess'
            if n=='sight_lens_rim':return 'green_emitter'
            if n.startswith('sight') and not n.startswith('sight_drum'):return 'aluminum'
            if n.startswith('stock_comb'):return 'rubber'
            if n=='light_bezel' and fn=='north':return 'lens'
            if n.startswith(('light','sight_drum','trigger')):return 'black_steel'
            if n.startswith(('brake','barrel','fsight','sling','rail','rear_r','stock_arm','stock_bracket','stock_pin','mag_body')):return 'aluminum'
            if n.startswith(('front_cap','rcv_rear')) or (n.startswith('rcv_main') and (n.endswith('_paint') or fn in ('up','north','south'))):return 'shell'
            if n.startswith('panel'):return 'shell'
            if n.startswith(('bolt','charge_knob')):return 'steel'
            if n.startswith(('grip_panel','foregrip','butt_pad','mag_floor','mag_pull')):return 'rubber'
            return 'polymer'
        if wid=='badlands_mk_24':
            if n=='muzzle_bore' or n=='bolt_slot':return 'recess'
            if n.startswith(('shroud_trim','muzzle','top_post','top_rail','sight_ear')):return 'brass'
            if n.startswith(('shroud','recv_upper')):return 'shell'
            if n.startswith(('tube','clip','recv_pin','bolt_knob')):return 'steel'
            if n.startswith(('pump','grip')):return 'rubber'
            return 'polymer'
        if wid=='botheration_mk_28':
            if n=='can_face' or n=='side_vent':return 'recess'
            if n.startswith('can_perf'):return 'aluminum'
            if n.startswith('can_collar'):return 'polymer'
            if n.startswith(('can','barrel','rcv_upper','stock_strut','side_box')):return 'shell'
            if n.startswith(('tube','loop','fsight','sight_base','sight_ear','bolt_knob')):return 'steel'
            if n.startswith(('grip_panel','butt','pump_pad')):return 'rubber'
            if n.startswith(('stock_tube','stock_lower','stock_brace','trigger','sight_drum')):return 'black_steel'
            return 'polymer'
        if n=='can_face' or n in ('barrel_in','side_vent'):return 'recess'
        if n.startswith(('drum','tube','recv_bolt','recv_knob','sight_ear')):return 'steel'
        if n.startswith('bracket_lens'):return 'lens' if fn=='north' else 'steel'
        if n.startswith(('can','shield','post','recv_front','recv_rear','stock_tube')):return 'shell'
        if n.startswith(('pump','grip_panel','butt_pad')):return 'rubber'
        if n.startswith(('stock_lower','stock_brace','trigger')):return 'black_steel'
        return 'polymer'

    def material(n,fn):
        k=key(n,fn);m=M[k]
        # Rotated edge strips/end caps cannot carry coherent rip panel relief; use material grain there.
        if wid=='sondok_c' and (n.startswith('rcv_rear') or n.startswith('rcv_main2_paint')):
            return dict(m,detail=0)  # source HAKKE logo would duplicate the crisp relocated plate
        if (wid=='harmony_21' and n.startswith(('shell_body','shell_nose'))) or (wid=='protostar_csu' and n.startswith(('rcv_main','panel'))):
            return dict(m,detail=0)
        if fn not in ('east','west') or '_ch' in n or n.endswith(('_capt','_capb','_capf')) or 'groove' in n:
            return dict(m,detail=0)
        return k

    def special(e,fn,s,t):
        n=e['name'];side=fn in ('east','west');x,y,z=kit.face_point(e,fn,s,t)
        c=None
        if wid=='harmony_21':
            if side and n.startswith('shell_body') and '_groove' not in n:
                u=z if fn=='west' else -z;u0=1.15 if fn=='west' else -3.5
                if u0-.65<u<u0-.25 and 10.78<y<11.43:c=(194,105,42)
                if text_hit(u,11.43-y,'SUROS',u0,0,.13):c=(194,105,42)
                if z>5.3 and 10.5<y<10.5+min(1.4,(z-5.3)*.33):c=(194,105,42)
            if side and n.startswith('frame_bar'):
                _,fu,fv=kit.face_frame(e,fn);w=round(math.dist((0,0,0),fu)*20);h=round(math.dist((0,0,0),fv)*20)
                if text_hit(s*w,t*h,'SUROS',w*.27,2,1.5):c=(198,111,49)
            if n.startswith('sight') and fn=='south' and .25<s<.75 and .2<t<.45:c=(233,141,56)
            if n.startswith('muzzle_plate') and side and (abs(z+2.2)<.12 or abs(z+3.0)<.12) and abs(y-10.98)<.14:c=(15,20,18)
        elif wid=='protostar_csu':
            if side and n.startswith('panel') and 12.25<y<12.6:
                for z0,z1,col in ((4.5,4.8,(52,73,158)),(4.9,5.2,(161,48,40)),(6.2,6.7,(65,137,153))):
                    if z0<z<z1:c=col
                if 6.24<z<6.54 and 12.49<y<12.55:c=(173,222,213)
                if 5.35<z<6.02 and every(z,5.36,.19,.06) and y>12.44:c=(141,145,123)
        elif wid in ('philippis_b','sondok_c'):
            import hakke
            zz=hakke.zo(z)
            if side and n.startswith('panel') and wid=='sondok_c' and zz>6.4:
                c=(199,83,41)
                u=zz if fn=='west' else -zz
                if text_hit(u,13.4-y,'HAKKE',6.55 if fn=='west' else -8.2,0,.075):c=(235,231,208)
            if side and n.startswith('rcv_main') and 11.74<y<12.24 and 5.25<zz<5.95:
                if abs(y-11.98)<.05 or abs(zz-5.42)<.045 or abs(zz-5.8)<.045:c=(202,90,46) if wid=='sondok_c' else (77,91,45)
            if side and n.startswith('selector'):
                if y>12.58 and every(zz,2.6,.4,.12):c=(208,215,194)
                for zz0 in (2.9,4.0):
                    if abs(zz-zz0)<.04 and 12.22<y<12.39:c=(208,215,194)
            if n=='light_bezel' and fn=='north' and .24<s<.64 and .2<t<.35:c=(247,248,218)
        elif wid=='badlands_mk_24':
            if side and n.startswith('shroud_low') and '_groove' not in n:
                if line(y,10.64 if z<-.5 else 10.81,.04):c=(190,166,115)
                for zz in (-8.45,-6.8,-4.2,-2,.3,1.65):
                    if max(abs(z-zz),abs(y-11.06))<.065:c=(184,163,119)
            if side and n=='pump':
                row=round((y-9.15)/.34);uz=((z+4.8+(row%2)*.25)%.5)-.25;vy=y-(9.15+row*.34)
                d=max(abs(uz)*.8+abs(vy)*.65,abs(vy))
                if .15<d<.18:c=(49,53,50)
        elif wid=='botheration_mk_28' and n.startswith('can_perf') and (side or fn in ('up','down')):
            v=y if side else x*1.3;row=int((v-10)/.33)
            if math.hypot(((z+6.57+(.16 if row%2 else 0))%.33)-.165,((v-10)%.33)-.165)<.1:c=(14,18,18)
        elif wid=='fussed_dark_mk_21':
            if n.startswith('drum') and (side or fn in ('up','down')):
                v=y if side else x*1.2;row=int((v-10)/.3)
                if math.hypot(((z+4.3+(.15 if row%2 else 0))%.3)-.15,((v-10)%.3)-.15)<.08:c=(15,19,17)
            if n=='bracket_lens' and fn=='north' and .23<s<.45 and .23<t<.35:c=(250,254,236)
        # Source pump flute accents remain sparse over the polymer/rubber material, never fill a whole face.
        if wid in ('botheration_mk_28','fussed_dark_mk_21') and side and n.startswith('pump_body'):
            start=-4.0 if wid=='botheration_mk_28' else -1.6
            if .22<t<.76 and every(z,start,.38,.035):c=(30,28,22) if wid=='botheration_mk_28' else (17,23,18)
            elif .22<t<.76 and every(z,start+.05,.38,.022):c=(89,70,48) if wid=='botheration_mk_28' else (64,69,49)
        return None if c is None else c+(255,)
    return M,material,special


# Material revision 2: expose machined fittings and restore large source colour blocks.
_setup_r1 = setup

def setup(wid):
    from paint import camo
    M, old_material, old_special = _setup_r1(wid)
    M['black_steel'].update(color=(66,74,72), detail=.35)
    M['receiver_steel']=spec('steel',(91,103,103),.4,8)
    M['rubber'].update(color=(20,23,22), detail=.2, plate=False)
    M['polymer'].update(color={
        'harmony_21':(66,72,64),'protostar_csu':(84,88,66),
        'philippis_b':(72,67,59),'sondok_c':(87,66,50),
        'badlands_mk_24':(61,66,64),'botheration_mk_28':(84,66,50),
        'fussed_dark_mk_21':(81,88,65)}[wid])
    if 'frame' in M:M['frame'].update(color=(52,61,55),kind='metal')
    if wid=='botheration_mk_28':M['receiver_steel'].update(color=(92,111,114))
    if wid=='fussed_dark_mk_21':M['receiver_steel'].update(color=(92,104,87))
    if wid=='protostar_csu':M['receiver_steel'].update(color=(96,105,89))
    for m in M.values():
        if m['kind']=='paint':m.update(wear=False,detail=min(m['detail'],.45))
    palettes={
      'protostar_csu':((176,184,149),(125,140,104),(215,200,180)),
      'philippis_b':((119,119,108),(78,81,77),(159,158,145)),
      'sondok_c':((184,191,168),(116,129,111),(211,213,191)),
      'badlands_mk_24':((115,49,46),(78,35,35),(143,75,62)),
      'botheration_mk_28':((48,79,81),(25,49,54),(115,150,154)),
      'fussed_dark_mk_21':((154,164,125),(111,127,95),(200,192,163))}

    def role(n,fn):
        if wid=='harmony_21':
            if n.startswith(('rail','rear_nub','sight','muzzle_plate','muzzle_prong','shell_slot_rail')):return 'aluminum'
            if n.startswith('shell_canopy'):return 'steel'
            if n.startswith(('trigger','frame_bolt','wire','chin')):return 'receiver_steel'
        elif wid=='protostar_csu':
            if n.startswith(('shroud','muzzle_','handguard','hg_rib')) and n!='muzzle_bore':return 'aluminum'
            if n.startswith(('guard','lower_rail','charge','panel')):return 'receiver_steel'
        elif wid in ('philippis_b','sondok_c'):
            if n.startswith(('panel','selector','guard','front_chin','frame_web')):return 'receiver_steel'
            if n.startswith(('bolt','charge_knob','trigger')):return 'steel'
        elif wid=='badlands_mk_24':
            if n.startswith('recv_upper0'):return 'receiver_steel'
            if n.startswith(('recv_collar','recv_lower','port','tail','guard','trigger')):return 'black_steel'
            if n.startswith(('top_rail','top_post')):return 'steel'
        elif wid=='botheration_mk_28':
            if n.startswith(('barrel','side_box','rcv_upper')) and not n.startswith(('rcv_upper_rear','rcv_upper_tail')):return 'receiver_steel'
            if n.startswith(('can_lip','can_collar','rcv_collar','rcv_lower','port','guard','trigger')):return 'black_steel'
        else:
            if n.startswith(('recv_front','recv_rear','side_box','post_')):return 'receiver_steel'
            if n.startswith(('guard','trigger','recv_tail','bracket')) and not n.startswith('bracket_lens'):return 'black_steel'
        return None

    def material(n,fn):
        r=role(n,fn)
        m=M[r] if r else old_material(n,fn)
        if isinstance(m,str):m=M[m]
        if fn not in ('east','west') or '_ch' in n or n.endswith(('_capt','_capb','_capf')):
            return dict(m,detail=0)
        return dict(m)

    def special(e,fn,s,t):
        n=e['name'];side=fn in ('east','west');x,y,z=kit.face_point(e,fn,s,t)
        c=old_special(e,fn,s,t)
        if c is not None:return c
        m=material(n,fn)
        # Camo is deliberately two/three large hard-edged patches on the actual painted covers.
        # Fine random wear is disabled, keeping the machined neighbours readable.
        if wid in palettes and m['kind']=='paint' and n.startswith(('shell','rcv','recv_upper','stock_top','stock_strut','stock_tube','can','shield','front_cap')):
            cols=palettes[wid]
            patch=camo((x,y,z),cols,cell=2.1,seed=31,cuts=(.56,.66))
            if patch!=cols[0]:return tuple(patch)+(255,)
        if wid=='harmony_21' and side and n.startswith('mag_body') and 5.15<y<7.1:
            if any(abs(z-a)<.025 for a in (6.88,7.17,7.46)):return (100,114,107,255)
        if wid=='protostar_csu' and side and n.startswith('panel'):
            if 12.19<y<12.24 and every(z,4.4,.24,.045):return (199,211,192,255)
        if wid in ('philippis_b','sondok_c') and side and n.startswith('mag_body'):
            import hakke
            zz=hakke.zo(z)
            if 4.8<y<7.1 and any(abs(zz-a)<.026 for a in (7.65,8.05,8.45)):return (108,122,116,255)
            if 4.35<y<4.55 and any(abs(zz-a)<.07 for a in (7.75,8.5)):return (23,29,26,255)
        if wid=='badlands_mk_24' and side and n.startswith(('recv_upper1','recv_upper2')) and 6.65<z<8.7 and abs(y-10.67)<.026:
            return (185,160,110,255)
        if wid=='botheration_mk_28' and side and n.startswith('can_collar') and 11.5<y<12.1 and every(z,-5.55,.13,.045):
            return (132,149,143,255)
        if wid=='fussed_dark_mk_21' and side and n.startswith('post_') and not n.startswith('post_bolt') and abs(y-10.95)<.026:
            return (183,196,178,255)
        return None
    return M,material,special
