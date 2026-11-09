#!/usr/bin/env python3
"""Whisper-only detail revision. Authored solids based on re-evaluated source .blend.
No source mesh conversion. Other W350 weapon paths are never written.
"""
import math,json,copy,sys,inspect,subprocess,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import power_r2 as r
p=r.p;ROOT=r.ROOT;A=r.A;ART=r.ART;W='whisper_of_the_worm';D=ART/W;OUT=D/'r3'
PALETTE={**p.PALETTES[W],'shell':(21,31,29),'dark':(12,20,20),'steel':(49,63,61),'bone':(235,243,241),'trim':(167,201,198),'ivory':(248,252,250),'silver':(96,117,109),'lens':(16,67,164),'rubber':(19,27,25)}

def geometry():
 s=r.whisper_of_the_worm()
 remove=('muzzle_throat','skull_','jaw_spine','receiver','lower_receiver','stock_','pistol_grip','scope_mount','scope_turret','scope_objective','scope_tube','scope_ocular','barrel_out','barrel_in','barrel_rim','trigger')
 s.e=[e for e in s.e if not e['name'].startswith(remove)];s.authored_triangles=[t for t in s.authored_triangles if not t['name'].startswith(remove)]
 s.cyl('muzzle_inner_bore',[(145,338,.32),(193,338,.32)],'dark',8,.12)
 s.e=[e for e in s.e if not e['name'].startswith(('scope_spine-1_1','scope_spine1_1'))];s.authored_triangles=[t for t in s.authored_triangles if not t['name'].startswith(('scope_spine-1_1','scope_spine1_1'))]
 # Shared-point closed chamfered shroud, replacing a long exposed generic cylinder.
 s.shell('barrel_shroud',[(188,322,352,1.0,.68),(312,322,353,1.0,.68),(610,321,354,1.1,.70),(641,313,355,1.27,.72)],'shell')
 s.shell('barrel_collar',[(632,313,355,1.39,.85),(645,313,355,1.39,.85),(655,327,355,1.18,.8)],'steel')
 # Narrow cranial bridge leaves both sculptural orbital recesses deep behind side brows.
 s.shell('skull_cranial_bridge',[(84,323,337,.45,.6),(108,316,340,.58,.7),(175,322,343,.58,.6),(204,324,344,.50,.6)],'bone')
 s.shell('skull_mandible',[(84,352,363,.40,.7),(107,353,373,.82,.7),(168,348,367,1.0,.6),(202,346,360,.58,.6)],'bone')
 for sd in [-1,1]:
  # Separate brow, zygomatic arch and jaw ramus create physical eye and mouth cavities.
  s.relief('skull_brow'+str(sd),[(83,324),(91,315),(106,315),(113,310),(134,315),(149,315),(165,321),(170,329),(155,328),(141,325),(129,327),(117,326),(105,329),(92,329)],sd*.48,.30,'bone')
  s.relief('skull_cheek'+str(sd),[(110,345),(121,343),(134,344),(145,339),(162,340),(176,341),(165,348),(150,349),(142,345),(127,349),(115,347)],sd*.51,.26,'ivory')
  s.relief('skull_socket_floor'+str(sd),[(111,328),(129,327),(145,331),(143,343),(122,344),(112,339)],sd*.35,.035,'dark')
  s.relief('skull_jaw_ramus'+str(sd),[(151,350),(173,343),(186,344),(178,354),(170,362),(156,366),(150,360)],sd*.55,.20,'bone')
  # Source jaw's prominent teeth and nasal horns are small closed wedges, not alpha spikes.
  for j,pts in enumerate([[(102,337),(110,338),(108,350)],[(144,340),(151,337),(148,352)],[(86,354),(94,357),(89,345)],[(121,369),(128,368),(124,384)],[(88,319),(93,306),(96,322)]]):s.relief('skull_tooth'+str(sd)+'_'+str(j),pts,sd*.48,.14,'ivory')
 # Bone roots swell into long source-evidenced swept spines, rather than sticks.
 def horn(n,stations,role='bone',N=5):
  rings=[]
  for k,(x,px,py,rx,ry) in enumerate(stations):
   if k==len(stations)-1:rx=ry=0
   rings.append([s.point(x+rx*math.sin(i*math.tau/N),px,py-ry*math.cos(i*math.tau/N)/s.u) for i in range(N)])
  s.loft(n,rings,role)
 for sd in [-1,1]:
  for j,st in enumerate([
   [(sd*.38,133,321,.24,.17),(sd*.65,171,315,.23,.16),(sd*.59,251,293,.018,.014)],
   [(sd*.40,165,326,.30,.20),(sd*.78,208,324,.23,.14),(sd*.66,330,309,.018,.012)],
   [(sd*.34,165,358,.29,.20),(sd*.63,211,366,.24,.18),(sd*.57,325,391,.018,.012)],
   [(sd*.39,190,350,.27,.19),(sd*.74,236,359,.20,.14),(sd*.60,355,369,.018,.012)],
   [(sd*.35,206,330,.20,.14),(sd*.50,249,327,.17,.10),(sd*.43,350,315,.018,.012)]
  ]):horn('skull_swept_horn'+str(sd)+'_'+str(j),st)
 # Receiver is a framed mechanism. The narrow core and exposed bolt sit behind diagonally separated plates.
 s.shell('receiver_mechanism',[(643,333,360,.58,.9),(715,329,372,.58,.9),(787,326,387,.54,.9),(857,328,386,.54,.9)],'dark')
 s.panel('receiver_upper_brace',[(640,313),(665,313),(666,329),(725,313),(761,307),(834,307),(854,317),(854,328),(765,320),(678,348),(641,348)],1.45,'shell')
 s.panel('receiver_lower_housing',[(754,350),(785,362),(856,362),(866,372),(865,389),(794,390),(775,403),(757,401)],1.48,'shell')
 s.panel('receiver_magwell',[(757,380),(794,386),(795,407),(768,406),(757,401)],1.46,'steel')
 s.cyl('receiver_exposed_bolt',[(786,340,.44),(835,340,.44),(855,340,.39)],'steel',8)
 s.cyl('receiver_bolt_front_band',[(784,340,.48),(791,340,.48)],'silver',8)
 s.cyl('receiver_bolt_rear_band',[(844,340,.47),(852,340,.47)],'bone',8)
 for sd in [-1,1]:
  s.relief('receiver_front_inset'+str(sd),[(690,337),(723,326),(756,324),(771,331),(772,345),(758,350),(721,348)],sd*.58,.10,'steel')
  s.relief('receiver_selector'+str(sd),[(799,375),(815,375),(819,379),(815,382),(799,382)],sd*.78,.08,'steel')
  s.beamp('receiver_bolt_return'+str(sd),(854,347),(922,347),.18,.20,'steel',sd*.40)
  # Structural lower bone roots have distinct swell and curvature beneath the mechanism.
  for j,st in enumerate([
   [(sd*.30,746,377,.32,.23),(sd*.69,692,370,.30,.20),(sd*.76,614,357,.018,.012)],
   [(sd*.35,748,388,.31,.22),(sd*.77,710,390,.26,.18),(sd*.74,657,374,.018,.012)],
  ]):horn('receiver_bone_sweep'+str(sd)+'_'+str(j),st)
 # Source-shaped grip is continuous with upper stock, with a real thumb aperture.
 s.panel('stock_upper',[(853,325),(905,325),(922,312),(958,316),(1010,323),(1083,319),(1092,329),(1087,351),(1010,351),(964,348),(950,356),(854,354)],1.40,'shell')
 s.panel('stock_butt',[(1071,325),(1095,316),(1100,326),(1094,414),(1083,423),(1065,418)],1.56,'rubber')
 s.panel('stock_lower',[(919,388),(930,409),(944,421),(1037,397),(1077,396),(1073,415),(942,435),(936,429)],1.22,'shell')
 s.panel('stock_grip_root',[(855,356),(922,356),(940,372),(927,391),(914,387),(854,384)],1.30,'shell')
 s.griploft('pistol_grip',[(375,914,934,.96),(389,916,939,1.05),(410,928,953,1.13),(426,939,957,.96)],'rubber')
 s.panel('stock_cheek',[(976,329),(1057,324),(1069,329),(1068,344),(991,347),(975,342)],1.50,'steel')
 for sd in [-1,1]:
  s.relief('stock_inset_plate'+str(sd),[(1006,357),(1067,356),(1065,390),(1008,398),(992,388),(1005,372)],sd*.64,.08,'bone')
  s.relief('stock_cheek_latch'+str(sd),[(981,332),(992,331),(992,345),(981,345)],sd*.81,.10,'bone')
  s.beamp('trigger_guard_front'+str(sd),(876,380),(879,394),.14,.17,'steel',sd*.19)
  s.beamp('trigger_guard_floor'+str(sd),(879,394),(910,394),.14,.17,'steel',sd*.19)
  horn('stock_taken_root'+str(sd),[(sd*.24,958,329,.28,.21),(sd*.61,984,322,.28,.16),(sd*.55,1038,306,.018,.012)])
 s.beamp('trigger',(897,378),(891,388),.16,.16,'dark')
 s.cyl('scope_main_optic',[(725,280,.90),(732,280,.90),(775,280,.82),(814,280,.58),(936,280,.55),(948,280,.62),(956,280,.57)],'shell',8,.17)
 # Real two-foot scope saddle with a gap, retention bands and side/top adjustment drums.
 s.panel('scope_front_pedestal',[(813,294),(833,294),(838,307),(812,307)],.66,'steel')
 s.panel('scope_rear_pedestal',[(872,292),(890,292),(896,307),(876,307)],.66,'steel')
 s.cyl('scope_forward_collar',[(812,280,.64),(821,280,.64)],'steel',8,.15)
 s.cyl('scope_rear_collar',[(931,280,.66),(940,280,.66)],'steel',8,.15)
 s.boxp('scope_adjustment_saddle',(842,260),(871,295),1.12,'shell',.10)
 # Cross-axis turret is a closed cylindrical solid, avoiding a generic square control block.
 rings=[]
 for x,rad in [(.51,.29),(.80,.29)]:rings.append([s.point(x,853+rad*math.cos(i*math.tau/8)/s.u,280+rad*math.sin(i*math.tau/8)/s.u) for i in range(8)])
 s.loft('scope_side_adjustment',rings,'bone')
 s.boxp('scope_top_adjustment',(842,251),(864,258),.72,'bone',.06)
 s.cyl('scope_front_lens',[(729,280,.71),(731,280,.71)],'lens',8)
 s.cyl('scope_rear_lens',[(950,280,.44),(952,280,.44)],'lens',8)
 # Subtle front top serrations are UV; only the large source top spines retained by R2 are geometry.
 return s

