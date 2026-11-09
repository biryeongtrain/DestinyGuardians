#!/usr/bin/env python3
"""W327 group 1 authored weapon volumes. Read-only .blend references; no ripped mesh conversion.
Run in a Python environment with Pillow: group1.py [build|render|check|all] [ID|all].
Source cache is temporary /tmp/w327-cache. Source evaluation and geometry notes accompany each design.
"""
import importlib.util, json, math, sys, shutil, contextlib, io, hashlib, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('w325kit',ROOT/'scripts/art/w325/kit.py');kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.ROOT=ROOT;kit.ASSETS=ROOT/'src/main/resources/assets/destiny';kit.REG=Path('/tmp/destiny-perks-20261106/candidates/final-registry.json');kit.RIPS=Path('/tmp/destiny-perks-20261106/rips')
kit.art=lambda w:ROOT/'art/weapons/w327'/w
kit.atlas_path=lambda w:kit.ASSETS/f'textures/item/weapon/w327/{w}.png'
kit.hud_path=lambda w:kit.ASSETS/f'textures/item/hud/w327/ammo_{w}.png'
SOURCE_EVALUATOR="import bpy,json,sys,mathutils,os,hashlib\nwid,out=sys.argv[sys.argv.index('--')+1:];os.makedirs(out,exist_ok=True)\nsc=bpy.context.scene\nsc.render.use_compositing=False\nsc.render.use_sequencer=False\ndef unexclude(lc):\n lc.exclude=False;lc.hide_viewport=False\n for x in lc.children:unexclude(x)\nunexclude(bpy.context.view_layer.layer_collection)\nfor c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False\nmeshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('Plane')]\npts=[o.matrix_world@mathutils.Vector(c) for o in meshes for c in o.bound_box]\nlo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]\ndata={'blend':bpy.data.filepath,'sha256':hashlib.sha256(open(bpy.data.filepath,'rb').read()).hexdigest(),'lo':lo,'hi':hi,'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'materials':[m.name for m in o.data.materials if m]} for o in meshes],'armatures':[{'name':o.name,'bones':[{'name':b.name,'head':list(o.matrix_world@b.head_local),'tail':list(o.matrix_world@b.tail_local)} for b in o.data.bones]} for o in bpy.data.objects if o.type=='ARMATURE'],'actions':[{'name':a.name,'range':list(a.frame_range),'slots':[s.identifier for s in a.slots]} for a in bpy.data.actions],'images':[{'name':i.name,'path':i.filepath,'size':list(i.size)} for i in bpy.data.images]}\njson.dump(data,open(out+'/source-evaluation.json','w'),indent=2)\nfor o in bpy.data.objects:\n if o not in meshes:o.hide_render=True\nfor o in meshes:o.hide_render=False;o.hide_set(False)\nsc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True\nsc.render.resolution_x=1200;sc.render.resolution_y=700;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'\nsc.world.color=(.18,.18,.18);sc.render.film_transparent=False\ncam=bpy.data.cameras.new('W327_owned_camera');cam.type='ORTHO';co=bpy.data.objects.new('W327_owned_camera',cam);sc.collection.objects.link(co);sc.camera=co\nc=mathutils.Vector([(lo[i]+hi[i])/2 for i in range(3)]);ext=max(hi[i]-lo[i] for i in range(3))*1.15\nfor name,vec in [('side',(0,1,0) if wid=='phyllotactic_spiral' else (1,0,0)),('oblique',(.65,1,.45) if wid=='phyllotactic_spiral' else (1,-.65,.45)),('top',(0,0,1))]:\n d=mathutils.Vector(vec).normalized();co.location=c+d*max(ext*3,3);co.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.ortho_scale=ext;cam.clip_end=1000;sc.render.filepath=out+'/source_'+name+'.png';bpy.ops.render.render(write_still=True)\n"
IDS=['krait','rufuss_fury','origin_story','age_old_bond','insidious','phyllotactic_spiral','igneous_hammer','eyasluna','nation_of_beasts','subjunctive','submission','hung_jury_sr4']

class Shape:
 def __init__(self):self.e=[];self.roles={}
 def box(self,n,x0,x1,y0,y1,z0,z1,m='shell'):
  assert x1>x0 and y1>y0 and z1>z0,(n,x0,x1,y0,y1,z0,z1)
  self.e.append(dict(name=n,**{'from':[x0,y0,z0],'to':[x1,y1,z1]}));self.roles[n]=m
 def block(self,n,w,y0,y1,z0,z1,m='shell',bevel=.14):
  """Three adjoining rectangular bands make a solid chamfered cross section; no overlapping plates."""
  w/=2;b=min(bevel,w*.4,(y1-y0)*.25)
  self.box(n+'_core',8-w+b,8+w-b,y0,y1,z0,z1,m)
  self.box(n+'_left',8-w,8-w+b,y0+b,y1-b,z0,z1,m)
  self.box(n+'_right',8+w-b,8+w,y0+b,y1-b,z0,z1,m)
 def tube(self,n,w,h,y,z0,z1,m='steel',wall=.18):
  # Eight adjoining orthogonal blocks: square inner bore with stepped outer corners.
  xl,xr,yb,yt=8-w/2,8+w/2,y-h/2,y+h/2
  self.box(n+'_top',xl+wall,xr-wall,yt-wall,yt,z0,z1,m)
  self.box(n+'_bottom',xl+wall,xr-wall,yb,yb+wall,z0,z1,m)
  self.box(n+'_left',xl,xl+wall,yb+wall,yt-wall,z0,z1,m)
  self.box(n+'_right',xr-wall,xr,yb+wall,yt-wall,z0,z1,m)
  d=wall*.38
  self.box(n+'_tl',xl+d,xl+wall,yt-wall,yt-d,z0,z1,m)
  self.box(n+'_tr',xr-wall,xr-d,yt-wall,yt-d,z0,z1,m)
  self.box(n+'_bl',xl+d,xl+wall,yb+d,yb+wall,z0,z1,m)
  self.box(n+'_br',xr-wall,xr-d,yb+d,yb+wall,z0,z1,m)
 def grip(self,n,z0,y0,w=1.25,height=3.2,back=.95,m='rubber'):
  # Stepped, adjoining grip lobes preserve finger scallops without oblique slab overlaps.
  for i in range(6):
   yy=y0+i*height/6;zz=z0-back*i/6
   self.block(n+str(i),w,yy,yy+height/6,zz,zz+1.25,m,.12)
  self.block(n+'_root',w+.08,y0+height-.08,y0+height+.22,z0-back*.84-.18,z0-back*.84+1.35,m,.12)
 def panel(self,n,xside,y0,y1,z0,z1,m='accent',depth=.12):
  for side in [-1,1]:
   x0=8+side*(xside-.025)
   self.box(n+('_l' if side<0 else '_r'),x0-depth if side<0 else x0,x0 if side<0 else x0+depth,y0,y1,z0,z1,m)
 def stair(self,n,stations,w,m='shell'):
  # stations: z0,z1,bottom,top; varying cross sections are meaningful silhouette blocks.
  prev=None
  for i,(z0,z1,y0,y1) in enumerate(stations):
   if prev is not None:
    if y0>=prev[1]-.10:y0=prev[1]-.20
    elif y1<=prev[0]+.10:y1=prev[0]+.20
   self.block(n+str(i),w,y0,y1,z0,z1,m);prev=(y0,y1)
 def guard(self,z0,z1,y0,y1):
  self.box('trigger_guard_front',7.82,8.18,y0,y1,z0,z0+.22,'steel')
  self.box('trigger_guard_floor',7.82,8.18,y0,y0+.22,z0+.22,z1,'steel')
  self.box('trigger',7.90,8.10,y1-.65,y1,z1-.5,z1-.28,'black_steel')
 def sight(self,z,y,width=.9,height=.75):
  self.box('sight_saddle',7.55,8.45,y-.2,y,z-.3,z+.6,'black_steel')
  self.box('sight_left',8-width/2,8-width/2+.12,y,y+height,z,z+.25,'steel')
  self.box('sight_right',8+width/2-.12,8+width/2,y,y+height,z,z+.25,'steel')
 def mag(self,z0,z1,y0,y1,w=1.1,m='steel'):
  mid=y0+(y1-y0)*.55
  self.block('mag_upper',w,mid,y1,z0,z1,m)
  self.block('mag_lower',w,y0+.22,mid,z0,z1,m)
  self.block('mag_floor',w+.16,y0,y0+.22,z0-.08,z1+.08,'black_steel')
 def fins(self,n,zs,y0,y1,w,m='steel'):
  for i,z in enumerate(zs):self.box(n+str(i),8-w/2,8+w/2,y0,y1,z,z+.16,m)

