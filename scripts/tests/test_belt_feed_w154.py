#!/usr/bin/env python3
"""W154 targeted offline geometry and reproduction regressions, not native QA."""
import base64
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
G=runpy.run_path(str(ROOT/'scripts/fix_belt_feed_w154.py'))
H=G['renderer']()
ASSET=G['ASSET']
PRESERVED={
    'hammerhead':(132,'d845848928be6f76ba9e52f6008c9593893e2f4f2c49a9a6600833b831964fe7'),
    'fixed_odds':(119,'533205e12595838ebb4e8ff1ab066e50d34513e5e5d85a1f61a4c4a6284f14b4'),
    'retrofit_escapade':(92,'f9b6699058212947e795fb644eabf1c513d7f0bd68a1a38d4b26eaef5d4db8da'),
}
PRESERVED_UV_PIXELS={
    'hammerhead':'cc16a9e7e373a2393a891a555c81b9f47188fc89e726fb23784e040d9746cf93',
    'fixed_odds':'2c33718b5edc4586e2240adf4f628b62e2398c0967edd9c426f37a0f39c5cc5f',
    'retrofit_escapade':'9613ee57dfe45a64eccd59c40ef92ddbe6d5164cc7dfebcd3c085d1eb633c081',
}


def read(rel):
    return json.loads((ROOT/rel).read_bytes())


def centre(element):
    return (np.array(element['from'])+element['to'])/2


def inside(element,point,tolerance=1e-6):
    p=np.asarray(point,float)
    if 'rotation' in element:
        r=element['rotation'];o=np.asarray(r['origin'])
        p=(p-o)@H['rotation'](r)+o
    return np.all(p>=np.array(element['from'])-tolerance) and np.all(p<=np.array(element['to'])+tolerance)


