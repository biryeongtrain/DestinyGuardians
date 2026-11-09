"""Remove exclusive orphan pose leaves, refresh manifests, write source-bound records."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AS=ROOT/'src/main/resources/assets/destiny'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def strings(obj):
 if isinstance(obj,str):yield obj
 elif isinstance(obj,dict):
  for val in obj.values():yield from strings(val)
 elif isinstance(obj,list):
  for val in obj:yield from strings(val)
for w in sys.argv[1:] or ['crimson','thorn','outbreak_perfected']:
 ad=ROOT/'art/weapons/w350'/w;refs=set()
 for ns in ['weapon_w350','weapon_aim_w350','weapon_reload_w350']:
  for p in (AS/'items'/ns/w).rglob('*.json'):refs.update(strings(json.loads(p.read_text())))
 for p in [AS/f'items/weapon/{w}.json',AS/f'items/weapon_aim_w350/{w}.json',AS/f'items/weapon_reload_w350/{w}.json']:refs.update(strings(json.loads(p.read_text())))
 removed=[]
 for p in (AS/f'models/weapon_w350/{w}/hands').glob('*.json'):
  ref='destiny:'+str(p.relative_to(AS/'models')).removesuffix('.json')
  if ref not in refs:removed.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p)));p.unlink()
 paths=set()
 for branch in ['models','items']:
  for ns in ['weapon_w350','weapon_aim_w350','weapon_reload_w350']:paths.update((AS/branch/ns/w).rglob('*.json'))
 paths.update([AS/f'items/weapon/{w}.json',AS/f'items/weapon_aim_w350/{w}.json',AS/f'items/weapon_reload_w350/{w}.json',AS/f'textures/item/weapon/w350/{w}.png',AS/f'textures/item/weapon/w350/{w}_hud.png'])
 manifest=json.loads((ad/'manifest.json').read_text());manifest['outputsSha256']={str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
 manifest['orphanPoseLeafCleanup']=dict(removed=removed,reason='Only own transform-hashed leaves absent from all current own item graphs; R1 render/design proof preserved.')
 manifest['canonicalPaletteReference']=dict(url=json.load(open('/tmp/exotic-expansion-20261109/data/icon-paths.json'))[{'crimson':'Crimson','thorn':'Thorn','outbreak_perfected':'Outbreak Perfected'}[w]],note='Pinned official Bungie base inventory icon; supplied grey source shader is geometry/relief evidence only for Outbreak.')
 (ad/'manifest.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n');print(w,'removed',len(removed),'exclusive unused hand leaves; runtime files',len(paths))