COMMON={'black_steel':dict(kind='metal',color=[39,44,46],detail=.25,wear=False),'steel':dict(kind='steel',color=[107,117,120],detail=.35,wear=False),'rubber':dict(kind='rubber',color=[30,34,34],detail=.0,wear=False),'recess':dict(kind='dark',color=[13,17,20],detail=0,wear=False),'shell':dict(kind='paint',color=[72,78,79],detail=.35,wear=False),'accent':dict(kind='paint',color=[190,199,72],detail=.0,wear=False),'trim':dict(kind='steel',color=[175,182,178],detail=.15,wear=False),'lens':dict(kind='lens',color=[88,183,196],detail=0,wear=False)}
PALETTES={
 'krait':{'shell':(55,62,58),'accent':(181,203,43),'steel':(90,99,91)},
 'rufuss_fury':{'shell':(58,63,74),'accent':(84,111,155),'trim':(134,149,175)},
 'origin_story':{'shell':(68,88,111),'accent':(208,111,50),'trim':(187,196,199)},
 'age_old_bond':{'shell':(211,201,165),'accent':(166,139,71),'steel':(76,76,79),'trim':(235,220,178)},
 'insidious':{'shell':(63,63,65),'accent':(176,70,50),'trim':(123,119,115)},
 'phyllotactic_spiral':{'shell':(170,173,165),'accent':(83,152,150),'steel':(93,100,101),'trim':(213,215,197)},
 'igneous_hammer':{'shell':(74,72,72),'accent':(199,160,76),'trim':(159,122,61),'rubber':(70,65,47)},
 'eyasluna':{'shell':(155,47,50),'accent':(207,71,61),'trim':(159,161,158),'steel':(91,94,94)},
 'nation_of_beasts':{'shell':(213,201,162),'accent':(175,143,65),'trim':(235,223,186),'steel':(74,75,75)},
 'subjunctive':{'shell':(87,107,106),'accent':(87,100,44),'trim':(143,153,125),'steel':(89,111,110),'lens':(108,210,217)},
 'submission':{'shell':(72,69,68),'accent':(171,69,46),'trim':(136,135,127)},
 'hung_jury_sr4':{'shell':(217,221,214),'accent':(70,114,115),'trim':(174,188,182),'steel':(81,91,95)}
}
NOTES={
 'krait':'VEIST: long suppressor, perforated forward grip, rising rear stock and green side charge bar. Source has no animation actions. The actual VEIST side-loading magazine is the moving assembly; steelfeather motion is approximate reused transport, not a source-authentic reload.',
 'rufuss_fury':'Root of Nightmares: dark organic barrel shroud, asymmetric horn lobes, blue receiver membrane, exposed skeleton stock and rectangular forward magazine. Lobes are adjoining block stations.',
 'origin_story':'Vanguard: blue rectangular receiver, orange chevrons, white stripe, short slotted handguard and skeleton pistol frame. Preserve actual through-slot and conventional magazine.',
 'age_old_bond':'Last Wish: ivory long nose, carved band, dark inner mechanism, triangular open stock. Rip shader has diagnostic-colored unpainted pieces; reconstructed dark metal roles do not reproduce those artifacts.',
 'insidious':'Vow: swept upper spine, front fin bank, long curved lower cable, open grip/stock void, red receiver insert and rear removable magazine.',
 'phyllotactic_spiral':'Neomuna: long pale receiver/shroud, teal blocks, central optic, pistol grip and rear magazine. Source axis differs: long axis X; source decorative plane excluded from geometry bounds.',
 'igneous_hammer':'Trials: broad flared upper barrel, gold sun motif, separated large cylinder, wrapped grip and open trigger guard. Source action absent; duke cylinder transport reused.',
 'eyasluna':'Red heavy barrel, dark fluted cylinder, secondary underbarrel mechanism and curved black grip. Actual source has no animation actions; austringer moving cylinder transport reused.',
 'nation_of_beasts':'Last Wish: ivory tapered swept barrel and grip, carved gold contours, dark cylinder visible between bridges. Source diagnostic shader areas replaced by intentional dark steel.',
 'subjunctive':'V2 source-led redesign: dense Vex tube chambers, broad triangular stock/forebrace, compact narrow magazine, stepped circular luminous cell and three irregular leaf clusters. Solid leaves have connected stems and drooping lobes, never repeated green bands or alpha slabs.',
 'submission':'Vow: short fin bank, stepped muzzle chin, red insert, tall central magazine/grip and sweeping rear cable. Front/rear silhouette differs from Insidious despite shared visual language.',
 'hung_jury_sr4':'Omolon: broad ivory housing, black curved graphics, visible circular fluid cell, rear thumbhole stock and turquoise grip. Moving Omolon fluid magazine retains the forward source position; distant_relation transport is an approximate reuse; source rig has no actions.'
}

def krait():
 s=Shape()
 s.tube('suppressor',1.05,1.05,10.9,-9.5,-5.2,'black_steel',.22)
 s.block('suppressor_rear',1.3,10.25,11.55,-5.2,-4.7,'steel')
 s.tube('inner_barrel',.65,.65,10.9,-4.7,-3.4,'black_steel',.12)
 s.tube('barrel_collar',1.05,1.05,10.9,-4.45,-3.4,'steel',.18)
 s.stair('receiver',[(-3.4,-.6,9.6,12.22),(-.6,3.9,9.65,12.35),(3.9,7.8,9.95,12.25)],1.72)
 s.stair('stock',[(7.8,9.4,10.35,12.1),(9.4,10.4,10.25,12.2),(10.4,11.5,9.2,12.3),(11.5,12.5,9.4,12.4),(12.5,13.5,9.55,12.5),(13.5,14.5,9.7,12.6),(14.5,15.2,9.8,12.65)],1.55)
 s.block('butt_rim',1.8,9.5,12.6,15.2,15.65,'rubber')
 s.stair('front_upper',[(-5.0,-3.4,12.0,12.35),(-3.4,-1.5,12.22,12.45)],1.25)
 s.block('front_grip_bridge',1.45,9.05,9.6,-4.3,.0,'black_steel')
 # Forward-grip opening is bounded by four physical pieces and visible from both sides.
 s.box('forward_hole_front',7.5,8.5,8.25,9.05,-3.8,-3.4,'black_steel')
 s.box('forward_hole_rear',7.5,8.5,8.25,9.05,-2.35,-1.95,'black_steel')
 s.box('forward_hole_floor',7.5,8.5,8.05,8.25,-3.4,-1.95,'black_steel')
 s.grip('front_grip',-.8,6.85,1.1,2.2,.9)
 s.grip('pistol_grip',9.2,6.75,1.25,3.8,1.1)
 s.guard(5.1,7.6,8.6,9.95)
 s.panel('mag_charge_bar',.88,10.72,11.1,-.1,7.4,'accent',.10)
 s.panel('mag_charge_end',.88,10.63,11.2,-1.3,-.1,'steel',.10)
 s.panel('lower_panel',.86,9.85,10.1,-3.3,1.3,'steel',.06)
 s.block('optic_foot',.65,12.2,12.52,4.6,5.6,'black_steel')
 s.sight(4.97,12.7,.72,.56)
 s.stair('top_fin',[(.0,.6,12.35,12.60),(.6,1.2,12.35,12.60),(1.2,2.1,12.35,12.55)],.65,'black_steel')
 s.fins('barrel_flange',[-4.65,-4.38],10.2,11.6,1.35,'black_steel')
 return s

