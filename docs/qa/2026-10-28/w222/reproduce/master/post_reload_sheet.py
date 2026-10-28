from pathlib import Path
from PIL import Image,ImageDraw
import sys
phase=sys.argv[1];assert phase in ('first','second')
q=Path('/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w222')
source=q/('vision1' if phase=='first' else 'vision2')
ids=['biting_winds', 'whispering_slab', 'long_arm', 'nezarec_s_whisper']
out=Image.new('RGB',(2562,1024),(23,27,34));draw=ImageDraw.Draw(out)
for i,w in enumerate(ids):
 im=Image.open(source/'frames'/('w222-'+w+'-after-reload.png')).convert('RGB');im.thumbnail((854,480))
 x=i%3*854;y=i//3*512;out.paste(im,(x,y+32));draw.text((x+8,y+8),w+' post reload',fill='white')
out.save(q/(phase+'-post-reload-review.png'))
