#!/usr/bin/env python3
"""Practical W143 asset regression; offline checks, not native certification."""
import base64
import json
import runpy
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_dead_man_walking_xx7463.py'))

class DeadManWalkingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meshes,cls.meta=G['source_meshes']()
        cls.d=json.loads((ROOT/G['ART']/'design.json').read_bytes())
        cls.m=json.loads((ROOT/G['MODEL']).read_bytes())
        cls.man=json.loads((ROOT/G['ART']/'manifest.json').read_bytes())
        cls.bb=json.loads((ROOT/G['ART']/'inspection.bbmodel').read_bytes())
        cls.atlas=Image.open(ROOT/G['TEXTURE']).convert('RGBA')

    def hits(self,p):
        p=np.array(p,float)
        for e in self.m['elements']:
            r=e.get('rotation');q=p.copy()
            if r:
                o=np.array(r['origin']);q=(q-o)@G['H']['rotation']({r['axis']:r['angle']})+o
            if np.all(q>=np.array(e['from'])-1e-7) and np.all(q<=np.array(e['to'])+1e-7):return True
        return False

    def test_source_frame_and_honest_counts(self):
        self.assertEqual(self.d['source'],self.meta)
        self.assertEqual(self.meta['anchor'],[8,8,8])
        self.assertEqual(self.meta['scale'],45.869875466067114)
        self.assertEqual(self.meta['source_axis'],dict(length=1,thin=0,muzzle_sign=-1))
        self.assertEqual(sorted(m['name'] for m in self.meshes),sorted(self.meta['source_objects']))
        count=sum(len(m['faces']) for m in self.meshes)
        self.assertEqual(count,12061);self.assertEqual(len(self.meshes),7)
        self.assertEqual(self.man['source_matching']['triangle_difference'],count-self.meta['source_triangles'])
        ps=np.concatenate([m['vertices'] for m in self.meshes])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],self.meta['model_bounds'],atol=1e-6,rtol=0)

    def test_positive_native_solids_and_assembled_budget(self):
        es=self.m['elements']
        self.assertGreater(len(es),0);self.assertLessEqual(len(es),1000)
        self.assertEqual(len(es),self.man['assembled_elements'])
        self.assertEqual(sum(self.man['groups'].values()),len(es))
        self.assertEqual(len({e['name'] for e in es}),len(es))
        self.assertEqual(self.man['triangle_adapter_elements'],0)
        self.assertEqual(self.man['alpha_body_elements'],0)
        for e in es:
            self.assertTrue(np.isfinite([e['from'],e['to']]).all())
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertFalse({'vertices','triangles'}&set(e))
            if 'rotation' in e:
                self.assertEqual(set(e['rotation']),{'origin','axis','angle'})
                self.assertIn(e['rotation']['axis'],'xyz')

    def test_original_display_and_source_envelope(self):
        self.assertEqual(self.m['display'],json.loads((ROOT/G['BASE']).read_bytes())['display'])
        self.assertTrue(self.man['full_only'])
        ps=np.concatenate([G['vertices'](e) for e in self.m['elements']])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],self.meta['model_bounds'],atol=.30,rtol=0)
        # Preserves coordinate frame, not source vertices or obsolete geometry hash.
        np.testing.assert_allclose([ps.min(0),ps.max(0)],self.man['actual_bounds'],atol=1e-6,rtol=0)

    def test_physically_open_muzzle_with_surrounding_walls(self):
        for z in np.linspace(-4.80,-3.70,15):
            for x in (7.72,8,8.28):
                for y in (13.05,13.70,14.35):
                    self.assertFalse(self.hits([x,y,z]),f'muzzle plugged: {x,y,z}')
        self.assertTrue(self.hits([8,13.70,-3.63]))
        for x,y in ((7.25,13.7),(8.75,13.7),(8,15.08),(8,12.32)):
            self.assertTrue(self.hits([x,y,-4.50]),f'no muzzle wall: {x,y}')

    def test_guard_and_rail_are_transverse_air_channels(self):
        for name in ('guard','rail_gap'):
            p=self.d['openings'][name]
            for x in np.linspace(6.25,9.75,25):
                for dy in (-.08,0,.08):
                    self.assertFalse(self.hits([x,p[1]+dy,p[2]]),name)
        # Supporting frame remains substantial around those apertures.
        for p in ([8,10.11,2.80],[8,12.15,2.0],[8,11.74,-1.5],[8,10.73,-1.5]):
            self.assertTrue(self.hits(p),p)

    def test_rear_sight_has_an_actual_axial_opening(self):
        for z in np.linspace(7.43,7.73,11):
            for x in (7.80,8,8.20):
                self.assertFalse(self.hits([x,16.05,z]))
        for x in (7.49,8.51):self.assertTrue(self.hits([x,16.05,7.58]))

    def test_filled_receiver_and_grip_cross_sections(self):
        for name,p in self.d['filled_probes'].items():
            for x in np.linspace(7.35,8.65,21):
                for dy in (-.10,0,.10):
                    self.assertTrue(self.hits([x,p[1]+dy,p[2]]),f'{name} hollow core')

    def test_face_uv_opacity_and_extruded_gutters(self):
        a=np.asarray(self.atlas);self.assertEqual(self.atlas.size,(1024,1024))
        self.assertEqual(int(a[:,:,3].min()),255)
        used=np.zeros((1024,1024),bool);es={e['name']:e for e in self.m['elements']}
        ledger=self.d['atlas']['islands'];self.assertEqual(len(ledger),len(es)*6)
        for it in ledger:
            x,y,r,b=it['rect'];self.assertTrue(2<=x<r<=1022 and 2<=y<b<=1022)
            self.assertFalse(used[y-2:b+2,x-2:r+2].any());used[y-2:b+2,x-2:r+2]=True
            np.testing.assert_array_equal(a[y-2:y,x:r],np.repeat(a[y:y+1,x:r],2,axis=0))
            np.testing.assert_array_equal(a[y:b,r:r+2],np.repeat(a[y:b,r-1:r],2,axis=1))
            f=es[it['element']]['faces'][it['face']]
            self.assertEqual(f['texture'],'#0');self.assertEqual(f['uv'],[q/64 for q in it['rect']])

    def test_inspection_project_matches_emitted_geometry(self):
        self.assertEqual(self.bb['display'],self.m['display'])
        self.assertEqual(base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        es={e['name']:e for e in self.bb['elements']}
        self.assertEqual(len(es),len(self.m['elements']))
        self.assertEqual(sum(len(g['children']) for g in self.bb['outliner']),len(es))
        for a in self.m['elements']:
            b=es[a['name']]
            for k in ('from','to'):self.assertEqual(a[k],b[k])
            r=a.get('rotation')
            self.assertEqual(b['rotation'],[r['angle'] if r and r['axis']==ax else 0 for ax in 'xyz'])
            if r:self.assertEqual(b['origin'],r['origin'])
            for f in a['faces']:self.assertEqual(b['faces'][f]['uv'],[v*64 for v in a['faces'][f]['uv']])

    def test_actual_inputs_and_outputs_have_current_provenance(self):
        for p,digest in self.man['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest)
        for p,digest in self.man['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),digest)
        for p,digest in self.man['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest)
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/G['SCRIPT']).read_bytes()))
        self.assertEqual(self.man['test_sha256'],G['sha'](Path(__file__).read_bytes()))
        self.assertFalse(any('manifest' in p for p in self.man['input_sha256']))

    def test_output_scope_has_only_the_seven_generated_owned_artifacts(self):
        expected={G['MODEL'],G['TEXTURE'],*[G['ART']+x for x in ('design.json','inspection.bbmodel','review.md','comparison.png')]}
        self.assertEqual(set(self.man['output_sha256']),expected)
        self.assertEqual(len(expected|{G['SCRIPT'],G['TEST'],G['REPORT'],G['ART']+'manifest.json'}),10)

    def test_regeneration_is_deterministic(self):
        for p,data in G['generate'](include_comparison=False).items():
            if p.endswith('manifest.json'):continue
            self.assertEqual((ROOT/p).read_bytes(),data,p)

    def test_real_comparison_and_explicit_native_limit(self):
        with Image.open(ROOT/G['ART']/'comparison.png') as im:self.assertEqual(im.size,(2700,2140))
        ref=next(r for r in json.loads((ROOT/G['REFS']).read_bytes()) if r['id']==G['ID'])
        self.assertEqual(self.man['default_photo_sha256'],ref['sha256'])
        self.assertFalse(self.man['native_accepted'])

if __name__=='__main__':unittest.main(verbosity=2)