def rufuss_fury():
 s=Shape()
 s.tube('inner_bore',.9,.9,10.95,-9.5,-4.2,'black_steel',.18)
 for i,(z0,z1,y0,y1,w) in enumerate([(-9.1,-8.2,10.2,11.6,1.25),(-8.2,-6.9,10.0,11.95,1.7),(-6.9,-5.4,9.8,12.1,1.95),(-5.4,-3.9,9.7,12.25,2.2),(-3.9,-2.1,9.5,12.35,2.35),(-2.1,-.5,9.65,12.3,2.1),(-.5,1.1,9.8,12.35,1.95),(1.1,2.7,9.9,12.5,2.4),(2.7,4.5,10.0,12.5,2.6),(4.5,5.7,9.9,12.55,2.3),(5.7,7.2,10.1,12.45,1.9)]):s.block('organic_forebody'+str(i),w,y0,y1,z0,z1)
 for side in [-1,1]:
  for i,(z0,z1,y0,y1) in enumerate([(-9.8,-9.1,10.1,10.45),(-9.65,-8.8,11.2,11.55),(-7.6,-6.6,11.6,11.95),(-3.3,-1.8,9.48,9.85),(3.5,5.1,12.3,12.65),(5.1,6.8,9.8,10.15)]):
   x=8+side*.98;s.box('organic_lobe'+str(side)+'_'+str(i),x-.23,x+.23,y0,y1,z0,z1,'shell' if i<3 else 'accent')
 s.panel('blue_receiver_front',1.31,10.15,12.3,2.72,4.48,'accent',.08)
 s.panel('blue_receiver_middle',1.16,10.05,12.4,4.52,5.68,'accent',.08)
 s.panel('blue_receiver_rear',.96,10.25,12.3,5.7,7.1,'accent',.08)
 s.block('stock_spine',1.15,11.15,11.75,7.2,14.8,'accent')
 s.block('stock_underbeam',.85,9.85,10.2,10,14.8,'steel')
 s.block('butt',1.35,9.7,12.2,14.8,15.35,'rubber')
 s.block('grip_neck',1.25,9.945,11.2,7.0,8.4,'accent')
 s.grip('grip',8.85,6.8,1.3,3.4,1.25)
 s.guard(4.8,7.7,8.6,10.2)
 s.mag(2.1,4.65,6.2,9.85,1.15)
 s.sight(5.0,12.7,.72,.56)
 for i,z in enumerate([-4.7,-3.5,4.9]):
  s.panel('organic_recess'+str(i),1.25 if i==2 else 1.18,10.75,11.25,z,z+.5,'recess',.04)
 s.fins('stock_teeth',[10,10.6,11.2],11.75,11.93,1.15,'steel')
 return s

def origin_story():
 s=Shape();s.tube('muzzle',1.0,1.05,11.2,-9.0,-7.6,'black_steel',.2)
 s.block('barrel_jacket',1.45,10.5,11.9,-7.6,-5.2,'steel')
 s.stair('receiver',[(-5.2,-1.8,10.3,12.35),(-1.8,2.0,10.3,12.5),(2.0,5.5,10.35,12.5),(5.5,8.5,10.35,12.4)],1.85)
 s.block('stock_spine',1.2,11.1,12.1,8.5,14.4,'black_steel')
 s.block('stock_lower',.95,10.4,11.1,11.2,14.4,'black_steel')
 s.block('butt_pad',1.4,10.1,12.2,14.6,15.2,'rubber')
 s.block('butt_orange',1.45,10.1,12.2,14.4,14.6,'accent')
 s.block('foregrip',1.4,9.5,10.3,-4.8,.6,'black_steel')
 for i,z in enumerate([-4.2,-3.4,-2.6,-1.8]):s.panel('foregrip_slot'+str(i),.71,9.7,9.95,z,z+.4,'recess',.04)
 s.grip('grip',8.1,5.65,1.25,4.8,1.6)
 s.guard(4.7,6.7,7.75,10.35)
 s.mag(1.0,4.2,5.6,8.7,1.1,'black_steel');s.block('magwell',1.55,8.7,10.3,.8,4.4,'black_steel')
 s.panel('ejection_recess',.93,11.05,11.45,5.7,7.9,'recess',.035)
 s.sight(5.8,12.65,1.0,.85)
 s.fins('rail',[-1.0,-.5,0,.5,1,1.5,2,2.5,3,3.5],12.5,12.65,.9,'black_steel')
 return s

def age_old_bond():
 s=Shape()
 s.tube('ivory_muzzle',1.65,1.5,11.5,-9.4,-8.65,'shell',.23)
 s.stair('long_carved_shroud',[(-8.65,-5.6,10.45,12.65),(-5.6,-2.5,10.45,12.65),(-2.5,.2,10.45,12.65),(.2,2.5,10.35,12.65),(2.5,5.6,10.4,12.65),(5.6,7.7,10.6,12.5)],1.8)
 s.block('stock_top',1.0,11.5,12.15,7.7,14.7,'black_steel')
 s.block('stock_end',1.2,8.85,12.15,14.7,15.15,'steel')
 # Triangular thumbhole: diagonal step beam with open middle, never a filled alpha slab.
 s.stair('stock_diagonal',[(9.0,10.2,7.0,7.45),(10.2,11.4,7.45,8.05),(11.4,12.6,8.05,8.65),(12.6,13.8,8.65,9.25),(13.8,14.7,9.25,9.85)],.65,'shell')
 s.grip('pistol_grip',8.6,6.2,1.15,4.5,1.25,'black_steel')
 s.guard(4.8,7.3,8.8,10.65)
 s.mag(1.75,4.6,5.6,10.25,1.15,'black_steel')
 s.panel('carved_gold_band',.91,10.48,12.6,-.15,.25,'accent',.08)
 s.panel('ivory_underlip',.91,10.5,10.85,-8.5,-.2,'trim',.07)
 s.panel('dark_nose_cut',.91,11.2,11.65,-8.4,-6.4,'recess',.03)
 s.sight(4.3,12.8,.8,.4)
 s.fins('receiver_bands',[.3,.65],10.3,12.7,1.9,'trim')
 return s

def insidious():
 s=Shape();s.tube('muzzle',1.4,1.15,11.5,-6.8,-5.9,'steel',.22)
 s.block('barrel_lower',1.45,10.75,11.6,-5.9,-1.0,'black_steel')
 s.stair('swept_spine',[(-5.9,-4.4,11.6,12.1),(-4.4,-2.6,11.6,12.45),(-2.6,-.5,11.6,12.8),(-.5,1.8,11.2,13.05),(1.8,4.2,10.95,13.25),(4.2,6.8,10.95,13.3)],1.75)
 s.block('rear_receiver',1.85,10.8,13.3,6.8,10.2,'shell')
 s.block('stock_upper',1.9,11.25,13.3,10.2,17.9,'shell')
 s.block('stock_tail',1.8,7.0,11.25,16.7,17.9,'shell')
 s.block('stock_floor',1.55,6.9,7.4,12.9,16.7,'black_steel')
 s.mag(10.3,13.0,6.6,11.7,1.25,'black_steel')
 s.grip('grip',7.9,6.7,1.2,4.2,1.45)
 s.guard(4.0,6.8,8.3,10.95)
 # Source lower cable: three descending adjoining stations preserve its open negative space.
 s.stair('lower_cable',[(-5.9,-3.7,10.35,10.56),(-3.7,-1.7,9.7,9.91),(-1.7,.3,9.15,9.36),(.3,2.3,8.75,8.96),(2.3,4.0,8.5,8.71)],.22,'trim')
 s.panel('red_receiver_insert',.94,11.85,13.05,6.9,9.8,'accent',.10)
 s.panel('rear_latch',.97,11.3,12.3,11.0,12.1,'black_steel',.25)
 s.fins('barrel_fin',[-5.5,-5.05,-4.6,-4.15,-3.7,-3.25,-2.8],11.7,12.7,1.6,'steel')
 s.sight(5.4,13.5,1.1,1.1)
 s.box('sight_cap',7.45,8.55,14.6,14.72,5.4,5.65,'steel')
 return s

