"""W123 semantic materials: subdued source relief and material-specific grain.
Colours are selected from the calibrated nx/px rip renders, not W123 weapon colours.
The kit performs the material bake. special() is reserved for sparse identity marks.
"""
import math
from _w3lib import face_pt
from _identity import glyph,line

def spec(kind,color,detail=.65,**kw):return dict(kind=kind,color=color,detail=detail,**kw)
def material_specs(w):
    common={'recess':spec('dark',(19,22,24),0,amp=1),'rubber':spec('rubber',(20,22,23),.18,amp=4,plate=False),
            'steel':spec('steel',(117,123,127),.65,amp=8),'darksteel':spec('metal',(82,89,94),.65,amp=5),
            'polymer':spec('polymer',(57,62,60),.55,amp=4)}
    extra={
     'thistle_and_yew':{'polymer':spec('polymer',(79,75,71),.8,amp=4),'blue':spec('paint',(104,121,139),.85),'bolt':spec('steel',(146,152,157),.75),'strap':spec('cloth',(40,40,39),.2,amp=3),'optic':spec('metal',(48,53,60),0)},
     'armillary_psu':{'navy':spec('paint',(40,52,75),1.0),'white':spec('paint',(190,186,182),.7),'silver':spec('steel',(188,188,183),.6,amp=8),'polymer':spec('polymer',(59,64,66),.7,amp=4)},
     'sonata_48':{'mint':spec('paint',(157,178,171),.8),'red':spec('paint',(133,37,40),.85),'silver':spec('steel',(192,198,199),.55,amp=9),'polymer':spec('polymer',(59,62,64),.65,amp=4)},
     'inverness_sr2':{'purple':spec('paint',(81,69,88),.85),'steel':spec('steel',(91,94,97),.65,amp=7),'magpaint':spec('paint',(49,58,53),.8),'polymer':spec('polymer',(59,63,61),.55,amp=4)},
     'black_tiger_2sr':{'mint':spec('paint',(190,208,194),.85),'lower':spec('polymer',(48,60,51),.7,amp=4),'silver':spec('steel',(156,170,161),.55,amp=7),'brass':spec('gold',(175,103,43),.3,amp=6),'magcase':spec('polymer',(69,69,60),.4)},
     'madrugada_sr2':{'olive':spec('paint',(62,77,40),1.0),'bone':spec('paint',(190,183,171),.75),'barrelsteel':spec('steel',(185,182,172),.6,amp=8),'battery':spec('metal',(137,124,90),.65,amp=6),'red':spec('paint',(144,45,36),.25),'polymer':spec('polymer',(58,62,51),.65,amp=4)}
    }[w]
    materials=dict(common,**extra)
    # W123 R2: controlled exposed substrate colour instead of grey dirt on every panel.
    for key,m in materials.items():
        if m['kind']=='paint':
            m['wear']=(140,148,147) if key in ('blue','navy','purple') else (109,115,105) if key in ('olive','bone') else (121,131,127)
    materials['machined']=spec('steel',(134,142,146),.65,amp=7)
    materials['receiver_metal']=spec('metal',(84,92,96),.7,amp=5)
    return materials