# Reuse the trusted native baker without changing the shared R2 generator or any other weapon.
# The copied function receives Whisper-only globals; version/proof outputs route to r3.
def apply_emission(s):
 for e in s.e:
  if e['name'].startswith('skull_') and not e['name'].startswith('skull_socket_floor'):
   e['light_emission']=15;e['shade']=False
  elif e['name'].startswith(('scope_front_lens','scope_rear_lens')):
   e['light_emission']=8;e['shade']=False


def build():
 OUT.mkdir(exist_ok=True)
 for f in Path('/tmp/exotic-expansion-20261109/whisper-r3/source-detail').glob('*'):
  if f.suffix in ('.png','.json'):shutil.copy2(f,OUT/f.name)
 p.PALETTES[W]=PALETTE
 fn=inspect.getsource(r.bake).replace("out=ART/w/'r2'","out=ART/w/'r3'").replace('revision=2','revision=3').replace("'scripts/art/w350/power_r2.py'","'scripts/art/w350/power_whisper_r3.py'")
 # Painter detail is kept separate from source geometry and uses the same face/world mapping.
 marker='  return c+(255,)'
 fn=fn.replace(marker,"  c=detail_color(s,e,fn,pt,px,py,side,c)\n"+marker)
 fn=fn.replace('T=22','T=32')
 fn=fn.replace("skin={'texture_size':","apply_emission(s)\n skin={'texture_size':")
 # Avoid empty space from R2 single-lines dominating the new Taken pattern.
 fn=fn.replace("if w=='whisper_of_the_worm' and side:","if False and w=='whisper_of_the_worm' and side:")
 ns=dict(r.__dict__);ns['detail_color']=detail_color;ns['apply_emission']=apply_emission;exec(fn,ns)
 s=ns['bake'](W,geometry());check()
 v=json.loads((D/'validation.json').read_text());v.update(revision=3,detailRevision='source-solid skull/bolt/receiver/scope/stock detail; native acceptance pending');p.write(D/'validation.json',v);p.write(OUT/'validation.json',v)
 m=json.loads((D/'manifest.json').read_text());m['generatorSHA256']=p.sha(__file__);m['qualityRevision']='Whisper R3 detail';p.write(D/'manifest.json',m)
 return s

