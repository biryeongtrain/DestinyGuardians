"""W325 W9 material pass: W123-style part surfaces, source-aligned camo, sparse identity decals.
RGB evidence: median-cut samples of each proj_cache nx/px/pz albedo plus visually reviewed rip.
Source relief stays in kit.materialize; new geometry and displaced faces explicitly disable it.
"""
import math,json
from pathlib import Path
from w9 import model_pt,flat
from identity import glyph


def mat(kind,color,detail=.7,**kw):return dict(kind=kind,color=color,detail=detail,**kw)
COMMON={
 'rubber':mat('rubber',(25,28,27),.12,amp=5),
 'polymer':mat('polymer',(43,46,43),.25,amp=3),
 'steel':mat('steel',(127,135,135),.55,amp=6),
 'dark':mat('dark',(16,19,20),0,amp=1),
 'lens':mat('lens',(32,66,84),0),
 'cyan':mat('glow',(70,155,190),0),
 'redlight':mat('glow',(155,34,30),0),
 'greenlight':mat('glow',(72,181,95),0),
}
MATERIALS={
 'requiem_43':dict(COMMON,mint=mat('paint',(134,156,151),.85),red=mat('paint',(139,40,40),.65),
  white=mat('steel',(183,190,186),.4,amp=4),gunmetal=mat('metal',(67,65,64),.65),polymer=mat('polymer',(52,49,47),.3)),
 'aachen_lr2':dict(COMMON,bone=mat('paint',(190,184,173),.75),olive=mat('paint',(64,75,49),.55),
  gunmetal=mat('steel',(62,66,60),.65,amp=5),polymer=mat('polymer',(46,48,41),.3),steel=mat('steel',(145,151,141),.6)),
 'damietta_lr2':dict(COMMON,ice=mat('paint',(171,201,217),.8),teal=mat('paint',(65,88,95),.6),
  brown=mat('polymer',(89,80,71),.4),brownmetal=mat('metal',(89,82,74),.65,amp=6),
  gunmetal=mat('steel',(58,57,54),.7,amp=5),steel=mat('steel',(179,187,187),.4)),
 'tongeren_lr3':dict(COMMON,maroon=mat('paint',(103,62,56),.9),bone=mat('paint',(165,150,129),.85),
  gunmetal=mat('metal',(63,65,61),.8,amp=5),polymer=mat('polymer',(44,47,43),.3)),
 'nox_cordis_ii':dict(COMMON,navy=mat('paint',(49,58,75),.8),white=mat('paint',(193,196,193),.6),
  pink=mat('metal',(201,184,179),.5,amp=4),gunmetal=mat('steel',(82,88,94),.7),polymer=mat('polymer',(35,38,40),.25)),
 'nox_lumen_ii':dict(COMMON,gunmetal=mat('metal',(83,79,73),.95,amp=6),white=mat('steel',(183,188,187),.55,amp=4),
  paint=mat('paint',(75,70,65),.8),polymer=mat('polymer',(42,39,35),.35),steel=mat('steel',(113,111,104),.55)),
 'parsec_tsu':dict(COMMON,white=mat('paint',(195,208,202),.85),mint=mat('paint',(164,186,173),.55),
  gunmetal=mat('metal',(60,72,64),.8),polymer=mat('polymer',(34,42,37),.3),orange=mat('paint',(183,99,41),.4)),
}