def phyllotactic_spiral():
 s=Shape();s.tube('muzzle',1.15,1.1,11.6,-6.7,-5.7,'steel',.18)
 s.stair('barrel_shroud',[(-5.7,-3.2,10.75,12.5),(-3.2,-.4,10.75,12.5),(-.4,2.3,10.65,12.5),(2.3,5.0,10.6,12.6),(5.0,8.2,10.4,12.65)],1.7)
 s.block('lower_front',1.5,9.7,10.65,-4.4,1.9,'shell')
 s.stair('stock',[(8.2,11,10.5,12.4),(11,14.4,10.7,12.3),(14.4,17.0,9.0,12.3)],1.65)
 s.block('butt',1.85,8.6,12.4,17.0,17.7,'rubber')
 s.grip('grip',7.9,6.7,1.25,3.8,1.0)
 s.guard(4.6,6.8,8.7,10.65)
 s.mag(11.0,13.3,6.0,10.7,1.3,'shell')
 s.panel('teal_shroud',.86,11.0,11.3,-5.4,1.8,'accent',.08)
 s.panel('side_port',.86,11.35,11.85,2.5,4.5,'recess',.04)
 s.panel('stock_inset',.84,10.8,11.9,11.2,16.4,'black_steel',.06)
 for i,z in enumerate([-4.9,-4.15,-3.4,-2.65,-1.9]):s.panel('vent'+str(i),.86,11.65,12.15,z,z+.35,'recess',.04)
 s.sight(5.0,12.85,1.15,1.6)
 s.box('optic_top',7.425,8.575,14.45,14.57,5.0,5.25,'steel')
 s.block('rail_spine',1.0,12.48,12.62,1.3,4.3,'black_steel')
 s.fins('top_rail',[1.5,2,2.5,3,3.5,4],12.6,12.75,1.1,'black_steel')
 return s

# Hand cannons share only the existing animation interface; authored barrel/grip layouts remain distinct.
def hand_cannon(w):
 s=Shape();duke=w=='igneous_hammer';cy=12.2 if duke else 12.45;top=14.6 if duke else 13.8
 if w=='eyasluna':
  s.tube('barrel_tip',1.6,1.4,12.9,-6.25,-5.8,'shell',.25)
  s.stair('red_barrel',[(-5.8,-3.1,12.1,13.75),(-3.1,-.3,12.1,13.75),(-.3,2.4,12.1,13.75)],1.7)
  s.block('underbarrel_rail',.85,11.35,11.75,-5.1,1.9,'steel')
  s.block('underbarrel_mechanism',1.1,10.6,11.35,-.8,3.5,'black_steel')
  s.tube('underbarrel_front',.75,.6,10.95,-1.5,-.8,'steel',.14)
 elif w=='igneous_hammer':
  s.tube('barrel_tip',1.65,1.75,12.8,-6.15,-5.65,'shell',.25)
  s.stair('sun_barrel',[(-5.65,-3.5,11.5,13.8),(-3.5,-1.2,11.2,14.05),(-1.2,1.0,10.9,14.2),(1.0,2.2,11.1,14.35)],1.75)
  s.stair('wing_crown',[(-6.0,-4.4,13.8,14.05),(-4.4,-2.5,14.05,14.3),(-2.5,-.5,14.3,14.5),(-.5,2.0,14.5,14.65),(2.0,4.9,14.5,14.65)],.8,'steel')
  s.panel('sun_inlay',.88,11.6,13.5,-3.8,.9,'accent',.035)
 else:
  s.tube('ivory_muzzle',1.45,1.65,12.6,-6.3,-5.8,'shell',.22)
  s.stair('carved_barrel',[(-5.8,-3.8,11.7,13.35),(-3.8,-1.8,11.7,13.6),(-1.8,.2,11.7,13.85),(.2,2.65,11.7,13.9)],1.7)
  s.panel('barrel_gold_edge',.86,11.72,11.9,-5.78,2.6,'accent',.06)
 # Open cylinder bridge and physical sidewalls; cylindrical moving volume never disappears inside a slab.
 cz0,cz1=(2.3,5.35) if duke else (2.85,5.85)
 s.block('bridge_top',1.35,top-.15,top,cz0,5.45 if duke else 5.85,'shell')
 if duke:s.block('bridge_rear_step',1.35,14.15,14.35,5.45,5.98,'shell')
 s.block('bridge_lower',1.45,10.65,11.15,1.8,6.6,'steel')
 if not duke:
  s.block('barrel_frame_join',1.2,11.15,13.4,2.35,2.85,'steel')
  s.block('bridge_rear_join',1.2,13.2,13.4,5.85,5.98,'steel')
 s.block('rear_frame',1.40,10.4,13.4 if not duke else 14.35,5.98,6.8,'shell' if w!='eyasluna' else 'black_steel')
 # Visible moving assembly honors base role and axis. 5 solid adjacent bands + rings yield 19 pieces.
 for j,(xw,yy0,yy1) in enumerate([(1.25,cy-1.05,cy-.7),(1.85,cy-.7,cy-.25),(2.1,cy-.25,cy+.25),(1.85,cy+.25,cy+.7),(1.25,cy+.7,cy+1.05)]):
  s.box('mag_cylinder_band'+str(j),8-xw/2,8+xw/2,yy0,yy1,cz0,cz1,'steel')
 s.block('mag_cylinder_front',2.15,cy-.75,cy+.75,cz0-.12,cz0,'black_steel')
 s.block('mag_cylinder_back',2.15,cy-.75,cy+.75,cz1,cz1+.12,'black_steel')
 for i,y in enumerate([cy-.6,cy+.45]):s.panel('mag_flute'+str(i),.94,y,y+.18,cz0+.3,cz1-.3,'recess',.03)
 s.grip('grip',7.8,5.9 if duke else 6.5,1.35,4.7 if duke else 3.9,1.35,'rubber' if w!='nation_of_beasts' else 'shell')
 s.guard(3.6,6.4,9.2,10.65)
 s.block('grip_heel',1.45,5.65 if duke else 6.25,5.9 if duke else 6.5,7.5,9.1,'accent' if w=='nation_of_beasts' else 'black_steel')
 s.box('hammer',7.75,8.25,13.4 if not duke else 14.35,13.85 if not duke else 14.55,6.7,7.0,'steel')
 s.box('sight_left',7.60,7.74,top,top+.18,5.2,5.45,'steel')
 s.box('sight_right',8.26,8.40,top,top+.18,5.2,5.45,'steel')
 # Material-specific wraps/channels affect parallax and are rooted in the source reference.
 if w=='igneous_hammer':
  for i in range(4):s.panel('grip_wrap'+str(i),.69,6.1+i*.85,6.35+i*.85,7.9-i*.27,8.9-i*.27,'rubber',.05)
 elif w=='eyasluna':
  s.panel('red_breach',.86,12.3,13.4,.4,2.5,'shell',.1)
  s.fins('under_lugs',[-.5,.1,.7,1.3,1.9,2.5],10.45,10.6,1.18,'steel')
 else:
  s.panel('ivory_breach',.87,13.1,13.65,.4,2.5,'trim',.05)
  s.stair('grip_carving',[(7.9,8.2,6.47,7.1),(7.5,7.9,7.1,7.9),(7.0,7.5,7.9,8.7),(6.7,7.0,8.7,9.5)],1.44,'trim')
 return s

