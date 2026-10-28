from pathlib import Path
from PIL import Image,ImageDraw
import json,sys
root=Path('/private/tmp/destiny-w223-pass2-native');out=root/'screenshots';out.mkdir(exist_ok=True)
ids=sys.argv[1:] or ['nezarec_s_whisper'];records=[]
thumb=(854,480)
def active_reload(label):
 p=root/'sequences'/(label+'-reload.json')
 if not p.exists():return []
 raw=json.loads(p.read_text());data=json.loads(raw.get('stdout') or '{}')
 return [root/'frames'/c['file'] for c in data.get('captures',[]) if any(mark in c['before'].get('interaction',{}).get('mainModel','') for mark in ('weapon_reload_', 'weapon_insert_', 'weapon_izanagi_')) and any(mark in c['after'].get('interaction',{}).get('mainModel','') for mark in ('weapon_reload_', 'weapon_insert_', 'weapon_izanagi_'))]

for weapon in ids:
 label='w223-'+weapon;cols=[]
 hip=root/'frames'/(label+'-hip.png');cols.append(('hip',hip))
 for mode in ['ads','reload']:
  files=active_reload(label) if mode=='reload' else sorted((root/'frames').glob(label+'-'+mode+'-sample-*.png'))
  if files:cols.append((mode,files[len(files)//2]))
 sheet=Image.new('RGB',(854*len(cols),512),(23,27,34));draw=ImageDraw.Draw(sheet)
 for i,(mode,path) in enumerate(cols):
  im=Image.open(path).convert('RGB');im.thumbnail(thumb);sheet.paste(im,(i*854,32));draw.text((i*854+10,10),weapon+' / '+mode,fill='white');records.append(dict(weapon=weapon,mode=mode,file=str(path.relative_to(root))))
 sheet.save(out/(weapon+'-review.png'))
 # Several bracketed real frames, not animation-tick synchronized.
 files=active_reload(label)
 if files:
  chosen=[files[round((len(files)-1)*t/4)] for t in range(5)]
  sheet=Image.new('RGB',(854*3,512*2),(23,27,34));draw=ImageDraw.Draw(sheet)
  for i,path in enumerate(chosen):
   im=Image.open(path).convert('RGB');im.thumbnail(thumb);x=(i%3)*854;y=(i//3)*512;sheet.paste(im,(x,y+32));draw.text((x+8,y+10),path.name,fill='white')
  sheet.save(out/(weapon+'-reload.png'))
(out/'selected-frames.json').write_text(json.dumps(records,indent=2)+'\n')
