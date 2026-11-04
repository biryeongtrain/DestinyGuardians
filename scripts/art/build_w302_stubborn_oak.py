#!/usr/bin/env python3
"""W302 Stubborn Oak campaign shotgun: authored low-element model + world-projected atlas.

Two stages (stdlib + Pillow, deterministic):
  reference  rip-measured placement data + world-projected painted atlas ->
             art/weapons/w302/stubborn_oak/reference/oak_reference.json, texture PNG.
             The model itself is then built in Blockbench (own tab) from this data.
  convert    Blockbench java_block export (art/.../blockbench/stubborn_oak.bb_export.json)
             -> parts.json + HUD icon + manifest, checked against the reference.
Rip (SHA-pinned, read-only): ~/Downloads/tutorial-weapons/Stubborn Oak.
Layout contract v2: mindbender_s_ambition_adept.  No Blender/Gradle/game.
"""
import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art/weapons/w302/stubborn_oak'
sys.path.insert(0, str(ART / 'tools'))
sys.path.insert(0, str(ROOT / 'scripts'))
sys.dont_write_bytecode = True

import oak_bake  # noqa: E402
import oak_design  # noqa: E402
import oak_math  # noqa: E402
import oak_paint  # noqa: E402

ASSETS = ROOT / 'src/main/resources/assets/destiny'
TEX = ASSETS / 'textures/item/weapon/w302/stubborn_oak.png'
HUD = ASSETS / 'textures/item/hud/w302/ammo_stubborn_oak.png'
SKIN = ROOT / 'src/main/resources/destiny/weapon_skins/stubborn_oak.json'
SRC_DIR = Path.home() / 'Downloads/tutorial-weapons/Stubborn Oak/Stubborn Oak'
SOURCES = {
    'Stubborn Oak.blend': '2eee2c92a67227958b1828d94ed5bb57b12da3001f65a534cbafe0eb6dce8b45',
    'Stubborn Oak.fbx': '98f10506575f7bc9efc303b0009b81dc72b84bb8afb84e35981d16c6d6854836',
    'SOBarrel_Diffuse.png': '8477db85137da291b531b1b6a216c10043c94cd09cf792848515921ed9cd6632',
    'SOGrip_Diffuse.png': 'f2c1a4f4027d3d235688d115b77b018fd4c07d53c538a7ad2c18e1a58b276b4f',
    'SOSight_Diffuse.png': 'e7c5db3edad60e5654ddefcdf57551b71359c28fa0776dd69f2f084e81265ce0',
    'SOStock_Diffuse.png': '130392d0a1b91f302b66b56b8d73412f15bf81e92ec7db7f83cff50b7101aa3d',
}
CONTRACT = 'destiny:weapon_insert_w221_mindbender_s_ambition_adept body (layout v2)'
REF = ART / 'reference/oak_reference.json'
EXPORT = ART / 'blockbench/stubborn_oak.bb_export.json'
CONTRACT_MODEL = 'models/weapon_insert_w221_mindbender_s_ambition_adept/mindbender_s_ambition_adept_body.json'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def jbytes(v):
    return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def pbytes(im):
    out = io.BytesIO()
    im.save(out, 'PNG', compress_level=9, optimize=False)
    return out.getvalue()


def check_sources():
    seen = {}
    for name, want in SOURCES.items():
        got = sha((SRC_DIR / name).read_bytes())
        if got != want:
            raise SystemExit(f'source drift: {name} {got}')
        seen[name] = got
    return seen


def reference(paint_name='paint'):
    solids = [oak_math.realize(s) for s in oak_design.design()]
    names = [s.name for s in solids]
    assert len(names) == len(set(names)), 'duplicate element names'
    faces = oak_bake.collect(solids)
    used_h = oak_bake.pack(faces)
    paint = getattr(oak_paint, paint_name, None) or oak_paint.paint_flat
    atlas = oak_bake.bake(faces, paint)
    parts = oak_bake.elements(solids, faces)
    groups = {s.name: s.group for s in solids}
    for es in parts.values():
        for e in es:
            e['group'] = groups[e['name']]
            for v in e['from'] + e['to']:
                assert -16 <= v <= 32, e['name']
    doc = {'note': 'Reference placement for the Blockbench build (not the shipped model).',
           'texture_size': [oak_bake.ATLAS, oak_bake.ATLAS], 'atlas_rows_used': used_h,
           'texels_per_px': oak_bake.D, 'sources_sha256': check_sources(), 'parts': parts}
    return {REF: jbytes(doc), TEX: pbytes(atlas)}, doc


