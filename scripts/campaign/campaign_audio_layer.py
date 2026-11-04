"""W300/W303 reviewed audio layer for the sound regression tests.

Writes art/campaign/w300/sounds-fragment.json (events added on top of the committed W282 index: guardian_rises.*,
guardian_down.*) and art/campaign/w300/audio-inventory.json (their OGG files). Re-run after adding campaign audio.
"""
import json, os, subprocess
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
os.chdir(ROOT)
PREFIXES = ('guardian_rises.', 'guardian_down.')
cur = json.load(open('src/main/resources/assets/destiny/sounds.json'))
frag = {k: v for k, v in cur.items() if k.startswith(PREFIXES)}
json.dump(frag, open('art/campaign/w300/sounds-fragment.json', 'w'), ensure_ascii=False, indent=2)
import hashlib
paths = []
for d in ('src/main/resources/assets/destiny/sounds/guardian_rises', 'src/main/resources/assets/destiny/sounds/guardian_down'):
    for r, _, fs in os.walk(d):
        paths += [os.path.join(r, f).replace(os.sep, '/') for f in fs]
music = ['src/main/resources/assets/destiny_music/sounds/tutorial_rise.ogg']
def pin(p):
    b = open(p, 'rb').read()
    return {'path': p, 'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}
json.dump({'paths': sorted(paths) + music, 'pins': [pin(p) for p in sorted(paths)]},
          open('art/campaign/w300/audio-inventory.json', 'w'), indent=2)
print(len(frag), 'events', len(paths), 'files')
