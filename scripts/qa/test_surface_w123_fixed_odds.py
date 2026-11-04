#!/usr/bin/env python3
"""Targeted offline regression for the W132 Fixed Odds full-only art candidate.
Run with bundled numpy/Pillow Python -B; unittest writes no cache/artifacts.
"""
import base64
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import generate_surface_w123_fixed_odds as g
import numpy as np
from PIL import Image


def inside(e,p):
    p=np.array(p,float)
    if 'rotation' in e:
        r=e['rotation']; o=np.array(r['origin']); p=(p-o)@g.rotation(r)+o
    return bool(np.all(p>np.array(e['from'])+1e-6) and np.all(p<np.array(e['to'])-1e-6))


class FixedOdds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((g.ROOT/(g.ART+'design.json')).read_bytes())
        cls.m=json.loads((g.ROOT/g.MODEL).read_bytes())
        cls.man=json.loads((g.ROOT/(g.ART+'manifest.json')).read_bytes())
        cls.tex=Image.open(g.ROOT/g.TEXTURE).convert('RGBA')
        cls.es=cls.m['elements']; cls.names={e['name']:e for e in cls.es}

    def test_schema_emitted_budget_and_meaningful_groups(self):
        self.assertEqual(set(self.m),{'credit','textures','elements','display'})
        self.assertEqual(self.man['assembled_elements'],len(self.es))
        self.assertEqual(self.man['counts'],{'full':len(self.es)})
        self.assertLessEqual(len(self.es),1000)
        self.assertEqual(len(self.names),len(self.es))
        self.assertEqual(sum(self.man['semantic_counts'].values()),len(self.es))
        self.assertEqual(self.man['triangle_adapter_elements'],0)
        self.assertTrue(self.man['full_only']); self.assertFalse(self.man['native_accepted'])
        for e in self.es:
            self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.isfinite(g.vertices(e)).all())
            self.assertTrue(np.all(np.array(e['to'])>np.array(e['from'])))
            self.assertEqual(set(e['faces']),set(g.FACES))
            if 'rotation' in e:
                self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
        for prefix,n in [('muzzle_bore_wall_',8),('belt_case_',7),('belt_link_',7),('belt_join_',6),('forearm_bridge_',5)]:
            self.assertEqual(sum(k.startswith(prefix) for k in self.names),n)

    def test_uv_faces_atlas_and_opaque_gutters(self):
        self.assertEqual(self.tex.size,(1024,1024)); a=np.array(self.tex)
        self.assertEqual(len(self.d['atlas']['islands']),len(self.es)*6)
        rectangles=set()
        for island in self.d['atlas']['islands']:
            x,y,x1,y1=island['rect']; self.assertGreater(x1,x); self.assertGreater(y1,y)
            self.assertTrue(2<=x<x1<=1022 and 2<=y<y1<=1022)
            f=self.names[island['element']]['faces'][island['face']]
            self.assertEqual(f['texture'],'#0'); self.assertEqual(f['uv'],[q*16/1024 for q in (x,y,x1,y1)])
            self.assertTrue(np.all(a[y-2:y1+2,x-2:x1+2,3]==255))
            self.assertNotIn((x,y,x1,y1),rectangles); rectangles.add((x,y,x1,y1))
        self.assertEqual(self.m['textures']['0'],'destiny:item/weapon/w123/fixed_odds')
        purple=np.array(self.d['palette']['purple']); self.assertGreater(purple[0],purple[1]); self.assertGreater(purple[2],purple[1])
        gold=self.d['palette']['gold']; self.assertGreater(gold[0],gold[2]*2)

    def test_reference_integrity_and_raw_bounds(self):
        for rel,digest in self.d['input_sha256'].items(): self.assertEqual(g.sha((g.ROOT/rel).read_bytes()),digest,rel)
        for absolute,digest in self.d['raw_input_sha256'].items(): self.assertEqual(g.sha(Path(absolute).read_bytes()),digest,absolute)
        self.assertEqual(g.sha(g.PHOTO.read_bytes()),self.d['reference']['sha256'])
        meshes,meta=g.source_meshes()
        self.assertEqual(sum(len(m['faces']) for m in meshes),30249)
        pts=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=1e-5)
        self.assertEqual(self.d['reference']['bungie_hash'],'2194955522')

    def test_preserved_full_display_and_contact_frame(self):
        canonical=json.loads((g.ROOT/g.BASE).read_bytes())
        self.assertEqual(self.m['display'],canonical['display'])
        self.assertEqual(self.man['source_anchor'],[8,8,8])
        self.assertEqual(self.man['source_scale'],self.d['source']['scale'])
        self.assertEqual(self.d['frame']['muzzle_axis'],[0,0,-1])
        self.assertTrue(inside(self.names['pistol_grip'],self.d['frame']['hand_contact']))
        self.assertAlmostEqual(self.man['actual_bounds'][0][2],self.d['source']['model_bounds'][0][2],delta=.03)
        self.assertAlmostEqual(self.man['actual_bounds'][1][2],self.d['source']['model_bounds'][1][2],delta=.05)
        self.assertAlmostEqual(min(g.vertices(self.names['grip_heel'])[:,1]),7.24,places=5)
        self.assertIn('generic full-only',self.d['frame']['reload_policy'])

    def test_key_openings_and_structural_surrounds(self):
        for name,p in self.d['openings'].items():
            self.assertFalse(any(inside(e,p) for e in self.es),'Blocked opening: '+name)
        # Through-voids in the stock/guard and a deep bore rather than black dots.
        for name in ('stock','trigger_guard','forearm'):
            p=self.d['openings'][name]
            for x in (7.15,7.6,8,8.4,8.85):
                self.assertFalse(any(inside(e,[x,p[1],p[2]]) for e in self.es),name)
        for z in (-13.3,-12.2,-10.3): self.assertFalse(any(inside(e,[8,11.41,z]) for e in self.es))
        self.assertTrue(inside(self.names['muzzle_deep_throat'],[8,11.41,-10.03]))
        for z in (4.05,4.42,4.75): self.assertFalse(any(inside(e,[8,12.80,z]) for e in self.es))
        self.assertTrue(inside(self.names['ammo_box_bottom'],[10.6,8.10,5.4]))
        self.assertTrue(inside(self.names['forearm_top_rail'],[8,10.3,-6.8]))
        self.assertTrue(inside(self.names['stock_comb'],[8,11.0,10.2]))

    def test_belt_parts_and_box_are_in_one_model(self):
        belt=[e for e in self.es if e['name'].startswith('belt_')]
        self.assertEqual(len(belt),34)
        centers=[]
        for i in range(7):
            case=self.names[f'belt_case_{i}']; centers.append((np.array(case['from'])+case['to'])/2)
            self.assertIn(f'belt_copper_tip_{i}',self.names)
            self.assertIn(f'belt_link_{i}',self.names)
            self.assertGreater(np.prod(np.array(case['to'])-case['from']),.06)
        # The ammunition path bows out of the receiver and down to the box.
        centers=np.array(centers)
        self.assertTrue(np.all(np.diff(centers[:,0])>0))
        self.assertTrue(np.all(np.diff(centers[:,1])<0))
        self.assertGreater(centers[-1,0]-centers[0,0],2.5)
        self.assertIn('ammo_box_bottom',self.names)
        self.assertEqual(set(self.d['parts']),{'full'})
        self.assertFalse((g.ROOT/g.MODEL.replace('.json','_body.json')).exists())
        self.assertFalse((g.ROOT/g.MODEL.replace('.json','_magazine.json')).exists())

    def test_editable_inspection_and_manifest_hashes(self):
        bb=json.loads((g.ROOT/(g.ART+'inspection.bbmodel')).read_bytes())
        self.assertEqual(bb['meta']['model_format'],'free')
        self.assertEqual(len(bb['elements']),len(self.es))
        self.assertEqual(bb['display'],self.m['display'])
        image=base64.b64decode(bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual(image,(g.ROOT/g.TEXTURE).read_bytes())
        for e,b in zip(self.es,bb['elements']):
            self.assertEqual(b['type'],'cube'); self.assertEqual(b['from'],e['from']); self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['rotation'],[e.get('rotation',{}).get(a,0) for a in 'xyz'])
            for f in g.FACES: self.assertEqual(b['faces'][f]['uv'],[q*1024/16 for q in e['faces'][f]['uv']])
        for p,h in self.man['output_sha256'].items(): self.assertEqual(g.sha((g.ROOT/p).read_bytes()),h,p)
        self.assertEqual(self.man['generator_sha256'],g.sha(Path(g.__file__).read_bytes()))

    def test_generated_payload_determinism_and_scope(self):
        outputs=g.generate(include_comparison=False)
        owned=set(next(f['owned_paths'] for f in json.loads((g.ROOT/'docs/qa/2026-10-26/w132/batch.json').read_bytes())['features'] if f['name']=='w132-fixed_odds'))
        self.assertLessEqual(set(outputs),owned)
        for rel,data in outputs.items():
            if not rel.endswith('manifest.json'): self.assertEqual((g.ROOT/rel).read_bytes(),data,rel)
        self.assertLess(sum((g.ROOT/p).stat().st_size for p in owned if (g.ROOT/p).exists()),25*1024*1024)


if __name__=='__main__': unittest.main(verbosity=2)
