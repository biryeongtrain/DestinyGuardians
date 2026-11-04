#!/usr/bin/env python3
"""Inspect preserved real-framebuffer red direction markers; never generates expected pixels.
Uses Pillow. Native states bracket captures; no exact tick synchronization is claimed.
"""
from pathlib import Path
import json,sys
from PIL import Image
root=Path(sys.argv[1]);output=Path(sys.argv[2]);rows=[]
for name,(ex,ey) in {'front':(0,-1),'right':(1,0),'back':(0,1),'left':(-1,0)}.items():
 p=root/'frames'/('damage-'+name+'.png');im=Image.open(p).convert('RGB');cx,cy=im.width/2,im.height/2
 points=[]
 for y in range(int(cy-145),int(cy+145)):
  for x in range(int(cx-145),int(cx+145)):
   r,g,b=im.getpixel((x,y))
   if r>180 and g<145 and b<145 and r>1.35*g:points.append((x-cx,y-cy))
 if not points:raise SystemExit('No marker pixels: '+str(p))
 dx=sum(p[0]for p in points)/len(points);dy=sum(p[1]for p in points)/len(points)
 projected=dx*ex+dy*ey;cross=dx*ey-dy*ex
 rows.append(dict(direction=name,file=str(p),pixels=len(points),centroidOffset=[dx,dy],expectedScreenDirection=[ex,ey],correct=projected>40 and abs(cross)<35))
report=dict(source='Real Vision framebuffer PNGs, not synthesized previews',cardinals=rows,allCardinalsCorrect=all(r['correct']for r in rows),exactFrameTick=False)
output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if not report['allCardinalsCorrect']:sys.exit(1)