class BeltFeedW154(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=G['generate']()
        cls.designs={w:read(f'art/weapons/w123/{w}/design.json') for w in G['IDS']}
        cls.models={w:read(ASSET+f'models/weapon_surface_w123/{w}.json') for w in G['IDS']}

    def test_01_exact_reproduction_and_ownership(self):
        owned=set(next(f['owned_paths'] for f in read('docs/qa/2026-10-26/w154/batch.json')['features']
                       if f['name']=='w154-machine-gun-feed'))
        self.assertLessEqual(set(self.outputs),owned)
        for rel,data in self.outputs.items():
            with self.subTest(path=rel):
                self.assertEqual((ROOT/rel).read_bytes(),data)

    def test_02_body_housing_material_and_motif_specs_preserved(self):
        # Hashes measured from the dirty-seeded W153+W152 baseline, before edit.
        for w,d in self.designs.items():
            specs=[s for ss in d['parts'].values() for s in ss if s['group']!='belt']
            self.assertEqual(len(specs),PRESERVED[w][0])
            self.assertEqual(G['sha'](json.dumps(specs,sort_keys=True).encode()),PRESERVED[w][1])

    def test_03_all_rounds_are_longitudinal_and_tips_muzzleward(self):
        for w,m in self.models.items():
            es={e['name']:e for e in m['elements']}
            for i in range(self.designs[w]['belt_feed_w154']['rounds']):
                case=es[('belt_round_' if w=='hammerhead' else 'belt_case_' if w=='fixed_odds' else 'round_case_')+str(i)]
                tip=es[('belt_tip_' if w=='hammerhead' else 'belt_copper_tip_' if w=='fixed_odds' else 'round_tip_')+str(i)]
                size=np.array(case['to'])-case['from']
                self.assertGreater(size[2],2*max(size[:2]),w)
                vector=centre(tip)-centre(case)
                np.testing.assert_allclose(vector/np.linalg.norm(vector),[0,0,-1],atol=1e-7)
                for e in (case,tip):
                    r=e.get('rotation',{})
                    np.testing.assert_allclose(H['rotation'](r)@np.array([0,0,-1]),[0,0,-1],atol=1e-7)

    def test_03b_nonbelt_face_pixels_preserved_across_atlas_repack(self):
        for w,d in self.designs.items():
            keep={s['geometry']['name'] for ss in d['parts'].values() for s in ss if s['group']!='belt'}
            im=np.asarray(Image.open(ROOT/(ASSET+f'textures/item/weapon/w123/{w}.png')).convert('RGBA'))
            digest=hashlib.sha256()
            for e in sorted(self.models[w]['elements'],key=lambda e:e['name']):
                if e['name'] not in keep:
                    continue
                for face,f in sorted(e['faces'].items()):
                    x0,y0,x1,y1=np.rint(np.array(f['uv'])*64).astype(int)
                    digest.update(e['name'].encode()+face.encode())
                    digest.update(im[y0:y1,x0:x1].tobytes())
            self.assertEqual(digest.hexdigest(),PRESERVED_UV_PIXELS[w])

    def test_04_case_to_tip_has_no_gap(self):
        for w,m in self.models.items():
            es={e['name']:e for e in m['elements']}
            for i in range(self.designs[w]['belt_feed_w154']['rounds']):
                names=([f'belt_round_{i}',f'belt_tip_{i}'] if w=='hammerhead' else
                       [f'belt_case_{i}',f'belt_copper_shoulder_{i}',f'belt_copper_tip_{i}'] if w=='fixed_odds' else
                       [f'round_case_{i}',f'round_shoulder_{i}',f'round_tip_{i}'])
                for a,b in zip(names,names[1:]):
                    self.assertGreaterEqual(es[b]['to'][2],es[a]['from'][2],(w,a,b))

    def test_05_links_connect_every_round_along_curve(self):
        for w,m in self.models.items():
            es={e['name']:e for e in m['elements']};feed=self.designs[w]['belt_feed_w154']
            points=[[*p,feed['link_z']] for p in feed['path_xy']]
            for i,point in enumerate(points):
                link=es[('round_link_' if w=='retrofit_escapade' else 'belt_link_')+str(i)]
                self.assertTrue(inside(link,point))
                if i+1<len(points):
                    join=es[f'feed_join_{i}']
                    for t in np.linspace(0,1,17):
                        self.assertTrue(inside(join,np.array(point)*(1-t)+np.array(points[i+1])*t),(w,i,t))
            self.assertGreater(points[0][1]-points[-1][1],1.8)

    def test_06_receiver_entries_and_magazine_seating(self):
        # Independent housing envelopes, not generated path constants.
        expected={
            'hammerhead':([7.18,11.98,3.08],[8.82,12.58,4.90],
                          [9.27,9.50,2.54],[10.69,9.80,5.18]),
            'fixed_odds':([7.64,10.77,3.32],[8.60,11.91,6.59],
                          [8.82,8.25,3.49],[12.10,9.79,5.72]),
            'retrofit_escapade':([7.15,11.86,2.57],[8.85,12.40,4.95],
                                 [5.30,9.47,3.045],[7.56,10.59,4.795]),
        }
        for w,d in self.designs.items():
            es={e['name']:e for e in self.models[w]['elements']}
            prefix='belt_round_' if w=='hammerhead' else 'belt_case_' if w=='fixed_odds' else 'round_case_'
            first=centre(es[prefix+'0']);last=centre(es[prefix+str(d['belt_feed_w154']['rounds']-1)])
            a,b,c,e=expected[w]
            self.assertTrue(np.all(first>=a) and np.all(first<=b),(w,'receiver',first))
            self.assertTrue(np.all(last>=c) and np.all(last<=e),(w,'magazine',last))
        # Retrofit must no longer protrude beyond the outer drum face in -X.
        retrofit=[s['geometry'] for s in self.designs['retrofit_escapade']['parts']['full'] if s['group']=='belt']
        self.assertGreater(min(H['vertices'](e)[:,0].min() for e in retrofit),4.745)

    def test_07_real_emitted_budget_geometry_uv_and_opacity(self):
        for w,m in self.models.items():
            self.assertLessEqual(len(m['elements']),1000)
            self.assertEqual(len({e['name'] for e in m['elements']}),len(m['elements']))
            im=np.asarray(Image.open(ROOT/(ASSET+f'textures/item/weapon/w123/{w}.png')).convert('RGBA'))
            for e in m['elements']:
                self.assertEqual(set(e['faces']),set(H['FACES']))
                self.assertTrue(np.isfinite(H['vertices'](e)).all())
                self.assertTrue(np.all(np.array(e['to'])>e['from']))
                self.assertNotIn('vertices',e);self.assertNotIn('triangles',e)
                for face in e['faces'].values():
                    self.assertEqual(face['texture'],'#0')
                    uv=np.array(face['uv'])*im.shape[0]/16
                    self.assertTrue(np.all(uv>=0) and np.all(uv<=im.shape[0]))
                    x0,y0,x1,y1=np.rint(uv).astype(int)
                    self.assertGreater(x1,x0);self.assertGreater(y1,y0)
                    self.assertTrue(np.all(im[y0-2:y1+2,x0-2:x1+2,3]==255))

    def test_07b_entire_terminal_cartridge_seated_in_magazine(self):
        for w,d in self.designs.items():
            es={e['name']:e for e in self.models[w]['elements']}
            i=d['belt_feed_w154']['rounds']-1
            names=([f'belt_round_{i}',f'belt_tip_{i}',f'belt_link_{i}'] if w=='hammerhead' else
                   [f'belt_case_{i}',f'belt_copper_shoulder_{i}',f'belt_copper_tip_{i}',f'belt_link_{i}'] if w=='fixed_odds' else
                   [f'round_case_{i}',f'round_facet_{i}',f'round_shoulder_{i}',f'round_tip_{i}',f'round_link_{i}'])
            cavity=({'from':[8.82,8.25,3.49],'to':[12.10,9.79,5.72]} if w=='fixed_odds' else
                    es['drum_feed_neck'] if w=='retrofit_escapade' else es['drum_1_vertical_core'])
            for name in names:
                for point in H['vertices'](es[name]):
                    self.assertTrue(inside(cavity,point),(w,name,point))

    def test_08_hammerhead_full_equals_splits_and_pivot_display_preserved(self):
        parts=[read(ASSET+f'models/weapon_surface_w123/hammerhead_{p}.json') for p in ('body','magazine','cover')]
        self.assertEqual(self.models['hammerhead']['elements'],sum((p['elements'] for p in parts),[]))
        self.assertTrue(all('display' not in p for p in parts))
        belt_names={e['name'] for e in parts[1]['elements'] if e['name'].startswith(('belt_','feed_join_'))}
        self.assertEqual(len(belt_names),31)
        self.assertEqual(self.designs['hammerhead']['cover_pivot'],[8.0,13.151657042558291,1.7248276566312146])
        for w,m in self.models.items():
            base=read(ASSET+f'models/weapon/machine_gun/{w}.json')
            self.assertEqual(m['display'],base['display'])

    def test_09_w114_pinned_geometry_and_sampled_wrappers_preserved(self):
        directory=ROOT/(ASSET+'models/weapon_reload_w114_hammerhead')
        hashes={str(p.relative_to(ROOT)):G['sha'](p.read_bytes()) for p in directory.glob('*.json')}
        self.assertEqual(len(hashes),129)
        self.assertEqual(G['sha'](json.dumps(hashes,sort_keys=True).encode()),
                         'b3a3e66e244f138efe2d975265d0b544ff78c298a10a634138ce76b0fd7ea974')

    def test_10_inspection_embeds_exported_geometry_and_atlas(self):
        for w,m in self.models.items():
            bb=read(f'art/weapons/w123/{w}/inspection.bbmodel')
            self.assertEqual(len(bb['elements']),len(m['elements']))
            byname={e['name']:e for e in bb['elements']}
            for e in m['elements']:
                b=byname[e['name']]
                self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
                r=e.get('rotation',{})
                self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
                for f in H['FACES']:
                    np.testing.assert_allclose(b['faces'][f]['uv'],np.array(e['faces'][f]['uv'])*64,atol=1e-9)
            atlas=base64.b64decode(bb['textures'][0]['source'].split(',',1)[1])
            self.assertEqual(atlas,(ROOT/(ASSET+f'textures/item/weapon/w123/{w}.png')).read_bytes())

    def test_11_manifest_hashes_and_honest_native_status(self):
        report=read(G['MANIFEST'])
        self.assertFalse(report['native_accepted'])
        self.assertEqual({w['id'] for w in report['weapons']},set(G['IDS']))
        for rel,digest in report['output_sha256'].items():
            self.assertEqual(G['sha']((ROOT/rel).read_bytes()),digest,rel)
        for w in G['IDS']:
            man=read(f'art/weapons/w123/{w}/manifest.json')
            self.assertFalse(man['native_accepted'])
            for rel,digest in man['output_sha256'].items():
                self.assertEqual(G['sha']((ROOT/rel).read_bytes()),digest,rel)


if __name__=='__main__':
    unittest.main(verbosity=2)
