"""W325 hand-painted identity details. Rip-image placement, no stochastic grime."""
import math
from hc import fpoint, _FA, inpoly

def tint(c, d): return tuple(max(0,min(255,v+d)) for v in c[:3])+(255,)
GLYPHS={
 'H':['101','101','111','101','101'], 'A':['010','101','111','101','101'],
 'K':['101','110','100','110','101'], 'E':['111','100','110','100','111'],
 'O':['111','101','101','101','111'], 'M':['10001','11011','10101','10001','10001'],
 'L':['100','100','100','100','111'], 'N':['1001','1101','1011','1001','1001'],
 'U':['101','101','101','101','111'], 'R':['110','101','110','101','101'],
 'S':['111','100','111','001','111'], 'T':['111','010','010','010','010'],
 'I':['111','010','010','010','111'], 'C':['111','100','100','100','111'],
 '0':['111','101','101','101','111'], '1':['010','110','010','010','111'],
 '2':['110','001','010','100','111'], '3':['110','001','010','001','110'],
 '4':['101','101','111','001','001'], '7':['111','001','010','010','010']}
def glyph(x,y,text,x0,y0,scale):
 xx=(x-x0)/scale; yy=int((y-y0)/scale)
 if yy<0 or yy>=5 or y<y0:return False
 for ch in text:
  g=GLYPHS.get(ch,['0']*5); w=len(g[0])
  if 0<=xx<w:return g[yy][int(xx)]=='1'
  xx-=w+1
 return False