def subjunctive():
 s=Shape()
 # V2: dense Vex tube body, compact vertical grip, actual fluid cell and three irregular foliage groups.
 s.tube('muzzle',1.6,1.55,11.45,-2.55,-1.8,'black_steel',.25)
 s.block('lower_vex_frame',1.6,9.95,10.75,-1.8,10.3,'shell')
 for i,(z0,z1,w,y0,y1) in enumerate([(-1.8,1.3,2.0,10.75,12.3),(1.3,4.5,2.15,10.8,12.45),(4.5,7.1,1.85,10.75,12.2),(7.1,10.2,2.15,10.7,12.4)]):
  s.block('vex_chamber'+str(i),w,y0,y1,z0,z1,'shell',.23)
 # Source pale cooling conduits break the moss-covered metal into readable functional parts.
 for sign in [-1,1]:
  x=8+sign*1.1;s.box('coolant_pipe_'+str(sign),x-.09,x+.09,11.0,11.18,-1.2,7.0,'trim')
 s.block('stock_spine',.9,10.1,10.65,10.2,16.3,'shell')
 # Broad triangular frame, with adjacent steps sharing positive-area contact.
 for i in range(8):
  z0=10.2+i*.7625;y0=9.75-i*.28
  s.box('stock_diagonal'+str(i),7.58,8.42,y0,y0+.5,z0,z0+.7625,'shell')
 s.block('butt_frame',1.2,7.6,12.25,16.3,16.8,'shell')
 s.box('butt_pad',7.5,8.5,7.75,12.1,16.8,17.02,'rubber')
 for i,(y0,y1) in enumerate([(7.3,8.25),(8.25,9.25),(9.25,10.2)]):
  s.block('grip_vex'+str(i),1.45,y0,y1,7.2,8.8,'shell',.16)
 s.block('grip_heel',1.65,7.15,7.45,7.1,8.9,'steel',.12)
 s.mag(7.55,8.55,5.0,7.25,.72,'black_steel')
 for i in range(8):
  z0=-1.2+i*.575;y0=9.55-i*.215
  s.box('foregrip_brace'+str(i),7.65,8.35,y0,y0+.45,z0,z0+.575,'shell')
 s.block('foregrip_post',.8,7.98,10.3,3.0,3.6,'steel',.12)
 # Stepped circular side cells: 5 rim bands and 3 luminous core bands on each side.
 for side in [-1,1]:
  for i in range(7):
   dy=-.91+i*.26;span=math.sqrt(max(.01,.91*.91-(dy+.13)**2))
   x0,x1=(6.64,7.25) if side<0 else (8.75,9.36)
   s.box('cell_rim'+str(side)+'_'+str(i),x0,x1,10.65+dy,10.65+dy+.26,3.25-span,3.25+span,'trim')
  for i in range(3):
   dy=-.54+i*.36;span=math.sqrt(max(.01,.54*.54-(dy+.18)**2))
   x0,x1=(6.55,6.64) if side<0 else (9.36,9.45)
   s.box('cell_core'+str(side)+'_'+str(i),x0,x1,10.65+dy,10.65+dy+.36,3.25-span,3.25+span,'lens')
 # Solid leaf clusters vary by silhouette, orientation, width and droop; never repeated bands or alpha slabs.
 leaves=[(7.1,-2.0,1.55,2.5,12.85),(8.2,-1.3,1.65,2.6,12.95),(9.0,-.22,1.35,2.0,12.015),
         (7.05,3.2,1.45,2.1,12.80),(8.65,3.985,1.65,2.0,12.145),
         (7.0,7.4,1.5,2.4,12.82),(8.15,8.05,1.7,2.3,12.92),(9.0,8.8,1.35,1.8,12.095)]
 for k,(cx,z,w,l,y) in enumerate(leaves):
  s.box('leaf_stem'+str(k),cx-.10,cx+.10,min(12.12,y-.2),max(12.25,y+.02),z+.04,z+.24,'accent')
  for j,scale in enumerate([.55,1.0,.66,.25]):
   z0=z+j*l/4;yy=y-[0,.18,.40,.63][j]
   s.box('leaf_'+str(k)+'_'+str(j),cx-w*scale/2,cx+w*scale/2,yy-.28,yy+.04,z0,z0+l/4,'accent')
 s.block('optic_mount',.8,12.2,12.55,2.0,2.9,'black_steel',.1)
 s.tube('optic_ring',1.20,1.25,13.05,2.25,2.65,'steel',.15)
 return s

def submission():
 s=Shape();s.tube('muzzle',1.3,1.45,11.35,-2.55,-1.9,'steel',.2)
 s.stair('front_casing',[(-1.9,.2,10.1,11.9),(.2,2.2,9.8,12.2),(2.2,3.6,9.3,12.5),(3.6,5.8,10.2,12.5),(5.8,8.7,10.25,12.5)],1.65)
 s.block('rear_top',1.7,10.9,12.45,8.7,16.3,'steel')
 s.stair('rear_housing',[(11.7,13.2,7.0,10.9),(13.2,15.0,7.3,10.9),(15.0,16.3,8.2,10.9)],1.65)
 s.grip('central_grip',8.8,6.5,1.2,3.8,.3,'black_steel')
 s.mag(7.0,10.2,5.6,9.8,1.18,'shell')
 s.guard(4.0,6.8,8.45,10.25)
 s.panel('red_wedge',.84,9.5,12.4,2.3,3.4,'accent',.08)
 s.panel('rear_port',.86,11.3,12.0,9.1,15.4,'black_steel',.1)
 s.panel('rear_port_inset',.97,11.5,11.8,9.4,14.8,'steel',.03)
 s.block('front_fin_rail',1.2,11.85,12.02,-1.88,1.9,'black_steel')
 s.fins('front_bank',[-1.6,-1.15,-.7,-.25,.22,.65,1.1,1.55],11.95,12.9,1.6,'steel')
 s.stair('rear_cable',[(11.5,13.0,6.3,6.5),(13,14.3,6.55,6.75),(14.3,15.5,7.0,7.2),(15.5,16.4,7.6,7.8),(16.4,17.0,8.5,8.7),(17.0,17.3,9.4,10.6)],.22,'trim')
 s.block('cable_rear_anchor',.5,10.25,10.65,16.1,17.32,'steel')
 s.sight(4.2,12.65,.9,.7)
 return s

def hung_jury_sr4():
 s=Shape();s.tube('omolon_muzzle',1.55,1.8,10.8,-8.25,-7.6,'shell',.23)
 s.stair('white_shroud',[(-7.6,-4.6,9.7,11.9),(-4.6,-1.4,9.7,11.9),(-1.4,1.8,9.9,12.0),(1.8,4.3,9.6,12.05),(4.3,7.2,9.5,12.0),(7.2,10.1,10.4,11.95),(10.1,13.1,10.55,11.9),(13.1,16.0,10.3,11.8)],1.85)
 s.block('rear_butt',1.65,8.1,11.75,16,16.8,'rubber')
 s.stair('thumbhole_floor',[(9.2,10.7,6.9,7.4),(10.7,12.2,7.4,8.0),(12.2,13.7,8.0,8.6),(13.7,16.0,8.6,9.15)],1.15,'shell')
 s.grip('grip',7.1,6.2,1.25,3.6,1.0,'accent')
 s.guard(3.8,6.0,8.8,9.65)
 s.mag(2.7,4.7,6.6,9.5,1.2,'black_steel')
 s.panel('forebody_dark',.94,9.7,10.4,-6.0,.6,'black_steel',.025)
 s.panel('fluid_casing',.94,9.1,11.2,2.3,4.4,'black_steel',.18)
 s.panel('fluid_ring',1.12,9.35,10.95,2.55,4.15,'trim',.08)
 s.panel('fluid_cell',1.20,9.65,10.65,2.85,3.85,'lens',.035)
 s.panel('secondary_cell',.72,7.4,8.6,5.6,6.8,'trim',.17)
 s.panel('black_stock_mark',.94,10.5,11.85,10.8,11.2,'black_steel',.025)
 s.block('rail_spine',.65,11.98,12.08,-.7,2.3,'steel')
 s.sight(4.6,12.05,.8,.45)
 s.fins('top_ticks',[-.5,0,.5,1,1.5,2],12.05,12.18,.7,'steel')
 for e in s.e:
  if not e['name'].startswith(('mag_', 'grip','secondary_cell')):
   e['from'][1]-=.95;e['to'][1]-=.95
 return s

BUILDERS={'krait':krait,'rufuss_fury':rufuss_fury,'origin_story':origin_story,'age_old_bond':age_old_bond,'insidious':insidious,'phyllotactic_spiral':phyllotactic_spiral,'igneous_hammer':lambda:hand_cannon('igneous_hammer'),'eyasluna':lambda:hand_cannon('eyasluna'),'nation_of_beasts':lambda:hand_cannon('nation_of_beasts'),'subjunctive':subjunctive,'submission':submission,'hung_jury_sr4':hung_jury_sr4}