def choose_material(n,face,g):
    w=g['IDENTITY_ID'];side=face in ('east','west');key=None
    # Every part gets an explicit semantic material; nothing falls back to auto palette.
    if w=='thistle_and_yew':
        pairs=[(('butt_rubber','cheek_pad','grip_insert'),'rubber'),(('strap_band',),'strap'),
               (('sc_',),'optic'),(('receiver','rcv_rear','port_lip','rail'),'blue'),(('bolt',),'bolt'),
               (('barrel','supp','trigger'),'darksteel'),(('ch_','gas_','front_post','clamp_bolt','cap_screw','forend_cap','sling','web_plate','tg_'),'steel'),
               (('mag_',),'darksteel')];fallback='polymer'
    elif w=='armillary_psu':
        pairs=[(('muzzle_inner','eject_port'),'recess'),(('butt_pad','grip_panel'),'rubber'),
               (('muzzle','bipod','rail_rib','forend_rib','stock_slot_rim'),'silver'),(('rcv_band','mid_strip'),'white'),
               (('rcv_top','forend','upper_block','stock_cap','butt_plate','rcv_lower_plate','sight_'),'navy'),
               (('shroud','top_bar','rail','ch_handle','trigger'),'darksteel'),(('mag_latch','mag_floor'),'steel')];fallback='polymer'
    elif w=='sonata_48':
        pairs=[(('muzzle_inner','logo_slot'),'recess'),(('butt_pad','grip_panel','handguard','hg_rib'),'rubber'),
               (('muzzle','spike','trigger'),'silver'),(('body_rear_panel','body_upper','top_front','sight_ring'),'mint'),
               (('red_band','body_mid','body_rear'),'red'),(('front_cap','sight_house','sight_bar','sight_vents','lower_block','tg_'),'darksteel')];fallback='polymer'
    elif w=='inverness_sr2':
        pairs=[(('cable','butt_pad','grip_panel'),'rubber'),(('rcv_port','rcv_vents'),'recess'),
               (('mag_panel',),'magpaint'),(('barrel_neck','barrel','bracket','neck_collar','front_rail','body_rail','sight_mount','trigger'),'darksteel'),
               (('butt_plate','stock_top','body_upper','body_panel','receiver','front_block','sight'),'purple'),
               (('stock_ribs','stock_strut','stock_mid','under_thumb','tg_','fil_','forend_low','rcv_low'),'steel')];fallback='polymer'
    elif w=='black_tiger_2sr':
        pairs=[(('win_cart',),'brass'),(('win_mag',),'magcase'),(('butt_pad','grip_panel'),'rubber'),
               (('side_rail','shroud_rib','front_band','ejector'),'silver'),
               (('upper','up_','win_rear','shroud','claw','sight','veist_plate'),'mint'),(('trigger','mag_'),'darksteel')];fallback='lower'
    else:
        pairs=[(('canister_band',),'red'),(('canister',),'battery'),(('barrel',),'barrelsteel'),
               (('butt_pad','stock_pad','grip_ribs'),'rubber'),(('rod','lever','ch_disc','strut','front_block','front_vents','mag_'),'darksteel'),
               (('stock_rim','butt_slot','fil_','hinge','top_strut','rcv_frame','rail','front_plate','front_sight','peep','tg_','port_depth'),'bone'),
               (('stock_top','stock_lower','stock_front','receiver','rcv_low','fixed_mag','port_ring'),'olive')];fallback='polymer'
    for prefixes,k in pairs:
        if n.startswith(prefixes):key=k;break
    key=key or fallback
    # Source exposed metal boundaries; coloured outer shells remain paint.
    overrides={
        'thistle_and_yew':[(('rail','port_lip','lower_rcv'),'receiver_metal'),(('forend_slot','web_plate','bolt'),'machined')],
        'armillary_psu':[(('rcv_lower','rcv_lower_plate','spine','mid_rear','tg_','rail','ch_handle'),'receiver_metal'),(('rcv_band','mid_strip','forend_rib','bipod_pin'),'machined')],
        'sonata_48':[(('body_mid','body_rear','handle','lower_block','tg_'),'receiver_metal'),(('sight_bar','sight_ring','muzzle_collar','muzzle_tip'),'machined')],
        'inverness_sr2':[(('body_panel','rcv_low','front_block_rear','sight_mount','tg_'),'receiver_metal'),(('neck_collar','stock_ribs','front_rail'),'machined')],
        'black_tiger_2sr':[(('win_rear','ejector','claw','tg_','trigger','shroud_tip'),'receiver_metal'),(('side_rail','front_band','veist_plate'),'machined')],
        'madrugada_sr2':[(('rcv_low','port_ring','fixed_mag','hinge','tg_','front_plate','rcv_frame','peep','rail','top_strut'),'receiver_metal'),(('port_depth','barrel_collar','barrel_ring','ch_disc'),'machined')]
    }
    for prefixes,value in overrides[w]:
        if n.startswith(prefixes):key=value;break
    if w=='sonata_48' and n.startswith('body_rear_panel'):key='mint'
    # Scope interiors must stay dark and open. They are authored to the base, so have no reliable rip relief.
    inner=(n.startswith(('sc_floor','sight_floor','peep_base')) and face=='up' or
           n.startswith(('sc_ceiling','sight_roof','sight_hood','sight_ring_t','peep_top')) and face=='down' or
           n.startswith(('sc_wall_in_l','sight_wall_l','sight_ring_l','peep_l')) and face=='east' or
           n.startswith(('sc_wall_in_r','sight_wall_r','sight_ring_r','peep_r')) and face=='west')
    if inner:return 'recess'
    # Invented/base-adapted geometry and narrow end faces can pick up unrelated source islands: use material grain only.
    disable=n.startswith(('sc_','sight_','peep_','cable','port_depth','mag_stub','muzzle_inner'))
    disable=disable or (w=='black_tiger_2sr' and n.startswith(('up_bot','veist_plate')))
    disable=disable or (w=='madrugada_sr2' and n.startswith(('stock_rim','top_strut','rail','rcv_frame','port_depth')))
    disable=disable or ('_cut' in n and not side) or ('_vent_' in n) or n.startswith('muzzle_centre_rail')
    if disable:return dict(g['MATERIALS'][key],detail=0,wear=False)
    if face in ('north','south') and n.startswith(('shroud','supp','muzzle','barrel','spike')):
        return dict(g['MATERIALS'][key],detail=0,wear=False)
    return key

