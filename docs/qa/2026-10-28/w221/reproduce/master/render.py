from pathlib import Path
import json
from PIL import Image,ImageDraw
root=Path('/Users/qf/IdeaProjects/DestinyGuardians')
raw=Path('/private/tmp/destiny-w221-source')
q=raw/'sheets';q.mkdir(exist_ok=True)
for group,tag in [['shotgun_2eb0529e', '80A8A3F1'], ['rocket_launcher_1a221f25', '80A8A1A2'], ['hand_cannon_5b24a8d7', '80A8A53D']]:
 d=json.loads((raw/f'{group}.json').read_text());frames=d['actions'][tag]['frames'];chosen=[frames[i] for i in [0,12,24,36,48,60]]
 points=[[m[i][3] for i in range(3)] for f in frames for k,m in f['joints'].items() if k!='utility'];lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
 im=Image.new('RGB',(1440,640),(16,24,34));draw=ImageDraw.Draw(im)
 for n,f in enumerate(chosen):
  x0=(n%3)*480;y0=(n//3)*320;draw.text((x0+10,y0+8),f"{tag} source chain / p={f['progress']:.2f}",fill='white')
  for v,axes in enumerate([(0,2),(1,2)]):
   draw.text((x0+v*240+10,y0+32),'XZ' if v==0 else 'YZ',fill=(150,160,180))
   scale=min(210/max(.01,hi[axes[0]]-lo[axes[0]]),220/max(.01,hi[axes[1]]-lo[axes[1]]))
   def xy(k):
    m=f['joints'][k];return(x0+v*240+15+(m[axes[0]][3]-lo[axes[0]])*scale,y0+285-(m[axes[1]][3]-lo[axes[1]])*scale)
   for side,color in [('right',(255,180,90)),('left',(90,210,255))]:
    names=[side+'Shoulder',side+'Elbow',side+'Wrist'];draw.line([xy(k) for k in names],fill=color,width=3)
    for k in names:
     x,y=xy(k);draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
  draw.text((x0+10,y0+304),'SOURCE BONES ONLY; no mesh/camera/gameplay claim',fill=(150,160,180))
 im.save(q/(group+'-'+tag+'-upper-chain.png'))
print('Rendered source shoulder/elbow/wrist chains')