def check():
 fn=inspect.getsource(r.check).replace("ART/w/'r2/validation.json'","ART/w/'r3/validation.json'").replace("'revision':2","'revision':3")
 ns=dict(r.__dict__);exec(fn,ns);ns['check'](W)

def segdist(x,y,a,b):
 vx,vy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*vx+(y-a[1])*vy)/(vx*vx+vy*vy)));return math.hypot(x-a[0]-t*vx,y-a[1]-t*vy)

def detail_color(s,e,fn,pt,px,py,side,c):
 n=e['name'];role=s.roles[n]
 if role in ('bone','ivory') and not n.startswith('skull_'):c=(37,51,48)
 if role=='lens':
  rr=math.hypot((pt[0]-8)/s.u,py-280)
  c=(12,40,106) if rr>15 else (20,84,173) if rr>7 else (13,56,136)
  if 4<rr<6:c=(28,113,188)
 if side:
  # Latest user render supersedes speculative white fissures: sparse short cyan marks/vents.
  if n.startswith('barrel_shroud'):
   if 289<px<440 and 334<py<346:
    if 1.6<((px+(py-338)*.55)%12)<4.2:c=(62,110,113)
   for cx,cy,rx,ry in [(314,328,3,2),(368,331,4,2),(427,329,3,4),(491,337,3,2),(530,332,2,3),(566,341,3,2),(595,334,2,3)]:
    if ((px-cx)/rx)**2+((py-cy)/ry)**2<1:c=(61,107,107)
  if n.startswith('receiver_upper_brace') and 645<px<672 and abs(py-343)<.8:c=(218,241,239)
  if n.startswith('receiver_front_inset') and any(segdist(px,py,a,b)<.65 for a,b in [((700,337),(719,332)),((736,331),(751,332))]):c=(39,80,79)
  # Large bone facets have shallow sculptural ridges and joint creases, not arbitrary vein noise.
  if n.startswith('skull_'):
   contours=[[(94,324),(110,322),(123,326),(141,322),(157,327)],[(113,360),(132,356),(153,360),(174,354)],[(174,325),(196,328),(221,321)],[(196,359),(220,366),(241,374)]]
   near=min(segdist(px,py,a,b) for path in contours for a,b in zip(path,path[1:]))
   if near<.55:c=tuple(max(0,q-22) for q in c)
   elif .8<near<1.4:c=tuple(min(255,q+14) for q in c)
  if n.startswith('stock_inset_plate'):
   if abs(px-(1033-.35*(py-358)))<.8:c=(34,62,58)
  if n.startswith('barrel_shroud') and py<326 and int(px/8)%3==0:c=tuple(min(255,q+5) for q in c)
  if n.startswith('receiver_bolt') and any(abs(px-x)<.9 for x in [818,823,838,843]):c=(30,43,39)
 if n.startswith('scope_'):
  if n.startswith('scope_ocular') and int(px*2)%5==0:c=tuple(min(255,q+16) for q in c)
  if n.startswith('scope_side_adjustment') and side:
   R=math.hypot(px-853,py-280)
   if 4.5<R<5.5:c=(143,174,160)
   elif R<1.0:c=(21,31,27)
 return c

