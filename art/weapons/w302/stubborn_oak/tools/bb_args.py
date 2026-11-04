"""Emit compact Blockbench MCP arguments from the reference data.

bb_args.py place <group>   -> place_cube elements for one group (geometry only)
bb_args.py uv <a:b>|<name> -> set_cube_uv faces per cube (hidden faces texture null)
bb_args.py groups          -> group names in order
bb_args.py js <outliner> <g1,g2..> -> compact list for W302OAK.place (risky_eval)
"""
import json, sys
from pathlib import Path
ref = json.loads((Path(__file__).resolve().parents[1] / 'reference/oak_reference.json').read_text())
els = [e for es in ref['parts'].values() for e in es]
TEX = 'stubborn_oak'
mode, sel = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '')
if mode == 'groups':
    seen = []
    for e in els:
        if e['group'] not in seen:
            seen.append(e['group'])
    print(' '.join(seen))
elif mode == 'js':
    gs = sys.argv[3].split(',')
    out = []
    for e in els:
        if e['group'] not in gs:
            continue
        c = {'n': e['name'], 'a': e['from'], 'b': e['to'],
             'f': {k: v['uv'] for k, v in e['faces'].items()}}
        r = e.get('rotation')
        if r:
            c['o'] = r['origin']
            c['r'] = [r['x'], r['y'], r['z']]
        out.append(c)
    print("W302OAK.place('%s', %s)" % (sel, json.dumps(out, separators=(',', ':'))))
elif mode == 'place':
    out = []
    for e in els:
        if e['group'] != sel:
            continue
        el = {'name': e['name'], 'from': e['from'], 'to': e['to']}
        r = e.get('rotation')
        if r:
            el['origin'] = r['origin']
            el['rotation'] = [r['x'], r['y'], r['z']]
        out.append(el)
    print(json.dumps(out, separators=(',', ':')))
else:
    if ':' in sel:
        a, b = map(int, sel.split(':'))
        pick = els[a:b]
    else:
        pick = [e for e in els if e['name'] == sel]
    for e in pick:
        faces = {}
        for k in ('north', 'east', 'south', 'west', 'up', 'down'):
            f = e['faces'].get(k)
            faces[k] = {'uv': f['uv'], 'texture': TEX} if f else {'texture': None}
        print(e['name'], json.dumps(faces, separators=(',', ':')))
