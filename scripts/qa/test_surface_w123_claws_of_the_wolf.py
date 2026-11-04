#!/usr/bin/env python3
"""Targeted offline W138 geometry/material/source and reproducibility checks.

No native/DCC launch or dependency writes; bundled Python -B only.
"""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
G = runpy.run_path(str(ROOT/'scripts/generate_surface_w123_claws_of_the_wolf.py'))


def contains(e, point):
    p=np.array(point,float);r=e.get('rotation')
    if r:
        origin=np.array(r['origin']);p=(p-origin)@G['rotation'](r)+origin
    return bool(np.all(p>=np.array(e['from'])-1e-7) and np.all(p<=np.array(e['to'])+1e-7))


def connected(a,b):
    """Separating-axis test on actual rotated solids, not only their AABBs."""
    av,bv=G['vertices'](a),G['vertices'](b)
    if np.any(av.max(0)+.003<bv.min(0)) or np.any(bv.max(0)+.003<av.min(0)):
        return False
    ar,br=G['rotation'](a.get('rotation',{})),G['rotation'](b.get('rotation',{}))
    for axis in [*ar.T,*br.T,*[np.cross(u,v) for u in ar.T for v in br.T]]:
        length=np.linalg.norm(axis)
        if length<1e-10:continue
        axis=axis/length;aa,bb=av@axis,bv@axis
        if aa.max()+.003<bb.min() or bb.max()+.003<aa.min():return False
    return True


class ClawsOfTheWolfArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meshes,cls.meta=G['source_meshes']()
        # Regenerate all outputs, including actual-source comparison, in RAM.
        cls.outputs=G['generate']()
        cls.d=json.loads(cls.outputs[G['ART']+'design.json'])
        cls.m=json.loads(cls.outputs[G['ART']+'manifest.json'])
        cls.model=json.loads(cls.outputs[G['MODEL']])
        cls.es=cls.model['elements'];cls.by_name={e['name']:e for e in cls.es}
        cls.atlas=np.asarray(Image.open(io.BytesIO(cls.outputs[G['TEXTURE']])).convert('RGBA'))

    def occupied(self,point):
        return any(contains(e,point) for e in self.es)

    def test_01_exact_ten_owned_paths(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w138/batch.json').read_bytes())
        feature=next(f for f in batch['features'] if f['name']=='w138-'+G['ID'])
        authored={'scripts/generate_surface_w123_'+G['ID']+'.py',
                  'scripts/qa/test_surface_w123_'+G['ID']+'.py'}
        self.assertEqual(set(feature['owned_paths']),set(self.outputs)|authored)
        self.assertEqual(len(feature['owned_paths']),10)
        if feature['destination'] != str(ROOT):
            # This art regression also runs in main after exact-path integration.
            # Export provenance, not a worker-only absolute cwd, is the contract.
            integration=json.loads((ROOT/'docs/qa/2026-10-26/w138'/
                                    (G['ID']+'-integration.json')).read_bytes())
            self.assertTrue(integration['mainBeforeAllMatched'])
            self.assertEqual(integration['status'],'integrated')
            self.assertEqual(integration['source'],feature['destination']+'-export')
            self.assertEqual(integration['outOfScope'],[])
            self.assertEqual({f['path'] for f in integration['files']},set(feature['owned_paths']))
            for f in integration['files']:
                self.assertEqual(G['sha']((ROOT/f['path']).read_bytes()), f['after']['sha256'], f['path'])
        self.assertEqual(self.m['candidate'],'FULL ONLY')
        self.assertNotIn('overrides',self.model)

    def test_02_emitted_budget_and_semantic_mass(self):
        self.assertEqual(self.m['assembled_elements'],len(self.es))
        self.assertLessEqual(self.m['assembled_elements'],1000)
        self.assertEqual(self.m['counts']['combined'],self.m['counts']['full'])
        self.assertEqual(self.m['triangle_adapter_elements'],0)
        self.assertEqual(sum(self.m['counts']['by_semantic_group'].values()),len(self.es))
        self.assertEqual(self.m['emitted_faces'],6*len(self.es))
        for name,minimum in [('receiver_core',15),('stock_core',9),('grip_core',3)]:
            e=self.by_name[name]
            self.assertGreater(np.prod(np.array(e['to'])-e['from']),minimum)
        # Cross-section centers must be filled; two side skins cannot pass.
        for p in ([8,10.8,0],[8,10.8,12.5],[8,8,8],[8,9.6,-.30]):
            self.assertTrue(self.occupied(p),p)

    def test_03_closed_positive_opaque_cuboids(self):
        self.assertEqual(len(self.by_name),len(self.es))
        for e in self.es:
            self.assertTrue(np.isfinite(G['vertices'](e)).all(),e['name'])
            self.assertTrue(np.all(np.array(e['to'])-e['from']>=.075),e['name'])
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertNotIn('vertices',e)
            for face in e['faces'].values():
                self.assertEqual(face['texture'],'#0')
                self.assertNotIn('cullface',face)
        self.assertEqual(self.atlas.shape,(1024,1024,4))
        self.assertTrue(np.all(self.atlas[:,:,3]==255))
        self.assertEqual(self.m['alpha_elements'],0)

    def test_04_actual_apertures_and_bore_depth(self):
        # Inspect the assembled solids; neighbouring masses cannot be hidden.
        for z in np.linspace(-8.65,-7.12,10):
            self.assertFalse(self.occupied([8,11.12,z]),('claw gap',z))
            self.assertTrue(self.occupied([8,11.50,z]),'upper claw')
            self.assertTrue(self.occupied([8,10.74,z]),'lower claw')
        for z in np.linspace(-7.02,-5.70,10):
            self.assertFalse(self.occupied([8,11.12,z]),('recessed bore',z))
        self.assertTrue(self.occupied([8,11.12,-5.55]),'bore depth stop')
        for x in np.linspace(6.9,9.1,13):
            self.assertFalse(self.occupied([x,9.40,5.25]),'swept guard air')
            self.assertFalse(self.occupied([x,8.95,10.0]),'grip to magazine air')
        for z in np.linspace(4.10,4.48,6):
            self.assertFalse(self.occupied([8,12.53,z]),'optic lens recess')
        self.assertTrue(self.occupied([8,12.53,4.57]),'opaque recessed lens')

    def test_05_single_connected_assembly(self):
        reached={0};pending=set(range(1,len(self.es)))
        while pending:
            new={j for j in pending if any(connected(self.es[i],self.es[j]) for i in reached)}
            if not new:break
            reached|=new;pending-=new
        self.assertFalse(pending,'Detached solids: '+', '.join(self.es[i]['name'] for i in sorted(pending)))

    def test_06_canonical_frame_display_and_bounds(self):
        canonical=json.loads((ROOT/G['BASE']).read_bytes())
        self.assertEqual(self.model['display'],canonical['display'])
        self.assertEqual(self.d['coordinate_policy']['anchor'],[8,8,8])
        self.assertEqual(self.m['source_scale'],self.meta['scale'])
        self.assertEqual(self.m['source_axis'],self.meta['source_axis'])
        ps=np.concatenate([G['vertices'](e) for e in self.es])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],self.meta['model_bounds'],atol=.19,rtol=0)
        self.assertTrue(contains(self.by_name['grip_core'],[8,8,8]))
        self.assertEqual(self.m['actual_bounds'],[ps.min(0).tolist(),ps.max(0).tolist()])
        self.assertIn('existing generic reload',self.m['reload_policy'])

    def test_07_source_alignment_catalogue_and_hashes(self):
        self.assertEqual(sorted(m['name'] for m in self.meshes),sorted(self.meta['source_objects']))
        self.assertEqual(sum(len(m['faces']) for m in self.meshes),28292)
        self.assertTrue(set(self.meta['excluded_objects']).isdisjoint(m['name'] for m in self.meshes))
        ps=np.concatenate([m['vertices'] for m in self.meshes])
        np.testing.assert_allclose([ps.min(0),ps.max(0)],self.meta['model_bounds'],atol=2e-6,rtol=0)
        raw=(ps-self.meta['anchor'])/self.meta['scale']
        np.testing.assert_allclose([raw[:,[0,2,1]].min(0),raw[:,[0,2,1]].max(0)],
                                   self.meta['source_bounds'],atol=1e-7,rtol=0)
        self.assertEqual(self.d['catalogue']['family'],'pulse_rifle')
        self.assertEqual(self.d['catalogue']['frame'],'rapid_fire')
        self.assertEqual(self.d['catalogue']['bungie_hash'],'1280933460')
        for p,digest in self.m['input_sha256'].items():
            self.assertEqual(G['sha']((ROOT/p).read_bytes()),digest,p)
        for p,digest in self.m['raw_input_sha256'].items():
            self.assertEqual(G['sha'](Path(p).read_bytes()),digest,p)
        self.assertEqual(self.m['default_photo_sha256'],G['sha'](G['PHOTO'].read_bytes()))

    def test_08_independent_proportional_uv_and_extruded_gutters(self):
        islands=self.d['atlas']['islands'];self.assertEqual(len(islands),6*len(self.es))
        used=np.zeros((1024,1024),bool);unique=set()
        for island in islands:
            x,y,xx,yy=island['rect'];rect=tuple(island['rect'])
            self.assertNotIn(rect,unique);unique.add(rect)
            self.assertGreaterEqual(x,2);self.assertGreaterEqual(y,2)
            self.assertLessEqual(xx,1022);self.assertLessEqual(yy,1022)
            self.assertFalse(used[y-2:yy+2,x-2:xx+2].any());used[y-2:yy+2,x-2:xx+2]=True
            tile=self.atlas[y:yy,x:xx]
            np.testing.assert_array_equal(self.atlas[y-2:yy+2,x-2:xx+2],np.pad(tile,((2,2),(2,2),(0,0)),mode='edge'))
            e=self.by_name[island['element']];face=island['face']
            np.testing.assert_allclose(np.array(e['faces'][face]['uv'])*1024/16,island['rect'])
            if next(p for p in self.d['parts']['full'] if p['geometry']['name']==e['name'])['motif']=='wolf' and face in ('east','west'):
                self.assertEqual((xx-x,yy-y),(32,32))
                continue
            ps=G['vertices'](e)[list(G['FACES'][face])]
            self.assertLess(abs((xx-x)-np.linalg.norm(ps[1]-ps[0])*self.d['atlas']['texels_per_unit']),6.01)
            self.assertLess(abs((yy-y)-np.linalg.norm(ps[3]-ps[0])*self.d['atlas']['texels_per_unit']),6.01)
        self.assertLessEqual(self.d['atlas']['used_height'],1024)

    def test_09_editable_bb_exact_atlas_and_geometry(self):
        bb=json.loads(self.outputs[G['ART']+'inspection.bbmodel'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),self.outputs[G['TEXTURE']])
        self.assertEqual(bb['display'],self.model['display'])
        self.assertEqual(len(bb['elements']),len(self.es))
        self.assertEqual(sum(len(g['children']) for g in bb['outliner']),len(self.es))
        self.assertEqual(len({e['uuid'] for e in bb['elements']}),len(self.es))
        for e,b in zip(self.es,bb['elements']):
            self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            r=e.get('rotation',{})
            self.assertEqual(b['rotation'],[r.get(a,0) for a in 'xyz'])
            self.assertEqual(b['origin'],r.get('origin',[8,8,8]))
            self.assertFalse(b['box_uv'])
            for f in G['FACES']:
                np.testing.assert_allclose(np.array(e['faces'][f]['uv'])*1024/16,b['faces'][f]['uv'])
                self.assertEqual(b['faces'][f]['texture'],0)
        self.assertFalse(bb['destiny_w138']['nativeAccepted'])

    def test_10_manifest_content_and_native_limits(self):
        self.assertEqual(self.m['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_claws_of_the_wolf.py').read_bytes()))
        for path,digest in self.m['output_sha256'].items():
            self.assertEqual(G['sha'](self.outputs[path]),digest,path)
        self.assertFalse(self.m['native_accepted'])
        self.assertTrue(any('pending master' in s for s in self.m['limitations']))
        self.assertGreaterEqual(len(self.m['limitations']),4)

    def test_11_byte_deterministic_delivered_artifacts(self):
        # Complete independent regeneration is compared to disk, including PNG
        # and embedded BB bytes. --verify repeats this sequentially after tests.
        for path,data in self.outputs.items():
            self.assertTrue((ROOT/path).is_file(),path)
            self.assertEqual((ROOT/path).read_bytes(),data,path)

    def test_12_comparison_is_three_view_source_and_candidate_sheet(self):
        im=Image.open(io.BytesIO(self.outputs[G['ART']+'comparison.png']))
        self.assertEqual(im.size,(3000,1960))
        arr=np.asarray(im)
        for col in range(3):
            for row in range(3):
                self.assertGreater(arr[500+row*360:810+row*360,col*1000+60:col*1000+950].std(),10)


if __name__=='__main__':
    unittest.main(verbosity=2)
