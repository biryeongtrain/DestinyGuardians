"""W325 material pass: semantic W123 material assignment and sparse original markings.
Base colours are sampled from each weapon's original nx albedo (see material-rip-samples.json).
Geometry stays in design.py / identity.geometry. All base surfaces go through kit.materialize;
special returns only original markings, engraving, or source-derived camouflage patches.
"""
import math,json,sys
from pathlib import Path
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/art/w325'))
import kit
from identity import GLYPHS

def M(kind,color,detail=.5,**kw):return dict(kind=kind,color=color,detail=detail,**kw)

def palette(kind):
    p={
      'steel':M('steel',(112,118,118),.18,amp=8,field=.075),
      'gunmetal':M('metal',(67,71,72),.35,amp=7,field=.07),
      'polymer':M('polymer',(51,54,50),.25,amp=6),
      'rubber':M('rubber',(38,41,37),.10,amp=6),
      'recess':M('dark',(22,25,24),0,amp=1,rim=.02),
      'sightmetal':M('metal',(47,53,51),.22,amp=5),
      'lens':M('lens',(115,63,39),0),
    }
    if kind in ('sand','yellow'):
      p.update({
       'shell':M('paint',(65,76,46) if kind=='sand' else (59,57,58),.6,amp=2.5),
       'ivory':M('paint',(230,221,208) if kind=='sand' else (214,217,214),0,amp=2,field=.045,rim=.12),
       'plate':M('metal',(61,66,58) if kind=='sand' else (69,68,62),.35,amp=6),
       'magazine':M('gold',(137,129,90),.2,amp=5) if kind=='sand' else M('paint',(154,182,85),.2,amp=3),
       'white':M('paint',(199,203,187),.12,amp=2),
       'polymer':M('polymer',(55,60,50) if kind=='sand' else (66,66,57),.25,amp=6),
       'steel':M('steel',(151,153,142),.2,amp=8),
       'sightmetal':M('metal',(66,75,51) if kind=='sand' else (52,55,49),.3,amp=6),
      })
    elif kind=='home':
      p.update({
       'olive':M('paint',(90,91,59),.55,amp=2.3,field=.045),
       'handguard':M('polymer',(54,57,56),.4,amp=5),
       'stock':M('metal',(48,53,52),.26,amp=5),
       'cloth':M('cloth',(87,57,43),0,amp=8,field=.035),
       'steel':M('steel',(145,149,136),.3,amp=8,field=.07),
       'barrelsteel':M('steel',(100,106,106),0,amp=9,field=.08),
       'magazine':M('metal',(43,48,48),.35,amp=6),
      })
    elif kind=='ros':
      p.update({
       'shell':M('paint',(61,87,93),.65,amp=2),
       'frost':M('paint',(182,214,229),.4,amp=2),
       'drumsteel':M('steel',(174,208,222),0,amp=3,field=.035,rim=0),
       'frame':M('metal',(83,77,71),.5,amp=6),
       'stock':M('polymer',(35,32,29),.2,amp=4),
       'magazine':M('metal',(87,84,80),.55,amp=7),
       'polymer':M('polymer',(48,44,40),.2,amp=5),
      })
    elif kind=='cyd':
      p.update({
       'maroon':M('paint',(95,63,64),.5,amp=2.5,field=.045),
       'frame':M('metal',(70,75,75),.6,amp=7),
       'polymer':M('polymer',(47,49,47),.25,amp=5),
       'magazine':M('metal',(48,52,51),.5,amp=7),
       'suppressor':M('steel',(56,61,62),0,amp=8,field=.07),
      })
    # R2: different material families must not collapse to the same value.
    p['rubber'].update(color=(20,24,21),amp=3,field=.02)
    if kind in ('sand','yellow'):
        p['shell'].update(wear=False,detail=0)
        p['plate'].update(color=(42,47,42) if kind=='sand' else (28,32,31))
        p['gunmetal'].update(color=(93,101,96))
        p['polymer'].update(color=(61,68,58) if kind=='sand' else (76,81,72))
        p['framealloy']=M('steel',(116,124,112),.25,amp=6)
        p['ivory'].update(wear=False)
        p['magazine'].update(detail=0,wear=False)
    elif kind=='home':
        p['polymer'].update(color=(65,71,66))
        p['gunmetal'].update(color=(113,121,115))
        p['olive'].update(wear=(144,143,120))
        p['handguard'].update(color=(58,64,60))
    elif kind=='ros':
        p['shell'].update(wear=False,detail=0)
        p['frost'].update(kind='steel',wear=False)
        p['frame'].update(color=(111,104,95),detail=0)
        p['polymer'].update(color=(74,72,65))
        p['magazine'].update(color=(91,94,89))
    elif kind=='cyd':
        p['frame'].update(color=(38,44,44),detail=0)
        p['suppressor'].update(color=(83,94,96))
        p['polymer'].update(color=(67,72,68))
        p['magazine'].update(color=(74,83,81))
        p['maroon'].update(wear=(140,127,119))
    return p

