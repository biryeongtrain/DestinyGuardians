#!/usr/bin/env python3
"""Practical offline regressions for this one full-model candidate.

Use bundled numpy/Pillow Python -B. No game, GUI, build or performance gates.
"""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_distant_relation.py'))


def read(rel):
    return json.loads((ROOT/rel).read_bytes())


class DistantRelationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=read(G['ART']+'design.json')
        cls.m=read(G['MODEL'])
        cls.man=read(G['ART']+'manifest.json')
        cls.bb=read(G['ART']+'inspection.bbmodel')
        cls.atlas=Image.open(ROOT/G['TEXTURE']).convert('RGBA')

    def occupied(self, p, names=None):
        for e in self.m['elements']:
            if names is not None and e['name'] not in names:
                continue
            q=np.array(p,float)
            if 'rotation' in e:
                r=e['rotation']; o=np.array(r['origin'])
                q=(q-o)@G['helper']()['rotation'](r)+o
            if np.all(q>=np.array(e['from'])-1e-6) and np.all(q<=np.array(e['to'])+1e-6):
                return True
        return False

    def test_01_schema_and_actual_emitted_budget(self):
        self.assertEqual(set(self.m),{'credit','textures','elements','display'})
        n=len(self.m['elements'])
        self.assertEqual(n,88)
        self.assertEqual(n,self.man['assembled_elements'])
        self.assertEqual(sum(self.man['groups'].values()),n)
        self.assertLessEqual(n,1000)
        self.assertEqual(self.man['triangle_adapter_elements'],0)
        self.assertEqual(self.man['alpha_elements'],0)
        self.assertEqual(self.man['emitted_faces'],n*6)
        names=[]
        for e in self.m['elements']:
            self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(e['faces']),set(G['helper']()['FACES']))
            if 'rotation' in e:
                self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
            names.append(e['name'])
        self.assertEqual(len(names),len(set(names)))

    def test_02_native_frame_and_hand_contact(self):
        base=read(G['BASE']); meta=read(G['BB'])['destiny_w30']
        self.assertEqual(self.m['display'],base['display'])
        self.assertEqual(self.d['source']['anchor'],meta['anchor'])
        self.assertEqual(self.d['source']['scale'],meta['scale'])
        self.assertEqual(self.d['muzzle_axis'],'-Z')
        pts=np.concatenate([G['vertices'](e) for e in self.m['elements']])
        self.assertAlmostEqual(float(pts[:,2].min()),meta['model_bounds'][0][2],places=5)
        self.assertLess(abs(float(pts[:,2].max())-meta['model_bounds'][1][2]),.02)
        self.assertTrue(np.allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=.15))
        self.assertTrue(self.occupied(self.d['hand_contact']))
        # This same contact neighbourhood exists in the canonical native frame.
        p=self.d['hand_contact']
        self.assertTrue(any(e['from'][0]<=p[0]<=e['to'][0] and e['from'][1]<=p[1]<=e['to'][1]
                            and e['from'][2]<=p[2]<=e['to'][2] for e in base['elements']))

    def test_03_large_stock_hand_loop_and_trigger_openings(self):
        for key in ('thumbhole','hand_loop','trigger_guard'):
            p=self.d['openings'][key]
            # A practical through-width ray, no alpha-dependent side opening.
            for x in np.linspace(6.8,9.3,15):
                self.assertFalse(self.occupied([x,p[1],p[2]]),(key,x))
        for p in ([8,9.3,12.3],[8,10.7,13.0],[8,8.05,12.5],
                  [8,9.55,1.5],[8,10.25,1.5],[8,10.1,6.0]):
            self.assertTrue(self.occupied(p),p)

    def test_04_muzzle_optic_and_front_sight_depth(self):
        for z in (-8.20,-7.65,-6.65):
            self.assertFalse(self.occupied([8,10.357,z]))
        self.assertTrue(self.occupied([8,10.60,-7.3]))
        for z in (3.86,4.02,4.20):
            self.assertFalse(self.occupied([8,11.88,z]))
        self.assertTrue(self.occupied([8,11.88,4.30]))
        self.assertFalse(self.occupied(self.d['openings']['front_sight']))
        self.assertTrue(self.occupied([7.68,11.04,-3.72]))
        self.assertTrue(self.occupied([8.32,11.04,-3.72]))

    def test_05_explicit_uv_opaque_faces_and_gutters(self):
        self.assertEqual(self.atlas.size,(1024,1024))
        a=np.array(self.atlas); occupied=np.zeros((1024,1024),np.uint8)
        islands=self.d['atlas']['islands']
        self.assertEqual(len(islands),len(self.m['elements'])*6)
        lookup={(e['name'],f):v for e in self.m['elements'] for f,v in e['faces'].items()}
        for island in islands:
            x0,y0,x1,y1=island['rect']; f=lookup[island['element'],island['face']]
            self.assertEqual(f['texture'],'#0')
            self.assertTrue(np.allclose(f['uv'],np.array([x0,y0,x1,y1])/64))
            self.assertTrue(2<=x0<x1<=1022 and 2<=y0<y1<=1022)
            self.assertFalse(occupied[y0-2:y1+2,x0-2:x1+2].any())
            occupied[y0-2:y1+2,x0-2:x1+2]=1
            self.assertTrue((a[y0-2:y1+2,x0-2:x1+2,3]==255).all())
            self.assertTrue(np.array_equal(a[y0-2:y0,x0:x1],np.repeat(a[y0:y0+1,x0:x1],2,axis=0)))
        self.assertEqual(set(self.m['textures'].values()),{'destiny:item/weapon/w123/distant_relation'})

    def test_06_editable_inspection_embeds_final_texture_and_solids(self):
        self.assertEqual(self.bb['meta']['model_format'],'free')
        self.assertEqual(len(self.bb['elements']),len(self.m['elements']))
        self.assertEqual(self.bb['display'],self.m['display'])
        raw=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual(raw,(ROOT/G['TEXTURE']).read_bytes())
        for b,e in zip(self.bb['elements'],self.m['elements']):
            self.assertEqual(b['type'],'cube')
            self.assertEqual(b['from'],e['from']); self.assertEqual(b['to'],e['to'])
            r=e.get('rotation',{})
            self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
            for f,v in e['faces'].items():
                self.assertTrue(np.allclose(b['faces'][f]['uv'],np.array(v['uv'])*64))
        children=[c for group in self.bb['outliner'] for c in group['children']]
        self.assertEqual(set(children),{e['uuid'] for e in self.bb['elements']})
        self.assertFalse(self.bb['destiny_w132']['nativeAccepted'])
        self.assertNotIn('animations',self.bb)

    def test_07_provenance_and_default_dye(self):
        for p,h in self.d['input_sha256'].items():
            self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        for p,h in self.d['raw_input_sha256'].items():
            self.assertEqual(G['sha'](Path(p).read_bytes()),h,p)
        self.assertEqual(self.d['reference']['bungie_hash'],'2034817450')
        self.assertEqual(self.d['reference']['sha256'],G['sha'](G['PHOTO'].read_bytes()))
        self.assertEqual(self.d['source']['triangles'],29579)
        self.assertGreater(self.d['palette']['wood'][0],self.d['palette']['wood'][1])
        self.assertGreater(self.d['palette']['teal'][1],self.d['palette']['teal'][0])

    def test_08_full_only_and_exact_owned_outputs(self):
        outputs=G['generate'](include_comparison=False)
        owned=next(f['owned_paths'] for f in read(G['BATCH'])['features'] if f['name']=='w132-distant_relation')
        self.assertEqual(len(owned),10)
        self.assertTrue(set(outputs)<=set(owned))
        self.assertEqual([p for p in outputs if '/models/' in p],[G['MODEL']])
        self.assertEqual(self.man['representation'],'full only')
        self.assertFalse(self.man['native_accepted'])
        for p,h in self.man['output_sha256'].items():
            self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)

    def test_09_comparison_contains_actual_photo_and_depth_views(self):
        im=Image.open(ROOT/(G['ART']+'comparison.png')).convert('RGB')
        self.assertEqual(im.size,(2200,1740))
        photo=Image.open(G['PHOTO']).convert('RGB').crop((300,180,1910,770))
        photo.thumbnail((1500,390))
        self.assertTrue(np.array_equal(np.array(im.crop((24,58,24+photo.width,58+photo.height))),np.array(photo)))
        # Both canonical/new columns have actual non-background side/oblique content.
        for row in range(3):
            for col in range(2):
                panel=np.array(im.crop((col*1100,495+row*310,(col+1)*1100,805+row*310)))
                self.assertGreater(np.count_nonzero(np.any(panel!=[32,39,48],axis=2)),1800)


if __name__=='__main__':
    unittest.main(verbosity=2)
