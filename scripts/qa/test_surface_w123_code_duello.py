#!/usr/bin/env python3
"""Targeted Code Duello offline art regression; live acceptance belongs to master."""
import base64
import io
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_code_duello.py'))
PHOTO_SHA='01bb55eb7026cb4ab762df9b406628e0a89307ef8a189ec0dabe57be9c3b6366'

class CodeDuelloSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=json.loads((ROOT/G['MODEL']).read_bytes())
        cls.d=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        cls.m=json.loads((ROOT/(G['ART']+'manifest.json')).read_bytes())
        cls.h=G['helper']();cls.elements=cls.model['elements']
        cls.byname={e['name']:e for e in cls.elements};cls.atlas=np.array(Image.open(ROOT/G['TEXTURE']))

    @classmethod
    def occupied(cls,p,e):
        r=e['rotation'];o=np.array(r['origin']);local=(np.array(p)-o)@cls.h['rotation'](r)+o
        return bool(np.all(local>np.array(e['from'])+1e-6) and np.all(local<np.array(e['to'])-1e-6))

    def air(self,p):
        self.assertFalse([e['name'] for e in self.elements if self.occupied(p,e)],str(p))

    def solid(self,p):
        self.assertTrue(any(self.occupied(p,e) for e in self.elements),str(p))

    def test_full_schema_and_assembled_output_budget(self):
        self.assertEqual(set(self.model),{'credit','textures','elements','display'})
        self.assertEqual(self.model['textures']['0'],'destiny:item/weapon/w123/code_duello')
        self.assertTrue(0<len(self.elements)<=1000)
        self.assertEqual(len(self.elements),len(self.byname))
        self.assertEqual(self.m['counts'],{'full':len(self.elements)})
        self.assertEqual(self.m['assembled_elements'],len(self.elements))
        self.assertEqual(self.m['emitted_faces'],6*len(self.elements))
        self.assertEqual(self.m['triangle_adapter_elements'],0)
        self.assertEqual(self.m['alpha_contour_elements'],0)
        self.assertTrue(self.m['full_only'])
        for e in self.elements:
            self.assertEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
            self.assertEqual(set(e['faces']),set(G['FACES']))
            for a,b in zip(e['from'],e['to']):
                self.assertTrue(math.isfinite(a) and math.isfinite(b) and -16<=a<b<=32)
                self.assertGreater(b-a,.075)
            for f in e['faces'].values():
                self.assertEqual(set(f),{'uv','texture'});self.assertEqual(f['texture'],'#0')
                self.assertTrue(all(math.isfinite(x) and 0<=x<=16 for x in f['uv']))
                self.assertGreater(f['uv'][2],f['uv'][0]);self.assertGreater(f['uv'][3],f['uv'][1])

    def test_original_frame_full_display_and_filled_hand_landmarks(self):
        source=json.loads((ROOT/G['BB']).read_bytes())['destiny_w30']
        self.assertEqual(self.model['display'],json.loads((ROOT/G['BASE']).read_bytes())['display'])
        self.assertEqual(self.d['anchor'],source['anchor'])
        self.assertEqual(self.d['scale'],source['scale'])
        self.assertEqual(source['source_axis'],{'length':1,'thin':0,'muzzle_sign':-1})
        points=np.concatenate([self.h['vertices'](e) for e in self.elements]);bounds=np.array(source['model_bounds'])
        self.assertTrue(np.all(abs(points.min(0)-bounds[0])<.22))
        self.assertTrue(np.all(abs(points.max(0)-bounds[1])<.22))
        for p in ([8,8,8.4],[8,9.5,7.8],[8,8.8,2],[8,10.3,5],[8,12,0],[8,12,8],[8,12,16]):self.solid(p)
        heart=self.byname['Tube_solid_heart']
        self.assertGreater(heart['to'][0]-heart['from'][0],1.2)
        self.assertGreater(heart['to'][1]-heart['from'][1],1.2)
        self.assertGreater(heart['to'][2]-heart['from'][2],12)

    def test_copper_bore_and_original_side_optic_have_true_depth(self):
        for z in (-5.40,-5.10,-4.1,-3.0,-2.20):
            self.air([8,12,z]);self.air([8.22,12.12,z])
        self.assertTrue(self.occupied([8,12,-1.95],self.byname['Bore_backstop']))
        self.solid([8.61,12,-4.2])
        for z in (3.72,4.05,4.38,4.54):
            self.air([9.55,12,z]);self.air([9.67,12,z])
        self.assertTrue(self.occupied([9.55,12,4.67],self.byname['Optic_recessed_lens']))
        self.solid([9.98,12,3.86])
        self.assertGreater(self.byname['Optic_recessed_lens']['from'][2]-3.68,.85)

    def test_gold_cage_u_scallops_guard_and_sight_are_real_openings(self):
        for p in self.d['air_probes'].values():self.air(p)
        # A few useful rays in each key opening, not exhaustive art score gates.
        for side in (-1,1):
            for z in (-1,.1,2.9):
                self.air([8+side*.85,13.025,z]);self.air([8+side*.85,10.96,z])
            for z in (.25,.92,1.59,2.26,5.65,6.32,6.99,7.66):
                self.air([8+side*.85,13.73,z])
                self.solid([8+side*.85,13.50,z])
        for x in (7.8,8,8.2):
            for z in (5.85,6.05):self.air([x,9.15,z])
        for x in (7.9,8,8.1):self.air([x,13.09,19.75])
        self.solid([8.28,13.09,19.75]);self.solid([8,8.57,6.15])

    def test_uv_panels_are_opaque_nonoverlapping_with_dilated_gutters(self):
        self.assertEqual(self.atlas.shape,(1024,1024,4))
        ledger=self.d['atlas']['islands'];self.assertEqual(len(ledger),6*len(self.elements))
        used=np.zeros((1024,1024),bool)
        for q in ledger:
            x0,y0,x1,y1=q['pixels'];sl=np.s_[y0-2:y1+2,x0-2:x1+2]
            self.assertFalse(used[sl].any(),q);used[sl]=True
            self.assertTrue((self.atlas[sl][:,:,3]==255).all(),q)
            face=self.byname[q['element']]['faces'][q['face']]
            self.assertEqual([round(v*64) for v in face['uv']],[x0,y0,x1,y1])
        self.assertNotEqual(self.byname['Tube_2']['faces']['east']['uv'],self.byname['Tube_2']['faces']['west']['uv'])
        self.assertGreater(sum(np.prod(np.array(q['pixels'][2:])-q['pixels'][:2]) for q in ledger),200000)
        # Long tube gets continuous panels; no hundreds of narrow reprojected islands.
        self.assertGreater(self.byname['Tube_2']['to'][2]-self.byname['Tube_2']['from'][2],16)
        self.assertEqual(sum(s['group']=='main_tube' for s in self.d['solids']),9)

    def test_embedded_editable_solids_texture_and_display_match(self):
        bb=json.loads((ROOT/(G['ART']+'inspection.bbmodel')).read_bytes())
        self.assertEqual(len(bb['elements']),len(self.elements));self.assertEqual(bb['display'],self.model['display'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        self.assertEqual({v for group in bb['outliner'] for v in group['children']},{e['uuid'] for e in bb['elements']})
        self.assertFalse(bb['destiny_w132']['native_accepted'])
        for e,b in zip(self.elements,bb['elements']):
            self.assertEqual(b['type'],'cube');self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            self.assertEqual([e['rotation'][a] for a in 'xyz'],b['rotation'])
            self.assertEqual(e['rotation']['origin'],b['origin'])
            for f in G['FACES']:
                self.assertEqual([q*64 for q in e['faces'][f]['uv']],b['faces'][f]['uv'])

    def test_photo_raw_and_readonly_integration_provenance(self):
        self.assertEqual(G['sha'](G['PHOTO'].read_bytes()),PHOTO_SHA)
        refs=json.loads(G['REFERENCES'].read_bytes())
        self.assertEqual(next(r['sha256'] for r in refs if r['id']=='code_duello'),PHOTO_SHA)
        meshes,meta=G['source_meshes']()
        self.assertEqual({m['name'] for m in meshes},set(meta['source_objects']))
        self.assertEqual(sum(len(m['faces']) for m in meshes),33820)
        self.assertIn('not the finished default shader',self.d['paint_evidence']['raw_diffuse'])
        for p,h in self.m['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        for p,h in self.m['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),h,p)
        for p,h in self.m['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        self.assertEqual(self.m['generator_sha256'],G['sha']((ROOT/G['GENERATOR']).read_bytes()))
        self.assertFalse(self.m['native_accepted'])

    def test_exact_seven_generated_assets_ten_owned_paths_and_comparison(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w132/batch.json').read_bytes())
        owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w132-code_duello'))
        outputs=G['generate']()
        self.assertEqual(set(outputs)|{G['GENERATOR'],G['TEST'],G['WORKER']},owned)
        self.assertEqual(len(owned),10)
        for p,data in outputs.items():self.assertEqual((ROOT/p).read_bytes(),data,p)
        self.assertEqual([p for p in outputs if p.startswith(G['ASSET']+'models/')],[G['MODEL']])
        sheet=Image.open(io.BytesIO(outputs[G['ART']+'comparison.png']))
        self.assertEqual(sheet.size,(2100,1970))
        photo=Image.open(G['PHOTO']).convert('RGB');photo.thumbnail((1000,465))
        self.assertTrue(np.array_equal(np.array(sheet.crop((12,55,12+photo.width,55+photo.height))),np.array(photo)))
        self.assertLess(sum((ROOT/p).stat().st_size for p in owned if (ROOT/p).exists()),25*1024*1024)

if __name__=='__main__':unittest.main(verbosity=2)
