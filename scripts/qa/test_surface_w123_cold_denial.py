#!/usr/bin/env python3
"""Portable W138 Cold Denial offline regression; bundled Python -B only."""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_cold_denial.py'))
BASELINE='61d9f956c2c0b096efad4a646a84d6f7b308429d08ab2245e1e621419bc89f2f'


def contains(e,p):
    p=np.array(p,float);r=e.get('rotation')
    if r:
        origin=np.array(r['origin']);p=(p-origin)@G['H']['rotation']({r['axis']:r['angle']})+origin
    return bool(np.all(p>=np.array(e['from'])-1e-7) and np.all(p<=np.array(e['to'])+1e-7))


def connected(a,b):
    av,bv=G['vertices'](a),G['vertices'](b)
    if np.any(av.max(0)+.003<bv.min(0)) or np.any(bv.max(0)+.003<av.min(0)):return False
    ar=G['H']['rotation'](G['render_element'](a).get('rotation',{}))
    br=G['H']['rotation'](G['render_element'](b).get('rotation',{}))
    for axis in [*ar.T,*br.T,*[np.cross(u,v) for u in ar.T for v in br.T]]:
        length=np.linalg.norm(axis)
        if length<1e-10:continue
        axis=axis/length;aa,bb=av@axis,bv@axis
        if aa.max()+.003<bb.min() or bb.max()+.003<aa.min():return False
    return True


class ColdDenialArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meshes,cls.meta=G['source_meshes']();cls.outputs=G['generate']()
        cls.d=json.loads(cls.outputs[G['ART']+'design.json'])
        cls.m=json.loads(cls.outputs[G['ART']+'manifest.json'])
        cls.model=json.loads(cls.outputs[G['MODEL']]);cls.es=cls.model['elements']
        cls.by_name={e['name']:e for e in cls.es}
        cls.atlas=np.asarray(Image.open(io.BytesIO(cls.outputs[G['TEXTURE']])).convert('RGBA'))

    def occupied(self,p):return any(contains(e,p) for e in self.es)

    def test_01_scope_and_portable_baseline_provenance(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w138/batch.json').read_bytes())
        feature=next(f for f in batch['features'] if f['name']=='w138-cold_denial')
        authored={'scripts/generate_surface_w123_cold_denial.py','scripts/qa/test_surface_w123_cold_denial.py'}
        self.assertEqual(set(feature['owned_paths']),set(self.outputs)|authored)
        self.assertEqual(len(feature['owned_paths']),10)
        if str(ROOT)==feature['destination']:
            gd=Path((ROOT/'.git').read_text().strip().split(': ',1)[1])
            provenance=json.loads((gd/'worktree-batch.json').read_bytes())
            self.assertEqual(provenance['baseline_sha256'],BASELINE)
            self.assertEqual(provenance['status'],'ready')
            self.assertEqual(provenance['owned_paths'],feature['owned_paths'])
        else:
            # Main integration is accepted via the exact export and its before/
            # after records, rather than an assertion tied to a worker-only cwd.
            export=Path(feature['destination']+'-export')
            provenance=json.loads((export/'manifest.json').read_bytes())
            self.assertEqual(provenance['baseline_sha256'],BASELINE)
            self.assertEqual(provenance['status'],'exported')
            self.assertEqual(provenance['out_of_scope'],[])
            self.assertEqual(provenance['source'],str(ROOT))
            self.assertEqual({f['path'] for f in provenance['files']},set(feature['owned_paths']))
            for f in provenance['files']:
                self.assertEqual(G['sha']((ROOT/f['path']).read_bytes()),f['after']['sha256'])
        self.assertTrue(self.m['full_only']);self.assertNotIn('overrides',self.model)

    def test_02_semantic_count_and_filled_mass(self):
        self.assertEqual(self.m['assembled_elements'],len(self.es))
        self.assertGreaterEqual(len(self.es),80);self.assertLessEqual(len(self.es),1000)
        self.assertEqual(self.m['triangle_adapter_elements'],0)
        self.assertEqual(sum(self.m['groups'].values()),len(self.es))
        for name,minimum in [('upper_receiver_core',25),('lower_receiver_core',30),('stock_upper_core',25),('grip_core',4)]:
            e=self.by_name[name];self.assertGreater(np.prod(np.array(e['to'])-e['from']),minimum)
        for p in ([8,13,0],[8,10.8,0],[8,12.7,15],[8,8,8],[8,8,12.14]):
            self.assertTrue(self.occupied(p),p)

    def test_03_positive_six_face_cuboids_and_opaque_atlas(self):
        self.assertEqual(len(self.by_name),len(self.es))
        for e in self.es:
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertTrue(np.all(np.array(e['to'])-e['from']>=.12-1e-7),e['name'])
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertNotIn('vertices',e);self.assertNotIn('triangles',e)
            for f in e['faces'].values():
                self.assertEqual(f['texture'],'#0');self.assertNotIn('cullface',f)
        self.assertEqual(self.atlas.shape,(1024,1024,4));self.assertTrue((self.atlas[:,:,3]==255).all())
        self.assertEqual(self.m['alpha_elements'],0)

    def test_04_real_bores_sight_trigger_and_stock_voids(self):
        for y,last in ((13.35,-6.0),(10.36,-5.68)):
            for z in np.linspace(-6.68,last,11):
                self.assertFalse(self.occupied([8,y,z]),('bore',y,z))
            self.assertTrue(self.occupied([8,y,last+.4]),'deep bore back')
        for y in np.linspace(14.65,15.4,7):
            self.assertFalse(self.occupied([8,y,5.53]),'open top sight')
        for x in np.linspace(7.2,8.8,9):
            self.assertFalse(self.occupied([x,10,5.86]),'trigger opening')
            self.assertFalse(self.occupied([x,9,15.4]),'stock/magazine clearance')
        self.assertTrue(self.occupied([8,10,5.26]),'solid guard front')
        self.assertTrue(self.occupied([8,9.34,6.08]),'solid guard bottom')

    def test_05_single_connected_solid_assembly(self):
        reached={0};pending=set(range(1,len(self.es)))
        while pending:
            new={j for j in pending if any(connected(self.es[i],self.es[j]) for i in reached)}
            if not new:break
            reached|=new;pending-=new
        self.assertFalse(pending,', '.join(self.es[i]['name'] for i in sorted(pending)))

    def test_06_exact_canonical_frame_and_source_envelope(self):
        canonical=json.loads((ROOT/G['BASE']).read_bytes())
        self.assertEqual(self.model['display'],canonical['display'])
        self.assertEqual(self.d['coordinate_policy']['anchor'],[8,8,8])
        self.assertEqual(self.m['source_scale'],self.meta['scale'])
        self.assertEqual(self.d['coordinate_policy']['muzzle'],'-Z')
        self.assertTrue(contains(self.by_name['grip_core'],[8,8,8]))
        ps=np.concatenate([G['vertices'](e) for e in self.es])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],self.meta['model_bounds'],atol=.025,rtol=0)
        self.assertEqual(self.m['actual_bounds'],[ps.min(0).tolist(),ps.max(0).tolist()])
        self.assertTrue(self.m['existing_generic_handling_unchanged'])
        self.assertTrue(self.m['combat_audio_timing_unchanged'])

    def test_07_raw_basis_and_input_hashes(self):
        self.assertEqual(sorted(m['name'] for m in self.meshes),sorted(self.meta['source_objects']))
        self.assertEqual(sum(len(m['faces']) for m in self.meshes),24191)
        self.assertTrue(set(self.meta['excluded_objects']).isdisjoint(m['name'] for m in self.meshes))
        ps=np.concatenate([m['vertices'] for m in self.meshes])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],self.meta['model_bounds'],atol=2e-6,rtol=0)
        raw=((ps-self.meta['anchor'])/self.meta['scale'])[:,[0,2,1]]
        np.testing.assert_allclose([raw.min(0),raw.max(0)],self.meta['source_bounds'],atol=4e-8,rtol=0)
        for p,digest in self.m['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest,p)
        for p,digest in self.m['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),digest,p)

    def test_08_independent_proportional_uvs_and_gutters(self):
        used=np.zeros((1024,1024),bool);islands=self.d['atlas']['islands']
        self.assertEqual(len(islands),6*len(self.es))
        for island in islands:
            x,y,xx,yy=island['pixels']
            self.assertGreaterEqual(min(x,y),2);self.assertLessEqual(max(xx,yy),1022)
            self.assertFalse(used[y-2:yy+2,x-2:xx+2].any());used[y-2:yy+2,x-2:xx+2]=True
            tile=self.atlas[y:yy,x:xx]
            np.testing.assert_array_equal(self.atlas[y-2:yy+2,x-2:xx+2],np.pad(tile,((2,2),(2,2),(0,0)),mode='edge'))
            e=self.by_name[island['element']];face=island['face'];p=G['vertices'](e)[list(G['FACES'][face])]
            np.testing.assert_allclose(np.array(e['faces'][face]['uv'])*64,island['pixels'])
            self.assertLess(abs(xx-x-np.linalg.norm(p[1]-p[0])*23),4.01)
            self.assertLess(abs(yy-y-np.linalg.norm(p[3]-p[0])*23),4.01)
        self.assertLessEqual(self.d['atlas']['used_height'],1024)

    def test_09_editable_inspection_parity(self):
        bb=json.loads(self.outputs[G['ART']+'inspection.bbmodel'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),self.outputs[G['TEXTURE']])
        self.assertEqual(bb['display'],self.model['display'])
        bes={e['name']:e for e in bb['elements']};self.assertEqual(set(bes),set(self.by_name))
        self.assertEqual(sum(len(g['children']) for g in bb['outliner']),len(self.es))
        self.assertEqual(len({e['uuid'] for e in bes.values()}),len(self.es))
        for name,e in self.by_name.items():
            b=bes[name];self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            r=e.get('rotation');self.assertEqual(b['rotation'],[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
            for face in G['FACES']:np.testing.assert_allclose(np.array(e['faces'][face]['uv'])*64,b['faces'][face]['uv'])
        self.assertFalse(bb['destiny_w138']['nativeAccepted']);self.assertTrue(bb['destiny_w138']['fullOnly'])

    def test_10_manifest_hashes_and_native_limits(self):
        self.assertEqual(self.m['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_cold_denial.py').read_bytes()))
        for p,digest in self.m['output_sha256'].items():self.assertEqual(G['sha'](self.outputs[p]),digest,p)
        self.assertFalse(self.m['native_accepted']);self.assertEqual(len(self.m['limitations']),4)
        self.assertIn('pending master',self.m['limitations'][-1])

    def test_11_byte_deterministic_artifacts_and_output_budget(self):
        for p,data in self.outputs.items():self.assertEqual((ROOT/p).read_bytes(),data,p)
        self.assertLess(sum(len(data) for data in self.outputs.values()),25*1024*1024)

    def test_12_comparison_contains_three_views_and_detail_panels(self):
        im=Image.open(io.BytesIO(self.outputs[G['ART']+'comparison.png']))
        self.assertEqual(im.size,(3000,1950));arr=np.asarray(im)
        for col in range(3):
            for row in range(3):
                self.assertGreater(arr[515+row*375:800+row*375,col*1000+55:col*1000+945].std(),9)
        for col in range(4):self.assertGreater(arr[1650:1880,col*750+100:col*750+650].std(),8)


if __name__=='__main__':unittest.main(verbosity=2)