def render():
 # R2 and R3 use identical camera/illumination; compare actual native model JSON.
 text=(ROOT/'scripts/art/w325/render_model.py').read_text().replace("'q': (-0.7, 0.45, -0.45)","'q': (-1, .65, -.45), 'otherq': (1, .65, -.45)").replace('* 1.1','* 1.15')
 text=text.replace("verts, polys, uvs = [], [], []", "verts, polys, uvs, emission = [], [], [], []")
 text=text.replace("polys.append((b, b + 1, b + 2, b + 3))", "polys.append((b, b + 1, b + 2, b + 3)); emission.append(e.get('light_emission',0)/15)")
 text=text.replace("me.materials.append(mat);", "ea=me.attributes.new('native_emission','FLOAT','FACE');ea.data.foreach_set('value',emission)\nattr=nt.nodes.new('ShaderNodeAttribute');attr.attribute_name='native_emission'\nem=nt.nodes.new('ShaderNodeEmission');nt.links.new(ti.outputs[0],em.inputs['Color']);em.inputs['Strength'].default_value=1\nmix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(attr.outputs['Fac'],mix.inputs[0]);nt.links.new(bs.outputs[0],mix.inputs[1]);tr=nt.nodes.new('ShaderNodeBsdfTransparent');ema=nt.nodes.new('ShaderNodeMixShader');nt.links.new(ti.outputs[1],ema.inputs[0]);nt.links.new(tr.outputs[0],ema.inputs[1]);nt.links.new(em.outputs[0],ema.inputs[2]);nt.links.new(ema.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],nt.nodes['Material Output'].inputs[0])\nme.materials.append(mat);")
 renderer=OUT/'render_native.py';renderer.write_text(text)
 for label,model,texture in [('after',OUT/'native-render-input.json',A/f'textures/item/weapon/w350/{W}.png'),('before',Path('/tmp/exotic-expansion-20261109/whisper-r3/before-model.json'),Path('/tmp/exotic-expansion-20261109/whisper-r3/before-atlas.png'))]:
  subprocess.run([p.BLENDER,'-b','--python',str(renderer),'--',str(OUT/label),str(model),str(texture),'east,q,otherq,front'],check=True)
 board=Image.new('RGB',(2400,2220),(24,30,33));dr=ImageDraw.Draw(board)
 for col,label in enumerate(['before','after']):
  dr.text((col*1200+16,12),('R2 before' if col==0 else 'R3 skull / mechanism detail - offline native JSON'),fill='white')
  for row,v in enumerate(['east','q','otherq']):board.paste(Image.open(OUT/f'{label}_{v}.png').convert('RGB'),(col*1200,40+row*720))
 board.save(OUT/'before-after.png')
 # Fixed 3D region cameras, shared between revisions and both sides; no mirrored crop mistakes.
 close_text=text.replace('for k in want:', "if len(a)>4:\n    region=a[4]\n    cc,ee=({'muzzle':([8,10.7,-11.0],10.5),'receiver':([8,10.6,10.5],18.0)})[region]\n    c=mathutils.Vector(mb(cc));ext=ee/16\n    sc.render.resolution_x,sc.render.resolution_y=1400,900\nfor k in want:")
 close_renderer=OUT/'render_close.py';close_renderer.write_text(close_text)
 for part in ['muzzle','receiver']:
  for label,model,texture in [('after',OUT/'native-render-input.json',A/f'textures/item/weapon/w350/{W}.png'),('before',Path('/tmp/exotic-expansion-20261109/whisper-r3/before-model.json'),Path('/tmp/exotic-expansion-20261109/whisper-r3/before-atlas.png'))]:
   subprocess.run([p.BLENDER,'-b','--python',str(close_renderer),'--',str(OUT/(part+'_'+label)),str(model),str(texture),'east,q,otherq',part],check=True)
  sheet=Image.new('RGB',(2800,2820),(25,31,35));dd=ImageDraw.Draw(sheet)
  for col,label in enumerate(['before','after']):
   dd.text((col*1400+12,8),label+' '+part+' / fixed 3D camera region',fill='white')
   for row,v in enumerate(['east','q','otherq']):sheet.paste(Image.open(OUT/f'{part}_{label}_{v}.png').convert('RGB'),(col*1400,40+row*920))
  sheet.save(OUT/f'{part}-closeups.png')
 print('Whisper R3 previews',OUT/'before-after.png',flush=True)

if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1] in ['build','render','check']
 if sys.argv[1]=='build':build()
 elif sys.argv[1]=='render':render()
 else:check()
