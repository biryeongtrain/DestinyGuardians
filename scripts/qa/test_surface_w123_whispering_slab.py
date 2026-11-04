#!/usr/bin/env python3
"""Targeted W147 geometry, provenance, dual-texture UV and W50 contract checks."""
import base64
from collections import Counter
import copy
import io
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import generate_surface_w123_whispering_slab as g
import numpy as np
from PIL import Image


def normalized(e,model):
    e=copy.deepcopy(e);e.pop('name',None)
    for f in e['faces'].values():
        key=f['texture'][1:]
        while str(model['textures'][key]).startswith('#'):key=model['textures'][key][1:]
        f['texture']=model['textures'][key]
    return json.dumps(e,sort_keys=True,separators=(',',':'))

class WhisperingSlabW147(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ROOT/(g.ART+'design.json')).read_bytes())
        cls.m=json.loads((ROOT/g.MODEL).read_bytes())
        cls.old=json.loads((ROOT/g.BASE).read_bytes())
        cls.bb=json.loads((ROOT/(g.ART+'inspection.bbmodel')).read_bytes())
        cls.atlas=Image.open(ROOT/g.TEXTURE).convert('RGBA')
        cls.manifest=json.loads((ROOT/(g.ART+'manifest.json')).read_bytes())
        cls.moving=set(cls.d['moving_element_names'])
        cls.body=[e for e in cls.m['elements'] if e['name'] not in cls.moving]

    def test_01_exact_w50_rest_counter(self):
        expected=g.w50.parts(self.old,g.w50.CONFIG[g.ID])[1]
        actual=[e for e in self.m['elements'] if e['name'] in self.moving]
        self.assertEqual(Counter(normalized(e,self.old) for e in expected),Counter(normalized(e,self.m) for e in actual))
        self.assertEqual([e['name'] for e in actual],[f'moving_rest_{i:03}' for i in range(len(expected))])
        self.assertEqual(len(actual),len(self.moving))
        self.assertEqual(self.m['textures']['original'],self.old['textures']['0'])
        self.assertTrue(all(f['texture']=='#original' for e in actual for f in e['faces'].values()))

    def test_02_assembled_worst_existing_state(self):
        states=[{},dict(empty=True)]+[dict(draw=i/20) for i in range(21)]+[dict(nock=i/20) for i in range(21)]
        maximum=max(len(g.w50.parts(self.old,g.w50.CONFIG[g.ID],**s)[1]) for s in states)
        self.assertEqual(maximum,self.d['budget']['largest_existing_W50_moving_state'])
        self.assertEqual(len(self.body)+maximum,self.d['budget']['max_assembled'])
        self.assertLessEqual(len(self.body)+maximum,1000)
        self.assertGreaterEqual(len(self.body),80)
        self.assertEqual(set(self.d['body_element_names']),{e['name'] for e in self.body})
        self.assertTrue(all(s['classification']=='rigid_body' for s in self.d['parts']))

    def test_03_native_frame_and_display(self):
        self.assertEqual(self.m['display'],self.old['display'])
        self.assertEqual(self.d['source']['anchor'],[8,8,8])
        self.assertAlmostEqual(self.d['source']['scale'],16.109745261806673)
        ps=np.concatenate([g.vertices(e) for e in self.body]);bounds=np.array([ps.min(0),ps.max(0)])
        self.assertAlmostEqual(bounds[0,0],5.441588955983752)
        self.assertAlmostEqual(bounds[0,1],3.8494189088840667)
        self.assertAlmostEqual(bounds[1,1],29.849418908884065)
        self.assertLess(bounds[1,0],7.0)  # Original offset X, never centered at 8.
        self.assertTrue(np.allclose(bounds,self.d['body_bounds']))
        rest=next(e for e in self.body if e['name']=='original_arrow_rest_shelf')
        self.assertTrue(np.allclose(rest['from'],[6.1565234,16.9244105,1.2383105]))
        self.assertFalse(any('string' in e['name'] or 'moving_rest' in e['name'] for e in self.body))

    def test_04_true_volumes_and_face_uv(self):
        names=[e['name'] for e in self.m['elements']];self.assertEqual(len(names),len(set(names)))
        for e in self.body:
            self.assertTrue(np.all(np.array(e['to'])>e['from']),e['name'])
            self.assertNotIn('vertices',e);self.assertNotIn('triangles',e)
            self.assertEqual(set(e['faces']),set(g.FACES))
            for f in e['faces'].values():
                self.assertEqual(f['texture'],'#0');self.assertEqual(len(f['uv']),4)
                self.assertTrue(all(0<=v<=16 for v in f['uv']))
        self.assertEqual(len(self.d['atlas']['islands']),len(self.body)*6)
        rects=[tuple(i['rect']) for i in self.d['atlas']['islands']]
        self.assertEqual(len(rects),len(set(rects)))
        self.assertEqual(self.atlas.getchannel('A').getextrema(),(255,255))
        # Broad source slabs retain measured cross-section depth rather than side cards.
        for e in self.body:
            if '_limb_core' in e['name']:self.assertGreater(e['to'][0]-e['from'][0],.35)

    def test_05_gutter_and_nonoverlapping_faces(self):
        arr=np.asarray(self.atlas);occupied=np.zeros((g.EDGE,g.EDGE),dtype=bool)
        for t in self.d['atlas']['islands']:
            x,y,x1,y1=t['rect'];self.assertFalse(occupied[y-2:y1+2,x-2:x1+2].any())
            occupied[y-2:y1+2,x-2:x1+2]=True
            self.assertTrue(np.array_equal(arr[y:y1,x-1],arr[y:y1,x]))
            self.assertTrue(np.array_equal(arr[y:y1,x1],arr[y:y1,x1-1]))

    def test_06_dual_texture_editable_bb_parity(self):
        self.assertEqual(len(self.bb['textures']),2);self.assertEqual(len(self.bb['elements']),len(self.m['elements']))
        native={e['name']:e for e in self.m['elements']}
        images=[Image.open(io.BytesIO(base64.b64decode(t['source'].split(',')[1]))).convert('RGBA') for t in self.bb['textures']]
        self.assertEqual(g.png(images[0]),g.png(self.atlas))
        source=Image.open(ROOT/(g.ASSET+'textures/item/weapon/w30/'+g.ID+'.png')).convert('RGBA')
        self.assertEqual(g.png(images[1]),g.png(source))
        for b in self.bb['elements']:
            e=native[b['name']];self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            r=e.get('rotation',{});angles=[0,0,0]
            if 'axis' in r:angles['xyz'.index(r['axis'])]=r['angle']
            self.assertEqual(b['rotation'],angles)
            for face,f in b['faces'].items():
                ti=1 if e['faces'][face]['texture']=='#original' else 0
                self.assertEqual(f['texture'],ti);w,h=images[ti].size
                uv=[v*16/(w if i%2==0 else h) for i,v in enumerate(f['uv'])]
                self.assertTrue(np.allclose(uv,e['faces'][face]['uv']))
        group=next(x for x in self.bb['outliner'] if x['name']=='W50_rest_moving_EXACT')
        self.assertEqual(len(group['children']),len(self.moving))

    def test_07_real_open_cage_and_sight(self):
        # Authored cage perimeter leaves a central hole through its YZ plane.
        cage=[e for e in self.body if e['name'].startswith('open_sight_cage_')]
        p=np.array([5.70,18.77,1.80])
        for e in cage:
            r=e.get('rotation',{});o=np.array(r.get('origin',[0,0,0]));q=(p-o)@g.rotation(r)+o
            self.assertFalse(np.all(q>=e['from']) and np.all(q<=e['to']))
        ring=[e for e in self.body if e['name'].startswith('sight_ring_')];self.assertEqual(len(ring),8)
        p=np.array([6.3821564758,18.8958083271,2.349])
        for e in ring:
            r=e['rotation'];o=np.array(r['origin']);q=(p-o)@g.rotation(r)+o
            self.assertFalse(np.all(q>=e['from']) and np.all(q<=e['to']))

    def test_08_provenance_original_assets_not_shared_manifest(self):
        for rel,digest in self.d['input_sha256'].items():
            self.assertEqual(g.sha((ROOT/rel).read_bytes()),digest)
            self.assertNotIn('migration',rel)
        for path,digest in self.d['raw_input_sha256'].items():self.assertEqual(g.sha(Path(path).read_bytes()),digest)
        meshes,meta=g.source_meshes()
        self.assertEqual(len(meshes),10);self.assertEqual(sum(len(m['faces']) for m in meshes),28726)
        self.assertEqual(meta['excluded_objects'],['Whispering-Slab.08.000'])

    def test_09_deterministic_generated_owned_artifacts(self):
        outputs=g.generate(include_comparison=False)
        # Full-render output manifest carries a comparison digest; compare its other fields separately.
        manifest=json.loads(outputs.pop(g.ART+'manifest.json'))
        recorded=copy.deepcopy(self.manifest);recorded['output_sha256'].pop(g.ART+'comparison.png')
        self.assertEqual(manifest,recorded)
        for rel,data in outputs.items():self.assertEqual((ROOT/rel).read_bytes(),data,rel)
        for rel,digest in self.manifest['output_sha256'].items():self.assertEqual(g.sha((ROOT/rel).read_bytes()),digest)
        self.assertEqual(self.manifest['generator_sha256'],g.sha(Path(g.__file__).read_bytes()))

    def test_10_comparison_real_pixels_and_both_texture_slots(self):
        im=Image.open(ROOT/(g.ART+'comparison.png')).convert('RGB');self.assertEqual(im.size,(2400,3380))
        a=np.asarray(im)
        for row in range(3):
            for col in range(3):
                crop=a[410+row*820:410+(row+1)*820,col*800:(col+1)*800]
                self.assertGreater(len(np.unique(crop.reshape(-1,3),axis=0)),80)
        tex={'#0':self.atlas,'#original':Image.open(ROOT/(g.ASSET+'textures/item/weapon/w30/'+g.ID+'.png'))}
        ts=g.model_triangles(self.m,tex);self.assertEqual(len(ts),len(self.m['elements'])*12)
        # Texture arrays for both slots are independently resolved.
        self.assertEqual({t[2].shape[:2] for t in ts},{tex[k].size[::-1] for k in tex})

if __name__=='__main__':unittest.main(verbosity=2)