class Baker(kit.Baker):
 def __init__(self,wid):
  # Same production baker, with read-only projection caches outside the repository.
  self.wid=wid;self.D=kit.load_design(wid);D=self.D;self.T=D.T;self.A=D.ATLAS
  self.grade=getattr(D,'grade',kit.default_grade);self.special=getattr(D,'special',lambda *a:None);self.clear=lambda *a:False
  self.is_mag=lambda n:n.startswith('mag_');self.fallback=(78,78,80,255)
  cache=Path('/tmp/w327-cache')/wid;man=json.loads((cache/'manifest.json').read_text());self.views={k:kit.View(cache,k,man) for k in man['views']};self.occ=max(man['hi'][i]-man['lo'][i] for i in range(3))*.025
 def materialize(self,faces):
  """V2 authored finish cues. Metal highlights, coating wear, rubber grooves and organic surfaces are separate.
  These are static RGBA material cues, not a claim of native PBR or dynamic specular response.
  """
  mats=self.D.MATERIALS
  for idx,(n,fn,img,clear,e,others,pm) in enumerate(faces):
   if clear:continue
   role=self.D.material(n,fn);m=mats[role];kind=m['kind'];base=m['color'];w,h=img.size
   out=kit.Image.new('RGBA',(w,h));op=out.load();ip=img.load()
   # Source low-frequency pigment is useful only for actual moss/patina, never blanket scratch noise.
   pigment=img.convert('RGB').filter(kit.ImageFilter.GaussianBlur(max(1,self.T*.11))).load()
   long_u=w>=h
   for i in range(w):
    for j in range(h):
     t=(j+.5)/h if long_u else (i+.5)/w
     v=(j+.5)/h;u=(i+.5)/w
     color=list(base);metal=kind in ('metal','steel','gold');f=1.0;glint=0.0
     if metal:
      # Broad dark-to-light reflection and one controlled soft machining highlight.
      f=.76+.23*math.cos(t*math.pi)+.13*math.exp(-((t-.24)/.18)**2)
      glint=.26*math.exp(-((t-.20)/.065)**2)
      grain=((j if long_u else i)%5-2)*.85
      color=[c+grain for c in color]
     elif kind=='paint':
      f=.94+.07*math.cos(v*math.pi)
      if m.get('coat')=='lacquer':glint=.17*math.exp(-((t-.21)/.10)**2)
     elif kind=='rubber':
      f=.96+.035*math.cos(v*math.pi)
      # Fine cut grip grooves, with a quiet untouched central surface.
      if (j%5==0 and 0<i<w-1):f*=.77
      elif j%5==1:f*=1.04
     elif kind=='cloth':
      f=.92+(.07 if (i//2+j//2)%2 else -.035)
      if j%7==0:f*=.78
     elif kind=='ceramic':
      f=.90+.10*math.cos(v*math.pi);glint=.10*math.exp(-((t-.18)/.13)**2)
     elif kind=='organic':
      f=.87+.15*math.cos(v*math.pi);glint=.16*math.exp(-((t-.22)/.13)**2)
      vein=.5+.5*math.sin((u*2.4+.1*math.sin(v*7))*math.pi*2)
      if vein>.94:color=[min(255,c+19) for c in color]
      elif vein<.06:color=[max(0,c-15) for c in color]
     elif kind=='foliage':
      f=.85+.16*math.cos(v*math.pi)
      # Broad leaf veins and brown tips rooted in its actual plant role.
      if abs(u-.5)<.055:f*=1.24
      elif abs((v+.2*u)% .28-.14)<.035:f*=.78
      if v>.8:color=[color[0]+17,color[1]-8,color[2]-5]
     elif kind=='patina':
      f=.87+.12*math.cos(t*math.pi)
      src=pigment[i,j];green=src[1]-min(src[0],src[2]);lum=sum(src)/3
      patch=max(0,min(1,(green+10)/38))
      patch=max(.04,min(.22,(green+8)/90))
      if lum<20:patch=.08
      # Exposed old alloy and matte moss use contrasting color/roughness, not random grey noise.
      alloy=(64,89,84);moss=(97,103,56)
      color=[alloy[k]*(1-patch)+moss[k]*patch for k in range(3)]
      glint=.22*math.exp(-((t-.22)/.10)**2)
     elif kind in ('lens','glow'):
      f=.90+.1*math.cos(v*math.pi)
      glint=.2*math.exp(-((t-.16)/.08)**2)
     else:f=.88+.08*math.cos(v*math.pi)
     if pm[i][j]:
      # Authored logo, gilding and inlay inherit the surface illumination; no fluorescent flat sticker.
      color=list(ip[i,j][:3])
     light=(244,224,170) if kind=='gold' else (218,231,234)
     rgb=[max(0,min(255,int(color[k]*f*(1-glint)+light[k]*glint))) for k in range(3)]
     # Quiet 1-texel edge wear only at actual exposed coating edges, never all-over grime.
     if kind=='paint' and min(i,j,w-1-i,h-1-j)==0 and ((i<3 or j<2) or (i>w-4 and j>h-4)):
      rgb=[int(c*.78+v*.22) for c,v in zip(rgb,(155,165,164))]
     op[i,j]=tuple(rgb)+(255,)
   if kind not in ('lens','glow','foliage'):
    strength=.32 if kind in ('metal','steel','gold') else .13 if kind in ('rubber','cloth','patina') else .21
    self.rim(out,e,fn,others,strength)
   faces[idx]=(n,fn,out,clear,e,others,pm)
 def hidden(self,e,fn,others):
  # Exact rectangular coverage sweep for these axis-aligned models. This avoids dense per-texel geometry scans.
  axis,side,u,_,v,_=kit.FACE_AXES[fn];plane=e['to' if side else 'from'][axis]+(.02 if side else -.02)
  u0,u1=e['from'][u],e['to'][u];v0,v1=e['from'][v],e['to'][v];rects=[]
  for o in others:
   if not o['from'][axis]+.002<plane<o['to'][axis]-.002:continue
   a,b=max(u0,o['from'][u]),min(u1,o['to'][u]);c,d=max(v0,o['from'][v]),min(v1,o['to'][v])
   if b>a and d>c:rects.append((a,b,c,d))
  if not rects:return False
  cuts=sorted(set([u0,u1]+[x for r in rects for x in r[:2]]))
  for a,b in zip(cuts,cuts[1:]):
   mid=(a+b)/2;cur=v0
   for c,d in sorted((r[2],r[3]) for r in rects if r[0]<=mid<=r[1]):
    if c>cur+1e-8:return False
    cur=max(cur,d)
   if cur<v1-1e-8:return False
  return True

DESIGNED_PAINT="import math\n_GLYPHS={'V':['101','101','101','101','010'],'E':['111','100','110','100','111'],'I':['111','010','010','010','111'],'S':['111','100','111','001','111'],'T':['111','010','010','010','010'],'O':['111','101','101','101','111'],'M':['101','111','111','101','101'],'L':['100','100','100','100','111'],'N':['101','111','111','111','101']}\ndef _text(u,v,txt,x,y,k=.075):\n a=int((u-x)/k);b=int((v-y)/k)\n if u<x or v<y or b>=5 or a>=len(txt)*4:return False\n return a%4<3 and _GLYPHS.get(txt[a//4],['000']*5)[b][a%4]=='1'\ndef _point(e,fn,s,t):\n f=e['from'];a=e['to'];axes={'north':(2,0,0,False,1,False),'south':(2,1,0,True,1,False),'east':(0,1,2,False,1,False),'west':(0,0,2,True,1,False),'up':(1,1,0,True,2,True),'down':(1,0,0,True,2,False)}\n pa,side,ua,uf,va,vf=axes[fn];p=[0,0,0];p[pa]=a[pa] if side else f[pa];p[ua]=f[ua]+(a[ua]-f[ua])*(s if uf else 1-s);p[va]=f[va]+(a[va]-f[va])*(t if vf else 1-t);return p\ndef special(e,fn,s,t):\n n=e['name'];x,y,z=_point(e,fn,s,t);side=fn in ('east','west');role=ROLES[n];base=MATERIALS[role]['color'];accent=MATERIALS['accent']['color'];dark=MATERIALS['recess']['color'];light=MATERIALS['trim']['color'];col=None\n if WID=='krait':\n  if n.startswith('mag_charge_bar') and side and .05<z<7.25 and 10.79<y<11.04:\n   if int((z+.1)*9)%3==0 and int(y*12)%2==0:col=[112,130,29]\n  if n.startswith('receiver') and side and _text(z if fn=='west' else -z,12.15-y,'VEIST',1.0 if fn=='west' else -2.6,0,.08):col=accent\n elif WID=='origin_story':\n  if n.startswith('receiver') and side:\n   stripe=z+(y-10.3)*.75\n   if -.8<stripe<.2 or 3.1<stripe<4.1:col=accent\n   elif .2<stripe<.65:col=light\n   if -4.9<z<-3.9 and 11.25<y<12.05:\n    u=(z+4.9);v=(12.05-y)\n    if abs(u-(.1+v*.5))<.12 or abs(u-(.9-v*.5))<.12:col=accent\n elif WID in ('age_old_bond','nation_of_beasts'):\n  if role in ('shell','trim') and side:\n   # Source-inspired flowing carved bands; clean deliberate paint rather than corrupt shader channels.\n   v=(y-11.0);curve=.34*math.sin((z+3.1)*.9)+11.8\n   if abs(y-curve)<.055 or abs(y-(curve-.32))<.045:col=[158,146,109]\n   if abs(y-(curve+.10))<.045:col=[237,226,188]\n   if WID=='age_old_bond' and -.1<z<.3:col=accent\n elif WID=='igneous_hammer':\n  if n.startswith(('sun_barrel','sun_inlay')) and side:\n   # Trials sun and concentric rays: same motif seen in the source albedo, redrawn for the block face.\n   dz=z+1.35;dy=y-12.4;r=math.hypot(dz,dy);a=math.atan2(dy,dz)\n   col=MATERIALS['shell']['color']\n   if abs(r-.36)<.055 or (.42<r<.72 and int((a+math.pi)*12/math.pi)%2==0):col=accent\n   if abs(r-1.10)<.055 or abs(r-1.36)<.045:col=accent\n   if z<-3.4 and int((z+(y-11.6)*.35)*7)%7==0:col=accent\n elif WID=='hung_jury_sr4':\n  if n.startswith('white_shroud') and side:\n   stripe=z+(y-10.2)*.52\n   if any(abs(stripe-k)<.38 for k in [-6.2,-1.4,4.5,9.4,13.2]):col=accent\n   if _text(z if fn=='west' else -z,10.75-y,'OMOLON',-4.3 if fn=='west' else 2.5,0,.075):col=light\n elif WID=='rufuss_fury':\n  if n.startswith('blue_receiver') and side:\n   curve=10.7+.38*math.sin((z-3.8)*1.3)\n   if abs(y-curve)<.075:col=[121,146,179]\n   elif y<curve-.12:col=[51,68,99]\n elif WID in ('insidious','submission'):\n  if role=='accent' and side:\n   if int((z+y)*13)%7==0:col=[196,93,69]\n  if n.startswith(('swept_spine','front_casing')) and side and y<11.2:\n   if abs(y-(10.8+.13*math.sin(z*5)))<.055:col=[100,96,90]\n elif WID=='phyllotactic_spiral':\n  if n.startswith('grip') and side and 7.0<y<9.7:\n   if int(z*8)%3==0 or int(y*8)%3==0:col=[143,156,152]\n elif WID=='subjunctive':\n  if n.startswith('moss') and fn in ('up','east','west'):\n   col=[74,89,38] if int(z*11+y*3)%4<2 else [105,119,53]\n  if n.startswith('cell_light') and side and (int(z*16)+int(y*16))%3==0:col=[180,236,230]\n if col is not None:return tuple(col)+(255,)\n return None\n"

def evaluate(w):
 # Own temporary scripts, loaded with auto-execution disabled; originals are never saved.
 tmp=Path('/tmp/w327-source');tmp.mkdir(parents=True,exist_ok=True)
 ev=tmp/'evaluate-owned.py';ev.write_text(SOURCE_EVALUATOR)
 row=kit.reg(w);src=row['blend_paths'][0]
 subprocess.run([kit.BLENDER,'-b','--disable-autoexec',src,'--python',str(ev),'--',w,str(tmp/w)],check=True)
 script=(ROOT/'scripts/art/w325/extract_projection_cache.py').read_text().replace('sc = bpy.context.scene',"sc = bpy.context.scene\nsc.render.use_compositing=False\nfor obj in bpy.data.objects:\n    if obj.name.startswith('Plane'): obj.hide_render=True")
 ex=tmp/'extract-owned.py';ex.write_text(script)
 subprocess.run([kit.BLENDER,'-b','--disable-autoexec',src,'--python',str(ex),'--','/tmp/w327-cache/'+w,'600'],check=True)

# Selected official inventory icons establish the finished dye/variant; raw diffuse alone is not final appearance.
FINISH={
'krait':{'shell':('metal',[65,75,71]),'black_steel':('metal',[28,34,34]),'steel':('steel',[122,135,129]),'rubber':('rubber',[24,29,26]),'accent':('paint',[185,208,43])},
'rufuss_fury':{'shell':('organic',[129,164,183]),'accent':('organic',[84,136,183]),'steel':('metal',[62,86,108]),'trim':('steel',[197,210,213]),'black_steel':('metal',[28,37,45])},
'origin_story':{'shell':('paint',[47,69,94]),'accent':('paint',[218,111,40]),'steel':('steel',[133,145,151]),'trim':('paint',[215,221,219]),'black_steel':('metal',[40,46,49])},
'age_old_bond':{'shell':('ceramic',[226,216,184]),'accent':('gold',[192,159,76]),'trim':('ceramic',[241,228,191]),'steel':('metal',[50,51,54]),'black_steel':('cloth',[38,36,45])},
'insidious':{'shell':('metal',[68,65,63]),'accent':('paint',[204,65,39]),'trim':('steel',[155,150,138]),'steel':('steel',[105,106,100]),'black_steel':('metal',[31,32,32]),'rubber':('rubber',[33,35,32])},
'phyllotactic_spiral':{'shell':('paint',[78,48,99]),'accent':('steel',[43,157,184]),'trim':('steel',[166,184,190]),'steel':('steel',[119,135,144]),'rubber':('metal',[39,113,141]),'black_steel':('metal',[32,42,49])},
'igneous_hammer':{'shell':('metal',[32,35,38]),'accent':('gold',[221,181,73]),'trim':('gold',[151,115,87]),'steel':('steel',[98,105,111]),'rubber':('cloth',[76,71,49]),'black_steel':('metal',[26,29,31])},
'eyasluna':{'shell':('paint',[174,40,41]),'accent':('paint',[209,58,44]),'steel':('steel',[108,120,129]),'trim':('steel',[166,177,185]),'black_steel':('metal',[33,38,44]),'rubber':('rubber',[31,35,38])},
'nation_of_beasts':{'shell':('ceramic',[228,217,185]),'accent':('gold',[196,164,77]),'trim':('ceramic',[243,231,195]),'steel':('metal',[58,61,65]),'black_steel':('metal',[28,30,34])},
'subjunctive':{'shell':('patina',[78,92,68]),'accent':('foliage',[110,115,44]),'steel':('metal',[100,123,116]),'trim':('steel',[134,158,139]),'rubber':('rubber',[27,40,31]),'black_steel':('metal',[37,56,47]),'lens':('glow',[139,199,214])},
'submission':{'shell':('metal',[76,70,64]),'accent':('paint',[204,69,39]),'trim':('steel',[151,147,135]),'steel':('steel',[105,109,107]),'black_steel':('metal',[35,36,35]),'rubber':('rubber',[30,33,30])},
'hung_jury_sr4':{'shell':('paint',[28,80,81]),'accent':('gold',[195,152,66]),'trim':('gold',[219,187,106]),'steel':('steel',[120,146,145]),'black_steel':('metal',[28,42,44]),'rubber':('rubber',[25,39,38]),'lens':('glow',[171,184,241])}}

def apply_finish(w,s,mats):
 for role,(kind,color) in FINISH[w].items():mats[role].update(kind=kind,color=color,detail=0,wear=False)
 if w=='eyasluna':mats['shell']['coat']='lacquer'
 for e in s.e:
  n=e['name']
  if w=='phyllotactic_spiral':
   if n.startswith(('lower_front','mag_','grip')):s.roles[n]='accent'
   elif n.startswith(('barrel_shroud0','barrel_shroud1','muzzle')):s.roles[n]='steel'
  if w=='igneous_hammer' and n.startswith('wing_crown'):s.roles[n]='trim'
  if w=='hung_jury_sr4':
   if n.startswith(('fluid_ring','secondary_cell')):s.roles[n]='trim'
   if n.startswith('grip'):s.roles[n]='shell'
  if s.roles[n]=='lens':e['light_emission']=3

def write_design(w):
 s=BUILDERS[w]();d=kit.art(w);d.mkdir(parents=True,exist_ok=True)
 mats={k:dict(v) for k,v in COMMON.items()}
 for k,col in PALETTES[w].items():mats[k]['color']=list(col)
 if w in ('age_old_bond','nation_of_beasts','hung_jury_sr4'):
  for v in mats.values():v['detail']=0
 apply_finish(w,s,mats)
 # Geometry is authored; finished pigment follows the selected official variant, not undyed rip diffuse.
 ev=json.loads((Path('/tmp/w327-source')/w/'source-evaluation.json').read_text())
 lo=[min(e['from'][i] for e in s.e) for i in range(3)];hi=[max(e['to'][i] for e in s.e) for i in range(3)]
 src_lo,src_hi=ev['lo'],ev['hi']
 text='"""'+NOTES[w]+'\nAuthored W327 block geometry. All motion is reused base motion; native acceptance pending."""\n'
 text+='ELEMENTS = '+repr(s.e)+'\nROLES = '+repr(s.roles)+'\nMATERIALS = '+repr(mats)+'\n'
 text+='STYLE="material"\nT=12\nATLAS=512\nPALETTE=8\nNO_OVERLAY=True\n'
 text+='def elements():return ELEMENTS\ndef material(n,fn):return ROLES[n]\n'
 text+='def model2world(name,p):\n'
 if w=='phyllotactic_spiral':
  text+=' return (.58056-(p[2]+6.7)*(.93851/24.4), -(p[0]-8)/27.0, -.076844+(p[1]-6.0)*(.309924/8.57))\n'
 else:
  text+=' return (-(p[0]-8)*'+repr((src_hi[0]-src_lo[0])/(hi[0]-lo[0]))+', '+repr(src_lo[1])+'+(p[2]-'+repr(lo[2])+')*'+repr((src_hi[1]-src_lo[1])/(hi[2]-lo[2]))+', '+repr(src_lo[2])+'+(p[1]-'+repr(lo[1])+')*'+repr((src_hi[2]-src_lo[2])/(hi[1]-lo[1]))+')\n'
 text+='WID='+repr(w)+'\n'+DESIGNED_PAINT
 (d/'design.py').write_text(text)
 icon=d/'source_official_icon.jpg'
 lines=['# W327 v2 material review — '+kit.reg(w)['name'],'','Latest user request: make actual material roles visible. Original v1 remains in revisions/v1.','',
 'Finish authority: selected Bungie definition '+str(kit.reg(w).get('bungie_hash'))+' official inventory icon, saved locally; icon SHA256 '+(kit.sha(icon) if icon.exists() else 'not present')+'. Actual .blend source, source albedo and source review images remain separate evidence.',
 '', 'The raw diffuse lacks final dye on Rufus, Phyllotactic and the selected Hung Jury variant. V2 uses the official icon finish: pale blue organic shell; purple/teal coated alloy; teal/gold Omolon respectively. It does not claim the white rip shader is the selected Hung Jury finish.',
 '', '| Role | Surface | RGB |','|---|---|---|']
 for role,m in mats.items():lines.append('| '+role+' | '+m['kind']+' | '+str(m['color'])+' |')
 lines += ['', 'Exposed alloy: controlled directional sheen and 1-texel exposed bevel. Coated metal: calm pigment planes, minimal corner wear. Rubber: fine grooves with low broad contrast. Cloth: restrained woven rows. Ceramic/organic shell: broad warm/pale highlights. Moss: actual foliage and patinated-body roles. Lens/cell: separate cool luminous color.', '', 'No blanket rip-seam overlay or random universal grime. These are static RGBA material cues in the native item texture, not a claim of dynamic PBR/specular reconstruction. Native client acceptance remains pending.']
 (d/'MATERIAL_REVIEW.md').write_text('\n'.join(lines)+'\n')
 for f in ['source-evaluation.json','source_side.png','source_oblique.png','source_top.png']:
  shutil.copy2(Path('/tmp/w327-source')/w/f,d/f)
 # Albedo is source evidence; do not confuse original diagnostic shader artifacts with intended color.
 src=Path('/tmp/w327-cache')/w/('py_albedo.png' if w=='phyllotactic_spiral' else 'px_albedo.png')
 shutil.copy2(src,d/'source_albedo.png')
 (d/'DESIGN.md').write_text('# '+kit.reg(w)['name']+' — W327\n\n'+NOTES[w]+'\n\nSource `.blend` evaluated headlessly with `--disable-autoexec`; original file never saved. Source JSON records SHA, objects, bones, actions. Source colors sampled through the existing projection extractor; dark/diagnostic source surfaces reconstructed using explicit material roles.\n\nSolid adjoining cross-section blocks provide actual thickness. Muzzle, sight and stock openings are geometry. Face UVs are packed with 1-texel gutters and bevels, 512 atlas maximum. Materials: '+', '.join(mats)+'.\n\nPresentation contract: '+kit.reg(w)['base']+'. Original source is a weapon-only rig; no player hand motion was claimed. Base 61-pose motion is reused, not a newly sourced reload. Native grip/contact/ADS/reload and 10–20 weapon display acceptance remain master QA.\n')
 return s

def visible_coplanar(a,b,ax,q,els):
 # Sweep the intersection of same-facing rectangles, subtracting every solid outside the common face.
 others=[e for e in els if e is not a and e is not b]
 uv=[j for j in range(3) if j!=ax];u,v=uv
 plane=a[q][ax];lo=[max(a['from'][j],b['from'][j]) for j in uv];hi=[min(a['to'][j],b['to'][j]) for j in uv]
 if any(hi[k]-lo[k]<=1e-7 for k in range(2)):return False
 cuts=[]
 for k,j in enumerate(uv):cuts.append(sorted(set([lo[k],hi[k]]+[max(lo[k],min(hi[k],e[t][j])) for e in others for t in ('from','to')])))
 for a0,a1 in zip(cuts[0],cuts[0][1:]):
  for b0,b1 in zip(cuts[1],cuts[1][1:]):
   if a1-a0<1e-7 or b1-b0<1e-7:continue
   pt=[0,0,0];pt[ax]=plane+(.00001 if q=='to' else -.00001);pt[u]=(a0+a1)/2;pt[v]=(b0+b1)/2
   if not any(all(e['from'][j]<pt[j]<e['to'][j] for j in range(3)) for e in others):return True
 return False

def check(w):
 p=kit.skin_path(w);d=json.loads(p.read_text());els=sum(d['parts'].values(),[])
 assert 0<len(els)<=1000
 assert len({e['name'] for e in els})==len(els)
 for e in els:
  assert all(-16<=v<=32 for v in e['from']+e['to'])
  assert all(e['from'][i]<e['to'][i] for i in range(3))
  assert len(e['faces'])==6
  for f in e['faces'].values():assert len(f['uv'])==4 and all(0<=v<=16 for v in f['uv'])
 out=io.StringIO()
 with contextlib.redirect_stdout(out):kit.adscheck(w)
 (kit.art(w)/'adscheck.txt').write_text(out.getvalue())
 # Same-facing coplanar positive-area overlaps are the potential z-fighting cases.
 overlaps=[]
 for i,a in enumerate(els):
  for b in els[i+1:]:
   for ax in range(3):
    rem=[j for j in range(3) if j!=ax]
    if any(abs(a[q][ax]-b[q][ax])<1e-7 and visible_coplanar(a,b,ax,q,els) for q in ['from','to']):
     # Faces completely internal to a third solid are hidden by design; still record for review.
     overlaps.append([a['name'],b['name'],ax])
 report={'elements':{k:len(v) for k,v in d['parts'].items()},'total':len(els),'uv_in_range':True,'atlas':d['texture_size'],'exposed_coplanar_overlaps':overlaps,'ads_profile_ok':'  OK:' in out.getvalue(),'native_qa':'pending master'}
 (kit.art(w)/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(w,json.dumps({k:v for k,v in report.items() if k!='exposed_coplanar_overlaps'}),'coplanar',len(overlaps),flush=True)

def build(w):
 write_design(w);Baker(w).build()
 p=kit.art(w)/'manifest.json';m=json.loads(p.read_text());m.update(batch='W327',revision=2,material_finish='selected official inventory icon; authored material-specific RGBA cues',source_blend_sha256=json.loads((kit.art(w)/'source-evaluation.json').read_text())['sha256'],motion='reused base 61-pose presentation contract; source weapon rig has no reload action',native_acceptance='pending master Vision');p.write_text(json.dumps(m,indent=2)+'\n');check(w)

if __name__=='__main__':
 cmd=sys.argv[1] if len(sys.argv)>1 else 'all';ids=IDS if len(sys.argv)<3 or sys.argv[2]=='all' else [sys.argv[2]]
 for w in ids:
  if cmd=='evaluate':evaluate(w)
  if cmd in ('build','all'):build(w)
  if cmd in ('render','all'):kit.render(w)
  if cmd=='check':check(w)
