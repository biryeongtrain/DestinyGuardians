#!/usr/bin/env python3
"""Targeted Beloved art/UV/partition checks; no native game acceptance implied."""
import base64
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
loader = importlib.util.spec_from_file_location('beloved_w126', ROOT/'scripts/generate_surface_w123_beloved.py')
g = importlib.util.module_from_spec(loader)
loader.loader.exec_module(g)


def intersects(a, b, tolerance=.002):
    """Separating-axis OBB intersection, including rotated wrist/diamond solids."""
    ar = g.rotation(a.get('rotation',{})); br = g.rotation(b.get('rotation',{}))
    av,bv = g.vertices(a),g.vertices(b)
    axes = [*ar.T,*br.T,*[np.cross(u,v) for u in ar.T for v in br.T]]
    for axis in axes:
        norm = np.linalg.norm(axis)
        if norm < 1e-10:
            continue
        axis = axis/norm; aa = av@axis; bb = bv@axis
        if aa.max()+tolerance < bb.min() or bb.max()+tolerance < aa.min():
            return False
    return True


def contains(e, point):
    p = np.array(point,float); r = e.get('rotation')
    if r:
        o = np.array(r['origin']); p = (p-o) @ g.rotation(r) + o
    return bool(np.all(p>=np.array(e['from'])-1e-6) and np.all(p<=np.array(e['to'])+1e-6))


class BelovedArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Full deterministic regeneration also exercises the actual PNG renderer.
        cls.outputs = g.generate()
        cls.design = json.loads(cls.outputs[g.ART+'design.json'])
        cls.manifest = json.loads(cls.outputs[g.ART+'manifest.json'])
        cls.models = {p:json.loads(cls.outputs[g.MODEL+suffix+'.json']) for p,suffix in [('full',''),('body','_body'),('magazine','_magazine')]}
        cls.elements = cls.models['full']['elements']
        cls.atlas = np.asarray(Image.open(io.BytesIO(cls.outputs[g.TEXTURE])))

    def test_01_exact_regeneration_all_artifacts(self):
        for rel,data in self.outputs.items():
            with self.subTest(path=rel):
                self.assertEqual((ROOT/rel).read_bytes(),data)

    def test_02_exact_owned_scope(self):
        batch = json.loads((ROOT/'docs/qa/2026-10-25/w126/batch.json').read_bytes())
        owned = set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w126-beloved'))
        self.assertEqual(len(owned),12)
        self.assertEqual(set(self.outputs),owned-{'scripts/generate_surface_w123_beloved.py','scripts/qa/test_surface_w123_beloved.py','docs/qa/2026-10-25/w126/beloved-worker.md'})

    def test_03_full_split_and_budget(self):
        b,m = self.models['body'],self.models['magazine']
        self.assertEqual(self.elements,b['elements']+m['elements'])
        self.assertLessEqual(len(b['elements'])+len(m['elements']),1000)
        self.assertEqual(self.manifest['assembled_elements'],len(self.elements))
        self.assertEqual(self.manifest['counts'],{p:len(m['elements']) for p,m in self.models.items()})
        self.assertEqual(len({e['name'] for e in self.elements}),len(self.elements))

    def test_04_solid_native_records_and_rotation_schema(self):
        for e in self.elements:
            with self.subTest(element=e['name']):
                self.assertTrue(np.all(np.array(e['to'])-e['from']>0))
                self.assertEqual(set(e['faces']),set(g.FACES))
                self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
                self.assertTrue(np.isfinite(g.vertices(e)).all())
                if 'rotation' in e:
                    self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
                    R = g.rotation(e['rotation'])
                    np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-10)
        self.assertEqual(self.manifest['alpha_elements'],0)

    def test_05_face_uv_opaque_unique_and_gutters(self):
        rects = []
        for e in self.elements:
            for f in e['faces'].values():
                self.assertEqual(f['texture'],'#0')
                x0,y0,x1,y1 = [int(round(v*g.EDGE/16)) for v in f['uv']]
                self.assertTrue(2<=x0<x1<=g.EDGE-2 and 2<=y0<y1<=g.EDGE-2)
                tile = self.atlas[y0:y1,x0:x1]
                self.assertTrue(np.all(tile[:,:,3]==255),'Transparent structural face')
                np.testing.assert_array_equal(self.atlas[y0-1,x0:x1],tile[0])
                np.testing.assert_array_equal(self.atlas[y1,x0:x1],tile[-1])
                np.testing.assert_array_equal(self.atlas[y0:y1,x0-1],tile[:,0])
                np.testing.assert_array_equal(self.atlas[y0:y1,x1],tile[:,-1])
                rects.append((x0,y0,x1,y1))
        self.assertEqual(len(rects),len(set(rects)))
        # Every padded island is disjoint, not merely UV values in bounds.
        occupied = np.zeros((g.EDGE,g.EDGE),bool)
        for x0,y0,x1,y1 in rects:
            self.assertFalse(occupied[y0-2:y1+2,x0-2:x1+2].any())
            occupied[y0-2:y1+2,x0-2:x1+2] = True

    def test_06_default_dye_and_source_jewelry(self):
        specs = [s for ss in self.design['parts'].values() for s in ss]
        gems = [s for s in specs if s['motif']=='gem']
        self.assertEqual(len(gems),6)
        for s in gems:
            e = next(e for e in self.elements if e['name']==s['geometry']['name'])
            for face in ('west','east'):
                uv = [int(round(q*g.EDGE/16)) for q in e['faces'][face]['uv']]
                x0,y0,x1,y1 = uv; rgb = self.atlas[y0:y1,x0:x1,:3].astype(float)
                self.assertGreater(rgb[:,:,2].mean(),rgb[:,:,1].mean()*1.5)
                self.assertGreater(np.unique(rgb.reshape(-1,3),axis=0).shape[0],100)
        self.assertGreater(self.design['palette']['gold'][0],self.design['palette']['gold'][2]*2)

    def test_07_display_axis_scale_and_magazine_frame(self):
        original = json.loads((ROOT/g.BASE).read_bytes())
        self.assertEqual(self.models['full']['display'],original['display'])
        for p in ('body','magazine'):
            self.assertNotIn('display',self.models[p])
        self.assertEqual(self.design['source']['source_axis'],{'length':0,'thin':1,'muzzle_sign':1})
        self.assertAlmostEqual(self.manifest['source_scale'],18.824982686476197)
        self.assertEqual(self.manifest['source_anchor'],[8.,8.,8.359254816030532])
        old = np.array(self.design['magazine_reference_bounds'])
        ps = np.concatenate([g.vertices(e) for e in self.models['magazine']['elements']])
        new = np.array([ps.min(0),ps.max(0)])
        np.testing.assert_allclose((new[0]+new[1])/2,(old[0]+old[1])/2,atol=.08)
        self.assertAlmostEqual(new[0,1],old[0,1],places=6)
        self.assertAlmostEqual(new[1,1],old[1,1],places=6)
        allps = np.concatenate([g.vertices(e) for e in self.elements])
        self.assertAlmostEqual(allps[:,2].min(),-15.5)
        self.assertAlmostEqual(allps[:,2].max(),13.5)

    def test_08_connected_assembly_no_floating_grip_or_magazine(self):
        # An art regression: the first blockout had a floating heel and mag socket.
        reached = {0}; pending = set(range(1,len(self.elements)))
        while pending:
            new = {j for j in pending if any(intersects(self.elements[i],self.elements[j]) for i in reached)}
            if not new:
                break
            reached.update(new); pending.difference_update(new)
        self.assertFalse(pending,'Detached solids: '+', '.join(self.elements[i]['name'] for i in sorted(pending)))

    def test_09_stock_muzzle_and_trigger_are_real_voids(self):
        # Multiple points across each aperture; transparency cannot satisfy this.
        for y,zs in [(8.9,[10.2,11.0,11.8]),(10.015,[-15.0,-14.0,-13.0]),(8.67,[7.45,7.68])]:
            for z in zs:
                for x in (7.85,8,8.15):
                    self.assertFalse(any(contains(e,[x,y,z]) for e in self.elements),(x,y,z))
        self.assertTrue(any(contains(e,[8,10.40,-14]) for e in self.elements))
        self.assertTrue(any(contains(e,[8,7.9,11.4]) for e in self.elements))

    def test_10_inspection_parity_embedded_atlas_and_no_native_claim(self):
        bb = json.loads(self.outputs[g.ART+'inspection.bbmodel'])
        self.assertEqual(len(bb['elements']),len(self.elements))
        self.assertEqual([q['name'] for q in bb['outliner']],['body','magazine'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),self.outputs[g.TEXTURE])
        for native,editor in zip(self.elements,bb['elements']):
            self.assertEqual(native['from'],editor['from']); self.assertEqual(native['to'],editor['to'])
            for f in g.FACES:
                np.testing.assert_allclose(np.array(native['faces'][f]['uv'])*g.EDGE/16,editor['faces'][f]['uv'])
            r = native.get('rotation',{})
            self.assertEqual([r.get(a,0) for a in 'xyz'],editor['rotation'])
            self.assertEqual(editor['origin'],r.get('origin',[8,8,8]))
        self.assertFalse(bb['destiny_w126']['nativeAccepted'])
        self.assertFalse(self.manifest['native_accepted'])

    def test_11_hash_provenance(self):
        for rel,h in self.manifest['input_sha256'].items():
            self.assertEqual(g.sha((ROOT/rel).read_bytes()),h)
        for path,h in self.manifest['raw_input_sha256'].items():
            self.assertEqual(g.sha(Path(path).read_bytes()),h)
        for path,h in self.manifest['output_sha256'].items():
            self.assertEqual(g.sha(self.outputs[path]),h)
        self.assertEqual(g.sha((ROOT/'scripts/generate_surface_w123_beloved.py').read_bytes()),self.manifest['generator_sha256'])

    def test_12_comparison_contains_rasterized_three_dimensional_views(self):
        im = np.array(Image.open(io.BytesIO(self.outputs[g.ART+'comparison.png'])))
        self.assertEqual(im.shape,(1760,3000,3))
        for y in (485,825,1165):
            crop = im[y+45:y+310,2020:2980]
            # Non-background content in each new-model row, not an empty preview.
            self.assertGreater(np.count_nonzero(np.any(crop!=[32,39,48],axis=2)),5000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