# Ordered prefix assignments: specific materials before broad family fallbacks.
RULES={
 'requiem_43':[
  (('muzzle_bore',),'dark'),(('grip_insert','grip_heel','butt_pad','id_butt'),'rubber'),
  (('stock_side',),'mint'),(('grip','wrist','guard','trigger','stock_block'),'polymer'),
  (('rsight_bead',),'redlight'),(('stock_comb',),'red'),
  (('muzzle_frame','muzzle_lug','fore_grip','stock_tube','port_lip','shroud_front_lip','id_port'),'white'),
  (('barrel','id_barrel','recv_window','recv_rear','recv_tail','stock_collar','port_','recv_button','recv_pin','rsight_hump'),'gunmetal'),
  (('shroud','recv_upper'),'mint')],
 'aachen_lr2':[
  (('sc_eyecup','stock_cheek','stock_butt','butt_','stock_grip'),'rubber'),
  (('laser_lens',),'redlight'),(('bolt_knob','recv_bolt_rod','id_scope_ring'),'steel'),
  (('hg_vent',),'dark'),(('mag_body','mag_id','mag_rib','magwell','lower_box','stock_lower','stock_rear','stock_heel','recv_tail','laser'),'polymer'),
  (('brake','barrel','sc_mount','sc_turret','guard','trigger','bolt_lever','recv_bolt','hg_lower','hg_rail','id_hg'),'gunmetal'),
  (('hg_upper','hg_rod','front_block','recv_front','recv_top','recv_rear','recv_sill','sc_obj','sc_visor','sc_mid','sc_tube','sc_ocular','stock_top','mag_plate'),'bone')],
 'damietta_lr2':[
  (('sc_eyepiece','stock_grip','butt_pad'),'rubber'),(('fold_hole','mag_window'),'dark'),
  (('bolt_knob','recv_pin'),'steel'),(('stock_upper','stock_lower','recv_tail','mag_body','mag_id','guard','trigger'),'brown'),
  (('brake_band','barrel_collar','fold_','bip_','bolt_lever','sc_ring','sc_turret','id_scope','mount_base'),'brownmetal'),
  (('hg_core','hg_floor','recv_port','top_cover'),'gunmetal'),
  (('brake','id_brake','barrel','hg_rail','hg_post','hg_truss','recv_upper','recv_spine','recv_front','recv_sill','recv_rear','stock_pad','stock_butt','sc_obj','sc_body','mag_floor'),'ice')],
 'tongeren_lr3':[
  (('butt_plate','stock_grip','scope_hood'),'rubber'),(('id_hex','stock_lower','stock_neck'),'polymer'),
  (('shroud_slot','recv_port'),'dark'),
  (('sight_band','collar','barrel_tip','stock_butt','stock_upper','mag_body','mag_lip','guard_loop','bolt_knob','scope_turret','plate_inset','id_shroud'),'bone'),
  (('shroud_top','shroud_bot','shroud_end','shroud_ramp','shroud_raise','recv_upper','scope_obj','scope_body'),'maroon'),
  (('barrel','shroud_wall','shroud_strip','skid','hinge','core','plate','recv_rail','recv_mid','recv_lower','bolt_lever','guard','trigger','scope_mount'),'gunmetal')],
 'nox_cordis_ii':[
  (('grip','butt','stock_butt'),'rubber'),(('shroud_rib','shroud_panel','frame_window','mag_cell','id_chevron'),'dark'),
  (('belly_light',),'greenlight'),(('cage_bolt','recv_pin','id_cell','mag_id'),'steel'),
  (('muzzle','rail','stock_strut','frame_strip','sight_base'),'pink'),
  (('cage_post','trigger','guard','lower_band','frame','stock','sight_ear','mag_latch'),'polymer'),
  (('recv_grille','recv_logo'),'white'),(('shroud','recv_front','recv_rear','cage_top','cage_low','barrel_core','mag_upper','mag_lower'),'navy')],
 'nox_lumen_ii':[
  (('grip','butt','stock_strut'),'rubber'),(('recv_slot','mag_win','recv_rear_win','mech_bolt'),'dark'),
  (('muzzle_nub_ring','cap','rail_white','arm_white','mag_rail','canister','shroud_line'),'white'),
  (('recv_grille',),'white'),(('id_vent','id_canister'),'steel'),
  (('trigger','sight','muzzle_nub','shroud_low_cell','mag_id'),'polymer'),
  (('mech','stock_tube','stock_butt','mag_block','mag_nose','mag_belly','mag_tail'),'paint'),
  (('shroud','recv','id_top'),'gunmetal')],
 'parsec_tsu':[
  (('grip','stock_post'),'rubber'),(('face_vent','stock_tube_slot','mag_slot','bore_rod'),'dark'),
  (('mag_stripe',),'orange'),(('recv_disc','recv_vents','id_recv'),'gunmetal'),
  (('face_plate','under_lip','under_step','recv_rear_band','guard_bar','trigger','frame_strip','sight_ear','side_box'),'polymer'),
  (('shroud_strip','shroud_square','shroud_window','id_window','mag_id'),'mint'),
  (('shroud','bumper','rail','recv','sight_base','frame','stock','mag_main','mag_tail'),'white')],
}
DEFAULT=dict(zip(MATERIALS,['mint','bone','ice','gunmetal','navy','gunmetal','white']))

