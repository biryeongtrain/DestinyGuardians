"""Hand-authored, deterministic face painting for the W325 m2 identity pass.
Every visible face receives exact flat material paint. One-texel edge/seam lines
are authored here because kit.special bypasses pixel-style postprocessing.
No source projection, grime, random noise, or invented labels.
"""
from PIL import Image, ImageDraw
import math
AX={'north':(0,1),'south':(0,1),'east':(2,1),'west':(2,1),'up':(0,2),'down':(0,2)}
DARK=(43,46,47); BLACK=(22,25,27); STEEL=(123,134,135); PALE=(208,216,209)
def shift(c,v): return tuple(max(0,min(255,x+v)) for x in c)
GLYPHS={'V':['101','101','101','101','010'],'E':['111','100','110','100','111'],'I':['111','010','010','010','111'],'S':['111','100','111','001','111'],'T':['111','010','010','010','010']}

def material(kind,n):
    if kind in ('sand','yellow'):
        if n=='sup_bore' or '_joint_' in n or n.startswith('eject_slot') or n.endswith('_vent'):return BLACK
        if n.startswith('sup') and 'mid_band' not in n:return (230,226,213) if kind=='sand' else (220,224,222)
        if n.startswith(('recv','stock_main','stock_over','stock_under','stock_chin','front_housing','win_end','win_lip')):return (102,115,69) if kind=='sand' else (81,84,84)
        if n.startswith('mag_body'):return (154,145,92) if kind=='sand' else (159,200,60)
        if n.startswith('mag_front'):return (216,218,201)
        if n.startswith('win_lip'):return (170,181,167)
        if n.startswith('plate'):return (62,69,60) if kind=='sand' else (57,63,60)
        if n.startswith(('grip','fg_')):return (62,69,58)
        if n.startswith('pad'):return (57,61,53)
        if n.startswith('sight'):return (94,106,69) if kind=='sand' else (65,72,66)
        return (71,77,70)
    if kind=='home':
        if n.startswith(('rcv_port',)) and n!='rcv_port_lip' or n=='brake_bore':return BLACK
        if n.startswith(('rcv_','well_lip')):return (107,109,59)
        if n.startswith(('well_frame','lever')):return (168,172,149)
        if n.startswith(('grip',)):return (109,66,43) if n not in ('grip_cap','grip_heel') else DARK
        if n.startswith(('brake','sleeve','barrel','pin','bolt')):return (96,107,109)
        if n.startswith(('mag_',)):return (47,53,54)
        if n.startswith('hg'):return (58,65,65)
        return (55,62,61)
    if kind=='ros':
        if n.startswith(('muz_prong','spike','drum','st_rail','st_upright')):return (177,217,226)
        if n.startswith(('shroud','nose','rcv_body','rcv_top','rcv_ramp','fore_plate','sight_cheek','sight_roof','sight_front')):return (75,120,133)
        if n.startswith(('mag','rcv_lower','grip','frame','guard')):return (86,76,65)
        if n.startswith(('st_','vent','rib','sight')):return (61,57,53)
        return (77,72,64)
    if kind=='cyd':
        if n in ('sup_bore','mag_window','rcv_window') or n.startswith(('vent_','cover_slot','st_pad_slot')):return BLACK
        if n.startswith(('cover','tube','fore_plate','st_block','st_rear','st_front','st_bar')) and not n.startswith(('tube_nose','tube_rib','cover_front')):return (119,61,62)
        if n.startswith(('rcv_upper','rcv_lower','mid_rail','side_lever')):return (90,101,104)
        return (54,61,64)
    return DARK

