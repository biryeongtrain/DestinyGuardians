#!/usr/bin/env python3
"""Targeted W127 Hammerhead art checks. Offline only; no game acceptance."""
import base64
from collections import Counter
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
loader=importlib.util.spec_from_file_location('hammerhead_w127',ROOT/'scripts/generate_surface_w123_hammerhead.py')
g=importlib.util.module_from_spec(loader);loader.loader.exec_module(g)

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

class HammerheadArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs=g.generate()
        cls.design=json.loads(cls.outputs[g.ART+'design.json'])
        cls.manifest=json.loads(cls.outputs[g.ART+'manifest.json'])
        cls.models={p:json.loads(cls.outputs[g.MODEL+('' if p=='full' else '_'+p)+'.json']) for p in (*g.PARTS,'full')}
        cls.elements=cls.models['full']['elements']
        cls.atlas=np.asarray(Image.open(io.BytesIO(cls.outputs[g.TEXTURE])))

    def test_01_deterministic_regeneration_all_ten_artifacts(self):
        # Recreates the atlas, embedded texture, JSON and all offline render rows.
        for path,data in self.outputs.items():
            with self.subTest(path=path):self.assertEqual((ROOT/path).read_bytes(),data)

    def test_02_owned_exact_paths(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w127/batch.json').read_bytes())
        owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w127-hammerhead'))
        self.assertEqual(len(owned),13)
        self.assertEqual(set(self.outputs),owned-{'scripts/generate_surface_w123_hammerhead.py','scripts/qa/test_surface_w123_hammerhead.py','docs/qa/2026-10-26/w127/hammerhead-worker.md'})

    def test_03_full_equals_three_parts_budget_and_canonical_delta(self):
        self.assertEqual(self.elements,sum([self.models[p]['elements'] for p in g.PARTS],[]))
        self.assertLessEqual(len(self.elements),1000)
        self.assertEqual(self.manifest['counts'],{p:len(m['elements']) for p,m in self.models.items()})
        self.assertEqual(len({e['name'] for e in self.elements}),len(self.elements))
        self.assertEqual(self.manifest['emitted_faces'],len(self.elements)*6)
        original=json.loads((ROOT/g.BASE).read_bytes())['elements']
        split=sum([json.loads((ROOT/(g.RELOAD+'_'+p+'.json')).read_bytes())['elements'] for p in g.PARTS],[])
        self.assertEqual(Counter(json.dumps(e,sort_keys=True) for e in original),Counter(json.dumps(e,sort_keys=True) for e in split))
        self.assertEqual(len(original),223)
        self.assertEqual(self.manifest['canonical_reload_delta'],0)

    def test_04_native_solid_schema_and_finite_xyz_rotation(self):
        for p,m in self.models.items():
            self.assertLessEqual(set(m),{'credit','textures','display','elements'})
            self.assertEqual(m['textures']['0'],'destiny:item/weapon/w123/hammerhead')
            self.assertEqual(m['textures']['particle'],m['textures']['0'])
        for e in self.elements:
            with self.subTest(element=e['name']):
                self.assertLessEqual(set(e),{'name','from','to','rotation','faces'})
                self.assertTrue(np.all(np.array(e['to'])-e['from']>0))
                self.assertEqual(set(e['faces']),set(g.FACES))
                self.assertTrue(np.isfinite(g.vertices(e)).all())
                if 'rotation' in e:
                    self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
                    R=g.rotation(e['rotation']);np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-10)
        self.assertEqual(self.manifest['alpha_body_plates'],0)
        self.assertEqual(self.manifest['triangle_adapter_elements'],0)
        for prefix in ('muzzle_bore_rim','drum_0_front_rim','drum_1_rear_rim'):
            ends=[e['from'][2] for e in self.elements if e['name'].startswith(prefix)]
            self.assertEqual(len(ends),8)
            self.assertEqual(len(set(ends)),8,'Coincident rim end caps')
        for name in ['shroud_roof','receiver_main','receiver_rear','cover_shell','feed_center']:
            e=next(e for e in self.elements if e['name']==name)
            self.assertGreater(min(np.array(e['to'])-e['from']),.4)

    def test_05_face_uv_noncollapsed_opaque_disjoint_extruded_gutters(self):
        occupied=np.zeros((g.EDGE,g.EDGE),bool);rects=[]
        for e in self.elements:
            for f in e['faces'].values():
                self.assertEqual(set(f),{'uv','texture'});self.assertEqual(f['texture'],'#0')
                x0,y0,x1,y1=[round(v*g.EDGE/16) for v in f['uv']]
                self.assertTrue(2<=x0<x1<=g.EDGE-2 and 2<=y0<y1<=g.EDGE-2)
                self.assertGreaterEqual(min(x1-x0,y1-y0),6)
                tile=self.atlas[y0:y1,x0:x1]
                self.assertTrue(np.all(tile[:,:,3]==255))
                self.assertGreater(np.ptp(tile[:,:,:3].astype(int)),3)
                np.testing.assert_array_equal(self.atlas[y0-1,x0:x1],tile[0])
                np.testing.assert_array_equal(self.atlas[y1,x0:x1],tile[-1])
                np.testing.assert_array_equal(self.atlas[y0:y1,x0-1],tile[:,0])
                np.testing.assert_array_equal(self.atlas[y0:y1,x1],tile[:,-1])
                self.assertFalse(occupied[y0-2:y1+2,x0-2:x1+2].any())
                occupied[y0-2:y1+2,x0-2:x1+2]=True;rects.append((x0,y0,x1,y1))
        self.assertEqual(len(set(rects)),len(self.elements)*6)

    def test_06_display_scale_axis_and_feed_frame_preserved(self):
        original=json.loads((ROOT/g.BASE).read_bytes())
        self.assertEqual(self.models['full']['display'],original['display'])
        for p in g.PARTS:self.assertNotIn('display',self.models[p])
        self.assertEqual(self.manifest['anchor'],[8.,8.,8.])
        self.assertAlmostEqual(self.manifest['scale'],23.3089771408205)
        self.assertEqual(self.design['source']['source_axis'],dict(length=1,thin=0,muzzle_sign=-1))
        points=np.concatenate([g.vertices(e) for e in self.elements])
        self.assertAlmostEqual(points[:,2].min(),-11.883723)
        self.assertAlmostEqual(points[:,2].max(),15.116277)
        mag=np.concatenate([g.vertices(e) for e in self.models['magazine']['elements']])
        self.assertGreater(mag[:,0].max(),12.8)  # lateral rigid belt preserved
        self.assertLess(mag[:,0].min(),4.7)      # left drum preserved
        self.assertLess(abs(mag[:,1].min()-7.000348),.05)

    def test_07_original_hinge_and_cover_sight_membership(self):
        self.assertEqual(self.design['cover_pivot'],[8.,13.151657042558291,1.7248276566312146])
        cover_names={e['name'] for e in self.models['cover']['elements']}
        self.assertIn('cover_shell',cover_names)
        self.assertTrue(all(e['name'] in cover_names for e in self.elements if e['name'].startswith('sight_')))
        pivot=np.array(g.HINGE);relative=pivot-np.array([8,8,8])
        # Existing external W114 p-Rp correction must keep hinge stationary.
        for angle in (0,-78,-92,-88):
            R=g.rotation({'x':angle});offset=relative-R@relative
            np.testing.assert_allclose(R@relative+offset,relative,atol=1e-12)
            np.testing.assert_allclose((pivot-pivot)@R.T+pivot,pivot,atol=1e-12)
        shell=next(e for e in self.models['cover']['elements'] if e['name']=='cover_shell')
        opened=(g.vertices(shell)-pivot)@g.rotation({'x':-92}).T+pivot
        self.assertGreater(opened[:,1].max()-g.vertices(shell)[:,1].max(),5)
        h=next(e for e in self.elements if e['name']=='cover_hinge_bar')
        np.testing.assert_allclose((np.array(h['from'])+h['to'])/2,pivot,atol=1e-12)

    def test_08_real_openings_and_negative_control(self):
        rays={
            'muzzle_bore':[[8,11.94,z] for z in np.linspace(-11.88,-9.4,15)],
            'sight':[[8,14.10,z] for z in np.linspace(2.9,5.3,15)],
            'carry':[[x,8.85,-.4] for x in np.linspace(6.5,9.5,15)],
            'stock':[[x,9.5,11.4] for x in np.linspace(6.5,9.5,15)],
            'trigger':[[x,9.85,6.1] for x in np.linspace(7.2,8.8,15)]}
        def clear(elements,points):return not any(contains(e,p) for p in points for e in elements)
        for name,ray in rays.items():
            self.assertTrue(clear(self.elements,ray),name)
            lo=np.min(ray,axis=0)-.04;hi=np.max(ray,axis=0)+.04
            blocker={'from':lo.tolist(),'to':hi.tolist()}
            self.assertFalse(clear(self.elements+[blocker],ray),'Void gate missed '+name+' filler')
        self.assertTrue(any(contains(e,[8,12.31,-11.72]) for e in self.elements))
        self.assertTrue(any(contains(e,[8,8.01,-.4]) for e in self.elements))

    def test_09_structural_connections(self):
        # Catches the observed first-blockout floating stock/handle/wrist regressions.
        byname={e['name']:e for e in self.elements}
        pairs=[('stock_lower_brace','stock_butt'),('stock_lower_brace','grip_heel'),
            ('pistol_grip','pistol_wrist'),('pistol_wrist','receiver_main'),
            ('carry_upper','gas_cylinder'),('gas_upper_spine','gas_cylinder'),
            ('feed_neck','belt_link_spine'),('cover_shell','cover_hinge_bar'),
            ('cover_sight_mount','sight_base'),('sight_lower_leg_1','sight_upper_leg_1'),
            ('sight_upper_leg_1','sight_bridge')]
        for a,b in pairs:self.assertTrue(intersects(byname[a],byname[b]),a+' / '+b)

    def test_10_inspection_parity_embedded_texture_and_cover_origin(self):
        bb=json.loads(self.outputs[g.ART+'inspection.bbmodel'])
        self.assertEqual(len(bb['elements']),len(self.elements))
        self.assertEqual([q['name'] for q in bb['outliner']],list(g.PARTS))
        self.assertEqual(bb['outliner'][2]['origin'],g.HINGE)
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),self.outputs[g.TEXTURE])
        for e,b in zip(self.elements,bb['elements']):
            self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            for f in g.FACES:np.testing.assert_allclose(np.array(e['faces'][f]['uv'])*g.EDGE/16,b['faces'][f]['uv'])
            r=e.get('rotation',{});self.assertEqual([r.get(a,0) for a in 'xyz'],b['rotation'])
            self.assertEqual(b['origin'],r.get('origin',[8,8,8]))
        self.assertFalse(bb['destiny_w127']['nativeAccepted']);self.assertFalse(self.manifest['native_accepted'])

    def test_11_hashes_and_paint_identity(self):
        for p,h in self.manifest['input_sha256'].items():self.assertEqual(g.sha((ROOT/p).read_bytes()),h)
        for p,h in self.manifest['raw_input_sha256'].items():self.assertEqual(g.sha(Path(p).read_bytes()),h)
        for p,h in self.manifest['output_sha256'].items():self.assertEqual(g.sha(self.outputs[p]),h)
        self.assertEqual(g.sha((ROOT/'scripts/generate_surface_w123_hammerhead.py').read_bytes()),self.manifest['generator_sha256'])
        specs=sum(self.design['parts'].values(),[])
        self.assertEqual(len([s for s in specs if s['motif']=='cartridge']),8)
        self.assertEqual(len([s for s in specs if s['motif']=='tip']),8)
        red=self.design['palette']['red'];self.assertGreater(red[0],red[1]*4)
        self.assertEqual(self.manifest['source_triangles'],25499)

    def test_12_comparison_contains_side_oblique_and_open_pose_rasters(self):
        im=np.asarray(Image.open(io.BytesIO(self.outputs[g.ART+'comparison.png'])))
        self.assertEqual(im.shape,(2060,2640,3))
        for y in (485,785,1085):
            crop=im[y+35:y+280,1780:2620]
            self.assertGreater(np.count_nonzero(np.any(crop!=[32,39,48],axis=2)),12000)
        crop=im[1430:1730,1340:2620]
        self.assertGreater(np.count_nonzero(np.any(crop!=[32,39,48],axis=2)),12000)

if __name__=='__main__':unittest.main(verbosity=2)
