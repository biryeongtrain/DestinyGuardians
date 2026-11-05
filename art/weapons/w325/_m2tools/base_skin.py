"""Convert a base model json (with #0 texture) into a skin-format json for render_model.py review renders."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
A = ROOT / 'src/main/resources/assets/destiny'
src, out = sys.argv[1], sys.argv[2]
els = []
tex = None
for s in src.split(','):
    d = json.loads((A / 'models' / s).read_text())
    t = d['textures'].get('0') or d['textures'].get('layer0')
    while t and t.startswith('#'): t = d['textures'][t[1:]]
    tex = tex or t
    for e in d['elements']:
        e = dict(e); e['faces'] = {k: {'uv': v.get('uv', [0, 0, 1, 1]), 'texture': '#0'} for k, v in e['faces'].items()}
        els.append(e)
ns, path = tex.split(':')
Path(out).write_text(json.dumps({'texture_size': [16, 16], 'parts': {'body': els}}))
print(A / 'textures' / (path + '.png'))