def write(outputs, verify):
    if verify:
        bad = [str(p) for p, b in outputs.items() if not p.is_file() or p.read_bytes() != b]
        if bad:
            raise SystemExit('stale: ' + ', '.join(bad))
        return
    for p, b in outputs.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)


def clean(e):
    out = {'name': e['name'], 'from': [round(v, 6) for v in e['from']],
           'to': [round(v, 6) for v in e['to']]}
    r = e.get('rotation')
    if r:
        if 'axis' in r:
            ang = {k: (r['angle'] if r['axis'] == k else 0) for k in 'xyz'}
        else:
            ang = {k: r.get(k, 0) for k in 'xyz'}
        if any(abs(v) > 1e-9 for v in ang.values()):
            out['rotation'] = {'origin': [round(v, 6) for v in r['origin']],
                               **{k: round(v, 6) + 0.0 for k, v in ang.items()}}
    faces = {}
    for k in ('north', 'east', 'south', 'west', 'up', 'down'):
        f = e.get('faces', {}).get(k)
        if f and f.get('texture') is not None:
            faces[k] = {'uv': [round(v, 6) for v in f['uv']], 'texture': '#0'}
            if f.get('rotation'):
                faces[k]['rotation'] = f['rotation']
    out['faces'] = faces
    return out


def convert(ref):
    exp = json.loads(EXPORT.read_text())
    els = [clean(e) for e in exp['elements']]
    refs = {e['name']: e for es in ref['parts'].values() for e in es}
    drift = []
    for e in els:
        r = refs.get(e['name'])
        if r is None:
            drift.append((e['name'], 'not in reference'))
            continue
        d = max(abs(a - b) for a, b in zip(e['from'] + e['to'], r['from'] + r['to']))
        if d > 1e-3:
            drift.append((e['name'], 'moved %.4f' % d))
    model = {'credit': 'W302 Stubborn Oak, Blockbench-authored solids / face UV',
             'textures': {'0': 'destiny:item/weapon/w302/stubborn_oak',
                          'particle': 'destiny:item/weapon/w302/stubborn_oak'},
             'elements': els}
    import build_weapon_hud_w112 as w112
    hud_img, hud_stats = w112.render(model, 'shotgun')
    parts_bytes = jbytes({'texture_size': ref['texture_size'], 'parts': {'body': els}})
    outputs = {ART / 'parts.json': parts_bytes, SKIN: parts_bytes,
               ART / 'preview_model.json': jbytes(model), HUD: w112.png_bytes(hud_img)}
    manifest = {
        'batch': 'W302', 'skin': 'stubborn_oak', 'layout_contract': CONTRACT,
        'authoring': 'Blockbench 5.1.4 java_block project (agent-owned tab) via MCP; Python only '
                     'for rip measurement/reference data, atlas paint and export conversion',
        'elements': {'body': len(els)}, 'element_total': len(els),
        'faces': sum(len(e['faces']) for e in els),
        'rotated_elements': sum(1 for e in els if 'rotation' in e),
        'reference_drift': drift, 'sources_sha256': ref['sources_sha256'], 'hud': hud_stats,
        'blockbench_export_sha256': sha(EXPORT.read_bytes()),
        'outputs_sha256': {str(p.relative_to(ROOT)): sha(b) for p, b in outputs.items()},
        'texture_sha256': sha(TEX.read_bytes()),
        'generator_sha256': sha(Path(__file__).read_bytes()),
        'tools_sha256': {p.name: sha(p.read_bytes()) for p in sorted((ART / 'tools').glob('*.py'))},
    }
    outputs[ART / 'manifest.json'] = jbytes(manifest)
    return outputs, manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=('reference', 'convert'))
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--paint', default='paint')
    a = ap.parse_args()
    if a.stage == 'reference':
        outputs, doc = reference(a.paint)
        write(outputs, a.verify)
        print('reference', sum(len(v) for v in doc['parts'].values()), 'elements')
    else:
        outputs, m = convert(json.loads(REF.read_text()))
        write(outputs, a.verify)
        print(json.dumps({k: m[k] for k in ('element_total', 'faces', 'rotated_elements',
                                            'reference_drift')}))


if __name__ == '__main__':
    main()
