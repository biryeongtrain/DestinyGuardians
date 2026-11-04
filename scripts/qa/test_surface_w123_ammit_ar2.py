#!/usr/bin/env python3
"""Lightweight W126 Ammit semantic art regression tests; no DCC, Java, client or build."""
import io
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_ammit_ar2.py'))

class AmmitSurfaceSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models={p:json.loads((ROOT/(G['MODEL']+suffix+'.json')).read_bytes())
                    for p,suffix in [('full',''),('body','_body'),('magazine','_magazine')]}
        cls.manifest=json.loads((ROOT/(G['ART']+'manifest.json')).read_bytes())

    def test_native_schema_and_canonical_display(self):
        self.assertEqual(self.models['full']['display'],json.loads((ROOT/G['BASE']).read_bytes())['display'])
        for part,model in self.models.items():
            if part!='full':self.assertNotIn('display',model)
            self.assertTrue(model['elements'])
            self.assertEqual(model['textures']['0'],'destiny:item/weapon/w123/ammit_ar2')
            for e in model['elements']:
                self.assertTrue(set(e['faces'])<=set(G['FACES']))
                self.assertTrue(e['faces'])
                for a,b in zip(e['from'],e['to']):
                    self.assertTrue(math.isfinite(a) and math.isfinite(b) and -16<=a<=b<=32)
                self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
                self.assertEqual(len(e['rotation']['origin']),3)
                for f in e['faces'].values():
                    self.assertEqual(f['texture'],'#0')
                    self.assertEqual(len(f['uv']),4)
                    self.assertTrue(all(math.isfinite(v) and 0<=v<=16 for v in f['uv']))

    def test_source_magazine_independent_and_exact_union(self):
        body=self.models['body']['elements'];mag=self.models['magazine']['elements']
        self.assertTrue(body and mag)
        self.assertEqual(self.models['full']['elements'],body+mag)
        self.assertLessEqual(len(body)+len(mag),1000)
        self.assertTrue(all(e['name'].startswith('Magazine_') for e in mag))
        self.assertFalse(any(e['name'].startswith('Magazine_') for e in body))
        self.assertFalse({e['name'] for e in body}&{e['name'] for e in mag})

    def test_atlas_inspection_and_manifest(self):
        raw=(ROOT/G['TEXTURE']).read_bytes();im=Image.open(io.BytesIO(raw))
        self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(G['EDGE'],G['EDGE']))
        self.assertEqual(im.getchannel('A').getextrema(),(0,255))
        self.assertGreater(len(im.getcolors(G['EDGE']**2)),10)
        bb=json.loads((ROOT/(G['ART']+'inspection.bbmodel')).read_bytes())
        self.assertEqual(len(bb['elements']),len(self.models['full']['elements']))
        self.assertEqual([g['name'] for g in bb['outliner']],['body','magazine'])
        for p,h in self.manifest['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        for p,h in self.manifest['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        self.assertEqual(self.manifest['emitted_faces'],sum(len(e['faces']) for e in self.models['full']['elements']))

    def test_semantic_solids_replace_profile_caps(self):
        design=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        self.assertEqual(design['stage'],'W126')
        self.assertEqual(design['source']['anchor'],[8,8,8])
        self.assertAlmostEqual(design['source']['scale'],29.582997427721224)
        self.assertEqual(self.manifest['alpha_contour_elements'],0)
        self.assertEqual(self.manifest['triangle_adapter_elements'],0)
        specs=[s for ss in design['parts'].values() for s in ss]
        self.assertTrue(all(s['kind']=='solid_cuboid' for s in specs))
        self.assertTrue({'upper','foreend','stock','grip','fluid','muzzle','tube','magazine'}<=set(design['groups']))
        self.assertFalse(any('_profile_cap' in e['name'] or '_edge_0' in e['name'] for e in self.models['full']['elements']))
        # Validate semantic structure, not an obsolete W124 geometry fingerprint.
        self.assertLess(len(specs),200)
        self.assertEqual(len(self.models['full']['elements']),len(specs))
        for e in self.models['full']['elements']:
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertTrue(all(b-a>.05 for a,b in zip(e['from'],e['to'])))
        for path,h in design['raw_input_sha256'].items():
            self.assertEqual(G['sha'](Path(path).read_bytes()),h,path)

    def test_real_negative_space_and_depth(self):
        import numpy as np
        helper=G['renderer']()
        def occupied(point,e):
            point=np.array(point);origin=np.array(e['rotation']['origin'])
            local=(point-origin)@helper['rotation'](e['rotation'])+origin
            return bool(np.all(local>np.array(e['from'])+1e-5) and np.all(local<np.array(e['to'])-1e-5))
        elements=self.models['full']['elements']
        design=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        for label,p in design['required_air_probes'].items():
            self.assertFalse(any(occupied(p,e) for e in elements),label)
        # Channel tube has real thickness, long lower beam and pistol grip are
        # solid; bore is open at entry AND deeper in front of its recess.
        for p in ([8,12.66,.82],[8,9.35,-5],[8,8.8,8.4]):
            self.assertTrue(any(occupied(p,e) for e in elements),p)
        for z in (-8.90,-8.70,-8.4,-8.15):
            self.assertFalse(any(occupied([8,12.37,z],e) for e in elements),z)
        self.assertTrue(any(occupied([8,12.37,-8.08],e) for e in elements))
        # Upper side-slot is genuinely open around the inset tube, not alpha.
        for x in (7.30,8.70):
            self.assertFalse(any(occupied([x,12.65,1],e) for e in elements))
        for s in (-1,1):
            self.assertEqual(sum(e['name'].startswith(f'Fluid_rim_{s}_') for e in elements),8)
        self.assertEqual(self.manifest['worst_two_magazines'],len(self.models['body']['elements'])+2*len(self.models['magazine']['elements']))

    def test_magazine_rake_and_original_coordinate_envelope(self):
        import numpy as np
        helper=G['renderer']()
        design=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        source=np.array(design['source_landmarks']['Magazine'])
        mag=self.models['magazine']['elements']
        p=np.concatenate([helper['vertices'](e) for e in mag])
        self.assertTrue(np.all(p.min(0)>=source[0]-.04))
        self.assertTrue(np.all(p.max(0)<=source[1]+.04))
        self.assertLess(np.max(abs(p.min(0)-source[0])),.04)
        self.assertLess(np.max(abs(p.max(0)-source[1])),.04)
        body=next(e for e in mag if e['name']=='Magazine_body')
        self.assertLess(body['rotation']['x'],0) # lower tip leans toward +Z
        top=next(e for e in mag if e['name']=='Magazine_neck')['rotation']['origin']
        bottom=next(e for e in mag if e['name']=='Magazine_base')['rotation']['origin']
        self.assertGreater(bottom[2]-top[2],.8)
        self.assertAlmostEqual(top[0],8)
        self.assertAlmostEqual(bottom[0],8)

    def test_face_uv_islands_are_opaque_padded_and_aspect_correct(self):
        import numpy as np
        design=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        atlas=np.array(Image.open(ROOT/G['TEXTURE']))
        helper=G['renderer']();byname={e['name']:e for e in self.models['full']['elements']}
        occupied=np.zeros((G['EDGE'],G['EDGE']),bool)
        for island in design['atlas']['islands']:
            x0,y0,x1,y1=island['pixels'];region=np.s_[y0-2:y1+2,x0-2:x1+2]
            self.assertFalse(occupied[region].any(),island)
            occupied[region]=True
            self.assertTrue((atlas[region][:,:,3]==255).all(),island)
            e=byname[island['element']];face=island['face'];p=helper['vertices'](e)[list(G['FACES'][face])]
            width=np.linalg.norm(p[1]-p[0]);height=np.linalg.norm(p[3]-p[0])
            # Very narrow faces have a 5px minimum, otherwise rounded dimensions
            # must retain the physical aspect ratio within a few texels.
            if min(x1-x0,y1-y0)>5:
                self.assertLessEqual(max((x1-x0-1)/width,(y1-y0-1)/height),min((x1-x0)/width,(y1-y0)/height)+1e-5)
        self.assertEqual(design['atlas']['face_islands'],6*len(byname))
        receiver=byname['Rear_receiver']
        self.assertNotEqual(receiver['faces']['east']['uv'],receiver['faces']['west']['uv'])
        self.assertGreater(design['atlas']['used_texels'],200000)
        for side in ('east','west'):
            uv=receiver['faces'][side]['uv'];x0,y0,x1,y1=[round(v*G['EDGE']/16) for v in uv]
            a=atlas[y0:y1,x0:x1,:3]
            # The source OMOLON triangles rasterize legible pale glyph pixels.
            self.assertGreater(np.all(a==G['PALETTE']['ivory'],axis=2).sum(),12)
            # Inner source object is an alpha/decal rectangle. Its GStack mask
            # must produce letters rather than a solid white rectangle.
            pts=helper['vertices'](receiver)[list(G['FACES'][side])]
            vv,uu=np.mgrid[:a.shape[0],:a.shape[1]]
            world=pts[0]+((uu+.5)/a.shape[1])[:,:,None]*(pts[1]-pts[0])+((vv+.5)/a.shape[0])[:,:,None]*(pts[3]-pts[0])
            region=(world[:,:,1]>11.787)&(world[:,:,1]<12.104)&(world[:,:,2]>6.62)&(world[:,:,2]<8.282)
            marks=np.all(a==G['PALETTE']['ivory'],axis=2)&region
            self.assertGreater(marks.sum(),8)
            self.assertLess(marks.sum()/region.sum(),.65)


    def test_regenerated_assets(self):
        # One targeted data regeneration; omit the slow review rasterizer.
        outputs=G['generate'](include_review=False)
        for p,b in outputs.items():
            if p.endswith('manifest.json'):continue
            self.assertEqual((ROOT/p).read_bytes(),b,p)

if __name__=='__main__':unittest.main()
