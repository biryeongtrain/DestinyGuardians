"""Face-specific source artwork, controlled material palette, and narrow real edge treatment."""
import math
from PIL import ImageFilter

def finish(baker,faces,k):
 for name,fn,img,clear,e,others,painted in faces:
  if clear:continue
  px=img.load();raw=img.copy();rp=raw.load();role=e['role'];base=baker.D.MATERIALS[role]['color'];w,h=img.size
  # Low frequency bone fields remain calm. Fine carved relief remains only where source contains it.
  smooth=raw.convert('L').filter(ImageFilter.GaussianBlur(2));sp=smooth.load()
  for i in range(w):
   for j in range(h):
    rc=rp[i,j];lum=.299*rc[0]+.587*rc[1]+.114*rc[2];c=base[:];fac=1
    p=k.face_point(e,fn,(i+.5)/w,(j+.5)/h);wp=baker.D.model2world(name,p)
    # Main flank decoration follows the original continuous navy slash; opposite flank has its own view.
    if role in ('ivory','ivory_edge','ivory_dark','grip'):
     navy=rc[2]>rc[0]*1.11 and rc[2]>rc[1]*1.055 and rc[2]-rc[0]>7 and sum(rc[:3])<390
     if navy and (fn in ('east','west','up','down') or e.get('_surface')):
      c=[39,46,72];fac=.92 if lum<30 else 1.04
     else:
      # Actual shallow sculpted bone seams, not synthetic airbrush edge bands.
      relief=lum-sp[i,j]
      if relief<-18 and lum<120:fac=.92
      elif relief>22:fac=1.025
      else:fac=1
      # Source frontstrap ribs stay limited to the grip's narrow anterior edge.
      if 'frontstrap' in name and fn in ('east','west'):
       srcpy=170.5-(wp[2]-.056399501860141754)*1400
       if int(srcpy)%7<2:fac=.76
    elif role=='navy':
     # Re-authored source spider engraving; it is a seal, never a generic repeated noise pattern.
     c=[40,43,77]
     if 'medallion' in name and fn in ('east','west'):
      sx=(wp[1]+.12476199120283127)*1400+257.5-441
      sy=170.5-(wp[2]-.056399501860141754)*1400-257
      rr=math.hypot(sx,sy)
      paths=[[(0,-22),(-4,-9),(-1,17),(3,-9),(0,-22)],
       [(-3,-10),(-13,-16),(-17,-23)],[ (3,-10),(13,-16),(16,-23)],
       [(-4,-5),(-17,-10),(-22,-6),(-15,-2),(-5,-1)],
       [(4,-5),(17,-10),(22,-6),(15,-2),(5,-1)],
       [(-3,5),(-14,13),(-15,22)],[(3,5),(14,13),(15,22)],
       [(-2,10),(-7,19),(-7,25)],[(2,10),(7,19),(7,25)]]
      def dist(x,y):
       dd=100
       for path in paths:
        for (ax,ay),(bx,by) in zip(path,path[1:]):
         dx=bx-ax;dy=by-ay;t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)));dd=min(dd,math.hypot(x-ax-t*dx,y-ay-t*dy))
       return dd
      if 24.2<rr<25.5 or dist(sx,sy)<1.25:c=[24,27,52]
      elif 22.8<rr<24 or dist(sx,sy+1.3)<1.35:c=[61,64,98]
    elif role in ('steel','steel_edge','bolt'):
     # Constant directional planes provide metallic section changes; no repeated sawtooth gradients.
     fac={'up':1.13,'down':.73,'north':.89,'south':.86,'east':1.00,'west':.98}[fn]
     if 'barrel/' in name and fn in ('east','west'):
      # Two longitudinal machining bands, source-specific exposed barrel only.
      ss=(j+.5)/h
      if .16<ss<.19:fac*=1.12
      if .77<ss<.80:fac*=.88
    elif role.startswith('gold'):
     fac={'up':1.13,'down':.79,'north':.9,'south':.94,'east':1.01,'west':.98}[fn]
    elif role=='bore':fac=.7
    px[i,j]=tuple(max(0,min(255,round(v*fac))) for v in c)+(255,)
  if e.get('_surface'):continue
  # Exactly one texel on exposed boundaries. Keep matte ivory restrained and metal crisp.
  o,u,v=k.face_frame(e,fn);lu=math.dist((0,0,0),u) or 1;lv=math.dist((0,0,0),v) or 1
  flags=[]
  for ss,tt in ((-.004,.5),(1.004,.5),(.5,-.004),(.5,1.004)):
   ss=.5+(ss-.5)*(1+.06/lu) if ss!=.5 else .5;tt=.5+(tt-.5)*(1+.06/lv) if tt!=.5 else .5
   flags.append(not any(k.inside(x,k.face_point(e,fn,ss,tt,push=-.015)) for x in others))
  hi=.12 if role in ('steel','steel_edge','gold','gold_edge') else .045
  lo=-.17 if role in ('steel','steel_edge','gold','gold_edge') else -.075
  def tint(i,j,f):px[i,j]=k.lighten(px[i,j],f)+(255,)
  if w>2 and h>2:
   if flags[2]:
    for i in range(w):tint(i,0,hi)
   if flags[3]:
    for i in range(w):tint(i,h-1,lo)
   if flags[0]:
    for j in range(h):tint(0,j,hi*.5)
   if flags[1]:
    for j in range(h):tint(w-1,j,lo*.5)