def material_decals(e,fn,s,t,g):
    n=e['name'];w=g['IDENTITY_ID'];side=fn in ('east','west');p=face_pt(e,fn,s,t)
    ix,iy=g['ix_of'](p[2]),g['iy_of'](p[1]);c=None
    if w=='thistle_and_yew':
        if side and n.startswith('web_plate'):
            # Triangular original stock-web reinforcement engraving; no whole-face base fill.
            if min(abs(t-.15),abs(t-(.15+.67*s)),abs(s-.85))<.025:c=(126,132,130)
        if n=='supp' and fn=='north' and math.hypot(s-.5,t-.5)<.19:c=(12,14,15)
    elif w=='armillary_psu':
        if side and n.startswith('sight_wall'):
            rr=math.hypot((s-.5)*1.2,t-.5)
            if .19<rr<.23:c=(165,172,179)
    elif w=='sonata_48':
        if side and n.startswith(('body_mid','red_band')):
            if glyph('SUROS',ix,iy,288,88,2.2,fn=='west'):c=(184,207,198)
            if 278<ix<286 and 91<iy<99 or 280<ix<295 and 88<iy<91:c=(184,207,198)
        if side and n.startswith('sight_vents'):
            # Three slanted pale inset marks visible on original optic housing.
            for a in (.20,.5,.8):
                if .15<t<.85 and abs(s-(a+.16*(t-.5)))<.025:c=(133,156,160)
    elif w=='inverness_sr2':
        if side and n.startswith('mag_panel'):
            # Small pale triangular manufacturer badge near the magazine shoulder.
            if .1<t<.2 and abs(abs(s-.5)-(.2-t)*1.1)<.02:c=(144,151,145)
    elif w=='black_tiger_2sr':
        if side and n.startswith('veist_plate'):
            if glyph('VEIST',ix,iy,165,109,2.0,fn=='west'):c=(139,70,26)
            if 153<ix<164 and 110<iy<117 and iy-110<(ix-153)*.65:c=(139,70,26)
        if side and n.startswith('shroud'):
            for cx,cy in ((535,72),(544,82),(535,92)):
                if (ix-cx)**2+(iy-cy)**2<3.6**2:c=(18,27,23)
        if side and n.startswith('win_mag') and .65<s<.95 and (int(s*70)+int(t*20))%12<2:c=(173,187,177)
    elif w=='madrugada_sr2':
        if side and n.startswith('receiver') and glyph('OMOLON',ix,iy,310,51,2.25,fn=='west'):c=(151,48,37)
        if side and n.startswith('port_ring'):
            for cx,cy,r in g['PORTS']:
                rr=math.hypot(ix-cx,iy-cy)
                if r+2<rr<r+4:c=(178,178,164)
        # Original camouflage is a sparse two-colour stencil over the olive paint, leaving material visible.
        if c is None and side and n.startswith(('stock_top','stock_lower','stock_front','receiver')):
            from _w3lib import blob
            v=blob(p,.65,.4)
            if v>.55:c=(46,61,30)
            elif v<-.58:c=(82,98,51)
    # Hand-authored reference motifs: sparse one-texel relief, not a uniform colour tile.
    if side and c is None:
        ua=abs(e['to'][2]-e['from'][2]);va=abs(e['to'][1]-e['from'][1])
        fw=max(1,round(ua*g['T']));fh=max(1,round(va*g['T']))
        ii=min(fw-1,int(s*fw));jj=min(fh-1,int(t*fh))
        if w=='thistle_and_yew' and n.startswith(('mag_body','mag_window')) and .14<t<.86:
            # Pressed vertical magazine channels seen on the source's dark sheet metal.
            if ii in (max(2,fw//5),max(3,4*fw//5)):c=(29,35,38)
            elif ii in (max(2,fw//5)+1,max(3,4*fw//5)+1):c=(122,131,135)
        elif w=='armillary_psu' and n.startswith(('forend_rib','rail_rib')) and .15<t<.85:
            if ii%5==0:c=(40,48,51)
            elif ii%5==1:c=(185,193,194)
        elif w=='sonata_48' and n.startswith(('handguard','hg_rib')) and .12<s<.88:
            if jj%7==0:c=(10,14,16)
            elif jj%7==1:c=(51,56,57)
        elif w=='inverness_sr2' and n.startswith('rcv_vents'):
            # Six cooling slots, two rows of three, matching the source receiver relief.
            if jj in (max(1,fh//3),max(2,2*fh//3)) and ii%(max(3,fw//3))<max(1,fw//5):c=(11,16,18)
        elif w=='black_tiger_2sr' and n.startswith('win_cart') and .14<t<.86:
            if ii%7==0:c=(77,44,21)
            elif ii%7==1:c=(217,158,79)
        elif w=='madrugada_sr2' and n.startswith(('grip','grip_ribs')) and .12<s<.88:
            if jj%6==0:c=(12,17,14)
            elif jj%6==1:c=(92,103,87)
    # Sparse cyan emitter pixel on authored optic end frames; no glass filling sight openings.
    if n.startswith(('sight','peep','sc_')) and fn in ('north','south') and .47<s<.53 and .47<t<.53:c=(100,168,172)
    return (*c,255) if c is not None else None