def choose(wid,name,face):
 key=next((m for names,m in RULES[wid] if name.startswith(names)),DEFAULT[wid])
 if wid=='nox_cordis_ii' and name=='shroud':key='dark'
 m=dict(MATERIALS[wid][key])
 # Identity additions have no exact corresponding projection surface; synthetic material only.
 if name.startswith(('id_','mag_id_')) or face in ('north','south') or (face in ('up','down') and ('grip' in name or 'stock' in name)):
  m['detail']=0
 if wid=='nox_lumen_ii' and name.startswith('recv_grille'):m['detail']=.4
 return m

_MAP={};_CACHE={}
def register(wid,mapfn):_MAP[wid]=mapfn

def source(wid,e,fn,s,t):
 import kit
 if wid not in _CACHE:
  path=kit.art(wid)/'proj_cache';man=json.loads((path/'manifest.json').read_text());_CACHE[wid]={k:kit.View(path,k,man) for k in man['views']}
  # Source-aligned large pigment masses: smooth tiny wear, then snap the mask field to 12-pixel blocks.
  from PIL import Image, ImageFilter
  for view in _CACHE[wid].values():
   im=Image.open(path/(next(k for k,v in _CACHE[wid].items() if v is view)+'_albedo.png')).convert('RGBA')
   im=im.filter(ImageFilter.GaussianBlur(8)).resize((max(1,view.W//12),max(1,view.H//12)),Image.Resampling.BOX).resize((view.W,view.H),Image.Resampling.NEAREST)
   view._pigment_image=im;view.alb=im.load()
 p=kit.face_point(e,fn,s,t);n=kit.rotate_vec(kit.NORMALS[fn],kit.rot_of(e));mp=_MAP[wid]
 a=mp(e['name'],p);b=mp(e['name'],tuple(p[k]+n[k]*.25 for k in range(3)));wn=[b[k]-a[k] for k in range(3)];k=max(range(3),key=lambda k:abs(wn[k]))
 v=_CACHE[wid][('p' if wn[k]>0 else 'n')+'xyz'[k]];u,vv=v.project(a);return v.sample(u,vv)

CAMO={
 'aachen_lr2':('hg_upper','hg_rod','front_block','recv_front','recv_top','recv_rear','recv_sill','sc_obj','sc_mid','sc_ocular','stock_top','mag_plate'),
 'damietta_lr2':('brake','barrel','hg_rail','hg_post','hg_truss','recv_upper','recv_front','recv_sill','recv_rear','stock_pad','stock_butt','sc_obj','sc_body','mag_floor'),
 'nox_cordis_ii':('shroud','recv_front','recv_rear','cage_top','cage_low','barrel_core','mag_upper','mag_lower'),
 'parsec_tsu':('shroud','bumper','rail','recv','frame_front','stock_tube','stock_butt','stock_wedge','mag_main','mag_tail'),
}

def decal(wid,e,fn,s,t):
 n=e['name'];x,y,z=model_pt(e,fn,s,t);side=fn in ('west','east')
 # Exact-rip pigment masks replace the former generic noise blobs. At least one base colour stays material-baked.
 if choose(wid,n,fn)['kind']=='paint' and not (wid=='nox_cordis_ii' and n=='shroud') and wid in CAMO and n.startswith(CAMO[wid]) and fn in ('east','west','up') and not n.startswith(('shroud_panel','shroud_rib','recv_grille','recv_disc','recv_vents','shroud_strip','shroud_window')):
  q=source(wid,e,fn,s,t)
  if q:
   r,g,b=q[:3];lum=.299*r+.587*g+.114*b;target=None
   if wid=='aachen_lr2' and lum<122 and g>=r*.96 and g>b*1.04:target=(65,77,48) if lum<85 else (114,119,89)
   if wid=='damietta_lr2' and lum<140 and b>r*1.04:target=(64,88,96) if lum<100 else (126,160,175)
   if wid=='nox_cordis_ii' and lum>121:target=(194,199,196)
   if wid=='parsec_tsu' and 83<lum<182 and g>r*1.015:target=(173,190,178)
   if target:
    # Restrained source relief and paint grain on camo pigment; never flat-fill the whole face.
    shade=.98+(lum%17-8)*.002+(int(s*379+t*193)%7-3)*.002
    return tuple(max(0,min(255,round(c*shade))) for c in target)+(255,)
 # Bore / emitter accent occupies only the front centre; surrounding metal remains baked.
 if fn=='north' and n in ('brake_crown','brake_tip','barrel_tip','muzzle_nub','muzzle_tip','bore_rod'):
  r=((s-.5)/.28)**2+((t-.5)/.28)**2
  if r<1:
   if wid=='nox_cordis_ii' and n=='muzzle_tip':return (70,155,190,255) if r<.65 else (24,42,51,255)
   return (12,17,18,255)
 # Lens area and highlight are small identity accents, exterior housing remains material-baked.
 lens_names=('sc_obj','sc_eyecup','sc_eyepiece','scope_obj','scope_hood')
 if n in lens_names and fn in ('north','south'):
  d=((s-.5)/.39)**2+((t-.5)/.39)**2
  if d<1:
   if d>.79:return (15,25,29,255)
   q=1-.24*d;col=tuple(round(k*q) for k in (38,79,103))
   if (.30<s<.35 and .3<t<.59) or (.30<s<.55 and .30<t<.35):col=(137,191,209)
   return col+(255,)
 if wid=='requiem_43':
  if n.startswith('shroud'):
   q=z-(y-10.8)*.87
   if y<10.99 or -.75<q<-.4 or .05<q<.4:return (139,39,39,255)
  if n=='recv_upper' and side and 11.54<y<11.94:
   zz=4.65-z if fn=='east' else z-1.7
   if glyph('SUROS',zz/.13,(11.94-y)/.07):return (219,232,225,255)
  if n.startswith('stock_comb') and side and y<11.45-max(0,z-13.0)*.35:return (134,156,151,255)
 elif wid=='aachen_lr2':
  if n.startswith('hg_upper') and side and -9.4<z<-5.0 and 9.77<y<10.11 and (z+(y-9.77)*.9)%.34<.11:return (24,29,24,255)
 elif wid=='tongeren_lr3':
  if n.startswith('id_hex') and side:
   qx=abs(s-.5);qy=abs(t-.5);d=max(qx/.43,(qy+qx*.5)/.43)
   if .70<d<.88:return (22,26,23,255)
 elif wid=='nox_cordis_ii':
  if n.startswith('id_chevron') and side:
   a=abs(t-.5)*.65;u=s if fn=='east' else 1-s
   if min(abs(u-(.73-a)),abs(u-(.46-a)))<.055:return (205,216,212,255)
  if n=='recv_logo_plate' and side and ((.45<s<.65 and .2<t<.8) or (.2<s<.65 and .2<t<.35)):return (49,58,75,255)
  if n=='belly_light' and side and .2<s<.75 and .2<t<.45:return (156,245,169,255)
 elif wid=='parsec_tsu':
  if n.startswith('shroud_window') and side and .51<s<.73 and .38<t<.68:return (21,28,24,255)
  if n=='shroud' and side and -6.8<z<-3.3 and 12.0<y<12.55 and z>-6.8+(y-12.0)*.7:return (169,190,179,255)
 return None


# Material r2: only the external factory-coated shells keep paint; exposed mechanisms use alloys.
# Luma separation is deliberately >=25 between adjacent rubber/polymer/metal families.
for _wid,_m in MATERIALS.items():
 _m['rubber']=mat('rubber',(18,21,20),.10,amp=3,plate=False)
 if 'polymer' in _m:_m['polymer']=mat('polymer',(55,59,56),.25,amp=3)
 _m['machined']=mat('steel',(112,119,116),.45,amp=5)
 if 'gunmetal' in _m:_m['gunmetal']=mat('metal',(86,90,86),.65,amp=5)
for _wid,_key in [('aachen_lr2','bone'),('damietta_lr2','ice'),('nox_cordis_ii','navy'),('parsec_tsu','white'),('parsec_tsu','mint')]:
 MATERIALS[_wid][_key]['wear']=False
MATERIALS['requiem_43']['mint']['wear']=(84,103,96)
MATERIALS['requiem_43']['red']['wear']=(76,72,66)
MATERIALS['tongeren_lr3']['maroon']['wear']=(161,148,127)
MATERIALS['tongeren_lr3']['bone']['wear']=(89,85,74)
MATERIALS['damietta_lr2']['brownmetal']=mat('metal',(118,108,96),.55,amp=5)
MATERIALS['damietta_lr2']['barrelsteel']=mat('steel',(141,158,166),.4,amp=5)
MATERIALS['parsec_tsu']['barewhite']=mat('steel',(157,174,164),.45,amp=4)
MATERIALS['tongeren_lr3']['alloy']=mat('steel',(140,134,120),.45,amp=5)

EXPOSED={
 'requiem_43':[(('recv_pin','recv_button','id_port'),'machined'),(('guard','trigger','barrel_rib'),'gunmetal')],
 'aachen_lr2':[(('recv_front','recv_top','recv_sill','recv_rear','lower_box','magwell','mag_body','mag_rib','mag_id'),'gunmetal'),(('bolt_','recv_bolt','id_scope_ring'),'machined')],
 'damietta_lr2':[(('barrel',),'barrelsteel'),(('hg_rail','hg_post','hg_truss','recv_sill','recv_rear','guard','trigger'),'machined'),(('mag_body','mag_id'),'brownmetal')],
 'tongeren_lr3':[(('collar','barrel_tip','sight_band','mag_body','mag_lip','guard_loop','bolt_knob','scope_turret'),'alloy')],
 'nox_cordis_ii':[(('barrel_core','cage_post','trigger','guard','mag_latch'),'gunmetal'),(('recv_grille','recv_logo','recv_pin','cage_bolt'),'machined')],
 'nox_lumen_ii':[(('mech','stock_tube','stock_butt','mag_block','mag_tail'),'gunmetal'),(('trigger','sight_base','mag_latch'),'machined')],
 'parsec_tsu':[(('recv_rear_band',),'gunmetal'),(('recv_disc','recv_vents'),'machined'),(('recv','frame_front','frame_pin','rail','bumper'),'barewhite'),(('guard_bar','trigger','side_box'),'gunmetal')],
}
_base_choose=choose
def choose(wid,name,face):
 key=next((key for prefixes,key in EXPOSED[wid] if name.startswith(prefixes)),None)
 if key is None:return _base_choose(wid,name,face)
 m=dict(MATERIALS[wid][key])
 if name.startswith(('id_','mag_id_')) or face in ('north','south'):m['detail']=0
 return m

_base_decal=decal
def decal(wid,e,fn,s,t):
 import kit
 n=e['name'];o,u,v=kit.face_frame(e,fn)
 w=max(1,round(math.dist((0,0,0),u)*20));h=max(1,round(math.dist((0,0,0),v)*20));ix=int(s*w);iy=int(t*h)
 side=fn in ('east','west')
 # One-texel handmade motifs, applied before the sparse pigment masks.
 if wid=='aachen_lr2' and n=='mag_body' and side and 4<iy<h-5:
  if any(abs(ix-int(w*q))<1 for q in (.22,.5,.78)):return (40,47,42,255)
 if wid=='damietta_lr2' and n.startswith('sc_turret') and side and iy in (2,3) and ix%5==0:return (192,199,192,255)
 if wid=='tongeren_lr3' and n=='mag_body' and side and iy in (3,h-4) and 3<ix<w-4:return (80,78,68,255)
 if wid=='nox_lumen_ii' and n.startswith('recv_grille') and side and 2<ix<w-3 and 2<iy<h-3:
  if ix%4==0 or iy%4==0:return (72,81,76,255)
 if wid=='parsec_tsu' and n=='mag_main' and side:
  a,b,c,d=int(w*.15),int(w*.37),int(h*.18),int(h*.83)
  if ((ix in (a,b) and c<=iy<=d) or (iy in (c,d) and a<=ix<=b)):return (99,121,107,255)
 return _base_decal(wid,e,fn,s,t)