def assign(kind,n,f):
    if 'reticle' in n:return dict(kind='glow',color=(70,235,90),detail=0)
    if '_joint_' in n or n.endswith('_bore') or n in ('mag_window','rcv_window') or n.startswith(('eject_slot','brake_slot','sup_slot','cover_slot','st_pad_slot')):return 'recess'
    if n.startswith('sight'):return 'sightmetal'
    if kind in ('sand','yellow'):
        if n.startswith(('recv_lower','front_housing_lip','win_end_rear')):return 'framealloy'
        if n.startswith('recv_band'):return 'gunmetal'
        if n=='trigger':return 'steel'
        if n.startswith('sup_mid_band') or n.startswith('barrel_'):return 'steel'
        if n.startswith('sup'):return 'steel' if n.startswith(('sup_band','sup_collar')) else 'ivory'
        if n.startswith('plate'):return 'recess' if n.endswith('_vent') else 'steel' if n.endswith('_bolt') else 'plate'
        if n.startswith('mag_front'):return 'white'
        if n.startswith('mag_body'):return 'magazine'
        if n.startswith(('mag_spine','win_lip','cam_disc')):return 'steel'
        if n.startswith(('pad_','grip_front_strap')):return 'rubber'
        if n.startswith(('grip_','fg_','trigger')):return 'polymer'
        if n.startswith(('recv','stock_main','stock_over','stock_under','stock_chin','front_housing','win_end')):return 'shell'
        if n.startswith(('eject_housing','win_back','stock_top','rail','holo_rail','rear_rail')):return 'gunmetal'
        return 'gunmetal'
    if kind=='home':
        if n.startswith(('rcv_lower','rcv_trigger_box','rcv_endplate','guard_','trigger')):return 'gunmetal'
        if n in ('rcv_port_lip','well_lip'):return 'steel'
        if n.startswith(('brake','barrel','sleeve')):return 'barrelsteel'
        if n.startswith(('well_frame','lever','bolt','pin')):return 'steel'
        if n.startswith(('rcv_port',)) and n!='rcv_port_lip':return 'recess'
        if n.startswith(('rcv_','well_lip')):return 'olive'
        if n in ('grip','grip_wrap_l','grip_wrap_r'):return 'cloth'
        if n.startswith(('grip_','st_pad','mag_floor')):return 'rubber'
        if n.startswith('hg'):return 'handguard'
        if n.startswith('st_'):return 'stock'
        if n.startswith('mag'):return 'magazine'
        return 'gunmetal'
    if kind=='ros':
        if n.startswith(('rcv_body_1','rcv_body_2')):return 'frame'
        if n.startswith(('fore_bolt','sight_dial')):return 'steel'
        if n.startswith('drum'):return 'drumsteel'
        if n.startswith(('muz_prong','spike','st_rail','st_upright')):return 'frost'
        if n.startswith(('shroud','nose','rcv_body','rcv_top','rcv_ramp','fore_plate')):return 'shell'
        if n.startswith(('mag',)):return 'magazine'
        if n.startswith(('grip_panel','rib','vent')):return 'polymer'
        if n.startswith('st_pad'):return 'rubber'
        if n.startswith('st_top'):return 'stock'
        if n.startswith(('grip','frame','guard','trigger','rcv_lower','st_lower','st_chin','ejector')):return 'frame'
        return 'gunmetal'
    if kind=='cyd':
        if n.startswith(('guard_','trigger','fore_bolt','rcv_rail')):return 'steel'
        if n.startswith('st_inset'):return 'recess'
        if n.startswith('vent_'):return 'recess'
        if n.startswith(('sup','barrel','tube_nose')):return 'suppressor'
        if n.startswith(('cover','tube','fore_plate','st_block','st_front','st_rear','st_bar')) and not n.startswith(('cover_front_cap','tube_rib')):return 'maroon'
        if n.startswith(('rcv_lower','rcv_upper','mid_rail','side_lever')):return 'frame'
        if n.startswith(('st_pad','grip_panel')):return 'rubber'
        if n.startswith(('grip','frame_','st_inset')):return 'polymer'
        if n.startswith('mag'):return 'magazine'
        if n.startswith('fore_bolt'):return 'steel'
        return 'gunmetal'
    raise ValueError(kind)

