#!/usr/bin/env python3
"""W154 MG feed correction and owned-output driver; offline numpy/Pillow only.

Run with bundled Python -B. Legacy generate() entry points use this transform,
so regeneration cannot silently restore the old sideways/floating belts.
Historical W114 resources and shared pack/sight derivatives stay master-owned.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSET = 'src/main/resources/assets/destiny/'
MANIFEST = 'art/weapons/w154/machine-gun-feed.json'
IDS = ('hammerhead', 'fixed_odds', 'retrofit_escapade')
PATHS = {
    'hammerhead': [(8.40,12.32),(8.98,12.29),(9.47,12.02),(9.80,11.60),
                   (10.00,11.13),(10.08,10.65),(10.06,10.17),(9.98,9.62)],
    'fixed_odds': [(8.42,11.45),(8.98,11.42),(9.42,11.18),(9.70,10.79),
                   (9.86,10.34),(9.92,9.87),(9.94,9.40)],
    'retrofit_escapade': [(7.26,12.14),(6.78,12.13),(6.32,11.94),(5.99,11.59),
                          (5.79,11.16),(5.70,10.69),(5.72,10.22)],
}


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def png(image):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


def correct_parts(weapon, parts):
    """Replace only belt semantics; preserve every other authored spec verbatim.

    Feed travel lies in XY. All cases, shoulders and tips lie along Z, with
    decreasing Z toward the muzzle. Endpoints overlap the existing tray/port
    and magazine saddle/recess; no new body, drum, UV motif or reload pivot.
    """
    target = parts['magazine'] if weapon == 'hammerhead' else parts['full']
    target[:] = [s for s in target if s['group'] != 'belt']

    def cube(name, pos, size, material, motif, turn=None):
        geometry = dict(name=name, **{
            'from':[round(a-b/2,7) for a,b in zip(pos,size)],
            'to':[round(a+b/2,7) for a,b in zip(pos,size)]})
        if turn:
            geometry['rotation'] = dict(origin=list(pos), x=0, y=0, z=turn)
        target.append(dict(geometry=geometry, material=material, group='belt', motif=motif))

    points = PATHS[weapon]
    if weapon == 'hammerhead':
        z, link_z = 3.99, 4.26
        for i,(x,y) in enumerate(points):
            cube(f'belt_round_{i}', [x,y,z], [.39,.26,1.37], 'belt', 'cartridge')
            cube(f'belt_tip_{i}', [x,y,3.20], [.25,.20,.35], 'red_edge', 'tip')
            cube(f'belt_link_{i}', [x,y,link_z], [.47,.34,.23], 'steel', 'links')
    elif weapon == 'fixed_odds':
        z, link_z = 4.68, 4.77
        for i,(x,y) in enumerate(points):
            cube(f'belt_case_{i}', [x,y,z], [.31,.29,.86], 'brass', 'case')
            cube(f'belt_copper_shoulder_{i}', [x,y,4.12], [.27,.25,.30], 'copper', 'copper')
            cube(f'belt_copper_tip_{i}', [x,y,3.90], [.14,.14,.18], 'copper', 'copper')
            cube(f'belt_link_{i}', [x,y,link_z], [.41,.39,.23], 'steel', 'link')
    else:
        z, link_z = 4.20, 4.40
        for i,(x,y) in enumerate(points):
            cube(f'round_case_{i}', [x,y,z], [.27,.27,1.17], 'copper', 'round')
            # Facet turns around the case's long Z axis, not around X.
            cube(f'round_facet_{i}', [x,y,z], [.27,.27,1.17], 'copper', 'round', 45)
            cube(f'round_shoulder_{i}', [x,y,3.48], [.21,.21,.30], 'brass', 'bullet')
            cube(f'round_tip_{i}', [x,y,3.205], [.12,.12,.27], 'copper', 'bullet')
            cube(f'round_link_{i}', [x,y,link_z], [.37,.37,.22], 'link', 'links')
        # Rear lip overlaps the shoulder at Z=4.95. The first case overlaps
        # its inner face, making the existing shoulder an actual feed throat.
        cube('feed_port_rear_lip', [7.14,12.14,4.85], [.52,.43,.24], 'teal', 'chassis')
    for i,((x,y),(nx,ny)) in enumerate(zip(points,points[1:])):
        material = 'steel' if weapon == 'hammerhead' else 'black' if weapon == 'fixed_odds' else 'link'
        motif = 'link' if weapon == 'fixed_odds' else 'links'
        cube(f'feed_join_{i}', [(x+nx)/2,(y+ny)/2,link_z],
             [math.hypot(nx-x,ny-y)+.10,.14,.18], material, motif,
             math.degrees(math.atan2(ny-y,nx-x)))
    return dict(revision='W154', travel_plane='XY', muzzle_axis=[0,0,-1],
                case_axis=[0,0,1], tip_axis=[0,0,-1], path_xy=[list(p) for p in points],
                link_z=link_z, rounds=len(points), representation='rigid linked cartridges',
                generator='scripts/fix_belt_feed_w154.py', generator_sha256=sha(Path(__file__).read_bytes()))


def renderer():
    # Inert CPU rasterizer; never opens the user's editor/game or DCC state.
    return runpy.run_path(str(ROOT/'scripts/generate_surface_w123_hammerhead.py'))


def comparison_sheet(weapon, design, model, texture):
    h = renderer()
    tri = h['model_triangles']({'full':model}, texture)
    points = np.concatenate([h['vertices'](e) for e in model['elements']])
    sheet = Image.new('RGB',(1800,1580),'#171f29')
    draw = ImageDraw.Draw(sheet)
    def label(x,y,text,size=21):
        draw.text((x,y),text,fill='#edf1f4',font_size=size)
    label(20,12,weapon.upper()+' / W154 FEED / OFFLINE CPU REVIEW',29)
    photo=Image.open('/tmp/destiny-weapons-w31/references/'+weapon+'.jpg').convert('RGB')
    photo.thumbnail((940,480)); sheet.paste(photo,(15,58))
    for i,text in enumerate([
        'Actual default photo / original body and material motifs retained',
        'Cartridge tips point toward muzzle: -Z',
        'Linked XY feed: receiver port -> magazine opening',
        f'{len(model["elements"])} assembled elements / limit 1000',
        'Native HIP / ADS / sideview / reload: PENDING MASTER',
        'W114 pinned geometries and shared manifests preserved']):
        label(970,105+i*54,text,20)
    side = 1 if weapon != 'retrofit_escapade' else -1
    for col,(title,cam) in enumerate([
        ('FULL / FEED SIDE',[side,0,0]),
        ('FULL / FRONT OBLIQUE',[side,.48,-.68]),
        ('FULL / OPPOSITE REAR',[-side,.35,.65])]):
        im,_=h['render'](tri,cam,h['frame'](points,cam,600,350),(600,350))
        sheet.paste(im,(600*col,520));label(600*col+12,530,title,18)
    # Include the surrounding body and magazine in the crop; isolated rounds
    # cannot prove the two attachment points or show housing intersections.
    specs=[s for ss in design['parts'].values() for s in ss if s['group']=='belt']
    bp=np.concatenate([h['vertices'](s['geometry']) for s in specs])
    for col,(title,cam) in enumerate([
        ('FEED / SIDE / RECEIVER TO MAG',[side,0,0]),
        ('FEED / FRONT OBLIQUE',[side,.40,-.75]),
        ('FEED / REAR / ROUND ENDS',[side,.25,.80])]):
        im,_=h['render'](tri,cam,h['frame'](bp,cam,600,570),(600,570))
        sheet.paste(im,(600*col,900));label(600*col+12,910,title,18)
    label(20,1502,'Feed detail keeps surrounding receiver + magazine visible; cases and links are separate opaque solids.',21)
    label(20,1540,'Static art only. No native parser/pack, game input, belt deformation, hand IK or performance certification.',20)
    return png(sheet)


def finish_outputs(weapon, outputs, include_comparison):
    """Update owned provenance/review after the legacy source compiler runs."""
    art=f'art/weapons/w123/{weapon}/'
    design=json.loads(outputs[art+'design.json'])
    model=json.loads(outputs[ASSET+f'models/weapon_surface_w123/{weapon}.json'])
    if include_comparison:
        texture=Image.open(io.BytesIO(outputs[ASSET+f'textures/item/weapon/w123/{weapon}.png'])).convert('RGBA')
        outputs[art+'comparison.png']=comparison_sheet(weapon,design,model,texture)
    count=len(model['elements'])
    assert count<=1000
    outputs[art+'review.md']=(f'# {weapon} W154 feed correction\n\n'
        f'{count} assembled opaque cuboids (0 triangle adapters; cap 1000). '
        f'{design["belt_feed_w154"]["rounds"]} linked rounds follow an XY curve from the receiver into the magazine. '
        'All tips point along -Z, parallel to the muzzle. The final round is seated in the existing magazine opening; '
        'exposed intermediate rounds form the photographed feed, not loose ammunition outside the housing.\n\n'
        'The original semantic body, sight, magazine housing, material palette, display, scale, anchor and pivot are preserved. '
        'The face atlas is deterministically repacked for the new belt solids; existing material/UV motifs remain authored by the original compiler. '
        'Retrofit case band paint uses longitudinal Z after the axis correction. '
        'Hammerhead full = body + magazine + cover; the rigid corrected belt belongs to magazine.\n\n'
        'References opened: actual /tmp/destiny-weapons-w31/references/ID.jpg for all three MGs, pre-change comparison.png files, '
        'and main sealed docs/qa/2026-10-26/w153/ads-heavy.png. '
        'comparison.png shows actual photo, three full views, and three receiver-to-magazine detail views with housing context.\n\n'
        'Reproduce using bundled Python -B scripts/fix_belt_feed_w154.py; --verify compares every generated output. '
        'Targeted regression: scripts/tests/test_belt_feed_w154.py. Historical tests are not claimed as all passing. '
        'Pinned W114 reload source/frames and shared surface manifest are unchanged; master must derive shared pack, W151 pulse/ADS and W153 MG body/ADS.\n\n'
        'Native HIP/ADS, static sideview and representative reload remain pending master, as do parser/pack and 10-20-display observations. '
        'Offline geometry/UV/CPU images do not prove native acceptance. Static cuboid noses and rigid links approximate the photographed rounds; no new dynamic belt deformation, IK, audio or combat work.\n').encode()
    manifest=json.loads(outputs[art+'manifest.json'])
    manifest.update(revision='W154',stage='W154',native_accepted=False,
                    belt_feed_w154=design['belt_feed_w154'],
                    validation=dict(targeted_python='scripts/tests/test_belt_feed_w154.py',
                                    native='pending master',historical_tests='not claimed all passing'))
    manifest['output_sha256']={p:sha(b) for p,b in sorted(outputs.items()) if p!=art+'manifest.json'}
    outputs[art+'manifest.json']=encode(manifest)
    return outputs


def generate(include_comparison=True):
    # Import by path, bypassing historical CLI assertions without editing a
    # sealed batch. Every emitted file is checked against current ownership.
    if str(ROOT/'scripts') not in sys.path:
        sys.path.insert(0,str(ROOT/'scripts'))
    outputs={}
    for weapon in IDS:
        module=runpy.run_path(str(ROOT/f'scripts/generate_surface_w123_{weapon}.py'))
        outputs.update(module['generate'](include_comparison=include_comparison))
    rows=[]
    for weapon in IDS:
        d=json.loads(outputs[f'art/weapons/w123/{weapon}/design.json'])
        model=json.loads(outputs[ASSET+f'models/weapon_surface_w123/{weapon}.json'])
        nonbelt=[s for ss in d['parts'].values() for s in ss if s['group']!='belt']
        rows.append(dict(id=weapon,assembled_elements=len(model['elements']),
                         part_counts={k:len(v) for k,v in d['parts'].items()},
                         nonbelt_specs_sha256=sha(json.dumps(nonbelt,sort_keys=True).encode()),
                         feed=d['belt_feed_w154']))
    outputs[MANIFEST]=encode(dict(stage='W154',feature='w154-machine-gun-feed',weapons=rows,
        generator='scripts/fix_belt_feed_w154.py',generator_sha256=sha(Path(__file__).read_bytes()),
        targeted_test='scripts/tests/test_belt_feed_w154.py',native_accepted=False,
        w114_reload='Pinned original geometry and 126 sampled wrappers preserved byte-for-byte; existing W123 substitution supplies corrected splits.',
        master_derivation=['shared surface pack manifest','W151 pulse/ADS','W153 MG bodies/ADS'],
        limitations=['Offline CPU review only; native HIP/ADS, sideview and representative reload pending master.',
                     'Atlas repacked; original nonbelt geometry/material/motif specs preserved.',
                     'Rigid belt, simplified solid tips; no dynamic deformation or native performance claim.',
                     'Historical test suites were not all run or claimed passing.'],
        output_sha256={p:sha(b) for p,b in sorted(outputs.items())}))
    batch=json.loads((ROOT/'docs/qa/2026-10-26/w154/batch.json').read_bytes())
    owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w154-machine-gun-feed'))
    assert set(outputs)<=owned, sorted(set(outputs)-owned)
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    outputs=generate()
    for rel,data in outputs.items():
        path=ROOT/rel
        if args.verify:
            assert path.read_bytes()==data, 'Regeneration differs: '+rel
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
    print(('Verified' if args.verify else 'Generated')+f' {len(outputs)} owned files; native pending master')


if __name__=='__main__':
    main()
