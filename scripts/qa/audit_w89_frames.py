#!/usr/bin/env python3
"""Read-only critical wash measurements from actual framebuffer PNGs.
No fabricated frames; healthy reference and capture bracket limits kept explicit.
"""
from pathlib import Path
import json,sys,math
from PIL import Image,ImageStat
root=Path(sys.argv[1]);out=Path(sys.argv[2])
base=Image.open(root/'frames/healthy-before.png').convert('RGB')
w,h=base.size
# Side world regions exclude the health bar, crosshair, held weapon and lower HUD.
regions={'left':(0,int(h*.2),int(w*.12),int(h*.7)),
         'right':(int(w*.88),int(h*.2),w,int(h*.7)),
         'center':(int(w*.44),int(h*.3),int(w*.56),int(h*.55))}
def stats(im,box):
 a=list(base.crop(box).getdata());b=list(im.crop(box).getdata())
 ds=[(q[0]-(q[1]+q[2])/2)-(p[0]-(p[1]+p[2])/2) for p,q in zip(a,b)]
 return {'meanRedExcessChange':sum(ds)/len(ds),'pixels':len(ds),'fractionDeltaAbove5':sum(d>5 for d in ds)/len(ds)}
rows=[]
for hp in (6,5,1):
 phases=json.loads((root/f'hp-{hp}-phases.json').read_text())
 for capture in phases:
  path=root/capture['file'];im=Image.open(path).convert('RGB');assert im.size==base.size
  r={name:stats(im,box)for name,box in regions.items()}
  rows.append({'hp':hp,'file':capture['file'],'bracketModels':[capture[k]['model'] for k in ('serverBefore','serverAfter')],
               'bracketTicks':[capture[k]['tick'] for k in ('serverBefore','serverAfter')],
               'regions':r,'visibleBothSideWash':all(r[k]['meanRedExcessChange']>5 and r[k]['fractionDeltaAbove5']>.2 for k in ('left','right'))})
healed=Image.open(root/'frames/healthy-after.png').convert('RGB')
clean={name:stats(healed,box)for name,box in regions.items()}
report={'source':'Actual Vision framebuffer PNGs, not offline previews','resolution':[w,h],'regions':regions,'samples':rows,
        'allSamplesVisible':all(r['visibleBothSideWash'] for r in rows),'healed':clean,
        'healedSideWashAbsent':all(abs(clean[k]['meanRedExcessChange'])<2 and clean[k]['fractionDeltaAbove5']<.05 for k in ('left','right')),
        'exactFrameTick':False,'centerOcclusionPolicy':'Center rectangle measured separately; protected center ellipse is verified in asset tests.',
        'wholeGoalAchieved':False}
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='samples'}))
if not report['allSamplesVisible'] or not report['healedSideWashAbsent']:sys.exit(1)
