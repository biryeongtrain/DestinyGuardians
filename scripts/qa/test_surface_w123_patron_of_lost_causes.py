#!/usr/bin/env python3
"""Focused offline asset regression; native acceptance belongs to master."""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_patron_of_lost_causes.py'))
ART=G['ART'];MODEL=G['MODEL'];TEXTURE=G['TEXTURE']

class PatronSurfaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((ROOT/ART/'design.json').read_bytes())
        cls.m=json.loads((ROOT/MODEL).read_bytes())
        cls.man=json.loads((ROOT/ART/'manifest.json').read_bytes())
        cls.bb=json.loads((ROOT/ART/'inspection.bbmodel').read_bytes())
        cls.atlas=Image.open(ROOT/TEXTURE).convert('RGBA')

    def hits(self,origin,direction):
        """Local-box ray intersection for the handful of signature openings."""
        hits=[]
        for e in self.m['elements']:
            r=e['rotation'];R=G['helper']()['rotation'](r);c=np.array(r['origin'])
            o=(np.array(origin)-c)@R+c;v=np.array(direction)@R
            lo=np.array(e['from']);hi=np.array(e['to']);a=-np.inf;b=np.inf
            for i in range(3):
                if abs(v[i])<1e-9:
                    if not lo[i]<o[i]<hi[i]:break
                else:
                    t=sorted(((lo[i]-o[i])/v[i],(hi[i]-o[i])/v[i]));a=max(a,t[0]);b=min(b,t[1])
            else:
                if b>=max(a,0):hits.append((max(a,0),e['name']))
        return sorted(hits)

    def test_full_schema_and_assembled_budget(self):
        es=self.m['elements'];self.assertEqual(len(es),98)
        self.assertEqual(self.man['counts'],{'full':98});self.assertLessEqual(len(es),1000)
        self.assertTrue(self.man['full_only']);self.assertFalse(self.man['native_accepted'])
        self.assertEqual(self.man['triangle_adapter_elements'],0)
        self.assertEqual(self.man['alpha_contour_elements'],0)
        self.assertEqual(len({e['name'] for e in es}),len(es))
        for e in es:
            self.assertEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
        self.assertEqual(sum(self.man['semantic_groups'].values()),98)

    def test_face_uv_atlas_and_texture_references(self):
        self.assertEqual(self.atlas.size,(1024,1024));a=np.array(self.atlas)
        self.assertEqual(self.man['emitted_faces'],588)
        self.assertEqual(len(self.d['atlas']['islands']),588)
        self.assertEqual(self.m['textures']['0'],'destiny:item/weapon/w123/patron_of_lost_causes')
        by_name={e['name']:e for e in self.m['elements']}
        for island in self.d['atlas']['islands']:
            x,y,x1,y1=island['pixels'];self.assertTrue(0<x<x1<1024 and 0<y<y1<1024)
            f=by_name[island['element']]['faces'][island['face']]
            self.assertEqual(f['uv'],[v/64 for v in [x,y,x1,y1]])
            self.assertEqual(f['texture'],'#0');self.assertTrue((a[y:y1,x:x1,3]==255).all())

    def test_photo_raw_and_input_provenance(self):
        meta=json.loads((ROOT/G['BB']).read_bytes())['destiny_w30']
        self.assertEqual(meta,self.d['source_metadata']);self.assertEqual(meta['source_triangles'],29158)
        for path,digest in self.d['input_sha256'].items():self.assertEqual(G['sha']((ROOT/path).read_bytes()),digest,path)
        for path,digest in self.d['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(path).read_bytes()),digest,path)
        ref=next(r for r in json.loads((ROOT/'art/weapons/w31/references.json').read_bytes()) if r['id']==self.d['id'])
        self.assertEqual(G['sha'](G['PHOTO'].read_bytes()),ref['sha256'])
        self.assertEqual(ref['bungie_hash'],'2723241847')
        self.assertIn('canonical W30',self.man['comparison_reference'])

    def test_existing_frame_display_and_full_only(self):
        canonical=json.loads((ROOT/G['BASE']).read_bytes())
        self.assertEqual(self.m['display'],canonical['display'])
        self.assertEqual(self.d['anchor'],[8,8,8]);self.assertEqual(self.d['scale'],23.684066163425207)
        lo,hi=np.array(self.man['actual_bounds']);source=np.array(self.d['source_metadata']['model_bounds'])
        self.assertLess(abs(lo[2]-source[0,2]),.01)
        self.assertLess(abs(hi[2]-source[1,2]),.15)
        self.assertTrue(np.all(np.abs(np.array([lo,hi])-source)<.45))
        self.assertEqual(self.man['counts'].keys(),{'full'})
        self.assertTrue(all(not e['name'].startswith('split') for e in self.m['elements']))
        self.assertEqual(self.hits([0,8.3,8.49],[1,0,0])[0][1],'silver_grip_shoulder')

    def test_triangular_stock_and_guard_are_through_openings(self):
        for y,z in ((9.25,10.45),(8.25,10.35),(9.6,10.6),(9.08,6.20)):
            self.assertEqual(self.hits([0,y,z],[1,0,0]),[],(y,z))
        # Real solid boundaries remain around the stock opening.
        for name in ('aperture_rear_post','lower_diagonal_brace','stock_silver_comb','pistol_grip'):
            self.assertIn(name,{e['name'] for e in self.m['elements']})

    def test_scope_recess_bore_and_saddle_have_depth(self):
        h=self.hits([8,12.8,4.724],[0,0,1]);self.assertEqual(h[0][1],'front_recessed_glass')
        self.assertAlmostEqual(h[0][0],.4185,places=5)
        h=self.hits([8,12.8,7.991],[0,0,-1]);self.assertEqual(h[0][1],'rear_recessed_glass')
        self.assertAlmostEqual(h[0][0],.3335,places=5)
        h=self.hits([8,10.52,-8.93233],[0,0,1]);self.assertEqual(h[0][1],'bore_backstop')
        self.assertAlmostEqual(h[0][0],1.31233,places=5)
        self.assertEqual(self.hits([0,12.02,7.85],[1,0,0]),[])
        self.assertTrue(any(e['name']=='hook_tip' for e in self.m['elements']))

    def test_editable_inspection_matches_final_asset(self):
        self.assertEqual(len(self.bb['elements']),98)
        embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual(embedded,(ROOT/TEXTURE).read_bytes())
        for b,e in zip(self.bb['elements'],self.m['elements']):
            self.assertEqual(b['type'],'cube');self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['rotation'],[e['rotation'][a] for a in 'xyz'])
            for face in G['FACES']:self.assertEqual(b['faces'][face]['uv'],[v*64 for v in e['faces'][face]['uv']])
        self.assertEqual(self.bb['display'],self.m['display'])
        self.assertEqual(self.bb['resolution'],{'width':1024,'height':1024})
        self.assertEqual(len(self.bb['outliner']),len(self.d['groups']))

    def test_deterministic_regeneration_and_output_hashes(self):
        outputs=G['generate']()
        scope=set(next(f['owned_paths'] for f in json.loads((ROOT/'docs/qa/2026-10-26/w130/batch.json').read_bytes())['features'] if f['name']=='w130-patron_of_lost_causes'))
        self.assertEqual(len(scope),10);self.assertTrue(set(outputs)<=scope)
        for path,data in outputs.items():self.assertEqual((ROOT/path).read_bytes(),data,path)
        for path,digest in self.man['output_sha256'].items():self.assertEqual(G['sha']((ROOT/path).read_bytes()),digest,path)
        self.assertEqual(G['sha']((ROOT/'scripts/generate_surface_w123_patron_of_lost_causes.py').read_bytes()),self.man['generator_sha256'])
        image=Image.open(io.BytesIO(outputs[ART+'comparison.png']));self.assertEqual(image.size,(2100,1980))

if __name__=='__main__':unittest.main(verbosity=2)