def detail(wid,e,fn,s,t,c,C,T):
 n=e['name']; c=c or (65,65,65,255)
 p=fpoint(e,fn,s,t); x,y=C.img(n,p)
 dark=(29,31,31,255); metal=(168,174,173,255)
 side=fn in ('west','east')
 def box(a,b,d,f):return a<=x<=d and b<=y<=f
 def line(a,b,d,f,width=.7):
  dx,dy=d-a,f-b; l=dx*dx+dy*dy
  k=max(0,min(1,((x-a)*dx+(y-b)*dy)/l)) if l else 0
  return math.hypot(x-a-k*dx,y-b-k*dy)<width
 def rect(a,b,d,f,width=.7):return box(a-width,b-width,d+width,f+width) and not box(a+width,b+width,d-width,f-width)
 def disk(a,b,r):return (x-a)**2+(y-b)**2<=r*r
 def textmark(text,x0,y0,scale):
  width=sum(len(GLYPHS.get(ch,['0'])[0])+1 for ch in text)-1
  xx=x0+width*scale-(x-x0) if fn=='west' else x
  return glyph(xx,y,text,x0,y0,scale)
 # Grip checkering is locked to model coordinates across the machined segment joins.
 grip=n.startswith('grip_panel') or (wid in ('ballyhoo_mk_27','guseva_c') and n.startswith('grip_core'))
 if grip:
  u=int(p[2]*T); v=int(p[1]*T)
  if side:
   if (u+v)%6==0 or (u-v)%6==0:c=tint(c,11)
   if (u+v)%6==1 and (u-v)%6==1:c=tint(c,-13)
  elif fn in ('north','south') and v%5==0:c=tint(c,-18)
 # Every fastener gets an engraved slot, not a solid square of colour.
 if n.startswith(('bolt_','grip_medallion')) and side:
  rr=math.hypot(s-.5,t-.5)
  c=dark if rr>.46 else metal
  if rr<.33 and abs(t-.5)<.065:c=dark
  if n.startswith('grip_medallion') and abs(s-.5)<.055 and rr<.33:c=dark
 # Moving drum surface has shallow flutes, bands and front/rear chamber embossing.
 if n.startswith('mag_drum'):
  if fn in ('north','south'):
   if .18<math.hypot(s-.5,t-.5)<.28:c=tint(c,-35)
  elif 'band' not in n:
   if .11<t<.2 or .8<t<.89:c=tint(c,-22)
   if .20<t<.23 or .77<t<.80:c=tint(c,21)
   if s<.08 or s>.92:c=tint(c,-15)
 # Rear sight horizontal serrations remain below the open notch.
 if n.startswith('sight_'):
  c=(27,29,29,255)
  if fn=='south' and int(t*max(1,round((e['to'][1]-e['from'][1])*T)))%3==0:c=(55,58,57,255)
  if fn=='south' and n in ('sight_rear_l','sight_rear_r') and .28<s<.72 and .28<t<.72:c=(193,217,171,255)
 if n.startswith('hammer') and fn=='up' and int(p[2]*T)%4==0:c=dark
 if side:
  if wid=='allegro_34':
   if n.startswith('shroud'):
    # White lightening slots, lower perforation rows and fine channel highlights.
    if box(247,32,370,42):
     c=(31,33,31,255)
     if box(251,34,276,39) or box(288,34,366,39):c=(224,226,216,255)
    if box(268,57,374,70):
     c=(172,178,167,255)
     for j in range(2):
      for i in range(11):
       cx=274+i*8.7+(j%2)*3;cy=60+j*6
       if disk(cx,cy,2.1):c=dark
       elif 2.1**2<(x-cx)**2+(y-cy)**2<2.8**2:c=(210,213,202,255)
    if line(242,47,370,47,.65):c=(118,121,111,255)
    if line(247,76,368,76,.65):c=(222,225,215,255)
   if n.startswith('frame_fore'):
    if disk(196,50,5):c=(62,72,44,255)
    if 3.8**2<(x-196)**2+(y-50)**2<5**2:c=(140,151,111,255)
   if n.startswith('frame_lower') and (rect(162,83,219,94) or line(160,95,220,95)):c=(107,109,103,255)
   if n.startswith('hammer') and 5.5<math.hypot(x-86,y-42)<6.5:c=dark
  elif wid=='ballyhoo_mk_27':
   if n.startswith('shroud_front'):
    # Brown upper shell with two inset securing straps and alternating rivets.
    if box(201,25,290,58):c=(91,79,65,255)
    if rect(202,26,290,57):c=(126,112,92,255)
    for a in (207,280):
     if abs(x-a)<1:c=(48,45,39,255)
     for b in (29,39,49):
      if box(a-3,b-1,a-1,b+1):c=(158,151,131,255)
    if box(303,25,316,53):
     c=(177,201,203,255)
     if box(306,28,312,49):c=(48,61,62,255)
    if line(293,60,315,22,1.8):c=(218,230,225,255)
   if n.startswith(('frame_front','barrel_lower')):
    if rect(163,36,190,79):c=(137,174,175,255)
    if line(166,77,192,77):c=(28,64,69,255)
   if n.startswith('front_lug'):
    if line(223,101,274,101):c=(91,92,81,255)
    for a in (232,258):
     if box(a-2,82,a+2,94):c=(114,143,146,255)
  elif wid=='lamia_hc2':
   if n.startswith(('shroud','barrel_block')):
    if box(205,49,317,65):
     c=(195,179,145,255)
     for j in range(3):
      for i in range(18):
       if disk(210+i*6+(j%2)*3,52+j*5,1.3):c=(32,33,30,255)
    # Two connected Omolon circles (not the former empty square glyphs).
    if box(230,26,281,46):
     c=(104,62,60,255)
     for a in (242,268):
      r=math.hypot(x-a,y-36)
      if 5.2<r<6.5:c=(196,180,152,255)
     if line(248,36,262,36,.55):c=(196,180,152,255)
    if rect(283,25,310,44):c=(135,90,80,255)
   if n.startswith(('grip_frame','shroud_rear')) and box(55,39,99,66):
    c=(104,62,60,255)
    r=math.hypot(x-76,y-49)
    if 6<r<8 or r<2:c=(208,195,172,255)
    if box(63,60,89,62):c=(208,195,172,255)
   if n.startswith('frame_mid') and box(120,83,174,94):
    c=(104,62,60,255)
    if textmark('OMOLON',124,87,1.35):c=(208,195,172,255)
   if n.startswith('lower_front'):
    if rect(232,82,267,97,1):c=(190,176,152,255)
    if rect(196,78,221,104,.6):c=(129,84,73,255)
    if box(237,87,245,91):c=(65,171,198,255)
    if box(251,87,259,91):c=(207,54,56,255)
   if n.startswith('mag_drum') and 'band' not in n and fn in ('west','east'):
    c=(101,126,108,255)
    if .24<t<.29:c=(174,194,173,255)
    if .7<t<.76:c=(57,77,64,255)
  elif wid in ('mos_ultima_ii','azimuth_dsu'):
   if n.startswith(('shroud','frame_lower')):
    ink=(159,177,187,255) if wid=='mos_ultima_ii' else (224,218,193,255)
    if rect(178,43,217,82,.65) or line(184,78,204,78) or rect(225,57,239,70,.6):c=ink
    if wid=='mos_ultima_ii' and rect(255,50,365,81,.7):c=ink
    if box(182,46,194,49):c=ink
    if box(184,47,192,48):c=dark
    if line(155,98,184,98) or line(184,98,196,88):c=ink
   if n.startswith('side_panel'):
    if rect(263,59,354,91,.7):c=(119,117,91,255)
    for a in (270,346):
     if box(a-2,65,a+2,85):c=(93,96,77,255)
     if box(a-1,68,a+1,83):c=(24,29,25,255)
   if n.startswith('top_rib'):
    if line(216,24,376,24,.6):c=(136,137,115,255)
  elif wid=='guseva_c':
   if n.startswith('shroud'):
    if box(200,47,258,57):
     c=(181,181,150,255)
     if textmark('HAKKE',205,49,1.5):c=(242,241,224,255)
    if rect(202,27,345,68,.65):c=(143,148,129,255)
    if line(207,66,336,66,.6):c=(246,244,231,255)
    if box(178,72,198,82):
     c=(44,48,42,255)
     if int((x-178)/2)%3==0 and y>79:c=(179,186,163,255)
   if n.startswith('grip_stock') and box(63,48,98,65):
    c=(214,217,197,255)
    if (71<x<75 or 84<x<88) and 51<y<62 or 68<x<91 and 55<y<58:c=(185,48,37,255)
   if n.startswith('light_body') and int(p[2]*T)%9 in (0,1):c=(34,36,32,255)
 # Lens, ports and end caps are authored on their own face, avoiding side-only detailing.
 if wid=='guseva_c' and n=='light_head' and fn=='north':
  r=math.hypot(s-.5,t-.5)
  c=(40,53,64,255) if r>.4 else (88,154,188,255)
  if .23<r<.32:c=(160,197,213,255)
  if .25<s<.38 and .23<t<.38:c=(235,247,250,255)
 if n.startswith('lamp_'):
  if n=='lamp_red':c=(207,54,56,255)
  elif n=='lamp_blue':c=(65,171,198,255)
  else:c=(190,176,152,255)
  if t<.22:c=tint(c,35)
 # One exact texel bright upper edge / dark lower seam for EVERY hand-painted face.
 _,_,ua,_,va,_=_FA[fn]
 w=max(1,round((e['to'][ua]-e['from'][ua])*T));h=max(1,round((e['to'][va]-e['from'][va])*T))
 i,j=int(s*w),int(t*h)
 if w>=3 and h>=3:
  if j==0:c=tint(c,24)
  elif j==h-1:c=tint(c,-24)
  elif i==0:c=tint(c,11)
  elif i==w-1:c=tint(c,-16)
 return c
