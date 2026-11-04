#!/usr/bin/env python3
"""Small offline Duke W127 regression: emitted geometry/UV/frame/reproducibility.

No native/parser/game/performance acceptance is implied by these Python checks.
"""
import ast
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
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_duke_mk_44.py'))


class DukeSurfaceSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models={p:json.loads((ROOT/(G['MODEL']+suffix+'.json')).read_bytes())
                    for p,suffix in [('full',''),('body','_body'),('cylinder','_cylinder')]}
        cls.design=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        cls.manifest=json.loads((ROOT/(G['ART']+'manifest.json')).read_bytes())
        cls.helper=G['renderer']()
        cls.elements=cls.models['full']['elements']
        cls.byname={e['name']:e for e in cls.elements}

    @classmethod
    def occupied(cls,point,e):
        origin=np.array(e['rotation']['origin'])
        local=(np.array(point)-origin)@cls.helper['rotation'](e['rotation'])+origin
        return bool(np.all(local>np.array(e['from'])+1e-6) and np.all(local<np.array(e['to'])-1e-6))

    def air(self,p,label='',elements=None):
        elements=self.elements if elements is None else elements
        blocked=[e['name'] for e in elements if self.occupied(p,e)]
        self.assertFalse(blocked,f'{label} {p}: {blocked}')

    def test_native_schema_and_exact_canonical_display(self):
        self.assertEqual(self.models['full']['display'],json.loads((ROOT/G['BASE']).read_bytes())['display'])
        for part,m in self.models.items():
            if part!='full':self.assertNotIn('display',m)
            self.assertEqual(set(m),{'credit','textures','elements','display'} if part=='full' else {'credit','textures','elements'})
            self.assertEqual(m['textures']['0'],'destiny:item/weapon/w123/duke_mk_44')
            for e in m['elements']:
                self.assertEqual(set(e),{'name','from','to','rotation','faces'})
                self.assertEqual(set(e['faces']),set(G['FACES']))
                self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
                for a,b in zip(e['from'],e['to']):
                    self.assertTrue(math.isfinite(a) and math.isfinite(b) and -16<=a<b<=32)
                    self.assertGreater(b-a,.06)
                self.assertTrue(all(math.isfinite(x) for x in e['rotation']['origin']))
                for face in e['faces'].values():
                    self.assertEqual(set(face),{'uv','texture'})
                    self.assertEqual(face['texture'],'#0')
                    u0,v0,u1,v1=face['uv']
                    self.assertTrue(all(math.isfinite(x) and 0<=x<=16 for x in face['uv']))
                    self.assertGreater(u1-u0,0);self.assertGreater(v1-v0,0)

    def test_full_is_split_assembly_and_budget(self):
        body=self.models['body']['elements'];cyl=self.models['cylinder']['elements']
        self.assertEqual(self.elements,body+cyl)
        self.assertGreater(len(body),0);self.assertGreater(len(cyl),0)
        self.assertLessEqual(len(body)+len(cyl),1000)
        self.assertEqual(len(self.byname),len(self.elements))
        self.assertEqual(self.manifest['counts'],{'body':len(body),'cylinder':len(cyl),'full':len(body)+len(cyl)})
        self.assertTrue(all(e['name'].startswith(('Cylinder_','Chamber_','Yoke_')) for e in cyl))
        self.assertFalse({e['name'] for e in body}&{e['name'] for e in cyl})
        self.assertEqual(self.manifest['emitted_faces'],6*len(self.elements))

    def test_historical_delta_and_w64_pivot(self):
        canonical=json.loads((ROOT/G['BASE']).read_bytes())
        body=json.loads((ROOT/(G['RELOAD']+'_body.json')).read_bytes())
        cyl=json.loads((ROOT/(G['RELOAD']+'_cylinder.json')).read_bytes())
        self.assertEqual([len(canonical['elements']),len(body['elements']),len(cyl['elements'])],[232,211,23])
        source=ast.parse((ROOT/'scripts/generate_reload_models_w64.py').read_text())
        pivot=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id=='PIVOT' for t in n.targets))
        self.assertEqual(self.design['cylinder_pivot'],pivot)
        self.assertEqual(self.manifest['cylinder_pivot'],[8,10.2,5.17])
        self.assertIn('2 moving yoke',self.design['canonical_reload_delta']['reason'])
        self.assertIn('shortened',self.design['yoke_shape_delta'])
        vertical=self.byname['Yoke_vertical'];arm=self.byname['Yoke_arm']
        self.assertEqual(vertical['from'],[7.78,10.2,4.97])
        self.assertEqual(vertical['to'],[8.22,11.72,5.37])
        self.assertEqual(arm['from'],[7.78,11.5,3.7])
        self.assertEqual(arm['to'],[8.22,11.8,5.37])

    def test_original_world_frame_and_solid_grip(self):
        self.assertEqual(self.design['anchor'],[8,8,8])
        self.assertAlmostEqual(self.design['source']['scale'],40.55098717904924)
        self.assertEqual(self.design['source']['source_axis'],{'length':0,'thin':1,'muzzle_sign':1})
        points=np.concatenate([self.helper['vertices'](e) for e in self.elements])
        original=np.array(self.design['source']['model_bounds'])
        self.assertTrue(np.all(points.min(0)>original[0]-.18))
        self.assertTrue(np.all(points.max(0)<original[1]+.18))
        # Original hand, barrel and cylinder remain in the same coordinate frame.
        self.assertEqual(self.byname['Muzzle_lip_0']['rotation']['origin'][1],11.94)
        self.assertLess(self.byname['Muzzle_lip_0']['rotation']['origin'][2],-5.8)
        for p in ([8,12.1,-1.5],[8,10.1,7.7],[8,9.4,8.3],[8,8.0,8.5],[8,13.0,6.3]):
            self.assertTrue(any(self.occupied(p,e) for e in self.elements),p)
        self.assertGreater(self.byname['Shroud_lower']['to'][0]-self.byname['Shroud_lower']['from'][0],1.5)
        self.assertGreater(self.byname['Grip_palm_wood']['to'][0]-self.byname['Grip_palm_wood']['from'][0],1.4)

    def test_real_openings_and_muzzle_depth(self):
        for label,p in self.design['required_air_probes'].items():self.air(p,label)
        for z in (-6.10,-5.92,-5.6,-5.3,-5.02):
            for a in range(0,360,45):
                t=math.radians(a);self.air([8+.20*math.cos(t),11.94+.20*math.sin(t),z],'muzzle')
        self.assertTrue(self.occupied([8,11.94,-4.91],self.byname['Muzzle_recess']))
        self.assertEqual(sum(e['name'].startswith('Muzzle_lip_') for e in self.elements),8)
        self.assertEqual(sum(e['name'].startswith('Muzzle_bore_') for e in self.elements),8)
        for z in (-5.30,-5.17,-5.03):self.air([8,13.3,z],'front housing recess')
        for z in (-3.30,-2.0,-.1):self.air([8,10.7,z],'underbarrel slot')

    def test_six_actual_through_chambers(self):
        centers=self.design['chamber_centers'];self.assertEqual(len(centers),6)
        cylinder=self.models['cylinder']['elements']
        for i,(x,y) in enumerate(centers):
            self.assertEqual(sum(e['name'].startswith(f'Chamber_{i}_') for e in cylinder),8)
            for z in self.design['chamber_air_z']:
                self.air([x,y,z],f'chamber {i} axis')
                for a in range(0,360,45):
                    t=math.radians(a)
                    self.air([x+.17*math.cos(t),y+.17*math.sin(t),z],f'chamber {i} aperture')
            # Bores have steel walls, not a solid black dot masquerading as a hole.
            e=self.byname[f'Chamber_{i}_0']
            self.assertTrue(self.occupied(e['rotation']['origin'],e))
        self.assertEqual(sum(e['name'].startswith('Cylinder_shell_') for e in cylinder),12)
        self.assertEqual(sum(e['name'].startswith('Cylinder_web_') for e in cylinder),6)

    def test_face_uv_opaque_nonoverlap_and_proportions(self):
        atlas=np.array(Image.open(ROOT/G['TEXTURE']))
        self.assertEqual(atlas.shape,(1024,1024,4))
        mask=np.zeros((1024,1024),bool)
        self.assertEqual(self.design['atlas']['face_islands'],6*len(self.elements))
        self.assertGreater(self.design['atlas']['used_texels'],200000)
        for island in self.design['atlas']['islands']:
            x0,y0,x1,y1=island['pixels'];region=np.s_[y0-2:y1+2,x0-2:x1+2]
            self.assertFalse(mask[region].any(),island);mask[region]=True
            self.assertTrue((atlas[region][:,:,3]==255).all(),island)
            p=self.helper['vertices'](self.byname[island['element']])[list(G['FACES'][island['face']])]
            width=np.linalg.norm(p[1]-p[0]);height=np.linalg.norm(p[3]-p[0])
            if min(x1-x0,y1-y0)>4:
                self.assertLessEqual(max((x1-x0-1)/width,(y1-y0-1)/height),min((x1-x0)/width,(y1-y0)/height)+1e-5)
        for name in ('Shroud_lower','Grip_palm_wood','Cylinder_shell_0'):
            e=self.byname[name];self.assertNotEqual(e['faces']['east']['uv'],e['faces']['west']['uv'])
        uv=self.byname['Shroud_lower']['faces']['west']['uv'];x0,y0,x1,y1=[round(v*1024/16) for v in uv]
        tile=atlas[y0:y1,x0:x1,:3]
        self.assertGreater(np.all(tile==[24,28,29],axis=2).sum(),10) # actual authored two vent marks

    def test_editable_inspection_and_embedded_texture(self):
        bb=json.loads((ROOT/(G['ART']+'inspection.bbmodel')).read_bytes())
        self.assertEqual(len(bb['elements']),len(self.elements))
        self.assertEqual([g['name'] for g in bb['outliner']],['body','cylinder'])
        self.assertEqual(bb['outliner'][1]['origin'],[8,10.2,5.17])
        self.assertEqual(bb['display'],self.models['full']['display'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        self.assertFalse(bb['destiny_w123']['nativeAccepted'])
        self.assertEqual(len({e['uuid'] for e in bb['elements']}),len(self.elements))

    def test_evidence_pins_and_reference_palette(self):
        for p,h in self.manifest['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        for p,h in self.manifest['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),h,p)
        for p,h in self.manifest['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        self.assertIn('restored the actual W31 blue/black',self.design['paint_evidence']['paint_correction'])
        self.assertGreater(G['PALETTE']['yellow'][2], G['PALETTE']['yellow'][0]+60)
        self.assertLess(max(G['PALETTE']['wood']),50)
        self.assertLess(G['PALETTE']['wood'][0],G['PALETTE']['wood'][2])
        self.assertIn('[0.12,0.22,0.65,1]',self.design['paint_evidence']['local_palette_record'])
        self.assertEqual(self.manifest['alpha_contour_elements'],0)
        self.assertEqual(self.manifest['triangle_adapter_elements'],0)
        self.assertFalse(self.manifest['native_accepted'])
        self.assertEqual(self.manifest['validation']['performance'],'not measured; offline only')

    def test_owned_paths_and_complete_deterministic_regeneration(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w127/batch.json').read_bytes())
        owned=set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w127-duke_mk_44'))
        self.assertEqual(len(owned),12)
        outputs=G['generate']()
        self.assertEqual(set(outputs)|{G['GENERATOR'],G['TEST'],G['WORKER']},owned)
        for p,b in outputs.items():self.assertEqual((ROOT/p).read_bytes(),b,p)
        im=Image.open(io.BytesIO(outputs[G['ART']+'comparison.png']))
        self.assertEqual(im.size,(1800,2320))


if __name__=='__main__':unittest.main()