class Materials:
    def __init__(self,kind):self.kind=kind;self.palette=palette(kind)
    def __call__(self,n,f):
        key=assign(self.kind,n,f)
        if isinstance(key,dict):return key
        # Narrow chamfers and the long, stretched VEIST suppressors do not have reliable source relief.
        # Material grain remains, but invalid/repeated projection is explicitly disabled.
        if '_ch_' in n or n.endswith(('_d1','_d2','_oct')) or n.startswith(('brake_port','sup_port','sup_tip','sup_rear','grip','fg_','st_chin','rcv_ramp','rcv_top_tail','rail','holo_rail','rear_rail','recv_band','stock_top','rcv_rail')):
            return dict(self.palette[key],detail=0)
        return key

class Decals:
    def __init__(self,kind,model2world,wid,T=20):
        self.kind=kind;self.model2world=model2world;self.T=T;self.views={}
        cache=ROOT/'art/weapons/w325'/wid/'proj_cache';man=json.loads((cache/'manifest.json').read_text())
        for name in ('nx','px','pz','nz'):
            v=kit.View(cache,name,man)
            # Remove single-pixel photographic grit from the camouflage stencil only.
            image=Image.open(cache/f'{name}_albedo.png').convert('RGBA')
            small=image.resize((max(1,image.width//8),max(1,image.height//8)),Image.Resampling.BOX).filter(ImageFilter.MedianFilter(3))
            image=small.resize(image.size,Image.Resampling.NEAREST)
            v.alb=image.load();self.views[name]=v
    def __call__(self,e,fn,s,t):
        n=e['name'];k=self.kind;f=e['from'];g=e['to'];side=fn in ('east','west')
        z=f[2]+(s if fn=='west' else 1-s)*(g[2]-f[2]);y=g[1]-t*(g[1]-f[1])
        if 'reticle' in n:return (70,235,90,255)
        # Original VEIST lettering, read independently on both sides.
        if k in ('sand','yellow') and side and n.startswith('plate_') and '_aft' in n:
            w=max(1,round((g[2]-f[2])*self.T));h=max(1,round((g[1]-f[1])*self.T))
            x=int(s*w)-4;yy=int(t*h)-3
            if 0<=x<20 and 0<=yy<5:
                ci=x//4;xx=x%4
                if xx<3 and GLYPHS['VEIST'[ci]][yy][xx]=='1':return ((161,173,104) if k=='sand' else (168,210,70))+(255,)
        if k in ('sand','yellow') and side and n=='mag_front':
            if any(abs((z-a)/.45+(y-9.98)/.64-1)<.12 for a in (4.75,5.1)):
                return ((163,48,37) if k=='sand' else (149,187,67))+(255,)
        # Two rows of VEIST magazine perforations: sparse dark decal, brass/paint base stays materialised.
        if k in ('sand','yellow') and n=='mag_body' and side:
            dz=(z-5.8)% .24;dy=min(abs(y-10.15),abs(y-10.45))
            if .015<dz<.07 and dy<.035:return (64,64,44,255) if k=='sand' else (76,101,40,255)
        if k=='home' and n in ('grip','grip_wrap_l','grip_wrap_r') and side:
            # Only the narrow selvage is special; the brown wrapping has real woven material grain.
            d=(y-.34*z)% .54
            if d<.045:return (46,31,25,255)
            if .045<=d<.075:return (120,80,52,255)
        if k=='ros' and n.startswith('drum') and side:
            idx=int(n.split('_')[1][1]);cz,cy=((-2.06,10.9),(-3.16,9.72),(-2.06,9.72))[idx]
            dz,dy=z-cz,y-cy;r=math.hypot(dz,dy)
            if .46<r<.50:return (79,111,123,255)
            if abs(dz+dy)<.055 and r<.39:return (34,53,59,255)
            if abs(dz+dy-.09)<.027 and r<.39:return (219,235,238,255)
        if n.startswith('sight_sill') or n in ('sight_base','sight_rear_bezel','sight_tail'):
            if fn in ('north','south') and .4<s<.6 and .25<t<.65:
                return ((225,113,58) if k in ('home','sand','yellow') else (82,194,90))+(255,)
        # R2 hand-authored motifs: one-texel flutes/slots, never a face-sized colour fill.
        if k=='home' and n=='mag_body' and side and 7.75<y<8.8:
            for rib in (2.65,3.6,4.25):
                if abs(z-rib)<.026:return (20,28,27,255)
                if abs(z-rib-.055)<.025:return (99,113,108,255)
        if k=='ros' and n.startswith(('rcv_body_1','rcv_body_2')) and side:
            # The exposed rear action has a continuous seam, not scattered projected grime.
            if 4.05<z<8.4 and abs(y-10.63)<.025:return (68,65,58,255)
            if 5.2<z<6.35 and abs(y-9.84)<.025:return (171,165,149,255)
        if k=='cyd' and n.startswith('mid_rail') and side and -4.1<z<-.1 and 10.25<y<10.82:
            phase=(z+4.0)%.28
            if phase<.047:return (124,139,139,255)
            if .047<=phase<.094:return (16,25,26,255)
        if k=='cyd' and n=='mag_body' and side and 5.6<y<7.8:
            for rib in (2.55,4.1):
                if abs(z-rib)<.026:return (26,35,34,255)
                if abs(z-rib-.055)<.025:return (126,139,133,255)
        # Use the ACTUAL source camouflage pattern as the decal stencil (not the previous repeated block pattern).
        camo=(k in ('sand','yellow') and n.startswith(('recv','stock_main','stock_over','stock_under','stock_chin','front_housing','win_end'))) or (k=='ros' and n.startswith(('shroud','nose','rcv_body','rcv_top','rcv_ramp','fore_plate','st_rail','st_upright','sight_cheek','sight_roof')))
        if camo and fn in ('east','west','up','down') and '_joint_' not in n and (assign(k,n,fn)=='shell' or n.startswith(('sight_cheek','sight_roof'))):
            name={'east':'nx','west':'px','up':'pz','down':'nz'}[fn];v=self.views[name]
            p=kit.face_point(e,fn,s,t);world=self.model2world(n,p);x,Y=v.project(world)
            # Nearest 2px grid makes the mask crisp and prevents sub-texel muddy edges.
            c=v.sample(round(x/2)*2+.5,round(Y/2)*2+.5)
            if c:
                lum=.299*c[0]+.587*c[1]+.114*c[2]
                thresh=108 if k=='sand' else 82 if k=='yellow' else 123
                if lum>thresh:
                    tint=(188,190,166) if k=='sand' else (113,111,113) if k=='yellow' else (187,217,232)
                    return tint+(255,)
        return None