class Painter:
    def __init__(self,kind,T=20):self.kind=kind;self.T=T;self.cache={}
    def __call__(self,e,fn,s,t):
        if 'reticle' in e['name']:return (70,235,90,255)
        key=(e['name'],fn)
        if key not in self.cache:self.cache[key]=self.paint(e,fn)
        im=self.cache[key];return im.getpixel((min(im.width-1,int(s*im.width)),min(im.height-1,int(t*im.height))))
    def paint(self,e,fn):
        n=e['name'];k=self.kind;T=self.T;f=e['from'];g=e['to'];ua,va=AX[fn]
        w=max(1,round(abs(g[ua]-f[ua])*T));h=max(1,round(abs(g[va]-f[va])*T))
        base=material(k,n);im=Image.new('RGB',(w,h),base);d=ImageDraw.Draw(im)
        side=fn in ('east','west');z0,z1=f[2],g[2];y0,y1=f[1],g[1]
        def xy(z,y):
            u=(z-z0)/(z1-z0);u=u if fn=='west' else 1-u
            return (round(u*w),round((y1-y)/(y1-y0)*h))
        def line(points,col,width=1):d.line([xy(*p) for p in points],fill=col,width=width)
        def rect(z,y,Z,Y,col):
            a=xy(z,y);b=xy(Z,Y);d.rectangle((min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])),fill=col)
        def poly(points,col):d.polygon([xy(*p) for p in points],fill=col)
        def slot(z,y,Z,Y):
            rect(z,y,Z,Y,BLACK);line([(z,y-.05),(Z,y-.05)],shift(base,30))
        def bolt(z,y):
            x,Y=xy(z,y);d.rectangle((x-1,Y-1,x+1,Y+1),fill=shift(base,40));d.point((x,Y),fill=BLACK)
        # Authored hard-edged camo panels, continuous in model coordinates.
        camo=(k in ('sand','yellow') and n.startswith(('recv','stock_main','stock_over','stock_under','stock_chin','front_housing','win_end'))) or (k=='ros' and n.startswith(('shroud','nose','rcv_body','rcv_top','rcv_ramp','fore_plate','sight_cheek','sight_roof','st_rail','st_upright')))
        if camo:
            light=(204,211,186) if k=='sand' else (129,137,134) if k=='yellow' else (181,221,232)
            mid=(68,84,46) if k=='sand' else (48,56,55) if k=='yellow' else (108,163,179)
            if side:
                for off in range(-12,20,4):
                    poly([(off,8),(off+1.5,8),(off+1.5,9),(off+2.2,9),(off+2.2,10.4),(off+3.6,10.4),(off+3.6,11),(off+2.5,11),(off+2.5,12.8),(off+1.6,12.8),(off+1.6,11.6),(off+.6,11.6),(off+.6,10),(off,10)],light)
                    poly([(off+.7,9.3),(off+1.6,9.3),(off+1.6,10.1),(off+2.5,10.1),(off+2.5,10.7),(off+1.3,10.7),(off+1.3,10.3),(off+.7,10.3)],mid)
            elif w>7 and h>7:
                d.rectangle((w//3,0,w//2,h//2),fill=light);d.rectangle((w//2,h//3,w-1,h//2),fill=light)
        if side:
            if k in ('sand','yellow'):
                if n.startswith('stock_main'):
                    col=(205,213,190) if k=='sand' else (153,161,155)
                    line([(11.5,11.66),(12.7,10.84),(14.5,10.68),(15.5,10.2)],col,2)
                    line([(11.6,8.15),(12.1,8.55),(13.4,8.55),(15.2,9.5)],col,2)
                    for z,y in ((12.2,11.35),(14.9,11.3),(12.1,8.7),(15.1,8.4)):bolt(z,y)
                if n.startswith('plate_') and '_vent' not in n and '_bolt' not in n:
                    slot(3.25,11.65,4.9,11.72);slot(6.5,11.6,8.2,11.67)
                    for z in (3.0,5.3,6.2,8.3):bolt(z,11.15)
                    # VEIST is on the aft upper receiver in both original textures.
                    if '_aft' in n:
                        color=(168,178,105) if k=='sand' else (170,215,65)
                        # Readable glyphs on both sides, not blindly mirrored.
                        sx,sy=4,3
                        for char in 'VEIST':
                            for yy,row in enumerate(GLYPHS[char]):
                                for xx,v in enumerate(row):
                                    if v=='1':d.point((sx+xx,sy+yy),fill=color)
                            sx+=4
                if n.startswith('mag_body'):
                    for z in [5.8+i*.24 for i in range(23)]:
                        for y in (10.15,10.45):
                            x,Y=xy(z,y);d.rectangle((x-1,Y-1,x+1,Y+1),outline=shift(base,-45));d.point((x,Y-1),fill=shift(base,30))
                if n=='mag_front':
                    accent=(168,52,40) if k=='sand' else (152,198,58)
                    for z in (4.75,5.1):line([(z,10.62),(z+.45,9.98)],accent,3)
                if n.startswith(('grip','fg_grip')):
                    for y in [6.2+i*.29 for i in range(10)]:line([(z0+.12,y),(z1-.12,y+.14)],shift(base,-15))
                if n.startswith('sup') and n!='sup_bore':
                    slot(z0+.15,10.31,z1-.15,10.35)
                    if 'collar' in n:line([(-1.3,10.1),(-1.3,10.9)],(138,144,132));line([(-.6,10.1),(-.6,10.9)],(138,144,132))
            if k=='home':
                if n.startswith('rcv_upper'):
                    line([(2.0,11.56),(4.8,11.56),(4.8,11.88),(5.7,11.88),(5.7,12.16),(7.8,12.16)],(53,60,39))
                    slot(2.3,11.65,4.4,11.91)
                    line([(2.35,11.69),(4.2,11.69)],(181,188,177),2)
                    for z,y in ((5.6,11.5),(7.7,11.8)):bolt(z,y)
                    # Cross stamp seen on the original receiver.
                    line([(6.45,11.6),(6.7,11.85)],(54,60,40));line([(6.45,11.85),(6.7,11.6)],(54,60,40))
                if n=='rcv_well':
                    line([(2.55,9.15),(4.65,9.3),(4.8,10.5),(2.55,10.5),(2.55,9.15)],(175,182,151))
                    line([(2.7,9.3),(4.5,9.4),(4.6,10.35)],(61,68,39))
                if n.startswith('grip') and n not in ('grip_heel','grip_cap'):
                    for j in range(5):
                        y=7.6+j*.54;line([(6.9,y),(8.4,y+.46)],(59,41,30),2);line([(6.9,y+.10),(8.4,y+.56)],(151,99,60))
                if n.startswith('hg_'):
                    line([(-5.0,10.95),(-3,10.95),(-1.7,10.2),(1.5,10.2)],(34,41,42))
                if n.startswith('st_'):
                    for z in (11.6,13.8):bolt(z,10.65)
                if n.startswith('mag_'):
                    for z in (2.6,3.6,4.25):line([(z,6.6),(z,8.8)],(25,32,33));line([(z+.07,6.6),(z+.07,8.8)],(84,92,91))
            if k=='ros':
                if n.startswith('drum'):
                    # A single world-space engraving spans all four octagon strips.
                    # Painting a separate normalised circle on each strip would make a cross.
                    idx=int(n.split('_')[1][1]);cz,cy=((-2.06,10.9),(-3.16,9.72),(-2.06,9.72))[idx]
                    for xx in range(w):
                        u=(xx+.5)/w;z=z0+(u if fn=='west' else 1-u)*(z1-z0)
                        for yy in range(h):
                            y=y1-(yy+.5)/h*(y1-y0);dz,dy=z-cz,y-cy;r=math.hypot(dz,dy)
                            col=(190,222,231)
                            if .46<r<.52:col=(87,129,140)
                            if abs(dz+dy)<.055 and r<.39:col=(37,59,64)
                            if abs(dz+dy-.09)<.027 and r<.39:col=(230,242,240)
                            d.point((xx,yy),fill=col)
                if n.startswith(('shroud','nose')):
                    slot(-5.8,10.85,-4.6,11.05);slot(-6.7,9.5,-5.8,9.65)
                    for z,y in ((-6.3,9.35),(-4.8,10.5),(-.3,9.3)):bolt(z,y)
                if n.startswith(('rcv_body','rcv_top','fore_plate')):
                    line([(.5,9.45),(2.7,9.45),(3.3,9.95),(6.4,9.95),(6.4,10.65),(8.4,10.65)],(182,219,229),2)
                    for z,y in ((1.1,8.6),(3.9,8.6),(6.9,10.6),(8.15,11.0)):bolt(z,y)
                    slot(5.15,9.8,6.35,10.1)
                if n.startswith('sight_'):
                    line([(4.6,12.66),(5.4,12.66),(6.2,13.0),(7.5,13.0)],(175,215,225))
                if n.startswith('st_'):
                    line([(9.1,10.13),(11.8,10.13),(12.5,8.2),(13.3,8.2)],(177,217,226),2)
            if k=='cyd':
                if n.startswith('cover'):
                    line([(-4.3,11.4),(-2.4,11.4),(-1.8,11.72),(1.1,11.72),(1.5,11.4),(3.6,11.4)],(66,35,37))
                    for z in (-3.9,.9,3.8):bolt(z,11.6)
                if n.startswith('mid_rail'):
                    slot(-4.1,9.75,-.1,10.0)
                    for z in [-3.9+i*.28 for i in range(14)]:line([(z,10.25),(z,10.82)],(155,167,169));line([(z+.08,10.25),(z+.08,10.82)],BLACK)
                    for z in (.4,1.0,1.6):slot(z,10.6,z+.3,10.74)
                if n.startswith('rcv_upper'):
                    slot(4.8,10.3,6.25,10.6);line([(4.8,10.26),(6.25,10.26)],(167,178,175))
                    line([(6.65,9.85),(6.65,11.5),(8.1,11.5)],(47,59,62))
                    for z in (6.7,8.0):bolt(z,11.1)
                if n.startswith('fore_plate'):
                    line([(1.0,8.2),(2.6,8.2),(4.7,9.2)],(158,87,84));bolt(4.6,9.15)
                if n.startswith(('st_block','st_rear')):
                    for z,y in ((10,10.9),(13.7,10.9),(13.7,7.65)):bolt(z,y)
                if n.startswith('st_inset'):slot(10.4,10.4,12.75,10.52)
                if n.startswith('tube_rib'):
                    for xx in range(3,w-2,4):d.line((xx,3,xx,h-4),fill=(113,124,126))
                if n.startswith('sup') and 'bore' not in n:slot(z0+.15,10.1,z1-.15,10.2)
            if k in ('ros','cyd') and n.startswith('rcv_lower'):
                line([(.7,8.65),(3.8,8.65),(4.3,8.9),(6.4,8.9)],shift(base,-28),2)
                line([(.7,8.74),(3.8,8.74)],shift(base,30))
                for z in (1.0,4.7,6.4):bolt(z,8.4)
            if k=='cyd' and n.startswith('mid_rail'):
                line([(.8,10.0),(3.5,10.0),(3.5,10.7)],(49,62,64))
                line([(.8,10.12),(3.3,10.12)],(138,151,152))
                for z in (.8,3.3):bolt(z,9.7)
            # Stipple and recessed magazine panels, as opposed to featureless blocks.
            if k in ('ros','cyd') and n.startswith('mag'):
                if n=='mag_body':
                    d.rectangle((3,3,w-4,h-4),outline=shift(base,24))
                    for xx in (5,w-6):d.line((xx,6,xx,h-7),fill=shift(base,-25))
                    d.rectangle((w//3,h//3,w*2//3,h*2//3),outline=shift(base,-28))
            if n in ('grip_panel','grip_core'):
                for xx in range(3,w-3,4):
                    for yy in range(3,h-3,4):d.point((xx,yy),fill=shift(base,-20))
            if n.startswith(('sight_cheek','sight_knob','sight_dial')):
                if w>5 and h>5:
                    d.rectangle((2,2,4,4),fill=BLACK);d.point((3,2),fill=(189,193,169))
        # Thin top highlights / bottom seams exactly one texel wide.
        if w>=3 and h>=3 and not (n.startswith('drum') and side):
            d.line((0,0,w-1,0),fill=shift(base,37));d.line((0,h-1,w-1,h-1),fill=shift(base,-24))
            d.line((0,1,0,h-2),fill=shift(base,17));d.line((w-1,1,w-1,h-2),fill=shift(base,-14))
        # Small tinted emitters are on frame faces; never fill the open ADS window.
        if n.startswith('sight_sill') or n in ('sight_base','sight_rear_bezel','sight_tail'):
            if fn in ('north','south') and w>4 and h>2:
                lens=(210,80,41) if k in ('home','sand','yellow') else (87,195,91)
                d.rectangle((w//2-1,1,w//2+1,min(3,h-2)),fill=lens);d.point((w//2-1,1),fill=(244,230,183))
        return im.convert('RGBA')


def geometry(els,kind):
    """Open the characteristic barrel/handguard vents, keeping original outer bounds."""
    from solid import B, octo, clean
    if kind=='ros':
        return clean([e for e in els if not (e['name'].startswith('drum') and e['name'].endswith('_hub'))])
    if kind=='home':
        out=[]
        for e in els:
            n=e['name']
            if n=='sight_hood_lip':
                out.append(B(n,(7.5,13.15,2.55),(8.5,13.32,2.7)))
            elif n=='hg_main':
                # Two actual transverse windows with a continuous top/lower beam and three posts.
                x0,x1=e['from'][0],e['to'][0];z0,z1=e['from'][2],e['to'][2]
                out.extend([B('hg_main_low',(x0,e['from'][1],z0),(x1,11.25,z1)),B('hg_main_high',(x0,11.8,z0),(x1,e['to'][1],z1))])
                for i,(a,b) in enumerate(((z0,-4.8),(-3.65,-3.25),(-2.1,z1))):out.append(B(f'hg_main_post_{i}',(x0,11.25,a),(x1,11.8,b)))
            elif n in ('brake','brake_oct','brake_d1','brake_d2'):continue
            else:out.append(e)
        # Two slots pass right through the brake, bounded by axial rings and top/bottom rails.
        for i,(a,b) in enumerate(((-8.85,-8.6),(-8.35,-8.15),(-7.9,-7.6))):out+=octo(f'brake_port_ring_{i}',8,11.16,.3,a,b)
        out+=[B('brake_port_upper',(7.86,11.33,-8.6),(8.14,11.46,-7.9)),B('brake_port_lower',(7.86,10.86,-8.6),(8.14,10.99,-7.9))]
        return clean(out)
    if kind=='cyd':
        out=[e for e in els if e['name'] not in ('sup','sup_oct','sup_d1','sup_d2')]
        # The front suppressor section's longitudinal port has actual depth through the side.
        for i,(a,b) in enumerate(((-9.45,-9.18),(-8.05,-7.75))):out+=octo(f'sup_port_ring_{i}',8,10.23,.45,a,b)
        out+=[B('sup_port_upper',(7.72,10.42,-9.18),(8.28,10.68,-8.05)),B('sup_port_lower',(7.72,9.78,-9.18),(8.28,10.04,-8.05))]
        return clean(out)
    return els
