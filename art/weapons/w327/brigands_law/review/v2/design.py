from pathlib import Path
import json
D=json.loads(Path(__file__).with_name('design.json').read_text())
STYLE='material'
T=10
ATLAS=512
PALETTE=16
NO_OVERLAY=False
MATERIALS=D['materials']
def elements():return D['elements']
def model2world(name,p):return (p[0],p[2],p[1])
def is_magazine(name):return name.startswith('mag_')
def special(e,fn,s,t):
 c=MATERIALS[e['role']]['color'];n=e['name']; side=fn in ('east','west')
 def line(points,width=.018):
  for (ax,ay),(bx,by) in zip(points,points[1:]):
   dx,dy=bx-ax,by-ay;v=max(0,min(1,((s-ax)*dx+(t-ay)*dy)/(dx*dx+dy*dy or 1)))
   if (s-ax-v*dx)**2+(t-ay-v*dy)**2<width**2:return True
  return False
 if side:
  if e['role']=='rubber' and int(t*max(3,(e['to'][1]-e['from'][1])*10))%5==0:c=[int(v*.72) for v in c]
  if ('vent' in n or 'ribbed' in n) and .2<t<.8 and int(s*12)%3==0:c=MATERIALS['black']['color']
  if 'circuit_panel' in n:
   if line([(.08,.25),(.3,.25),(.3,.46),(.52,.46),(.52,.72),(.82,.72),(.82,.5),(.96,.5)],.016) or line([(.16,.8),(.3,.8),(.3,.64)],.016):c=MATERIALS['black']['color']
  if 'rune_plate' in n or 'purple_rune_panel' in n:
   if line([(.22,.8),(.44,.28),(.54,.28),(.38,.55),(.73,.55),(.78,.78)],.018):c=MATERIALS['glow']['color']
  if 'receiver_mark' in n or 'receiver_steel_mark' in n:
   if line([(.15,.2),(.8,.2),(.8,.33),(.58,.33)],.018):c=MATERIALS['black']['color']
   if .35<t<.42 and .15<s<.65:c=MATERIALS['accent']['color']
  if 'orange_tail' in n:
   u=(s*5)%1;v=(t*2)%1
   if abs(v-.23)<.035 and .25<u<.75 or abs(v-.77)<.035 and .25<u<.75 or abs(u-.25+abs(v-.5)*.45)<.035 or abs(u-.75-abs(v-.5)*.45)<.035:c=[int(x*.68) for x in c]
  if 'grip' in n and e['role']=='rubber' and MATERIALS['accent']['color']==[53,139,177]:
   if (int(s*14)+int(t*18))%7==0 or (int(s*14)-int(t*18))%7==0:c=MATERIALS['accent']['color']
  if 'engraved_panel' in n:
   if line([(.08,.7),(.32,.3),(.55,.65),(.88,.2)],.018):c=MATERIALS['gold']['color']
  if 'grip_blue_seal' in n:
   if line([(.25,.7),(.5,.3),(.75,.7),(.5,.5),(.25,.7)],.022):c=MATERIALS['gold']['color']
  if 'blue_grip_medallion_center' in n:
   if line([(.5,.2),(.44,.46),(.5,.78),(.56,.46),(.5,.2)],.018) or line([(.44,.4),(.25,.28),(.2,.15)],.018) or line([(.56,.4),(.75,.28),(.8,.15)],.018) or line([(.44,.5),(.2,.48),(.15,.6)],.018) or line([(.56,.5),(.8,.48),(.85,.6)],.018) or line([(.46,.6),(.3,.75),(.3,.9)],.018) or line([(.54,.6),(.7,.75),(.7,.9)],.018):c=[22,30,55]
 return None if list(c)==MATERIALS[e['role']]['color'] else tuple(c)+(255,)

def material(name,fn):
 e=next(e for e in D["elements"] if e["name"]==name)
 return e["role"]
