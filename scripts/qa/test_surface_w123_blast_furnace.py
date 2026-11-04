#!/usr/bin/env python3
"""W127 Blast Furnace lightweight offline data/geometry/UV/reproduction checks."""
import base64
import collections
import io
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_blast_furnace.py'))


class BlastFurnaceArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models={p:json.loads((ROOT/(G['MODEL']+suffix+'.json')).read_bytes())
            for p,suffix in [('full',''),('body','_body'),('magazine','_magazine')]}
        cls.manifest=json.loads((ROOT/(G['ART']+'manifest.json')).read_bytes())
        cls.design=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        cls.h=G['renderer']()
        cls.elements=cls.models['full']['elements']
        cls.atlas=np.array(Image.open(ROOT/G['TEXTURE']))

    def occupied(self,point):
        for e in self.elements:
            origin=np.array(e['rotation']['origin'])
            p=(np.array(point)-origin)@self.h['rotation'](e['rotation'])+origin
            if np.all(p>np.array(e['from'])+1e-6) and np.all(p<np.array(e['to'])-1e-6):return True
        return False

    def test_01_native_schema_and_display(self):
        canonical=json.loads((ROOT/G['BASE']).read_bytes())
        self.assertEqual(canonical['display'],self.models['full']['display'])
        for part,m in self.models.items():
            if part!='full':self.assertNotIn('display',m)
            self.assertEqual(set(m),{'credit','textures','elements','display'} if part=='full' else {'credit','textures','elements'})
            self.assertEqual(m['textures'],{'0':'destiny:item/weapon/w123/blast_furnace','particle':'destiny:item/weapon/w123/blast_furnace'})
            for e in m['elements']:
                self.assertEqual(set(e),{'name','from','to','rotation','faces'})
                self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
                self.assertEqual(len(e['rotation']['origin']),3)
                for a,b in zip(e['from'],e['to']):self.assertTrue(math.isfinite(a) and math.isfinite(b) and -16<=a<b<=32)
                self.assertTrue(all(math.isfinite(v) for v in e['rotation']['origin']))
                self.assertTrue(all(math.isfinite(e['rotation'][a]) for a in 'xyz'))
                self.assertEqual(set(e['faces']),set(G['FACES']))
                for f in e['faces'].values():
                    self.assertEqual(set(f),{'uv','texture'});self.assertEqual(f['texture'],'#0')
                    self.assertEqual(len(f['uv']),4)
                    self.assertTrue(all(math.isfinite(v) and 0<=v<=16 for v in f['uv']))
                    self.assertGreater(f['uv'][2]-f['uv'][0],0);self.assertGreater(f['uv'][3]-f['uv'][1],0)

    def test_02_union_budget_and_reload_sources(self):
        body=self.models['body']['elements'];mag=self.models['magazine']['elements']
        self.assertEqual(self.elements,body+mag)
        self.assertLessEqual(len(body)+len(mag),1000)
        self.assertEqual(len(self.elements),len({e['name'] for e in self.elements}))
        self.assertTrue(all(e['name'].startswith('Magazine_') for e in mag))
        self.assertFalse(any(e['name'].startswith('Magazine_') for e in body))
        src=G['ASSET']+'models/weapon_reload_w114_blast_furnace/blast_furnace'
        original=json.loads((ROOT/G['BASE']).read_bytes())['elements']
        bp=json.loads((ROOT/(src+'_body.json')).read_bytes())['elements']
        mp=json.loads((ROOT/(src+'_magazine.json')).read_bytes())['elements']
        self.assertEqual((len(original),len(bp),len(mp)),(249,237,12))
        key=lambda e:json.dumps(e,sort_keys=True)
        self.assertEqual(collections.Counter(map(key,original)),collections.Counter(map(key,bp+mp)))
        self.assertEqual(self.manifest['worst_two_magazines'],len(body)+2*len(mag))

    def test_03_axis_scale_anchor_and_magazine_insertion(self):
        self.assertEqual(self.design['source']['anchor'],[8,8,8])
        self.assertAlmostEqual(self.design['source']['scale'],30.010419887180735)
        points=np.concatenate([self.h['vertices'](e) for e in self.elements])
        source=np.array(self.design['source']['model_bounds'])
        self.assertTrue(np.all(abs(points.min(0)-source[0])<.025))
        self.assertTrue(np.all(abs(points.max(0)-source[1])<.025))
        mag=self.models['magazine']['elements'];p=np.concatenate([self.h['vertices'](e) for e in mag])
        src=G['ASSET']+'models/weapon_reload_w114_blast_furnace/blast_furnace_magazine.json'
        sm=json.loads((ROOT/src).read_bytes())['elements'];sp=np.concatenate([self.h['vertices'](e) for e in sm])
        self.assertTrue(np.all(p.min(0)>=sp.min(0)-.20))
        self.assertTrue(np.all(p.max(0)<=sp.max(0)+.20))
        insert=next(e for e in mag if e['name']=='Magazine_rear_insert')
        self.assertAlmostEqual(insert['to'][1],11.76,places=4)
        self.assertEqual(insert['rotation']['origin'],[8.00624,10.70,12.53])
        self.assertTrue(all(e['rotation']['origin'][0]==8.00624 for e in mag))
        self.assertLess(min(p[:,2]),0+10.0) # original forward red catch, not a recentered magazine

    def test_04_actual_air_corridors(self):
        for name,p in self.design['required_air_probes'].items():self.assertFalse(self.occupied(p),name)
        for x in np.linspace(7.1,8.9,7):
            for y,z in [(10.0,4.5),(14.75,7.90),(12.20,14.70)]:
                # Optic clear aperture is narrower than the receiver/stock.
                if y==14.75 and abs(x-8)>.20:continue
                self.assertFalse(self.occupied([x,y,z]),(x,y,z))
        for x in (7.12,8.88):
            for z in np.linspace(-2.3,2.2,7):self.assertFalse(self.occupied([x,12.85,z]))
        for z in np.linspace(-6.70,-6.06,9):
            for x in (7.94,8.0,8.06):self.assertFalse(self.occupied([x,12.78,z]))
        self.assertTrue(self.occupied([8,12.78,-5.99]))
        self.assertEqual(sum(e['name'].startswith('Muzzle_rim_') for e in self.elements),8)
        self.assertEqual(sum(e['name'].startswith('Bore_wall_') for e in self.elements),8)

    def test_05_solid_volumes_not_alpha_body(self):
        for p in ([8,11.76,6.2],[8,12.55,-4.62],[8,12.155,0],[8,13.02,7.88],[8,13.35,13.14],[8,8.24,11.77],[8,8.5,8.2]):
            self.assertTrue(self.occupied(p),p)
        for e in self.elements:self.assertTrue(all(b-a>.05 for a,b in zip(e['from'],e['to'])))
        specs=[s for ss in self.design['parts'].values() for s in ss]
        self.assertEqual(len(specs),len(self.elements))
        self.assertTrue(all(s['kind']=='solid_cuboid' for s in specs))
        self.assertEqual(self.manifest['alpha_contour_elements'],0)
        self.assertEqual(self.manifest['triangle_adapter_elements'],0)
        self.assertTrue({'receiver','foreend','breech','stock','grip','trigger','muzzle','optic','magazine'}<=set(self.design['groups']))

    def test_06_atlas_padded_opaque_and_physical_aspect(self):
        a=self.atlas;edge=G['EDGE'];self.assertEqual(a.shape,(edge,edge,4))
        names={e['name']:e for e in self.elements};used=np.zeros((edge,edge),bool)
        for island in self.design['atlas']['islands']:
            x0,y0,x1,y1=island['pixels'];region=np.s_[y0-2:y1+2,x0-2:x1+2]
            self.assertFalse(used[region].any(),island);used[region]=True
            self.assertTrue((a[region][:,:,3]==255).all())
            e=names[island['element']];f=island['face'];p=self.h['vertices'](e)[list(G['FACES'][f])]
            w=np.linalg.norm(p[1]-p[0]);h=np.linalg.norm(p[3]-p[0])
            self.assertEqual(e['faces'][f]['uv'],[v*16/edge for v in (x0,y0,x1,y1)])
            if min(x1-x0,y1-y0)>5:
                self.assertLessEqual(max((x1-x0-1)/w,(y1-y0-1)/h),min((x1-x0)/w,(y1-y0)/h)+1e-5)
        self.assertEqual(len(self.design['atlas']['islands']),len(self.elements)*6)
        self.assertGreater(self.design['atlas']['used_texels'],150000)
        receiver=names['Receiver_main']
        self.assertNotEqual(receiver['faces']['east']['uv'],receiver['faces']['west']['uv'])
        for name in ('Receiver_main','Front_lower_core','Magazine_core','Red_breech'):
            for face in ('east','west'):
                x0,y0,x1,y1=[round(v*edge/16) for v in names[name]['faces'][face]['uv']]
                self.assertGreater(len(np.unique(a[y0:y1,x0:x1,:3].reshape(-1,3),axis=0)),8,(name,face))

    def test_07_bbmodel_and_hash_provenance(self):
        bb=json.loads((ROOT/(G['ART']+'inspection.bbmodel')).read_bytes())
        self.assertEqual(len(bb['elements']),len(self.elements))
        self.assertEqual([g['name'] for g in bb['outliner']],['body','magazine'])
        for group in bb['outliner']:self.assertEqual(group['origin'],[8,8,8])
        self.assertEqual(bb['display'],self.models['full']['display'])
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',')[1]),(ROOT/G['TEXTURE']).read_bytes())
        for p,h in self.manifest['input_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        for p,h in self.manifest['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(p).read_bytes()),h,p)
        for p,h in self.manifest['output_sha256'].items():self.assertEqual(G['sha']((ROOT/p).read_bytes()),h,p)
        self.assertEqual(self.manifest['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_blast_furnace.py').read_bytes()))
        self.assertEqual(self.manifest['emitted_faces'],len(self.elements)*6)
        self.assertFalse(self.manifest['native_accepted'])

    def test_08_deterministic_generation(self):
        outputs=G['generate'](include_review=False)
        for p,data in outputs.items():
            if p.endswith('manifest.json'):continue # review omission changes only manifest hash inventory
            self.assertEqual((ROOT/p).read_bytes(),data,p)
        outputs2=G['generate'](include_review=False)
        self.assertEqual(outputs,outputs2)

    def test_09_ownership_and_review_artifact(self):
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w127/batch.json').read_bytes())
        owned=next(f['owned_paths'] for f in batch['features'] if f['name']=='w127-blast_furnace')
        self.assertEqual(len(owned),12)
        self.assertTrue(all((ROOT/p).is_file() for p in owned))
        self.assertTrue(set(self.manifest['output_sha256'])<=set(owned))
        with Image.open(ROOT/(G['ART']+'comparison.png')) as im:self.assertEqual(im.size,(2000,1780))
        self.assertEqual(self.manifest['source_triangles'],29124)


if __name__=='__main__':unittest.main()
